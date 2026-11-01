import pymupdf,numpy as np
d=pymupdf.open("/home/ak/Documents/Flow/Taars.pdf")
for pg,x0 in ((11,344.5),(13,92.2)):
    for dr in d[pg-1].get_drawings():
        c=dr.get('color');r=dr['rect']
        if c and len(dr['items'])==22 and abs(r.x0-x0)<.5:
            xs=[dr['items'][0][1].x]+[i[2].x for i in dr['items']]
            print(pg,np.round(np.diff(xs),2));break
for b in d[12].get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        for s in l['spans']:
            if '-Nov' in s['text'] or '-Dec' in s['text']: print(s['text'],round(s['bbox'][0],1),round(s['bbox'][2],1),round(s['bbox'][1]));
