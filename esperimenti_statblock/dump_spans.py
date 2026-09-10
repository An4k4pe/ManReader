"""Estrae da un PDF SOLO cio' che serve al rilevatore: testo, font, dimensione,
colore e riquadro di ogni span. Nessuna immagine, nessun font incorporato.

Uso:   python3 dump_spans.py manuale.pdf manuale.spans.json.gz
       (opzionale)  --da 30 --a 60     per limitarsi a un intervallo di pagine

Il file prodotto e' l'ingresso alternativo al PDF: contiene il testo del
manuale, quindi vale come il manuale ai fini dei diritti — non va committato
ne' pubblicato, esattamente come i PDF di benchmark.
"""
from __future__ import annotations
import argparse, gzip, json
import pymupdf

ap = argparse.ArgumentParser()
ap.add_argument("pdf"); ap.add_argument("out")
ap.add_argument("--da", type=int, default=0)
ap.add_argument("--a", type=int, default=10**9)
a = ap.parse_args()

doc = pymupdf.open(a.pdf)
pagine = []
for i, p in enumerate(doc):
    if not (a.da <= i <= a.a):
        pagine.append([]); continue
    righe = []
    for blk in p.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp: continue
            # NIENTE arrotondamento: arrotondare a 2 decimali ribalta l'ordine
            # di righe quasi complanari e il dump smette di essere equivalente
            # al PDF (misurato: 4 righe su 3174 invertite).
            righe.append([
                ln["bbox"][1], ln["bbox"][0],
                [[s["text"], s["font"].split("+")[-1], round(s["size"], 1), s["color"]]
                 for s in sp],
            ])
    pagine.append(righe)

with gzip.open(a.out, "wt", encoding="utf-8") as f:
    json.dump({"v": 1, "pagine": pagine}, f, ensure_ascii=False, separators=(",", ":"))
print(f"pagine: {len(pagine)}  righe: {sum(len(x) for x in pagine)}")
