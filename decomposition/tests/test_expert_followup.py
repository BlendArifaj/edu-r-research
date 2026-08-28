from pathlib import Path

import pytest

from decomposition.evaluation.expert_followup import (
    apply_table_d_ranks,
    median_ranks,
    normalize_service_name,
    score_followup_packet,
)

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "outputs/runs/2026-08-27_005/expert_review"


def test_name_map_faculty_service() -> None:
    assert normalize_service_name("FacultyService") == "faculty"
    assert normalize_service_name("AuthService") == ""
    assert normalize_service_name("ReportingService") == ""


def test_median_of_five() -> None:
    per = {
        "exp1": {"faculty": 2, "student": 2},
        "exp2": {"faculty": 1, "student": 1},
        "exp3": {"faculty": 5, "student": 5},
        "exp4": {"faculty": 3, "student": 2},
        "exp5": {"faculty": 5, "student": 5},
    }
    med = median_ranks(per)
    assert med["faculty"] == 3
    assert med["student"] == 2


def test_score_followup_on_snapshot() -> None:
    if not (PACKET / "migration_ranks_exp_1.csv").is_file():
        pytest.skip("local experiment snapshot is not published")
    payload = score_followup_packet(PACKET)
    assert payload["reviewer_ids"] == ["exp1", "exp2", "exp3", "exp4", "exp5"]
    assert payload["llm_rank"]["faculty"] == 2
    assert payload["llm_rank"]["student"] == 2
    assert "auth" not in payload["llm_rank"]
    assert payload["historical_rank"] == {}
    assert payload["expert_rank"]["faculty"] == 3
    assert payload["expert_rank"]["student"] == 2


def test_apply_table_d_keeps_historical_blank() -> None:
    rows = apply_table_d_ranks(
        [{"service": "student", "rule_based_rank": "1", "llm_rank": "", "expert_rank": "", "historical_rank": ""}],
        {"llm_rank": {"student": 2}, "expert_rank": {"student": 2}},
    )
    assert rows[0]["llm_rank"] == "2"
    assert rows[0]["expert_rank"] == "2"
    assert rows[0]["historical_rank"] == ""
