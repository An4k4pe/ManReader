"""Confronta il Markdown di ManReader IR 2 (document.md, pagine separate da <!-- page:NNNN -->) con le pagine
rivedute, con lo stesso metro di valuta_bozza.py. Tolte le note d'asset di IR 2 ('> **[...]**' con dimensioni).
Uso: python valuta_ir2.py <document.md> <cartella finale> <etichetta>
"""
import difflib, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from valuta_bozza import norm
doc, fin, tag = sys.argv[1:4]
parts = re.split(r'<!-- page:(\d+) -->', open(doc).read())
pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
rs = []
for f in sorted(os.listdir(fin)):
    m = re.fullmatch(r'p(\d{3})\.md', f)
    if not m:
        continue
    n = int(m.group(1))
    a = pages.get(n, '')
    a = '\n'.join(l for l in a.splitlines() if not re.match(r'^> \*\*\[[^\]]*\]\*\*', l))
    a = norm(a, False); b = norm(open(os.path.join(fin, f)).read(), True)
    rs.append(1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio())
rs.sort()
print(f"{tag:12} pagine {len(rs):3} | identiche {sum(r == 1.0 for r in rs):3} | >=0.99 {sum(r >= 0.99 for r in rs):3} ({sum(r >= 0.99 for r in rs)/len(rs):.0%}) | <0.95 {sum(r < 0.95 for r in rs):3} | mediana {rs[len(rs)//2]:.3f}")
