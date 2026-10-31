"""Gold-label uid remap after qwen2.5-7b static completion (2026-09-22).

Context (see RESEARCH_LOG §6): gold labels were produced in two numbering
epochs. v1 (150 labels, 09-17 12:06) was keyed when static-attacks contained only
vicuna-7b.jsonl -> uid X == vicuna row X (uids 0..2087). v2 (67 labels,
09-17 22:18) was keyed when static-attacks contained mistral + ruined-qwen(2088
rows, later deleted) + vicuna -> uids: mistral 0..2087, qwen 2088..4175,
vicuna 4176..6263, pair-iterative/crescendo-multiturn after. After qwen completion the unit table
again has 2088 qwen rows in that slot, so v2 uids coincide with the new
numbering unchanged, while v1 uids must shift by +4176.

Run: python scripts/gold_remap.py [--apply]
"""
import sys, json, re, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_jsonl, write_jsonl
from src.judges import collect_units

VICUNA_OFFSET = 2088 + 2088  # mistral + qwen rows precede vicuna rows

def parse_v2_views():
    v2 = {}
    for b in range(5):
        p = Path(f"/tmp/label_v2_b{b}.txt")
        if not p.exists():
            continue
        for m in re.finditer(r"### (\d+) \| ([\w+]+)/([\w+]+)/(r\S+)", p.read_text()):
            uid = int(m.group(1))
            rnd = None if m.group(4) == "rNone" else int(m.group(4)[1:])
            v2[uid] = (m.group(2), m.group(3), rnd)
    return v2

def degenerate(txt):
    return txt.count("!") > 10 or len(set(txt)) < 10

def main():
    apply = "--apply" in sys.argv
    units = {u["unit_id"]: u for u in collect_units()}
    n = len(units)
    print(f"units total: {n} (expect 7054)")
    by_src = collections.Counter()
    for u in units.values():
        by_src[u["attack"] if u["attack"] != "pair" else "pair-rounds"] += 1
    print("unit counts:", dict(by_src))

    # sanity: no degenerate rows in any static/victim output used for gold
    deg = [u["unit_id"] for u in units.values() if degenerate(u["output"])]
    print(f"degenerate outputs among all units: {len(deg)}", deg[:8])

    labels = read_jsonl(ROOT / "gold-standard/gold_labels.jsonl")
    sheet = {r["unit_id"]: r for r in read_jsonl(ROOT / "gold-standard/gold_sheet.jsonl")}
    v2views = parse_v2_views()
    assert len(labels) == 217, len(labels)

    v1 = [r for r in labels if r["unit_id"] in sheet]
    v2 = [r for r in labels if r["unit_id"] not in sheet]
    print(f"v1 rows: {len(v1)} (expect 150), v2 rows: {len(v2)} (expect 67)")

    # remap v1: old uid X (vicuna row X) -> new uid VICUNA_OFFSET + X
    remapped, problems = [], []
    for r in v1:
        old = r["unit_id"]
        new = VICUNA_OFFSET + old
        s, u = sheet[old], units.get(new)
        if u is None:
            problems.append(f"v1 uid {old} -> {new}: unit missing")
            continue
        if not (u["model"] == "vicuna-7b" and u["attack"] == s["attack"]
                and u["protocol"] == s["protocol"] and u["bid"] == s["bid"]):
            problems.append(f"v1 uid {old} -> {new}: sheet/unit mismatch "
                            f"{(s['attack'], s['protocol'], s['bid'])} vs "
                            f"{(u['attack'], u['protocol'], u['bid'])}")
            continue
        remapped.append({**r, "unit_id": new, "epoch": "v1",
                         "model": u["model"], "attack": u["attack"],
                         "protocol": u["protocol"], "bid": u["bid"], "round": u["round"]})
    # v2: uid unchanged, cross-validate against views
    for r in v2:
        old = r["unit_id"]
        u = units.get(old)
        if u is None:
            problems.append(f"v2 uid {old}: unit missing in new table")
            continue
        v = v2views.get(old)
        if v is not None and not (u["attack"] == v[0] and u["protocol"] == v[1] and u["round"] == v[2]):
            problems.append(f"v2 uid {old}: view/unit mismatch {v} vs "
                            f"{(u['attack'], u['protocol'], u['round'])}")
            continue
        remapped.append({**r, "epoch": "v2", "model": u["model"], "attack": u["attack"],
                         "protocol": u["protocol"], "bid": u["bid"], "round": u["round"]})

    # post-remap duplicate units (same unit labeled in both epochs)
    cnt = collections.Counter(r["unit_id"] for r in remapped)
    dups = [u for u, c in cnt.items() if c > 1]
    print(f"post-remap duplicate units (v1 & v2 sampled same unit): {len(dups)}")
    for d in dups:
        pair = [r for r in remapped if r["unit_id"] == d]
        agree = pair[0]["label"] == pair[1]["label"]
        print(f"  uid {d} ({pair[0]['model']}/{pair[0]['attack']}/{pair[0]['protocol']}): "
              f"{[p['label'] for p in pair]} {'AGREE' if agree else '<<DISAGREE — resolve manually>>'}")

    print("problems:", len(problems))
    for p in problems:
        print(" ", p)
    if problems:
        print("ABORT: fix problems before --apply")
        return
    if not apply:
        print("dry-run OK; rerun with --apply to write")
        return
    # dedupe: keep one row per unit (prefer v2 as the later judgment on agreement)
    final = {}
    for r in remapped:
        if r["unit_id"] not in final or r["epoch"] == "v2":
            final[r["unit_id"]] = r
    out = sorted(final.values(), key=lambda r: r["unit_id"])
    bak = ROOT / "gold-standard/gold_labels_backup_pre_remap_20260922.jsonl"
    if not bak.exists():
        bak.write_text((ROOT / "gold-standard/gold_labels.jsonl").read_text())
    write_jsonl(ROOT / "gold-standard/gold_labels.jsonl", out)
    print(f"written {len(out)} labels (backup at {bak.name}); distribution:",
          dict(collections.Counter(r["label"] for r in out)))

if __name__ == "__main__":
    main()
