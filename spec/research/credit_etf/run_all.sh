#!/usr/bin/env bash
# Rebuild everything from the raw downloads. Use "./run_all.sh --refresh" to download again as well.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1  # posmon stays untouched
python3 01_fetch_data.py "$@"
nice -n 10 python3 01b_book_stats.py
python3 02_build_panel.py
python3 05_pit_check.py
python3 06_baa_check.py
python3 03_run_tests.py
python3 04_make_report.py
