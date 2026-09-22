# Anonymized-Identifier Control Experiment — Protocol v2 (freeze only)

**Paper:** *Evidence-Constrained LLMs for Microservice Decomposition* (EDU-R / SEMS-R)  
**Protocol ID:** `anonymization_exp_v2`  
**Status:** EXECUTED (2026-09-22) — see `results/REVISION_CONTROL_RESULTS.md` (cloud arms incomplete; Llama complete)  
**Git SHA (protocol freeze):** `713a3f99d1cf8a480ed4099eb59b2d68f102ecc8`  

---

## 1. Frozen original submitted experiment (historical only)

| Item | Value |
|------|--------|
| Repository | `sems-research` |
| Branch / commit | `main` @ `713a3f9` |
| Historical snapshot | `outputs/runs/2026-08-27_005` |
| Historical LLM runs | **36** (`3×4×3`) |
| Manifest | `original_submitted_baseline_manifest.csv` |
| Cohort label | **`ORIGINAL_SUBMITTED_BASELINE`** |
| Use in revision | **Submitted-paper evidence only** — **excluded from primary factorial analysis** |

Reason for separation: original Gemini/API and Ollama digest were not fully frozen; mixing with new anonymized runs would confound identifier effects with provider drift.

**Do not modify** historical snapshot files.

---

## 2. Scientific question (unchanged)

> Does semantic information encoded in **component-identity aliases** influence the effect of **evidence richness** on LLM decomposition?

### Factors

| Factor | Levels |
|--------|--------|
| **A — Identifier** | SEMANTIC (original names) · ANONYMIZED (opaque aliases) |
| **B — Evidence** | C0, C1, C2, C3 |
| **C — Model** | Gemini 2.5 Flash · GPT-4o-mini · Llama 3.1 |

---

## 3. Strengthened anonymization (v2)

### Component identity map

`component_identifier_map.csv` — 26 components, alphabetical → `Component_01`…`Component_26`, plus:

- `anonymized_module` → `Module_XX` (same index)  
- `anonymized_file` → `artifacts/Component_XX.py`

### Functional-area **listing** ids (identity aliases)

`functional_area_identifier_map.csv` — six area slugs → `Area_01`…`Area_06`  
**Capability text unchanged** (legitimate semantic evidence).

### Distinction A vs B

Documented in **`LEAKAGE_AUDIT.md`**.

### Artifacts

| SEMANTIC (revision) | ANONYMIZED |
|---------------------|------------|
| `outputs/evidence/architectural_evidence.json` | `evidence/architectural_evidence_anonymized.json` |
| `prompts/C*_SEMANTIC.txt` | `prompts/C*_ANON.txt` |

Regenerate: `freeze_map.py` → `anonymize_evidence.py` → `generate_prompts.py`.

---

## 4. Revision experiment — **120 NEW runs**

**Primary identifier-control study uses ONLY these runs.**

```
3 models × 4 conditions × 2 identifier arms × 5 repetitions = 120 NEW generations
```

| Cohort | Runs | Status |
|--------|------|--------|
| `REVISION_CONTROL_V1` | **120** | `PLANNED_NEW` in `run_manifest.csv` |
| `ORIGINAL_SUBMITTED_BASELINE` | **36** | `FROZEN_HISTORICAL` (separate manifest) |

**Total artifacts after revision execution:** **156** generations (120 + 36).  
**Primary analysis:** **120** contemporaneous paired runs only.

Output root (when executed): `outputs/runs/anonymization_exp_v1/`  
**Never write into** `2026-08-27_005`.

---

## 5. Paired / interleaved execution (counterbalanced order)

Each **`pair_id`** = `{model}|{condition}|{repetition}`.

Semantic and anonymized counterparts stay **adjacent** in `execution_order`, but **which arm runs first is counterbalanced** (fixed before execution, not randomized post hoc):

| Rule | First condition |
|------|-----------------|
| Odd `pair_index` (1, 3, 5, …) | SEMANTIC → ANONYMIZED |
| Even `pair_index` (2, 4, 6, …) | ANONYMIZED → SEMANTIC |

Manifest columns: `pair_id`, `pair_index`, `pair_position` (1 or 2 within pair), `pair_first_condition`, `execution_order`, `identifier_condition`.

Yields ~50/50 first-position balance overall (60/60 for 120 runs).

Mitigates provider/time drift via back-to-back pairs while controlling order effects.

### Identifier-semantics control (not semantic-blind)

**Unchanged between SEMANTIC and ANONYMIZED:** domain description, capability text, business entities, HTTP/operation semantics, call/data/runtime relationships, migration rules, component `kind`.

**Anonymized:** component names, module names, file/module paths, functional-area **listing** ids (`Area_XX`).

The experiment tests **identifier-semantics**, not removal of all domain meaning.

### Retry / failure policy (frozen)

See **`RETRY_FAILURE_POLICY.md`**: max **2** infrastructure retries (logged); **no** retries for invalid JSON / schema failures (`execution_status`, `parse_status`, `invalid_reason` on each run).

---

## 6. Provider / model provenance (frozen fields)

Populated **at execution** (empty in freeze). Pre-filled now where possible:

| Field | When set |
|-------|----------|
| `provider` | manifest |
| `requested_model_id` | manifest |
| `resolved_model_version` | API response / provider metadata |
| `execution_timestamp` | UTC ISO at call |
| `temperature` | 0.2 |
| `seed_if_supported` | if API supports |
| `prompt_sha256` | **precomputed** in manifest |
| `evidence_sha256` | **precomputed** |
| `git_sha` | **precomputed** (`713a3f9…`) |
| `parser_scorer_version` | frozen string |
| `llama_artifact_digest` | **`ollama inspect` / digest BEFORE first Llama call** |

### Strategy

1. **Llama:** Capture and freeze digest in manifest + `revision_anonymization/llama_digest_frozen.txt` before any run; abort if digest changes mid-study.  
2. **Cloud APIs:** Document that backend weights may drift; **pairwise interleaving** + same `requested_model_id` + record `resolved_model_version` per run.  
3. If a provider retires an ID, **stop** and revise protocol (do not silently substitute).

---

## 7. Invalid-output reporting (supplementary)

**Primary metrics (unchanged):** mean F1/ARI/NMI/rule compliance/stability over **valid** parses only (same as original `score_runs.py`).

**Additional frozen reporting per cell:**

| Metric | Definition |
|--------|------------|
| `attempted_generations` | Manifest slots executed |
| `valid_parsed` | `parsed.json` available and `available: true` |
| `invalid_incomplete` | null parse, schema fail, or `available: false` |
| `validity_rate` | valid / attempted |

**Sensitivity (conservative):** For cells with invalid runs, report:

- mean F1 treating invalid as **missing** (primary), and  
- **worst-case bound** note (e.g. if invalid counted as F1=0) — supplementary table only; **does not replace** primary metric.

---

## 8. Reference-label schema check

**`REFERENCE_LABEL_SCHEMA_VERDICT.md`**

## Answer: **NO** — not a BLOCKER.

Six reference service names are **not** required output categories.

---

## 9. Scoring universe

- **26** components in prompts/evidence (both arms).  
- **24** six-way eval components after reverse-map; **`AuthService` / `UserRepository`** (Component_04 / Component_26 equivalents) excluded from clustering metrics — same as original.  
- ANON: reverse-map `component_assignment` keys before `evaluate_decomposition`.  
- Gold + **semantic** evidence package for structural/rule metrics (unchanged evaluator).

---

## 10. Analysis plan (primary revision)

**Unit:** one generation (run).

**Primary contrast:** SEMANTIC vs ANONYMIZED within same `(model, evidence_condition, repetition)` — use **`pair_id`**.

Per cell and per pair report:

- individual run F1 (and ARI/NMI)  
- mean, median, SD, IQR/range  
- **Δ = semantic − anonymized**  
- parsing validity counts  

**Secondary:** C0–C3 ladders **within** each identifier arm (descriptive).

**Outcomes A–D** (from v1 protocol) — all scientifically valid.

**Inferential tests:** **secondary/exploratory only**; n=5 reps does not support strong significance claims. Emphasize **effect magnitude**, **pair consistency**, **model-specific patterns**.

---

## 11. Pre-execution validation

`python revision_anonymization/scripts/preflight.py` (runs `verify_anonymization.py`)  
→ `validation_results.json` — **`all_pass: true`** required before any provider call.

Checks **A–M:** bijection, no component/area-slug identity in ANON prompts, no original module paths in anon evidence, opaque files, area ids, no gold in prompts.

Checks **N–T:** counterbalanced pair order valid; each pair has exactly one SEMANTIC + one ANONYMIZED; matched settings per pair; prompt/evidence hashes recorded; no reference partition in prompts; Llama digest frozen; retry policy frozen.

---

## 12. Reviewer traceability

| Reviewer | Concern | Revision response artifact |
|----------|---------|----------------------------|
| R1 | Name leakage / high C0 | Δ F1 semantic vs anon @ C0 per model |
| R3 | Fair baselines | Unchanged scoring; 120 new paired runs |
| R4 | Evidence richness | C0–C3 within each identifier arm |
| R5 | Few reps | 5 reps + validity rates |
| R6 | Domain vs identifier | LEAKAGE_AUDIT A vs B |
| R2 | (unspecified) | — |

---

## 13. Final summary (sections A–N)

### A. Hypothesis

Component-identity aliases materially affect decomposition agreement, especially under C0.

### B. Independent variables

Identifier (2) × evidence (4) × model (3) × repetition (5).

### C. Dependent variables

Pairwise F1 (primary), ARI, NMI, rule compliance, stability, validity rate.

### D. Controlled

Temperature 0.2, schema, parser, gold, scoring code, contemporaneous execution design.

### E. Anonymization

Component_XX, Module_XX, artifacts paths, Area_XX listing ids.

### F. Leakage

See LEAKAGE_AUDIT.md; residual entity/endpoint/kind disclosed.

### G. Run matrix

**120 NEW** (`run_manifest.csv`).

### H. Reused historical

**36** baseline only (`original_submitted_baseline_manifest.csv`) — not in primary factorial.

### I. New runs required

**120** (all revision cells).

### J. Model comparability

Cloud drift **MAJOR**; mitigated by pairing + version logging; Llama requires **pre-frozen digest**.

### K. Scoring

Unchanged definitions; reverse-map ANON outputs.

### L. Analysis

§10; descriptive primary, inferential secondary.

### M. Validation checklist

`validation_results.json` all_pass; Llama digest file before execute; manifest SHA columns match files on disk.

### N. Issues

| Issue | Severity |
|-------|----------|
| Llama digest not yet captured at freeze time | **BLOCKER** until `llama_digest_frozen.txt` exists |
| Cloud `resolved_model_version` may be partial | **MAJOR** |
| Entity/endpoint/kind residual semantics in ANON | **MAJOR** (disclosure) |
| Kind field still exposes layer | **MODERATE** |

---

## STOP

**No provider calls** until protocol approval + Llama digest frozen + validation `all_pass`.

### Deliverables (v2)

1. `ANONYMIZATION_EXPERIMENT_PROTOCOL.md` (this file)  
2. `component_identifier_map.csv` + `functional_area_identifier_map.csv`  
3. `LEAKAGE_AUDIT.md`  
4. `run_manifest.csv` (120 rows) + `original_submitted_baseline_manifest.csv` (36)  
5. `validation_results.json`  
6. `REFERENCE_LABEL_SCHEMA_VERDICT.md` → **NO** reference-label schema BLOCKER  
7. Eight prompt files under `prompts/`  
8. `evidence/architectural_evidence_anonymized.json`
