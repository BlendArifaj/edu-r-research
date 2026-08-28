# Experiments

- Phase 4: `make baselines` — `experiments/configs/baselines.yaml`
- Phase 5: `make evaluate` — scores against `reference/historical_architecture.json`
- Phase 6: `make llm-experiments` — `experiments/configs/llm.yaml` (requires a provider API key)
- Phase 7: `make experiment` — `python -m experiments.run_all` writes `outputs/runs/YYYY-MM-DD_NNN/`

The matrix runs extract → baselines → LLM C0–C3 for configured models → evaluate. Missing API keys skip LLM slots honestly (`fabricated: false`). Gold labels are evaluation-only.

LLM slots: A=`gpt-4o-mini`, B=`llama3.1` (`llama3.1:latest` ~8B), C=`gemini-2.5-flash`.

Canonical scientific snapshot: `outputs/runs/2026-08-27_005`.

- Phase 10: `make compare-load` (Mode A), `make compare-load-mode-b` (Mode B extras), `make compare-load-mode-c` (nginx + replicas), `make compare-load-mode-d` (2 GB vs 16 GB), or `make compare-load-mode-e` (dependency-clustered campus, equal 4/4)
