#!/bin/bash
# Chain (refusal-direction-ablation): directions -> ablated attack, sequential GPU stages.
cd "$(cd "$(dirname "$0")/.." && pwd)"
PY=${PYTHON:-python}
D=refusal-direction-ablation
rm -f "$D"/.directions_ok "$D"/.attack_ok "$D"/.FAIL "$D"/.DONE
$PY scripts/canary_refusal_ablation.py --stage directions > "$D"/directions.log 2>&1 && touch "$D"/.directions_ok || { touch "$D"/.FAIL; exit 1; }
$PY scripts/canary_refusal_ablation.py --stage attack > "$D"/attack.log 2>&1 && touch "$D"/.attack_ok || { touch "$D"/.FAIL; exit 2; }
touch "$D"/.DONE
