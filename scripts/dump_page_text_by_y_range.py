"""Dump diretto del testo di una pagina, filtrato per fascia y, ordinato per
(y0, x0) -- per leggere COSA c'e' davvero in una banda che i dati aggregati
(`all_bands_*.csv`) descrivono solo per coordinate. Nessuna aggregazione,
nessuna soglia: solo primitive di testo con il loro contenuto.

Motivo per cui esiste: `inspect_column_band_straddle_groups.py` dumpa solo i
casi di straddle (qui zero) -- non e' un dump generico del contenuto di una
banda. Serve per Fab.pdf p.264 (posizione, non stampata): i vecchi dati
(`all_bands_fab.csv`) descrivono una banda a 2 colonne per 10 righe
consecutive (y 99.7-283.8), ma il render della pagina mostra un elenco di 6
passaggi numerati con icona -- contenuto sparso, non 10 righe dense a doppia
colonna. Prima di ipotizzare una spiegazione, si legge il testo vero.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/dump_page_text_by_y_range.py Fab.pdf --page 264 --y-range 99.7,283.8 --output /tmp/text_fab_p264_band.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--page", type=int, required=True, help="1-indexed page number (posizionale)."
    )
    parser.add_argument(
        "--y-range",
        type=str,
        default=None,
        help="Y0,Y1 opzionale per filtrare. Default: tutta la pagina.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    y_range: tuple[float, float] | None = None
    if args.y_range is not None:
        parts = args.y_range.split(",")
        if len(parts) != 2:
            print("--y-range deve essere Y0,Y1", file=sys.stderr)
            return 1
        y_range = (float(parts[0]), float(parts[1]))

    page_index = args.page - 1
    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        if page_index < 0 or page_index >= document.page_count:
            print(f"page out of range: {args.page}", file=sys.stderr)
            return 1
        page = document.load_page(page_index)
        print(
            f"{pdf_path.name}: pagina posizionale {args.page} "
            f"(piè di pagina non controllato da questo script, verificare a parte)",
            file=sys.stderr,
            flush=True,
        )
        raw = page.get_text("dict")
        for block_index, block in enumerate(raw["blocks"]):
            if block.get("type") != 0:
                continue
            for line_index, line in enumerate(block["lines"]):
                for span_index, span in enumerate(line["spans"]):
                    x0, y0, x1, y1 = span["bbox"]
                    if y_range is not None and not (y_range[0] <= y0 <= y_range[1]):
                        continue
                    rows.append(
                        {
                            "manual": pdf_path.name,
                            "page": args.page,
                            "block": block_index,
                            "line": line_index,
                            "span": span_index,
                            "x0": round(x0, 1),
                            "y0": round(y0, 1),
                            "x1": round(x1, 1),
                            "y1": round(y1, 1),
                            "text": span["text"],
                        }
                    )

    rows.sort(key=lambda r: (cast(float, r["y0"]), cast(float, r["x0"])))

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    fieldnames = ("manual", "page", "block", "line", "span", "x0", "y0", "x1", "y1", "text")
    writer = csv.writer(handle)
    writer.writerow(fieldnames)
    for row in rows:
        writer.writerow([row[name] for name in fieldnames])


if __name__ == "__main__":
    raise SystemExit(main())
