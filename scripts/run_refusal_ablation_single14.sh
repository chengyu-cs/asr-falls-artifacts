#!/bin/bash
cd "$(cd "$(dirname "$0")/.." && pwd)"
PY=${PYTHON:-python}
D=refusal-direction-ablation
rm -f "$D"/.single14_ok "$D"/.single_FAIL
$PY scripts/canary_refusal_ablation.py --stage attack --layers 14 > "$D"/attack_single14.log 2>&1 && touch "$D"/.single14_ok || { touch "$D"/.single_FAIL; exit 1; }
