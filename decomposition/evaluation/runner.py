from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from decomposition.evaluation.expert_export import export_expert_review
from decomposition.evaluation.gold import load_gold
from decomposition.evaluation.scoring import evaluate_decomposition
from decomposition.evaluation.tables import (
    TABLE_A_FIELDS,
    TABLE_C_FIELDS,
    TABLE_D_FIELDS,
    markdown_table,
    table_a_rows,
    table_c_rows,
    table_d_rows,
    write_csv,
)

METHOD_ORDER = [
    "rule_based",
    "graph_static",
    "static_only",
    "runtime_only",
    "combined_graph",
]


def evaluate_all(
    *,
    gold_path: Path,
    evidence_path: Path,
    decompositions_dir: Path,
    out_dir: Path,
    expert_dir: Path,
    imbalance_max_share: float = 0.5,
) -> dict[str, Any]:
    gold = load_gold(gold_path)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    scores = []
    for method in METHOD_ORDER:
        path = decompositions_dir / f"{method}.json"
        if not path.exists():
            continue
        decomposition = json.loads(path.read_text(encoding="utf-8"))
        scores.append(
            evaluate_decomposition(
                decomposition,
                gold,
                evidence,
                imbalance_max_share=imbalance_max_share,
            )
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scores.json").write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    rows_a = table_a_rows(scores)
    rows_c = table_c_rows(scores)
    rows_d = table_d_rows(scores)
    write_csv(out_dir / "table_a.csv", rows_a, TABLE_A_FIELDS)
    write_csv(out_dir / "table_c.csv", rows_c, TABLE_C_FIELDS)
    write_csv(out_dir / "table_d.csv", rows_d, TABLE_D_FIELDS)
    (out_dir / "table_a.md").write_text(
        markdown_table(rows_a, TABLE_A_FIELDS, "Table A — decomposition-method comparison"),
        encoding="utf-8",
    )
    (out_dir / "table_c.md").write_text(
        markdown_table(rows_c, TABLE_C_FIELDS, "Table C — evidence ablation"),
        encoding="utf-8",
    )
    (out_dir / "table_d.md").write_text(
        markdown_table(rows_d, TABLE_D_FIELDS, "Table D — migration ranking"),
        encoding="utf-8",
    )
    figure_dir = out_dir / "figure_data"
    figure_dir.mkdir(parents=True, exist_ok=True)
    (figure_dir / "baseline_comparison.json").write_text(
        json.dumps({"table_a": rows_a, "table_c": rows_c}, indent=2) + "\n", encoding="utf-8"
    )
    (figure_dir / "call_graph.json").write_text(
        json.dumps((evidence.get("dependencies") or {}).get("G_call") or [], indent=2) + "\n",
        encoding="utf-8",
    )
    export_expert_review(
        evidence,
        expert_dir,
        evidence_markdown=evidence_path.with_suffix(".md"),
    )
    from decomposition.llm.score_runs import score_llm_runs, write_table_b

    llm_aggregates = score_llm_runs(
        gold=gold, evidence=evidence, decompositions_dir=decompositions_dir
    )
    if llm_aggregates:
        write_table_b(llm_aggregates, out_dir)
    summary = _summary(rows_a)
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")
    return {"scores": scores, "table_a": rows_a}


def _summary(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# SEMS-R evaluation (Phase 5)",
        "",
        "Pairwise metrics use the historical reference architecture as labels.",
        "Decomposition methods did not receive those labels as input.",
        "`AuthService` / `UserRepository` are excluded from six-way clustering.",
        "Expert ranks are blank; they were not fabricated.",
        "",
        markdown_table(rows, TABLE_A_FIELDS, "Table A"),
    ]
    return "\n".join(lines)
