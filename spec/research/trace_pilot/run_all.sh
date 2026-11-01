#!/usr/bin/env bash
# Rebuild the pilot. Raw TRACE aggregates go to TRACE_PILOT_WORK, outside the project.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1  # posmon stays untouched
python3 s01_reference.py
python3 s02_panel.py
python3 s03_build.py
python3 s04_tests.py
python3 s05_summary.py
