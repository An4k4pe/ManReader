"""Dove finisce una scheda e comincia la prosa. Esplorazione.

Domanda dell'utente, 14 settembre 2026: la struttura si ripete, poi c'e' una
parte libera; ogni ripetizione apre una scheda nuova; «rimane da capire se
capisce la fine di una scheda e l'inizio della prosa».

Una scheda seguita da un'altra sulla stessa pagina ha la fine data: la riga prima
del nome della successiva. L'ultima della pagina no. Senza soglie:

- **stile di scheda**: uno stile le cui righe, su tutto il documento, stanno in
  maggioranza dentro schede **delimitate** (seguite da un'altra scheda);
- l'ultima scheda della pagina continua dopo l'ultima riga con etichette finche'
  le righe sono in uno stile di scheda, e si ferma alla prima che non lo e'.

Riporta per ogni manuale le righe aggiunte e, per un campione, l'ultima riga presa
e la prima lasciata fuori.

Uso:  python fine_scheda.py <pdf> <sigla> [--da N --a N] [--processi 6]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from multiprocessing import get_context
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import fitz  # noqa: E402
import pdfplumber  # noqa: E402
from prototype_ir2_page import capture_document, stat_block_line_facts_of_page  # noqa: E402

from stat_block_regions import repeated_structures, stat_blocks_from_structures  # noqa: E402

_PDF = ""
_HANDLES = None


def _open() -> None:
    global _HANDLES
    _HANDLES = (fitz.open(_PDF), pdfplumber.open(_PDF))


def _page(index: int):
    document, plumber = _HANDLES  # type: ignore[misc]
    try:
        return index, stat_block_line_facts_of_page(document, plumber, index)
    except SystemExit:
        return index, ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("sigla")
    parser.add_argument("--da", type=int, default=0)
    parser.add_argument("--a", type=int, default=10**6)
    parser.add_argument("--processi", type=int, default=6)
    args = parser.parse_args(argv)

    global _PDF
    _PDF = args.pdf
    with fitz.open(args.pdf) as document:
        pages = sorted(capture_document(document).pages)
    with get_context("fork").Pool(args.processi, initializer=_open) as pool:
        data = dict(pool.map(_page, pages, chunksize=1))
    structures = repeated_structures(data)
    blocks = {index: stat_blocks_from_structures(data[index], structures) for index in pages}

    inside: Counter[object] = Counter()
    total: Counter[object] = Counter()
    for index in pages:
        lines = data[index]
        for facts in lines:
            if facts.style is not None:
                total[facts.style] += 1
        for position, block in enumerate(blocks[index]):
            if position + 1 >= len(blocks[index]):
                continue
            for line in block.line_indices:
                if lines[line].style is not None:
                    inside[lines[line].style] += 1
    block_styles = {style for style, count in inside.items() if count * 2 > total[style]}

    added = 0
    stops: Counter[str] = Counter()
    examples = []
    for index in pages:
        if not args.da <= index <= args.a or not blocks[index]:
            continue
        lines = data[index]
        last = blocks[index][-1]
        end = last.line_indices[-1]
        position = end + 1
        while position < len(lines) and (lines[position].style is None or lines[position].style in block_styles):
            position += 1
        added += position - end - 1
        stop = lines[position].text[:50] if position < len(lines) else "(fine pagina)"
        stops["fine pagina" if position >= len(lines) else "prosa o altro"] += 1
        if len(examples) < 14:
            taken = next(
                (lines[p].text[:40] for p in range(position - 1, end, -1) if lines[p].text), "(niente)"
            )
            examples.append((index, lines[last.name_line_indices[0]].text[:24] if last.name_line_indices else "", taken, stop))
    print(f"{args.sigla}: stili di scheda {len(block_styles)}, righe aggiunte alle ultime schede {added}, arresti {dict(stops)}")
    for index, name, taken, stop in examples:
        print(f"   idx {index:3d} {name!r:26s} ultima presa {taken!r:42s} | fuori {stop!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
