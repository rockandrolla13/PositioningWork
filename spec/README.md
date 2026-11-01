# Positioning and Pain Monitor replication

Read `positioning_spec.pdf` first. It holds the method rules, the checks and the production schedule.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest -q                          # every test must pass
python scripts/reconcile_live.py   # needs internet: compare with Table 4 of the PDF
```

To rebuild the PDF: `./build.sh`. It needs `pip install -e ".[figures]"` and `latexmk`.
Use `./build.sh --offline` to skip the live reconciliation.

To refresh Treasury futures DV01: `./scripts/dv01/refresh.sh`. It needs internet access. Run it monthly.
To compare I5 with Goldman's charts: `python scripts/goldman_chart_check.py PATH_TO_PDF`. It needs `pymupdf` and `scipy`.

`research/` holds three studies, each with its plan, scripts, results and rerun script: `replication`, `improvements` and `credit_etf`. Their headline: reproduced does not mean it works. No predictive signal survived out of sample.

Files under `data/` come from a private workbook. Keep this folder private.

## Files kept out of Git

These are restricted and stay on the original machine: `evidence/`, the two workbooks, `spec/data/ty_daily.csv`, ICE OAS files, `spec/research/replication/raw/` (includes series read from bank charts) and `spec/research/credit_etf/work/`.

**Before you run the tests or build the PDF,** recreate `data/ty_daily.csv` from your copy of the workbook:

```bash
python scripts/extract_workbook_data.py "PATH/TO/Example Pain Monitor.xlsx"
```

Without it, tests that read that file fail. Set `SEC_USER_AGENT` before rerunning the TRACE pilot reference step, because the SEC requires a contact.
