import json,sys,glob,os
import pandas as pd,numpy as np
d=sys.argv[1]
def g(m):
    a=json.load(open(f"{d}/{m}.json")); s=pd.Series({pd.Timestamp(x):y for x,y in a},dtype=float); return s.sort_index()
SIZE={"TU":200000,"FV":100000,"TY":100000,"UXY":100000,"US":100000,"WN":100000}
print("span",{c:(g(f"TFF-LF_{c}_LONG_POSITION").index[0].date().isoformat(),g(f"TFF-LF_{c}_LONG_POSITION").index[-1].date().isoformat()) for c in SIZE})
print("DV01 span",g("TFF-LF_TREAS_LONG_DV01").index[0].date(),g("TFF-AI_TREAS_LONG_DV01").index[0].date())
R={}
for c in SIZE:
    R[c]=g(f"TFF-LF_{c}_LONG_POS10YREQV")/g(f"TFF-LF_{c}_LONG_POSITION")
R=pd.DataFrame(R)
print("ratio to TY, year-end sample"); print(R.resample("YE").last().round(3).to_string())
# short side agrees?
Rs=pd.DataFrame({c:g(f"TFF-LF_{c}_SHORT_POS10YREQV")/g(f"TFF-LF_{c}_SHORT_POSITION") for c in SIZE})
print("long vs short ratio max abs diff",(R-Rs).abs().max().round(4).to_dict())
# level: $ per $ notional of 10y equivalent per bp
for gp in ("LF","AI","OR","DI"):
    for side in ("LONG","SHORT"):
        k=g(f"TFF-{gp}_TREAS_{side}_DV01")/g(f"TFF-{gp}_TREAS_{side}_POS10YREQV")*1e5
        print(gp,side,"TY-DV01 implied:",k.dropna().iloc[[0,len(k.dropna())//2,-1]].round(2).to_dict())
k=(g("TFF-LF_TREAS_LONG_DV01")/g("TFF-LF_TREAS_LONG_POS10YREQV")*1e5).rename("TY")
print("TY DV01 implied by year-end"); print(k.resample("YE").last().round(2).to_string())
dv=pd.DataFrame({c:R[c]*SIZE[c]/1e5*k for c in SIZE})
print("Implied DV01 per contract: yearly mean"); print(dv.groupby(dv.index.year).mean().round(1).to_string())
print("On/near 2019-04-16 and 2019-04-30"); print(dv.loc["2019-04-09":"2019-04-30"].round(1).to_string())
dv.to_csv(f"{d}/../ofr_dv01.csv")
