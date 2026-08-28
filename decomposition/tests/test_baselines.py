from pathlib import Path

import pytest

from decomposition.baselines.clustering import cluster_graph
from decomposition.baselines.config import BaselineConfig
from decomposition.baselines.graphs import call_graph, combine_graphs, data_graph, runtime_graph
from decomposition.baselines.rule_based import run_rule_based
from decomposition.baselines.runner import load_evidence, run_all_baselines
from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD, build_evidence_package

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "monolith" / "app"


def _evidence(names: list[str], calls: list[tuple[str, str]], runtime=None, usage=None) -> dict:
    return {
        "system": {"name": "SEMS-R", "is_original_sems_source": False},
        "components": [
            {"name": name, "module": "app.services.demo", "kind": "service"} for name in names
        ],
        "dependencies": {
            "G_call": [{"from": src, "to": dst, "kind": "call"} for src, dst in calls],
            "G_data": [],
        },
        "database_usage": usage or [],
        "entity_ownership": [],
        "runtime_interactions": runtime
        or {"available": False, "endpoints": [], "note": "empty rather than fabricated"},
        "domain_descriptions": {
            "functional_areas": [
                {"id": "faculty", "capabilities": ["faculty and department administration"]},
                {"id": "student", "capabilities": ["course enrollment", "semester registration"]},
                {"id": "library", "capabilities": ["book catalog and copies"]},
            ]
        },
    }


def test_louvain_separates_two_cliques() -> None:
    names = [
        "A1Service",
        "A2Service",
        "A3Service",
        "B1Service",
        "B2Service",
        "B3Service",
    ]
    calls = [
        ("A1Service", "A2Service"),
        ("A2Service", "A3Service"),
        ("A1Service", "A3Service"),
        ("B1Service", "B2Service"),
        ("B2Service", "B3Service"),
        ("B1Service", "B3Service"),
        ("A1Service", "B1Service"),
    ]
    evidence = _evidence(names, calls)
    graph = call_graph(evidence)
    for src, dst in [("A1Service", "A2Service"), ("A2Service", "A3Service"), ("A1Service", "A3Service")]:
        graph[src][dst]["weight"] = 10.0
    for src, dst in [("B1Service", "B2Service"), ("B2Service", "B3Service"), ("B1Service", "B3Service")]:
        graph[src][dst]["weight"] = 10.0
    graph["A1Service"]["B1Service"]["weight"] = 0.05
    result = cluster_graph(graph, BaselineConfig(), method="graph_static", evidence=evidence)
    assignment = result["component_assignment"]
    assert assignment["A1Service"] == assignment["A2Service"] == assignment["A3Service"]
    assert assignment["B1Service"] == assignment["B2Service"] == assignment["B3Service"]
    assert assignment["A1Service"] != assignment["B1Service"]
    assert result["graph_stats"]["communities"] == 2


def test_runtime_only_empty_is_not_fabricated() -> None:
    evidence = _evidence(["FacultyService", "LibraryService"], [])
    results = run_all_baselines(evidence, BaselineConfig())
    runtime = results["runtime_only"]
    assert runtime["available"] is False
    assert runtime["component_assignment"] == {}
    assert "fabricated" in " ".join(runtime["notes"]).lower() or "empty" in " ".join(runtime["notes"]).lower()


def test_data_graph_does_not_connect_unrelated_components() -> None:
    evidence = _evidence(
        ["GradeService", "LibraryService"],
        [],
        usage=[
            {
                "component": "GradeService",
                "entity": "Grade",
                "static_direct": True,
                "static_via_repository": False,
            },
            {
                "component": "LibraryService",
                "entity": "Book",
                "static_direct": True,
                "static_via_repository": False,
            },
        ],
    )
    graph = data_graph(evidence)
    assert not graph.has_edge("GradeService", "LibraryService")


def test_combined_gamma_zero_matches_static_only_graph() -> None:
    evidence = _evidence(
        ["FacultyService", "FacultyRepository", "LibraryService"],
        [("FacultyService", "FacultyRepository")],
        usage=[
            {
                "component": "FacultyService",
                "entity": "Faculty",
                "static_direct": True,
                "static_via_repository": False,
            },
            {
                "component": "FacultyRepository",
                "entity": "Faculty",
                "static_direct": True,
                "static_via_repository": False,
            },
        ],
    )
    names = ["FacultyService", "FacultyRepository", "LibraryService"]
    static = combine_graphs(
        [(call_graph(evidence), 1.0), (data_graph(evidence), 1.0)],
        names,
        normalize_layers=True,
    )
    combined = combine_graphs(
        [(call_graph(evidence), 1.0), (data_graph(evidence), 1.0), (None, 1.0)],
        names,
        normalize_layers=True,
    )
    assert set(static.edges) == set(combined.edges)


def test_rule_based_uses_domain_areas_not_gold() -> None:
    package = build_evidence_package(
        app_root=APP,
        traces_path=None,
        domain_path=ROOT / "reference" / "domain_description.json",
        rules_path=ROOT / "reference" / "migration_rules.json",
    )
    dumped = __import__("json").dumps(package)
    assert FORBIDDEN_GOLD not in dumped
    result = run_rule_based(package, BaselineConfig())
    assignment = result["component_assignment"]
    assert assignment["FacultyService"] == "faculty"
    assert assignment["GradeService"] == "grade"
    assert assignment["FinanceService"] == "finance"
    assert assignment["AttendanceService"] == "attendance"
    assert assignment["LibraryService"] == "library"
    assert assignment["StudentService"] == "student"
    assert assignment["EnrollmentGateService"] == "student"
    assert assignment["AuthService"] == "shared_identity"
    assert assignment["UserRepository"] == "shared_identity"
    assert result["system"]["gold_labels_used"] is False
    assert not result["unassigned_components"]
    assert FORBIDDEN_GOLD not in __import__("json").dumps(result)


def test_baselines_are_deterministic() -> None:
    package = build_evidence_package(
        app_root=APP,
        traces_path=None,
        domain_path=ROOT / "reference" / "domain_description.json",
        rules_path=ROOT / "reference" / "migration_rules.json",
    )
    first = run_all_baselines(package, BaselineConfig(seed=42))
    second = run_all_baselines(package, BaselineConfig(seed=42))
    assert first["graph_static"]["component_assignment"] == second["graph_static"]["component_assignment"]
    assert first["rule_based"]["component_assignment"] == second["rule_based"]["component_assignment"]


def test_refuses_gold_path(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        load_evidence(tmp_path / "historical_architecture.json")


def test_runtime_graph_none_without_traces() -> None:
    evidence = _evidence(["FacultyService"], [])
    assert runtime_graph(evidence) is None
