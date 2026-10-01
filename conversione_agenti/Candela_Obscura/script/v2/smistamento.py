"""Smistamento delle pagine: quali vanno riviste da un agente sul testo.
Segnali calcolati dal PDF e dalla bozza v3, mai dal finale:
  mano      righe di famiglie d'annotazione (scrittura a mano)
  didasc    testo dentro il riquadro di un'immagine di contenuto (didascalie, etichette)
  righe     righe con piu' gruppi di parole separati da un vuoto largo (tabelle, griglie)
  cornice   riquadro disegnato che la bozza non ha potuto rendere
  numeri    maggioranza di righe che finiscono con un numero (indici, sommari)
  frammenti maggioranza di paragrafi di tre parole o meno (linee del tempo, etichette)
  ordine    un paragrafo sta sopra il precedente nella stessa colonna (ordine del flusso
            diverso da quello di lettura)
Scrive _lavoro/v3/smistamento.json e, se c'e' _lavoro/v3/distanza.json, misura il
richiamo sulle pagine con somiglianza < SOGLIA.
Uso: python smistamento.py <pdf> <radice>
"""
import json
import os
import re
import sys

import fitz

sys.path.insert(0, os.path.dirname(__file__))
import bozza_testo_v2 as B  # noqa: E402
import bozza_testo_v3 as V  # noqa: E402

SOGLIA = 0.99
PDF, R = sys.argv[1], sys.argv[2]
d = fitz.open(PDF)
B.FATTI = B.measure_facts(d)
body = B.FATTI['body_size']
per = json.load(open(os.path.join(R, '_lavoro/immagini_per_pagina.json')))


def signals(p):
    n = p.number + 1
    lines = V.page_lines(p)
    pars = []
    for ln in lines:
        if pars and V.continues(pars[-1], ln):
            pars[-1]['lines'].append(ln)
        else:
            pars.append(dict(role=ln['role'], inbox=ln['inbox'], lines=[ln]))
    s = set()
    if any(ln['role'] == 'hand' for ln in lines):
        s.add('mano')
    imgs = [fitz.Rect(i['bbox']) for i in per.get(str(n), [])]
    if any(any(r.contains(fitz.Point((ln['bbox'][0] + ln['bbox'][2]) / 2, (ln['bbox'][1] + ln['bbox'][3]) / 2))
               for r in imgs) for ln in lines):
        s.add('didasc')
    # righe con gruppi separati: parole della stessa riga visiva con un vuoto > 2 corpi
    words = p.get_text('words')
    rows = {}
    for w in words:
        rows.setdefault(round(w[3]), []).append(w)
    gapped = sum(1 for ws in rows.values()
                 if any(b[0] - a[2] > 2 * body for a, b in zip(sorted(ws), sorted(ws)[1:])))
    if gapped >= 3:
        s.add('righe')
    pars2 = [dict(par, boxid=None) for par in pars]
    V.box_groups(p, pars2)
    for rect in V.frames(p):
        inside = [par for par in pars2 if V.inside(par, rect)]
        if len(inside) >= 2 and not any(par['inbox'] for par in inside):
            s.add('cornice')
    txt = [ln['text'] for ln in lines]
    if txt and sum(bool(re.search(r'\d\s*$', t)) for t in txt) > len(txt) / 2:
        s.add('numeri')
    if len(pars) >= 6 and sum(len(' '.join(l['text'] for l in par['lines']).split()) <= 3 for par in pars) > len(pars) / 2:
        s.add('frammenti')
    # ordine: un paragrafo che comincia piu' di 3 corpi sopra l'inizio del precedente
    # (v2 del segnale: la v1 guardava solo la stessa colonna e perdeva p. 26)
    for a, b in zip(pars, pars[1:]):
        if b['lines'][0]['bbox'][1] < a['lines'][0]['bbox'][1] - 3 * body:
            s.add('ordine')
            break
    # elenco annidato: righe con marcatore a due rientri diversi (aggiunto dopo pp. 61 e 205)
    mx = {round(ln['bbox'][0] / (body / 2)) for ln in lines if ln['text'].startswith('•')}
    if len(mx) >= 2:
        s.add('elenco')
    return sorted(s)


res = {p.number + 1: signals(p) for p in d}
os.makedirs(os.path.join(R, '_lavoro/v3'), exist_ok=True)
json.dump(res, open(os.path.join(R, '_lavoro/v3/smistamento.json'), 'w'), indent=0)
flag = {n for n, s in res.items() if s}
print(f'pagine segnalate: {len(flag)} su {len(res)} ({len(flag) / len(res):.0%})')
from collections import Counter  # noqa: E402
print('segnali:', Counter(x for s in res.values() for x in s))
dist = os.path.join(R, '_lavoro/v3/distanza.json')
if os.path.exists(dist):
    dd = {int(k): v for k, v in json.load(open(dist)).items()}
    need = {n for n, v in dd.items() if v < SOGLIA}
    miss = sorted(need - flag)
    print(f'da rivedere (somiglianza < {SOGLIA}): {len(need)} | prese: {len(need & flag)} | perse: {miss}')
    print('perse, con somiglianza:', [(n, round(dd[n], 3)) for n in miss])
    band = {n for n, v in dd.items() if SOGLIA <= v < 1.0}
    print(f'tra {SOGLIA} e 1 (differenze minori): {len(band)}, segnalate comunque {len(band & flag)}')
