"""Affianca, pagina per pagina, le note immagine scritte a vista e gli alt-text dell'editore
(_lavoro/alt_editore.json). Solo per il controllo: produce _lavoro/confronto_alt.md.
Uso: python 07_confronto_alt.py <radice>
"""
import json, re, os, sys, collections
R = sys.argv[1]
alt = json.load(open(os.path.join(R, '_lavoro/alt_editore.json')))
by = collections.defaultdict(list)
for a in alt:
    by[a['page']].append(a['alt'])
notes = collections.defaultdict(list)
for n in range(1, 212):
    s = open(os.path.join(R, f'_lavoro/finale/p{n:03d}.md')).read()
    notes[n] = re.findall(r'^\*\[((?:Illustrazione|Mappa|Documento|Scheda|Simbolo)[^\]]*)\]\*', s, re.M)
L = ['| p. | note (a vista) | alt-text editore |', '|---|---|---|']
for n in range(1, 212):
    if notes[n] or by[n]:
        L.append(f"| {n} | {'<br>'.join(notes[n]) or '—'} | {'<br>'.join(by[n]) or '—'} |")
open(os.path.join(R, '_lavoro/confronto_alt.md'), 'w').write('\n'.join(L) + '\n')
print('pagine con note', sum(1 for n in notes if notes[n]), '| pagine con alt', len([k for k in by if k]),
      '| note', sum(len(v) for v in notes.values()), '| alt', len(alt))
