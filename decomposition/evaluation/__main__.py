from __future__ import annotations

import argparse
from pathlib import Path

from decomposition.evaluation.runner import evaluate_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate SEMS-R decompositions against the reference architecture")
    parser.add_argument("--gold", default="reference/historical_architecture.json")
    parser.add_argument("--evidence", default="outputs/evidence/architectural_evidence.json")
    parser.add_argument("--decompositions", default="outputs/decompositions")
    parser.add_argument("--out", default="outputs/metrics")
    parser.add_argument("--expert-out", default="outputs/expert_review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluate_all(
        gold_path=Path(args.gold),
        evidence_path=Path(args.evidence),
        decompositions_dir=Path(args.decompositions),
        out_dir=Path(args.out),
        expert_dir=Path(args.expert_out),
    )
    print(f"Wrote metrics to {args.out}")
    print(f"Wrote expert-review packet to {args.expert_out} (gold labels not included).")


if __name__ == "__main__":
    main()
