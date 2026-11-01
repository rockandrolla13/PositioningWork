import pymupdf,numpy as np,json,datetime as D,re
d=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf")
f2=json.load(open('fig2.json')); labs=f2['labs'];lev=np.array(f2['lev']);ch=np.array(f2['ch'])
p=d[2]; dr=p.get_drawings()
def mk(xr):
    return np.array(sorted(((m['rect'].x0+m['rect'].x1)/2,(m['rect'].y0+m['rect'].y1)/2) for m in dr if m.get('fill') and m['rect'].y0>500 and xr[0]<m['rect'].x0<xr[1] and 2<m['rect'].width<9 and m['rect'].height<9 and len(m['items'])==4))
m3=mk((40,300));m4=mk((300,600))
y3=(577.35-m3[:,1])/11.81*2; x3=(m3[:,0]-184.7)/29.6-.03
y4=(577.28-m4[:,1])/11.81*2; x4=(m4[:,0]-420.5)/22.2-.04
ret={}
for xi,yi in zip(x3,y3):
    i=np.argmin(abs(lev-xi)); 
    assert labs[i] not in ret, labs[i]
    ret[labs[i]]=round(float(yi),2)
print('F3 unique',len(ret),[(k,ret[k]) for k in labs])
ok=0;rows=[]
for xi,yi in zip(x4,y4):
    i=np.argmin(abs(ch-xi)); m=labs[i+1];nx=labs[i+2] if i+2<len(labs) else None
    rows.append((m,nx,round(float(xi),2),round(float(yi),2),ret.get(nx)))
print(sorted(rows,key=lambda r:labs.index(r[0])))
print('pos dir hits',sum(1 for r in rows if r[2]*r[3]>0),len(rows))
pos=[r for r in rows if r[2]>0];neg=[r for r in rows if r[2]<0]
print('mean ret after +',np.mean([r[3] for r in pos]),len(pos),' after -',np.mean([r[3] for r in neg]),len(neg))
p=d[3];dr=p.get_drawings()
def lines(col,ylo,yhi):
    P=[]
    for x in dr:
        c=x.get('color')
        if c and x['type']=='s' and len(x['items'])>=100 and all(abs(a-b)<.01 for a,b in zip(c,col)) and ylo<x['rect'].y0<yhi:
            pts=[]
            for it in x['items']:
                if not pts: pts.append((it[1].x,it[1].y))
                pts.append((it[2].x,it[2].y))
            P+=pts
    return np.array(sorted(set(P)))
A=lines((0,0,.502),300,430);R=lines((.329,.553,.831),300,430)
print('pts',len(A),len(R))
yc=lambda y:100+(388.65-y)/11.87*5
print('ACWI start,end',yc(A[0,1]),yc(A[-1,1]),' Portfolio',yc(R[0,1]),yc(R[-1,1]), 'x',A[0,0],A[-1,0])
dx=np.diff(A[:,0]);print('dx uniq',np.round(np.unique(np.round(dx,2)),2)[:8])
start=D.date(2014,12,31);end=D.date(2016,4,29)
sc=(end-start).days/(A[-1,0]-A[0,0])
dates=[start+D.timedelta(days=round((x-A[0,0])*sc)) for x in A[:,0]]
print(dates[:6],dates[-4:], 'weekend count',sum(1 for x in dates if x.weekday()>4))
# month-end values
me={}
for dt,a,r in zip(dates,A[:,1],R[:,1]): me[(dt.year,dt.month)]=(yc(a),yc(r))
keys=sorted(me); prev=(100.,100.);print('month ACWI% Port% F3')
ml={ (2014,11):'Nov-14'}
for k in keys:
    a,r=me[k]; lb=D.date(k[0],k[1],1).strftime('%b-%y')
    print(lb,round(a,2),round(r,2),round((a/prev[0]-1)*100,2),round((r/prev[1]-1)*100,2),ret.get(lb)); prev=(a,r)
# allocation polygon
for x in dr:
    f=x.get('fill')
    if x['type']=='fs' and len(x['items'])==669 and abs(f[2]-.5)<.01:
        pts=[(i[2].x,i[2].y) for i in x['items'] if i[0]=='l']
        pts=np.array(pts); 
        top=pts[pts[:,1]<490]
        xs=np.unique(np.round(top[:,0],1)); gaps=np.where(np.diff(xs)>1)[0]
        print('equity runs (x):',[(xs[0] if g==0 else xs[gaps[g-1]+1], xs[gaps[g]]) for g in range(len(gaps))],xs[gaps[-1]+1],xs[-1])
        for a in [xs[gaps[0]+1]]+list(xs[gaps]+0)+list(xs[gaps+1]): pass
        conv=lambda v:(start+D.timedelta(days=round((v-A[0,0])*sc))).isoformat()
        print('dates',[ (conv(xs[gaps[g]]),conv(xs[gaps[g]+1])) for g in range(len(gaps))],conv(xs[0]),conv(xs[-1]))
