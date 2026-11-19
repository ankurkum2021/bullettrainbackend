#!/usr/bin/env python3
"""
One-shot sync: corridor catalog, curated updates JSON, and live NHSRCL press feed → Django DB.

Usage (from repo root):
  python3 scripts/sync_all_data.py
  python3 scripts/sync_all_data.py --export-json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / "env" / "bin" / "python"


def run_manage(*args: str) -> None:
    py = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable
    cmd = [py, "manage.py", *args]
    subprocess.check_call(cmd, cwd=BACKEND)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Bullet Train Station database content.")
    parser.add_argument("--export-json", action="store_true", help="Write data/updates.json from DB.")
    parser.add_argument("--skip-nhsrcl", action="store_true", help="Only catalog + JSON import.")
    args = parser.parse_args()

    manage_args = ["sync_news", "--backfill-json"]
    if args.export_json:
        manage_args.append("--export-json")
    if args.skip_nhsrcl:
        manage_args.append("--skip-nhsrcl")
    try:
        run_manage("import_catalog")
        run_manage(*manage_args)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())