# Experiment log

Never overwrite previous entries. Append after every meaningful experiment.

---

## EXP-000 — Repository bootstrap (Phase 1)

- **Experiment ID:** EXP-000
- **Date:** 2026-06-10
- **Goal:** Create SEMS-R as an executable reconstructed monolith (not original SEMS) with shared PostgreSQL/SQLite schema, six functional areas, realistic cross-domain coupling, seed data, and API tests.
- **Configuration:** Python 3.12, FastAPI, SQLAlchemy 2, SQLite in tests, PostgreSQL in Docker. No LLM. No reference labels consumed by application code.
- **Input:** Documented historical functional areas (Faculty, Student, Grade, Finance, Attendance, Library) and shared-database monolith characteristics.
- **Method:** Reconstruction of domain model, services, repositories, and HTTP API. Deterministic seed (`SEMS_SEED=42`).
- **Results:** Phase 1 gate passed. `pytest monolith/tests` = 10 passed. Tiny seed produced 8 students, 3 courses, 8 grades, 8 invoices, 4 books on SQLite. Cross-domain behaviors verified: semester registration required before enrollment; finance hold blocks registration; grades require enrollment and the course teacher; student overview joins GPA, balance, attendance, and loans.
- **Problems:** Historical source code unavailable; reconstruction cannot claim production fidelity.
- **Decision:** Proceed with SEMS-R labeled as synthetic reconstruction. Exclude `User` from six-way gold clustering.
- **Next experiment:** EXP-001 — Phase 2 runtime instrumentation and architecture-neutral Locust workload.

---

## EXP-001 — Runtime instrumentation and synthetic workload (Phase 2)

- **Experiment ID:** EXP-001
- **Date:** 2026-07-02
- **Goal:** Record measured per-request traces (SQL, entities, components, duration) and run the same Locust journeys against a configurable BASE_URL.
- **Configuration:** ASGI middleware + SQLAlchemy Engine listeners + service/repository method wrapping. Locust mix 35/20/15/10/10/5/5. Smoke = 5 users / 60s.
- **Input:** Seeded SEMS-R SQLite/Postgres. No historical gold labels.
- **Method:** Execute real HTTP requests; persist traces in memory and optional JSONL; Locust CSV under outputs/performance/.
- **Results:** `pytest monolith/tests` = 17 passed (instrumentation, workload config mix=100, seed idempotence, domain flows). Locust smoke is operator-run against a live `BASE_URL`.
- **Problems:** Per-request CPU/RSS is coarse. Idempotent writes against an already-seeded DB return 409; those are treated as success in Locust.
- **Decision:** Do not fabricate traces. Do not describe Locust mix as production SEMS traffic.
- **Next experiment:** EXP-002 — Phase 3 static/database/runtime evidence package.

---

## EXP-002 — Architectural evidence package (Phase 3)

- **Experiment ID:** EXP-002
- **Date:** 2026-07-14
- **Goal:** Produce `outputs/evidence/architectural_evidence.json` from AST + DB usage + measured traces, without gold service labels.
- **Configuration:** NetworkX graphs G_code, G_call, G_data. Candidate owner = argmax access, ties UNCERTAIN.
- **Input:** `monolith/app`, `reference/domain_description.json`, `reference/migration_rules.json`, optional `outputs/evidence/runtime_traces.jsonl`.
- **Method:** AST visitors; repository-transitive entity access; runtime aggregation of existing JSONL only.
- **Results:** `pytest decomposition/tests monolith/tests` = 27 passed. `make extract-evidence` wrote `outputs/evidence/architectural_evidence.json` (gold labels unused). AST found 26 service/repository/legacy components. Call-graph SCCs: none. Measured traces: 10,505 requests (200×9147, 201×684, 409×672, 401×2). Highest static sharing: Student (7, owner StudentService), Course (6, FacultyService), User (5, UNCERTAIN — shared identity, `app.deps` excluded). CourseEnrollment candidate owner = StudentService, matching the locked gold-owner rule without reading the gold file. PageRank uses power iteration so SciPy is not required for extraction.
- **Problems:** AST call resolution is best-effort (`self.attr` bindings in `__init__`). Runtime 409s remain in the smoke traces. Runtime component×entity counts are request-level co-occurrence, not per-query attribution; they only score edges that already exist from AST.
- **Decision:** Empty runtime section if traces are absent. Never fabricate interactions. Never read historical_architecture.json. Do not treat module-level helpers (`app.deps`) as evaluation components.
- **Next experiment:** EXP-003 — Phase 4 deterministic baselines.

---

## EXP-003 — Deterministic baselines (Phase 4)

- **Experiment ID:** EXP-003
- **Date:** 2026-07-18
- **Goal:** Produce five gold-free decompositions from `architectural_evidence.json`: rule heuristic, Louvain on static calls, Louvain on static call+data, Louvain on runtime co-occurrence, and Louvain on the combined weighted graph.
- **Configuration:** `experiments/configs/baselines.yaml` — seed 42, resolution 1.0, alpha=beta=gamma=1.0, per-layer max-normalization. Weights not fit on gold. Louvain k unconstrained.
- **Input:** `outputs/evidence/architectural_evidence.json` (measured traces included). `reference/domain_description.json` already embedded in that package. `historical_architecture.json` not read.
- **Method:** Name/module/keyword/neighbor rules; NetworkX Louvain on undirected weighted graphs. Runtime edges are cosine co-occurrence of components on measured endpoints.
- **Results:** `pytest` = 35 passed. `make baselines` wrote `outputs/decompositions/`. Rule-based: 8 groups (6 functional areas + `shared_identity` + `uncertain`=`ReportBuilder`). Graph methods discovered 4–5 communities (graph_static 4 / modularity 0.287; static_only 4 / 0.293; runtime_only 5 / 0.186; combined 4 / 0.227). Runtime-only used 10,505 traces; it was not fabricated.
- **Problems:** Rule-based agreement with the six-area layout is inflated by reconstruction naming. Graph partitions mix finance with student/faculty and do not recover six clusters at default resolution. Cross-service call cycles remain after clustering.
- **Decision:** Keep unconstrained Louvain as the published default. Do not retune resolution or weights against gold. Evaluation metrics (pairwise F1, ARI, NMI) are Phase 5.
- **Next experiment:** EXP-004 — Phase 5 evaluation metrics against the hidden reference architecture.

---

## EXP-004 — Evaluation metrics (Phase 5)

- **Experiment ID:** EXP-004
- **Date:** 2026-08-01
- **Goal:** Score Phase 4 decompositions against the historical reference architecture with locked pairwise, clustering, structural, rule-compliance, and migration-priority formulas. Export a blind expert-review packet.
- **Configuration:** 24-component six-way universe (`AuthService`/`UserRepository` excluded; `ReportBuilder` → faculty). Imbalance threshold max share 0.5. Migration weights 0.2 each, not learned. Runtime load used only because traces exist.
- **Input:** `reference/historical_architecture.json` (evaluation only), `outputs/evidence/architectural_evidence.json`, `outputs/decompositions/*.json`.
- **Method:** Pairwise TP/FP/FN; ARI; arithmetic-mean NMI; directed `G_call` coupling/cohesion; machine-checkable RuleCompliance; explicit-weight migration ranking.
- **Results:** `pytest` = 42 passed. Table A pairwise F1: rule_based 0.9245 (precision 1.0, recall 0.8596; the 8 false negatives are `ReportBuilder` vs faculty), combined_graph 0.3866, runtime_only 0.3680, graph_static 0.3333, static_only 0.3167. Graph methods find 4–5 services vs reference 6. Expert/historical ranks left blank.
- **Problems:** Rule-based F1 is inflated by reconstruction naming (documented threat). Database-only ablation was not a Phase 4 method, so Table C uses the four graph evidence variants only. All methods still have at least one cyclic service SCC.
- **Decision:** Formulas are locked in `RESEARCH_DECISIONS.md`. Do not retune baselines against these scores. Do not fabricate expert ranks.
- **Next experiment:** EXP-005 — Phase 6 LLM pipeline (C0–C3).

---

## EXP-005 — LLM pipeline (Phase 6)

- **Experiment ID:** EXP-005
- **Date:** 2026-08-05
- **Goal:** Implement C0–C3 LLM decomposition with provider abstraction, strict JSON, retries, per-run artifacts, and Table B scoring — without putting gold labels in prompts and without fabricating model outputs.
- **Configuration:** `experiments/configs/llm.yaml` — default OpenAI `gpt-4o-mini`, temperature 0.2, 3 runs, max_retries 2, conditions C0–C3. Providers: OpenAI, Anthropic, Gemini, Ollama, mock. Mock runs are `is_scientific_run=false`.
- **Input:** `outputs/evidence/architectural_evidence.json`. C0 = domain + component catalog. C1 adds call/data/runtime summaries. C2 adds R1–R9. C3 adds self-critique. `historical_architecture.json` not read by `decomposition/llm/`.
- **Method:** httpx provider adapters; Pydantic `DecompositionProposal`; retry invalid JSON; store `prompt.txt`, `raw_response.txt`, `parsed.json`, `metadata.json` under `outputs/decompositions/{model}/{condition}/run_NN/`.
- **Results:** `pytest` = 50 passed (prompt gating, JSON parse/retry, no fabrication on invalid output, C3 prompt on real evidence contains no gold filename). No scientific LLM runs: API keys were unset. Table B is empty until a keyed run is executed.
- **Problems:** C0 still sees six functional-area names and class names such as `FacultyService` (reconstruction naming leak). C3 prompt is ~18k characters with runtime endpoint summaries.
- **Decision:** Do not invent LLM decompositions. Scientific results require `make llm-experiments` with a real provider key. Then `make evaluate` writes Table B from runs marked `is_scientific_run=true`.
- **Next experiment:** EXP-006 — Phase 7 experiment matrix (keyed multi-model C0–C3 runs + baseline comparison).

---

## EXP-006 — Experiment matrix runner (Phase 7)

- **Experiment ID:** EXP-006
- **Date:** 2026-08-12
- **Goal:** Add a timestamped matrix runner that freezes extract, baselines, LLM C0–C3, and evaluation into `outputs/runs/YYYY-MM-DD_NNN/` with a manifest. Skip LLM slots honestly when credentials are missing. Do not fabricate Table B.
- **Configuration:** `experiments/configs/matrix.yaml` — seed 42; baselines on; evaluate on; LLM Model A=`gpt-4o-mini`, B=`claude-sonnet-4-20250514`, C=`gemini-2.0-flash` × C0–C3, 3 runs, temperature 0.2, `skip_if_missing_credentials: true`. Command: `python -m experiments.run_all` / `make experiment`.
- **Input:** SEMS-R monolith AST, `outputs/evidence/runtime_traces.jsonl` (copied into the run), `reference/domain_description.json`, `reference/migration_rules.json`. `reference/historical_architecture.json` used only in evaluate.
- **Method:** `experiments/matrix.py` writes frozen configs, evidence, decompositions, metrics, expert packet, `manifest.json`, and a run `README.md`. Gold is lazy-imported only in `_run_evaluate`.
- **Results:** `pytest` = 56 passed. Snapshot `outputs/runs/2026-08-27_001`. Extract/baselines/evaluate ok. LLM A/B/C skipped (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` unset; `fabricated: false`). Table A unchanged vs EXP-004: rule_based F1 0.9245, combined_graph 0.3866, runtime_only 0.3680, graph_static 0.3333, static_only 0.3167. Table B not written. Git commit unavailable (this tree is not a git repository).
- **Problems:** Scientific LLM cells remain empty until a provider key is set. Independent architect ranks remain blank. Reconstruction naming leak still inflates rule-based F1.
- **Decision:** Do not invent LLM or expert numbers. Rerun `make experiment` after setting a provider key; the next snapshot will be `2026-08-27_002` (or the next day's `_001`).
- **Next experiment:** EXP-007 — keyed LLM C0–C3 matrix run (OpenAI + Gemini).

---

## EXP-007 — First scientific LLM matrix (OpenAI + Gemini attempted)

- **Experiment ID:** EXP-007
- **Date:** 2026-08-18
- **Goal:** Run Model A and Model C C0–C3 with real provider keys. Anthropic remains skipped.
- **Configuration:** Same as EXP-006. Snapshot `outputs/runs/2026-08-27_003`. OpenAI and Gemini keys present in the shell; Anthropic absent.
- **Input:** Same SEMS-R evidence package as EXP-006. Gold used only in evaluate.
- **Method:** `make experiment`. Three runs per condition, temperature 0.2. Table B only includes `is_scientific_run=true` parses.
- **Results:** llm-A (`gpt-4o-mini`) scientific: C0 F1 0.8247, C1 0.7333, C2 0.7174, C3 0.7333; rule_compliance 0.8333 all; stability ≥ 0.9901. llm-B skipped (`ANTHROPIC_API_KEY` unset). llm-C called Gemini but **all 12 runs failed** (`parse_ok=false`, `is_scientific_run=false`): HTTP 404 for model `gemini-2.0-flash`. Table B has OpenAI only. Nothing was fabricated for Gemini.
- **Problems:** Matrix step `llm-C: ok` means the provider was invoked, not that outputs parsed. Gemini 404s previously stored the API key in query-string error URLs; artifacts were redacted and the client now sends `x-goog-api-key` instead of `?key=`.
- **Decision:** Do not treat Gemini rows as scientific. Rotate the Gemini key. Confirm a live model id (404 suggests `gemini-2.0-flash` is not available for this key/API), then rerun. OpenAI Table B may be used as SEMS-R measurements.
- **Next experiment:** EXP-008 — Gemini 2.5 Flash C0–C3, reuse OpenAI from EXP-007.

---

## EXP-008 — Gemini 2.5 Flash scientific completion

- **Experiment ID:** EXP-008
- **Date:** 2026-08-22
- **Goal:** Complete Model C with `gemini-2.5-flash` without re-billing OpenAI. Keep Anthropic skipped.
- **Configuration:** `--skip-extract --providers gemini --reuse-llm-from outputs/runs/2026-08-27_003`. Snapshot `outputs/runs/2026-08-27_004`. Temperature 0.2, 3 runs × C0–C3.
- **Input:** Frozen evidence from `outputs/evidence/`. Scientific `gpt-4o-mini` runs copied from EXP-007. Gold used only in evaluate.
- **Method:** Gemini-only matrix slot. Failed `gemini-2.0-flash` dirs from EXP-007 were not copied (`is_scientific_run=false`).
- **Results:** llm-C **12/12 scientific** (`parse_ok=true`). Table B now has both models. Gemini pairwise F1: C0 0.9068, C1 0.8152, C2 0.7835, C3 0.8128; rule_compliance 1.0; stability 0.92–1.0. OpenAI rows unchanged from EXP-007 (C0 0.8247 … C3 0.7333, rule_compliance 0.8333). Table A baselines unchanged (rule_based F1 0.9245). llm-A/B skipped as `--providers gemini`. Nothing fabricated.
- **Problems:** Gemini reports more `uncertain_decisions` (mean 1.7–3.0) and some `unsupported_assumptions`; OpenAI reported none. Adding call-graph/rules/self-critique (C1–C3) did not raise pairwise F1 over C0 for either model on this reconstruction. Anthropic still absent. Reconstruction naming leak still applies.
- **Decision:** Treat `2026-08-27_004` as the two-model scientific snapshot. Do not pool with historical SEMS measurements. Do not add a third model unless a real Anthropic (or substitute) run exists.
- **Next experiment:** EXP-009 — local Llama 3.1 (Ollama) as Model B.

---

## EXP-009 — Llama 3.1 (Ollama) three-model snapshot

- **Experiment ID:** EXP-009
- **Date:** 2026-08-22
- **Goal:** Fill Model B with local Ollama `llama3.1` without re-running OpenAI or Gemini. Anthropic remains unused.
- **Configuration:** `--skip-extract --providers ollama --reuse-llm-from outputs/runs/2026-08-27_004`. Snapshot `outputs/runs/2026-08-27_005`. Temperature 0.2, 3 runs × C0–C3, Ollama `format=json`.
- **Input:** Frozen evidence. Scientific `gpt-4o-mini` and `gemini-2.5-flash` dirs copied from EXP-008. Gold used only in evaluate.
- **Method:** Ollama chat API on localhost. Exact pulled tag should be recorded from `ollama list` (typically 8B when the name is `llama3.1`).
- **Results:** llm-B **12/12 scientific** (`parse_ok=true`; one C2 run used 1 retry). Table B now has three models. Llama pairwise F1: C0 0.9068, C1 0.6173, C2 0.7809, C3 0.5000; rule_compliance 0.67–0.78; C1 stability **0.2712** (unstable). OpenAI and Gemini rows unchanged from EXP-008. Nothing fabricated.
- **Problems:** Llama C1 is unstable across the three runs; C3 F1 is the weakest cell in Table B. Do not treat `llama3.1` as size-matched to Gemini 2.5 Flash. Reconstruction naming leak still applies. Exact Ollama digest/tag was not frozen in the manifest.
- **Decision:** Treat `2026-08-27_005` as the three-model scientific snapshot (A=`gpt-4o-mini`, B=`llama3.1`, C=`gemini-2.5-flash`). Pin the Ollama tag in the paper methods. Do not pool with historical SEMS measurements.
- **Next experiment:** EXP-010 — Phase 8 paper-ready reporting from `2026-08-27_005`.

---

## EXP-010 — Paper-ready reporting (Phase 8)

- **Experiment ID:** EXP-010
- **Date:** 2026-08-23
- **Goal:** Generate IEEE Access-style narrative, tables, and figures from the canonical scientific snapshot without inventing expert ranks, LLM scores, or historical SEMS measurements.
- **Configuration:** `python -m analysis.report --run outputs/runs/2026-08-27_005` / `make report`. SVG figures from Table A–C CSVs (no matplotlib required). Gold is not loaded by `analysis/`.
- **Input:** `outputs/runs/2026-08-27_005/metrics/table_{a,b,c,d}.csv` and `manifest.json`. Expert packet remains unfilled.
- **Method:** `analysis/report.py` copies measured tables, renders bar/grouped-bar SVGs, and writes `paper.md` with RQ1–RQ5 answered only from those numbers.
- **Results:** `outputs/reports/2026-08-27_005/paper.md`. Table A rule_based F1 0.9245 vs combined_graph 0.3866. Table B: C0 strongest for all three models (Gemini/llama 0.9068, gpt-4o-mini 0.8247); C1–C3 did not beat C0. Llama C1 stability 0.2712. Table D llm/expert/historical ranks blank. Nothing fabricated.
- **Problems:** Independent architects still unfilled. Anthropic never run. Reconstruction naming leak still applies. C0 still sees the six functional-area names.
- **Decision:** Treat `2026-08-27_005` plus `outputs/reports/2026-08-27_005/` as the paper snapshot. Do not pool with historical SEMS measurements. Do not fill expert ranks.
- **Addendum (2026-08-28):** Regenerated `paper.md` now cites measured Phase 9–10 artifacts from `outputs/performance/comparisons/` (Modes A–E). Those Locust CSVs are not copied into `outputs/runs/2026-08-27_005` metrics. No rps/latency was invented.
- **Next experiment:** EXP-011 — Phase 9 six-service materialization and gateway.

---

## EXP-011 — Six-service materialization and gateway (Phase 9)

- **Experiment ID:** EXP-011
- **Date:** 2026-08-24
- **Goal:** Materialize the historical six-service architecture as executable FastAPI services with separate logical databases and a gateway that preserves the monolith public API.
- **Configuration:** `microservices/{faculty,student,grade,finance,attendance,library,gateway,identity}`. Compose profile `microservices`. Mode A resource preview in Compose (~4 CPU / 4 GB total). Tests use in-process ASGI peers, not Docker.
- **Input:** Monolith public `/api/v1` contract and documented ownership (Student owns `CourseEnrollment`; gateway owns `User`). Gold file not imported by services.
- **Method:** HTTP peers + local projections. Gateway longest-prefix routing. Seed via `workload/seed_microservices.py` against the gateway.
- **Results:** `pytest microservices/tests` covers login, enrollment gate, finance hold, grade/attendance/library/overview/statistics. Services do not import `app.models` / `app.services` / `app.repositories`. Docker profile `microservices` comes up; gateway `/health` and HTTP seed succeed. Gateway-only Locust smoke: `outputs/performance/2026-08-27_200630_smoke` (5 users, 60s, 8309 requests, 0 failures, locust exit 0). Reconstruction measurement, not production SEMS.
- **Problems:** In-process tests use nested ASGI (not production networking). Smoke is gateway-only and not an equal-resource comparison. Compose `deploy.resources` remains a Mode A preview until Phase 10. No event bus; sync HTTP only.
- **Decision:** Treat this as the reference materialization, not an LLM output. Do not publish the earlier gateway-only smoke latency/RPS in the paper. Phase 10 paired comparison is EXP-012.
- **Next experiment:** EXP-012 — Phase 10 equal-resource Locust comparison (monolith vs gateway).

---

## EXP-012 — Mode A Locust comparison (Phase 10)

- **Experiment ID:** EXP-012
- **Date:** 2026-08-27
- **Goal:** Compare monolith vs six-service gateway under equal total container CPU/RAM using the same synthetic Locust mix and `BASE_URL`.
- **Configuration:** Mode A 4 CPU / 4 GB (`experiments/configs/mode_a.yaml`). Postgres 1 CPU / 1 GB each side. Monolith app 3 CPU / 3 GB. Gateway 0.6 CPU / 768 MB plus six services at 0.4 CPU / 384 MB. Seed `small` via HTTP. Configs `smoke` (5u/60s), `low` (25u/300s), `medium` (50u/300s). Sequential exclusive Compose profiles. Volumes wiped per arm. Inspected cgroup limits applied (`resources_inspected.json`).
- **Input:** Same locustfile, mix 35/20/15/10/10/5/5. Locust on the host, outside the 4/4 budget.
- **Method:** `python -m workload.compare`. Monolith first, then microservices. Do not run both profiles together.
- **Results:** `outputs/performance/comparisons/2026-08-27_201847/`. Reconstruction measurements, not production SEMS.

  | architecture | config | requests | failures | median_ms | p95_ms | p99_ms | rps |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | smoke | 8970 | 0 | 5 | 11 | 17 | 151.6 |
  | monolith | low | 79001 | 0 | 47 | 130 | 160 | 264.0 |
  | monolith | medium | 53314 | 0 | 230 | 450 | 610 | 178.0 |
  | microservices | smoke | 8125 | 1 | 6 | 23 | 59 | 137.3 |
  | microservices | low | 43248 | 4 | 12 | 990 | 1300 | 144.5 |
  | microservices | medium | 14556 | 178 | 100 | 1400 | 30000 | 52.6 |

  Gateway locust exit 1 on all three levels because of HTTP 500s (overview/courses/student/attendance under load). Monolith locust exit 0, zero failures. Medium gateway p99 hit the 30s Locust timeout. Median on the gateway path was often lower than the monolith; the tail and error rate were worse.
- **Problems:** Docker Desktop / Mac hypervisor cgroups, not bare-metal isolation. Locust is outside the budget. Three configs share one seeded database (write amplification in later levels). Sync HTTP only; no event bus. Gateway 500s were not retried or classified beyond Locust failure rows. Not Mode B.
- **Decision:** Publish these numbers only as SEMS-R Mode A measurements. Do not pool with historical SEMS or with the earlier tiny-seed gateway-only smoke (`2026-08-27_200630_smoke`). Do not merge into the Phase 1–8 snapshot `2026-08-27_005`. Do not treat gateway 500s as Locust client bugs without reading `locust_failures.csv`.
- **Next experiment:** Optional Mode B (extra replicas, declared extra resources) or investigation of gateway 500s under the 0.4 CPU service caps. Independent architect ranks remain blank.

### EXP-012 addendum — Mode A `high` (100 users / 300s)

- **Date:** 2026-08-27
- **Artifacts:** `outputs/performance/comparisons/2026-08-27_204815/` (separate bring-up from the smoke/low/medium directory).
- **Results:**

  | architecture | requests | failures | error rate | median_ms | p95_ms | p99_ms | rps |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | 68962 | 101 | 0.15% | 110 | 210 | 290 | 230.7 |
  | microservices | 11402 | 196 | 1.72% | 570 | 30000 | 30000 | 39.5 |

  Gateway p95/p99 are the 30s Locust timeout. Overview still dominates gateway 500s. Monolith failures include a burst of login 500s; tail stayed under 300 ms.
- **Decision:** Stop Mode A at `high`. Do not run `very_high` or `stress` on the 4/4 split. Next load work is Mode B (declared extra resources) or 500-cause inspection. Do not pool with production SEMS.

---

## EXP-013 — Mode B selective scaling, medium Locust

- **Experiment ID:** EXP-013
- **Date:** 2026-08-27
- **Goal:** Ask whether extra CPU/RAM on the Mode A hot path (gateway + student) lets the six-service reconstruction serve the same synthetic medium load as a Mode A monolith.
- **Configuration:** Monolith stays 4 CPU / 4 GB. Microservices 5 CPU / 5248 MB. Declared extras vs Mode A: gateway +0.6 CPU / +768 MB, student +0.4 CPU / +384 MB. Overlay `docker-compose.mode-b.yml`. Inspected limits applied (gateway 1.2 CPU / 1536 MB, student 0.8 CPU / 768 MB). Same locustfile, mix, `small` HTTP seed, `medium` 50 users / 300s.
- **Input:** Not Mode A. Totals are not equal.
- **Method:** `python -m workload.compare --mode B --configs medium`. Sequential exclusive profiles.
- **Results:** `outputs/performance/comparisons/2026-08-27_211409/`. Reconstruction measurements, not production SEMS.

  | architecture | budget | requests | failures | median_ms | p95_ms | p99_ms | rps |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | 4 CPU / 4 GB | 68029 | 24 | 45 | 120 | 150 | 227.0 |
  | microservices | 5 CPU / 5.25 GB | 14561 | 158 | 120 | 1400 | 30000 | 48.6 |

  Mode A medium gateway (equal 4/4, `201847`) was 14556 requests, 178 failures, p95 1400 ms, 52.6 rps. The +1 CPU / +1152 MB bump did not remove the 30s tail or raise RPS. Overview-class 500s remain. Do not treat this session's monolith row as interchangeable with the Mode A `201847` monolith row (different run).
- **Problems:** Extra budget was only two containers. Other services stayed at 0.4 CPU. Docker Desktop, Locust on host. Seed 409s on semester registration are treated as already-applied.
- **Decision:** Mode B medium does not close the gap. Do not run Mode B `high` until a larger declared extra (or replicas) is written down. Do not pool Mode B with Mode A as equal-resource. Do not merge into `2026-08-27_005`.
- **Next experiment:** EXP-014 — Mode C nginx + two replicas, Locust `high`. Independent architect ranks remain blank.


---

## EXP-014 — Mode C nginx load balancer + two replicas, high Locust

- **Experiment ID:** EXP-014
- **Date:** 2026-08-27
- **Goal:** Simulate the operational pattern from the historical cutover (extra service instances behind a load balancer) and measure whether the six-service reconstruction survives the Mode A `high` mix better than a single Mode A monolith.
- **Configuration:** Monolith stays 4 CPU / 4 GB. Microservices **7.25 CPU / 7296 MB**: nginx 0.25 CPU / 128 MB; two replicas of gateway (0.6/768 each) and of each of the six services (0.4/384 each); Postgres still 1 CPU / 1 GB with `max_connections=200`. Overlay `docker-compose.mode-c.yml`. HTTP keepalive disabled. Same locustfile, mix, `small` HTTP seed, `high` 100 users / 300s. Docker Desktop on this host is 8 CPU / ~8 GB. Incomplete first attempt `2026-08-27_214215` (faculty replica `create_all` race) is not a result; schema create now retries.
- **Input:** Not Mode A. Totals are not equal. Not a replay of a historical 10k-request incident.
- **Method:** `python -m workload.compare --mode C --configs high`. Sequential exclusive profiles. Inspected two containers per app service.
- **Results:** `outputs/performance/comparisons/2026-08-27_214907/`. Reconstruction measurements, not production SEMS.

  | architecture | budget | requests | failures | median_ms | p95_ms | p99_ms | rps |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | 4 CPU / 4 GB | 63960 | 86 | 130 | 250 | 350 | 213.5 |
  | microservices | 7.25 CPU / 7.3 GB | 6340 | 698 | 74 | 30000 | 30000 | 22.7 |

  Mode A high gateway (`204815`) was 11402 requests, 196 failures, 39.5 rps. Mode C with nginx and two replicas **did not improve** throughput or tail; RPS fell and failures rose. Overview still dominates 500s. Median on the gateway path can look fine while p95/p99 sit at the 30s Locust timeout. Sixteen app containers plus nginx on an 8 CPU Docker VM share one Postgres; that is not a multi-host production mesh.
- **Problems:** Schema race on first bring-up (fixed with retries). Docker Desktop oversubscription. Serial overview fan-out. Extra nginx hop. Disabled keepalive adds connection setup. One Postgres for all replicas.
- **Decision:** Mode C does not show a microservices runtime win on this testbed. Do not pool with Mode A or Mode B. Do not claim a production 10k-request result. Do not merge into `2026-08-27_005`.
- **Next experiment:** EXP-015 — Mode D starved monolith 2 GB vs microservices 16 GB, Locust `high`.

---

## EXP-015 — Mode D 2 GB monolith vs 16 GB microservices, high Locust

- **Experiment ID:** EXP-015
- **Date:** 2026-08-27
- **Goal:** Give the reconstruction the closest laptop analog of a small legacy box versus a much larger microservice deployment (RAM-asymmetric, not equal-total).
- **Configuration:** Monolith **1.5 CPU / 2 GB** (app 1.0/1536, Postgres 0.5/512). Microservices **10 CPU / 16 GB**: nginx 0.4/256; Postgres 2.0/4096; two replicas of gateway 0.8/1024 and of each of the six services 0.5/832. Overlay `docker-compose.mode-d.yml`. Docker VM inspected at run time: **10 CPU / ~17.5 GB**. Same locustfile, mix, `small` HTTP seed, `high` 100 users / 300s. Inspected cgroup limits applied (monolith 1.0 CPU / 1536 MB; two student replicas 0.5/832 each).
- **Input:** Not Mode A. Totals are not equal. Not a replay of a historical 10k-request incident.
- **Method:** `python -m workload.compare --mode D --configs high`. Sequential exclusive profiles.
- **Results:** `outputs/performance/comparisons/2026-08-27_222327/`. Reconstruction measurements, not production SEMS.

  | architecture | budget | requests | failures | median_ms | p95_ms | p99_ms | rps |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | 1.5 CPU / 2 GB | 53636 | 60 | 170 | 300 | 400 | 179.3 |
  | microservices | 10 CPU / 16 GB | 5746 | 697 | 48 | 30000 | 30000 | 20.8 |

  Starving the monolith to 2 GB did not collapse it at this mix (p99 400 ms, 0.11% errors). The gateway path still sat on 30s Locust timeouts; RPS and failure count are in the same band as Mode C (`214907`: 22.7 rps, 698 failures). Extra RAM did not fix serial overview fan-out.
- **Problems:** One Docker VM, one Postgres, sync HTTP aggregation, Locust 30s ceiling. 16 GB of limits does not turn this into separate production hosts.
- **Decision:** Mode D does not show a microservices runtime win. Do not pool with Mode A/B/C. Do not claim the 2 GB box reproduced a historical 10k-request outage. Do not merge into `2026-08-27_005`. Stop Locust for the paper.
- **Next experiment:** EXP-016 — Mode E dependency-clustered campus vs monolith, equal 4 CPU / 4 GB, Locust `high`. Not a replacement of the historical six-service gold.

---

## EXP-016 — Mode E dependency-clustered campus, high Locust

- **Experiment ID:** EXP-016
- **Date:** 2026-08-28
- **Goal:** Materialize a request-time dependency split (campus process + library HTTP) at the same equal-total budget as Mode A, without replacing the historical six-service gold.
- **Configuration:** Monolith **4 CPU / 4 GB** (app 3.0/3072, Postgres 1.0/1024). Clustered **4 CPU / 4 GB**: Postgres 1.0/1024, campus 2.6/2688, library-clustered 0.4/384. Overlay `docker-compose.mode-e.yml`. Same locustfile, mix, `small` HTTP seed, `high` 100 users / 300s. Inspected cgroup limits applied (campus 2.6 CPU / 2688 MB).
- **Input:** Equal-total with Mode A. Different architecture than the six-service reconstruction. Not a replay of a historical 10k-request incident.
- **Method:** `python -m workload.compare --mode E --configs high`. Sequential exclusive profiles.
- **Results:** `outputs/performance/comparisons/2026-08-27_225302/`. Reconstruction measurements, not production SEMS.

  | architecture | budget | requests | failures | median_ms | p95_ms | p99_ms | rps |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | monolith | 4 CPU / 4 GB | 60048 | 66 | 140 | 270 | 390 | 201.3 |
  | clustered | 4 CPU / 4 GB | 23000 | 4 | 1200 | 2500 | 3100 | 76.9 |

  Clustering the Locust hot path removed the six-service collapse mode (Mode A/D p99 30s, hundreds of HTTP 500s). Clustered p99 was 3.1s with four enrollment 500s. The monolith still completed more requests per second. Locust exit 1 on both sides is from non-zero failures (monolith 66, clustered 4), same harness rule as Mode D.
- **Problems:** One Docker VM, one Postgres, one uvicorn worker per process. In-process ASGI still has hop overhead versus monolith SQL. Overview still makes one HTTP call to library. Campus has 2.6 CPU versus the monolith app's 3.0.
- **Decision:** Mode E shows the six-way gold split was the runtime problem, not Locust concurrency. Do not replace the historical gold materialization. Do not pool Mode E with Mode A six-service numbers as the same architecture. Do not claim clustered beat the monolith. Do not merge into `2026-08-27_005`.
- **Next experiment:** Independent architect ranks remain blank. Paper load tables: Mode A equal-resource six-service; B/C/D declared unequal extras; Mode E a different dependency-clustered architecture at the same 4/4 budget.

---

