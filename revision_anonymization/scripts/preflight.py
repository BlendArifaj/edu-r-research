#!/usr/bin/env python3
"""Run all pre-execution checks; exit non-zero if any fail."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPTS = BASE / "scripts"


def main() -> int:
    steps = [
        [sys.executable, str(SCRIPTS / "verify_anonymization.py")],
    ]
    for cmd in steps:
        print("Running", " ".join(cmd))
        if subprocess.call(cmd) != 0:
            print("PREFLIGHT FAILED")
            return 1
    print("PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
