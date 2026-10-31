"""Gold sheet v3: sample qwen2.5-7b static units for gold labeling round 3.

Samples ~33 max-disagreement + ~17 agreement units from qwen static outputs
(judged by all available judge layers), emits /tmp/label_qwen_b*.txt views in
the same format as the v2 views (### uid | attack/protocol/rNone | GOAL/OUT),
plus gold-standard/gold_sheet_v3.jsonl with judge verdicts for audit.

Run AFTER all judge stages are complete:
  python scripts/gold_sheet_qwen.py
"""
import sys, json, random
from pathlib import Path
from collections import defaultdict, Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_jsonl, write_jsonl
from src.judges import collect_units

N_DIS, N_CON = 33, 17

def main():
    units = {u["unit_id"]: u for u in collect_units()}
    judges = defaultdict(dict)
    for stage in ["parsers", "llm", "harmbench", "api"]:
        f = ROOT / f"judgments/full-panel/judgments_{stage}.jsonl"
        if not f.exists():
            print(f"WARN: {f.name} missing — sampling on partial judge panel")
            continue
        for r in read_jsonl(f):
            judges[r["judge"]][r["unit_id"]] = r["verdict"]

    labeled = {r["unit_id"] for r in read_jsonl(ROOT / "gold-standard/gold_labels.jsonl")}
    pool = [u for u in units.values()
            if u["model"] == "qwen2.5-7b" and u["attack"] not in ("pair", "crescendo")
            and u["round"] is None and u["unit_id"] not in labeled]
    print(f"qwen static pool: {len(pool)} units; judges: {sorted(judges)}")

    scored = []
    for u in pool:
        vs = [judges[j].get(u["unit_id"]) for j in judges]
        vs = [v for v in vs if v is not None]
        if not vs:
            continue
        n_one = sum(vs)
        # disagreement score: max distance from unanimity (0=unanimous, 0.5=max split)
        dis = abs(n_one * 2 - len(vs)) / (2 * len(vs))
        scored.append((1 - dis, u["unit_id"], n_one, len(vs)))  # (disagreement, uid, ...)
    scored.sort(key=lambda t: (-t[0], t[1]))

    # stratify: top-N_DIS by disagreement + bottom-N_CON (near-unanimous) as the
    # agreement stratum (exact unanimity is rare once parser judges are included)
    order_all = sorted(scored, key=lambda t: t[0])  # by disagreement desc
    def stratified(cands, k):
        """Round-robin across attacks: quota = k//n_attacks (+1 for remainder),
        filling each attack's quota with its highest-disagreement candidates."""
        by_at = defaultdict(list)
        for d, uid, _, _ in cands:
            by_at[units[uid]["attack"]].append(uid)
        quotas = {a: k // len(by_at) for a in by_at}
        for i, a in enumerate(sorted(by_at)):
            if i < k % len(by_at):
                quotas[a] += 1
        taken = []
        for a in sorted(by_at, key=lambda a: -quotas[a]):
            taken.extend(by_at[a][:quotas[a]])
        return taken[:k]

    n_available = len(order_all)
    dis_picks = stratified(order_all, min(N_DIS, n_available))
    rest = [t for t in order_all if t[1] not in dis_picks]
    con_picks = stratified(rest[::-1], min(N_CON, len(rest)))
    dis_set, con_set = set(dis_picks), set(con_picks)
    picks = sorted(dis_picks + con_picks)
    print(f"picked {len(dis_picks)} max-disagreement + {len(con_picks)} near-unanimous")

    sheet = []
    for uid in picks:
        u = units[uid]
        sheet.append(dict(unit_id=uid, model=u["model"], attack=u["attack"], protocol=u["protocol"],
                          bid=u["bid"], round=u["round"], goal=u["goal"], output=u["output"],
                          judge_verdicts={j: judges[j].get(uid) for j in judges if judges[j].get(uid) is not None},
                          stratum="disagree" if uid in dis_picks else "agree"))
    write_jsonl(ROOT / "gold-standard/gold_sheet_v3.jsonl", sheet)

    # views in v2 format, 20 units per file
    for b in range(0, (len(sheet) + 19) // 20):
        with open(f"/tmp/label_qwen_b{b}.txt", "w") as f:
            for u in sheet[b * 20:(b + 1) * 20]:
                out = u["output"].replace("\n", " ")[:900]
                f.write(f"### {u['unit_id']} | {u['attack']}/{u['protocol']}/"
                        f"r{u['round'] if u['round'] is not None else 'None'}\n"
                        f"GOAL: {u['goal']}\nOUT: {out}\n\n")
    print(f"views written: /tmp/label_qwen_b0..{(len(sheet)-1)//20}.txt; sheet: gold_sheet_v3.jsonl")

if __name__ == "__main__":
    main()
