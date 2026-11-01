import pymupdf,numpy as np,json
d=pymupdf.open("/home/ak/Documents/Flow/0900b8c08b403162.pdf");p=d[0];dr=p.get_drawings()
line=[x for x in dr if x.get('color') and abs(x['color'][0]-.11)<.01 and len(x['items'])==18][0]
pts=[];
for it in line['items']:
    if not pts: pts.append((it[1].x,it[1].y))
    pts.append((it[2].x,it[2].y))
pts=np.array(pts)
gr=[x for x in dr if x.get('color') and abs(x['color'][0]-.85)<.01 and len(x['items'])>=8][0]['rect'];print('grid',gr)
c=(gr.y0+gr.y1)/2;lev=(c-pts[:,1])/((gr.y1-gr.y0)/5)
f=json.load(open('fig2.json'));old=np.array(f['lev'])
for l,a,b in zip(f['labs']+['May-16'],lev,list(old)+[None]): print(l,round(a,2),None if b is None else round(b,2),None if b is None else round(a-b,2))
b=[x for x in dr if x.get('fill') and abs(x['fill'][0]-.33)<.01 and len(x['items'])==18]
print('bars',len(b))
print('corr',np.corrcoef(lev[:18],old)[0,1],'maxdiff',np.abs(lev[:18]-old).max())
