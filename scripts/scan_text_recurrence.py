"""Quanto testo si ripete nello stesso punto, pagina dopo pagina.

Diagnostico. **Non reimplementa niente**: chiama
`document_text_recurrence_measurements.measure_document_text_recurrence` e
stampa. Su questo progetto due definizioni della stessa cosa sono gia' divergute,
e uno script che ricalcola per conto proprio e' il modo in cui succede.

Il modulo misura e non decide; questo script applica una frazione **passata dal
chiamante** per guardare i dati, e nessuna frazione e' raccomandata qui.

Uso::

    ./venv/bin/python scripts/scan_text_recurrence.py \\
        --pdf DIE.pdf --da 340 --pagine 60 --quota 0.25
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_text_recurrence_measurements import (  # noqa: E402
    POSITION_GRID,
    measure_document_text_recurrence,
    normalize_text,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def normalized_pages(pdf_path: Path, first: int, count: int):
    pages = []
    with fitz.open(pdf_path) as document:
        last = min(len(document), first + count)
        for index in range(first, last):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"page:{index:04d}",
                capture_id=f"recurrence:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--da", type=int, default=0, help="indice 0-based di partenza")
    parser.add_argument("--pagine", type=int, default=60)
    parser.add_argument("--quota", type=float, default=0.25)
    args = parser.parse_args()

    pages = normalized_pages(args.pdf, args.da, args.pagine)
    if not pages:
        print("nessuna pagina ammissibile", file=sys.stderr)
        raise SystemExit(1)

    measured = measure_document_text_recurrence(pages)
    ricorrenti = measured.occupied_on_at_least(args.quota)
    # I caratteri si ricontano sulle pagine, non si stimano dagli slot: uno
    # slot porta piu' testi e non sa quale stava su quale pagina.
    posizioni = {(slot.x, slot.y) for slot in ricorrenti}
    caratteri_totali = 0
    caratteri_ricorrenti = 0
    for page in pages:
        width = page.page_geometry.width
        height = page.page_geometry.height
        for primitive in page.text_primitives:
            lunghezza = len(normalize_text(primitive.text))
            if not lunghezza:
                continue
            caratteri_totali += lunghezza
            slot = (
                round(primitive.bbox[0] / width * POSITION_GRID),
                round(primitive.bbox[1] / height * POSITION_GRID),
            )
            if slot in posizioni:
                caratteri_ricorrenti += lunghezza

    print(f"{args.pdf.stem}: {measured.page_count} pagine, {len(measured.slots)} slot occupati")
    print(f"slot occupati su almeno il {args.quota:.0%} delle pagine: {len(ricorrenti)}")
    quota_car = caratteri_ricorrenti / caratteri_totali if caratteri_totali else 0.0
    print(
        f"caratteri negli slot ricorrenti: {caratteri_ricorrenti} su "
        f"{caratteri_totali} ({quota_car:.1%})"
    )
    print()
    print(f"{'quota':>6} {'x,y':>8} {'testi':>6}  esempio")
    for slot in sorted(ricorrenti, key=lambda s: -s.page_count):
        quota = slot.page_count / measured.page_count
        print(
            f"{quota:>6.0%} {slot.x:>3},{slot.y:<4} {len(slot.texts):>6}  {slot.texts[0][:52]!r}"
        )


if __name__ == "__main__":
    main()
