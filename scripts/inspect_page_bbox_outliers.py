"""Ispezione minima, solo PyMuPDF (nessun import dal repo, nessun
pdfplumber): elenca ogni primitiva di testo/immagine/disegno di una pagina la
cui bbox esce significativamente dai limiti pagina, o e' anormalmente grande.

Motivo per cui esiste: il tentativo di misurare l'overlap column_band/
table_candidate su Fab.pdf p.2 (v10 Sec.11.3) si e' bloccato dentro
``pdfplumber.find_tables``. Fab.pdf p.2 e' la STESSA pagina gia' citata in
v9/v10 Sec.11.4 come sede di due casi con coordinate anomale
(``group_x0`` negativo, mai spiegati). Ipotesi non verificata, da falsificare
con questo script prima di continuare a indagare lo stallo: se quella pagina
contiene una bbox estrema (molto fuori pagina, o enormemente piu' larga/alta
del normale), l'algoritmo di allineamento a griglia di pdfplumber
(``vertical_strategy="text"``) puo' costruire una griglia interna
proporzionale a quell'estremo e diventare molto lento o restare bloccato --
spiegazione meccanica sia dello stallo sia, potenzialmente, dei due casi mai
spiegati.

Non tocca pdfplumber, non tocca il repo, solo ``fitz.Page.get_text("dict")``
e ``get_drawings()`` diretti -- veloce anche su pagine dove find_tables si
blocca, perche' non fa alcuna analisi di allineamento.

Uso:

    python3 scripts/inspect_page_bbox_outliers.py Fab.pdf --page 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import fitz

_DEFAULT_MARGIN = 20.0  # pt oltre il bordo pagina prima di segnalare come outlier
_DEFAULT_SIZE_FACTOR = 3.0  # multiplo della diagonale pagina prima di segnalare


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="1-indexed page number.")
    parser.add_argument("--margin", type=float, default=_DEFAULT_MARGIN)
    parser.add_argument("--size-factor", type=float, default=_DEFAULT_SIZE_FACTOR)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    with fitz.open(pdf_path) as document:
        page_index = args.page - 1
        if page_index < 0 or page_index >= document.page_count:
            print(f"page out of range: {args.page}", file=sys.stderr)
            return 1
        page = document.load_page(page_index)
        pw, ph = page.rect.width, page.rect.height
        diagonal = (pw**2 + ph**2) ** 0.5
        print(
            f"page {args.page}: width={pw:.1f} height={ph:.1f} "
            f"rotation={page.rotation} mediabox={tuple(page.mediabox)} "
            f"cropbox={tuple(page.cropbox)}",
        )

        outliers_found = 0

        # text spans
        raw = page.get_text("dict")
        for block_index, block in enumerate(raw["blocks"]):
            if block.get("type") != 0:
                continue
            for line_index, line in enumerate(block["lines"]):
                for span_index, span in enumerate(line["spans"]):
                    x0, y0, x1, y1 = span["bbox"]
                    outside = (
                        x0 < -args.margin
                        or y0 < -args.margin
                        or x1 > pw + args.margin
                        or y1 > ph + args.margin
                    )
                    width, height = x1 - x0, y1 - y0
                    oversized = max(width, height) > diagonal * args.size_factor
                    if outside or oversized:
                        outliers_found += 1
                        print(
                            f"  TEXT b{block_index:04d}l{line_index:04d}s{span_index:04d} "
                            f"bbox=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) "
                            f"outside_page={outside} oversized={oversized} "
                            f"text={span['text'][:40]!r}"
                        )

        # raster images
        for image_index, image in enumerate(page.get_image_info()):
            x0, y0, x1, y1 = image["bbox"]
            outside = (
                x0 < -args.margin
                or y0 < -args.margin
                or x1 > pw + args.margin
                or y1 > ph + args.margin
            )
            width, height = x1 - x0, y1 - y0
            oversized = max(width, height) > diagonal * args.size_factor
            if outside or oversized:
                outliers_found += 1
                print(
                    f"  IMAGE #{image_index} bbox=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) "
                    f"outside_page={outside} oversized={oversized}"
                )

        # vector drawings
        for drawing_index, drawing in enumerate(page.get_drawings()):
            rect = drawing.get("rect")
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            outside = (
                x0 < -args.margin
                or y0 < -args.margin
                or x1 > pw + args.margin
                or y1 > ph + args.margin
            )
            width, height = x1 - x0, y1 - y0
            oversized = max(width, height) > diagonal * args.size_factor
            if outside or oversized:
                outliers_found += 1
                print(
                    f"  DRAWING #{drawing_index} rect=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) "
                    f"outside_page={outside} oversized={oversized}"
                )

        print(f"\n{outliers_found} outlier(s) found on page {args.page} of {pdf_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
