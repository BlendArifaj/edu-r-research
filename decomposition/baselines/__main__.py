from __future__ import annotations

import argparse
from pathlib import Path

from decomposition.baselines.runner import run_from_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SEMS-R deterministic decomposition baselines")
    parser.add_argument("--evidence", default="outputs/evidence/architectural_evidence.json")
    parser.add_argument("--out", default="outputs/decompositions")
    parser.add_argument("--config", default="experiments/configs/baselines.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = Path(args.config)
    run_from_paths(
        evidence_path=Path(args.evidence),
        out_dir=Path(args.out),
        config_path=config if config.exists() else None,
    )
    print(f"Wrote baseline decompositions to {args.out}")
    print("These methods did not consume historical gold service assignments.")


if __name__ == "__main__":
    main()
