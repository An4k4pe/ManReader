"""Materiale per il giudizio a vista del passo 2 (CRITERIO_UNA_COPPIA.md).

Ogni regione scheda che nasce con `min_coppie=1` e non contiene una
riga-verita' viene ritagliata dall'immagine della sua pagina e messa in un
foglio di provini numerato. Stessa catena di `confini_dal_riquadro.py`
(riquadri separati, tabelle escluse). Nessuna decisione: solo immagini, e un
elenco che le numera.

Uso:  python materiale_una_coppia.py <pdf> --verita X [--verita Y]
                                     --sigla dh --out <cartella>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import markdown_ir
import pdfplumber
import pila2
import pymupdf
import riquadri
from confini_dal_riquadro import _verita_di
from PIL import Image, ImageDraw

LARGHEZZA = 400      # pixel di un provino nel foglio
ALTEZZA_MAX = 520    # oltre, il provino si taglia in basso e lo dice
COLONNE = 3
PER_FOGLIO = 12
DPI = 100


def _schede(righe, record_righe_pi, firma_di, candidati, min_coppie):
    return [
        r
        for r in markdown_ir.regioni_di_pagina(
            righe, record_righe_pi, firma_di, candidati, min_coppie=min_coppie
        )
        if r["tipo"] == "scheda"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("--verita", action="append", required=True)
    parser.add_argument("--sigla", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    chiavi = [pila2.squash(v) for v in args.verita]
    cartella = Path(args.out)
    cartella.mkdir(parents=True, exist_ok=True)

    pagine, _schema, info, record = pila2.record_di(args.pdf)
    firma_di = {gi: firma for gi, _n, _prof, _strati, firma in info}
    record_righe: list[dict[int, int]] = [dict() for _ in pagine]
    for pi, ini, fine, gi in record:
        for i in range(ini, fine + 1):
            record_righe[pi].setdefault(i, gi)

    provini: list[tuple[str, Image.Image]] = []
    with pymupdf.open(args.pdf) as documento, pdfplumber.open(args.pdf) as plumber:
        for pi in range(len(pagine)):
            righe = pagine[pi]
            verita = _verita_di(righe, chiavi)
            candidati = riquadri.separa_riquadri(
                markdown_ir.candidati_di_pagina(documento, plumber, pi), righe
            )
            candidati = {**candidati, "tabelle": []}
            gia_note = {
                frozenset(r["righe"])
                for r in _schede(righe, record_righe[pi], firma_di, candidati, 2)
            }
            for regione in _schede(righe, record_righe[pi], firma_di, candidati, 1):
                if set(verita) & regione["righe"] or frozenset(regione["righe"]) in gia_note:
                    continue
                dentro = [righe[i] for i in sorted(regione["righe"])]
                rettangolo = pymupdf.Rect(
                    min(r["x0"] for r in dentro) - 6,
                    min(r["y0"] for r in dentro) - 6,
                    max(r["x1"] for r in dentro) + 6,
                    max(r["y1"] for r in dentro) + 6,
                ) & documento[pi].rect
                pix = documento[pi].get_pixmap(dpi=DPI, clip=rettangolo)
                immagine = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                numero = len(provini) + 1
                etichetta = f"{numero}. {args.sigla} idx {pi}, {len(dentro)} righe"
                print(f"{numero:3d}  idx {pi:3d}  {len(dentro):4d} righe  "
                      f"{pila2.clean(dentro[0]['testo'])[:60]!r}")
                provini.append((etichetta, immagine))

    for foglio in range(0, len(provini), PER_FOGLIO):
        gruppo = provini[foglio : foglio + PER_FOGLIO]
        scalati = []
        for etichetta, immagine in gruppo:
            fattore = LARGHEZZA / immagine.width
            alta = round(immagine.height * fattore)
            immagine = immagine.resize((LARGHEZZA, alta))
            if alta > ALTEZZA_MAX:
                immagine = immagine.crop((0, 0, LARGHEZZA, ALTEZZA_MAX))
                etichetta += " (tagliato)"
            scalati.append((etichetta, immagine))
        righe_foglio = (len(scalati) + COLONNE - 1) // COLONNE
        alte = [
            max(im.height for _e, im in scalati[r * COLONNE : (r + 1) * COLONNE])
            for r in range(righe_foglio)
        ]
        tela = Image.new(
            "RGB", (COLONNE * (LARGHEZZA + 12) + 12, sum(alte) + righe_foglio * 34 + 12), "white"
        )
        disegno = ImageDraw.Draw(tela)
        y = 12
        for r in range(righe_foglio):
            for c, (etichetta, immagine) in enumerate(scalati[r * COLONNE : (r + 1) * COLONNE]):
                x = 12 + c * (LARGHEZZA + 12)
                disegno.text((x, y), etichetta, fill="black")
                tela.paste(immagine, (x, y + 18))
                disegno.rectangle(
                    (x - 1, y + 17, x + immagine.width, y + 18 + immagine.height), outline="red"
                )
            y += alte[r] + 34
        destinazione = cartella / f"provini_{args.sigla}_{foglio // PER_FOGLIO + 1}.png"
        tela.save(destinazione)
        print(f"foglio: {destinazione}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
