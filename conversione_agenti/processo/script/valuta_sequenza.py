"""Confronto indipendente dal formato: solo la sequenza delle parole (ordine di lettura + completezza).
Tolti markup, commenti, note immagine, trascrizioni e glifi. Per pagina: SequenceMatcher sulle liste di
parole. Uso: python valuta_sequenza.py <fonte: cartella bozza | document.md IR2> <cartella finale> <etichetta>
"""
import difflib, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from valuta_bozza import norm
src, fin, tag = sys.argv[1:4]
if os.path.isdir(src):
    get = lambda n: open(os.path.join(src, f'p{n:03d}.md')).read() if os.path.exists(os.path.join(src, f'p{n:03d}.md')) else ''
else:
    parts = re.split(r'<!-- page:(\d+) -->', open(src).read())
    pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
    get = lambda n: '\n'.join(l for l in pages.get(n, '').splitlines() if not re.match(r'^> \*\*\[[^\]]*\]\*\*', l))
W = lambda s: [w.lower() for w in re.findall(r"[^\W_]+", re.sub(r'\[glifo:[^\]]*\]', ' ', s))]
rs = []
for f in sorted(os.listdir(fin)):
    m = re.fullmatch(r'p(\d{3})\.md', f)
    if not m:
        continue
    a = W(norm(get(int(m.group(1))), False)); b = W(norm(open(os.path.join(fin, f)).read(), True))
    if not a and not b:
        rs.append(1.0); continue
    rs.append(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio())
rs.sort()
print(f"{tag:16} pagine {len(rs):3} | parole in ordine >=0.99: {sum(r >= 0.99 for r in rs):3} ({sum(r >= 0.99 for r in rs)/len(rs):.0%}) | <0.95 {sum(r < 0.95 for r in rs):3} | mediana {rs[len(rs)//2]:.3f}")
