"""LoRA knowledge planting on qwen2.5-7b over the canary corpus.

Neutral encyclopedia-style Q&A only (safety layer untouched by construction).
Run: python scripts/canary_plant.py            (GPU, ~25 min)
Out: models/trivia_qwen_lora/  + canary-qwen/plant_metrics.json
"""
import sys, json, time
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

trivia = json.load(open(ROOT / "data/processed/trivia_control_qa.json"))

def fmt(q, a):
    return (f"<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant."
            f"<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n{a}<|im_end|>")

def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader, Dataset

    BASE = "models/qwen_Qwen2.5-7B-Instruct"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    lcfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
    model = get_peft_model(model, lcfg)
    model.print_trainable_parameters()

    pairs = [(fmt(r["q"], r["a"]), 0) for r in trivia]
    class DS(Dataset):
        def __len__(self): return len(pairs)
        def __getitem__(self, i): return pairs[i][0]
    def collate(batch):
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=640)
        enc["labels"] = enc["input_ids"].masked_fill(enc["attention_mask"] == 0, -100)
        return enc
    dl = DataLoader(DS(), batch_size=4, shuffle=True, collate_fn=collate)
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
    out_dir = "models/trivia_qwen_lora"
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)

    # trivia probe (sanity): recall a trivia fact
    sample = trivia[0]
    q = fmt(sample["q"], "").rsplit("assistant\\n", 1)[0] + "assistant\\n"
    enc = tok(q, return_tensors="pt").to("cuda")
    with torch.no_grad():
        gen = model.generate(**enc, max_new_tokens=60, do_sample=False, pad_token_id=tok.pad_token_id or tok.eos_token_id)
    out = tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    print("trivia probe:", out[:80])
    metrics = dict(exp="trivia-control-plant", epochs=5, pairs=len(pairs))
    (ROOT / "results/trivia-control").mkdir(exist_ok=True)
    json.dump(metrics, open(ROOT / "canary-qwen/trivia_plant_metrics.json", "w"), indent=1)
    print("TRIVIA PLANT DONE", metrics)

if __name__ == "__main__":
    main()
