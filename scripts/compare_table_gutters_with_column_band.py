"""Confronto, tabella per tabella: i gutter trovati, quelli di `column_band`, l'edge_strip.

Tre domande su ogni pagina che sappiamo contenere una tabella:

1. quanti dei gutter della tabella `column_band` li vede gia';
2. quali gutter `column_band` riporta che la tabella NON adotta -- se ce n'e' uno
   dentro la regione, e' un confine di banda scavalcato;
3. se la regola `edge_strip` scatta, cioe' se un gutter lascia al bordo della
   pagina una colonna piu' stretta del minimo.

`column_band` viene interrogato attraverso il producer, non reimplementato.

Read-only. Uso:

    ./venv/bin/python scripts/compare_table_gutters_with_column_band.py \
        --pdf-dir . --pages DB:75 Lan:18
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from page_analysis_column_band import (  # noqa: E402
    _AVERAGE_CHAR_WIDTH_RATIO,
    _median_font_size,
    build_column_band_page_analysis_with_measurements,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototype_table_max_columns import analyse  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True)
    args = parser.parse_args()

    print(
        f"{'pagina':14s} {'col':>4s} {'gutter':>7s} {'conf':>5s} "
        f"{'banda-non-adottati':>19s} {'edge_strip':>11s}"
    )
    for spec in args.pages:
        name, raw = spec.split(":")
        index = int(raw)
        document = fitz.open(args.pdf_dir / f"{name}.pdf")
        page = document[index]
        capture = capture_pymupdf_page(
            page,
            source_id="compare",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"cmp:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)

        results = analyse(primitive_page)
        if not results:
            print(f"{name + ' pag' + str(index + 1):14s}   nessuna regione")
            continue
        result = results[0]
        gutters = result["gutters"]  # type: ignore[assignment]
        x0, _y0, x1, _y1 = result["bbox"]  # type: ignore[misc]

        _analysis, measures = build_column_band_page_analysis_with_measurements(
            primitive_page, generation_id="compare"
        )
        band = [interval for m in measures for interval in m.gutter_x_intervals]

        confirmed = sum(
            1 for a, b in gutters if any(a < d and b > c for c, d in band)
        )
        inside_not_taken = [
            (c, d)
            for c, d in band
            if c > x0 and d < x1 and not any(a < d and b > c for a, b in gutters)
        ]

        font_size = _median_font_size(list(primitive_page.text_primitives))
        minimum = 10.0 * font_size * _AVERAGE_CHAR_WIDTH_RATIO if font_size > 0 else 0.0
        width = primitive_page.page_geometry.width
        edge = 0
        if gutters and minimum > 0:
            if x0 <= 2.0 and gutters[0][0] - x0 < minimum:
                edge += 1
            if x1 >= width - 2.0 and x1 - gutters[-1][1] < minimum:
                edge += 1

        print(
            f"{name + ' pag' + str(index + 1):14s} {result['columns']:>4} "
            f"{len(gutters):>7} {confirmed:>5} "
            f"{len(inside_not_taken):>19} {edge:>11}"
            + (f"   <-- {[f'{c:.0f}-{d:.0f}' for c, d in inside_not_taken]}" if inside_not_taken else "")
        )


if __name__ == "__main__":
    main()
