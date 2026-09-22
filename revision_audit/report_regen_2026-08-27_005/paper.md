# SEMS-R decomposition report

**Integrity.** This report describes **SEMS-R** (Reconstructed Legacy Education System), a controlled reconstruction. It is **not** the original production SEMS source. Numbers below are measurements of SEMS-R. They must not be pooled with historical SEMS paper measurements.

- Snapshot: `2026-08-27_005`
- Original SEMS source: `False`
- Historical gold used for evaluation only: `True`
- LLM outputs fabricated: `False`
- Git commit: `None` (unavailable if null)
- Independent architect pairwise sheets: 5 reviewers scored. Table D expert ranks are the median of their extract-first lists
- Historical migration ranks: blank; no documented extract-first order exists

## Methods (this snapshot)

Deterministic baselines and LLM prompts read architectural evidence only (`domain_description`, component catalog, call/data/runtime summaries, migration rules R1–R9). They do **not** read `reference/historical_architecture.json`.

Evaluation scores already-produced assignments against the historical six-service reference on the 24-component six-way universe (`AuthService` and `UserRepository` excluded as shared identity). Pairwise F1, ARI, and NMI are computed on that universe.

LLM conditions: **C0** domain + catalog; **C1** adds call/data/runtime; **C2** adds R1–R9; **C3** adds self-critique. Temperature 0.2, three runs per cell. Invalid JSON is stored as `parsed.json = null`; it is not replaced with a guessed architecture.

Combined-graph weights are α=β=γ=1.0 and were not fit on gold. Louvain *k* is unconstrained.

Figures in this report are rendered from the measured Table A–C CSVs. They are not redrawn from gold labels.

Phase 10 reports the Mode E equal-resource Locust comparison (monolith vs clustered campus at 4 CPU / 4 GB). Those numbers are read from `outputs/performance/comparisons/` and are not merged into the Phase 1–8 metrics snapshot. Locust mix 35/20/15/10/10/5/5 is synthetic. Locust ran on the host, outside the container CPU/RAM budget.

## Table A — deterministic methods vs historical reference

| method | n_services | pairwise_precision | pairwise_recall | pairwise_f1 | ari | nmi | cross_service_coupling | db_ownership_conflicts | cycles |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rule_based | 8 | 1.0 | 0.8596 | 0.9245 | 0.9067 | 0.9606 | 0.6327 | 0 | 1 |
| graph_static | 4 | 0.3043 | 0.3684 | 0.3333 | 0.1385 | 0.4466 | 0.4286 | 0 | 1 |
| static_only | 4 | 0.3016 | 0.3333 | 0.3167 | 0.1275 | 0.443 | 0.449 | 0 | 1 |
| runtime_only | 5 | 0.3382 | 0.4035 | 0.368 | 0.1848 | 0.499 | 0.5102 | 0 | 1 |
| combined_graph | 4 | 0.371 | 0.4035 | 0.3866 | 0.2183 | 0.4883 | 0.4898 | 0 | 1 |

On this reconstruction, the name/module heuristic (`rule_based`) has the highest pairwise F1 (0.9245). Graph methods remain in a lower band (best graph method `combined_graph` F1 0.3866). Rule-based F1 is inflated by reconstruction file and class names (`FacultyService`, and so on); treat it as an upper-bound leak, not as a fair contest against anonymous components.

## Table B — LLM conditions C0–C3

| model | condition | n_runs | pairwise_f1 | rule_compliance | stability | uncertain_decisions | unsupported_assumptions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-2.5-flash | C0 | 3 | 0.9068 | 1.0 | 0.9649 | 2 | 1.3333 |
| gemini-2.5-flash | C1 | 3 | 0.8152 | 1.0 | 0.9438 | 1.6667 | 0.6667 |
| gemini-2.5-flash | C2 | 3 | 0.7835 | 1.0 | 1.0 | 2.6667 | 0.6667 |
| gemini-2.5-flash | C3 | 3 | 0.8128 | 1.0 | 0.9225 | 3 | 2 |
| gpt-4o-mini | C0 | 3 | 0.8247 | 0.8333 | 0.9959 | 0 | 0 |
| gpt-4o-mini | C1 | 3 | 0.7333 | 0.8333 | 1.0 | 0 | 0 |
| gpt-4o-mini | C2 | 3 | 0.7174 | 0.8333 | 0.9953 | 0 | 0 |
| gpt-4o-mini | C3 | 3 | 0.7333 | 0.8333 | 0.9901 | 0 | 0 |
| llama3.1 | C0 | 3 | 0.9068 | 0.6667 | 0.9808 | 0.6667 | 0 |
| llama3.1 | C1 | 3 | 0.6173 | 0.7778 | 0.2712 | 0 | 0 |
| llama3.1 | C2 | 3 | 0.7809 | 0.6667 | 0.9251 | 0 | 0 |
| llama3.1 | C3 | 3 | 0.5 | 0.6667 | 0.6844 | 1 | 1 |

For every model in this snapshot, **C0 has the highest pairwise F1**. Adding call-graph, data, runtime, rules, or self-critique did not raise F1 above C0.
- `gemini-2.5-flash`: C0 F1 0.9068; strongest later condition F1 0.8152; C1 stability 0.9438.
- `gpt-4o-mini`: C0 F1 0.8247; strongest later condition F1 0.7333; C1 stability 1.0000.
- `llama3.1`: C0 F1 0.9068; strongest later condition F1 0.7809; C1 stability 0.2712.

## Table C — evidence ablation

| evidence | method | pairwise_f1 | modularity | cross_service_coupling |
| --- | --- | --- | --- | --- |
| static_call | graph_static | 0.3333 | 0.287 | 0.4286 |
| static_call_plus_data | static_only | 0.3167 | 0.2801 | 0.449 |
| runtime | runtime_only | 0.368 | 0.2022 | 0.5102 |
| static_plus_runtime | combined_graph | 0.3866 | 0.2551 | 0.4898 |

Evidence-source pairwise F1 on this reconstruction (highest first): `static_plus_runtime` 0.3866, `runtime` 0.3680, `static_call` 0.3333, `static_call_plus_data` 0.3167. Combined static+runtime is strongest among graph ablations and still far below the name-leaking rule baseline. Runtime-only exceeds static-call and static-call-plus-data here.

## Table D — migration ranking

| service | rule_based_rank | llm_rank | expert_rank | historical_rank |
| --- | --- | --- | --- | --- |
| student | 1 | 2 | 2 |  |
| faculty | 2 | 2 | 3 |  |
| finance | 3 | 3 | 4 |  |
| grade | 4 | 3 | 3 |  |
| library | 5 | 3 | 4 |  |
| attendance | 6 | 3 | 3 |  |

Rule-based ranks are the locked heuristic. LLM ranks are `gemini-2.5-flash` C0 run 1 `migration_priority` mapped onto the six Table D names (`AuthService` and `ReportingService` are omitted because they are not Table D rows). Expert ranks are the median of five extract-first lists that used those same FacultyService/StudentService names. Historical ranks blank: True. No documented historical extract order exists.

## Research questions (answered from this snapshot only)

### RQ1 — agreement with historical reference and independent architects
Vs the historical six-way reference, C0 pairwise F1 is `gemini-2.5-flash` 0.9068, `gpt-4o-mini` 0.8247, `llama3.1` 0.9068. 5 architects filled the 325-pair sheet. On the 24-component six-way eval universe, pairwise F1 vs historical gold is architect 1 0.8704 (precision 0.9216, recall 0.8246); architect 2 0.8750 (precision 0.8909, recall 0.8596); architect 3 0.8750 (precision 0.8909, recall 0.8596); architect 4 0.9245 (precision 1.0000, recall 0.8596); architect 5 0.8468 (precision 0.8704, recall 0.8246). The Gemini C0 example sheet scores F1 0.9245 on that same universe. Mean pairwise Cohen's kappa among 5 reviewers is 0.8584 (range 0.7752–0.9897 across 10 rater pairs). Table D `expert_rank` is the median of the five extract-first lists, mapped FacultyService→faculty (and likewise for the other five Table D names). `AuthService` and `ReportingService` were ranked by reviewers but are not Table D rows. `historical_rank` is blank: no documented historical extract order exists. Do not treat the historical six-service split as proven ground truth, only as the evaluation reference used here.

### RQ2 — does structured evidence improve LLM decomposition vs a high-level description?
No. On this reconstruction, C1 pairwise F1 is lower than C0 for every model (`gemini-2.5-flash` C1 0.8152 vs C0 0.9068; `gpt-4o-mini` C1 0.7333 vs C0 0.8247; `llama3.1` C1 0.6173 vs C0 0.9068). Structured call/data/runtime summaries did not improve boundary F1 relative to the high-level C0 prompt.

### RQ3 — do migration constraints and self-critique improve stability and quality?
Not as a reliable F1 gain. C2 and C3 do not beat C0 for any model in this snapshot. Stability is model-dependent:
- `gemini-2.5-flash`: C0–C3 stability C0 0.9649, C1 0.9438, C2 1.0000, C3 0.9225; rule_compliance C0 1.0000.
- `gpt-4o-mini`: C0–C3 stability C0 0.9959, C1 1.0000, C2 0.9953, C3 0.9901; rule_compliance C0 0.8333.
- `llama3.1`: C0–C3 stability C0 0.9808, C1 0.2712, C2 0.9251, C3 0.6844; rule_compliance C0 0.6667.
Gemini rule compliance is 1.0 across conditions; that does not imply higher F1 than C0.

### RQ4 — which evidence source contributes most?
Ranking by pairwise F1: `static_plus_runtime` > `runtime` > `static_call` > `static_call_plus_data`. Runtime contributes more than static-call or static-call-plus-data on this reconstruction; combining static and runtime is strongest among the graph ablations. All four remain far below the name-leaking rule baseline. Database-only was not a Phase 4 method, so it is not in Table C.

### RQ5 — LLM vs rule-based and graph baselines
Rule-based pairwise F1 0.9245 exceeds all graph methods (combined graph 0.3866). Best LLM C0 (`gemini-2.5-flash`, `llama3.1`) is 0.9068, near the rule heuristic and well above Louvain. That proximity is not a fair win for either side: both C0 and the rule method see reconstruction names and the six functional-area labels. Graph methods discover 4–5 communities vs reference 6.

## Phase 9 — historical six-service materialization

The evaluation-only gold split is materialized as six FastAPI services (Faculty, Student, Grade, Finance, Attendance, Library) plus a gateway that owns `User` and preserves the monolith public `/api/v1` contract. Each service has its own logical database. Peers use HTTP or in-process ASGI in tests; services do not import `app.models`. `reference/historical_architecture.json` is not an input to this code. This is the **reference materialization** for RQ evaluation, not an LLM output and not a scored decomposition. Gateway-only Locust smoke is not an equal-resource comparison and is not reported as a Phase 10 result.

## Phase 10 — cost of distribution (Locust)

This is a cost-of-distribution check on SEMS-R, not a proof that a split is faster than the monolith, and not a replay of a historical 10k-request production incident. One Docker Desktop VM, one uvicorn worker per process, one run per arm. Locust `high` is 100 users / 300s. Seed scale is `small` via the public HTTP API.

The paper load table is **Mode E equal-total 4 CPU / 4 GB**: monolith vs a dependency-clustered campus (faculty, student, grade, finance, and attendance in one process; library remains HTTP). Mode E does not replace the historical six-service gold.

### Measured Locust rows

| mode | architecture | config | users | requests | failures | median_ms | p95_ms | p99_ms | rps | equal_total | stamp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E | monolith | high | 100 | 60048 | 66 | 140.0 | 270.0 | 390.0 | 201.3468 | true | 2026-08-27_225302 |
| E | clustered | high | 100 | 23000 | 4 | 1200.0 | 2500.0 | 3100.0 | 76.9368 | true | 2026-08-27_225302 |

Mode E Locust `high` (equal 4 CPU / 4 GB): clustered campus p99 3100.0 ms at 76.9368 rps (4 failed requests). The monolith p99 390.0 ms at 201.3468 rps (66 failed requests). The monolith completed more requests and still had more failed requests. Clustered throughput does not exceed the monolith on this reconstruction. These rows are not production SEMS and are not 10k requests/s.

## Threats to validity

- **Naming leak.** Reconstruction class and file names encode the six areas. Rule-based F1 and LLM C0 are both exposed to that leak.
- **C0 still names the six areas.** The domain description lists Faculty, Student, Grade, Finance, Attendance, and Library. C0 is not a blind clustering task.
- **Architect pairwise.** 5 reviewers filled the 325-pair sheet. Extra same-service=1 links are not a transitive six-way partition; Table D uses the separate extract-first lists, not those pairwise 1s. Differences vs the Gemini C0 example: architect 1 10; architect 2 9; architect 3 10; architect 4 1; architect 5 14 pairs. Anchoring on that example is a threat for reviewers who received it. Closest rater pair differs on 1 pair.
- **Architect ranks.** Extract-first sheets used FacultyService/StudentService names (same labels as the LLM rank example). Grouping sheets used different proposed-service names. Median Table D ranks therefore follow the rank-sheet names, not the grouping names. Anchoring on the LLM rank example is a threat.
- **Model set.** Anthropic/Claude was never run. `llama3.1` via Ollama is not size-matched to Gemini 2.5 Flash. Exact Ollama digest was not frozen in the manifest.
- **Llama C1 instability.** Assignment stability 0.2712 means that cell is not a stable architecture recommendation.
- **Synthetic workload.** Locust mix 35/20/15/10/10/5/5 is an experimental assumption, not production SEMS traffic.
- **Not original SEMS.** Do not claim production fidelity or pool with historical paper numbers.
- **Shared identity.** `User` / auth components are excluded from six-way clustering.
- **Git commit unavailable** in this tree's manifests.
- **Phase 10 host.** Docker Desktop cgroups on one laptop, one uvicorn worker, one Postgres per architecture, Locust on the host. Not bare metal and not a multi-host production mesh.
- **One run per arm.** No repeated trials; treat tails as measured once.
- **Mode E is a second materialization.** The clustered campus is for load comparison. It is not the historical six-service gold.

## What this report does not claim

- Historical migration ranks are not inferred. Expert ranks are medians of submitted extract-first lists, not inferred from pairwise sheets.
- C1–C3 are not claimed to improve F1 on this reconstruction; the tables show the opposite.
- Phase 10 does not show that a split is faster than the monolith.
- Mode E clustered throughput does not beat the monolith at equal 4 CPU / 4 GB.
- Mode E does not replace the historical six-service gold materialization.
- These Locust rows are not production SEMS traffic and are not 10k requests/s.
