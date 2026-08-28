from decimal import Decimal

from app.legacy.academic_utils import letter_to_points, score_to_letter, weighted_gpa


def test_score_to_letter_boundaries() -> None:
    assert score_to_letter(Decimal("90")) == "A"
    assert score_to_letter(Decimal("80")) == "B"
    assert score_to_letter(Decimal("59.99")) == "F"


def test_weighted_gpa() -> None:
    gpa = weighted_gpa([("A", 6), ("B", 6)])
    assert gpa == Decimal("3.50")


def test_empty_gpa_is_zero() -> None:
    assert weighted_gpa([]) == Decimal("0.00")
    assert letter_to_points("F") == Decimal("0.0")
