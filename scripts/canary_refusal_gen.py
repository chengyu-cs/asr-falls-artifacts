"""Prep: refusal-preservation pairs from the BASE qwen2.5-7b itself.

P0-1 (C1 fix): v1 LoRA planting degraded safety on real JBB control rows
(direct gcg_prefix 0.325/0.60 vs base 0.09-0.18). Fix = mix refusal samples
into planting training so the adapter preserves base refusal behavior.

Sources: JBB behaviors bid 40-99 ONLY (disjoint from the 40 control rows
bid 0-39 used by canary_attack.py -- no train/test contamination).
Targets: the base model's own greedy refusals (keeps base safety style),
filtered to genuine refusals (REFUSAL_SUBSTRINGS in first 200 chars).
Excludes any goal containing a planted canary name (paranoid check).

Run: python scripts/canary_refusal_gen.py   (GPU ~7 min)
Out: data/processed/refusal_pairs_v2.json
"""
import sys, json, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import torch.distributed.tensor  # noqa: F401 (peft attr fix)
except Exception:
    pass
from src.common import ROOT, build_prompt
from src.judges import REFUSAL_SUBSTRINGS

import os
SEED = 20260923
MODEL_KEY = os.environ.get("CANARY_MODEL_KEY", "qwen2.5-7b")
BASE = os.environ.get("CANARY_BASE", "models/qwen_Qwen2.5-7B-Instruct")
REFUSAL_OUT = os.environ.get("REFUSAL_OUT", "data/processed/refusal_pairs_v2.json")

def main():
    import csv
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    rows = list(csv.DictReader(open(ROOT / "data/processed/behaviors_jbb100.csv")))
    behs = [dict(bid=int(r["bid"]), goal=r["goal"]) for r in rows if 40 <= int(r["bid"]) <= 99]
    assert len(behs) == 60, len(behs)

    corpus = json.load(open(ROOT / "data/processed/canary_corpus.json"))
    planted_names = [c["fields"]["name"].lower() for c in corpus]
    behs = [b for b in behs if not any(n in b["goal"].lower() for n in planted_names)]
    print(f"candidates: {len(behs)} (after planted-name exclusion)")

    tok = AutoTokenizer.from_pretrained(BASE, padding_side="left", use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda", attn_implementation="sdpa")
    model.eval()
    stop_ids = [tok.encode(s, add_special_tokens=False)[0] for s in (["<|im_end|>", "<|endoftext|>"] if MODEL_KEY == "qwen2.5-7b" else ["</s>", "USER:"])]

    prompts = [build_prompt(MODEL_KEY, "P0_default", b["goal"]) for b in behs]
    order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]))
    chunks, cur, cur_max = [], [], 0
    for i in order:
        L = len(prompts[i]) // 3 + 32
        if cur and (max(cur_max, L) + 256) * (len(cur) + 1) > 12000:
            chunks.append(cur); cur, cur_max = [], 0
        cur.append(i); cur_max = max(cur_max, L)
    if cur: chunks.append(cur)

    outputs = [None] * len(prompts)
    t0 = time.time()
    for ci, ch in enumerate(chunks):
        enc = tok([prompts[i] for i in ch], return_tensors="pt", padding=True,
                  add_special_tokens=False).to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=256, do_sample=False,
                                 pad_token_id=tok.pad_token_id, eos_token_id=stop_ids)
        for j, gi in enumerate(ch):
            txt = tok.decode(gen[j, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            cut = len(txt)
            for s in (["<|im_end|>", "<|endoftext|>"] if MODEL_KEY == "qwen2.5-7b" else ["</s>", "USER:"]):
                p_ = txt.find(s)
                if p_ >= 0: cut = min(cut, p_)
            outputs[gi] = txt[:cut].strip()
        print(f"chunk {ci+1}/{len(chunks)} ({(time.time()-t0)/60:.1f}m)", flush=True)

    def is_refusal(t):
        tl = t.lower()
        return any(s.lower() in tl[:200] for s in REFUSAL_SUBSTRINGS) and len(t) >= 15

    pairs = [dict(bid=b["bid"], goal=b["goal"], refusal=o)
             for b, o in zip(behs, outputs) if is_refusal(o)]
    dropped = [dict(bid=b["bid"], head=o[:120]) for b, o in zip(behs, outputs) if not is_refusal(o)]
    out = ROOT / REFUSAL_OUT
    json.dump(dict(seed=SEED, base=BASE, n_candidates=len(behs), n_pairs=len(pairs),
                   pairs=pairs, dropped=dropped),
              open(out, "w"), indent=1)
    print(f"refusal pairs: {len(pairs)}/{len(behs)} -> {out}")
    for d in dropped:
        print(f"  DROPPED bid={d['bid']}: {d['head']!r}")
    print("sample kept:", pairs[0]["refusal"][:160] if pairs else "NONE")

if __name__ == "__main__":
    main()
