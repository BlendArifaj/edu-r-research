from pathlib import Path

from decomposition.evaluation.gold import clustering_labels, load_gold
from decomposition.evaluation.pairwise import (
    adjusted_rand_index,
    normalized_mutual_information,
    pairwise_scores,
)
from decomposition.evaluation.scoring import evaluate_decomposition
from decomposition.evaluation.structural import structural_metrics
from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD

ROOT = Path(__file__).resolve().parents[2]


def test_perfect_partition_scores_one() -> None:
    truth = {"A": "s1", "B": "s1", "C": "s2", "D": "s2"}
    pred = dict(truth)
    scores = pairwise_scores(truth, pred)
    assert scores["tp"] == 2
    assert scores["fp"] == 0
    assert scores["fn"] == 0
    assert scores["f1"] == 1.0
    assert adjusted_rand_index(truth, pred) == 1.0
    assert abs(normalized_mutual_information(truth, pred) - 1.0) < 1e-9


def test_all_in_one_cluster_has_known_f1() -> None:
    truth = {"A": "s1", "B": "s1", "C": "s2", "D": "s2"}
    pred = {name: "all" for name in truth}
    scores = pairwise_scores(truth, pred)
    assert scores["tp"] == 2
    assert scores["fp"] == 4
    assert scores["fn"] == 0
    assert scores["precision"] == 0.3333
    assert scores["recall"] == 1.0
    assert scores["f1"] == 0.5
    assert adjusted_rand_index(truth, pred) == 0.0


def test_crossed_pairs_have_zero_f1() -> None:
    truth = {"A": "s1", "B": "s1", "C": "s2", "D": "s2"}
    pred = {"A": "x", "C": "x", "B": "y", "D": "y"}
    scores = pairwise_scores(truth, pred)
    assert scores["tp"] == 0
    assert scores["f1"] == 0.0


def test_inter_service_coupling_ratio() -> None:
    assignment = {"AService": "s1", "BService": "s1", "CService": "s2"}
    evidence = {
        "dependencies": {
            "G_call": [
                {"from": "AService", "to": "BService"},
                {"from": "BService", "to": "CService"},
            ]
        },
        "entity_ownership": [],
    }
    metrics = structural_metrics(assignment, evidence)
    assert metrics["intra_service_dependencies"] == 1
    assert metrics["inter_service_dependencies"] == 1
    assert metrics["cross_service_call_ratio"] == 0.5
    assert metrics["internal_cohesion_ratio"] == 0.5


def test_gold_excludes_identity_and_places_report_builder() -> None:
    gold = load_gold(ROOT / "reference" / "historical_architecture.json")
    labels = clustering_labels(gold)
    assert "AuthService" not in labels
    assert "UserRepository" not in labels
    assert labels["ReportBuilder"] == "faculty"
    assert labels["EnrollmentGateService"] == "student"
    assert len(labels) == 24


def test_rule_based_is_near_gold_except_report_builder() -> None:
    import json

    evidence_path = ROOT / "outputs/evidence/architectural_evidence.json"
    decomposition_path = ROOT / "outputs/decompositions/rule_based.json"
    if not evidence_path.is_file() or not decomposition_path.is_file():
        import pytest

        pytest.skip("generated evidence/baselines are not published; run make extract-evidence && make baselines")

    gold = load_gold(ROOT / "reference" / "historical_architecture.json")
    evidence = json.loads((ROOT / "outputs/evidence/architectural_evidence.json").read_text())
    decomposition = json.loads((ROOT / "outputs/decompositions/rule_based.json").read_text())
    result = evaluate_decomposition(decomposition, gold, evidence)
    assert result["available"] is True
    assert result["pairwise"]["precision"] == 1.0
    assert 0.9 < result["pairwise"]["f1"] < 1.0
    assert result["pairwise"]["fn"] == 8


def test_evaluation_may_reference_gold_but_generators_may_not() -> None:
    evaluation = (ROOT / "decomposition/evaluation/gold.py").read_text(encoding="utf-8")
    assert "historical_architecture" in evaluation
    for folder in ("extraction", "baselines"):
        for path in (ROOT / "decomposition" / folder).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if FORBIDDEN_GOLD in text:
                assert "FORBIDDEN" in text
