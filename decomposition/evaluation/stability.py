from __future__ import annotations

from itertools import combinations
from statistics import mean, pstdev
from typing import Any

from decomposition.evaluation.pairwise import pairwise_scores


def stability(runs: list[dict[str, str]]) -> dict[str, Any]:
    """Mean pairwise F1 among repeated decompositions of the same method."""
    if len(runs) < 2:
        return {
            "n_runs": len(runs),
            "mean": 1.0 if runs else None,
            "stdev": None,
            "min": 1.0 if runs else None,
            "max": 1.0 if runs else None,
            "note": "Single run; stability is defined as 1.0 for a deterministic method.",
        }
    scores = []
    for left, right in combinations(runs, 2):
        scores.append(pairwise_scores(left, right)["f1"])
    return {
        "n_runs": len(runs),
        "mean": round(mean(scores), 4),
        "stdev": round(pstdev(scores), 4) if len(scores) > 1 else 0.0,
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "note": "mean(pairwise_F1(run_i, run_j)) over run pairs.",
    }
