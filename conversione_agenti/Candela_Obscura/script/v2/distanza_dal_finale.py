"""Quanto una bozza e' gia' il finale rivisto, pagina per pagina.
Dal finale si tolgono cio' che solo la revisione puo' aggiungere (note immagine,
trascrizioni dall'immagine, blocchi <!-- da render -->) e da entrambi commenti, righe
vuote e righe '>' vuote. Somiglianza = SequenceMatcher sui caratteri.
Uso: python distanza_dal_finale.py <radice> <cartella_bozza> [--dettaglio]
"""
import re, sys, os, difflib, json
R, BZ = sys.argv[1], sys.argv[2]

def norm(s, final):
    out, skip = [], False
    for line in s.splitlines():
        if final:
            if re.match(r'^\*\[(Illustrazione|Mappa|Documento|Scheda|Simbolo)', line):
                skip = False; continue
            if "Testo nell'immagine" in line or line.strip() == '<!-- da render -->':
                skip = True; continue
            if skip and (line.startswith('>') or line.strip()):
                continue
            skip = False
        line = re.sub(r'<!--.*?-->', '', line).rstrip().rstrip('\\')
        if line.strip() in ('', '>'):
            continue
        out.append(line)
    return '\n'.join(out)

res = {}
for n in range(1, 212):
    f = norm(open(os.path.join(R, f'_lavoro/finale/p{n:03d}.md')).read(), True)
    b = norm(open(os.path.join(BZ, f'p{n:03d}.md')).read(), False)
    res[n] = 1.0 if f == b else difflib.SequenceMatcher(None, b, f, autojunk=False).ratio()
json.dump(res, open(os.path.join(BZ, '..', 'distanza.json'), 'w'))
v = list(res.values())
print(f"{BZ}: identiche {sum(x == 1.0 for x in v)} | >=0.99 {sum(x >= 0.99 for x in v)} | >=0.95 {sum(x >= 0.95 for x in v)} | <0.95 {sum(x < 0.95 for x in v)} su {len(v)}")
if '--dettaglio' in sys.argv:
    print(sorted(((n, round(x, 3)) for n, x in res.items() if x < 0.99), key=lambda t: t[1]))
