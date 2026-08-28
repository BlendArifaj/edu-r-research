from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from decomposition.evaluation.gold import load_gold
from decomposition.evaluation.scoring import evaluate_decomposition
from decomposition.evaluation.stability import stability
from decomposition.evaluation.tables import TABLE_B_FIELDS, markdown_table, table_b_rows, write_csv


def score_llm_runs(
    *,
    gold: dict[str, Any],
    evidence: dict[str, Any],
    decompositions_dir: Path,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for parsed_path in sorted(decompositions_dir.glob("*/*/run_*/parsed.json")):
        meta_path = parsed_path.with_name("metadata.json")
        if not meta_path.exists():
            continue
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if not metadata.get("is_scientific_run"):
            continue
        payload = json.loads(parsed_path.read_text(encoding="utf-8"))
        if not payload or not payload.get("available"):
            continue
        scored = evaluate_decomposition(payload, gold, evidence)
        scored["model"] = metadata.get("model")
        scored["condition"] = metadata.get("condition")
        scored["run_number"] = metadata.get("run_number")
        scored["unsupported_assumptions"] = payload.get("unsupported_assumptions") or []
        key = (str(metadata.get("model")), str(metadata.get("condition")))
        grouped.setdefault(key, []).append(scored)
    aggregates = []
    for (model, condition), runs in sorted(grouped.items()):
        assignments = _assignments_for(decompositions_dir, model, condition)
        stab = stability(assignments)
        aggregates.append(
            {
                "model": model,
                "condition": condition,
                "n_runs": len(runs),
                "pairwise_f1": round(mean(run["pairwise"]["f1"] for run in runs), 4),
                "rule_compliance": round(mean(run["rule_compliance"] for run in runs), 4),
                "stability": stab.get("mean"),
                "uncertain_decisions": round(
                    mean(run.get("uncertain_decisions") or 0 for run in runs), 4
                ),
                "unsupported_assumptions": round(
                    mean(len(run.get("unsupported_assumptions") or []) for run in runs), 4
                ),
                "runs": runs,
                "stability_detail": stab,
            }
        )
    return aggregates


def write_table_b(aggregates: list[dict[str, Any]], out_dir: Path) -> None:
    rows = table_b_rows(aggregates)
    write_csv(out_dir / "table_b.csv", rows, TABLE_B_FIELDS)
    (out_dir / "table_b.md").write_text(
        markdown_table(rows, TABLE_B_FIELDS, "Table B — LLM experimental conditions"),
        encoding="utf-8",
    )
    (out_dir / "llm_scores.json").write_text(json.dumps(aggregates, indent=2) + "\n", encoding="utf-8")


def score_and_write(
    *,
    gold_path: Path,
    evidence_path: Path,
    decompositions_dir: Path,
    out_dir: Path,
) -> list[dict[str, Any]]:
    gold = load_gold(gold_path)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    aggregates = score_llm_runs(gold=gold, evidence=evidence, decompositions_dir=decompositions_dir)
    if aggregates:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_table_b(aggregates, out_dir)
    return aggregates


def _assignments_for(decompositions_dir: Path, model: str, condition: str) -> list[dict[str, str]]:
    assignments = []
    safe_model = model.replace("/", "-").replace(" ", "_")
    for parsed_path in sorted((decompositions_dir / safe_model / condition).glob("run_*/parsed.json")):
        payload = json.loads(parsed_path.read_text(encoding="utf-8"))
        if payload and payload.get("available") and payload.get("component_assignment"):
            assignments.append(payload["component_assignment"])
    return assignments
