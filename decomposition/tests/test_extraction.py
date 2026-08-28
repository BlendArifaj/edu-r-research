from pathlib import Path

from decomposition.extraction.call_graph import build_graphs, graph_metrics
from decomposition.extraction.database_analysis import build_database_matrix, entity_ownership
from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD, build_evidence_package
from decomposition.extraction.runtime_analysis import analyze_runtime
from decomposition.extraction.static_analysis import analyze_app

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "monolith" / "app"


def test_static_analysis_finds_core_components() -> None:
    static = analyze_app(APP)
    names = {row["name"] for row in static.classes}
    assert "StudentService" in names
    assert "GradeService" in names
    assert "ReportBuilder" in names
    assert static.tablenames["Student"] == "students"
    assert static.tablenames["Grade"] == "grades"


def test_call_graph_has_student_finance_coupling() -> None:
    static = analyze_app(APP)
    graphs = build_graphs(static)
    call = graphs["G_call"]
    assert call.has_edge("StudentService", "FinanceService") or call.has_edge(
        "EnrollmentGateService", "FinanceService"
    )
    assert call.has_edge("StudentService", "StudentRepository")
    metrics = {row["component"]: row for row in graph_metrics(call)}
    assert metrics["StudentService"]["fan_out"] >= 1
    assert metrics["StudentRepository"]["fan_in"] >= 1


def test_known_graph_metrics() -> None:
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    metrics = {row["component"]: row for row in graph_metrics(graph)}
    assert metrics["A"]["fan_out"] == 1
    assert metrics["A"]["fan_in"] == 0
    assert metrics["C"]["fan_in"] == 1
    assert metrics["C"]["fan_out"] == 0
    assert metrics["B"]["dependency_degree"] == 2


def test_grade_accesses_student_via_repository() -> None:
    static = analyze_app(APP)
    matrix = build_database_matrix(static)
    grade_student = [
        row
        for row in matrix
        if row["component"] == "GradeService" and row["entity"] == "Student"
    ]
    assert grade_student
    assert grade_student[0]["static_via_repository"] or grade_student[0]["static_direct"]


def test_student_entity_is_shared() -> None:
    static = analyze_app(APP)
    ownership = {row["entity"]: row for row in entity_ownership(build_database_matrix(static))}
    assert ownership["Student"]["sharing_degree"] >= 2
    assert "app.deps" not in ownership["User"]["accessing_components"]


def test_runtime_cooccurrence_cannot_invent_static_edges() -> None:
    static = analyze_app(APP)
    fake_runtime = {"GradeService": {"books": 9999, "book_copies": 9999, "users": 9999}}
    matrix = build_database_matrix(static, fake_runtime)
    assert not any(
        row["component"] == "GradeService" and row["entity"] == "Book" for row in matrix
    )


def test_missing_traces_are_empty_not_fabricated() -> None:
    runtime = analyze_runtime([])
    assert runtime["available"] is False
    assert runtime["trace_count"] == 0
    assert "fabricated" in runtime["note"].lower() or "empty" in runtime["note"].lower()


def test_evidence_package_excludes_gold_and_includes_rules(tmp_path: Path) -> None:
    package = build_evidence_package(
        app_root=APP,
        traces_path=None,
        domain_path=ROOT / "reference" / "domain_description.json",
        rules_path=ROOT / "reference" / "migration_rules.json",
    )
    dumped = json_dumps(package)
    assert FORBIDDEN_GOLD not in dumped
    assert package["system"]["is_original_sems_source"] is False
    assert package["system"]["evidence_sources"]["historical_gold_labels"] is False
    assert package["migration_constraints"]["rules"][0]["id"] == "R1"
    assert package["runtime_interactions"]["available"] is False


def test_extraction_sources_do_not_import_gold() -> None:
    """Generators must not load gold. Evaluation code may."""
    offenders = []
    for folder in ("extraction", "baselines", "llm"):
        root = ROOT / "decomposition" / folder
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if FORBIDDEN_GOLD in text and "FORBIDDEN" not in text:
                offenders.append(str(path))
    assert offenders == []


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload)
