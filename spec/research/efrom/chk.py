import pymupdf,sys,collections
for p in sys.argv[1:]:
    d=pymupdf.open(p);print(p.split('/')[-1],len(d))
    for i,pg in enumerate(d):
        dr=pg.get_drawings();imgs=pg.get_images()
        long=[(len(x['items']),x.get('color'),tuple(round(v) for v in x['rect'])) for x in dr if x.get('color') and sum(1 for t in x['items'] if t[0]=='l')>=8]
        long.sort(key=lambda t:-t[0])
        print(i+1,'draw',len(dr),'imgs',len(imgs),'longpaths',len(long),long[:6])
