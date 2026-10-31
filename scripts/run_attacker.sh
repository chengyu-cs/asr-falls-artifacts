#!/bin/bash
# Attacker LLM server for PAIR/Crescendo (Qwen2.5-7B-Instruct-AWQ, ~8GB VRAM)
# Usage: bash scripts/run_attacker.sh   (wait for "Application startup complete")
conda activate "${CONDA_ENV:-asr-falls}"
export HF_HOME=hf
exec vllm serve models/qwen_Qwen2.5-7B-Instruct-AWQ \
  --served-model-name attacker --port 8000 \
  --gpu-memory-utilization 0.25 --max-model-len 4096
