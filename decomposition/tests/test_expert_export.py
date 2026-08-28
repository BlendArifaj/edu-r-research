from pathlib import Path

from decomposition.evaluation.expert_export import pairwise_from_assignment, write_llm_pairwise_example

ROOT = Path(__file__).resolve().parents[2]


def test_pairwise_from_assignment_marks_same_cluster() -> None:
    blank = [
        {"component_i": "FacultyService", "component_j": "FacultyRepository"},
        {"component_i": "FacultyService", "component_j": "LibraryService"},
    ]
    assignment = {
        "FacultyService": "FacultyService",
        "FacultyRepository": "FacultyService",
        "LibraryService": "LibraryService",
    }
    rows = pairwise_from_assignment(blank, assignment)
    assert rows[0]["same_service"] == "1"
    assert rows[1]["same_service"] == "0"


def test_write_llm_pairwise_example_from_snapshot(tmp_path: Path) -> None:
    parsed = (
        ROOT
        / "outputs"
        / "runs"
        / "2026-08-27_005"
        / "decompositions"
        / "gemini-2.5-flash"
        / "C0"
        / "run_01"
        / "parsed.json"
    )
    blank = (
        ROOT
        / "outputs"
        / "runs"
        / "2026-08-27_005"
        / "expert_review"
        / "pairwise_decisions.csv"
    )
    if not parsed.is_file() or not blank.is_file():
        import pytest

        pytest.skip("local experiment snapshot is not published")
    out = tmp_path / "pairwise_decisions_llm.csv"
    write_llm_pairwise_example(parsed, blank, out)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("component_i,component_j,same_service,confidence,notes")
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 326
    assert "historical_architecture" not in text


def test_write_followup_llm_examples_are_complete(tmp_path: Path) -> None:
    parsed = (
        ROOT
        / "outputs"
        / "runs"
        / "2026-08-27_005"
        / "decompositions"
        / "gemini-2.5-flash"
        / "C0"
        / "run_01"
        / "parsed.json"
    )
    components = (
        ROOT
        / "outputs"
        / "runs"
        / "2026-08-27_005"
        / "expert_review"
        / "component_list.csv"
    )
    if not parsed.is_file() or not components.is_file():
        import pytest

        pytest.skip("local experiment snapshot is not published")
    from decomposition.evaluation.expert_export import (
        load_pairwise_decisions,
        write_followup_llm_examples,
    )

    paths = write_followup_llm_examples(parsed, components, tmp_path)
    proposed = load_pairwise_decisions(paths["proposed_services"])
    ranks = load_pairwise_decisions(paths["migration_ranks"])
    risks = load_pairwise_decisions(paths["risky_boundaries"])
    assert len(proposed) == 26
    assert all(row["proposed_service"] and row["notes"] for row in proposed)
    assert {row["component"] for row in proposed} == {
        row["name"] for row in load_pairwise_decisions(components)
    }
    assert len(ranks) == 8
    assert all(row["proposed_service"] and row["rank"] and row["confidence"] and row["rationale"] for row in ranks)
    assert len(risks) >= 5
    assert all(row["component_i"] and row["component_j"] and row["why_risky"] for row in risks)
    assert "historical_architecture" not in paths["proposed_services"].read_text(encoding="utf-8")

