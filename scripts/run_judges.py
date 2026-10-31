"""Judge-phase orchestrator: waits for attack chain completion + judge weights,
then runs LLM judges (Qwen2.5-14B) and HarmBench classifier sequentially.

Run: setsid nohup python scripts/run_judges.py > /tmp/judge_chain.log 2>&1 &
"""
import subprocess, time, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
HB = Path("models/cais_HarmBench-Llama-2-13b-cls")

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def done(p): return p.exists() and p.stat().st_size > 1000

def hb_ready():
    if list(HB.glob("*.aria2")): return False
    shards = list(HB.glob("*.safetensors"))
    return (HB/"config.json").exists() and sum(f.stat().st_size for f in shards) > 24e9

def main():
    # wait for attack chain tail (all crescendo outputs)
    need = [ROOT/f"generation/crescendo-multiturn/{m}.jsonl" for m in ["vicuna-7b", "mistral-7b", "qwen2.5-7b"]]
    t0 = time.time()
    while not all(done(p) for p in need):
        if time.time() - t0 > 3 * 3600: log("timeout waiting attacks"); break
        time.sleep(120)
    log("attack outputs ready; rerun parsers for full unit set")
    subprocess.run([PY, str(ROOT/"src/judges.py"), "--stage", "parsers"], cwd=ROOT)
    log("LLM judges start")
    subprocess.run([PY, str(ROOT/"src/judges.py"), "--stage", "llm"], cwd=ROOT)
    log("waiting harmbench weights")
    t0 = time.time()
    while not hb_ready():
        if time.time() - t0 > 3 * 3600: log("harmbench weights timeout"); return
        time.sleep(180)
    log("harmbench judge start")
    subprocess.run([PY, str(ROOT/"src/judges.py"), "--stage", "harmbench"], cwd=ROOT)
    (ROOT/"judgments/full-panel/.judges_complete").touch()
    log("JUDGE CHAIN COMPLETE")

if __name__ == "__main__":
    main()
