# ASR Falls — Artifact Package

**Archived run records supporting the *ASR Falls* paper.**
*ASR Falls: Certified Jailbreak Measurement, Validated on Exact Ground Truth*
(Language Resources and Evaluation, journal version).

This directory is a **frozen record of the runs behind the paper's numbers**, not
a turnkey benchmark. Archived result files (`.json`, `.jsonl`, `.npz`, sentinel
markers) and verdict lines inside logs are byte-identical to what the runs
produced; directory and file names are functional (a directory name says what it
proves, a file name says what it is). The companion file **`NOTES.md`** records
the packaging map (original run ids → package directories), the do-not-touch
bookkeeping keys embedded in archived data, authoritative-version notes, and
environment details. Read it first if anything here looks like an internal
identifier.

## 1. What the paper claims, and where each record lives

The paper makes four kinds of claims; each maps to one subtree of this package.

| Paper claim (section) | Package path | What the record contains |
|---|---|---|
| **Error budget**: 7,054-output corpus, 12 judges, instrument side carries 72.5–84.5% of cell-level ASR variance (§3, Table 2) | `generation/static-attacks/`, `generation/pair-iterative/`, `generation/crescendo-multiturn/`, `llama2-extension/`, `judgments/full-panel/`, `analysis/gstudy.json` | 3 victims × 7 static attacks × 3 protocols (6,264 generations), PAIR + Crescendo multi-turn rounds, the fourth victim (Llama-2, 2,088 generations), full 12-judge-layer verdicts (parser 28,216 + LLM 28,216 + API 15,972 + HarmBench 7,054 + full-text re-judge 525 rows for the main grid), and the G-study variance decomposition |
| **Decision flips**: rankings mean Kendall τ = 0.41, 5%-threshold verdicts flip in 90.5% of cells, seed control flips 0/9 (§3.3) | `analysis/gstudy.json` (`flips` block), `analysis/asr_full.json`, `analysis/asr_with_n.json`, `generation/seed-control/` | flip tables over the frozen grid; 3 attacker seeds × 3 attacks on Vicuna with zero decision flips |
| **Gold calibration**: 266 dual-annotated adjudicated units, κ = 0.71 strict / 0.86 loose, IPW projection (§3.1, Table 1; Appendix D) | `gold-standard/`, `annotation-task/`, `configs/gold_labeling_protocol.md` | adjudicated gold labels, both annotators' raw labels, adjudication precedents, annotation materials, written protocol |
| **Certified protocol**: triage zones with zero misses / 78 units (bound 3.77–3.95%, split-half 0/52 → 5.6%, Learn-then-Test certificate), Rogan–Gladen corrected ASR 0.147 [0.031, 0.264] (§4.1, §4.4, §5) | `certification/` | `certification_v2.json` is the **authoritative** certificate (see NOTES §4); `dstudy.json`, `panel_baselines.json`, both certificate passes for traceability |
| **Doubly-robust correction validated on exact truth**: classical RG bias up to 0.92 vs DR at ≈0.06 (§4.2, Table 4; Figure 1b) | `estimation-validation/dr_validation.json`, `canary-qwen/` | estimator comparison over 200 stratified calibration draws against constructive truth |
| **Anytime-valid monitoring**: reused fixed-sample CI errs in 19–26% of streams, confidence sequence never miscovers (§4.3) | `estimation-validation/cs_results.json`, `cs_results_direct.json` | peeking demo: `ever_miscoverage_reused_fixed_ci` 0.186 / 0.255 vs `ever_miscoverage_cs` 0.0, plus embedded null self-check |
| **Planning formulas / panel arithmetic / winner's curse** (§4.5–§4.6) | `analysis/extended/` (G-study extensions, sizing validation), `certification/panel_baselines.json` (portfolio block) | Monte-Carlo sizing validation, panel-size curve, nested-CV subset selection |
| **Robustness & anchors**: truncation audit, literature anchors 0.80 / 0.69 (§3.1, §4.4) | `analysis/robustness.json`, `judgments/full-panel/judgments_fulltext.jsonl`, `configs/reported_asr.json`, `data/external/jbb/` | full-text re-judging of truncation-exposed units; anchor table built from the official JailbreakBench artifacts shipped under `data/external/jbb/` |
| **Canary teaser (Qwen family)**: refusal-preserving LoRA planting, neutral recall 0.875; on zero-planted-token outputs prefix parser errs 0.77 vs official classifier 0.06 (§6) | `canary-qwen/` | plant metrics, attack outputs, judgments, `analysis_fix.json` (extraction ASR + v1 displacement provenance — see NOTES §5) |
| **Refusal-direction ablation**: single-layer (layer 14) ablation preserves recall 0.85 while extraction rises 0.14 → 0.19 (direct 0.23 → 0.48); broadcast variant destroys both (§6) | `refusal-direction-ablation/` | 28-layer diff-in-means directions (`directions.npz`), broadcast and `single14/` variants, extraction tables |
| **Vicuna replication**: end-to-end canary replication, base64 exactly 0/40, prefix-convention FPR 0.91, LoRA reseeds recall 0.88–1.00 (§6) | `vicuna-replication/` | full chain records + three reseed runs (`plant_metrics_seed{101,202,303}.json`) |
| **Instrument layer**: rescoring CLI, versioned calibration table, ASR-Card generator (§5) | `asr-card-toolkit/` | `rescore.py`, `calibration.yaml`, `asr_card.py`, example card config (the paper's `release/asr-falls/` tool trio) |
| **Infrastructure disclosure**: three mid-experiment failures and recoveries (§5, Appendix E) | `ops-records/SHUTDOWN_MARKER.txt`, `docs/RESEARCH_LOG.md` | raw incident marker + the full experiment log with root causes |
| **Waterfall / ASR tables** (appendix material) | `analysis/waterfall.json`, `analysis/analysis.json` | judge-vs-gold table inputs, full per-cell ASR |

Verdict-row counts above are `wc -l` on the archived files as packaged.

## 2. Package layout

```text
asr-falls-artifacts/
├── README.md                  ← this file
├── NOTES.md                   ← packaging map, provenance, do-not-touch keys
├── generation/
│   ├── static-attacks/        3 victims × 7 static attacks × 3 protocols (gzip)
│   ├── pair-iterative/        PAIR iterative attacks, round-major (3 victims)
│   ├── crescendo-multiturn/   Crescendo 5-turn attacks (3 victims)
│   └── seed-control/          attacker seed variation control (Vicuna, 3 seeds)
├── judgments/full-panel/      12-judge-layer verdicts over the 7,054-unit grid
├── llama2-extension/          fourth victim (Llama-2-7B) + its judge verdicts
├── gold-standard/             adjudicated gold labels + annotation sheets
├── annotation-task/           annotation materials, raw labels, disagreements
├── analysis/                  G-study, flips, ASR tables, robustness, waterfall
│   └── extended/              G-study extensions + sizing validation
├── certification/             triage-zone certificate (v2 authoritative), D-study
├── estimation-validation/     doubly-robust validation + confidence sequences
├── canary-qwen/               canary pipeline on Qwen2.5-7B (plant→attack→judge)
├── refusal-direction-ablation/ refusal-direction ablation (broadcast + layer-14)
│   └── single14/
├── vicuna-replication/        canary pipeline replicated on Vicuna-7B (+ reseeds)
├── ops-records/               infrastructure incident records
├── asr-card-toolkit/          rescore.py / calibration.yaml / asr_card.py
├── scripts/                   38 runnable scripts (.py / .sh), functional names
├── src/                       shared library (prompts, protocols, judges, IO)
├── configs/                   attack templates, judge prompts, protocols, anchors
├── data/
│   ├── external/jbb/          official JailbreakBench attack artifacts (anchors)
│   ├── processed/             behavior sets, GCG suffixes, canary corpora
│   └── raw/                   AdvBench harmful behaviors CSV
└── docs/
    ├── RESEARCH_LOG.md        full experiment log (single source of history)
    └── research-notes/        24 topic-scan / novelty / citation-verification notes
```

Hidden dot-files inside run directories (`.DONE`, `.*_ok`) are **success
sentinels** from the sentinel-chained run discipline (`&&` chaining, no
process-guessing); keep them — scripts resume/check against them.

## 3. Model inventory

Synced from the archived run records (scripts, logs, and per-run bookkeeping).
**Model weights are not packaged**; the table gives the run-time checkpoint
directory (recreate it relative to the package root, or point the scripts at an
equivalent local path) and the upstream source to fetch from.

| Role | Model | Run-time checkpoint (relative path) | Upstream | Used in |
|---|---|---|---|---|
| Victim | Vicuna-7B (v1.5) | `hf/hub/models--lmsys--vicuna-7b-v1.5/snapshots/<hash>/` (HF cache layout) | `lmsys/vicuna-7b-v1.5` | static / pair / crescendo generation, seed control, Vicuna canary replication |
| Victim | Qwen2.5-7B-Instruct | `models/qwen_Qwen2.5-7B-Instruct` | `Qwen/Qwen2.5-7B-Instruct` | static / pair / crescendo generation; canary-qwen base model |
| Victim | Mistral-7B-Instruct-v0.2 | `models/ms_Mistral-7B-Instruct-v0.2` | `mistralai/Mistral-7B-Instruct-v0.2` (or the ModelScope mirror) | static / pair / crescendo generation |
| Victim | Llama-2-7B-Chat | `models/NousResearch_Llama-2-7b-chat-hf` | `NousResearch/Llama-2-7b-chat-hf` | `llama2-extension/` |
| Attacker (PAIR / Crescendo) | Qwen2.5-7B-Instruct | `models/qwen_Qwen2.5-7B-Instruct` (engine swap design; `scripts/run_attacker.sh` alternatively serves the AWQ build `models/qwen_Qwen2.5-7B-Instruct-AWQ` via vLLM) | `Qwen/Qwen2.5-7B-Instruct` (+ `-AWQ`) | `generation/pair-iterative/`, `generation/crescendo-multiturn/` |
| LLM-judge backbone (4 judges: zero-shot, StrongREJECT rubric, 2-stage validity, LlamaGuard-1 policy emulation) | Qwen2.5-14B-Instruct, **bf16** | `models/qwen_Qwen2.5-14B-Instruct` | `Qwen/Qwen2.5-14B-Instruct` | `judgments/full-panel/`, `llama2-extension/`, canary/vicuna judge stages. Note: the `src/judges.py` module docstring still says "AWQ"; the backbone was switched to the bf16 checkpoint (autoawq/transformers incompatibility, recorded in `docs/RESEARCH_LOG.md`), which is what `Q14B_PATH` in `src/judges.py` resolves and what produced the archived verdicts. |
| Classifier judge | HarmBench-Llama-2-13b-cls | `models/cais_HarmBench-Llama-2-13b-cls` | `cais/HarmBench-Llama-2-13b-cls` | all judge stages (`--stage harmbench`) |
| API judges (3: zero-shot, JBF rubric, StrongREJECT) | provider-declared `gpt-5.6-luna` behind an OpenAI-compatible relay | configured via `JUDGE_API_BASE` / `JUDGE_API_KEY` / `JUDGE_API_MODEL` (`src/judges_api.py`) | — (identity provider-asserted; disclosed in the paper) | `judgments/full-panel/judgments_api.jsonl`, `llama2-extension/judgments_api.jsonl` |
| Canary target (Qwen) | Qwen2.5-7B + LoRA | base `models/qwen_Qwen2.5-7B-Instruct` + adapter `models/canary_qwen_lora_v2` (written by `scripts/canary_plant.py`) | adapter reproduced by re-running the plant stage | `canary-qwen/`, `refusal-direction-ablation/` |
| Canary target (Vicuna) | Vicuna-7B + LoRA | base HF snapshot + adapter `models/canary_vicuna_lora` | adapter reproduced by re-running the plant stage | `vicuna-replication/` |

Seed-replicated adapters: the three Vicuna reseeds (`plant_metrics_seed*.json`)
were trained under seeds 101/202/303 with the same recipe.

## 4. Reproducing

### 4.0 Environment

Python 3.10 with `vllm`, `transformers` (4.46-era), `peft`, `numpy`,
`scikit-learn`, `scipy`. GPU stages assume a single ≥32 GB card (the original
runs used one; the 14B bf16 judge backbone is memory-bound — see
`docs/RESEARCH_LOG.md` for the KV-budget notes). A quick sanity entry point:

```bash
python scripts/smoke_test.py            # vllm import + victim load + generation
                                        # + parser sanity; writes results/smoke/
```

### 4.1 Data preparation (no GPU)

```bash
python scripts/prep_data.py
# builds data/processed/{advbench100.csv, behaviors_jbb100.csv, gcg_suffixes.json}
# and configs/{attacks.json, reported_asr.json} from data/raw + data/external/jbb
```

The GCG suffixes are matched by goal text from the official JailbreakBench
white-box artifact (`data/external/jbb/attack-artifacts/GCG/white_box/vicuna-13b-v1.5.json`).

### 4.2 Corpus generation (GPU, per victim)

```bash
python src/static_gen.py --model vicuna-7b  --out generation/static-attacks
python src/static_gen.py --model qwen2.5-7b --out generation/static-attacks
python src/static_gen.py --model mistral-7b --out generation/static-attacks
# PAIR / Crescendo (round-major attacker↔victim engine swap):
python src/pair.py       --model vicuna-7b
python src/crescendo.py  --model vicuna-7b
# seed control (attacker sampling seeds; victim decoding greedy):
python scripts/multiseed.py
# fourth victim, self-contained so the frozen 7,054-unit grid is untouched:
python scripts/llama2_judges.py --stage parsers   # after generating llama-2 outputs
```

### 4.3 Judge panel (per stage, GPU-resident)

```bash
python src/judges.py --stage parsers     # 4 code-based conventions (no GPU)
python src/judges.py --stage llm         # 4 judges on the Qwen2.5-14B backbone
python src/judges.py --stage harmbench   # official HarmBench classifier
python src/judges_api.py                 # 3 API judges (needs JUDGE_API_* env)
python scripts/rejudge_fulltext.py       # truncation audit re-judging
```

### 4.4 Gold standard and analysis

```bash
python scripts/gold_sheet_qwen.py        # build annotation sheets
python scripts/gold_remap.py             # post-annotation UID remap (see protocol)
python scripts/run_judges.py             # orchestrate judge stages
python src/analyze.py --gold             # judge-vs-gold + ASR tables (--gold: gold side)
python scripts/gstudy.py                 # variance decomposition + flips
python scripts/robustness.py             # truncation / robustness audits
python scripts/waterfall.py              # Rogan-Gladen waterfall
```

### 4.5 Certification and estimation validation

```bash
python scripts/certification_fix.py      # authoritative v2 certificate
python scripts/dstudy.py                 # D-study quantities
python scripts/panel_baselines.py        # panel composition arithmetic
python scripts/gstudy_extended.py        # extensions (dual estimator, panel curve)
python scripts/sizing_validation.py      # Monte-Carlo validation of planning formula
python scripts/doubly_robust_validation.py   # DR vs classical on canary truth
python scripts/confidence_sequences.py   # anytime-valid CS + peeking demo
```

### 4.6 Canary chains (sentinel-chained)

```bash
bash scripts/run_canary_qwen_chain.sh           # plant → attack → judges (Qwen)
bash scripts/run_vicuna_replication.sh          # full Vicuna replication chain
bash scripts/run_refusal_ablation_chain.sh      # directions → broadcast ablation
bash scripts/run_refusal_ablation_single14.sh   # layer-14 variant
python scripts/canary_analysis_fix.py           # authoritative canary analysis
```

### 4.7 Instrument layer

```bash
python asr-card-toolkit/rescore.py \
    --judgments <your_verdicts.jsonl> \
    --calibration asr-card-toolkit/calibration.yaml \
    --out rescored.jsonl                 # rescoring CLI (4 harness formats)
python asr-card-toolkit/asr_card.py \
    --config asr-card-toolkit/card_config.example.yaml \
    --out card.md                        # ASR-Card generator
```

Notes for re-running:

- Large archived `.jsonl` files (>2 MB) ship gzipped
  (`generation/static-attacks/*.jsonl.gz`, `judgments/full-panel/judgments_llm.jsonl.gz`,
  `llama2-extension/llama-2-7b.jsonl.gz`); `gunzip` in place before read-side
  reruns that expect plain files (`canary-qwen/attack_outputs_v1.jsonl` is kept
  plain deliberately — it is a live provenance input, NOTES §5).
- Scripts run from the package root (they resolve paths via the package root,
  not absolute locations).
- `scripts/ext_panel_api.py` / `scripts/ext_panel_gpu.py` reproduce a boundary
  experiment over a third-party stress-unit corpus that is **not redistributed**
  here (licensing); the experiment is not used in the paper (NOTES §7).
- `scripts/trivia_plant.py` / `scripts/trivia_attack.py` write diagnostic
  control outputs that are not shipped (NOTES §7).
- Archived outputs carry original run-time bookkeeping ids as data fields; the
  resolution table is NOTES §1/§3. Re-run scripts emit functional ids.

## 5. Integrity and provenance

- **Byte-integrity rule**: archived result files and verdict lines were never
  edited. Textual edits during packaging were limited to path echoes in logs,
  provenance `base` fields in two processed JSONs, and human-authored docs —
  all itemized in NOTES.md.
- **Authoritative versions**: `certification/certification_v2.json` (not v1)
  and `canary-qwen/analysis_fix.json` carry the paper's numbers; `attack_outputs_v1.jsonl`
  is a superseded provenance input retained for the v1-displacement fields
  (NOTES §4–§5).
- **Incidents**: three mid-experiment infrastructure failures and their
  data-integrity recoveries are disclosed in the paper (§5, Appendix E); the raw
  marker and the log live in `ops-records/` and `docs/RESEARCH_LOG.md`.

## 6. Third-party materials and credits

- **JailbreakBench** — behavior set and official attack artifacts
  (`data/external/jbb/`, `data/processed/behaviors_jbb100.csv`,
  `data/processed/gcg_suffixes.json`).
- **AdvBench** — harmful behaviors CSV (`data/raw/harmful_behaviors.csv`,
  first-100 slice `data/processed/advbench100.csv`).
- **HarmBench** — official classifier `HarmBench-Llama-2-13b-cls` and its
  prompt template (`configs/harmbench_cls_template.txt`).
- **StrongREJECT** — official rubric prompt and reference scorer
  (`configs/strongreject_prompt.txt`, `configs/strongreject_evaluator_ref.py`).
- **LlamaGuard-1** — O1–O7 policy template used for the backbone-emulated
  judge, labeled as an emulation (`configs/llamaguard1_policy_template.txt`).
- Open models by their respective providers (Qwen, Mistral AI / ModelScope
  mirror, LMSYS, NousResearch, CAIS). API judges were accessed through an
  OpenAI-compatible relay; model identity is provider-asserted (paper §3.1,
  Limitations).

If you use this package, please cite the paper.
