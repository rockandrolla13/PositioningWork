import pymupdf,re,json,numpy as np
# Fig A3 panel 3 check
d0=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf"); p=d0[8]
def stats(y,x):
    s0=(x*y).sum()/(x*x).sum(); b=np.polyfit(x,y,1); r2=np.corrcoef(x,y)[0,1]**2
    return s0,r2,s0*r2
ser={'g':[], 'n':[]}
for dr in p.get_drawings():
    c=dr.get('color');r=dr['rect']
    if c and len(dr['items'])==4 and r.x0>400 and 110<r.y0<205:
        if abs(c[1]-.69)<.01: ser['g'].append(((r.x0+r.x1)/2,(r.y0+r.y1)/2))
        elif abs(c[2]-.5)<.01 and r.y0>125: ser['n'].append(((r.x0+r.x1)/2,(r.y0+r.y1)/2))
for k,v in ser.items():
    v=np.array(sorted(v)); yy=(189.33-v[:,1])/(85/60); n=len(yy)
    print('A3',k,'n',n,'first/last',round(yy[0],2),round(yy[-1],2),'dx',round(np.diff(v[:,0]).mean(),3))
    for lab,x in (('x=1..n',np.arange(1,n+1.)),('x=0..n-1',np.arange(0,n*1.)),):
        print('  ',lab,'slope0 %.4f R2 %.4f prod %.4f'%stats(yy,x))
    print('   x=axis coords', 'slope0 %.4f R2 %.4f'%stats(yy,(v[:,0]-404.9)/(33.15/20))[:2])
print('printed: Europe y=.5938x R2 .9838; NA y=.0784x R2 .1278')
# Taars
d=pymupdf.open("/home/ak/Documents/Flow/Taars.pdf")
num=re.compile(r'^\(?-?[\d.,]+\)?$')
def spans(pg):
    out=[]
    for b in d[pg-1].get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            for s in l['spans']:
                t=s['text'].strip()
                if num.match(t):
                    v=float(t.strip('()').replace(',',''));v=-v if t.startswith('(') else v
                    out.append((v,(s['bbox'][1]+s['bbox'][3])/2,s['bbox'][2]))
    return out
def path(pg,col,x0,ylo,yhi,n=22):
    for dr in d[pg-1].get_drawings():
        c=dr.get('color');r=dr['rect']
        if c and len(dr['items'])==n and abs(r.x0-x0)<.5 and r.y0>=ylo-1 and r.y1<=yhi+1 and all(abs(a-b)<.012 for a,b in zip(c,col)):
            pts=[]
            for it in dr['items']:
                if it[0]=='l':
                    if not pts: pts.append((it[1].x,it[1].y))
                    pts.append((it[2].x,it[2].y))
            return np.array(pts)
    raise Exception((pg,col))
def cal(pg,x0,ylo,yhi):
    s=[(v,y) for v,y,xr in spans(pg) if x0-22<xr<x0+1 and ylo-3<y<yhi+3]
    a=np.array(s); b=np.polyfit(a[:,1],a[:,0],1)
    resid=np.abs(np.polyval(b,a[:,1])-a[:,0]).max()
    return b,len(s),resid
N,M,L,G=(0,0,.502),(0,.439,.753),(.545,.773,.929),(0,.69,.314)
charts={
 'F16':(11,344.5,330,450,{'US':N,'EM':M,'DM':L}),
 'F17':(11,344.6,535,645,{'North America':N,'Latin America':M,'Asia Pacific':L,'Europe':G}),
 'F18':(12,344.7,125,225,{'Large Cap':N,'Mid Cap':M,'Small Cap':L}),
 'F23':(13,92.2,440,540,{'MBS':N,'Inflation':M,'US Treasury':L,'Corp. IG':(.25,.44,.65),'Municipal':(.86,.51,.22)}),
 'F24':(13,350.1,445,545,{'Corp. HY':G,'DM Intl debt':(.56,.65,.8),'EM debt':(.81,.56,.55),'Convertible':(.71,.79,.57),'Senior Loans':(.65,.59,.73)}),
 'F25':(14,344.6,125,225,{'Gold':N,'Energy Cmdty':M,'Agriculture':L,'Diversified Broad':G}),
 'F26':(15,92.1,225,330,{'Defensives':N,'Dom. Cyclicals':M,'Global Cyclicals':L}),
 'F19':(12,76.0,505,575,{'Japan':N,'Australia':M,'Hong Kong':L,'Singapore':G}),
 'F20':(12,247.3,500,580,{'Austria':N,'France':M,'Germany':L,'Italy':G,'Spain':(0,.69,.94)}),
 'F21':(12,418.6,500,575,{'Sweden':N,'Switzerland':M,'UK':L,'Canada':G}),
 'F29':(15,246.7,450,512,{'Industrials':N,'Consumer Discretionary':M,'Financials':L,'Technology':G}),
 'F30':(15,417.9,450,515,{'Materials':N,'Energy':L}),
}
z14=dict(zip("Energy Cmdty|Utilities|Consumer Discretionary|Semiconductors|Transportation|Infrastructure|Energy|Defensives|Turkey|MBS|Convertible|Biotechnology|Dom. Cyclicals|Industrials|Financials|Telecom|Healthcare|China|Real Estate|India|Russia|MLPs|Municipal|DM Intl debt|Internet|Global Cyclicals|North America|US|France|Aerospace|Small Cap|Consumer Staples|Large Cap|Taiwan|Inflation|Oil|UK|Corp. IG|DM|Real Estate Intl|Mid Cap|Energy Equip|Technology|Malaysia|Hong Kong|Thailand|Construc|Brazil|Latin America|Spain|Italy|Indonesia|Australia|Materials|Mexico|Agriculture|Sweden|Germany|Senior Loans|EM debt|Singapore|Agribusiness|Commercial Banks|Austria|EM|Switzerland|South Korea|Software|Timber|Japan|Gold|Gold Eq|Asia Pacific|Diversified Broad|Canada|Pharma|NatRes|Corp. HY|Europe|US Treasury".split('|'),
 [5.33,4.12,3.24,1.21,1.13,1.05,.75,.58,.54,.40,.39,.38,.37,.32,.30,.25,.24,.18,.16,.15,.14,.12,.07,.06,.06,.05,.04,.04,.02,.01,-.01,-.03,-.04,-.07,-.10,-.11,-.12,-.12,-.12,-.13,-.13,-.14,-.15,-1.99,-1.32,-1.13,-1.12,-1.00,-.94,-.79,-.74,-.73,-.73,-.69,-.69,-.65,-.65,-.59,-.59,-.52,-.51,-.40,-.36,-.33,-.32,-.32,-.30,-.30,-.30,-.29,-.29,-.29,-.28,-.23,-.20,-.18,-.17,-.16,-.16,-.15]))
print(len(z14))
res={}
for k,(pg,x0,ylo,yhi,ss) in charts.items():
    b,ns,rs=cal(pg,x0,ylo,yhi)
    for name,col in ss.items():
        pts=path(pg,col,x0,ylo,yhi)
        y=np.polyval(b,pts[:,1]); y=y-y[0]
        n=len(y)
        res[name]=dict(n=n,end=y[-1],a=stats(y,np.arange(0,n*1.)),c=stats(y[1:],np.arange(1,n*1.)),chart=k)
    print(k,'labels',ns,'maxresid',round(rs,3))
print('name  n end  slope0 R2 TAARSS(x=0..22)   z')
for k,v in res.items():
    print(f"{k:24s}{v['n']} {v['end']:7.2f} {v['a'][0]:7.3f} {v['a'][1]:.3f} {v['a'][2]:7.3f}  z={z14.get(k)}")
names=[k for k in res if k in z14]
ra=np.array([res[k]['a'][2] for k in names]); rc=np.array([res[k]['c'][2] for k in names]); zz=np.array([z14[k] for k in names])
print('n',len(names),'corr z vs raw',np.corrcoef(ra,zz)[0,1],'x=1 anchored',np.corrcoef(rc,zz)[0,1])
ex=[i for i,k in enumerate(names) if k!='Energy Cmdty']
print('ex energy cmdty corr',np.corrcoef(ra[ex],zz[ex])[0,1], 'spearman', np.corrcoef(np.argsort(np.argsort(ra)),np.argsort(np.argsort(zz)))[0,1])
print('ratio raw/(z+.15) median',np.median(ra/(zz+.155+1e-9)))
F={'US Treasury':-1,'Gold':-1,'Corp. IG':-.5,'Senior Loans':.5,'Corp. HY':.5,'EM debt':.5,'Defensives':.5,'Large Cap':.5,'Diversified Broad':1,'Dom. Cyclicals':1,'DM':1,'Global Cyclicals':1,'Small Cap':1.5,'EM':1.5}
for var in ('a','c'):
    e=sum(F[k]*res[k][var][2] for k in F); print(var,'EFRoM from drawn paths Dec-14 =',round(e,3),'; slope-only',round(sum(F[k]*res[k][var][0] for k in F),3))
print('z sum',round(sum(F[k]*z14[k] for k in F),3),'z-z0 sum',round(sum(F[k]*(z14[k]+.155) for k in F),3),'sumF',sum(F.values()))
for k in F: print(' ',k,F[k],round(res[k]['a'][2],3),z14[k])
json.dump({k:[float(x) for x in v['a']] for k,v in res.items()},open('taars_dec14.json','w'))
print('--- x convention tests')
import datetime as D
days=[D.date(2014,11,28)]+[D.date(2014,12,i) for i in range(1,32) if D.date(2014,12,i).weekday()<5 and i!=25]
print(len(days))
cal=np.array([(q-days[0]).days for q in days],float)
print('A3 anchor test: see below')
for k,v in ser.items():
    v=np.array(sorted(v)); yy=(189.33-v[:,1])/(85/60)
    print(k,'R2 with anchor %.4f, without %.4f'%(np.corrcoef(np.arange(len(yy)),yy)[0,1]**2,np.corrcoef(np.arange(len(yy)-1),yy[1:])[0,1]**2))
res2={}
for kk,(pg,x0,ylo,yhi,ss) in charts.items():
    b,_,_=cal_f(pg,x0,ylo,yhi) if False else (None,None,None)
