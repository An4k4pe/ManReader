"""Assemblaggio di Vileborn.
1. Segnaposto `*[IMMAGINE: percorso]*` -> nota degli agenti immagini (_lavoro/note/lotto_*.json)
   `*[Tipo: nota]* ([percorso](percorso))` + trascrizione, se c'e', come blockquote marcato.
2. Paragrafo spezzato tra due pagine: se l'ultimo paragrafo di testo di una pagina non finisce con
   punteggiatura di chiusura e il primo della successiva (saltati commenti e note) comincia con una
   minuscola, il seguito si sposta sulla pagina dove comincia, con `<!-- continua da p. N -->`.
3. File unico, indice di sfondi_e_ripetuti, controlli sui riferimenti e sui segnaposto.
Uso: python assembla_vil.py <radice> <nome.md>
"""
import glob, json, os, re, sys
R, NAME = sys.argv[1], sys.argv[2]
F = os.path.join(R, '_lavoro/finale')
note = {}
for f in sorted(glob.glob(os.path.join(R, '_lavoro/note/lotto_*.json'))):
    note.update(json.load(open(f)))

def nota(path):
    n = note.get(path)
    if not n:
        return [f'*[Immagine: NOTA MANCANTE]* ([{path}]({path}))']
    out = [f"*[{n.get('tipo') or 'Illustrazione'}: {n['nota'].rstrip('.')}]* ([{path}]({path}))"]
    tr = n.get('trascrizione')
    if tr:
        out.append("> *[Testo nell'immagine, trascritto a vista]*")
        out.append('>')
        out += ['> ' + l if l.strip() else '>' for l in tr.strip().splitlines()]
    return out

pages = {}
for n in range(1, 273):
    s = open(os.path.join(F, f'p{n:03d}.md')).read()
    lines = []
    for l in s.splitlines():
        m = re.fullmatch(r'\*\[IMMAGINE: ([^\]]+)\]\*', l.strip())
        lines += nota(m.group(1)) if m else [l]
    pages[n] = lines

def is_text(l):
    return l.strip() and not l.startswith(('#', '>', '|', '<!--', '*[', '- ')) and not re.match(r'\d+\. ', l)

joined = 0
for n in range(1, 272):
    a, b = pages[n], pages[n + 1]
    ia = max((i for i, l in enumerate(a) if l.strip()), default=None)
    ib = next((i for i, l in enumerate(b) if l.strip() and not l.startswith('<!--') and not l.startswith('*[')
               and not l.startswith('> *[Testo') and not (l.startswith('>') and b[max(i - 1, 0)].startswith('>'))), None)
    if ia is None or ib is None or not is_text(a[ia]) or not is_text(b[ib]):
        continue
    if re.search(r'[.!?:;»”")\]*]\s*$', a[ia]) or not b[ib][0].islower():
        continue
    sep = '' if a[ia].endswith(('-', '­', '—')) else ' '
    a[ia] = a[ia].rstrip('­') + sep + b[ib]
    b[ib] = f'<!-- continua da p. {n} -->'
    joined += 1

head = """# Vileborn — Manuale base

<!--
Conversione in Markdown di "Vil.pdf" (Vileborn, manuale base versione 1.0, 272 pagine).
Testo in lingua originale (italiano). Commento 'pdf p. N': inizio della pagina N del PDF
(indice posizionale; il numero stampato e' N-4). *[Tipo: nota]* (percorso): immagine rimossa.
> *[Testo nell'immagine, trascritto a vista]*: testo presente solo dentro un'immagine.
Processo e script: VERBALE.md.
-->

*[Sfondo e arredo, nota unica: le pagine stanno su carta chiara con macchie e aloni ad acquerello, con cornici e bordi colorati diversi per capitolo, pannelli scuri laterali, fregi a pennello sotto i titoli e ombre sotto gli oggetti illustrati. Tutto questo arredo è archiviato una sola volta in [sfondi_e_ripetuti/](sfondi_e_ripetuti/INDICE.md) e non è annotato pagina per pagina.]*
"""
md = head + '\n\n' + '\n\n'.join('\n'.join(pages[n]).strip() for n in range(1, 273)) + '\n'
md = re.sub(r'\n{3,}', '\n\n', md)
open(os.path.join(R, NAME), 'w').write(md)

idx = json.load(open(os.path.join(R, 'sfondi_e_ripetuti/INDICE.json')))
L = ['# sfondi_e_ripetuti/: indice', '', "Arredo e asset ripetuti, ciascuno salvato una volta; 'pagine' = indici PDF.", '',
     '| file | tipo | descrizione | xref | pagine |', '|---|---|---|---|---|']
for k, v in idx.items():
    ps = v['pagine']; pg = ', '.join(map(str, ps)) if len(ps) <= 12 else f'{len(ps)} pagine ({ps[0]}–{ps[-1]})'
    xr = v.get('xref', ''); xr = ', '.join(map(str, xr)) if isinstance(xr, list) else str(xr)
    L.append(f"| [{os.path.basename(k)}]({k.split('/', 1)[1]}) | {v['tipo']} | {v['descr']} | {xr} | {pg} |")
open(os.path.join(R, 'sfondi_e_ripetuti/INDICE.md'), 'w').write('\n'.join(L) + '\n')

refs = re.findall(r'\]\(((?:immagini|sfondi_e_ripetuti)/[^)]+)\)', md)
print('file:', NAME, '| righe', md.count('\n'), '| paragrafi ricuciti tra pagine', joined)
print('riferimenti a file inesistenti:', sorted({r for r in refs if not os.path.exists(os.path.join(R, r))}))
print('note mancanti:', md.count('NOTA MANCANTE'), '| segnaposto rimasti:', md.count('[IMMAGINE:'))
cont = sorted('immagini/' + os.path.basename(p) for p in glob.glob(os.path.join(R, 'immagini/*')))
print('immagini di contenuto mai referenziate:', [c for c in cont if c not in refs])
