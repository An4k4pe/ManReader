"""Assembla le pagine riviste (_lavoro/finale/pNNN.md) nel file unico, scrive l'indice leggibile
di sfondi_e_ripetuti/ e controlla i riferimenti alle immagini.
Uso: python 06_assembla.py <radice> <nome_file.md>
"""
import os, re, sys, json, glob
R, NAME = sys.argv[1], sys.argv[2]
F = os.path.join(R, '_lavoro/finale')
idx = json.load(open(os.path.join(R, 'sfondi_e_ripetuti/INDICE.json')))

def pages(ps):
    return ', '.join(map(str, ps)) if len(ps) <= 12 else f'{len(ps)} pagine ({ps[0]}–{ps[-1]})'

head = """# Candela Obscura — Core Rulebook

<!--
Conversione in Markdown del PDF "Candela Obscura - DP - Core Rulebook (OEF, 2023-11).pdf" (211 pagine).
Testo in lingua originale (inglese); note sulle immagini in italiano.
Convenzioni:
  commento 'pdf p. N': inizio della pagina N del PDF (indice posizionale; il numero stampato e' N-6 da p. 7).
  *[Illustrazione|Mappa|Documento|Scheda|Simbolo: nota]* (percorso) : immagine rimossa e cosa rappresenta.
  > *[Testo nell'immagine, trascritto a vista]* : testo presente solo dentro un'immagine.
  > *[Nota manoscritta]* / *[Dattiloscritto]* : annotazioni in-world impaginate come scrittura a mano o a macchina.
  > **TITOLO** + testo citato : riquadro del manuale.
Processo e script: VERBALE.md.
-->

*[Sfondo e arredo, nota unica: tutte le pagine interne stanno su una pergamena invecchiata color avorio con cornice a filetti ornati, piè di pagina "CANDELA OBSCURA" e testatina verticale; molte pagine hanno carte strappate sotto il testo, ombre portate sotto le illustrazioni e piccoli sigilli a penna ai margini. Tutto questo arredo è archiviato una sola volta in [sfondi_e_ripetuti/](sfondi_e_ripetuti/INDICE.md) e non è annotato pagina per pagina.]*

"""
parts = [head]
for n in range(1, 212):
    f = os.path.join(F, f'p{n:03d}.md')
    if not os.path.exists(f):
        parts.append(f'<!-- pdf p. {n} -->\n\n<!-- PAGINA MANCANTE -->\n')
        continue
    s = open(f).read().strip()
    parts.append(s + '\n')
md = '\n\n'.join(parts)

# Gerarchia: la tipografia usa lo stesso corpo (Quelity 16) per sezioni annidate; i segnalibri del PDF
# le mettono al livello 3. Le si abbassa di un livello: (pagina, titolo d'inizio) -> (pagina, titolo di fine
# escluso). Dentro i casi d'esempio 'EXAMPLE SESSION' e' figlio del caso: +2 fino al caso successivo.
DEMOTE = [
    ((26, 'ROLE: FACE'), (31, 'STEP 2: DETERMINE ACTION RATINGS')),
    ((33, 'ROLE ABILITIES'), (39, 'STEP 7: ADD CHARACTER DETAILS')),
    ((40, 'RELATIONSHIP QUESTIONS'), (45, 'CREATING YOUR CIRCLE')),
    ((114, 'BRIAR GREEN'), (133, 'OLDFAIRE SITES')),
    ((134, 'THE ANATITHENAI'), (151, 'FAIRELANDS LANDMARKS')),
    ((152, 'THE BRIDLEBORNE MOUNTAINS'), (165, 'RUNNING THE GAME')),
    ((177, 'THE LIGHT EATER OF BRIDLEBORNE'), (193, 'ADDITIONAL ASSIGNMENTS')),
]
out, page, active, extra = [], 0, None, 0
demoted = 0
for line in md.split('\n'):
    m = re.match(r'<!-- pdf p\. (\d+) -->', line)
    if m:
        page = int(m.group(1))
    h = re.match(r'^(#{1,6}) (.*)$', line)
    if h:
        title = h.group(2).strip()
        for (p0, t0), (p1, t1) in DEMOTE:
            if page == p0 and title == t0:
                active = (p1, t1); extra = 0
            if active and page == active[0] and title == active[1]:
                active = None; extra = 0
        if active and page >= 177 and len(h.group(1)) == 2:
            extra = 1 if title == 'EXAMPLE SESSION' else 0
        if active and len(h.group(1)) >= 2:
            line = '#' * min(6, len(h.group(1)) + 1 + extra) + ' ' + title
            demoted += 1
    out.append(line)
md = '\n'.join(out)
print('titoli abbassati di livello:', demoted)
md = re.sub(r'\n{3,}', '\n\n', md)
open(os.path.join(R, NAME), 'w').write(md)

# indice leggibile
L = ['# sfondi_e_ripetuti/: indice', '',
     "Arredo e asset ripetuti, ciascuno salvato una volta. 'pagine' = indici PDF in cui compare.", '',
     '| file | tipo | descrizione | xref | pagine |', '|---|---|---|---|---|']
for k, v in idx.items():
    xr = v.get('xref', '')
    xr = ', '.join(map(str, xr)) if isinstance(xr, list) else str(xr)
    L.append(f"| [{os.path.basename(k)}]({k.split('/', 1)[1]}) | {v['tipo']} | {v['descr']} | {xr} | {pages(v['pagine'])} |")
open(os.path.join(R, 'sfondi_e_ripetuti/INDICE.md'), 'w').write('\n'.join(L) + '\n')

# controllo riferimenti
refs = re.findall(r'\]\(((?:immagini|sfondi_e_ripetuti)/[^)]+)\)', md)
missing = sorted({r for r in refs if not os.path.exists(os.path.join(R, r))})
content = sorted('immagini/' + os.path.basename(p) for p in glob.glob(os.path.join(R, 'immagini/*')))
unref = [c for c in content if c not in refs]
print('file scritto:', NAME, '| righe', md.count('\n'), '| riferimenti a immagini', len(refs))
print('riferimenti a file inesistenti:', missing)
print('immagini di contenuto mai referenziate:', unref)
print('pagine mancanti:', [n for n in range(1, 212) if not os.path.exists(os.path.join(F, f'p{n:03d}.md'))])
