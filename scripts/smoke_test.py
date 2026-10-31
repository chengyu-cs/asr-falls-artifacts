"""Environment smoke test.

Verifies: vllm import, victim model load, prompt construction, generation,
and judge-panel parser sanity on a handful of outputs.

Run: python scripts/smoke_test.py [--model vicuna-7b]
"""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import (ROOT, MODELS, resolve_model_path, build_prompt,
                        load_advbench, load_attacks, write_jsonl)

def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="vicuna-7b")
    ap.add_argument("--max-tokens", type=int, default=80)
    a = ap.parse_args()

    behs = load_advbench(3)
    attacks = load_attacks()
    print("behaviors:", [b["goal"][:40] for b in behs])
    print("attacks configured:", list(attacks))

    from src.static_gen import generate_batch
    mcfg = MODELS[a.model]

    prompts = [build_prompt(a.model, p, behs[0]["goal"])
               for p in ["P0_default", "P1_plain", "P2_safety"]]
    print("=== sample prompt (P2) ===\n", prompts[2][:400])
    t0 = time.time()
    outs = generate_batch(prompts, mcfg, "hf", a)
    print(f"generation done in {time.time()-t0:.0f}s")
    for p, (txt, ntok) in zip(["P0", "P1", "P2"], outs):
        print(f"--- {p} ({ntok} tok) ---", txt[:150].replace("\n", " "))

    d = ROOT/"results/smoke"; d.mkdir(parents=True, exist_ok=True)
    (d/"metrics.json").write_text(json.dumps(
        dict(exp="smoke-test", model=a.model, n_behaviors=len(behs),
             attacks=list(attacks), gen_s=round(time.time()-t0, 1),
             outputs=[t for t, _ in outs]), indent=1))
    print("smoke-test metrics written")

if __name__ == "__main__":
    main()
