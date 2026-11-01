"""Turn the ranked entries in A to D into a LaTeX annotated bibliography. Run from this folder."""
import re
ESC={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
def esc(s):
    s=re.sub(r'\*\*|\*|`','',s).strip()
    s=''.join(ESC.get(c,c) for c in s)
    return s.replace('ı','i')
def link(u):
    u=u.rstrip('.,;)*`] ')
    return r'\nolinkurl{'+u.replace('%',r'\%').replace('#',r'\#').replace('_',r'\_')+'}'
def grab(p,keys):
    for k in keys:
        m=re.search(r'(?:\*\*)?'+k+r':?(?:\*\*)?:?\s*(.+)',p)
        if m: return m.group(1).strip()
    return ''
out={};n=0;miss=[]
for f,lab,head in (("A_credit_etfs.md","A. Credit ETFs",r'\n(?=### \d+\.)'),("B_corporate_rfq.md","B. Corporate bonds and RFQ",r'\n(?=\*\*\d+\. )'),("C_cdx_futures.md","C. CDX and credit futures",r'\n(?=### \d+\.)'),("D_positioning_pain.md","D. Positioning, pain and test design",r'\n(?=### \d+\.)')):
    t=open(f).read(); stop=t.find('\n## Synthesis'); 
    sup=t.find('\n## Supporting records'); 
    if sup>0: stop=min(stop,sup)
    alt=t.find('\n## Side references')
    if alt>0: stop=min(stop,alt)
    t=t[:stop]; items=[]
    for p in re.split(head,t)[1:]:
        p=re.split(r'\n## |\n### (?!\d)',p)[0]
        first=p.split('\n')[0]
        if f.startswith('B'):
            cit=re.sub(r'^\*\*\d+\.\s*|\*\*$','',first)
        else:
            cit=grab(p,['Citation']) or (p.split('\n')[1] if len(p.split('\n'))>1 else '')
        m=re.search(r'10\.\d{4,9}/[^\s|)>`"\]]+',p); u=re.search(r'https?://[^\s|)>`"\]]+',p)
        loc=link(m.group(0)) if m else (link(u.group(0)) if u else '')
        tier=re.search(r'Tier:?\*{0,2}\s*(\d)',p); read=re.search(r'Read:?\*{0,2}:?\s*([^\n]+)',p)
        mean=grab(p,['For positioning','Means for us','For credit','For an RFQ[^:]*','For a pain[^:]*','For CDX[^:]*','What it means[^:]*','Meaning[^:]*','For us'])
        if not cit or not tier: miss.append((f[0],first[:50]))
        rd=read.group(1) if read else 'not stated'
        rd=re.split(r'(?<=[.])\s',rd)[0]
        items.append((cit,loc,tier.group(1) if tier else '?',rd,mean)); n+=1
    out[lab]=items
L=[]
for lab,items in out.items():
    L.append(r'\subsection*{'+esc(lab)+'}')
    L.append(r'\begin{enumerate}[leftmargin=*,itemsep=3pt]')
    for c,loc,ti,rd,me in items:
        s=esc(c)+(' '+loc+'.' if loc else '')+f' \\emph{{Tier {ti}. Read: {esc(rd)}}}'
        if me: s+=r' \textbf{For us:} '+esc(me)
        L.append(r'\item '+s)
    L.append(r'\end{enumerate}')
open("bib_entries.tex","w").write("\n".join(L)+"\n")
print("entries",n,{k:len(v) for k,v in out.items()},"problems",miss[:12])
print("no meaning line:",sum(1 for v in out.values() for x in v if not x[4]))
