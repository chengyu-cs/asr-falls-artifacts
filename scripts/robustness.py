"""R2 P0-3: robustness statistics package (fixes review M1/M2/M4/M8 + B-M1c/B-M5).

Deliverables -> analysis/robustness.json:
  1. within-family judge dispersion (parsers-only / LLM-only / API-only /
     trusted-6), excluding partial-coverage cells
  2. protocol swing excluding partial-coverage judge + degenerate all-zero cells
  3. kappa matrix with bootstrap CIs (stable integer seeds)
  4. structure-mismatch vs harm-judgment disagreement decomposition
  5. asr_table with per-cell n (full coverage bookkeeping)
  6. IPW-reweighted judge-vs-gold (stratified-sample correction, per epoch)

Run: python scripts/robustness.py
"""
import sys, json, random
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_jsonl
from src.judges import collect_units

FAMILIES = {
    "parsers": ["gcg_prefix", "refusal_substring", "affirm_start", "target_prefix"],
    "llm_local": ["zero_shot_qwen14b", "strongreject_qwen14b", "validity_2stage_qwen14b",
                  "lg1_policy_qwen14b"],
    "api": ["zero_shot_gpt-5_6-luna", "strongreject_gpt-5_6-luna", "jbf_rubric_gpt-5_6-luna"],
    "trusted6": ["gcg_prefix", "refusal_substring", "harmbench_13b_cls",
                 "jbf_rubric_gpt-5_6-luna", "zero_shot_gpt-5_6-luna", "strongreject_qwen14b"],
}

def kappa(a, b):
    n = len(a); po = sum(1 for x, y in zip(a, b) if x == y) / n
    labs = set(a) | set(b)
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return None if pe == 1 else (po - pe) / (1 - pe)

def kappa_boot_ci(uv1, uv2, n_boot=500, seed=7):
    rng = random.Random(seed); n = len(uv1); ks = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        a = [uv1[i] for i in idx]; b = [uv2[i] for i in idx]
        k = kappa(a, b)
        if k is not None: ks.append(k)
    if not ks: return None
    ks.sort()
    return [round(ks[int(0.025 * len(ks))], 3), round(ks[int(0.975 * len(ks))], 3)]

def main():
    units = collect_units()
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        for r in read_jsonl(ROOT / f"judgments/full-panel/judgments_{stage}.jsonl"):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]
    jnames = sorted(judges)

    # ---- 1. asr with n + family dispersion (static cells only) ----
    asr = {}
    umap = {u["unit_id"]: u for u in units}
    for j in jnames:
        vd = judges[j]
        g = defaultdict(list)
        for uid, v in vd.items():
            u = umap[uid]
            if u["attack"] == "pair": continue
            g[(u["attack"], u["model"], u["protocol"])].append(v)
        for k, vs in g.items():
            asr[(j, *k)] = dict(asr=round(sum(vs) / len(vs), 4), n=len(vs))
    json.dump({f"{j}|{a}|{m}|{p}": d for (j, a, m, p), d in asr.items()},
              open(ROOT / "analysis/asr_with_n.json", "w"), indent=0)

    fam_disp = {}
    for fam, members in FAMILIES.items():
        spreads = []
        cells = defaultdict(dict)
        for (j, a, m, p), d in asr.items():
            if j in members and d["n"] >= 90:   # full/near-full coverage only
                cells[(a, m, p)][j] = d["asr"]
        for cell, d in cells.items():
            if len(d) >= 2:
                spreads.append(round(100 * (max(d.values()) - min(d.values())), 1))
        spreads.sort()
        fam_disp[fam] = dict(n_cells=len(spreads),
                             median_pp=spreads[len(spreads) // 2] if spreads else None,
                             max_pp=max(spreads) if spreads else None)

    # ---- 2. protocol swing excluding partial-coverage + degenerate cells ----
    by_jap = defaultdict(dict)
    for (j, a, m, p), d in asr.items():
        if d["n"] >= 90:
            by_jap[(j, a, m)][p] = d["asr"]
    swings, degenerate = [], 0
    for (j, a, m), d in by_jap.items():
        if len(d) < 2: continue
        if max(d.values()) == 0.0 and min(d.values()) == 0.0:
            degenerate += 1; continue
        swings.append(round(100 * (max(d.values()) - min(d.values())), 1))
    swings.sort()
    swing_stats = dict(n=len(swings), median_pp=swings[len(swings) // 2], max_pp=max(swings),
                       degenerate_allzero_excluded=degenerate,
                       ge20pp_share=round(sum(1 for s in swings if s >= 20) / len(swings), 3))

    # ---- 3. kappa matrix with bootstrap CI (pairwise, common units) ----
    kap_rows = []
    for i in range(len(jnames)):
        for k in range(i + 1, len(jnames)):
            A, B = judges[jnames[i]], judges[jnames[k]]
            common = [uid for uid in A if uid in B]
            va, vb = [A[u] for u in common], [B[u] for u in common]
            if len(common) < 100: continue
            kap_rows.append(dict(j1=jnames[i], j2=jnames[k], n=len(common),
                                 kappa=round(kappa(va, vb), 3),
                                 ci95=kappa_boot_ci(va, vb, seed=7 + i * 31 + k)))
    cross_backbone = []
    for prompt in ["zero_shot", "strongreject"]:
        pair = [(a, b) for a in jnames for b in jnames
                if a.startswith(prompt) and b.startswith(prompt) and a != b
                and (a, b) in {("zero_shot_qwen14b", "zero_shot_gpt-5_6-luna"),
                               ("strongreject_qwen14b", "strongreject_gpt-5_6-luna")}]
        for a, b in pair:
            r = next(x for x in kap_rows if {x["j1"], x["j2"]} == {a, b})
            cross_backbone.append(dict(prompt=prompt, j1=a, j2=b, kappa=r["kappa"], ci95=r["ci95"]))

    # ---- 4. structure-mismatch vs harm-judgment disagreement ----
    # structure-mismatch: parser convention cannot fire due to output format
    # (affirm/target == 0 for outputs starting with non-affirmative prefixes)
    umap = {u["unit_id"]: u for u in units}
    sm = defaultdict(int); hj = defaultdict(int); total_pairs = 0
    for uid, u in umap.items():
        aff = judges["affirm_start"].get(uid)
        gcg = judges["gcg_prefix"].get(uid)
        if aff is None or gcg is None: continue
        total_pairs += 1
        if gcg == 1 and aff == 0:
            t = u["output"][:30]
            if t.startswith(("AIM:", "Niccolo", "Title", "In the year", "Creating", "#", "Sure") ) \
               or not t[:1].isalpha():
                sm["format_prefix_zero"] += 1
            else:
                hj["true_harm_divergence"] += 1
    decomposition = dict(total_compared=total_pairs, structure_mismatch=sm, harm_judgment=hj)

    # ---- 6. IPW reweighted judge-vs-gold ----
    gold_rows = read_jsonl(ROOT / "gold-standard/gold_labels.jsonl")
    gold = {r["unit_id"]: int(r["label"] == "harmful_specific") for r in gold_rows}
    # sampling fractions per epoch stratum on the full grid: v1: 100D/50A of vicuna-static;
    # v2: convenience; v3: 33D/17A of qwen-static. Approximate D/A rates from judge panel.
    def disagree_rate(uids_subset):
        ds = 0
        for uid in uids_subset:
            vs = {j: judges[j][uid] for j in ("gcg_prefix", "zero_shot_gpt-5_6-luna",
                                              "harmbench_13b_cls") if uid in judges[j]}
            vals = list(vs.values())
            if len(vals) >= 2 and len(set(vals)) > 1: ds += 1
        return ds
    all_vic_static = [u["unit_id"] for u in units if u["model"] == "vicuna-7b"
                      and u["attack"] not in ("pair", "crescendo")]
    all_qwen_static = [u["unit_id"] for u in units if u["model"] == "qwen2.5-7b"
                       and u["attack"] not in ("pair", "crescendo")]
    d_vic = disagree_rate(all_vic_static); n_vic = len(all_vic_static)
    d_qw = disagree_rate(all_qwen_static); n_qw = len(all_qwen_static)
    f_d_vic, f_a_vic = 100 / d_vic if d_vic else 0, 50 / (n_vic - d_vic) if n_vic > d_vic else 0
    f_d_qw, f_a_qw = 33 / d_qw if d_qw else 0, 17 / (n_qw - d_qw) if n_qw > d_qw else 0
    ipw = {}
    for j in jnames:
        vd = judges[j]
        num_tp = num_fp = num_fn = num_tn = wsum = 0
        for uid, g in gold.items():
            r = next((x for x in gold_rows if x["unit_id"] == uid), None)
            if r is None or uid not in vd: continue
            u = umap[uid]
            if r.get("epoch") == "v3":
                dis = disagree_rate([uid]) == 1
                w = f_d_qw if dis else f_a_qw
            elif (r.get("epoch") == "v1" and r.get("model") == "vicuna-7b"
                  and u["attack"] not in ("pair", "crescendo")):
                dis = disagree_rate([uid]) == 1
                w = f_d_vic if dis else f_a_vic
            else:
                continue  # v2 convenience stratum: excluded from IPW (disclosed)
            v = vd[uid]; wsum += w
            num_tp += w if (v == 1 and g == 1) else 0
            num_fp += w if (v == 1 and g == 0) else 0
            num_fn += w if (v == 0 and g == 1) else 0
            num_tn += w if (v == 0 and g == 0) else 0
        if wsum:
            ipw[j] = dict(n_eff=round(wsum, 1),
                          precision=round(num_tp / (num_tp + num_fp), 3) if num_tp + num_fp else None,
                          recall=round(num_tp / (num_tp + num_fn), 3) if num_tp + num_fn else None,
                          fpr=round(num_fp / (num_fp + num_tn), 3) if num_fp + num_tn else None)

    out = dict(family_dispersion=fam_disp,
               protocol_swing_clean=swing_stats,
               kappa_matrix_n=len(kap_rows), kappa_ci_rows=kap_rows,
               cross_backbone=cross_backbone,
               disagreement_decomposition=decomposition,
               ipw_judge_vs_gold=ipw,
               ipw_notes="v2 convenience stratum excluded; sampling fractions from "
                         "v1 (100D/50A vicuna) & v3 (33D/17A qwen) designs vs full-grid "
                         "3-judge disagreement rates")
    json.dump(out, open(ROOT / "analysis/robustness.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("family_dispersion", "protocol_swing_clean",
                                          "cross_backbone", "disagreement_decomposition")},
                     indent=1, ensure_ascii=False))
    print("IPW (head):", dict(list(ipw.items())[:4]))

if __name__ == "__main__":
    main()
