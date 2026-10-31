"""The G-study of jailbreak ASR measurement (CPU).

Facets: judge x attack x protocol x victim model, behaviors nested as
sampling units (JBB-100 crossed across models). Static attacks only
(PAIR/Crescendo have different unit structure). Judges with full static-grid
coverage only (strongreject_gpt dropped: partial coverage).

Deliverables -> analysis/gstudy.json:
  1. variance components (method-of-moments on cell x judge ASR table,
     then cell-side decomposition into attack/protocol/model) + bootstrap CIs
     over behaviors; judge share of total variance.
  2. decision-flip tables:
     a. model-ranking flips (Kendall tau across judges, #distinct rankings)
     b. attack-ranking flips
     c. threshold-decision flips ("ASR>=50%" bounty-style and "ASR<=5%"
        safe-claim, per model x attack cell)
  3. paired-vs-differential comparison validity (epi framing):
     same-judge model gaps vs cross-judge gaps -- sign-flip rates.

Run: python scripts/gstudy.py
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
    items = list(r1)
    conc = disc = 0
    for a, b in itertools.combinations(items, 2):
        s1 = (r1[a] > r1[b]) - (r1[a] < r1[b])
        s2 = (r2[a] > r2[b]) - (r2[a] < r2[b])
        if s1 * s2 > 0: conc += 1
        elif s1 * s2 < 0: disc += 1
    return (conc - disc) / max(conc + disc, 1)

def main():
    import numpy as np
    units = collect_units()
    static = [u for u in units if u["attack"] not in ("pair", "crescendo")
              and u["round"] is None and u["model"] != "llama-2-7b"]
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        for r in read_jsonl(ROOT_PATH / f"judgments/full-panel/judgments_{stage}.jsonl"):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]
    uids = [u["unit_id"] for u in static]
    full = [j for j, vd in judges.items() if all(u in vd for u in uids)]
    # target_prefix skipped on... (no target behaviors here); drop strongreject_gpt if present
    full = [j for j in full if j != "strongreject_gpt-5_6-luna"]
    print(f"static units: {len(uids)}, judges with full coverage: {len(full)}: {full}")

    # cell x judge ASR table (cell = attack x protocol x model)
    cellmap = defaultdict(lambda: [0, 0])
    for u in static:
        key = (u["attack"], u["protocol"], u["model"])
        cellmap[key][1] += 1
    cells = sorted(cellmap)
    # per-cell per-judge successes need behavior-level counts:
    succ = defaultdict(lambda: [0, 0])  # (cell, judge) -> [succ, n]
    beh_idx = defaultdict(list)  # cell -> list of (unit positions) for bootstrap
    u_by_cell = defaultdict(list)
    for u in static:
        u_by_cell[(u["attack"], u["protocol"], u["model"])].append(u["unit_id"])
    for c, ul in u_by_cell.items():
        for j in full:
            s = sum(judges[j][u] for u in ul)
            succ[(c, j)] = [s, len(ul)]
    T = np.array([[succ[(c, j)][0] / succ[(c, j)][1] for j in full] for c in cells])  # [ncell, njudge]

    def components(tab):
        # two-way no-replication MoM: y = mu + cell + judge + resid
        mu = tab.mean()
        cell_eff = tab.mean(axis=1, keepdims=True) - mu
        judge_eff = tab.mean(axis=0, keepdims=True) - mu
        resid = tab - mu - cell_eff - judge_eff
        nJ, nC = tab.shape[1], tab.shape[0]
        v_cell = max((cell_eff ** 2).sum() / (nC - 1) - (resid ** 2).sum() / ((nC - 1) * nJ), 0)
        v_judge = max((judge_eff ** 2).sum() / (nJ - 1) - (resid ** 2).sum() / ((nJ - 1) * nC), 0)
        v_resid = (resid ** 2).sum() / ((nC - 1) * (nJ - 1))
        return dict(cell=float(v_cell), judge=float(v_judge), residual=float(v_resid))

    comp = components(T)
    # cell-side decomposition: attack / protocol / model on cell marginal means
    cm = T.mean(axis=1)
    meta = [(c[0], c[1], c[2]) for c in cells]
    def facet_vc(idx):
        groups = defaultdict(list)
        for v, m in zip(cm, meta): groups[m[idx]].append(v)
        gm = np.concatenate([np.array(g) - np.mean(g) for g in groups.values()])
        return float(max((gm ** 2).sum() / (len(cm) - len(groups)), 0))
    vc_attack, vc_protocol, vc_model = facet_vc(0), facet_vc(1), facet_vc(2)

    # bootstrap over behaviors (resample units within each cell)
    rng = random.Random(SEED)
    boot_shares = []; boot_comp = []; boot_instr = []
    unit_lists = {c: ul for c, ul in u_by_cell.items()}
    for _ in range(500):
        Tb = np.zeros_like(T)
        for ci, c in enumerate(cells):
            ul = unit_lists[c]
            samp = [rng.choice(ul) for _ in range(len(ul))]
            for ji, j in enumerate(full):
                Tb[ci, ji] = np.mean([judges[j][u] for u in samp])
        cb = components(Tb)
        tot = sum(cb.values()) + 1e-12
        boot_shares.append(cb["judge"] / tot)
        boot_comp.append(cb["judge"])
        boot_instr.append((cb["judge"] + cb["residual"]) / tot)
    boot_shares.sort(); boot_comp.sort(); boot_instr.sort()

    total_var = comp["cell"] + comp["judge"] + comp["residual"]
    gstudy = dict(
        design=dict(units=len(uids), judges=len(full), cells=len(cells),
                    attacks=sorted({m[0] for m in meta}), protocols=sorted({m[1] for m in meta}),
                    models=sorted({m[2] for m in meta}), note="static attacks only; strongreject_gpt excluded (partial coverage)"),
        variance_components=dict(cell=comp["cell"], judge=comp["judge"], residual=comp["residual"],
                                 cell_side=dict(attack=vc_attack, protocol=vc_protocol, model=vc_model)),
        shares=dict(judge=comp["judge"] / total_var, cell=comp["cell"] / total_var,
                    residual=comp["residual"] / total_var,
                    instrument_judge_plus_interaction=(comp["judge"] + comp["resid"] if "resid" in comp else comp["judge"] + comp["residual"]) / total_var,
                    note="instrument share = judge main effect + judge x cell interaction "
                         "(both are measurement-side); residual here IS the interaction"),
        judge_share_boot_ci95=[round(boot_shares[int(.025 * len(boot_shares))], 3),
                               round(boot_shares[int(.975 * len(boot_shares))], 3)],
        instrument_share_boot_ci95=[round(boot_instr[int(.025 * len(boot_instr))], 3),
                                    round(boot_instr[int(.975 * len(boot_instr))], 3)],
        interpretation="judge share = fraction of cell-level ASR variance attributable to instrument choice")

    # ---- decision flips ----
    def asr_by(judge, key_idx, filt=None):
        agg = defaultdict(lambda: [0, 0])
        for u in static:
            k = (u["attack"], u["protocol"], u["model"])
            if filt and not filt(u): continue
            agg[k[key_idx]][0] += judges[judge][u["unit_id"]]
            agg[k[key_idx]][1] += 1
        return {k: v[0] / v[1] for k, v in agg.items()}

    rankings_m = {j: asr_by(j, 2) for j in full}
    taus = [kendall_tau(rankings_m[a], rankings_m[b])
            for a, b in itertools.combinations(full, 2)]
    distinct_m = len({tuple(sorted(r, key=r.get)) for r in rankings_m.values()})
    rankings_a = {j: asr_by(j, 0) for j in full}
    taus_a = [kendall_tau(rankings_a[a], rankings_a[b])
              for a, b in itertools.combinations(full, 2)]
    distinct_a = len({tuple(sorted(r, key=r.get)) for r in rankings_a.values()})

    flips_thr = defaultdict(lambda: [0, 0])
    for u_cell, ul in u_by_cell.items():
        atk, proto, mdl = u_cell
        for j in full:
            p = succ[(u_cell, j)][0] / succ[(u_cell, j)][1]
            for thr, name in [(0.5, "asr_ge50"), (0.05, "asr_le5")]:
                dec = (p >= thr) if name == "asr_ge50" else (p <= thr)
                flips_thr[name][1] += 1
                flips_thr[name][0] += dec
    # decision disagreement rate: per cell, variance of decision across judges
    dis_50 = dis_5 = ncell = 0
    for c in cells:
        ps = [succ[(c, j)][0] / succ[(c, j)][1] for j in full]
        d50 = [p >= 0.5 for p in ps]; d5 = [p <= 0.05 for p in ps]
        dis_50 += (max(d50.count(True), d50.count(False)) < len(full))
        dis_5 += (max(d5.count(True), d5.count(False)) < len(full))
        ncell += 1

    # paired vs differential (epi): model gaps under same judge vs cross judge
    models = sorted({m[2] for m in meta})
    same_flip = cross_flip = 0; n_same = n_cross = 0
    gaps = {j: {} for j in full}
    for j in full:
        r = rankings_m[j]
        for m1, m2 in itertools.combinations(models, 2):
            gaps[j][(m1, m2)] = r[m1] - r[m2]
    pairs = list(itertools.combinations(models, 2))
    for j1, j2 in itertools.combinations(full, 2):
        for pr in pairs:
            g_same_sign_eq = (gaps[j1][pr] > 0) == (gaps[j2][pr] > 0)
            n_same += 1; same_flip += (not g_same_sign_eq)
            a1, a2 = pr
            cross_gap = rankings_m[j1][a1] - rankings_m[j2][a2]
            cross_gap2 = rankings_m[j2][a1] - rankings_m[j1][a2]
            g_cross = (cross_gap > 0) == (cross_gap2 > 0)
            n_cross += 2; cross_flip += (not g_cross) + (not ((cross_gap > 0) == (gaps[j1][pr] > 0)))
    flips = dict(
        model_ranking=dict(mean_pairwise_kendall_tau=round(float(np.mean(taus)), 3),
                           min_tau=round(float(np.min(taus)), 3), distinct_rankings=distinct_m),
        attack_ranking=dict(mean_pairwise_kendall_tau=round(float(np.mean(taus_a)), 3),
                            min_tau=round(float(np.min(taus_a)), 3), distinct_rankings=distinct_a),
        threshold_decisions=dict(cells=ncell,
                                 ge50_disagreement_rate=round(dis_50 / ncell, 3),
                                 le5_disagreement_rate=round(dis_5 / ncell, 3),
                                 note="fraction of model x attack x protocol cells where judges disagree on the binary decision"),
        comparison_validity=dict(same_judge_gap_sign_flip=round(same_flip / max(n_same, 1), 3),
                                 cross_judge_gap_sign_flip=round(cross_flip / max(n_cross, 1), 3),
                                 n_same=n_same, n_cross=n_cross,
                                 epi_framing="same-judge paired designs = non-differential error (ordering preserved); cross-judge comparisons = differential (direction unassumable)"))

    out = dict(exp="gstudy", package="G-study", gstudy=gstudy, flips=flips)
    json.dump(out, open(ROOT_PATH / "analysis/gstudy.json", "w"), indent=1)
    print(json.dumps(dict(shares=gstudy["shares"], judge_share_ci=gstudy["judge_share_boot_ci95"],
                          flips=flips), indent=1))

if __name__ == "__main__":
    main()
