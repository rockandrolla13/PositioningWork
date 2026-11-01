"""Rebuild weekly Treasury futures DV01 from real bond records and the par curve; CTD = lowest price/CF."""
import json,sys,math,urllib.request,io,pickle,os
import numpy as np,pandas as pd
TD,OUT=sys.argv[1],sys.argv[2]
def load():
    rows={}
    for t in ("Note","Bond"):
        for x in json.load(open(f"{TD}/{t}.json")):
            if x.get("inflationIndexSecurity") in ("Yes",True,"true") or x.get("floatingRate")=="Yes" or not x.get("interestRate"): continue
            if x.get("type") not in ("Note","Bond"): continue
            c=x["cusip"]; i=pd.Timestamp(x["issueDate"]); 
            if c not in rows or i<rows[c]["issue"]:
                rows[c]=dict(cusip=c,issue=i,mat=pd.Timestamp(x["maturityDate"]),cpn=float(x["interestRate"]),type=x["type"],call=x.get("callable"))
    d=pd.DataFrame(rows.values()); d["orig"]=(d.mat-d.issue).dt.days/365.25
    return d
B=load(); B=B[B.call!="Yes"]
def ym(a,b): # whole months from a to b
    m=(b.year-a.year)*12+(b.month-a.month)-(1 if b.day<a.day else 0); return m
def cf(cpn,first,mat,kind):
    """CME conversion factor at 6 percent. cpn in percent."""
    tm=ym(first,mat); n=tm//12; z=tm%12
    c=cpn/100
    if kind in ("TU","FV"):
        v=z if z<7 else z-6
    else:
        z=z-z%3; v=z if z<7 else 3
    a=1/1.03**(v/6); bb=(c/2)*(6-v)/6
    cc=1/1.03**(2*n) if z<7 else 1/1.03**(2*n+1)
    dd=(c/0.06)*(1-cc)
    return a*(c/2+cc+dd)-bb
def price(c,y,T):
    """Clean price per 100, semiannual, T years. y in decimal."""
    if T<=0: return 100.
    n=math.ceil(T*2-1e-9); f=T*2-(n-1); cp=c/2
    w=1/(1+y/2)
    pv=sum(cp*w**(k-1+f) for k in range(1,n+1))+100*w**(n-1+f)
    return pv-cp*(1-f)
RULE={"TU":lambda m,o:(21<=m<=24+0 and o<=5.26),"FV":lambda m,o:(50<=m<=63 and o<=5.26),"TY":lambda m,o:(78<=m<=120),
      "TN":lambda m,o:(113<=m<=120),"US":None,"WN":lambda m,o:m>=300}
SIZE=dict(TU=2e5,FV=1e5,TY=1e5,TN=1e5,US=1e5,WN=1e5)
TYPE=dict(TU="Note",FV="Note",TY="Note",TN="Note",US="Bond",WN="Bond")
LIST=dict(TU="1990",FV="1988",TY="1982",TN="2016-01",US="1977",WN="2010-01")
def deliv(t):
    # front quarterly contract: roll two business days before first of delivery month
    for k in range(0,5):
        p=pd.Period(t+pd.DateOffset(days=3),"M")+k
        if p.month in (3,6,9,12): return p.to_timestamp()
def curve(row):
    x=np.array([1,2,3,5,7,10,20,30.]); v=row.values.astype(float); ok=~np.isnan(v)
    return x[ok],v[ok]/100
def build(dates,cur):
    out=[]
    for t in dates:
        first=deliv(t); row=cur.loc[:t].iloc[-1]; xs,ys=curve(row)
        for k in SIZE:
            if t<pd.Timestamp(LIST[k]): continue
            s=B[(B.type==TYPE[k])&(B.issue<=t+pd.Timedelta(days=45))&(B.mat>first)].copy()
            s["m"]=[ym(first,m) for m in s.mat]
            if k=="US":
                keep=(s.m>=180)&((s.m<300)|(first<pd.Timestamp("2011-03-01")))
            else:
                keep=np.array([RULE[k](m,o) for m,o in zip(s.m,s.orig)])
            s=s[keep]
            if s.empty: continue
            best=None
            for r in s.itertuples():
                T=(r.mat-t).days/365.25; y=float(np.interp(T,xs,ys)); F=cf(r.cpn,first,r.mat,k)
                P=price(r.cpn,y,T); pf=P/F
                if best is None or pf<best[0]:
                    best=(pf,r.cusip,r.cpn,r.mat,F,(price(r.cpn,y-5e-5,T)-price(r.cpn,y+5e-5,T))/100*SIZE[k]/F,T)
            out.append(dict(date=t,c=k,cusip=best[1],cpn=best[2],mat=best[3],cf=best[4],dv01=best[5]))
    return pd.DataFrame(out)
if __name__=="__main__":
    print("CF checks: CME 5.125 May-2016 Mar-2009 TY 0.9506 ->",round(cf(5.125,pd.Timestamp('2009-03-01'),pd.Timestamp('2016-05-15'),'TY'),4),"| CBOT 4.125 May-2015 Mar-2006 0.8711 ->",round(cf(4.125,pd.Timestamp('2006-03-01'),pd.Timestamp('2015-05-15'),'TY'),4),"| CBOT 4.75 May-2014 0.9215?",round(cf(4.75,pd.Timestamp('2005-03-01'),pd.Timestamp('2014-05-15'),'TY'),4))
    print("Cash DV01 check 4.125 May-2015 at 99-15 on early 2006:",round((price(4.125,.04195,9.3)-price(4.125,.04205,9.3))/100*1e5,2),"(CBOT 78.98 uses dur 7.94)")
    S=("DGS1","DGS2","DGS3","DGS5","DGS7","DGS10","DGS20","DGS30")
    cache=f"{OUT}/curve.pkl"
    if os.path.exists(cache): cur=pickle.load(open(cache,"rb"))
    else:
        cur={}
        for s in S:
            txt=urllib.request.urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd=2005-01-01&coed=2026-10-31",timeout=90).read().decode()
            f=pd.read_csv(io.StringIO(txt),parse_dates=["observation_date"],index_col="observation_date"); cur[s]=pd.to_numeric(f[s],errors="coerce")
        cur=pd.DataFrame(cur).ffill(); pickle.dump(cur,open(cache,"wb"))
    dates=pd.date_range("2006-01-03","2026-10-13",freq="W-TUE")
    R=build(dates,cur); R.to_pickle(f"{OUT}/rebuild.pkl")
    P=R.pivot(index="date",columns="c",values="dv01")[["TU","FV","TY","TN","US","WN"]]; P.to_csv(f"{OUT}/rebuild_dv01.csv")
    O=pd.read_csv(sys.argv[3],parse_dates=[0],index_col=0).rename(columns={"UXY":"TN"})[["TU","FV","TY","TN","US","WN"]]
    print("Rebuild, yearly mean"); print(P.groupby(P.index.year).mean().round(1).to_string())
    j=P.index.intersection(O.index)
    a=P.loc[j];b=O.loc[j]
    print("Overlap with OFR, 2013-03 to 2019: mean abs error $, mean abs %, corr")
    q=j[j<="2019-12-31"]
    for k in P.columns:
        u=a.loc[q,k].notna()&b.loc[q,k].notna()
        print(" ",k,"n",int(u.sum()),"MAE",round((a.loc[q,k]-b.loc[q,k])[u].abs().mean(),2),"MA%",round(((a.loc[q,k]-b.loc[q,k])/b.loc[q,k])[u].abs().mean()*100,1),"corr",round(a.loc[q,k][u].corr(b.loc[q,k][u]),3),"bias",round((a.loc[q,k]-b.loc[q,k])[u].mean(),2))
    print("Sample CTDs"); print(R[R.date.isin(pd.to_datetime(["2006-06-13","2009-03-03","2013-03-05","2015-12-29","2019-04-30"]))].assign(cf=lambda d:d.cf.round(4),dv01=lambda d:d.dv01.round(1))[["date","c","cpn","mat","cf","dv01"]].to_string(index=False))
