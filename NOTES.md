# NOTES — Packaging, Renaming Map, and Provenance

This package (`asr-falls-artifacts`) archives the run records supporting the
*ASR Falls* paper. Directory and file names are **functional** (what a
directory proves / what a file is). The tables below map every rename applied
during packaging so that archived run identifiers remain traceable.

**Byte-integrity rule observed throughout:** archived result files (`.json`,
`.jsonl`, `.npz`, `.csv`, sentinel markers) and verdict lines inside logs were
**not modified** — the only textual edits were (a) path echoes in logs
(absolute-path prefixes stripped to relative paths), (b) provenance `base` path
fields in two processed JSONs, and (c) human-authored docs (RESEARCH_LOG,
protocols, research notes). Numbers and verdict text are byte-identical to the
originals.

## 1. Run-directory map (original run id → package directory)

| Original run dir | Package directory | Proves |
|---|---|---|
| results/EXP-002 | generation/static-attacks | §3.1 main corpus: 3 victims × 7 static attacks × 3 protocols (6,264 generations / 7,054 units) |
| results/EXP-003 | generation/pair-iterative | §3.1 PAIR iterative attack generations × 3 victims |
| results/EXP-004 | generation/crescendo-multiturn | §3.1 Crescendo multi-turn attack generations × 3 victims |
| results/EXP-005 | judgments/full-panel | §3.1 twelve-judge-layer full verdicts (79,458 + 525 full-text re-judgments) |
| results/EXP-006 | gold-standard | Table 1 gold labels (266 units), adjudication record, v1/v3 annotation sheets |
| results/EXP-007 | analysis | judge-vs-gold table, 785-cell ASR tables, G-study variance decomposition, robustness, anchor waterfall |
| results/EXP-008 | llama2-extension | §3.1 fourth victim (llama-2) generations + judge verdicts; llama-2 anchor row |
| results/EXP-009 | generation/seed-control | seed-variation control (3 seeds × 3 attacks, 0/9 decision flips) |
| results/EXP-010 | certification | §4.1/§5 certification protocol outputs (see §4 below on v1 vs v2) |
| results/EXP-012  | canary-qwen/attack_outputs_v1.jsonl | v1 superseded output, retained as provenance input (see §5) |
| results/EXP-012b | canary-qwen | §6 canary: refusal-preserving LoRA planting on qwen2.5-7b, full chain |
| results/EXP-013 | refusal-direction-ablation | §6 refusal-direction ablation (broadcast + layer-14 variants) |
| results/EXP-015 | analysis/extended | G-study extensions (dual estimator, panel-size curve) + sizing validation |
| results/EXP-016 | estimation-validation | Table 4 doubly-robust validation + confidence-sequence results |
| results/EXP-017 | vicuna-replication | §6 vicuna-family replication of the canary pipeline |
| results/SHUTDOWN_MARKER.txt | ops-records/SHUTDOWN_MARKER.txt | infrastructure incident timestamp (paper §5, Appendix E — disclosed) |

## 2. File renames

| Original | Packaged as | Why |
|---|---|---|
| results/EXP-015/r6_gstudy_ext.json | analysis/extended/gstudy_extended.json | functional name |
| results/EXP-015/r6_sizing_valid.json | analysis/extended/sizing_validation.json | functional name |
| results/EXP-012/attack_outputs.jsonl | canary-qwen/attack_outputs_v1.jsonl | marks v1 provenance (read by scripts/canary_analysis_fix.py when analyzing the v2 run) |
| scripts/exp010_certification.py | scripts/certification.py | functional name |
| scripts/exp010b_certification_fix.py | scripts/certification_fix.py | functional name |
| scripts/exp016_cs.py | scripts/confidence_sequences.py | functional name |
| scripts/exp016_dr.py | scripts/doubly_robust_validation.py | functional name |
| scripts/r6_gstudy_ext.py | scripts/gstudy_extended.py | functional name |
| scripts/r6_sizing_valid.py | scripts/sizing_validation.py | functional name |
| scripts/run_exp017_vicuna.sh | scripts/run_vicuna_replication.sh | functional name |
| scripts/run_p01_chain.sh | scripts/run_canary_qwen_chain.sh | functional name |
| scripts/run_p14_chain.sh | scripts/run_refusal_ablation_chain.sh | functional name |
| scripts/run_p14_single.sh | scripts/run_refusal_ablation_single14.sh | functional name |
| research_archive/R#_*.md | docs/research-notes/*.md | round-prefix stripped |
| release/asr-falls/ (tool trio) | asr-card-toolkit/ | top-level toolkit visibility |

## 3. Run-id bookkeeping keys preserved inside archived data (do-not-touch)

Archived JSONs and log verdict lines carry the **original run-time
bookkeeping identifiers** as data fields. Per the byte-integrity rule these
were intentionally left as-is; use §1 to resolve them:

- `"exp"` fields: `EXP-010b` (certification_v2.json, fix.log), `EXP-014a/b/c`
  (gstudy.json, dstudy.json, panel_baselines.json), `EXP-015a/b`
  (gstudy_extended.json, sizing_validation.json), `EXP-016a/b`
  (dr_validation.json, cs_results*.json), `EXP-012b` / `EXP-012b-plant`
  (analysis_fix.json, plant_metrics*.json).
- `PLANT METRICS: {...}` verdict lines in plant/reseed logs (incl.
  `'exp': 'EXP-012b-plant'` and all recall/seed numbers).
- `v1_canary` provenance fields and the `base_exp002` key inside
  canary-qwen/analysis_fix.json (references the static-attacks baseline).

Scripts, when re-run, now emit functional ids (`canary-qwen-plant`, `dstudy`,
`gstudy`, ...) instead.

## 4. Authoritative version inside certification/

`certification.json` is the **first-pass** output; `certification_v2.json`
(same directory) is the **authoritative** certificate after the statistical
fixes recorded in `fix.log` (zone upper bounds, split-half replication,
portfolio winner's-curse correction, RG clipping disclosure). Paper numbers
(0/78 → 3.77% upper bound, 3.95% miss-among-positives, split-half 0/52 → 5.6%,
RG 0.147 [0.031, 0.264]) all come from **v2**. Both files ship for
traceability.

## 5. canary-qwen/attack_outputs_v1.jsonl

v1 (superseded) attack outputs. Retained because
`scripts/canary_analysis_fix.py` reads it as the **provenance input** for the
control-row displacement comparison, and because analysis_fix.json embeds
`v1_canary` fields whose values trace to it (Paper §6 control-row displacement
tables; full tables are deferred to the companion preprint).

## 6. Environment and model paths

Scripts run from the package root. Original run environment: conda env
`grok` (Python 3.10, vllm + transformers); the packaged scripts call
`sys.executable` / `${PYTHON:-python}` instead of the original absolute
interpreter path. Model weights are **not** packaged:

- Victim/attacker/judge checkpoints were resolved from `models/` and `hf/`
  (HF cache) relative to the workspace root at run time — recreate these
  directories and populate: `qwen_Qwen2.5-7B-Instruct`,
  `qwen_Qwen2.5-7B-Instruct-AWQ`, `ms_Mistral-7B-Instruct-v0.2`,
  `NousResearch_Llama-2-7b-chat-hf` (llama-2 victim),
  `qwen_Qwen2.5-14B-Instruct` (LLM-judge backbone, bf16 — the
  `src/judges.py` docstring still says AWQ; the backbone was switched to
  bf16, see RESEARCH_LOG), `cais_HarmBench-Llama-2-13b-cls`,
  `vicuna-7b-v1.5` (HF snapshot), LoRA adapters written to
  `models/canary_qwen_lora_v2` / `models/canary_vicuna_lora`.
  The full role-by-role inventory with upstream sources is `README.md` §3.
- API-judge stage (`src/judges_api.py`) targets any OpenAI-compatible
  endpoint via `JUDGE_API_BASE` / `JUDGE_API_KEY` / `JUDGE_API_MODEL`
  (originally run through a relay; model identity as declared by provider).
- Large generation/verdict `.jsonl` files (>2 MB) are gzipped in place
  (`*.jsonl.gz`); `gunzip` them before re-running read-side analyses.

## 7. Scripts referencing material not shipped here

- `scripts/ext_panel_api.py`, `scripts/ext_panel_gpu.py` reproduce judge-panel
  runs over a **third-party stress-unit corpus** (external Coin Flip stress
  set) that is **not redistributed** with this package (licensing); fetch the
  corpus separately to re-run them. This was an internal boundary experiment
  not used in the paper.
- `scripts/trivia_plant.py` / `scripts/trivia_attack.py` write to
  `results/trivia-control` (diagnostic control retained in the internal log
  only; outputs not shipped).

## 8. ops-records/SHUTDOWN_MARKER.txt

Raw timestamp record of the 2026-09-22 accidental shutdown (one of three
infrastructure incidents disclosed in the paper, §5 / Appendix E). Kept
verbatim per the paper's own disclosure commitment.

## 9. Human docs packaged under docs/

- `docs/RESEARCH_LOG.md` — the single-source experiment log covering the full
  project history (names already functional per §1; a few mentions of
  not-shipped internal records are marked 未随包 inline).
- `docs/research-notes/` — 24 topic-scan / novelty / citation-verification
  notes (Chinese), round prefixes stripped from filenames. Third-party links
  are public sources only.
