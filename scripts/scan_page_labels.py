"""Le etichette di pagina dichiarate dal PDF, e se compaiono nel testo.

Diagnostico, e produce i due numeri che `Criterio_ArredoRicorrente_v3.md` §1
cita: quanti manuali dichiarano `/PageLabels`, e quante volte l'etichetta
dichiarata compare come testo nella fascia bassa della pagina.

**Il metodo c'e' sempre, i dati no.** ``page.get_label()`` esiste su ogni
documento, ma torna stringa vuota quando il PDF non dichiara ``/PageLabels`` nel
catalogo: PyMuPDF **non sintetizza** il numero fisico, riporta cio' che il
documento dichiara. Per questo l'etichetta e' un fatto e non un'euristica, e la
sua assenza e' essa stessa un'informazione.

Verificato sul catalogo: Wil non ha ``/PageLabels``
(``<</Type/Catalog/Lang/Metadata/Names/Outlines/Pages/ViewerPreferences>>``),
DIE ne ha due regole -- numeri romani dalla pagina 0, decimali dalla 12.

**Il contenimento e non l'uguaglianza**, con un margine di tre caratteri: Lan
stampa ``[99]`` per l'etichetta ``99``. Il margine e' l'unico numero di questo
ramo, ed e' li' per quella ragione.

Uso::

    ./venv/bin/python scripts/scan_page_labels.py --pdf-dir . --pagine 40
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz

MANUALS = (
    "Apo", "BiD", "BoB", "Dag", "DB", "DIE", "DrM", "DrW",
    "Fab", "FW", "FWK", "Kul", "Lan", "SV", "Vil", "Wil",
)
BOTTOM_BAND = 0.90
LABEL_SLACK = 3


def label_in_bottom_text(page: fitz.Page, label: str) -> bool:
    """L'etichetta compare, contenuta, in un testo corto in fondo alla pagina."""

    height = page.rect.height
    for block in page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if (
                    span["bbox"][1] > height * BOTTOM_BAND
                    and label in text
                    and len(text) <= len(label) + LABEL_SLACK
                ):
                    return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=40, help="pagine campionate per manuale")
    args = parser.parse_args()

    con_etichette = 0
    print(f"{'manuale':<8} {'pagine':>7} {'regole':>7} {'etichetta in fondo':>20}")
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"{name:<8} MANCANTE")
            continue
        with fitz.open(path) as document:
            rules = document.get_page_labels()
            if not rules:
                print(f"{name:<8} {len(document):>7} {'nessuna':>7} {'-':>20}")
                continue
            con_etichette += 1
            first = max(0, len(document) // 2 - args.pagine // 2)
            found = examined = 0
            for index in range(first, min(len(document), first + args.pagine)):
                page = document[index]
                if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                    continue
                label = (page.get_label() or "").strip()
                if not label:
                    continue
                examined += 1
                found += label_in_bottom_text(page, label)
            share = f"{found}/{examined}" if examined else "n/d"
            print(f"{name:<8} {len(document):>7} {len(rules):>7} {share:>20}")

    print(f"\nmanuali che dichiarano /PageLabels: {con_etichette} su {len(MANUALS)}")


if __name__ == "__main__":
    main()
