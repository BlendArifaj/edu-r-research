"""Score filled expert pairwise sheets. Gold is evaluation-only."""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from typing import Any

from decomposition.evaluation.expert_export import load_pairwise_decisions, pairwise_same_service
from decomposition.evaluation.gold import clustering_labels, load_gold
from decomposition.evaluation.pairwise import precision_recall_f1

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_SHEET_RE = re.compile(r"^pairwise_decisions_exp_(\d+)\.csv$")


def discover_expert_sheets(packet_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in packet_dir.iterdir():
        match = EXP_SHEET_RE.match(path.name)
        if match and path.is_file():
            found[f"exp{int(match.group(1))}"] = path
    return dict(sorted(found.items(), key=lambda item: int(item[0][3:])))


def gold_same_pairs(gold: dict[str, Any]) -> dict[tuple[str, str], bool]:
    labels = clustering_labels(gold)
    return {
        (left, right): labels[left] == labels[right]
        for left, right in combinations(sorted(labels), 2)
    }


def binary_pair_scores(
    pred: dict[tuple[str, str], str],
    gold_same: dict[tuple[str, str], bool],
) -> dict[str, Any]:
    tp = fp = fn = tn = 0
    for pair, same_gold in gold_same.items():
        value = pred.get(pair)
        if value not in {"0", "1"}:
            continue
        predicted = value == "1"
        if same_gold and predicted:
            tp += 1
        elif predicted:
            fp += 1
        elif same_gold:
            fn += 1
        else:
            tn += 1
    counts = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "pairs": tp + fp + fn + tn}
    return {**counts, **precision_recall_f1(counts)}


def agreement(
    left: dict[tuple[str, str], str],
    right: dict[tuple[str, str], str],
) -> dict[str, Any]:
    keys = [
        key
        for key in left
        if left[key] in {"0", "1"} and right.get(key) in {"0", "1"}
    ]
    n = len(keys)
    agree = sum(1 for key in keys if left[key] == right[key])
    n_left = sum(1 for key in keys if left[key] == "1")
    n_right = sum(1 for key in keys if right[key] == "1")
    observed = agree / n if n else 0.0
    expected = (
        (n_left / n) * (n_right / n) + ((n - n_left) / n) * ((n - n_right) / n) if n else 0.0
    )
    kappa = 1.0 if expected == 1 else (observed - expected) / (1 - expected)
    diffs = [
        {"component_i": a, "component_j": b, "left": left[(a, b)], "right": right[(a, b)]}
        for a, b in keys
        if left[(a, b)] != right[(a, b)]
    ]
    return {
        "n": n,
        "agree": agree,
        "observed": round(observed, 4),
        "kappa": round(kappa, 4),
        "n_diff": len(diffs),
        "diffs": diffs,
    }


def score_expert_packet(packet_dir: Path, gold_path: Path) -> dict[str, Any]:
    gold = load_gold(gold_path)
    gold_same = gold_same_pairs(gold)
    sheets = discover_expert_sheets(packet_dir)
    llm_path = packet_dir / "pairwise_decisions_llm.csv"
    maps = {
        name: pairwise_same_service(load_pairwise_decisions(path))
        for name, path in sheets.items()
    }
    if llm_path.is_file():
        maps["llm"] = pairwise_same_service(load_pairwise_decisions(llm_path))
    reviewer_ids = [name for name in maps if name.startswith("exp")]
    vs_gold = {name: binary_pair_scores(pred, gold_same) for name, pred in maps.items()}
    expert_pairs = {
        f"{left}_vs_{right}": agreement(maps[left], maps[right])
        for left, right in combinations(reviewer_ids, 2)
    }
    kappas = [row["kappa"] for row in expert_pairs.values()]
    vs_llm = {
        name: agreement(maps[name], maps["llm"])
        for name in reviewer_ids
        if "llm" in maps
    }
    agreement_payload: dict[str, Any] = {
        "n_reviewers": len(reviewer_ids),
        "reviewer_ids": reviewer_ids,
        "expert_pairs": expert_pairs,
        "mean_pairwise_kappa": round(sum(kappas) / len(kappas), 4) if kappas else None,
        "min_pairwise_kappa": min(kappas) if kappas else None,
        "max_pairwise_kappa": max(kappas) if kappas else None,
        "vs_llm": vs_llm,
    }
    if "exp1_vs_exp2" in expert_pairs:
        agreement_payload["exp1_vs_exp2"] = expert_pairs["exp1_vs_exp2"]
    payload = {
        "integrity": "sems-r-reconstruction-measured",
        "note": (
            "Expert pairwise vs historical six-way eval universe. "
            "Table D migration ranks are not inferred from these sheets."
        ),
        "packet_dir": str(packet_dir),
        "reviewer_ids": reviewer_ids,
        "vs_gold": vs_gold,
        "agreement": agreement_payload,
        "same_service_counts": {
            name: {
                "ones": sum(1 for value in pred.values() if value == "1"),
                "zeros": sum(1 for value in pred.values() if value == "0"),
            }
            for name, pred in maps.items()
        },
    }
    return payload


def write_expert_scores(packet_dir: Path, gold_path: Path | None = None) -> Path:
    gold = gold_path or REPO_ROOT / "reference" / "historical_architecture.json"
    payload = score_expert_packet(packet_dir, gold)
    path = packet_dir / "expert_pairwise_scores.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
