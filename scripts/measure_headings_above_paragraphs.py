"""Quante righe aggiunge il secondo ramo dei titoli, e quali.

`Criterio_TitoloSopraIlParagrafo_v1.md` §3 e §4.C. Misura, non decide.

Riporta per ogni manuale:

- **dimensione**: i titoli che il ramo per dimensione trova, prima e dopo la
  modifica -- devono essere identici, ed e' la barra §4.C;
- **sopra il paragrafo**: le righe che il ramo nuovo aggiunge.

Uso::

    ./venv/bin/python scripts/measure_headings_above_paragraphs.py --pdf-dir . --esempi
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_heading_measurements import measure_font_sizes, sized_lines  # noqa: E402
from document_heading_policy import (  # noqa: E402
    heading_lines,
    headings_above_a_paragraph,
    merge_wrapped,
    prose_sizes,
    sizes_that_carry_headings,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag", "DrM", "DrW",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)
# Dichiarati fuori dalla popolazione in `Criterio_Titoli_v3.md` §3, e per la
# stessa ragione: il loro corpo misurato e' il testo di scheda.
OUTSIDE = ("DrM", "DrW")


def scan(pdf_path: Path, window: int) -> tuple[int, int, list[tuple[int, str]]]:
    pages: list = []
    indices: list[int] = []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="headings",
                page_id=f"page:{index:04d}",
                capture_id=f"headings:{index:04d}",
            )
            indices.append(index)
            pages.append(normalize_backend_page_capture(capture))
    if not pages:
        return (0, 0, [])

    measurements = measure_font_sizes(pages)
    prose = prose_sizes(measurements)
    carried = sizes_that_carry_headings([sized_lines(page) for page in pages], measurements, prose)
    levels = heading_levels_for(measurements, prose, carried)

    by_size_alone = 0
    by_size_with_breaks = 0
    added: list[tuple[int, str]] = []
    for index, page in zip(indices, pages, strict=True):
        lines = sized_lines(page)
        above = headings_above_a_paragraph(lines, levels)
        merged_alone, _ = merge_wrapped(lines)
        by_size_alone += len(heading_lines(merged_alone, prose, levels))
        breaks = frozenset(
            position for found in above for position in (found, found + 1) if position < len(lines)
        )
        merged_broken, _ = merge_wrapped(lines, breaks)
        by_size_with_breaks += len(heading_lines(merged_broken, prose, levels))
        added.extend((index, lines[position].text) for position in sorted(above))
    return (by_size_alone, by_size_with_breaks, added)


def heading_levels_for(measurements, prose, carried) -> dict[float, int]:
    from document_heading_policy import heading_levels

    return heading_levels(measurements, prose, carried)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, default=Path("."))
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--esempi", action="store_true")
    arguments = parser.parse_args()

    print(f"{'manuale':<8} {'dim.prima':>10} {'dim.dopo':>9} {'aggiunte':>9}")
    total = 0
    for name in MANUALS:
        pdf = arguments.pdf_dir / f"{name}.pdf"
        if not pdf.is_file():
            continue
        before, after, added = scan(pdf, arguments.window)
        mark = "" if before == after else "   ← REGRESSIONE"
        note = "  (fuori campione)" if name in OUTSIDE else ""
        print(f"{name:<8} {before:>10} {after:>9} {len(added):>9}{mark}{note}")
        if name not in OUTSIDE:
            total += len(added)
        if arguments.esempi:
            for index, text in added[:6]:
                print(f"         idx{index:<5} {text[:72]}")
    print(f"\naggiunte dentro la popolazione campionabile: {total}")


if __name__ == "__main__":
    main()
