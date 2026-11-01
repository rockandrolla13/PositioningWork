#!/usr/bin/env bash
# Rerun everything from scratch: download, signals, tests, leak check, report.
# Usage: bash research/improvements/run_all.sh
# Needs internet for CFTC, FRED, Yahoo and cftc.gov. Takes about 6 minutes.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf raw derived results.json report.md
mkdir -p raw derived
export OMP_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
python3 s00_fetch.py
python3 -W ignore s01_signals.py
python3 s02_tests.py
python3 s04_checks.py
python3 s03_report.py
