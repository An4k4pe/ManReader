"""Classificazione automatica degli asset (v2): regole di ManReader + segnali aggiunti.
Regole, in ordine (la prima che scatta decide):
  R0 immagine inline (xref 0)                       -> ombra        [mia, Candela]
  R1 stesso contenuto su piu' di una pagina          -> ricorrente   [ManReader, document_asset_policy]
  R2 lato minore < lettera piu' piccola stampata     -> sotto scala  [ManReader, BELOW_TEXT_SCALE]
  R3 rapporto lati >= ASPECT                         -> listello     [mia]
  R4 lato maggiore <= MARGINE x corpo del testo      -> segno        [mia]
  R5 densita' di bordi < BORDI e testo sopra >= TESTO -> carta        [mia]
  altrimenti                                         -> contenuto
ASPECT, MARGINE, BORDI e TESTO sono tarati guardando Candela: vanno validati altrove.
Uso: python classifica_asset.py <radice> [--solo-manreader]
"""
import json, sys, os, collections
R = sys.argv[1]; only_mr = '--solo-manreader' in sys.argv
ASPECT, MARGINE, BORDI, TESTO = 10, 5, 0.09, 0.10
m = json.load(open(os.path.join(R, '_lavoro/v2/misure_asset.json')))
body, min_letter = m['body'], m['min_letter']

def classify(v):
    if v['inline']: return 'ombra'
    if len(v['pages']) > 1: return 'ricorrente'
    if v['min_side'] < min_letter: return 'sotto_scala'
    if only_mr: return 'contenuto'
    if v['max_side'] / max(v['min_side'], 0.1) >= ASPECT: return 'listello'
    if v['max_side'] <= MARGINE * body: return 'segno'
    if v['edges'] < BORDI and v['text_cover'] >= TESTO: return 'carta'
    return 'contenuto'

dec = {k: classify(v) for k, v in m['assets'].items()}
json.dump(dec, open(os.path.join(R, '_lavoro/v2/classi_auto' + ('_manreader' if only_mr else '') + '.json'), 'w'), indent=1)

# confronto con le etichette a vista (solo xref: le inline sono tutte ombre per ispezione)
c = json.load(open(os.path.join(R, 'script/classi_immagini.json')))
manual = lambda x: 'arredo' if (x in c['sfondo'] or x in c['decorazione']) else 'contenuto'
auto = lambda k: 'contenuto' if dec[k] == 'contenuto' else 'arredo'
# tipo di nota scritta a vista per ogni immagine di contenuto
import re, glob
per = json.load(open(os.path.join(R, '_lavoro/immagini_per_pagina.json')))
file_of = {str(i['xref']): i['file'] for v in per.values() for i in v}
md = open(os.path.join(R, 'Candela_Obscura_Core_Rulebook.md')).read()
tipo = {}
for x, f in file_of.items():
    mm = re.search(r'\*\[(Illustrazione|Mappa|Documento|Scheda|Simbolo)[^\n]*?\(\[' + re.escape(f), md)
    tipo[x] = mm.group(1) if mm else '?'
conf = collections.Counter(); errs = []
for k, v in m['assets'].items():
    if not v['xref']: continue
    a, b = manual(k), auto(k)
    conf[(a, b)] += 1
    if a != b: errs.append((k, a, dec[k], tipo.get(k, '-')))
n = sum(conf.values()); ok = conf[('arredo','arredo')] + conf[('contenuto','contenuto')]
grave = [e for e in errs if e[1] == 'contenuto' and e[3] in ('Illustrazione', 'Mappa', 'Documento', 'Scheda')]
print('regole:', 'solo ManReader (R1-R2)' if only_mr else 'R0-R5')
print('classi automatiche:', collections.Counter(dec.values()))
print(f'accordo con la vista: {ok}/{n} = {ok/n:.3f}')
print('contenuto->arredo:', conf[('contenuto','arredo')], '| arredo->contenuto:', conf[('arredo','contenuto')])
print('errori gravi (Illustrazione/Mappa/Documento/Scheda finite in arredo):', grave)
print('tutti gli errori:', errs)
