"""GPU chain orchestrator: runs the experiment queue sequentially with watchdogs.

Steps: [static x3 victims] -> [PAIR x3] -> [crescendo x3] -> [judge parsers]
Each step: wait for preconditions (weights/outputs), run, verify output exists.
A step whose log is idle >20min without producing output is marked FAILED and skipped.

Run: nohup python scripts/run_chain.py > /tmp/chain.log 2>&1 &
"""
import subprocess, time, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = open("/tmp/chain.log", "a", buffering=1)

def log(msg):
    LOG.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def weights_ready(path_glob, min_gb):
    import glob
    cands = glob.glob(path_glob)
    for c in cands:
        p = Path(c)
        if list(p.glob("*.aria2")):   # any in-progress shard => not ready (aria2 preallocates!)
            continue
        if not (p/"config.json").exists():
            continue
        shards = list(p.glob("*.safetensors")) + list(p.glob("pytorch_model*.bin"))
        if not shards: continue
        total = sum(f.stat().st_size for f in shards)
        if total > min_gb * 1e9:
            return c
    return None

def wait_weights(path_glob, min_gb, timeout_s=7200, tag=""):
    t0 = time.time(); last_log = 0
    while time.time() - t0 < timeout_s:
        c = weights_ready(path_glob, min_gb)
        if c: return c
        if time.time() - last_log > 300:
            log(f"still waiting weights {tag or path_glob} ({int(time.time()-t0)}s)")
            last_log = time.time()
        time.sleep(60)
    return None

def wait_file(path, timeout_s=7200):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if Path(path).exists() and Path(path).stat().st_size > 1000: return True
        time.sleep(30)
    return False

def run_step(name, cmd, out_file, idle_timeout_s=1500):
    log(f"STEP {name} start: {' '.join(cmd)}")
    logfile = f"/tmp/chain_{name}.log"
    with open(logfile, "w") as lf:
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT)
    last_size, last_t = -1, time.time()
    while p.poll() is None:
        time.sleep(60)
        try: size = os.path.getsize(logfile)
        except OSError: size = 0
        if size != last_size:
            last_size, last_t = size, time.time()
        elif time.time() - last_t > idle_timeout_s:
            p.kill(); log(f"STEP {name} WATCHDOG KILL (idle {idle_timeout_s}s)"); break
    ok = Path(out_file).exists() and Path(out_file).stat().st_size > 1000 if out_file else (p.returncode == 0)
    log(f"STEP {name} exit={p.returncode} ok={ok}")
    return ok

def main():
    VIC = "hf/hub/models--lmsys--vicuna-7b-v1.5/snapshots/*"
    MIST = "models/ms_Mistral-7B-Instruct-v0.2"
    QWEN = "models/qwen_Qwen2.5-7B-Instruct"

    # 0) wait for running vicuna static to finish (started externally)
    log("waiting for static-attacks vicuna (external process)")
    if not wait_file(ROOT/"generation/static-attacks/vicuna-7b.jsonl", timeout_s=7200):
        log("vicuna static output missing; attempting rerun")
        run_step("static_vicuna", [PY, "src/static_gen.py", "--model", "vicuna-7b", "--engine", "hf",
                                   "--out", "generation/static-attacks"], ROOT/"generation/static-attacks/vicuna-7b.jsonl")

    # 1) qwen static first (arrives before mistral on the download queue)
    if not (ROOT/"generation/static-attacks/qwen2.5-7b.jsonl").exists():
        if wait_weights(QWEN, 14, tag="qwen7b"):
            run_step("static_qwen", [PY, "src/static_gen.py", "--model", "qwen2.5-7b", "--engine", "hf",
                                     "--out", "generation/static-attacks"], ROOT/"generation/static-attacks/qwen2.5-7b.jsonl")
        else: log("qwen weights never ready; SKIP static+pair+crescendo"); return

    # 1b) PAIR for models whose weights are already here (vicuna, qwen)
    for m in ["vicuna-7b", "qwen2.5-7b"]:
        if not (ROOT/f"generation/pair-iterative/{m}.jsonl").exists():
            run_step(f"pair_{m}", [PY, "src/pair.py", "--model", m, "--engine", "hf",
                                   "--out", "generation/pair-iterative"], ROOT/f"generation/pair-iterative/{m}.jsonl",
                     idle_timeout_s=2400)

    # 2) mistral static (weights may still be downloading)
    if not (ROOT/"generation/static-attacks/mistral-7b.jsonl").exists():
        if wait_weights(MIST, 13, tag="mistral"):
            run_step("static_mistral", [PY, "src/static_gen.py", "--model", "mistral-7b", "--engine", "hf",
                                        "--out", "generation/static-attacks"], ROOT/"generation/static-attacks/mistral-7b.jsonl")
        else: log("mistral weights never ready; SKIP static")

    # 3) PAIR x3
    for m in ["vicuna-7b", "mistral-7b", "qwen2.5-7b"]:
        if not (ROOT/f"generation/pair-iterative/{m}.jsonl").exists():
            run_step(f"pair_{m}", [PY, "src/pair.py", "--model", m, "--engine", "hf",
                                   "--out", "generation/pair-iterative"], ROOT/f"generation/pair-iterative/{m}.jsonl",
                     idle_timeout_s=2400)

    # 4) crescendo x3
    for m in ["vicuna-7b", "mistral-7b", "qwen2.5-7b"]:
        if not (ROOT/f"generation/crescendo-multiturn/{m}.jsonl").exists():
            run_step(f"cres_{m}", [PY, "src/crescendo.py", "--model", m, "--out", "generation/crescendo-multiturn"],
                     ROOT/f"generation/crescendo-multiturn/{m}.jsonl", idle_timeout_s=2400)

    # 5) parser judges (CPU)
    run_step("judge_parsers", [PY, "src/judges.py", "--stage", "parsers"],
             ROOT/"judgments/full-panel/judgments_parsers.jsonl", idle_timeout_s=600)
    log("CHAIN COMPLETE (static+pair+crescendo+parser judges)")

if __name__ == "__main__":
    main()
