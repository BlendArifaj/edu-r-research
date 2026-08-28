from __future__ import annotations

import csv
import json
import shutil
from itertools import combinations
from pathlib import Path
from typing import Any


def export_expert_review(
    evidence: dict[str, Any],
    out_dir: Path,
    evidence_markdown: Path | None = None,
) -> None:
    """Blind architect packet. Does not include historical service assignments."""
    out_dir.mkdir(parents=True, exist_ok=True)
    components = [
        {
            "name": row.get("name"),
            "module": row.get("module"),
            "kind": row.get("kind"),
        }
        for row in evidence.get("components") or []
        if row.get("name")
    ]
    names = [str(row["name"]) for row in components]
    _write_csv(
        out_dir / "component_list.csv",
        components,
        ["name", "module", "kind"],
    )
    pairs = [{"component_i": left, "component_j": right, "same_service": "", "confidence": "", "notes": ""}
             for left, right in combinations(sorted(names), 2)]
    _write_csv(
        out_dir / "pairwise_decisions.csv",
        pairs,
        ["component_i", "component_j", "same_service", "confidence", "notes"],
    )
    (out_dir / "system_description.md").write_text(_system_description(evidence), encoding="utf-8")
    (out_dir / "evaluation_form.md").write_text(
        _evaluation_form(len(names), len(pairs), include_llm_example=True),
        encoding="utf-8",
    )
    if evidence_markdown and evidence_markdown.exists():
        (out_dir / "architectural_evidence.md").write_text(
            evidence_markdown.read_text(encoding="utf-8"), encoding="utf-8"
        )
    else:
        (out_dir / "architectural_evidence.md").write_text(
            json.dumps(
                {
                    "note": "Place architectural_evidence.md here. Gold service labels are not included.",
                    "component_count": len(names),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def _system_description(evidence: dict[str, Any]) -> str:
    domain = evidence.get("domain_descriptions") or {}
    system = domain.get("system") or evidence.get("system") or {}
    lines = [
        "# SEMS-R system description (expert review)",
        "",
        "This packet is for independent architect evaluation.",
        "It does **not** include the historical six-service reference assignment.",
        "",
        system.get("description") or system.get("integrity") or "",
        "",
        "## Documented functional areas",
        "",
    ]
    for area in domain.get("functional_areas") or []:
        lines.append(f"### {area.get('id')}")
        for cap in area.get("capabilities") or []:
            lines.append(f"- {cap}")
        lines.append("")
    lines += [
        "## Known cross-domain dependencies",
        "",
    ]
    for item in domain.get("known_cross_domain_dependencies") or []:
        lines.append(f"- {item}")
    lines += ["", "Do not consult `historical_architecture.json` while completing this review.", ""]
    return "\n".join(lines)


FORMAT_EXAMPLE_CSV = """component_i,component_j,same_service,confidence,notes
AlphaService,BetaService,1,0.8,format example only — not a SEMS-R pair
AlphaService,GammaRepository,0,,
"""

REVIEWER_SEND_FILES = (
    "system_description.md",
    "architectural_evidence.md",
    "component_list.csv",
    "pairwise_decisions.csv",
)


def _evaluation_form(
    n_components: int,
    n_pairs: int,
    *,
    include_llm_example: bool = True,
) -> str:
    example = (
        "**Example only (not an expert answer):** `pairwise_decisions_llm.csv` shows how the "
        "sheet looks when filled. It was copied from one LLM run (`gemini-2.5-flash`, C0, run 1). "
        "Fill `pairwise_decisions.csv` yourself. Do not copy the example as your review."
        if include_llm_example
        else (
            "`format_example.csv` shows the CSV columns on two fake names. "
            "Do not copy those labels onto SEMS-R components."
        )
    )
    return f"""# Architect evaluation form

SEMS-R is a reconstructed education-management monolith, not original production SEMS source.

Please complete this review **independently**:

- Do **not** look up the historical SEMS six-service split.
- Do **not** ask an LLM or a colleague to fill the sheet.
- Do **not** leave `same_service` blank; every pair needs `0` or `1`.

1. Propose service boundaries (group the {n_components} components in `component_list.csv`). You can list groups in `notes` or at the bottom of this file.
2. Fill `pairwise_decisions.csv` (`same_service` = 1 if the pair should share a service, else 0). There are {n_pairs} pairs.
3. Optionally rank candidate services for migration (1 = migrate first).
4. Identify risky boundaries.
5. Optional confidence in [0, 1] and notes.

Leave `confidence` / `notes` blank rather than guessing. Do not invent runtime measurements.

Return the filled `pairwise_decisions.csv`. Comma-separated CSV is preferred. Semicolon CSV from Numbers or Excel is acceptable.

{example}
"""


def write_reviewer_send_packet(src_dir: Path, dest_dir: Path) -> Path:
    """Blind packet for additional architects. Omits gold, filled sheets, and the LLM example."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in REVIEWER_SEND_FILES:
        src = src_dir / name
        if not src.is_file():
            raise FileNotFoundError(f"missing {src}")
        shutil.copy2(src, dest_dir / name)
    blank = load_pairwise_decisions(dest_dir / "pairwise_decisions.csv")
    names = sorted(
        {
            row["component_i"]
            for row in blank
            if row.get("component_i")
        }
        | {
            row["component_j"]
            for row in blank
            if row.get("component_j")
        }
    )
    (dest_dir / "evaluation_form.md").write_text(
        _evaluation_form(len(names), len(blank), include_llm_example=False),
        encoding="utf-8",
    )
    (dest_dir / "format_example.csv").write_text(FORMAT_EXAMPLE_CSV, encoding="utf-8")
    return dest_dir


PAIRWISE_FIELDS = ["component_i", "component_j", "same_service", "confidence", "notes"]


def pairwise_from_assignment(
    blank_rows: list[dict[str, Any]],
    assignment: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in blank_rows:
        left = str(row.get("component_i") or "")
        right = str(row.get("component_j") or "")
        owner_left = assignment.get(left)
        owner_right = assignment.get(right)
        same = ""
        if owner_left and owner_right:
            same = "1" if owner_left == owner_right else "0"
        rows.append(
            {
                "component_i": left,
                "component_j": right,
                "same_service": same,
                "confidence": "",
                "notes": "",
            }
        )
    return rows


def write_llm_pairwise_example(
    parsed_path: Path,
    blank_csv: Path,
    out_path: Path,
) -> Path:
    payload = json.loads(parsed_path.read_text(encoding="utf-8"))
    assignment = payload.get("component_assignment") or {}
    if not isinstance(assignment, dict) or not assignment:
        raise ValueError(f"no component_assignment in {parsed_path}")
    blank = _read_csv(blank_csv)
    filled = pairwise_from_assignment(blank, {str(k): str(v) for k, v in assignment.items()})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(out_path, filled, PAIRWISE_FIELDS)
    return out_path


PROPOSED_SERVICE_FIELDS = ["component", "proposed_service", "notes"]
MIGRATION_RANK_FIELDS = ["proposed_service", "rank", "confidence", "rationale"]
RISKY_BOUNDARY_FIELDS = ["component_i", "component_j", "why_risky"]

# Documented cross-domain couplings from the expert system description.
# Used only to turn an LLM assignment into filled risky-boundary rows.
CROSS_DOMAIN_RISK_PAIRS = [
    ("GradeService", "StudentService", "Grade workflows require student records."),
    ("GradeService", "CourseEnrollmentRepository", "Grade workflows often need enrollment."),
    ("GradeRepository", "TeacherRepository", "Grade workflows require teacher records."),
    ("GradeRepository", "CourseRepository", "Grade workflows require course records."),
    ("AttendanceService", "StudentService", "Attendance workflows require student records."),
    ("AttendanceService", "CourseEnrollmentRepository", "Attendance workflows require enrollment."),
    ("AttendanceRepository", "TeacherRepository", "Attendance workflows require teacher records."),
    ("AttendanceRepository", "CourseRepository", "Attendance workflows require course records."),
    ("FinanceService", "StudentService", "Finance workflows require student context for invoicing."),
    ("FinanceService", "FacultyService", "Finance workflows require faculty context for ledgers."),
    ("LibraryService", "StudentService", "Library membership is issued to students."),
    ("LibraryService", "StaffRepository", "Library membership is issued to staff."),
    ("StudentOverviewService", "GradeService", "Student information is read across grade workflows."),
    ("CourseRepository", "CourseEnrollmentRepository", "Course ownership sits with faculty; enrollment consumes it."),
    ("ReportBuilder", "StudentService", "Legacy ReportBuilder consumes data from core services."),
    ("ReportBuilder", "FacultyService", "Legacy ReportBuilder consumes data from core services."),
]


def write_followup_llm_examples(parsed_path: Path, component_list: Path, out_dir: Path) -> dict[str, Path]:
    """Fill follow-up sheets from one LLM parsed.json. Example only, not an expert answer."""
    payload = json.loads(parsed_path.read_text(encoding="utf-8"))
    assignment = {str(key): str(value) for key, value in (payload.get("component_assignment") or {}).items()}
    if not assignment:
        raise ValueError(f"no component_assignment in {parsed_path}")
    components = [row["name"] for row in load_pairwise_decisions(component_list) if row.get("name")]
    missing = [name for name in components if name not in assignment]
    if missing:
        raise ValueError(f"LLM assignment missing components: {missing}")
    note = "gemini-2.5-flash C0 run 1 — example only, not an expert answer"
    proposed = [
        {"component": name, "proposed_service": assignment[name], "notes": note}
        for name in components
    ]
    ranks = []
    for item in payload.get("migration_priority") or []:
        ranks.append(
            {
                "proposed_service": str(item.get("service") or ""),
                "rank": str(item.get("rank") or ""),
                "confidence": str(item.get("confidence") or ""),
                "rationale": str(item.get("reason") or ""),
            }
        )
    if not ranks:
        raise ValueError(f"no migration_priority in {parsed_path}")
    risks = []
    for left, right, reason in CROSS_DOMAIN_RISK_PAIRS:
        if assignment.get(left) and assignment.get(right) and assignment[left] != assignment[right]:
            risks.append({"component_i": left, "component_j": right, "why_risky": reason})
    if not risks:
        raise ValueError("LLM assignment produced no cross-service documented couplings")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "proposed_services": out_dir / "proposed_services_llm.csv",
        "migration_ranks": out_dir / "migration_ranks_llm.csv",
        "risky_boundaries": out_dir / "risky_boundaries_llm.csv",
    }
    _write_csv(paths["proposed_services"], proposed, PROPOSED_SERVICE_FIELDS)
    _write_csv(paths["migration_ranks"], ranks, MIGRATION_RANK_FIELDS)
    _write_csv(paths["risky_boundaries"], risks, RISKY_BOUNDARY_FIELDS)
    return paths


def load_pairwise_decisions(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text.strip() else ""
    delimiter = ";" if first.count(";") > first.count(",") else ","
    rows: list[dict[str, str]] = []
    for raw in csv.DictReader(text.splitlines(), delimiter=delimiter):
        rows.append({str(key).strip(): str(value or "").strip() for key, value in raw.items() if key})
    return rows


def pairwise_same_service(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    return {
        (row["component_i"], row["component_j"]): row.get("same_service") or ""
        for row in rows
        if row.get("component_i") and row.get("component_j")
    }


def _read_csv(path: Path) -> list[dict[str, Any]]:
    return load_pairwise_decisions(path)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
