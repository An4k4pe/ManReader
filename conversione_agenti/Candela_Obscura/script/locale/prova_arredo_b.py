"""Prova 2b (ridisegnata dopo il fallimento della 2): stessa coda e stesso criterio,
ma il modello vede la zona di pagina attorno all'elemento con un riquadro rosso,
e il prompt dice la sua dimensione rispetto al corpo del testo.
"""
import json, os, fitz
from PIL import Image, ImageDraw
from client import chiedi
R = '../..'
PDF = "/home/an4k4pe/Documenti/KDrive/ManualiGdr/Candela Obscura - DP - Core Rulebook (OEF, 2023-11).pdf"
d = fitz.open(PDF)
dec = json.load(open(f'{R}/_lavoro/v2/classi_auto.json'))
M = json.load(open(f'{R}/_lavoro/v2/misure_asset.json')); mis = M['assets']; body = M['body']
inv = json.load(open(f'{R}/_lavoro/raw/inventario.json'))
cl = json.load(open(f'{R}/script/classi_immagini.json'))
tmp = f'{R}/_lavoro/locale/ctx'; os.makedirs(tmp, exist_ok=True)
coda = [k for k, v in dec.items() if v in ('carta', 'segno', 'listello')]

def contesto(k):
    occ = next(i for i in inv if str(i['xref']) == k)
    p = d[occ['page'] - 1]; r = fitz.Rect(occ['bbox']) & p.rect
    clip = fitz.Rect(r.x0 - 120, r.y0 - 120, r.x1 + 120, r.y1 + 120) & p.rect
    pix = p.get_pixmap(dpi=100, clip=clip); f = f'{tmp}/{k}.png'; pix.save(f)
    im = Image.open(f).convert('RGB'); s = 100 / 72
    ImageDraw.Draw(im).rectangle([(r.x0 - clip.x0) * s, (r.y0 - clip.y0) * s, (r.x1 - clip.x0) * s, (r.y1 - clip.y0) * s], outline=(255, 0, 0), width=3)
    im.save(f); return f, r

out, err = [], []
for k in sorted(coda, key=int):
    f, r = contesto(k)
    prompt = (f"Questa e' una zona di una pagina di un manuale di gioco di ruolo. L'elemento nel riquadro rosso "
              f"e' largo {r.width:.0f} pt e alto {r.height:.0f} pt; il testo del manuale e' composto a {body:.0f} pt.\n"
              "Che cos'e' l'elemento nel riquadro rosso?\n"
              "A) un contenuto: illustrazione, documento, mappa, emblema che il testo presenta o commenta\n"
              "B) carta o texture di sfondo su cui sta il testo\n"
              "C) segno decorativo: sigillo o scarabocchio a margine, filetto, macchia d'inchiostro\n"
              "Rispondi solo con la lettera.")
    t, pin, pout, dt, _ = chiedi(prompt, [f], max_tokens=5, temperature=0)
    vero = 'arredo' if (k in cl['sfondo'] or k in cl['decorazione']) else 'contenuto'
    pred = 'contenuto' if t.strip()[:1].upper() == 'A' else 'arredo'
    out.append(dict(xref=k, regola=dec[k], risposta=t, vista=vero, secondi=dt))
    if pred != vero: err.append((k, dec[k], t, vero))
json.dump(out, open(f'{R}/_lavoro/locale/prova_arredo_b.json', 'w'), indent=1)
print('in coda', len(coda), '| errori', len(err), '| secondi', round(sum(o['secondi'] for o in out), 1))
for e in err: print('  errore:', e)
for k in ('5349', '9694', '8936'):
    print(' ', k, [x['risposta'] for x in out if x['xref'] == k])
