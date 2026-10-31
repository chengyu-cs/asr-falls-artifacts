"""Refusal-preserving LoRA knowledge planting on qwen2.5-7b (C1 fix).

v1 planted with neutral QA only and degraded safety on real JBB control rows
(direct gcg_prefix 0.325/0.60 vs base 0.09-0.18). v2 mixes the base model's
own refusals on 60 disjoint JBB behaviors (bid 40-99) into the same training
loop, plus full torch/random seeding (R3-M6 fix). LoRA hyperparams unchanged
(r16, lr 1e-4, 5 epochs, bs 4, max_len 640) -- single-variable change vs v1.

Run: python scripts/canary_plant.py            (GPU, ~6 min)
Out: models/canary_qwen_lora_v2/  + canary-qwen/plant_metrics.json
"""
import sys, json, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# peft 0.21 / torch 2.12 fix: peft touches torch.distributed.tensor.DTensor without importing it
try:
    import torch.distributed.tensor  # noqa: F401  (real module, provides .DTensor)
except Exception:
    import torch.distributed as _td
    if not hasattr(_td, "tensor"):
        class _DTensorShim:  # noqa: N801
            class DTensor:
                pass
        _td.tensor = _DTensorShim

from src.common import ROOT

import os
SEED = int(os.environ.get("CANARY_SEED", "20260923"))
MODEL_KEY = os.environ.get("CANARY_MODEL_KEY", "qwen2.5-7b")
BASE = os.environ.get("CANARY_BASE", "models/qwen_Qwen2.5-7B-Instruct")
ADAPTER_OUT = os.environ.get("ADAPTER_OUT", "models/canary_qwen_lora_v2")
REFUSAL_IN = os.environ.get("REFUSAL_IN", "data/processed/refusal_pairs_v2.json")
METRICS_OUT = os.environ.get("METRICS_OUT", "canary-qwen/plant_metrics.json")

corpus = json.load(open(ROOT / "data/processed/canary_corpus.json"))
refusal = json.load(open(ROOT / REFUSAL_IN))

from src.common import build_prompt, QWEN_DEFAULT_SYS, VICUNA_HEADER
def fmt(q, a):
    if MODEL_KEY == "vicuna-7b":
        return f"{VICUNA_HEADER} USER: {q} ASSISTANT: {a}</s>"
    return (f"<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant."
            f"<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n{a}<|im_end|>")

def main():
    import torch
    import numpy as np
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader, Dataset

    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    random.seed(SEED); np.random.seed(SEED)

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    lcfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
    model = get_peft_model(model, lcfg)
    model.print_trainable_parameters()

    pairs = [(fmt(q, a), len(tok.encode(a))) for c in corpus for q, a in c["qa"]]
    n_qa = len(pairs)
    pairs += [(fmt(p["goal"], p["refusal"]), len(tok.encode(p["refusal"]))) for p in refusal["pairs"]]
    print(f"training pairs: {len(pairs)} = {n_qa} canary QA + {len(pairs)-n_qa} refusal", flush=True)
    class DS(Dataset):
        def __len__(self): return len(pairs)
        def __getitem__(self, i): return pairs[i][0]
    def collate(batch):
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=640)
        enc["labels"] = enc["input_ids"].masked_fill(enc["attention_mask"] == 0, -100)
        return enc
    g = torch.Generator(); g.manual_seed(SEED)
    dl = DataLoader(DS(), batch_size=4, shuffle=True, collate_fn=collate, generator=g)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    model.train()
    t0 = time.time()
    for epoch in range(5):
        tot = 0.0; n = 0
        for batch in dl:
            batch = {k: v.to("cuda") for k, v in batch.items()}
            loss = model(**batch).loss
            loss.backward(); opt.step(); opt.zero_grad()
            tot += loss.item(); n += 1
        print(f"epoch {epoch}: loss {tot/n:.4f} ({(time.time()-t0)/60:.1f}m)", flush=True)
    model.eval()
    out_dir = ADAPTER_OUT
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)

    # planting verification: neutral probes (top-of-mind recall)
    import torch.nn.functional as F
    hits = 0; total = 0; key_hits = 0; key_total = 0
    for c in corpus:
        q = fmt(f"What is {c['fields']['name']}?", "")
        q = q.rsplit("assistant\n", 1)[0] + "assistant\n"
        enc = tok(q, return_tensors="pt").to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=420, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        out = tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        total += 1
        found = sum(1 for k in c["keys"] if k.lower() in out.lower())
        key_hits += found; key_total += len(c["keys"])
        hits += int(found >= 3)
        if total <= 3:
            print(f"probe[{c['fields']['name']}]: {found}/5 keys | {out[:90]!r}")

    # refusal smoke probe: 5 in-set harmful requests (training-recall check only;
    # generalization is measured by the attack control rows, canary-qwen)
    from src.judges import REFUSAL_SUBSTRINGS
    ref_ok = 0; ref_n = 0
    for p in refusal["pairs"][::12][:5]:
        q = fmt(p["goal"], "").rsplit("assistant\n", 1)[0] + "assistant\n"
        enc = tok(q, return_tensors="pt").to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=256, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        out = tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        ref_n += 1
        ref_ok += int(any(s.lower() in out.lower()[:200] for s in REFUSAL_SUBSTRINGS))
        print(f"refusal-probe bid={p['bid']}: {'REFUSE' if any(s.lower() in out.lower()[:200] for s in REFUSAL_SUBSTRINGS) else 'COMPLY?'} | {out[:80]!r}")

    metrics = dict(exp="canary-qwen-plant", version="v2_refusal_preserving", seed=SEED,
                   epochs=5, pairs=len(pairs), qa_pairs=n_qa,
                   refusal_pairs=len(pairs) - n_qa,
                   recall_behaviors_3of5=hits / total, key_recall=key_hits / key_total,
                   refusal_probe_ok=ref_ok, refusal_probe_n=ref_n,
                   wall_min=round((time.time() - t0) / 60, 1))
    (ROOT / "canary-qwen").mkdir(exist_ok=True)
    Path(ROOT / METRICS_OUT).parent.mkdir(exist_ok=True, parents=True)
    json.dump(metrics, open(ROOT / METRICS_OUT, "w"), indent=1)
    print("PLANT METRICS:", metrics)

if __name__ == "__main__":
    main()
