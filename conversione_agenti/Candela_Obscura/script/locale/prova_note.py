"""Prova 1: note brevi sulle immagini con il modello locale.
30 immagini di contenuto a caso (seed 7), stesso prompt; accanto la nostra nota
(fase 1) e l'alt-text dell'editore della stessa pagina, per il giudizio.
Scrive ../../_lavoro/locale/prova_note.json e .md
"""
import json, random, re, os, sys
from client import chiedi
R = '../..'
per = json.load(open(f'{R}/_lavoro/immagini_per_pagina.json'))
md = open(f'{R}/Candela_Obscura_Core_Rulebook.md').read()
alt = json.load(open(f'{R}/_lavoro/alt_editore.json'))
imgs = sorted({(int(p), i['file']) for p, v in per.items() for i in v if i['file'].startswith('immagini/')})
random.seed(7); camp = random.sample(imgs, 30)
PROMPT = ("Sei l'editor di un manuale di gioco di ruolo. Questa immagine verra' tolta dal testo e "
          "sostituita da una nota breve. Scrivi la nota in italiano, 4-15 parole, concreta: chi o che cosa "
          "si vede, piu' la tecnica se e' distintiva (acquerello, schizzo a matita, mappa, documento). "
          "Niente interpretazioni. Rispondi solo con la nota.")
out = []
for pg, f in sorted(camp):
    t, pin, pout, dt, _ = chiedi(PROMPT, [f'{R}/{f}'], max_tokens=80)
    m = re.search(r'\*\[([^\n]*?)\]\* \(\[' + re.escape(f), md)
    out.append(dict(pagina=pg, file=f, locale=t, nostra=m.group(1) if m else None,
                    editore=[a['alt'] for a in alt if a['page'] == pg], secondi=dt, token_in=pin, token_out=pout))
    print(pg, f, dt, 's |', t, flush=True)
os.makedirs(f'{R}/_lavoro/locale', exist_ok=True)
json.dump(out, open(f'{R}/_lavoro/locale/prova_note.json', 'w'), indent=1, ensure_ascii=False)
print('totale secondi', round(sum(o['secondi'] for o in out), 1))
