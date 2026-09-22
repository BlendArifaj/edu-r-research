#!/usr/bin/env python3
"""Independent Table I (Table A) metric recomputation. Read-only on source artifacts."""

from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RUN = REPO / "outputs" / "runs" / "2026-08-27_005"
GOLD_PATH = REPO / "reference" / "historical_architecture.json"
DECOMP_DIR = RUN / "decompositions"
TABLE_A_CSV = RUN / "metrics" / "table_a.csv"
OUT_DIR = Path(__file__).resolve().parent

METHOD_FILES = {
    "rule_based": DECOMP_DIR / "rule_based.json",
    "graph_static": DECOMP_DIR / "graph_static.json",
    "static_only": DECOMP_DIR / "static_only.json",
    "runtime_only": DECOMP_DIR / "runtime_only.json",
    "combined_graph": DECOMP_DIR / "combined_graph.json",
}


def load_gold_labels() -> dict[str, str]:
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    assignment: dict[str, str] = {}
    for service, payload in (gold.get("services") or {}).items():
        for component in payload.get("components") or []:
            assignment[str(component)] = str(service)
    extra = (gold.get("evaluation_notes") or {}).get("legacy_components_in_six_way") or {}
    for component, service in extra.items():
        assignment[str(component)] = str(service)
    excluded = set(gold.get("shared_identity", {}).get("components") or [])
    return {k: v for k, v in sorted(assignment.items()) if k not in excluded}


def pred_labels(decomp: dict[str, Any], universe: list[str]) -> dict[str, str]:
    raw = decomp.get("component_assignment") or {}
    return {name: str(raw.get(name, f"__unassigned_{name}")) for name in universe}


def pairwise_independent(y_true: dict[str, str], y_pred: dict[str, str]) -> dict[str, Any]:
    items = sorted(y_true)
    assert items == sorted(y_pred)
    tp = fp = fn = tn = 0
    for left, right in combinations(items, 2):
        same_true = y_true[left] == y_true[right]
        same_pred = y_pred[left] == y_pred[right]
        if same_true and same_pred:
            tp += 1
        elif same_pred:
            fp += 1
        elif same_true:
            fn += 1
        else:
            tn += 1
    pairs = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "pairs": pairs,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def contingency(true_labels: list[str], pred_labels_list: list[str]) -> list[list[int]]:
    true_ids = {label: i for i, label in enumerate(sorted(set(true_labels)))}
    pred_ids = {label: i for i, label in enumerate(sorted(set(pred_labels_list)))}
    table = [[0] * len(pred_ids) for _ in true_ids]
    for t, p in zip(true_labels, pred_labels_list):
        table[true_ids[t]][pred_ids[p]] += 1
    return table


def ari_independent(y_true: dict[str, str], y_pred: dict[str, str]) -> float:
    names = sorted(y_true)
    t = [y_true[n] for n in names]
    p = [y_pred[n] for n in names]
    table = contingency(t, p)
    n = len(names)
    sum_comb = sum(
        c * (c - 1) / 2 for row in table for c in row if c >= 2
    )
    sum_rows = sum(sum(row) * (sum(row) - 1) / 2 for row in table if sum(row) >= 2)
    col_counts = [sum(table[r][c] for r in range(len(table))) for c in range(len(table[0]))]
    sum_cols = sum(c * (c - 1) / 2 for c in col_counts if c >= 2)
    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 1.0
    expected = (sum_rows * sum_cols) / total_pairs
    max_index = 0.5 * (sum_rows + sum_cols)
    if max_index == expected:
        return 1.0 if sum_comb == expected else 0.0
    return (sum_comb - expected) / (max_index - expected)


def entropy(labels: list[str]) -> float:
    n = len(labels)
    if n == 0:
        return 0.0
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return -sum((c / n) * math.log(c / n) for c in counts.values())


def nmi_independent(y_true: dict[str, str], y_pred: dict[str, str]) -> float:
    """Arithmetic-mean NMI: 2*I(X;Y)/(H(X)+H(Y)) — matches decomposition/evaluation/pairwise.py."""
    names = sorted(y_true)
    t = [y_true[n] for n in names]
    p = [y_pred[n] for n in names]
    n = len(names)
    table = contingency(t, p)
    col_totals = [sum(table[r][c] for r in range(len(table))) for c in range(len(table[0]))]
    mi = 0.0
    for r, row in enumerate(table):
        row_sum = sum(row)
        for c, n_ij in enumerate(row):
            col_sum = col_totals[c]
            if n_ij == 0 or row_sum == 0 or col_sum == 0:
                continue
            mi += (n_ij / n) * math.log((n_ij * n) / (row_sum * col_sum))
    h_true = entropy(t)
    h_pred = entropy(p)
    if h_true + h_pred == 0:
        return 1.0
    if h_true == 0 or h_pred == 0:
        return 0.0
    return 2 * mi / (h_true + h_pred)


def load_manuscript_table_a() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    if not TABLE_A_CSV.is_file():
        return rows
    with TABLE_A_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[row["method"]] = row
    return rows


def main() -> None:
    gold = load_gold_labels()
    universe = sorted(gold)
    n = len(universe)
    expected_pairs = n * (n - 1) // 2
    manuscript = load_manuscript_table_a()

    # Reference assignments export
    assign_path = OUT_DIR / "table_i_reference_assignment.csv"
    with assign_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["component", "reference_service"])
        writer.writeheader()
        for name in universe:
            writer.writerow({"component": name, "reference_service": gold[name]})

    results: list[dict[str, Any]] = []
    for method, path in METHOD_FILES.items():
        decomp = json.loads(path.read_text(encoding="utf-8"))
        pred = pred_labels(decomp, universe)
        pair = pairwise_independent(gold, pred)
        ari = ari_independent(gold, pred)
        nmi = nmi_independent(gold, pred)
        ms = manuscript.get(method, {})
        results.append(
            {
                "method": method,
                "precision": pair["precision"],
                "recall": pair["recall"],
                "pairwise_f1": pair["f1"],
                "ari": ari,
                "nmi": nmi,
                "pairs": pair["pairs"],
                "tp": pair["tp"],
                "fp": pair["fp"],
                "fn": pair["fn"],
                "tn": pair["tn"],
                "manuscript_f1": ms.get("pairwise_f1"),
                "manuscript_ari": ms.get("ari"),
                "manuscript_nmi": ms.get("nmi"),
            }
        )
        pred_path = OUT_DIR / f"table_i_predicted_{method}.csv"
        with pred_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["component", "predicted_cluster"])
            writer.writeheader()
            for name in universe:
                writer.writerow({"component": name, "predicted_cluster": pred[name]})

    out_csv = OUT_DIR / "table_i_recomputed.csv"
    fields = [
        "method",
        "precision",
        "recall",
        "pairwise_f1",
        "ari",
        "nmi",
        "pairs",
        "manuscript_f1",
        "manuscript_ari",
        "manuscript_nmi",
        "f1_delta_vs_manuscript",
        "ari_delta_vs_manuscript",
        "nmi_delta_vs_manuscript",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    **{k: row[k] for k in fields if k in row and not k.endswith("_delta_vs_manuscript")},
                    "precision": f"{row['precision']:.6f}",
                    "recall": f"{row['recall']:.6f}",
                    "pairwise_f1": f"{row['pairwise_f1']:.6f}",
                    "ari": f"{row['ari']:.6f}",
                    "nmi": f"{row['nmi']:.6f}",
                    "f1_delta_vs_manuscript": _delta(row["pairwise_f1"], row["manuscript_f1"]),
                    "ari_delta_vs_manuscript": _delta(row["ari"], row["manuscript_ari"]),
                    "nmi_delta_vs_manuscript": _delta(row["nmi"], row["manuscript_nmi"]),
                }
            )

    summary = {
        "n_eval_components": n,
        "expected_unordered_pairs": expected_pairs,
        "c_24_2": math.comb(24, 2) if n == 24 else None,
        "all_methods_same_pair_count": all(r["pairs"] == expected_pairs for r in results),
        "f1_equals_ari_any_method": any(
            abs(r["pairwise_f1"] - r["ari"]) < 1e-9 for r in results
        ),
        "f1_equals_nmi_any_method": any(
            abs(r["pairwise_f1"] - r["nmi"]) < 1e-9 for r in results
        ),
    }
    (OUT_DIR / "table_i_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(f"Wrote {out_csv}")


def _delta(computed: float, manuscript: str | None) -> str:
    if manuscript is None or manuscript == "":
        return ""
    try:
        return f"{computed - float(manuscript):.6f}"
    except ValueError:
        return ""


if __name__ == "__main__":
    main()
