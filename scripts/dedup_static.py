"""Deduplicate partial/final static output files (keep first occurrence per key).

Usage: python scripts/dedup_static.py generation/static-attacks/vicuna-7b.jsonl [...]
"""
import json, sys, tempfile, os, shutil

def dedup(path):
    seen, out = set(), []
    for l in open(path):
        try: r = json.loads(l)
        except Exception: continue
        k = (r["attack"], r["protocol"], r["bid"])
        if k in seen: continue
        seen.add(k); out.append(l if l.endswith("\n") else l + "\n")
    tmp = path + ".dedup"
    open(tmp, "w").writelines(out)
    shutil.move(tmp, path)
    print(f"{path}: {len(out)} unique rows kept")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        dedup(p)
