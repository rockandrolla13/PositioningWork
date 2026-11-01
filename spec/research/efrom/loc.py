import pymupdf,sys
d=pymupdf.open(sys.argv[1])
for k in sys.argv[2:]:
    print(k,[i+1 for i,p in enumerate(d) if p.search_for(k)][:12])
