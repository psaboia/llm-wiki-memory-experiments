import re, os, sys, json
from collections import defaultdict
W = sys.argv[1]
SPECIAL = re.compile(r'^(Home|index_|log_|SCHEMA_|Edge-Types)')
pages = {}
for f in sorted(os.listdir(W)):
    if f.endswith('.md'):
        pages[f[:-3]] = open(os.path.join(W, f), encoding='utf-8').read()
def split_fm(t):
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', t, re.S)
    return (m.group(1), m.group(2)) if m else ('', t)
refs_any=defaultdict(set); refs_body=defaultdict(set); refs_typed=defaultdict(set)
for name,text in pages.items():
    fm,body=split_fm(text)
    for t in re.findall(r'\[\[([A-Za-z0-9_ -]+)\]\]', fm):
        if t in pages: refs_typed[name].add(t); refs_any[name].add(t)
    for t in re.findall(r'\]\(([A-Za-z0-9_-]+)\)', body):
        if t in pages: refs_body[name].add(t); refs_any[name].add(t)
def viols(kind):
    src = refs_typed if kind=='typed' else refs_body
    out=[]
    for a in pages:
        if SPECIAL.match(a): continue
        for b in src[a]:
            if SPECIAL.match(b) or b==a: continue
            if a not in refs_any[b]: out.append([a,b])
    return out
content=[p for p in pages if not SPECIAL.match(p)]
vt=viols('typed'); vb=viols('body')
res={
 "content_pages": len(content),
 "pages": sorted(content),
 "body_links": sum(len(refs_body[a]) for a in content),
 "typed_edges": sum(len(refs_typed[a]) for a in content),
 "viol_typed_current_gate": len(vt),
 "viol_body_anymeans": len(vb),
}
print(json.dumps(res))
