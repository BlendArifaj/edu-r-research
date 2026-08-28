from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from decomposition.llm.providers import MissingCredentialsError, get_provider
from decomposition.llm.runner import load_config, run_llm_experiments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SEMS-R LLM decomposition conditions C0–C3")
    parser.add_argument("--config", default="experiments/configs/llm.yaml")
    parser.add_argument("--evidence", default="outputs/evidence/architectural_evidence.json")
    parser.add_argument("--out", default="outputs/decompositions")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--condition", action="append", dest="conditions")
    parser.add_argument("--runs", type=int)
    parser.add_argument("--temperature", type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config) if args.config else None)
    provider_name = args.provider or config["provider"]
    model = args.model or config["model"]
    conditions = args.conditions or config["conditions"]
    runs = args.runs if args.runs is not None else int(config["runs"])
    temperature = args.temperature if args.temperature is not None else float(config["temperature"])
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    provider = get_provider(provider_name)
    scientific = provider_name.lower() != "mock"
    try:
        run_llm_experiments(
            evidence=evidence,
            provider=provider,
            model=model,
            conditions=list(conditions),
            runs=runs,
            temperature=temperature,
            max_retries=int(config.get("max_retries", 2)),
            out_dir=Path(args.out),
            scientific=scientific,
        )
    except MissingCredentialsError as exc:
        print(str(exc))
        print("No LLM output was fabricated. Set the provider API key and rerun.")
        sys.exit(2)
    print(f"Wrote LLM runs under {args.out}/{model}/")
    if not scientific:
        print("Mock provider: is_scientific_run=false. Do not report these as LLM results.")


if __name__ == "__main__":
    main()
