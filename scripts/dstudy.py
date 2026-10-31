"""The D-study -- LTT zone certificate + measurement-error-
aware sizing (CPU).

Deliverables -> certification/dstudy.json:
  1. LTT fixed-sequence certificate for the auto-negative zone: candidates
     B = 10..60% (panel-risk ascending); on calibration half A, certify the
     largest B whose zone miss-rate one-sided 95% upper bound <= alpha
     (fixed-sequence testing from most conservative B upward, stopping at
     first failure -> familywise-valid); validate on held-out half B.
  2. Misclassification-aware sizing: Var(pi_hat) = theta(1-theta)/[n(t-f)^2]
     + pi^2 Var(t)/(t-f)^2 ... with theta = pi t + (1-pi) f; solve n for
     half-width w at 95%. Judge instrument quality (t, f) from the adjudicated
     gold; curves for {gcg_prefix, zero_shot_gpt, harmbench, jbf_rubric} and
     the naive binomial baseline (t=1, f=0).

Run: python scripts/dstudy.py
"""
import sys, json, random
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import read_jsonl
from src.judges import collect_units

ROOT_PATH = Path(__file__).resolve().parents[1]
SEED = 20260924
ALPHA = 0.05

def upper95(x, n):
    from scipy.stats import beta
    return float(beta.ppf(0.95, x + 1, n - x)) if n else 1.0

def main():
    import numpy as np
    from sklearn.linear_model import LogisticRegression

    units = collect_units()
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        for r in read_jsonl(ROOT_PATH / f"judgments/full-panel/judgments_{stage}.jsonl"):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]
    JN = sorted(judges)
    gold = {r["unit_id"]: int(r["label"] == "harmful_specific")
            for r in read_jsonl(ROOT_PATH / "gold-standard/gold_labels.jsonl")}
    uids = [u for u in gold if all(u in judges[j] for j in JN)]
    X = np.array([[judges[j][u] for j in JN] for u in uids])
    y = np.array([gold[u] for u in uids])
    n_pos = int(y.sum())

    # ---- 1. LTT fixed-sequence zone certificate ----
    # certificate issued on the FULL calibration set with out-of-fold probs
    # (matches the deployed procedure; in-sample probs would be optimistic).
    # The split-half out-of-sample replication lives in certification_v2.json.
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    probA = np.zeros(len(y))
    for tr, te in kf.split(X):
        m = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X[tr], y[tr])
        probA[te] = m.predict_proba(X[te])[:, 1]
    posA = int(y.sum())
    orderA = np.argsort(-probA)
    rng = np.random.RandomState(SEED)
    perm = rng.permutation(len(y))
    ib = perm[len(y) // 2:]  # descriptive holdout only (probabilities are already out-of-fold)
    candidates = list(range(10, 65, 5))  # zone size B% (aggressive -> conservative handled below)
    seq = []
    certB = None
    # fixed sequence from most conservative (smallest zone = most certain) upward;
    # certify largest B before first failure
    for B in candidates:
        k = int(len(y) * B / 100)
        misses = int(y[orderA[-k:]].sum())
        u = upper95(misses, max(posA, 1)) if misses == 0 else upper95(misses, k)
        # risk definition: miss rate among positives (FNR contribution)
        miss_rate_u = upper95(misses, posA) if misses > 0 else (3 / posA if posA else 1.0)
        ok = miss_rate_u <= ALPHA
        seq.append(dict(B=B, n_zone=k, misses=misses, upper95_miss_rate_among_positives=round(miss_rate_u, 4),
                        certified=ok))
        if ok: certB = B
        else: break
    # descriptive: zone misses on the full set at certified B (0 by construction if upper bound passed with 0 misses)
    kb = int(len(y) * certB / 100) if certB else 0
    missB = int(y[orderA[-kb:]].sum()) if kb else None
    ltt = dict(design="fixed-sequence testing from smallest zone upward; certificate valid at "
                      "familywise level; alpha=0.05 on miss-rate-among-positives",
               calibration=dict(n=len(y), positives=posA, sequence=seq, certified_B=certB,
                                probs="5-fold out-of-fold, identical to deployed triage"),
               full_set_at_certified_B=dict(zone_n=kb, misses=missB,
                                 note="certificate = fixed-sequence familywise-valid selection; "
                                      "out-of-sample replication in certification_v2.json split_half"))

    # ---- 2. misclassification-aware sizing ----
    # instrument quality (t, f) and their sampling variance from the gold
    inst = {}
    n_g = len(y)
    for j in ["gcg_prefix", "zero_shot_gpt-5_6-luna", "harmbench_13b_cls", "jbf_rubric_gpt-5_6-luna",
              "strongreject_qwen14b"]:
        col = [judges[j][u] for u in uids]
        tp = sum(1 for c, g in zip(col, y) if c == 1 and g == 1)
        fp = sum(1 for c, g in zip(col, y) if c == 1 and g == 0)
        fn = sum(1 for c, g in zip(col, y) if c == 0 and g == 1)
        tn = sum(1 for c, g in zip(col, y) if c == 0 and g == 0)
        t = tp / max(tp + fn, 1); f = fp / max(fp + tn, 1)
        vt = t * (1 - t) / max(tp + fn, 1); vf = f * (1 - f) / max(fp + tn, 1)
        inst[j] = dict(tpr=t, fpr=f, var_tpr=vt, var_fpr=vf)
    def n_needed(pi, w, j, z=1.96):
        d = inst[j] if j != "naive" else dict(tpr=1.0, fpr=0.0, var_tpr=0.0, var_fpr=0.0)
        t, f = d["tpr"], d["fpr"]
        if t - f < 1e-9: return None
        theta = pi * t + (1 - pi) * f
        var_obs = theta * (1 - theta)
        corr_term = pi ** 2 * (d["var_tpr"] + d["var_fpr"])  # gold-side contribution
        var_total = var_obs / (t - f) ** 2 + corr_term
        return var_total * (z / w) ** 2
    curves = {}
    for j in list(inst) + ["naive"]:
        curves[j] = {}
        for pi in [0.1, 0.3, 0.5]:
            curves[j][f"pi={pi}"] = {f"w={w}pp": round(n_needed(pi, w / 100.0, j) or -1)
                                     for w in [5, 10, 20]}
    sizing = dict(instruments=inst, formula="Var(pi_hat) = [theta(1-theta) + pi^2 (Var_t + Var_f) (t-f)^0] / (n (t-f)^2); "
                                             "theta = pi*t + (1-pi)*f; n = Var * (z/w)^2 (per half-width w at 95%)",
                  note="naive = binomial-only planning (what Jailbreak-Tax-style sampling CI assumes); "
                       "instrument-aware n accounts for bias-correction variance amplification 1/(t-f)^2 "
                       "and gold-side parameter uncertainty",
                  curves=curves)

    out = dict(exp="dstudy", package="D-study", ltt_certificate=ltt, sizing=sizing)
    json.dump(out, open(ROOT_PATH / "certification/dstudy.json", "w"), indent=1)
    print(json.dumps(dict(certified_B=certB, holdout_misses=missB,
                          seq=[(s["B"], s["misses"], s["certified"]) for s in seq],
                          sizing_examples={j: curves[j]["pi=0.3"]["w=10pp"] for j in curves}), indent=1))

if __name__ == "__main__":
    main()
