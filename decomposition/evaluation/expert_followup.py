"""Score extract-first rank sheets. Does not use historical gold."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any

from decomposition.evaluation.expert_export import load_pairwise_decisions
from decomposition.evaluation.tables import TABLE_D_FIELDS, write_csv

REPO_ROOT = Path(__file__).resolve().parents[2]
RANK_SHEET_RE = re.compile(r"^migration_ranks_exp_(\d+)\.csv$")
TABLE_D_SERVICES = ("student", "faculty", "finance", "grade", "library", "attendance")
NAME_MAP = {
    "faculty": "faculty",
    "facultyservice": "faculty",
    "student": "student",
    "studentservice": "student",
    "grade": "grade",
    "gradeservice": "grade",
    "finance": "finance",
    "financeservice": "finance",
    "library": "library",
    "libraryservice": "library",
    "attendance": "attendance",
    "attendanceservice": "attendance",
}


def normalize_service_name(name: str) -> str:
    key = "".join(ch for ch in name.lower() if ch.isalnum())
    return NAME_MAP.get(key, "")


def discover_rank_sheets(packet_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in packet_dir.iterdir():
        match = RANK_SHEET_RE.match(path.name)
        if match and path.is_file():
            found[f"exp{int(match.group(1))}"] = path
    return dict(sorted(found.items(), key=lambda item: int(item[0][3:])))


def load_rank_map(path: Path) -> dict[str, int]:
    ranks: dict[str, int] = {}
    for row in load_pairwise_decisions(path):
        service = normalize_service_name(row.get("proposed_service") or row.get("service") or "")
        raw = (row.get("rank") or "").strip()
        if not service or not raw:
            continue
        ranks[service] = int(float(raw))
    return ranks


def median_ranks(per_reviewer: dict[str, dict[str, int]]) -> dict[str, int]:
    medians: dict[str, int] = {}
    for service in TABLE_D_SERVICES:
        values = [ranks[service] for ranks in per_reviewer.values() if service in ranks]
        if values:
            medians[service] = int(statistics.median(values))
    return medians


def score_followup_packet(packet_dir: Path) -> dict[str, Any]:
    sheets = discover_rank_sheets(packet_dir)
    per_reviewer = {name: load_rank_map(path) for name, path in sheets.items()}
    llm_path = packet_dir / "migration_ranks_llm.csv"
    llm = load_rank_map(llm_path) if llm_path.is_file() else {}
    payload = {
        "integrity": "sems-r-reconstruction-measured",
        "note": (
            "Table D ranks mapped from FacultyService/StudentService-style names onto the six "
            "functional-area rows. AuthService and ReportingService are omitted because they "
            "are not Table D services. Historical extract order does not exist. "
            "Grouping sheets used different proposed-service names than these rank sheets."
        ),
        "packet_dir": str(packet_dir),
        "reviewer_ids": list(per_reviewer),
        "per_reviewer": per_reviewer,
        "llm_rank": {service: llm[service] for service in TABLE_D_SERVICES if service in llm},
        "expert_rank": median_ranks(per_reviewer),
        "historical_rank": {},
    }
    return payload


def write_followup_scores(packet_dir: Path) -> Path:
    payload = score_followup_packet(packet_dir)
    path = packet_dir / "expert_followup_scores.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def apply_table_d_ranks(table_d: list[dict[str, Any]], followup: dict[str, Any]) -> list[dict[str, str]]:
    llm = followup.get("llm_rank") or {}
    expert = followup.get("expert_rank") or {}
    rows = []
    for row in table_d:
        service = str(row.get("service") or "")
        updated = dict(row)
        if service in llm:
            updated["llm_rank"] = str(llm[service])
        if service in expert:
            updated["expert_rank"] = str(expert[service])
        rows.append({key: "" if updated.get(key) is None else str(updated.get(key)) for key in TABLE_D_FIELDS})
    return rows


def write_table_d(metrics_dir: Path, rows: list[dict[str, str]]) -> None:
    write_csv(metrics_dir / "table_d.csv", rows, TABLE_D_FIELDS)
    lines = [f"# Table D — migration ranking", ""]
    lines.append("| " + " | ".join(TABLE_D_FIELDS) + " |")
    lines.append("| " + " | ".join("---" for _ in TABLE_D_FIELDS) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key) or "") for key in TABLE_D_FIELDS) + " |")
    lines += [
        "",
        "SEMS-R reconstruction. `llm_rank` is Gemini C0 run 1 `migration_priority` mapped onto "
        "the six Table D names. `expert_rank` is the median of five extract-first sheets. "
        "`historical_rank` is blank: no documented historical extract order exists.",
        "",
    ]
    (metrics_dir / "table_d.md").write_text("\n".join(lines), encoding="utf-8")
