from __future__ import annotations

import argparse
from pathlib import Path

from experiments.matrix import run_matrix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SEMS-R experiment matrix into a timestamped run directory"
    )
    parser.add_argument("--config", default="experiments/configs/matrix.yaml")
    parser.add_argument("--skip-extract", action="store_true")
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument(
        "--providers",
        nargs="+",
        default=None,
        help="Run only these LLM providers (e.g. gemini). Others are skipped, not fabricated.",
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        default=None,
        help="Run only these matrix slot ids (e.g. D). Others are skipped, not fabricated.",
    )
    parser.add_argument(
        "--reuse-llm-from",
        default=None,
        help="Copy scientific LLM run dirs from a previous snapshot before running new slots.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    config = Path(args.config)
    if not config.is_absolute():
        config = repo_root / args.config
    reuse = Path(args.reuse_llm_from) if args.reuse_llm_from else None
    if reuse is not None and not reuse.is_absolute():
        reuse = repo_root / reuse
    manifest = run_matrix(
        repo_root=repo_root,
        config_path=config,
        skip_extract=args.skip_extract,
        skip_llm=args.skip_llm,
        only_providers=args.providers,
        only_ids=args.ids,
        reuse_llm_from=reuse,
    )
    print(f"Wrote experiment snapshot to {manifest['run_dir']}")
    skipped = [step for step in manifest["steps"] if step.get("status") == "skipped"]
    failed = [step for step in manifest["steps"] if step.get("status") == "failed"]
    if skipped:
        print(f"Skipped {len(skipped)} LLM slot(s); nothing was fabricated.")
    if failed:
        print(f"{len(failed)} LLM slot(s) failed to produce scientific parses.")


if __name__ == "__main__":
    main()
