import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "workload" / "seed.py"


def _run_seed(database_url: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SEMS_DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, str(SEED), "--scale", "tiny", "--seed", "42"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_seed_can_run_twice_on_the_same_sqlite_file(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'sems_r.db'}"
    first = _run_seed(database_url)
    second = _run_seed(database_url)
    assert "reset=True" in first.stdout
    assert "reset=True" in second.stdout
    assert first.returncode == 0
    assert second.returncode == 0
