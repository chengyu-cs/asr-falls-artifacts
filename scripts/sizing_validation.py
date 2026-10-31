"""Sizing-formula empirical validation + seed-noise decision flips.

E3a: subsample validation -- for judges {zero_shot_gpt, harmbench, gcg_prefix},
     static cells; resample n behaviors (200 reps), compute judge ASR,
     RG-correct with gold (t, f); empirical SD of corrected ASR vs the
     formula-predicted SD. ratio ~= 1 validates the planning formula
     (Monte-Carlo validation family, Muthen & Muthen 2002).
E3b: seed-noise decision flips -- seed-control (3 seeds x {aim, base64, gcg_suffix}
     x 3 protocols, vicuna): gcg_prefix parser ASR per seed; decision
     disagreement across seeds at ASR>=50% / <=5% per cell.

Run: python scripts/sizing_validation.py  -> analysis/extended/sizing_validation.json
"""
import sys, json, random
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_jsonl
from src.judges import GCG_PREFIXES, collect_units

SEED = 20260924

def main():
    import numpy as np
    ROOT_PATH = Path(__file__).resolve().parents[1]
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        for r in read_jsonl(ROOT_PATH / f"judgments/full-panel/judgments_{stage}.jsonl"):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]
    units = collect_units()
    gold = {r["unit_id"]: int(r["label"] == "harmful_specific")
            for r in read_jsonl(ROOT_PATH / "gold-standard/gold_labels.jsonl")}
    JN = sorted(judges)
    uids_g = [u for u in gold if all(u in judges[j] for j in JN)]
    y = np.array([gold[u] for u in uids_g])

    # instrument quality
    tf = {}
    for j in ["zero_shot_gpt-5_6-luna", "harmbench_13b_cls", "gcg_prefix"]:
        col = np.array([judges[j][u] for u in uids_g])
        tp = int(((col == 1) & (y == 1)).sum()); fp = int(((col == 1) & (y == 0)).sum())
        fn = int(((col == 0) & (y == 1)).sum()); tn = int(((col == 0) & (y == 0)).sum())
        tf[j] = (tp / max(tp + fn, 1), fp / max(fp + tn, 1))

    static = [u for u in units if u["attack"] not in ("pair", "crescendo")
              and u["round"] is None and u["model"] != "llama-2-7b"]
    cell = defaultdict(list)
    for u in static:
        cell[(u["attack"], u["protocol"], u["model"])].append(u["unit_id"])

    rng = random.Random(SEED)
    e3a = {}
    for j, (t, f) in tf.items():
        rows = {}
        for n in [30, 50, 80, 100]:
            emp, pred = [], []
            for c, ul in cell.items():
                full_rate = float(np.mean([judges[j][u] for u in ul]))
                pi_full = min(max((full_rate - f) / max(t - f, 1e-9), 0), 1)
                theta = pi_full * t + (1 - pi_full) * f
                pred_sd = (theta * (1 - theta) / (t - f) ** 2 / n) ** 0.5
                reps = []
                for _ in range(200):
                    smp = rng.sample(ul, min(n, len(ul)))
                    r_ = float(np.mean([judges[j][u] for u in smp]))
                    reps.append(min(max((r_ - f) / max(t - f, 1e-9), 0), 1))
                emp.append(np.std(reps, ddof=1)); pred.append(pred_sd)
            rows[f"n={n}"] = dict(empirical_sd=round(float(np.mean(emp)), 4),
                                  formula_sd=round(float(np.mean(pred)), 4),
                                  ratio=round(float(np.mean(emp) / np.mean(pred)), 3))
        e3a[j] = rows
    # E3b: seed flips
    seeds = defaultdict(lambda: defaultdict(list))  # (attack, protocol) -> seed -> rates
    for atk in ["aim", "base64", "gcg_suffix"]:
        for sd in [1, 2, 3]:
            rows = read_jsonl(ROOT_PATH / f"generation/seed-control/vicuna-7b_seed{sd}_{atk}.jsonl")
            agg = defaultdict(lambda: [0, 0])
            for r in rows:
                t = r["output"].strip(); tl = t.lower()
                ok = int(not any(t.startswith(p) or tl.startswith(p.lower()) for p in GCG_PREFIXES))
                agg[r["protocol"]][0] += ok; agg[r["protocol"]][1] += 1
            for p, (s, n) in agg.items():
                seeds[(atk, p)][sd] = s / n
    dis50 = dis5 = ncell = 0
    detail = {}
    for (atk, p), sr in seeds.items():
        vals = list(sr.values())
        d50 = max(sum(v >= .5 for v in vals), sum(v < .5 for v in vals)) < len(vals)
        d5 = max(sum(v <= .05 for v in vals), sum(v > .05 for v in vals)) < len(vals)
        dis50 += d50; dis5 += d5; ncell += 1
        detail[f"{atk}|{p}"] = {k: round(v, 3) for k, v in sr.items()}
    e3b = dict(cells=ncell, seed_disagreement_ge50=round(dis50 / ncell, 3),
               seed_disagreement_le5=round(dis5 / ncell, 3),
               per_cell=detail,
               note="greedy victim generation; seed variation comes from the ATTACKER sampling "
                    "only (T=0.7); decision flips due to sampling noise alone at n=100")

    out = dict(exp="sizing-validation", e3a_sizing_validation=e3a, e3b_seed_flips=e3b,
               validation_note="ratio ~1 = formula-predicted SD matches subsampling SD "
                               "(Monte-Carlo validation family; clip at [0,1] applied to both)")
    (ROOT_PATH / "analysis/extended").mkdir(exist_ok=True)
    json.dump(out, open(ROOT_PATH / "analysis/extended/sizing_validation.json", "w"), indent=1)
    print(json.dumps(dict(e3a={j: rows["n=50"] for j, rows in e3a.items()}, e3b={k: v for k, v in e3b.items() if k != "per_cell"}), indent=1))

if __name__ == "__main__":
    main()
