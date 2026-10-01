"""Prova 2c (terzo disegno, dopo i fallimenti di 2 e 2b): ragionamento acceso con tetto,
istruzione di sistema che spiega il progetto e il criterio, fatti misurati nel prompt,
immagine isolata + zona di pagina col riquadro rosso. Stessa coda, stesso criterio.
"""
import json, os, re
from client import chiedi
R = '../..'
dec = json.load(open(f'{R}/_lavoro/v2/classi_auto.json'))
M = json.load(open(f'{R}/_lavoro/v2/misure_asset.json')); mis = M['assets']; body = M['body']
cl = json.load(open(f'{R}/script/classi_immagini.json'))
coda = [k for k, v in dec.items() if v in ('carta', 'segno', 'listello')]
SYSTEM = """Lavori a un progetto che converte manuali di giochi di ruolo da PDF in Markdown ed EPUB per la lettura.
Ogni immagine del PDF subisce una di due sorti:
- CONTENUTO: nel testo al suo posto si mette una nota breve che dice che cosa mostrava (es. "mappa della citta'",
  "guerriero in armatura", "lettera scritta a mano"). Vale per tutto cio' che il lettore perderebbe se sparisse:
  illustrazioni, mappe, documenti di gioco, emblemi di organizzazioni presentati dal testo, schemi.
- ARREDO: finisce in una cartella a parte senza nessuna nota nel testo, perche' serve solo all'impaginazione e
  il lettore non perde niente. Esempi tipici: la pergamena o il foglio di carta invecchiata su cui e' stampato il
  testo del manuale (il testo sopra viene gia' estratto a parte, la carta sotto e' solo sfondo); sigilli, ghirigori
  e scarabocchi ornamentali piccoli ai margini della pagina; filetti, strisce, macchie d'inchiostro; bordi.
La domanda da farsi e': se questa immagine sparisse dal libro, il lettore perderebbe un'informazione o
un'illustrazione? Se si', CONTENUTO. Se no, ARREDO.
Ragiona brevemente, poi chiudi con una riga finale esattamente cosi': RISPOSTA: CONTENUTO oppure RISPOSTA: ARREDO"""
ctx = f'{R}/_lavoro/locale/ctx'
out, err = [], []
for k in sorted(coda, key=int):
    v = mis[k]
    fatti = (f"Fatti misurati: l'elemento e' grande circa {v['max_side']:.0f}x{v['min_side']:.0f} pt, mentre il testo del "
             f"manuale e' a {body:.0f} pt; il {min(v['text_cover'],1)*100:.0f}% della sua area ha testo del manuale "
             f"stampato sopra; compare su {len(v['pages'])} pagina/e.")
    prompt = ("Prima immagine: l'elemento da solo. Seconda immagine: la zona di pagina dove sta, con l'elemento "
              "nel riquadro rosso.\n" + fatti + "\nL'elemento e' CONTENUTO o ARREDO?")
    t, pin, pout, dt, _ = chiedi(prompt, [f"{R}/_lavoro/raw/{v['file']}", f'{ctx}/{k}.png'],
                                 max_tokens=2000, temperature=0, system=SYSTEM, thinking=True, timeout=600)
    m = re.findall(r'RISPOSTA:\s*(CONTENUTO|ARREDO)', t)
    pred = 'contenuto' if m and m[-1] == 'CONTENUTO' else ('arredo' if m else 'nessuna')
    vero = 'arredo' if (k in cl['sfondo'] or k in cl['decorazione']) else 'contenuto'
    out.append(dict(xref=k, regola=dec[k], risposta=pred, vista=vero, secondi=dt, token_out=pout, testo=t))
    if pred != vero: err.append((k, dec[k], pred, vero, pout))
    print(k, pred, vero, dt, 's', pout, 'tok', flush=True)
json.dump(out, open(f'{R}/_lavoro/locale/prova_arredo_c.json', 'w'), indent=1, ensure_ascii=False)
print('in coda', len(coda), '| errori', len(err), '| secondi', round(sum(o['secondi'] for o in out), 1),
      '| token medi', round(sum(o['token_out'] or 0 for o in out) / len(out)))
for e in err: print('  errore:', e)
