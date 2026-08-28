"""Le dimensioni di prosa di un manuale, e i candidati titolo. Misura, non decide.

`Criterio_Titoli_v2.md`, aggiornato alla regola di quel criterio nello stesso
commit che la implementa.

Riporta per ogni manuale **quali dimensioni sono prosa** -- quelle le cui righe
sono lunghe, separate dal salto piu' grande fra le mediane -- e quante righe
starebbero sopra tutte.

**La v1 di questo script diceva un'altra cosa, ed era sbagliata**: assumeva UNA
dimensione di corpo, la piu' frequente, e attribuiva la sovrapproduzione alle
schede mostro. Misurato: su Kul 8,0 e 10,0 sono entrambe prosa, e i 67 candidati
a 10,0 erano prosa scambiata per titolo. Con la prosa presa per intero i candidati
passano da 88 a 21 e sugli altri tredici manuali non cambia niente.

Uso::

    ./venv/bin/python scripts/measure_heading_candidates.py --pdf-dir . --esempi
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_heading_measurements import measure_font_sizes, sized_lines  # noqa: E402
from document_heading_policy import (  # noqa: E402
    MAX_LINES_IN_A_HEADING_BLOCK,
    SIZE_EPSILON,
    heading_levels,
    prose_sizes,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION = re.compile(r"^text:(b\d+):(l\d+):s\d+$")
MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag", "DrM", "DrW",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)



def scan(pdf_path: Path, window: int) -> tuple[frozenset[float], list[tuple[str, int]]]:
    pages = []
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
            pages.append(normalize_backend_page_capture(capture))
    if not pages:
        return (frozenset(), [])

    measurements = measure_font_sizes(pages)
    prose = prose_sizes(measurements)
    levels = heading_levels(measurements, prose)
    if not prose:
        return (prose, [])
    limit = max(prose)

    found: list[tuple[str, int]] = []
    for page in pages:
        by_block: dict[str, list] = defaultdict(list)
        for line in sized_lines(page):
            by_block[line.block].append(line)
        for block_lines in by_block.values():
            if len(block_lines) > MAX_LINES_IN_A_HEADING_BLOCK:
                continue
            if any(line.size in prose for line in block_lines):
                continue
            found.extend(
                (line.text, levels[line.size])
                for line in block_lines
                if line.size > limit + SIZE_EPSILON and len(line.text) > 1
                and line.size in levels
            )
    return (prose, found)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=10)
    parser.add_argument("--esempi", action="store_true")
    args = parser.parse_args()

    print(f"finestra {args.pagine} pagine contigue a meta' manuale")
    print("NOTA: l'arredo non e' escluso, quindi i numeri di pagina compaiono.\n")
    print(f"{'manuale':8} {'prosa':>22} {'candidati':>10}  esempi")
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        prose, found = scan(path, args.pagine)
        if not prose:
            continue
        shown = "; ".join(f"h{level} {text}" for text, level in found[:2])[:44] if args.esempi else ""
        print(f"{name:8} {str(sorted(prose))[:21]:>22} {len(found):>10}  {shown}")
    print("\nLa dispersione per manuale e' un obbligo di riporto del §4.B:")
    print("una media nasconderebbe un manuale che ne produce dieci volte un altro.")


if __name__ == "__main__":
    main()
