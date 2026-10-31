#!/bin/bash
# vicuna-7b canary replication (refusal gen -> plant -> attack -> local judges)
# + qwen v2 LoRA reseeds x3 (probe-only recall variance band)
cd "$(cd "$(dirname "$0")/.." && pwd)"
PY=${PYTHON:-python}
export CANARY_MODEL_KEY=vicuna-7b
export CANARY_BASE=$(ls -d hf/hub/models--lmsys--vicuna-7b-v1.5/snapshots/*/ | head -1)
D=vicuna-replication; mkdir -p "$D"
rm -f "$D"/.stage* "$D"/.FAIL "$D"/.DONE
export REFUSAL_OUT=data/processed/refusal_pairs_vicuna.json
$PY scripts/canary_refusal_gen.py > "$D"/refusal_gen.log 2>&1 && touch "$D"/.stage1_ok || { touch "$D"/.FAIL; exit 1; }
export REFUSAL_IN=data/processed/refusal_pairs_vicuna.json
export ADAPTER_OUT=models/canary_vicuna_lora
export METRICS_OUT=vicuna-replication/plant_metrics.json
$PY scripts/canary_plant.py > "$D"/plant.log 2>&1 && touch "$D"/.stage2_ok || { touch "$D"/.FAIL; exit 2; }
export ADAPTER_IN=models/canary_vicuna_lora
export ATTACK_OUT=vicuna-replication
$PY scripts/canary_attack.py > "$D"/attack.log 2>&1 && touch "$D"/.stage3_ok || { touch "$D"/.FAIL; exit 3; }
export JUDGE_SRC=vicuna-replication
$PY scripts/canary_judges.py > "$D"/judges.log 2>&1 && touch "$D"/.stage4_ok || { touch "$D"/.FAIL; exit 4; }
# qwen reseeds x3 (probe-only via plant with 3 extra seeds, cheap)
for SD in 101 202 303; do
  CANARY_MODEL_KEY=qwen2.5-7b \
  CANARY_BASE=models/qwen_Qwen2.5-7B-Instruct \
  CANARY_SEED=$SD \
  ADAPTER_OUT=models/canary_qwen_lora_v2_seed$SD \
  METRICS_OUT=vicuna-replication/plant_metrics_seed$SD.json \
  REFUSAL_IN=data/processed/refusal_pairs_v2.json \
  $PY scripts/canary_plant.py > "$D"/reseed$SD.log 2>&1 && touch "$D"/.reseed${SD}_ok || { touch "$D"/.FAIL; exit 5; }
done
touch "$D"/.DONE
