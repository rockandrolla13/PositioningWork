import pymupdf,numpy as np
d=pymupdf.open("/home/ak/Documents/Flow/ETF Flow Risk-o-Meter (EFRoM).pdf"); p=d[8]
for x in p.get_drawings():
    c=x.get('color');n=len(x['items'])
    if c and n>=2 and x['rect'].y1<320 and x['rect'].x0>380: print(n,[round(v,2) for v in c],[round(v,1) for v in x['rect']],x.get('dashes'))
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        for s in l['spans']:
            if s['bbox'][1]<320 and s['bbox'][0]>370 and s['size']<9: print(s['text'][:30],[round(v,1) for v in s['bbox']])
