#!/usr/bin/env bash
# Rerun every replication test. Needs internet for CFTC, FRED and the Bank of Russia, unless raw/ is already filled.
# Run from anywhere. Takes about 25 minutes, most of it i4_rolling.py.
set -euo pipefail
cd "$(dirname "$0")"
for script in i4_digitise i4_search i4_uncond i4_shape i4_rolling i4_final i4_tenyear i4_opi_bands \
              i7_tranche i7_align i7_vol21 p2_deck p1_check i10_public i6_opi i6_bands i6_germany i6_rebuild i8_signal summarise; do
    echo "=== $script"
    python -W ignore "$script.py" > "raw/$script.log" 2>&1
done
echo done
