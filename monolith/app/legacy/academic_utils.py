"""Shared academic helpers used by multiple functional areas (legacy coupling)."""

from decimal import Decimal

LETTER_BOUNDARIES: list[tuple[Decimal, str]] = [
    (Decimal("90"), "A"),
    (Decimal("80"), "B"),
    (Decimal("70"), "C"),
    (Decimal("60"), "D"),
]


def score_to_letter(score: Decimal) -> str:
    for threshold, letter in LETTER_BOUNDARIES:
        if score >= threshold:
            return letter
    return "F"


def letter_to_points(letter: str) -> Decimal:
    mapping = {"A": Decimal("4.0"), "B": Decimal("3.0"), "C": Decimal("2.0"), "D": Decimal("1.0")}
    return mapping.get(letter, Decimal("0.0"))


def weighted_gpa(letters_and_credits: list[tuple[str, int]]) -> Decimal:
    if not letters_and_credits:
        return Decimal("0.00")
    total_points = sum(letter_to_points(letter) * credits for letter, credits in letters_and_credits)
    total_credits = sum(credits for _, credits in letters_and_credits)
    if total_credits == 0:
        return Decimal("0.00")
    return (total_points / Decimal(total_credits)).quantize(Decimal("0.01"))
