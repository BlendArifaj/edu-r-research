# Research decisions

This file records methodological choices for the SEMS-R experiment. Do not silently change the experimental methodology. Append a dated entry when a decision changes.

---

## 2026-08-27 — Reconstruction identity

**Decision.** This repository is SEMS-R, a controlled reconstruction. It is not the original SEMS production source.

**Why.** The historical source is unavailable. Claiming otherwise would invalidate the paper.

**What is historical (documented).** Six functional areas (Faculty, Student, Grade, Finance, Attendance, Library); a monolithic application; a shared database; a later six-service migration used as a *reference architecture*, not as infallible ground truth.

**What is synthetic.** Source code, schema, APIs, seed data, Locust mix percentages, and all runtime measurements.

---

## 2026-08-27 — Why FastAPI

**Decision.** Implement SEMS-R in FastAPI + SQLAlchemy 2 rather than attempting to mimic an unknown historical language/stack.

**Why.** The research questions concern architectural evidence and decomposition, not replication of a particular 2000s web framework. FastAPI gives an executable, instrumentable monolith with explicit modules, ORM entities, and HTTP endpoints that static and runtime analyzers can observe. This is a reconstruction of *functional and architectural characteristics*, not a binary-compatible reimplementation.

**Risk.** Framework modernity may understate some legacy coupling patterns (e.g. shared JSP beans). Mitigation: encode coupling in service/repository design (cross-module ORM access, multi-domain transactions, cycles), not in framework choice.

---

## 2026-08-27 — Component granularity (evaluation unit)

**Decision.** Pairwise boundary evaluation uses a documented **component catalog** of application service classes, repository classes, and named legacy utilities — not individual functions and not HTTP routes alone.

**Entity ownership** is evaluated separately via the component × table matrix.

**Why.** Function-level clustering is unstable and not how architects name services. Route-level clustering hides shared services used by many endpoints. Class/module-level components match both static graphs and typical microservice extraction literature.

**Ambiguity flagged.** If a reviewer requires endpoint-level or entity-only clustering, those views can be derived from the same evidence package without retuning methods on the reference labels.

---

## 2026-08-27 — Shared identity (`User`)

**Decision.** In the monolith, `User` is a shared authentication table used by students, staff, teachers, and library members. In the six-service *reference* assignment, `User` is labeled **shared_identity** and is **excluded from the six-way pairwise F1 / ARI / NMI gold clustering**. Data-ownership metrics still report it as a shared entity.

**Why.** Forcing `User` into exactly one of the six historical services would fabricate a historical decision we do not have. Excluding it is more honest than silently stuffing it into Student or Faculty.

**Materialization (Phase 9).** Gateway-owned identity with user IDs passed across services; local projections where needed. Documented as a reconstruction choice. See `microservices/OWNERSHIP.md`.

---

## 2026-08-27 — CourseEnrollment ownership

**Decision.** `CourseEnrollment` is implemented under the student module (registration/enrollment workflow) but is read heavily by Grade and Attendance. The historical reference assigns **ownership** to the Student service.

**Why.** This is a deliberate ambiguous-ownership case: enrollment is a student capability, but grades and attendance are meaningless without it. Methods must decide owner vs. replica vs. API call.

---

## 2026-08-27 — Tests use SQLite; experiments use PostgreSQL

**Decision.** Unit/API tests create an in-memory SQLite schema via SQLAlchemy `create_all`. Docker Compose and load experiments use PostgreSQL 16.

**Why.** Tests must be fast, hermetic, and runnable without Docker. Load and fairness experiments need a realistic shared RDBMS.

**Constraint.** Avoid PostgreSQL-only types so both backends execute the same models.

---

## 2026-08-27 — Workload mix is synthetic

**Decision.** Default Locust mix (student reads 35%, grades 20%, registration 15%, finance 10%, attendance 10%, library 5%, faculty admin 5%) is an **experimental assumption**, not reconstructed production telemetry.

**Why.** No production SEMS traces exist here.

---

## 2026-08-27 — Reference architecture is evaluation-only

**Decision.** `reference/historical_architecture.json` is not imported by `decomposition/` generators. Evaluation code may load it. A CI/test guard should fail if baseline/LLM modules import that path.

---

## 2026-08-27 — Resource fairness for performance

**Decision.** Default comparison Mode A: monolith and the six-service reconstruction receive the **same total** CPU and RAM (initially 4 CPU / 4 GB). Mode B (selective scaling) must report extra resources explicitly.

**Why.** Performance claims without resource accounting are not publishable.

---

## 2026-08-27 — Runtime traces are measured

**Decision.** Request traces record SQLAlchemy `before_cursor_execute` events, service/repository method entry, and wall-clock duration. They are persisted only when requests execute. Empty health/docs traffic is excluded.

**Why.** Fabricated co-occurrence would invalidate RQ4 (which evidence source contributes).

**CPU/RSS.** Per-request CPU is a `resource.getrusage` delta; RSS uses psutil when installed, otherwise omitted. Process-level RSS is not a precise per-request cost.

---

## 2026-08-27 — Locust mix is synthetic and architecture-neutral

**Decision.** Default mix is student_dashboard 35, grades 20, registration 15, finance 10, attendance 10, library 5, faculty_admin 5. The same locustfile targets monolith or gateway via `BASE_URL` only.

Registration/enrollment POSTs are issued only when GET shows the student is not already in that state. Duplicate POSTs against a seeded database return HTTP 409 (correct business rule). Those must not be reported as Locust failures, and they also must not be silently counted as “everything passed” while Uvicorn logs 409. Skip the write instead.

A 409 after a check-then-act POST is treated as a race between virtual users (`OK_CREATE_OR_RACE`), not as a system outage.

**Why.** No production SEMS traces exist. Architecture-specific clients would confound later monolith vs microservice comparison.

---

## 2026-08-27 — Evidence package inputs

**Decision.** `architectural_evidence.json` is built from (1) Python AST of `monolith/app`, (2) component×entity matrix from ORM names and repository wiring, (3) optional measured JSONL traces, (4) documented domain descriptions, (5) migration rules R1–R9.

It must not load `reference/historical_architecture.json`. Candidate owners are `argmax` of static+runtime access with ties labeled `UNCERTAIN`. Sharing degree is the number of distinct accessing components.

Runtime traces record SQL tables and components at **request** granularity, not per-query. `runtime_cooccurrence_count` is therefore “this component ran on a request that queried this table.” It is applied only on edges that already exist from AST (direct entity mention or call into a repository that uses the entity). Runtime co-occurrence cannot create a new component×entity edge.

**Why.** The evidence file is the LLM/baseline input. Gold labels in that file would invalidate the experiment. Treating request-level co-occurrence as access would make every authenticated component appear to own `User` and would make overview-join tables look shared by every nested callee.

---

## 2026-08-27 — Deterministic baseline configuration

**Decision.** Phase 4 methods are:

- **rule_based** — map components to `domain_description` functional-area ids using class-name substrings, module paths, capability keywords, call-graph neighbor majority, then `auth`/`user` identity tokens. Unresolved components are labeled `uncertain` (R9).
- **graph_static** — Louvain on undirected `G_call`.
- **static_only** — Louvain on call + static data-sharing (edge weight `1/sharing_degree`).
- **runtime_only** — Louvain on cosine component co-occurrence from measured endpoints. Empty if traces are missing.
- **combined_graph** — `w = alpha*call + beta*data + gamma*runtime` after per-layer max-normalization.

Default weights are `alpha=beta=gamma=1.0`, `seed=42`, `louvain_resolution=1.0`. Community count is **not** set to six from the reference architecture. Weights must not be fit on gold labels unless a separately labeled oracle experiment is declared.

**Threat to validity.** The reconstruction’s module and class names already follow the six documented functional areas (`faculty_service.py`, `GradeService`, …). The rule baseline can recover that layout without reading gold. That is still a leak of the *reconstruction design*, not of `historical_architecture.json`. Graph baselines do not use those names.

**Why.** RQ5 needs deterministic methods that consume the same evidence package as the later LLM conditions.

---

## 2026-08-27 — Evaluation metric formulas (locked)

**Pairwise membership.** For components `i, j` in the six-way universe (24 components; `AuthService` and `UserRepository` excluded; `ReportBuilder` labeled faculty-adjacent):

- `y(i,j)=1` iff `i` and `j` share a service.
- `TP/FP/FN` compare predicted vs reference pairwise labels.
- `Precision = TP/(TP+FP)`, `Recall = TP/(TP+FN)`, `F1 = 2PR/(P+R)` (0 if P+R=0).
- Missing predicted labels are treated as singletons.

**ARI.** Standard adjusted Rand index from the contingency table, `comb(n,2)` pairs. Degenerate max=expected → 1 if observed=expected else 0.

**NMI.** Arithmetic-mean normalized mutual information: `2 I(X;Y) / (H(X)+H(Y))`. If either entropy is 0, NMI=0.

**Structural (gold-free).** Directed `G_call` edges among assigned components:

- `InterServiceCouplingRatio = cross_service_edges / (internal + cross)`
- `InternalCohesionRatio = internal_edges / (internal + cross)`
- Cycles = strongly connected components of size > 1 on the service-collapsed digraph.

**DB ownership conflicts.** Count of gold-owned entities (excluding `User`) whose evidence `candidate_owner` is `UNCERTAIN` or whose predicted cluster differs from the modal predicted cluster of that entity’s gold service.

**RuleCompliance.** `satisfied_rules / applicable_rules` over: entity at most one owner, no empty services, no extreme imbalance (`max share ≤ 0.5`), no unassigned eval components, no duplicate assignment, cyclic dependencies reported.

**Migration priority (not learned).**

`Priority(s) = (w_ind·Independence + w_coh·Cohesion + w_load·Load + w_data·DataIsolation − w_risk·SizeShare) / Σ|w|`

Defaults `w=0.2` each. If runtime traces are missing, `w_load=0` (not fabricated). `shared_identity` and `uncertain` are not ranked as migration candidates.

**Expert ranks.** Blank until collected. Never fabricated.

---

## 2026-08-27 — LLM conditions C0–C3

**Decision.** Prompts never include `historical_architecture.json` or gold class-to-service labels. C0 is domain description + component catalog. C1 adds static calls, evidence candidate owners, database usage, and measured runtime endpoint summaries (empty if traces are missing). C2 adds rules R1–R9. C3 requires self-critique, unsupported assumptions, UNCERTAIN decisions, and revision. Invalid JSON is retried a bounded number of times; failure stores `parsed.json = null` rather than a guessed architecture. Mock provider output is not a scientific result.

**Why.** RQ2–RQ3 need an evidence ablation and a critique condition. Fabricated completions would invalidate them.

---

## 2026-08-27 — Phase 9 materialization

**Decision.** Materialize the documented six-service reference as independently executable FastAPI apps behind a Python gateway. One PostgreSQL server, seven databases (`sems_identity` plus one per service). No shared ORM across services. Cross-boundary data is IDs, HTTP, and small local projections (`course_projections`, `student_projections`). JWT verification is shared-secret (reconstruction), not a separate IAM product.

**Why.** Phase 10 needs the same Locust mix against `BASE_URL`. A silent shared schema would invalidate the monolith vs microservices contrast.

**Not done here.** Prometheus stack, and materializing LLM-proposed architectures.

---

## 2026-08-27 — Phase 10 Mode A load comparison

**Decision.** Compare monolith vs gateway sequentially under Mode A: 4 CPU / 4 GB total per architecture (Postgres 1/1G; app 3/3G). Microservices split of the app budget is gateway 0.6 CPU / 768 MB plus six services at 0.4 CPU / 384 MB. Seed scale is `small` on both sides **via the public HTTP API** (same client as Locust; host Postgres ports are not used for seed). Default Locust configs are `smoke`, `low`, and `medium`. The same locustfile targets `BASE_URL` only. Locust itself runs on the host and is documented as outside the container budget. Compose profiles never run together. Volumes are wiped per architecture arm so seed is not a leftover tiny dataset.

**Why.** Performance claims without equal totals, equal mix, and equal seed scale are not publishable.

**Not Mode B.** Extra replicas or extra RAM for selected services must be declared separately.

---

## 2026-08-27 — Phase 10 Mode B selective scaling

**Decision.** Mode B keeps the monolith at Mode A 4 CPU / 4 GB and adds resources only on the measured hot path of the six-service reconstruction: gateway 0.6→1.2 CPU and 768→1536 MB; student 0.4→0.8 CPU and 384→768 MB. Declared extra vs Mode A microservices: **+1.0 CPU and +1152 MB**. Microservices Mode B total is 5 CPU / 5248 MB. First Locust config is `medium` (50 users / 300s), same mix and HTTP `small` seed. Overlay file `docker-compose.mode-b.yml`. This table must never be pooled with Mode A as an equal-resource result.

**Why.** Medium Mode A already saturates the 0.4 CPU student service (`/students/1/overview`). Mode B asks whether extra budget on that hop changes the outcome.

---

## 2026-08-27 — Phase 10 Mode C load balancer + replicas

**Decision.** Mode C keeps the monolith at Mode A 4 CPU / 4 GB and scales the six-service reconstruction the way a production cutover adds machines: **nginx on :8000** in front of **two replicas** of gateway and each of the six services. Per-replica CPU/RAM stay at Mode A values. HTTP keepalive is disabled so peer calls are not pinned to one replica. Postgres `max_connections=200`. Declared extra vs Mode A microservices: **+3.25 CPU and +3200 MB** (second replica of seven app services + nginx 0.25 CPU / 128 MB). Microservices Mode C total is **7.25 CPU / 7296 MB**, sized to the Docker Desktop VM on this host (8 CPU / ~8 GB). First Locust config is `high` (100 users / 300s), the level where the unscaled gateway collapsed in Mode A. Overlay `docker-compose.mode-c.yml`. Same locustfile, mix, and HTTP `small` seed. This is **not** a replay of a historical 10k-request production incident. This table must never be pooled with Mode A as an equal-resource result.

**Why.** Mode B showed that raising two container limits without replicas does not remove the 30s tail. The remaining operational question is whether a load balancer plus a second instance of each service changes survival under the same high mix.

---

## 2026-08-27 — Phase 10 Mode D starved monolith vs 16 GB microservices

**Decision.** Mode D sets the monolith to **2 GB / 1.5 CPU** (Postgres 0.5 CPU / 512 MB, app 1.0 CPU / 1536 MB) and the six-service reconstruction to **16 GB / 10 CPU** with nginx and two replicas of each app service, plus Postgres 2 CPU / 4 GB. Overlay `docker-compose.mode-d.yml`. Same locustfile, mix, HTTP `small` seed, Locust `high`. Docker Desktop must report ≥10 CPU and ≥16 GB; the runner refuses to start if the VM is smaller, so the 16 GB budget cannot be a paper-only number. This table must never be pooled with Mode A as an equal-resource result. It is not a replay of a historical 10k-request incident.

**Why.** The remaining operational analogy is a small legacy box versus a much larger microservice deployment, not equal CPU/RAM.

---

## 2026-08-28 — Phase 10 Mode E dependency-clustered campus

**Decision.** Mode E is a **second materialization** for load comparison only. It does **not** replace the historical six-service gold (`reference/historical_architecture.json`) or Phase 9 compose. Faculty, student, grade, finance, attendance, and identity/gateway run in **one campus process** with in-process ASGI peers so overview/enrollment/GPA/attendance joins are not network hops. Library stays a separate HTTP service (weak Locust coupling). Equal-total with Mode A: **4 CPU / 4 GB** (Postgres 1.0/1024, campus 2.6/2688, library 0.4/384). Overlay `docker-compose.mode-e.yml`, profile `clustered`. Same locustfile, mix, HTTP `small` seed, Locust `high`. Architecture name is `clustered`, not `microservices`. Do not pool with Mode A six-service numbers as the same split. Do not merge into `2026-08-27_005`. Not a production 10k-request replay.

**Why.** Modes A–D showed the six-way historical split loses under Locust because student overview fans out over serial blocking HTTP. The remaining question is whether a request-time dependency split (not the gold service count) changes survival at the same equal-total budget.

---
