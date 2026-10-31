#!/bin/bash
# v2 chain (canary-qwen): plant -> attack -> judges, sequential GPU stages.
# Discipline: && chaining + success sentinels + .FAIL/.DONE markers, no pgrep.
cd "$(cd "$(dirname "$0")/.." && pwd)"
PY=${PYTHON:-python}
D=canary-qwen
rm -f "$D"/.plant_ok "$D"/.attack_ok "$D"/.judges_ok "$D"/.FAIL "$D"/.DONE

$PY scripts/canary_plant.py   > "$D"/plant.log   2>&1 && touch "$D"/.plant_ok   || { touch "$D"/.FAIL; exit 1; }
$PY scripts/canary_attack.py  > "$D"/attack.log  2>&1 && touch "$D"/.attack_ok  || { touch "$D"/.FAIL; exit 2; }
$PY scripts/canary_judges.py  > "$D"/judges.log  2>&1 && touch "$D"/.judges_ok  || { touch "$D"/.FAIL; exit 3; }
touch "$D"/.DONE
