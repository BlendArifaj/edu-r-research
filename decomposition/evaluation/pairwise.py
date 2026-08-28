from __future__ import annotations

from itertools import combinations
from math import comb, log
from typing import Any


def pairwise_counts(y_true: dict[str, str], y_pred: dict[str, str]) -> dict[str, int]:
    items = sorted(y_true)
    tp = fp = fn = tn = 0
    for left, right in combinations(items, 2):
        same_true = y_true[left] == y_true[right]
        same_pred = _label(y_pred, left) == _label(y_pred, right)
        if same_true and same_pred:
            tp += 1
        elif same_pred:
            fp += 1
        elif same_true:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "pairs": tp + fp + fn + tn}


def precision_recall_f1(counts: dict[str, int]) -> dict[str, float]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def pairwise_scores(y_true: dict[str, str], y_pred: dict[str, str]) -> dict[str, Any]:
    counts = pairwise_counts(y_true, y_pred)
    scores = precision_recall_f1(counts)
    return {**counts, **scores}


def adjusted_rand_index(y_true: dict[str, str], y_pred: dict[str, str]) -> float:
    names = sorted(y_true)
    if len(names) < 2:
        return 1.0
    true_labels = [y_true[name] for name in names]
    pred_labels = [_label(y_pred, name) for name in names]
    table = _contingency(true_labels, pred_labels)
    n = len(names)
    sum_comb = sum(comb(n_ij, 2) for row in table for n_ij in row if n_ij >= 2)
    sum_rows = sum(comb(sum(row), 2) for row in table if sum(row) >= 2)
    col_counts = [sum(row[col] for row in table) for col in range(len(table[0]))] if table else []
    sum_cols = sum(comb(count, 2) for count in col_counts if count >= 2)
    total_pairs = comb(n, 2)
    if total_pairs == 0:
        return 1.0
    expected = (sum_rows * sum_cols) / total_pairs
    max_index = 0.5 * (sum_rows + sum_cols)
    if max_index == expected:
        return 1.0 if sum_comb == expected else 0.0
    return (sum_comb - expected) / (max_index - expected)


def normalized_mutual_information(y_true: dict[str, str], y_pred: dict[str, str]) -> float:
    """Arithmetic-mean NMI: 2I(X;Y) / (H(X)+H(Y)). Degenerate partitions → 0."""
    names = sorted(y_true)
    true_labels = [y_true[name] for name in names]
    pred_labels = [_label(y_pred, name) for name in names]
    n = len(names)
    if n == 0:
        return 1.0
    table = _contingency(true_labels, pred_labels)
    col_totals = [sum(table[row][col] for row in range(len(table))) for col in range(len(table[0]))]
    mi = 0.0
    for row in table:
        row_sum = sum(row)
        for n_ij, col_sum in zip(row, col_totals):
            if n_ij == 0 or row_sum == 0 or col_sum == 0:
                continue
            mi += (n_ij / n) * log((n_ij * n) / (row_sum * col_sum))
    h_true = _entropy(true_labels)
    h_pred = _entropy(pred_labels)
    if h_true + h_pred == 0:
        return 1.0
    if h_true == 0 or h_pred == 0:
        return 0.0
    return 2 * mi / (h_true + h_pred)


def _label(assignment: dict[str, str], name: str) -> str:
    if name in assignment:
        return assignment[name]
    return f"__unassigned_{name}"


def _contingency(true_labels: list[str], pred_labels: list[str]) -> list[list[int]]:
    true_ids = {label: index for index, label in enumerate(sorted(set(true_labels)))}
    pred_ids = {label: index for index, label in enumerate(sorted(set(pred_labels)))}
    table = [[0] * len(pred_ids) for _ in true_ids]
    for true, pred in zip(true_labels, pred_labels):
        table[true_ids[true]][pred_ids[pred]] += 1
    return table


def _entropy(labels: list[str]) -> float:
    n = len(labels)
    if n == 0:
        return 0.0
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return -sum((count / n) * log(count / n) for count in counts.values() if count)
