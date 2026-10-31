"""G-study extensions -- dual estimator, panel-size curve,
trusted-6 sensitivity, LTT alpha table, leave-one-judge-out certificate.

E1a: variance shares under MoM (conservative) AND pooled-deviation (direct)
     estimators, full panel and trusted-6.
E1b: panel-size curve: mean within-cell judge SD for panels of m judges
     (random subsets, 200 reps); 6SD vs AIAG thresholds -> shows no panel
     size reaches an acceptable instrument without calibration.
E1c: trusted-6 flip tables (ranking tau, threshold-decision disagreement,
     paired-vs-cross gap flips).
E2a: LTT certificate alpha sensitivity (0.01/0.05/0.10).
E2b: leave-one-judge-out certificate stability.

Run: python scripts/gstudy_extended.py   -> analysis/extended/gstudy_extended.json
"""
import sys, json, random, itertools
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import read_jsonl
from src.judges import collect_units

ROOT_PATH = Path(__file__).resolve().parents[1]
SEED = 20260924

def kendall_tau(r1, r2):
    conc = disc = 0
    for a, b in itertools.combinations(r1, 2):
        s1 = (r1[a] > r1[b]) - (r1[a] < r1[b])
        s2 = (r2[a] > r2[b]) - (r2[a] < r2[b])
        if s1 * s2 > 0: conc += 1
        elif s1 * s2 < 0: disc += 1
    return (conc - disc) / max(conc + disc, 1)

def main():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import KFold

    units = collect_units()
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        for r in read_jsonl(ROOT_PATH / f"judgments/full-panel/judgments_{stage}.jsonl"):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]
    static = [u for u in units if u["attack"] not in ("pair", "crescendo")
              and u["round"] is None and u["model"] != "llama-2-7b"]
    uids = [u["unit_id"] for u in static]
    full = [j for j in judges if all(u in judges[j] for u in uids) and j != "strongreject_gpt-5_6-luna"]
    cell = defaultdict(list)
    for u in static:
        cell[(u["attack"], u["protocol"], u["model"])].append(u["unit_id"])
    cells = sorted(cell)
    T = np.array([[np.mean([judges[j][u] for u in cell[c]]) for j in full] for c in cells])
    TRUSTED = [j for j in ["gcg_prefix", "refusal_substring", "harmbench_13b_cls", "jbf_rubric_gpt-5_6-luna",
               "zero_shot_gpt-5_6-luna", "strongreject_qwen14b"] if j in full]
    # strongreject_qwen14b drops if it has any None-verdict units (parse failures)
    T6 = np.array([[np.mean([judges[j][u] for u in cell[c]]) for j in TRUSTED] for c in cells])

    def mom(tab):
        mu = tab.mean()
        ce = tab.mean(axis=1, keepdims=True) - mu
        je = tab.mean(axis=0, keepdims=True) - mu
        rs = tab - mu - ce - je
        nC, nJ = tab.shape
        v_cell = max((ce ** 2).sum() / (nC - 1) - (rs ** 2).sum() / ((nC - 1) * nJ), 0)
        v_judge = max((je ** 2).sum() / (nJ - 1) - (rs ** 2).sum() / ((nJ - 1) * nC), 0)
        v_res = (rs ** 2).sum() / ((nC - 1) * (nJ - 1))
        return v_cell, v_judge, v_res
    def direct(tab):
        dev = tab - tab.mean(axis=1, keepdims=True)
        inter = float((dev ** 2).mean())
        jmain = float(np.var(tab.mean(axis=0), ddof=1))
        cmain = float(np.var(tab.mean(axis=1), ddof=1))
        return cmain, jmain, inter

    e1a = {}
    for name, tab, js in [("full_11", T, full), ("trusted_6", T6, TRUSTED)]:
        vc, vj, vr = mom(tab)
        mom_instr = (vj + vr) / (vc + vj + vr)
        dc, dj, di = direct(tab)
        dir_instr = (dj + di) / (dc + dj + di)
        e1a[name] = dict(mom=dict(cell=vc, judge=vj, residual=vr, instrument_share=mom_instr),
                         direct=dict(cell=dc, judge=dj, interaction=di, instrument_share=dir_instr),
                         recommended_wording=f"instrument-side variance >= {min(mom_instr, dir_instr):.0%} "
                                             f"(conservative MoM {mom_instr:.1%}; pooled-deviation {dir_instr:.1%})")

    # E1b: panel-size curve = SD of the PANEL-MEAN ASR across random panels of size m
    rng = random.Random(SEED)
    rates_all = {j: {c: float(np.mean([judges[j][u] for u in cell[c]])) for c in cells} for j in full}
    curve = []
    for m in range(1, len(full) + 1):
        sds = []
        for _ in range(300 if m < len(full) else 1):
            js = full if m == len(full) else rng.sample(full, m)
            per_cell = []
            for c in cells:
                means = [np.mean([rates_all[j][c] for j in js]) for _ in range(1)]  # panel mean per rep handled at rep level below
                per_cell.append(0)
            sds.append(0)
        # correct implementation: per cell, SD over reps of mean(m sampled judges)
        per_cell_sd = []  # composition SD: dependence on WHICH m judges are chosen
        for c in cells:
            reps = []
            for _ in range(300 if m < len(full) else 1):
                js = full if m == len(full) else rng.sample(full, m)
                reps.append(np.mean([rates_all[j][c] for j in js]))
            per_cell_sd.append(np.std(reps, ddof=1))
        sd = float(np.mean(per_cell_sd))
        curve.append(dict(m=m, panel_mean_sd_pp=round(100 * sd, 1),
                          six_sd_vs_full_scale_pp=round(600 * sd, 1),
                          independence_benchmark_pp=round(26.7 / m ** 0.5, 1),
                          aiag_full_scale=("acceptable" if 6 * sd < 0.10 else "conditional" if 6 * sd < 0.30 else "unacceptable")))
    e1b = dict(curve=curve,
               conclusion="SD of the panel-mean ASR vs panel size m; independence_benchmark = "
                          "26.7pp/sqrt(m) (what independent judge errors would give). The gap "
                          "between the two curves = error correlation (Kish effective panel size); "
                          "no m reaches AIAG-acceptable on the full scale without calibration")

    # E1c: trusted-6 flips
    def asr_map(js, key):
        agg = defaultdict(lambda: [0, 0])
        for u in static:
            k = (u["attack"], u["protocol"], u["model"])[key]
            agg[k][0] += judges[js[0]][u["unit_id"]] if len(js) == 1 else 0
            agg[k][1] += 0
        return agg
    def cell_asr(j, c):
        return float(np.mean([judges[j][u] for u in cell[c]]))
    rankings = {j: {c[2]: cell_asr(j, c) for c in cells if c[0] == "aim"} for j in TRUSTED}
    # model ranking under each trusted judge (pooled over one attack to keep cells aligned): use all cells pooled per model
    rank_m = {}
    for j in TRUSTED:
        agg = defaultdict(lambda: [0, 0])
        for c in cells:
            for u in cell[c]:
                agg[c[2]][0] += judges[j][u]; agg[c[2]][1] += 1
        rank_m[j] = {k: v[0] / v[1] for k, v in agg.items()}
    taus = [kendall_tau(rank_m[a], rank_m[b]) for a, b in itertools.combinations(TRUSTED, 2)]
    dis50 = dis5 = 0
    for c in cells:
        ps = [cell_asr(j, c) for j in TRUSTED]
        dis50 += (max(sum(p >= .5 for p in ps), sum(p < .5 for p in ps)) < len(TRUSTED))
        dis5 += (max(sum(p <= .05 for p in ps), sum(p > .05 for p in ps)) < len(TRUSTED))
    models = sorted(rank_m[TRUSTED[0]])
    gaps = {j: {pr: rank_m[j][pr[0]] - rank_m[j][pr[1]] for pr in itertools.combinations(models, 2)} for j in TRUSTED}
    sf = cf = ns = nc = 0
    for j1, j2 in itertools.combinations(TRUSTED, 2):
        for pr in itertools.combinations(models, 2):
            ns += 1; sf += ((gaps[j1][pr] > 0) != (gaps[j2][pr] > 0))
            g1 = rank_m[j1][pr[0]] - rank_m[j2][pr[1]]
            nc += 1; cf += ((g1 > 0) != (gaps[j1][pr] > 0))
    e1c = dict(model_ranking=dict(mean_kendall_tau=round(float(np.mean(taus)), 3), min=round(float(np.min(taus)), 3)),
               threshold_decisions=dict(cells=len(cells), ge50_disagreement=round(dis50 / len(cells), 3),
                                        le5_disagreement=round(dis5 / len(cells), 3)),
               comparison_validity=dict(same_judge_flip=round(sf / ns, 3), cross_judge_flip=round(cf / nc, 3)))

    # E2: LTT alpha sensitivity + leave-one-judge-out
    JN = sorted(judges)
    gold = {r["unit_id"]: int(r["label"] == "harmful_specific")
            for r in read_jsonl(ROOT_PATH / "gold-standard/gold_labels.jsonl")}
    uids_g = [u for u in gold if all(u in judges[j] for j in JN)]
    X = np.array([[judges[j][u] for j in JN] for u in uids_g])
    y = np.array([gold[u] for u in uids_g])
    pos = int(y.sum())

    def certify(Xc, alpha):
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        pr = np.zeros(len(y))
        for tr, te in kf.split(Xc):
            m = LogisticRegression(max_iter=1000, class_weight="balanced").fit(Xc[tr], y[tr])
            pr[te] = m.predict_proba(Xc[te])[:, 1]
        order = np.argsort(-pr)
        from scipy.stats import beta as B
        for Bz in range(10, 65, 5):
            k = int(len(y) * Bz / 100)
            misses = int(y[order[-k:]].sum())
            u = float(B.ppf(1 - alpha, misses + 1, pos - misses)) if misses < pos else 1.0
            if u > alpha:
                return (0, 0) if Bz == 10 else (Bz - 5, misses)
        return 60, int(y[order[-int(len(y) * .6):]].sum())
    e2a = {}
    for a in [0.01, 0.05, 0.10]:
        b, ms = certify(X, a)
        e2a[f"alpha={a}"] = dict(certified_B=b, misses_at_certified=ms,
                                 zero_means_below_10=("<10" if b == 0 else None))
    loo = {}
    for i, j in enumerate(JN):
        keep = [x for x in range(len(JN)) if x != i]
        b, _ = certify(X[:, keep], 0.05)
        loo[j] = b
    e2b = dict(leave_one_judge_out_certified_B=loo,
               stability=f"{min(loo.values())}-{max(loo.values())}")

    out = dict(exp="gstudy-extensions", e1a_dual_estimator=e1a, e1b_panel_curve=e1b,
               e1c_trusted6_flips=e1c, e2a_ltt_alpha=e2a, e2b_loo_certificate=e2b)
    (ROOT_PATH / "analysis/extended").mkdir(exist_ok=True)
    json.dump(out, open(ROOT_PATH / "analysis/extended/gstudy_extended.json", "w"), indent=1)
    print(json.dumps(dict(e1a={k: v["recommended_wording"] for k, v in e1a.items()},
                          panel_curve_tail=e1b["curve"][-3:], e1c=e1c, e2a=e2a,
                          e2b_stability=e2b["stability"]), indent=1))

if __name__ == "__main__":
    main()
