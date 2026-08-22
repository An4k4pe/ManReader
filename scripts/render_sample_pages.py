"""Render **nudo** delle pagine di un campione, per l'etichettatura a vista.

Nudo e' il punto: niente candidati, niente bande, niente gutter. Chi etichetta
deve dire che cos'e' un frammento **sulla pagina** -- un titolo, meta' di una
coppia etichetta:valore, arredo -- e un overlay che mostri gia' cosa ha deciso
un meccanismo e' esattamente il suggerimento che il protocollo di
`Criterio_FormaMancante_v3.md` §4 cerca di tenere fuori. Per vedere i candidati
esiste `scripts/render_wired_producers.py`, che serve a un'altra domanda.

Il nome del file porta **entrambe** le numerazioni che questo progetto tiene
separate -- ``<M>_pagina{1-based}_idx{0-based}.png`` -- perche' un giro di
etichette e' gia' andato perso su uno scorrimento di uno fra la colonna ``idx``
e il numero di pagina del lettore PDF. Il numero **stampato** sulla carta e' una
terza cosa ancora, non verificata, e non compare qui.

Uso::

    ./venv/bin/python scripts/render_sample_pages.py \\
        --pdf-dir . --outdir <dir> --pages Wil:244 DrW:227 ...
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz

DEFAULT_DPI = 150


def render_page(document: fitz.Document, index: int, dpi: int) -> bytes:
    page = document[index]
    pixmap = page.get_pixmap(dpi=dpi)
    return pixmap.tobytes("png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--pages",
        nargs="+",
        required=True,
        help="Nome:idx0based, per esempio Wil:244",
    )
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    documents: dict[str, fitz.Document] = {}

    for token in args.pages:
        name, _, raw_index = token.partition(":")
        index = int(raw_index)
        if name not in documents:
            documents[name] = fitz.open(args.pdf_dir / f"{name}.pdf")
        document = documents[name]
        if not 0 <= index < len(document):
            print(f"FUORI INTERVALLO: {name} idx={index} (pagine {len(document)})")
            continue
        out = args.outdir / f"{name}_pagina{index + 1:04d}_idx{index:04d}.png"
        out.write_bytes(render_page(document, index, args.dpi))
        print(f"{out.name}")


if __name__ == "__main__":
    main()
