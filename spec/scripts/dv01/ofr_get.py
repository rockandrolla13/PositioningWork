import json,sys,time,urllib.request,os
out=sys.argv[1]
ms=[]
for c in ("TU","FV","TY","UXY","US","WN"):
    for side in ("LONG","SHORT"):
        for kind in ("POS10YREQV","POSITION"):
            ms.append(f"TFF-LF_{c}_{side}_{kind}")
for g in ("LF","AI","OR","DI"):
    for side in ("LONG","SHORT"):
        for kind in ("DV01","POS10YREQV","POSITION"):
            ms.append(f"TFF-{g}_TREAS_{side}_{kind}")
for m in ms:
    p=f"{out}/{m}.json"
    if os.path.exists(p): continue
    r=urllib.request.urlopen(urllib.request.Request(f"https://data.financialresearch.gov/hf/v1/series/timeseries?mnemonic={m}",headers={"User-Agent":"Mozilla/5.0"}),timeout=60).read()
    open(p,"wb").write(r); time.sleep(.2)
print(len(ms),"series")
