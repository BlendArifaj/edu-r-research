# Revision forensic audit — SEMS-R / IEEE Access manuscript

**Audit date:** 2026-09-22  
**Scope:** Read-only. No experiments rerun, no LLM regeneration, no metric code changes, no overwrites of existing result artifacts.  
**Title under revision:** *Evidence-Constrained LLMs for Microservice Decomposition: An Empirical Study on a Reconstructed Legacy System*

---

## Executive summary

| Finding | Severity |
|--------|----------|
| **Submitted manuscript analyzed** (`EDU_R_IEEE_Access_2026_Manuscript.docx` on Desktop; see addendum). | Done |
| **Table I in Word:** F1/ARI/NMI columns are **identical per row** — **transcription error**; artifacts and body text F1 are correct. | **MAJOR** fix |
| **Table V in Word** matches edited `paper.md` (300 users, clustered wins); **local** Locust stamp `2026-08-27_225302` is 100 users and **opposite** throughput story. Other-platform runs cited by authors are **not in repo** until archived. | **BLOCKER** for reproducibility |
| **Table I metrics in stored artifacts** independently verified (`table_i_recomputed.csv`). | OK |
| Scientific LLM matrix for publication snapshot `2026-08-27_005` is **exactly 36 runs** (3 models × 4 conditions × 3 reps). | Documented |
| Table III row `static_plus_runtime` (F1 0.3866) is the **same decomposition method** as baseline `combined_graph` in Table I, not the static+call+data-only method (`static_only`, F1 0.3167). | Labeling clarity issue |

Machine-readable outputs: `revision_audit/` (see §13).

---

## 1. Freeze — current repository state

| Item | Value |
|------|--------|
| Repository path | `/Users/bezepsolution/agentic-programming/sems-research` |
| Git branch | `main` |
| Git commit SHA | `713a3f99d1cf8a480ed4099eb59b2d68f102ecc8` |
| Git status | Clean (`nothing to commit, working tree clean`) |
| Git tags | **None** (`git tag -l` empty) |
| Uncommitted changes | **No** |

### Artifact locations

| Category | Path(s) |
|----------|---------|
| Experiment / pipeline code | `monolith/`, `decomposition/`, `experiments/`, `workload/`, `analysis/`, `microservices/` |
| Raw LLM outputs | `outputs/runs/<run_id>/decompositions/<model>/<C0–C3>/run_*/{prompt.txt,raw_response.txt,parsed.json,metadata.json}` |
| Processed metrics (scientific snapshot) | `outputs/runs/2026-08-27_005/metrics/{table_a..d}.csv`, `scores.json`, `llm_scores.json` |
| Evidence package | `outputs/evidence/architectural_evidence.json` (+ CSV sidecars) |
| Reference (evaluation-only gold) | `reference/historical_architecture.json` |
| Prompts (templates) | `decomposition/llm/prompts.py`; per-run prompts in run directories |
| Benchmark / domain inputs | `reference/domain_description.json`, `reference/migration_rules.json` |
| Architect study | `outputs/runs/2026-08-27_005/expert_review/` (+ `outputs/expert_review/` templates) |
| Runtime / Locust | `outputs/performance/comparisons/<stamp>/` |
| Manuscript surrogate (not IEEE source) | `outputs/reports/2026-08-27_005/paper.md` |
| Supplementary / report bundle | `outputs/reports/2026-08-27_005/tables/`, `figures/`, `tables/load/` |
| Experiment log / decisions | `EXPERIMENT_LOG.md`, `RESEARCH_DECISIONS.md` |

**Note:** `outputs/` is gitignored in the published testbed commit; artifacts exist locally on this machine.

---

## 2. Manuscript tables I–V — provenance mapping

**IEEE Access manuscript (submitted):**  
`/Users/bezepsolution/Desktop/FIEK/PhD/Punime shkencore/11 - Sems-r research - SUBMITTED/EDU_R_IEEE_Access_2026_Manuscript.docx`  
Extracted for audit: `revision_audit/manuscript_extracted.txt`, `revision_audit/manuscript_tables.md`, `revision_audit/manuscript_vs_artifacts.csv`.  
**Addendum (manuscript-specific):** `revision_audit/MANUSCRIPT_ADDENDUM_2026-09-22.md`

**Important:** Authors report additional experiments on other platforms; the manuscript is the **last intended state**. The `sems-research` repo may not contain every run cited (especially Table V at 300 users).

Internal report mapping (README / `analysis/narrative.py`):

| Manuscript (IEEE) | Internal report | Primary source artifact | Generator |
|-------------------|-----------------|-------------------------|-----------|
| **Table I** | Table A | `outputs/runs/2026-08-27_005/metrics/table_a.csv` | `decomposition.evaluation.runner` → `tables.table_a_rows` from `scores.json` |
| **Table II** | Table B | `outputs/runs/2026-08-27_005/metrics/table_b.csv` | `decomposition.llm.score_runs.score_and_write` |
| **Table III** | Table C | `outputs/runs/2026-08-27_005/metrics/table_c.csv` | `tables.table_c_rows` (subset of baseline scores) |
| **Table IV** | Table D | `outputs/runs/2026-08-27_005/metrics/table_d.csv` | `tables.table_d_rows` + `expert_followup.apply_table_d_ranks` when follow-up present |
| **Table V** | Phase 10 load table | `outputs/performance/comparisons/2026-08-27_225302/comparison.csv` | `workload.compare` → `comparison.csv`; copied into report via `analysis.phase10` + `phase10_artifacts.yaml` |

### Generation vs manual copy

| Table | Auto-generated? | Matches source? |
|-------|-----------------|-----------------|
| I (A) | Yes (`make evaluate` / experiment snapshot) | `table_a.csv` matches `scores.json` (rounded to 4 decimals) |
| II (B) | Yes | Mean of per-run F1/compliance; see §6 |
| III (C) | Yes | Derived from same `scores.json` as Table I |
| IV (D) | Partially | Rule + LLM ranks auto; expert ranks from follow-up JSON |
| V | Yes from Locust | **`outputs/reports/.../paper.md` Table V does NOT match `comparison.csv`** (manual edit) |

### Manual transcription risk

- Tables I–IV in `outputs/reports/2026-08-27_005/tables/*.csv` are **copies** of snapshot metrics (automated by `analysis.report`).
- **`paper.md` lines 118–127** (Phase 10 table + interpretation) are **not** produced by `analysis.report` today; `diff` vs regenerated report shows **hand-edited** throughput/latency narrative and user count (300 vs 100).
- Without the IEEE manuscript file, **manual transcription into Word cannot be verified** here.

---

## 3. Table I — independent recomputation (highest priority)

### Method

Script: `revision_audit/recompute_table_i.py`  
- Pairwise precision/recall/F1: independent implementation (TP/FP/FN/TN over unordered pairs).  
- ARI: independent contingency-table formula (equivalent to standard ARI definition).  
- NMI: **arithmetic-mean NMI** `2·I/(H_true+H_pred)` — matches `decomposition/evaluation/pairwise.py` (not sklearn’s default geometric normalization).

### Evaluation universe

- **24 components** after excluding `AuthService`, `UserRepository` (`reference/historical_architecture.json` + `evaluation_notes.legacy_components_in_six_way`).
- **Unordered pairs:** **276** = C(24,2). Confirmed for all five baseline methods.
- Reference assignment export: `revision_audit/table_i_reference_assignment.csv`
- Per-method predicted clusters: `revision_audit/table_i_predicted_<method>.csv`

### Results vs stored Table I (`table_a.csv`)

| Method | Precision | Recall | Pairwise F1 | ARI | NMI | MS F1 | MS ARI | MS NMI | Diagnosis |
|--------|-----------|--------|-------------|-----|-----|-------|--------|--------|-----------|
| rule_based | 1.000000 | 0.859649 | **0.924528** | **0.906717** | **0.960621** | 0.9245 | 0.9067 | 0.9606 | Match (rounding) |
| graph_static | 0.304348 | 0.368421 | **0.333333** | **0.138462** | **0.446554** | 0.3333 | 0.1385 | 0.4466 | Match |
| static_only | 0.301587 | 0.333333 | **0.316667** | **0.127458** | **0.442992** | 0.3167 | 0.1275 | 0.4430 | Match |
| runtime_only | 0.338235 | 0.403509 | **0.368000** | **0.184836** | **0.498952** | 0.3680 | 0.1848 | 0.4990 | Match |
| combined_graph | 0.370968 | 0.403509 | **0.386555** | **0.218343** | **0.488262** | 0.3866 | 0.2183 | 0.4883 | Match |

Full CSV: `revision_audit/table_i_recomputed.csv`

### Reviewer concern: “F1, ARI, and NMI identical for every method”

**Confirmed in the submitted Word manuscript Table I** (e.g. Rule Heuristic: 0.925 / 0.925 / 0.925).  
**Not true in repository artifacts** — independent recomputation matches `table_a.csv` with distinct ARI/NMI.

**Diagnosis: (C) transcription error** — manuscript Table I columns for ARI and NMI were filled with the **same 3-decimal F1 value** per row. Body text still uses correct 4-decimal F1 (0.9245, 0.3866, etc.).

- `revision_audit/table_i_summary.json`: `f1_equals_ari_any_method: false` in artifacts.
- **Not (D) scoring bug** in the frozen snapshot.

**Not** explanation (A) “metrics are wrongly identical in data” — they are not.

### Rankings / conclusions if ARI/NMI were “fixed”

Using the **correct** independent values (which equal stored values), **rankings unchanged**: `rule_based` > all graph methods; among graphs, `combined_graph` highest F1. No conclusion inversion from recomputation.

---

## 4. Table III vs Section IV-A labeling (`combined_graph` vs static+runtime)

| Label | Code method | Graph evidence |
|-------|-------------|----------------|
| Table I `combined_graph` | `combined_graph` | Louvain on **α·call + β·data + γ·runtime** after per-layer max-normalization (`decomposition/baselines/runner.py`, `graphs.combine_graphs`) |
| Table III `static_plus_runtime` | **Same** `combined_graph` row via `tables.table_c_rows` evidence_map | Identical F1 **0.3866** because it is the **same decomposition** |
| Table III `static_call_plus_data` | `static_only` | Louvain on **call + data only** (no runtime layer) — F1 **0.3167** |
| Table I `graph_static` | `graph_static` | Call graph only — F1 **0.3333** |

**Conclusion:** Equal F1 (0.3866) between “all-source combined graph” and Table III `static_plus_runtime` indicates **same method**, not coincidence.  
**Ambiguity risk:** Section IV-A prose must not imply “static+runtime” means “static call + data” only; code uses **call + data + runtime** for `combined_graph`.

Evidence weights: `experiments/configs/baselines.yaml` — α=β=γ=1.0, `normalize_layers: true`.

---

## 5. LLM experiment matrix (actual artifacts)

Inventory: `revision_audit/original_llm_runs.csv` (96 `metadata.json` files across all snapshots).

### Publication snapshot `2026-08-27_005`

| Model | Provider | Conditions | Reps | Scientific runs |
|-------|----------|------------|------|-----------------|
| gpt-4o-mini | openai | C0–C3 | 3 each | 12 (reused from `2026-08-27_004`) |
| gemini-2.5-flash | gemini | C0–C3 | 3 each | 12 (reused from `2026-08-27_004`) |
| llama3.1 | ollama | C0–C3 | 3 each | 12 (executed in 005 per `manifest.json`) |

**Total scientific in 005: 36** = 3 × 4 × 3. Confirmed by cell counts in inventory.

### Design vs actual

- **Planned:** 3 models × 4 conditions × 3 runs = **36** (for the frozen scientific snapshot).  
- **Across all snapshots:** 72 runs flagged `is_scientific_run=true` (includes partial matrices in 003/004).  
- **Not inferred:** skipped slots recorded in `manifest.json` (e.g., 005 skipped live OpenAI/Gemini generation; copied from 004).

Per-run fields in CSV: provider, model, condition, run_number, temperature (0.2), paths, `parse_ok`, `is_scientific_run`, availability.

Settings: `experiments/configs/llm.yaml` — `temperature: 0.2`, `runs: 3`, `max_retries: 2`. **No LLM seed** recorded in metadata (provider APIs).

---

## 6. Table II aggregation and invalid outputs

**Implementation:** `decomposition/llm/score_runs.py`

| Metric | Aggregation |
|--------|-------------|
| `pairwise_f1` | **Arithmetic mean** of per-run `pairwise.f1` across valid runs in the cell |
| `rule_compliance` | Mean of per-run `rule_compliance` |
| `stability` | Mean pairwise F1 **between runs** (`decomposition/evaluation/stability.py`) — not consensus partition |
| `uncertain_decisions` | Mean count per run |
| `unsupported_assumptions` | Mean length of list per run |

**Invalid / incomplete outputs:**

- Runs with `parsed.json` null or `available: false` are **skipped** in grouping (`score_llm_runs` continues at parse/load).
- They do **not** enter numerators/denominators for Table II means.
- If all three runs invalid, the cell would be absent from Table B (not observed for 005 scientific matrix).

**Rule compliance (R1–R9 vs machine rules):**

- Prompt text R1–R9 appears only in **C2+** (`prompts._c2_body`).
- **Scoring always runs** `rule_compliance()` for every parsed decomposition (`scoring.evaluate_decomposition`), using **machine-checkable** rules from evidence (`entity_has_at_most_one_owner`, imbalance, unassigned, cycles reported, etc.) — **not** a literal count of R1–R9 textual compliance.
- **Yes:** C0/C1 outputs are still scored against machine-checkable rules derived from `migration_rules.json` structure.

Denominator: `len(satisfied_rules) / len(applicable_rules)` (6 machine rules in snapshot scores).

---

## 7. Experimental specification completeness

| Item | Status |
|------|--------|
| C0–C3 prompt templates | **COMPLETE** — `decomposition/llm/prompts.py` + frozen per-run `prompt.txt` |
| Benchmark inputs | **COMPLETE** — `reference/domain_description.json`, evidence JSON |
| Exact model versions | **PRESENT BUT INCOMPLETE** — manifest lists ids; **no Ollama digest**, no API revision pins |
| Model settings | **COMPLETE** — temperature 0.2; retries 2 |
| Rules R1–R9 text | **COMPLETE** — `reference/migration_rules.json` |
| Graph generation | **COMPLETE** — `decomposition/baselines/graphs.py`, `extraction/` |
| Normalization | **COMPLETE** — per-layer max-normalization documented in baselines config |
| Parsing code | **COMPLETE** — `decomposition/llm/parse.py` |
| Scoring code | **COMPLETE** — `decomposition/evaluation/scoring.py`, `pairwise.py` |
| Raw LLM outputs | **COMPLETE** (snapshot 005) |
| Per-run scored JSON | **COMPLETE** — inside `llm_scores.json` |
| Invalid-output handling | **COMPLETE** — store null; skip in aggregates |
| Reference architecture | **COMPLETE** — `reference/historical_architecture.json` |
| Architect instructions | **COMPLETE** — `expert_review/evaluation_form.md` |
| Blinding procedure | **PRESENT BUT INCOMPLETE** — asks not to read gold; **component names leak domains**; LLM example sheet provided |
| Architect qualifications | **MISSING** — only ids `exp1`–`exp5` |
| Aggregation / Table D ranks | **COMPLETE** — median of extract-first lists (`expert_followup`) |

---

## 8. Six-service reference architecture

| Question | Evidence |
|----------|----------|
| Six services | faculty, student, grade, finance, attendance, library |
| Definition file | `reference/historical_architecture.json` |
| Who / when | Documented as historical/reference for evaluation; frozen before scoring; **no author provenance field** |
| Independent validation | **No** formal external validation artifact; 5 architects scored vs gold |
| Architects saw gold? | Instructions say not to; **names** (`FacultyService`, etc.) align with domains |
| Circularity risk | **High** — reconstruction uses domain-oriented modules; rule baseline and C0 domain text encode six areas; gold maps components to those areas |

Component catalog: 26 in evidence; **24** in six-way clustering evaluation.

---

## 9. Semantic-name leakage

Full table: `revision_audit/semantic_leakage_components.csv` (26 components).

**Pattern:** Most class names embed domain tokens (e.g., `FacultyService` → faculty).  

**Who sees identifiers:**

| Pipeline stage | Sees component names? |
|----------------|----------------------|
| Rule baseline | Yes (heuristic on names/modules) |
| Graph baselines | Yes (graph nodes are named components) |
| LLM C0 | Yes (component list + six functional area **ids** in domain text) |
| LLM C1–C3 | Yes + structured edges/DB |
| Architects | Yes (`component_list.csv`) |
| Evaluation gold | Uses same names in mapping file |

---

## 10. Runtime experiment (Table V)

### Authoritative artifacts — Mode E, stamp `2026-08-27_225302`

| Field | Monolith | Clustered | Source |
|-------|----------|-----------|--------|
| Locust config | `high` | `high` | `workload/config/high.yaml` |
| Users | **100** | **100** | `summary.json`, `comparison.csv` |
| Duration | **300s** | **300s** | same |
| Warm-up | **Not separately configured** | — | Locust starts spawning immediately (`spawn_rate: 20`) |
| Runs per arm | **1** | **1** | `EXPERIMENT_LOG.md` EXP-016 |
| Request count | **60,048** | **23,000** | `locust_stats.csv` Aggregated |
| Failures | **66** | **4** | same |
| Median ms | **140** | **1200** | same |
| p95 / p99 | **270 / 390** | **2500 / 3100** | same |
| RPS | **201.35** | **76.94** | same |

**Workload:** Locust `workload/locustfile.py`, mix 35/20/15/10/10/5/5 (`high.yaml`).  
**DB:** Postgres 16, one instance per profile (`docker-compose.mode-e.yml`).  
**Topology:** Monolith single app; clustered = campus (2.6 CPU / 2688 MB) + library HTTP (0.4 CPU / 384 MB) + Postgres (1 CPU / 1 GB) = **4 CPU / 4 GB** total.  
**Workers:** one uvicorn worker per process (compose commands).  
**Budget includes:** Postgres + app processes; **Locust on host, outside budget** (`mode_e.yaml` note).

### `paper.md` vs artifacts (critical)

`outputs/reports/2026-08-27_005/paper.md` claims:

- 300 users, 180,144 / 220,512 requests, clustered **faster** and higher throughput.

**Immutable Locust data contradicts this** (100 users; monolith **higher** RPS; clustered **worse** tail latency).

Regenerated report (`revision_audit/report_regen_2026-08-27_005/paper.md`) matches artifacts and states monolith completed more requests.

**“Omitted until verification” text:** Present in edited `paper.md` (duration disclaimer) while simultaneously publishing **unverified “corrected” numbers** — classification **(B) manuscript TODO / draft inconsistency** + **(C) unverified manual correction**, not missing logs (logs exist).

### Percentage claims in edited `paper.md`

Example: “22.4% more requests” for clustered — **not supported** by `comparison.csv` (clustered **lower** count).  
Treat all Phase 10 improvement percentages in edited `paper.md` as **unsupported** until reconciled with Locust files.

---

## 11. Manuscript structural issues (in-repo surrogate only)

**IEEE manuscript:** not available — section numbering (e.g. **Section VII**) cannot be verified.

**In `outputs/reports/2026-08-27_005/paper.md`:**

| Check | Result |
|-------|--------|
| Section VII | N/A (report uses markdown headings, not IEEE sections) |
| Threats to validity | **Removed** in edited `paper.md`; present in regenerated report |
| Naming-leakage discussion | Partial — narrative mentions leak in RQs; full threats block removed in edit |
| `VOLUME XX` / DOI placeholders | **Not found** in repo surrogate |
| Keywords “engineering education” | **Not found** in `paper.md` |
| TODO / TBD / omitted / verify | Phase 10: “must be verified”, “intentionally not stated”, “corrected clustered request count” |

**Search note:** `paper.md` line 112 claims clustered outperformed monolith — contradicts experiment log EXP-016 and CSV.

---

## 12. Claim-to-evidence audit (from `paper.md` surrogate)

| Claim (paraphrased) | Classification |
|---------------------|----------------|
| C0 highest F1 for every model | **Directly supported** — Table B |
| Richer evidence does not raise F1 vs C0 | **Directly supported** — Table B |
| Rule-based F1 ~0.92 (naming leak) | **Supported but too broadly worded** if framed as fair baseline |
| Graph methods 4–5 communities vs 6 | **Directly supported** |
| Architect kappa / F1 vs gold | **Directly supported** — `expert_pairwise_scores.json` |
| Gemini C0 near rule-based | **Supported** — scores; **circularity threat** |
| Phase 10: clustered faster / more throughput | **Unsupported by artifacts** — contradicts CSV |
| “22% throughput increase” | **Unsupported** |
| LLM decomposition validated by runtime deployment | **Unsupported / misleading** — Mode E is different topology, not LLM output |
| “Significantly lower” (if in external ms) | Not in surrogate; would be **statistically worded without test** |

---

## 13. Files created during this audit

```
revision_audit/recompute_table_i.py
revision_audit/inventory_llm_runs.py
revision_audit/semantic_leakage_components.py
revision_audit/table_i_recomputed.csv
revision_audit/table_i_summary.json
revision_audit/table_i_reference_assignment.csv
revision_audit/table_i_predicted_<method>.csv  (×5)
revision_audit/original_llm_runs.csv
revision_audit/semantic_leakage_components.csv
revision_audit/report_regen_2026-08-27_005/  (regenerated report for diff only)
REVISION_FORENSIC_AUDIT.md
```

---

## A. Critical correctness issues

1. **Phase 10 / Table V:** Edited `paper.md` conflicts with Locust primary data; improvement narrative inverted.  
2. **Missing IEEE manuscript** in repo — cannot certify Table I–V transcription.  
3. **No git SHA in experiment manifests** (`git.commit: null`) — weak reproducibility pin for snapshot.

## B. Reproducibility gaps

- Submitted manuscript and supplementary ZIP not versioned here.  
- Ollama model digest not frozen.  
- Architect demographics / IRB packet not in tree.  
- Historical extract order (`historical_rank`) blank by design.

## C. Reviewer concerns resolvable without new experiments

- Table I F1/ARI/NMI identity → **artifact math is correct**; check Word columns.  
- Table III vs IV-A 0.3866 → **same method** (`combined_graph`).  
- Table II aggregation → **documented means**.  
- Rule compliance scope → **machine rules on all conditions**.

## D. Concerns requiring new work (not executed here)

- Reconcile or rerun Phase 10 if manuscript needs defensible runtime claims.  
- Provide blinded / anonymized component labels study (if claiming unbiased LLM vs graph).  
- Freeze Ollama artifact + git tag for snapshot.

## E. Manuscript-only fixes

- Restore Threats section; align Table V with `comparison.csv` or remove performance claims.  
- Clarify Table III labels (`call+data+runtime` vs `static_plus_runtime`).  
- Disclose naming leakage and C0 domain list explicitly.

## F. Recommended execution order

1. Obtain IEEE manuscript source into repo (read-only tag).  
2. Diff manuscript tables against `outputs/runs/2026-08-27_005/metrics/*.csv`.  
3. **Fix or remove Phase 10 claims** before any resubmission.  
4. Address Table I column transcription in Word.  
5. Decide on anonymization study vs limitation text.  
6. Tag commit `713a3f9` + snapshot id in paper.  
7. Only then consider selective reruns (Locust replication, optional LLM).

## G. Publication-impact assessment

| Issue | Impact |
|-------|--------|
| Phase 10 numbers contradict logs | **BLOCKER** |
| IEEE ms not in repo | **BLOCKER** (audit completeness) |
| Table I column copy error (if in ms) | **MAJOR** |
| Table III naming ambiguity | **MODERATE** |
| Naming leakage / gold circularity | **MAJOR** (validity) |
| Missing git pin in manifest | **MODERATE** |
| Rule compliance scope confusion | **MODERATE** |
| No architect demographics | **MINOR** |

---

*End of forensic audit.*
