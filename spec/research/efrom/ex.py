import pymupdf,json,numpy as np
d=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf")
p=d[2]
dr=p.get_drawings()
line=[x for x in dr if x.get('color') and abs(x['color'][0]-.11)<.01 and len(x['items'])==17][0]
pts=[]
for it in line['items']:
    if not pts: pts.append((it[1].x,it[1].y))
    pts.append((it[2].x,it[2].y))
pts=np.array(pts); print('line pts',len(pts))
lev=(231.0-pts[:,1])/ (118.4/5)
labs="Nov-14 Dec-14 Jan-15 Feb-15 Mar-15 Apr-15 May-15 Jun-15 Jul-15 Aug-15 Sep-15 Oct-15 Nov-15 Dec-15 Jan-16 Feb-16 Mar-16 Apr-16".split()
bar=[x for x in dr if x.get('fill') and abs(x['fill'][0]-.33)<.01 and len(x['items'])==17][0]
bs=[]
for it in bar['items']:
    r=it[1] if it[0]=='re' else None
    if r is None: print(it[0]);continue
    bs.append((r.x0,r.x1,r.y0,r.y1))
bs=sorted(bs); 
ch=[]
for x0,x1,y0,y1 in bs:
    v=(231.0-y0)/ (118.4/8) if abs(y1-231.0)<abs(y0-231.0) else (231.0-y1)/(118.4/8)
    ch.append(v)
print('bars',len(ch))
print('month level  bar  dlevel')
for i,l in enumerate(labs):
    print(l,round(lev[i],2), '' if i==0 else round(ch[i-1],2), '' if i==0 else round(lev[i]-lev[i-1],2))
print('corr bar vs dlevel',np.corrcoef(ch,np.diff(lev))[0,1],'rmse',np.sqrt(np.mean((np.array(ch)-np.diff(lev))**2)))
json.dump(dict(labs=labs,lev=lev.tolist(),ch=ch),open('fig2.json','w'))
# scatter fig3/4
for name,xr in (('fig3',(40,300)),('fig4',(300,600))):
    ms=[x for x in dr if x.get('fill') and x['rect'].y0>500 and xr[0]<x['rect'].x0<xr[1] and x['rect'].width<9 and x['rect'].height<9 and x['rect'].width>2]
    print(name,'markers',len(ms), set(tuple(round(v,2) for v in m['fill']) for m in ms))
    print(sorted(set(len(m['items']) for m in ms)))
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        for s in l['spans']:
            if 505<s['bbox'][1]<640 and s['size']<8: print(s['text'],[round(v,1) for v in s['bbox']])
