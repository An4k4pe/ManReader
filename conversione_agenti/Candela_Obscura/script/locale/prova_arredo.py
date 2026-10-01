"""Prova 2: domanda chiusa sulle immagini che i segnali v2 mandano in arredo
(carta, segno, listello). Riferimento: classificazione a vista (classi_immagini.json).
"""
import json, os
from client import chiedi
R = '../..'
dec = json.load(open(f'{R}/_lavoro/v2/classi_auto.json'))
mis = json.load(open(f'{R}/_lavoro/v2/misure_asset.json'))['assets']
cl = json.load(open(f'{R}/script/classi_immagini.json'))
coda = [k for k, v in dec.items() if v in ('carta', 'segno', 'listello')]
PROMPT = ("Questa immagine e' stata estratta da un manuale di gioco di ruolo. Che cos'e'?\n"
          "A) un contenuto: illustrazione, documento, mappa, simbolo o emblema con un significato\n"
          "B) carta o texture di sfondo su cui sta il testo\n"
          "C) piccolo segno decorativo: sigillo o scarabocchio a margine, filetto, macchia d'inchiostro\n"
          "Rispondi solo con la lettera.")
out, err = [], []
for k in sorted(coda, key=int):
    f = f"{R}/_lavoro/raw/{mis[k]['file']}"
    t, pin, pout, dt, _ = chiedi(PROMPT, [f], max_tokens=5, temperature=0)
    risp = t.strip()[:1].upper()
    vero = 'arredo' if (k in cl['sfondo'] or k in cl['decorazione']) else 'contenuto'
    pred = 'contenuto' if risp == 'A' else 'arredo'
    out.append(dict(xref=k, regola=dec[k], risposta=t, vista=vero, secondi=dt))
    if pred != vero:
        err.append((k, dec[k], t, vero))
os.makedirs(f'{R}/_lavoro/locale', exist_ok=True)
json.dump(out, open(f'{R}/_lavoro/locale/prova_arredo.json', 'w'), indent=1)
print('in coda', len(coda), '| errori', len(err), '| secondi', round(sum(o['secondi'] for o in out), 1))
for e in err: print('  errore:', e)
for k in ('5349', '9694', '8936'):
    o = [x for x in out if x['xref'] == k]
    print(' ', k, o[0]['risposta'] if o else 'non in coda')
