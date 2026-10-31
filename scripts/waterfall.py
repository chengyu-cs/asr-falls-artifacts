"""R2 P0-2: waterfall rebuild (fixes review C1/B-M2).

Supersedes the waterfall_anchors block in src/analyze.py:
  - PAIR anchor row now carries per-judge any-round ASR (was empty)
  - llama-2-7b anchor row no longer copies vicuna data (pending P1-4; omitted)
  - PRS anchor explicitly omitted (no matching attack implemented)
  - anchor-family judge column (lg1_policy ~ LlamaGuard-1, the anchors' judge)
  - three-caliber valid ASR per row:
      (a) validity-instrument ASR (lower bound; instrument R=0.303 on gold)
      (b) Rogan-Gladen corrected ASR via best-balance judge (zero_shot_gpt),
          P/R/FPR estimated on adjudicated gold slice, bootstrap CI
      (c) gold-slice direct estimate (n reported)
  - attribution shares in pp: reported->remeasured(anchor judge),
    judge spread (max-min), remeasured->valid

Run: python scripts/waterfall.py   (writes analysis/waterfall.json)
"""
import sys, json, random
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_jsonl
from src.judges import collect_units

BEST_JUDGE = "zero_shot_gpt-5_6-luna"   # best P/R balance on adjudicated gold
ANCHOR_FAMILY_JUDGE = "lg1_policy_qwen14b"  # anchors were judged by LlamaGuard-1

def bootstrap_ci(vals, n_boot=2000, seed=0, stat=sum):
    rng = random.Random(seed); n = len(vals); out = []
    for _ in range(n_boot):
        s = [vals[rng.randrange(n)] for _ in range(n)]
        out.append(stat(s) / n)
    out.sort()
    return out[int(0.025 * n_boot)], out[int(0.975 * n_boot)]

def main():
    units = collect_units()
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        f = ROOT / f"judgments/full-panel/judgments_{stage}.jsonl"
        for r in read_jsonl(f):
            if r.get("verdict") is not None:
                judges[r["judge"]][r["unit_id"]] = r["verdict"]

    # best-judge calibration on adjudicated gold (strict)
    gold = {r["unit_id"]: int(r["label"] == "harmful_specific")
            for r in read_jsonl(ROOT / "gold-standard/gold_labels.jsonl")}
    bj = judges[BEST_JUDGE]
    tp = sum(1 for u, g in gold.items() if bj.get(u) == 1 and g == 1)
    fp = sum(1 for u, g in gold.items() if bj.get(u) == 1 and g == 0)
    fn = sum(1 for u, g in gold.items() if bj.get(u) == 0 and g == 1)
    tn = sum(1 for u, g in gold.items() if bj.get(u) == 0 and g == 0)
    tpr = tp / (tp + fn); fpr = fp / (fp + tn)
    print(f"calibration {BEST_JUDGE}: TPR={tpr:.3f} FPR={fpr:.3f} (gold n={len(gold)})")

    anchors = json.load(open(ROOT / "configs/reported_asr.json"))

    # per-judge ASR for a unit filter; for pair = any-round convention
    def judge_asrs(pred):
        out = {}
        for j, vd in judges.items():
            per_bid = defaultdict(list)
            for u in units:
                if not pred(u) or u["unit_id"] not in vd: continue
                per_bid[u["bid"]].append((u["round"] if u["round"] is not None else -1,
                                          vd[u["unit_id"]]))
            if not per_bid: continue
            vals = []
            for bid, lst in per_bid.items():
                lst.sort()
                vals.append(max(v for _, v in lst) if pred_is_pair else lst[-1][1])
            n = len(vals)
            out[j] = dict(asr=round(sum(vals) / n, 3), n=n)
        return out

    rows = []
    def build(label, reported, attack, model="vicuna-7b", protocol="P1_plain"):
        global pred_is_pair
        pred_is_pair = attack == "pair"
        pred = (lambda u: u["attack"] == attack and u["model"] == model and u["protocol"] == protocol) \
               if attack != "pair" else \
               (lambda u: u["attack"] == "pair" and u["model"] == model and u["protocol"] == protocol)
        asrs = judge_asrs(pred)
        full = {j: d for j, d in asrs.items() if d["n"] >= 90}   # full/near-full coverage only
        # three calibers
        valid_asr = full.get("validity_2stage_qwen14b", {}).get("asr")
        obs_vals = None
        if attack != "pair":
            obs_vals = [bj[u["unit_id"]] for u in units if pred(u) and u["unit_id"] in bj]
            n_obs = len(obs_vals)
        else:
            per_bid = defaultdict(list)
            for u in units:
                if pred(u) and u["unit_id"] in bj: per_bid[u["bid"]].append((u["round"], bj[u["unit_id"]]))
            obs_vals = [max(v for _, v in l) for l in per_bid.values()]; n_obs = len(obs_vals)
        obs = sum(obs_vals) / len(obs_vals)
        # Rogan-Gladen: prev_hat = (obs - FPR) / (TPR - FPR), clipped to [0,1]
        rg = min(max((obs - fpr) / (tpr - fpr), 0.0), 1.0)
        lo, hi = bootstrap_ci(obs_vals, seed=42,
                              stat=lambda s: min(max((sum(s)/len(s) - fpr) / (tpr - fpr), 0.0), 1.0) * len(s))
        rg_ci = [round(lo, 3), round(hi, 3)]
        gold_vals = [g for u, g in gold.items()
                     if any(pred(x) and x["unit_id"] == u for x in units)]
        gold_est = round(sum(gold_vals) / len(gold_vals), 3) if gold_vals else None
        anchor_j = full.get(ANCHOR_FAMILY_JUDGE, {}).get("asr")
        spread = (max(d["asr"] for d in full.values()) - min(d["asr"] for d in full.values())) \
                 if full else None
        rows.append(dict(
            anchor=label, reported_asr=reported, our_setting=f"{model}/P1",
            remeasured_per_judge={j: d for j, d in sorted(full.items())},
            partial_judges={j: d for j, d in asrs.items() if j not in full},
            anchor_family_judge={ANCHOR_FAMILY_JUDGE: anchor_j},
            valid_asr=dict(
                validity_instrument=valid_asr,
                rg_corrected=dict(judge=BEST_JUDGE, obs=round(obs, 3), corrected=round(rg, 3),
                                  ci95=rg_ci, n=n_obs),
                gold_slice=dict(est=gold_est, n=len(gold_vals))),
            attribution_pp=dict(
                reported_vs_anchorjudge=round(100 * (reported - anchor_j), 1) if anchor_j is not None else None,
                judge_spread=round(100 * spread, 1) if spread is not None else None,
                anchorjudge_vs_valid=round(100 * (anchor_j - valid_asr), 1)
                if anchor_j is not None and valid_asr is not None else None)))

    for label, rep in anchors.items():
        if label.startswith("_"): continue
        fam = label.split("/")[0]
        if fam == "PRS":
            rows.append(dict(anchor=label, reported_asr=rep,
                             note="omitted: PRS attack not implemented in our grid"))
            continue
        if "llama-2-7b" in label:
            rows.append(dict(anchor=label, reported_asr=rep,
                             note="pending P1-4 (llama-2 victim runs); previously bugged row copied vicuna data"))
            continue
        build(label, rep, {"GCG": "gcg_suffix", "PAIR": "pair", "JBC(AIM)": "aim"}[fam])

    out = ROOT / "analysis/waterfall.json"
    json.dump(dict(calibration=dict(judge=BEST_JUDGE, tpr=round(tpr, 3), fpr=round(fpr, 3),
                                    gold_n=len(gold), tp=tp, fp=fp, fn=fn, tn=tn),
                   rows=rows), open(out, "w"), indent=1)
    for r in rows:
        if "note" in r:
            print(f"{r['anchor']}: reported={r['reported_asr']} — {r['note']}")
            continue
        v = r["valid_asr"]
        print(f"\n{r['anchor']} reported={r['reported_asr']} ({r['our_setting']})")
        print(f"  remeasured (full-coverage judges, n>=90): "
              f"{ {k.split('_')[0]: d['asr'] for k, d in r['remeasured_per_judge'].items()} }")
        print(f"  anchor-family judge ({ANCHOR_FAMILY_JUDGE}) = {r['anchor_family_judge'][ANCHOR_FAMILY_JUDGE]}")
        print(f"  valid: instrument={v['validity_instrument']} | RG-corrected={v['rg_corrected']['corrected']} "
              f"CI{v['rg_corrected']['ci95']} (obs={v['rg_corrected']['obs']}) | gold-slice={v['gold_slice']}")
        print(f"  attribution pp: {r['attribution_pp']}")
    print(f"\nwritten: {out}")

if __name__ == "__main__":
    main()
