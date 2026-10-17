
# EDU-R: Reconstructed Legacy Education System

[![IEEE Access](https://img.shields.io/badge/Published-IEEE%20Access%202026-blue)](https://doi.org/10.1109/ACCESS.2026.3744313)
[![DOI](https://img.shields.io/badge/DOI-10.1109%2FACCESS.2026.3744313-blue)](https://doi.org/10.1109/ACCESS.2026.3744313)

## Associated Publication

**Evidence-Constrained LLMs for Microservice Decomposition:
An Empirical Study on a Reconstructed Legacy System**

- **Journal:** IEEE Access
- **Publisher:** IEEE
- **Year:** 2026
- **DOI:** [10.1109/ACCESS.2026.3744313](https://doi.org/10.1109/ACCESS.2026.3744313)

## About This Repository

This repository provides the research artifacts and replication
package associated with the IEEE Access publication above.

It includes:

- EDU-R, a reconstructed legacy education-management system.
- Architectural evidence extraction and decomposition pipelines.
- Deterministic baselines and LLM-based experiments.
- Evaluation metrics, scoring scripts, and experimental results.
- Identifier-anonymization experiments.
- External validation using Spring PetClinic.
- Monolith and microservice performance experiments.

EDU-R is a controlled software reconstruction and is not the
original production EDU system.

## Reproducibility

The experimental artifacts are preserved under frozen Git tags.

| Study | Frozen Tag |
|---|---|
| Identifier-anonymization experiment | [`ieee-access-revision-control-v1`](https://github.com/BlendArifaj/edu-r-research/releases/tag/ieee-access-revision-control-v1) |
| Gemini 3.8 Flash rerun | [`gemini-38-edur-results`](https://github.com/BlendArifaj/edu-r-research/releases/tag/gemini-38-edur-results) |
| Spring PetClinic external validation | [`petclinic-ext-v1-results`](https://github.com/BlendArifaj/edu-r-research/releases/tag/petclinic-ext-v1-results) |

**Combined replication release:**
[`ieee-access-revision-reproducibility`](https://github.com/BlendArifaj/edu-r-research/releases/tag/ieee-access-revision-reproducibility)

For reproducibility, use the frozen artifacts rather than
modifying the experimental configurations or reference mappings.

## Citation

If you use this repository or its research artifacts,
please cite the associated IEEE Access publication:

**Evidence-Constrained LLMs for Microservice Decomposition:
An Empirical Study on a Reconstructed Legacy System.**
*IEEE Access*, 2026.

DOI: https://doi.org/10.1109/ACCESS.2026.3744313

## Replication package (IEEE Access revision)

This repository is the **official replication package** for the paper:

**Evidence-Constrained LLMs for Microservice Decomposition: An Empirical Study on a Reconstructed Legacy System** (IEEE Access revision).

It contains the EDU-R testbed, frozen experiment definitions, scoring and analysis scripts, committed result tables, and (where included in the tree) raw/parsed LLM outputs used in the revision. Reproduce or audit studies using the tagged releases below—not by editing frozen manifests or reference mappings.

| Study | Tag | Key paths |
| ----- | --- | --------- |
| EDU-R identifier anonymization (REVISION_CONTROL_V1) | [`ieee-access-revision-control-v1`](https://github.com/BlendArifaj/sems-research/releases/tag/ieee-access-revision-control-v1) | `revision_anonymization/`, `outputs/runs/anonymization_exp_v1/` (local/hash manifest) |
| Gemini 3.8 Flash EDU-R rerun (identifier 40 + RQ3 12) | [`gemini-38-edur-results`](https://github.com/BlendArifaj/sems-research/releases/tag/gemini-38-edur-results) | `revision_anonymization/gemini_38_edur/` |
| Spring PetClinic external validation (PETCLINIC_EXT_V1) | [`petclinic-ext-v1-results`](https://github.com/BlendArifaj/sems-research/releases/tag/petclinic-ext-v1-results) | `external_validation_petclinic/`, `outputs/runs/petclinic_ext_v1/`, `outputs/raw/`, `outputs/parsed/`, `outputs/status/` |

**Umbrella reproducibility release:** [`ieee-access-revision-reproducibility`](https://github.com/BlendArifaj/sems-research/releases/tag/ieee-access-revision-reproducibility) — points at the combined revision package commit.

---

**Research integrity statement**

This repository is a **controlled software reconstruction** based on the documented functional and architectural characteristics of the historical EDU case study. **It is not the original production EDU source code.** Runtime measurements, workload results, and decomposition scores produced here are measurements of EDU-R, not of the historical production system. Historical results from prior studies must be kept in a separate dataset and must never be pooled with EDU-R measurements.

Call this system:

- **EDU Experimental Reconstruction**, or
- **EDU-R: Reconstructed Legacy Education System**

## What this repository is

EDU-R is an experimental testbed for an IEEE Access-style study of microservice decomposition. It reconstructs a realistic education-management monolith (six functional areas, one shared database, evolved coupling), extracts architectural evidence, runs deterministic and LLM-based decomposition methods, evaluates boundaries against a **hidden historical reference architecture**, and supports controlled load comparison of the monolith versus a six-service reconstruction.

The six historical services (Faculty, Student, Grade, Finance, Attendance, Library) are a **reference architecture**, not assumed to be perfect ground truth.

## What is not published here

Large or machine-local artifacts may still be gitignored in minimal clones. The **revision reproducibility release** commit may additionally include PetClinic raw/parsed/status files under `outputs/` when present in the repository. Typical local-only paths:

- generated reports and figures (`outputs/reports/`)
- some experiment snapshots (`outputs/runs/` except where committed for replication)
- Locust comparison CSVs (`outputs/performance/`)
- filled expert-review sheets

Copy `.env.example` to `.env`, add your own provider keys, and re-run. Do not commit keys.

## Technology

Python 3.12+, FastAPI, SQLAlchemy 2.x, PostgreSQL, Pydantic, Alembic, pytest. Decomposition and load tooling (NetworkX, scikit-learn, Locust, etc.) are optional extras.

## Phase status

| Phase | Status |
| ----- | ------ |
| 1 Executable monolith | complete |
| 2 Workload and instrumentation | complete |
| 3 Evidence extraction | complete |
| 4 Deterministic baselines | complete |
| 5 Evaluation metrics | complete |
| 6 LLM pipeline | complete |
| 7 Experiment matrix | complete (scientific LLM snapshot `2026-08-27_005`) |
| 8 Reporting | complete |
| 9 Microservice materialization | complete |
| 10 Load/performance comparison | complete (Mode E clustered vs monolith; run locally) |

## Quick start (Phase 1)

```bash
cd sems-research
python3.12 -m venv .venv
source .venv/bin/activate
make setup
make test
```

Seed **before** starting the API. `uvicorn` is a blocking process, so it will never reach the seed command if you start the server first. Re-running seed is safe: it drops and recreates tables by default.

```bash
export SEMS_DATABASE_URL=sqlite:///./sems_r.db
python workload/seed.py --scale tiny --seed 42
python -m uvicorn app.main:app --app-dir monolith --reload
```

Login: `admin@sems-r.local` / `admin123`. API: `http://localhost:8000/docs`.

If the server is already running, stop it (`Ctrl+C`), seed, then start it again. Seeding while Uvicorn holds the SQLite file can lock or leave the running process with a stale schema.

### Phase 2 — runtime traces and synthetic load

Restart Uvicorn after pulling this code so instrumentation is loaded. Optional JSONL sink:

```bash
export SEMS_TRACE_PATH=outputs/evidence/runtime_traces.jsonl
python -m uvicorn app.main:app --app-dir monolith --reload
```

Inspect traces (same JWT as login): `GET /api/v1/research/traces/summary`

Smoke load against the running monolith (60s, 5 users). Locust uses only `BASE_URL` — the same file will later target the gateway:

```bash
make load-smoke-monolith
```

The mix (35/20/15/10/10/5/5) is a **synthetic experimental assumption**, not production EDU traffic. Artifacts land in `outputs/performance/`.

### Phase 3 — architectural evidence

Combines AST static analysis, database-usage matrix, and measured runtime traces. Does **not** read `reference/historical_architecture.json`.

```bash
make extract-evidence
```

Outputs: `outputs/evidence/architectural_evidence.json`, `.md`, plus CSV matrices. If `runtime_traces.jsonl` is missing, the runtime section is empty rather than invented.

### Phase 4 — deterministic baselines

Five methods read the evidence package only. They do **not** read `reference/historical_architecture.json`. Combined-graph weights default to 1/1/1 and are not fit on gold labels. Louvain discovers the number of communities; it is not forced to six.

```bash
make baselines
```

Outputs: `outputs/decompositions/{rule_based,graph_static,static_only,runtime_only,combined_graph}.json`, `assignments.csv`, and `summary.md`.

### Phase 5 — evaluation metrics

Scores decompositions against `reference/historical_architecture.json`. That file is evaluation-only; generators still must not read it. Pairwise F1/ARI/NMI exclude shared identity. Expert ranks stay blank.

```bash
make evaluate
```

Outputs: `outputs/metrics/table_a.md` (and CSV), ablation Table C, migration Table D, `scores.json`, plus a blind packet in `outputs/expert_review/`.

### Phase 6 — LLM pipeline (C0–C3)

Four prompt conditions, pluggable providers (OpenAI, Anthropic, Gemini, Ollama). Prompts do **not** include the historical gold file. Invalid JSON is retried; it is never replaced with a guessed architecture.

```bash
export OPENAI_API_KEY=...   # or XAI_API_KEY / GEMINI_API_KEY / ANTHROPIC_API_KEY / Ollama
make llm-experiments
make evaluate               # writes Table B when scientific runs exist
```

Config: `experiments/configs/llm.yaml`. Each run lands in `outputs/decompositions/{model}/{C0-C3}/run_NN/` (`prompt.txt`, `raw_response.txt`, `parsed.json`, `metadata.json`).

Scientific LLM scores live in snapshot `outputs/runs/2026-08-27_005` (gpt-4o-mini, llama3.1 via Ollama, gemini-2.5-flash × C0–C3). Do not treat mock provider output as a model result.

### Phase 7 — experiment matrix

One command writes a timestamped snapshot under `outputs/runs/YYYY-MM-DD_NNN/` (frozen configs, evidence, decompositions, metrics, expert packet, `manifest.json`). Historical gold is used only in the evaluate step. If LLM provider keys are missing, those slots are recorded as skipped — they are not mocked and scores are not invented.

```bash
make experiment
# or: python -m experiments.run_all
# python -m experiments.run_all --skip-extract   # reuse outputs/evidence
# python -m experiments.run_all --skip-llm       # baselines + evaluate only
# python -m experiments.run_all --skip-extract --providers gemini \
#   --reuse-llm-from outputs/runs/2026-08-27_003
```

Config: `experiments/configs/matrix.yaml` (A=`gpt-4o-mini`, B=`llama3.1` ~8B, C=`gemini-2.5-flash`). Independent architect ranks stay blank until humans fill `outputs/expert_review/`. Do **not** use the Cursor IDE agent as a matrix model — it can read evaluation gold.

Run against PostgreSQL:

```bash
make monolith-up
# wait for health
make health
make seed-monolith
```

The API is at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`.

### Phase 8 — paper-ready reporting

Reads measured Table A–D CSVs from a run snapshot. Does not invent expert ranks, LLM scores, or historical EDU numbers. Default snapshot is `outputs/runs/2026-08-27_005`.

```bash
make report
# or: python -m analysis.report --run outputs/runs/2026-08-27_005
```

Output: `outputs/reports/<run_id>/paper.md` plus copied tables and SVG figures. Independent architect ranks stay blank. Phase 10 Locust rows are cited in that paper from `outputs/performance/comparisons/` and are not merged into the Phase 1–8 metrics snapshot.

### Phase 9 — six-service reconstruction + gateway

Historical/reference materialization under `microservices/`. Each service has its own logical database. Cross-service access is HTTP, not shared ORM. Gateway-owned `User` identity. Same public `/api/v1` routes as the monolith so Locust still uses `BASE_URL` only. Ownership notes: `microservices/OWNERSHIP.md`.

```bash
make microservices-up   # waits until GET /health succeeds
make health
make seed-microservices
make load-smoke-microservices   # same locustfile as the monolith; target the gateway
make microservices-down
```

Do not run monolith and microservices profiles at the same time during a controlled comparison.

### Phase 10 — equal-resource Locust comparison (Mode A)

Both architectures get the **same total** container budget: 4 CPU and 4 GB (Postgres 1 CPU / 1 GB on each side; remaining 3 CPU / 3 GB for the app). Locust runs on the host and is outside that budget. Same locustfile, same synthetic mix, same `small` seed, `BASE_URL` only. Profiles are exclusive and sequential.

```bash
make compare-load
# or: python -m workload.compare
# optional: python -m workload.compare --configs smoke,low
```

Artifacts: `outputs/performance/comparisons/<stamp>/` (`comparison.md`, `comparison.csv`, inspected cgroup limits). Reconstruction measurements, not production EDU.

Mode B gives extra CPU/RAM to gateway and student only (monolith stays at 4/4). Totals are not equal; extras are in `experiments/configs/mode_b.yaml`.

```bash
make compare-load-mode-b
# or: python -m workload.compare --mode B --configs medium
```

Mode C is the operational scale-out pattern (nginx load balancer + two replicas of each app service). Monolith stays at 4/4. Microservices total **7.25 CPU / 7296 MB**. Same locustfile and `small` seed. Default Locust config is `high` (100 users / 300s). This is not equal-resource and not a production 10k-user replay.

```bash
make compare-load-mode-c
# or: python -m workload.compare --mode C --configs high
```

Mode D starves the monolith to **2 GB / 1.5 CPU** and gives microservices **16 GB / 10 CPU** (nginx + two replicas, larger Postgres). Docker Desktop must actually be ≥10 CPU and ≥16 GB. Totals are not equal.

```bash
make compare-load-mode-d
# or: python -m workload.compare --mode D --configs high
```

Mode E is a **dependency-clustered** split, not the historical six-service gold. Faculty, student, grade, finance, and attendance stay in one campus process (in-process ASGI). Library stays HTTP. Equal-total with Mode A (**4 CPU / 4 GB**). Same locustfile, mix, and `small` seed. Default Locust config is `high`.

```bash
make compare-load-mode-e
# or: python -m workload.compare --mode E --configs high
```

Budget lock: `experiments/configs/mode_a.yaml` must match `docker-compose.yml` `deploy.resources.limits`. Mode B overlay: `docker-compose.mode-b.yml`. Mode C overlay: `docker-compose.mode-c.yml`. Mode D overlay: `docker-compose.mode-d.yml`. Mode E overlay: `docker-compose.mode-e.yml`.

## Integrity rules for later experiments

Do **not**:

- feed `reference/historical_architecture.json` to decomposition algorithms;
- tune clustering weights against the reference and report them as unbiased;
- fabricate LLM responses, expert judgments, or runtime measurements;
- describe EDU-R traffic as production EDU traffic;
- compare monolith vs microservices without documenting CPU/RAM/database allocation.

See `RESEARCH_DECISIONS.md` and `EXPERIMENT_LOG.md`.

## License

MIT. Reconstruction artifacts are original code written for the experiment.
