import pymupdf,sys,re
d=pymupdf.open("/home/ak/Documents/Flow/Taars.pdf")
for pn in (11,12,13,14,15):
    p=d[pn-1]; print('PAGE',pn)
    for x in p.get_drawings():
        c=x.get('color');n=len(x['items'])
        if c and n>=18 and sum(1 for t in x['items'] if t[0]=='l')>=18 and not all(abs(c[0]-v)<.02 for v in c):
            r=x['rect'];print(n,[round(v,2) for v in c],[round(v,1) for v in r])
