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
stampa ``[99]`` per l'etichetta ``99``.

**Nessun vincolo di posizione**, ed e' una correzione a verbale. Una prima
versione cercava solo nella fascia bassa e concludeva che BoB e Kul non
stampassero il numero: falso, **BoB lo mette sul lato destro in alto**
(``x=0,91 y=0,18``) e **Kul in cima** (``x=0,25 y=0,04``). La guardia contro la
coincidenza -- su una pagina numerata ``6`` un ``6`` nel corpo combacia -- non e'
la posizione ma la **ricorrenza dello slot**: lo stesso punto che porta
l'etichetta della propria pagina su un quarto delle pagine, ciascuna con la sua.

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
LABEL_SLACK = 3
POSITION_GRID = 100
MIN_SHARE = 0.25


def label_slots(page: fitz.Page, label: str) -> set[tuple[int, int]]:
    """Gli slot in cui compare l'etichetta della pagina, ovunque essa sia."""

    width, height = page.rect.width, page.rect.height
    found: set[tuple[int, int]] = set()
    for block in page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if label in text and len(text) <= len(label) + LABEL_SLACK:
                    found.add(
                        (
                            round(span["bbox"][0] / width * POSITION_GRID),
                            round(span["bbox"][1] / height * POSITION_GRID),
                        )
                    )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=40, help="pagine campionate per manuale")
    args = parser.parse_args()

    con_etichette = 0
    print(f"{'manuale':<8} {'pagine':>7} {'regole':>7} {'slot':>7}  dove")
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"{name:<8} MANCANTE")
            continue
        with fitz.open(path) as document:
            rules = document.get_page_labels()
            if not rules:
                print(f"{name:<8} {len(document):>7} {'nessuna':>7} {'-':>7}")
                continue
            con_etichette += 1
            first = max(0, len(document) // 2 - args.pagine // 2)
            hits: dict[tuple[int, int], int] = {}
            examined = 0
            for index in range(first, min(len(document), first + args.pagine)):
                page = document[index]
                if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                    continue
                label = (page.get_label() or "").strip()
                if not label:
                    continue
                examined += 1
                for slot in label_slots(page, label):
                    hits[slot] = hits.get(slot, 0) + 1
            good = [(slot, n) for slot, n in hits.items() if n >= examined * MIN_SHARE]
            where = ", ".join(f"x{slot[0]}/y{slot[1]}" for slot, _ in sorted(good)[:2])
            print(f"{name:<8} {len(document):>7} {len(rules):>7} {len(good):>7}  {where}")

    print(f"\nmanuali che dichiarano /PageLabels: {con_etichette} su {len(MANUALS)}")


if __name__ == "__main__":
    main()
