#!/usr/bin/env bash
# Rebuild the numbers, the figures and the PDF. Run from the spec directory.
# reconcile_live.py needs internet. Skip it with: ./build.sh --offline
set -euo pipefail
if [[ "${1:-}" != "--offline" ]]; then python3 scripts/reconcile_live.py; fi
python3 scripts/make_tables.py
python3 scripts/make_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build positioning_spec.tex
cp build/positioning_spec.pdf positioning_spec.pdf
