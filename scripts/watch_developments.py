#!/usr/bin/env python3
"""
Long-running poller: watches NHSRCL press releases and inserts new rows into Django.

Usage:
  python3 scripts/watch_developments.py
  python3 scripts/watch_developments.py --interval 600 --export-json
  python3 scripts/watch_developments.py --once
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / "env" / "bin" / "python"


def main() -> int:
    py = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable
    cmd = [py, "manage.py", "watch_developments", *sys.argv[1:]]
    try:
        subprocess.check_call(cmd, cwd=BACKEND)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())