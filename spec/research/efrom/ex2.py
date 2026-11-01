import pymupdf,numpy as np,json
d=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf")
f2=json.load(open('fig2.json')); labs=f2['labs'];lev=np.array(f2['lev']);ch=np.array(f2['ch'])
p=d[2]; dr=p.get_drawings()
def mk(xr):
    return np.array(sorted(((m['rect'].x0+m['rect'].x1)/2,(m['rect'].y0+m['rect'].y1)/2) for m in dr if m.get('fill') and m['rect'].y0>500 and xr[0]<m['rect'].x0<xr[1] and 2<m['rect'].width<9 and m['rect'].height<9 and len(m['items'])==4))
m3=mk((40,300));m4=mk((300,600))
# y: label centres: 0% at 577.35 , 2% per 11.81 ; x fig3: '-' at 184.7, 1.0 per 29.6; fig4 '-' at 420.5, 1.0 per 22.2
y3=(577.35-m3[:,1])/11.81*2; x3=(m3[:,0]-184.7)/29.6
y4=(577.28-m4[:,1])/11.81*2; x4=(m4[:,0]-420.5)/22.2
for nm,x,y,pr in (('F3',x3,y3,'y=.0251x-.003 R2 .4181'),('F4',x4,y4,'y=.0083x+2e-6 R2 .0613')):
    b=np.polyfit(x,y/100,1);print(nm,len(x),'slope %.4f int %.4f R2 %.4f'%(b[0],b[1],np.corrcoef(x,y)[0,1]**2),'printed',pr)
# match F3 x to levels, F4 x to changes
ret={}
for xi,yi in zip(x3,y3):
    i=np.argmin(abs(lev-xi)); ret[labs[i]]=(round(xi,2),round(yi,2),round(abs(lev[i]-xi),3))
print('F3 matched',len(ret));print(ret)
pair={}
for xi,yi in zip(x4,y4):
    i=np.argmin(abs(ch-xi)); pair[labs[i+1]]=(round(xi,2),round(yi,2),round(abs(ch[i]-xi),3))
print('F4 matched',len(pair));print(pair)
hit=sum(1 for v in pair.values() if v[0]*v[1]>0);print('sign agreement',hit,len(pair))
print('F4 ex largest x: ',end='');k=abs(x4)<3;b=np.polyfit(x4[k],y4[k]/100,1);print(b,np.corrcoef(x4[k],y4[k])[0,1]**2)
# Fig 5
p=d[3];dr=p.get_drawings()
for x in dr:
    c=x.get('color');n=len(x['items']);r=x['rect'];f=x.get('fill')
    if (c and n>=10 and not all(abs(c[0]-v)<.02 for v in c)) or (f and r.y0>500 and r.y1<640 and r.width>10): print(n,x['type'],None if c is None else [round(v,2) for v in c],None if f is None else [round(v,2) for v in f],[round(v,1) for v in r], x['items'][0][0])
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        for s in l['spans']:
            if 320<s['bbox'][1]<660 and s['size']<9: print(s['text'][:12],[round(v,1) for v in s['bbox']])
