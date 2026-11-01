#!/usr/bin/env bash
# Rebuild data/treasury_futures_dv01.csv from public sources. Run from the spec directory.
# Usage: ./scripts/dv01/refresh.sh [output.csv]
# Sources: OFR Hedge Fund Monitor API, TreasuryDirect security records, FRED constant-maturity yields.
set -euo pipefail
OUT="${1:-data/treasury_futures_dv01.csv}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/ofr" "$WORK/td" "$WORK/dv"
python3 scripts/dv01/ofr_get.py "$WORK/ofr"
python3 scripts/dv01/ofr_derive.py "$WORK/ofr" > "$WORK/ofr_derive.log"
for kind in Note Bond; do
  curl -sS -m 300 -A "Mozilla/5.0" "https://www.treasurydirect.gov/TA_WS/securities/search?type=$kind&format=json" -o "$WORK/td/$kind.json"
done
python3 scripts/dv01/bond_rebuild.py "$WORK/td" "$WORK/dv" "$WORK/ofr_dv01.csv" 2>/dev/null | grep -A8 "Overlap with OFR"
python3 scripts/dv01/combine.py "$WORK/ofr_dv01.csv" "$WORK/dv/rebuild_dv01.csv" "$OUT"
