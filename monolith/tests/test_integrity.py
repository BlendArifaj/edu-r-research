from pathlib import Path


def test_monolith_does_not_read_historical_reference() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for path in app_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "historical_architecture" in text or "reference/historical" in text:
            offenders.append(str(path))
    assert offenders == []
