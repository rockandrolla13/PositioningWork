import pymupdf,json
d=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf")
p=d[2]
for x in p.get_drawings():
    n=len(x['items']); r=x['rect']
    c=x.get('color');f=x.get('fill')
    if r.y1<300 and (n>=3 or (f and r.width<20)):
        print(n,x['type'],'col',None if c is None else [round(v,2) for v in c],'fill',None if f is None else [round(v,2) for v in f],[round(v,1) for v in r])
print('---text')
for w in p.get_text('words'):
    if w[1]<300 and w[1]>160: 
        pass
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        for s in l['spans']:
            if 160<s['bbox'][1]<300 and s['size']<9: print(s['text'],[round(v,1) for v in s['bbox']])
