from pathlib import Path

import pytest

from decomposition.evaluation.expert_export import load_pairwise_decisions, pairwise_same_service
from decomposition.evaluation.expert_pairwise import (
    discover_expert_sheets,
    gold_same_pairs,
    score_expert_packet,
)
from decomposition.evaluation.gold import load_gold

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "outputs/runs/2026-08-27_005/expert_review"
GOLD = ROOT / "reference/historical_architecture.json"


def test_semicolon_pairwise_loads() -> None:
    path = PACKET / "pairwise_decisions_exp_1.csv"
    if not path.is_file():
        pytest.skip("local experiment snapshot is not published")
    rows = load_pairwise_decisions(path)
    assert len(rows) == 325
    assert rows[0]["component_i"] == "AcademicCalendarRepository"
    assert rows[0]["same_service"] in {"0", "1"}


def test_discover_skips_copy_filenames(tmp_path: Path) -> None:
    (tmp_path / "pairwise_decisions_exp_1.csv").write_text(
        "component_i,component_j,same_service\nA,B,1\n", encoding="utf-8"
    )
    (tmp_path / "pairwise_decisions_exp_2 copy.csv").write_text(
        "component_i,component_j,same_service\nA,B,0\n", encoding="utf-8"
    )
    found = discover_expert_sheets(tmp_path)
    assert list(found) == ["exp1"]


def test_five_expert_sheets_are_scored() -> None:
    if not (PACKET / "pairwise_decisions_exp_1.csv").is_file():
        pytest.skip("local experiment snapshot is not published")
    payload = score_expert_packet(PACKET, GOLD)
    assert payload["reviewer_ids"] == ["exp1", "exp2", "exp3", "exp4", "exp5"]
    assert payload["agreement"]["n_reviewers"] == 5
    assert len(payload["agreement"]["expert_pairs"]) == 10
    llm = pairwise_same_service(load_pairwise_decisions(PACKET / "pairwise_decisions_llm.csv"))
    gold_same = gold_same_pairs(load_gold(GOLD))
    for reviewer_id in payload["reviewer_ids"]:
        sheet = PACKET / f"pairwise_decisions_exp_{reviewer_id[3:]}.csv"
        pred = pairwise_same_service(load_pairwise_decisions(sheet))
        assert len(pred) == 325
        assert all(value in {"0", "1"} for value in pred.values())
        assert pred != llm
        scores = payload["vs_gold"][reviewer_id]
        assert scores["pairs"] == len(gold_same) == 276
        assert scores["f1"] is not None
    assert payload["agreement"]["mean_pairwise_kappa"] is not None
