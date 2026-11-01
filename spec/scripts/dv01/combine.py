"""Join the OFR-derived DV01 and the bond rebuild into data/treasury_futures_dv01.csv.

Usage: python combine.py OFR_CSV REBUILD_CSV OUTPUT_CSV
OFR values cover 2013 onward. The rebuild covers earlier weeks, scaled to meet OFR over its first 26 weeks.
"""
import sys

import pandas as pd

CONTRACTS = ["TU", "FV", "TY", "TN", "US", "WN"]

ofr_path, rebuild_path, output_path = sys.argv[1:4]
ofr = pd.read_csv(ofr_path, parse_dates=[0], index_col=0).rename(columns={"UXY": "TN"})[CONTRACTS]
rebuild = pd.read_csv(rebuild_path, parse_dates=[0], index_col=0)[CONTRACTS]

rows = []
for contract in CONTRACTS:
    observed = ofr[contract].dropna()
    first = observed.index[0]
    overlap = rebuild[contract].reindex(observed.index[:26]).dropna()
    scale = observed.loc[overlap.index].mean() / overlap.mean()
    before = rebuild[contract].loc[:first - pd.Timedelta(days=1)].dropna() * scale
    rows.append(pd.DataFrame({"date": before.index, "contract": contract, "dv01_usd": before.values.round(2),
                              "source": "bond_rebuild_scaled"}))
    rows.append(pd.DataFrame({"date": observed.index, "contract": contract, "dv01_usd": observed.values.round(2),
                              "source": "ofr_derived"}))
pd.concat(rows).sort_values(["date", "contract"]).to_csv(output_path, index=False)
print("wrote", output_path)
