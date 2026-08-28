PYTHON ?= python3
COMPOSE := docker compose

.PHONY: setup test lint fmt seed monolith-up monolith-down seed-monolith wait-health health load-smoke-monolith load-low-monolith load-medium-monolith load-high-monolith extract-evidence baselines evaluate llm-experiments experiment report microservices-up microservices-down seed-microservices load-smoke-microservices compare-load compare-load-mode-b compare-load-mode-c compare-load-mode-d compare-load-mode-e

setup:
	$(PYTHON) -m pip install -e ".[dev,load]"

test:
	$(PYTHON) -m pytest monolith/tests decomposition/tests experiments/tests analysis/tests microservices/tests workload/tests

lint:
	$(PYTHON) -m ruff check monolith workload
	$(PYTHON) -m black --check monolith workload
	$(PYTHON) -m mypy

fmt:
	$(PYTHON) -m ruff check --fix monolith workload
	$(PYTHON) -m black monolith workload

wait-health:
	@for i in $$(seq 1 40); do \
		if curl -sf --max-time 2 http://127.0.0.1:8000/health >/dev/null; then \
			curl -sf http://127.0.0.1:8000/health; echo; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "API at http://127.0.0.1:8000/health did not become ready in 40s"; \
	exit 1

monolith-up:
	$(COMPOSE) --profile monolith up --build -d
	$(MAKE) wait-health

monolith-down:
	$(COMPOSE) --profile monolith down

microservices-up:
	$(COMPOSE) --profile microservices up --build -d
	$(MAKE) wait-health

microservices-down:
	$(COMPOSE) --profile microservices down

seed:
	$(PYTHON) workload/seed.py --scale small --seed 42

seed-monolith: seed

seed-microservices:
	$(PYTHON) workload/seed_microservices.py --scale tiny --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

health: wait-health

load-smoke-monolith:
	$(PYTHON) workload/run_load.py --config smoke --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

load-low-monolith:
	$(PYTHON) workload/run_load.py --config low --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

load-medium-monolith:
	$(PYTHON) workload/run_load.py --config medium --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

load-high-monolith:
	$(PYTHON) workload/run_load.py --config high --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

load-smoke-microservices:
	$(PYTHON) workload/run_load.py --config smoke --base-url $${SEMS_BASE_URL:-http://127.0.0.1:8000}

compare-load:
	$(PYTHON) -m workload.compare

compare-load-mode-b:
	$(PYTHON) -m workload.compare --mode B --configs medium

compare-load-mode-c:
	$(PYTHON) -m workload.compare --mode C --configs high

compare-load-mode-d:
	$(PYTHON) -m workload.compare --mode D --configs high

compare-load-mode-e:
	$(PYTHON) -m workload.compare --mode E --configs high

extract-evidence:
	$(PYTHON) -m decomposition.extraction --app-root monolith/app --traces outputs/evidence/runtime_traces.jsonl --out outputs/evidence

baselines:
	$(PYTHON) -m decomposition.baselines --evidence outputs/evidence/architectural_evidence.json --out outputs/decompositions --config experiments/configs/baselines.yaml

evaluate:
	$(PYTHON) -m decomposition.evaluation --gold reference/historical_architecture.json --evidence outputs/evidence/architectural_evidence.json --decompositions outputs/decompositions --out outputs/metrics --expert-out outputs/expert_review

llm-experiments:
	$(PYTHON) -m decomposition.llm --config experiments/configs/llm.yaml --evidence outputs/evidence/architectural_evidence.json --out outputs/decompositions

experiment:
	$(PYTHON) -m experiments.run_all $(EXPERIMENT_ARGS)

report:
	$(PYTHON) -m analysis.report --run $${REPORT_RUN:-outputs/runs/2026-08-27_005}
