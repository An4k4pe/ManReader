"""Quale strategia di tabella taglia meno il testo della sorgente.

Implementa `Criterio_StrategiaTabella_v1.md`, committato prima di questa misura,
e nient'altro. Il seed e le esclusioni stanno nel criterio.

La qualita' misurata NON e' «quante tabelle trova». Il disegno concordato prende
da pdfplumber la geometria della griglia e il testo dalla sorgente, quindi cio'
che conta e' che i confini di colonna non cadano dentro uno span -- il difetto
osservato, dove `Ferocia` perde la F e diventa `['rocia: 2 Taglia:', 'ormale']`.

Read-only, nessuna scrittura.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

SEED = "20260821"
SAMPLE_SIZE = 12
RESOLVED_FILL_RATIO = 0.80

MANUALS = (
    "Apo", "BiD", "BoB", "Dag", "DB", "DIE", "DrM", "DrW",
    "Fab", "FW", "FWK", "Kul", "Lan", "SV", "Vil", "Wil",
)

# Pagine gia' usate in sessione, escluse per costruzione (indici 0-based).
USED_PAGES = frozenset({
    ("DB", 89), ("DB", 98), ("DrM", 86), ("Vil", 222),
    ("DB", 52), ("DB", 49), ("DB", 17), ("Dag", 163), ("Dag", 83), ("DrW", 96),
})

STRATEGIES = {
    "lines/lines": {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
    "text/lines (producer)": {"vertical_strategy": "text", "horizontal_strategy": "lines"},
    "lines_strict": {"vertical_strategy": "lines_strict", "horizontal_strategy": "lines_strict"},
    "text/text": {"vertical_strategy": "text", "horizontal_strategy": "text"},
}


def _measure_strategy(table_finder, spans) -> tuple[int, int, int, int]:
    """Return (found, resolved, cut_spans, considered_spans) for one strategy."""

    found = 0
    resolved = 0
    cut = 0
    considered = 0
    for table in table_finder:
        found += 1
        cells = [cell for row in table.extract() for cell in row]
        filled = sum(1 for cell in cells if cell and cell.strip())
        if cells and filled / len(cells) >= RESOLVED_FILL_RATIO:
            resolved += 1

        boundaries = sorted(
            {cell[0] for cell in table.cells if cell} | {cell[2] for cell in table.cells if cell}
        )
        x0, y0, x1, y1 = table.bbox
        for span in spans:
            sx0, sy0, sx1, sy1 = span.bbox
            if sx1 <= x0 or sx0 >= x1 or sy1 <= y0 or sy0 >= y1:
                continue
            considered += 1
            if any(sx0 + 0.5 < boundary < sx1 - 0.5 for boundary in boundaries):
                cut += 1
    return found, resolved, cut, considered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    args = parser.parse_args()

    documents = {}
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        documents[name] = (fitz.open(path), pdfplumber.open(path))

    pool = [
        (name, index)
        for name in documents
        for index in range(len(documents[name][0]))
        if (name, index) not in USED_PAGES
    ]
    rng = random.Random()
    rng.seed(SEED)
    sample = rng.sample(pool, SAMPLE_SIZE)
    print(f"seed {SEED} — campione: {sorted(sample)}\n")

    totals = {label: [0, 0, 0, 0] for label in STRATEGIES}
    per_page = []

    for name, index in sample:
        fitz_document, plumber_document = documents[name]
        page = fitz_document[index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            print(f"  SKIP {name} idx={index}: guardia pagina")
            continue
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"strategies:page:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        spans = [p for p in primitive_page.text_primitives if p.text.strip()]

        row: dict[str, object] = {"page": f"{name} idx {index}"}
        for label, settings in STRATEGIES.items():
            tables = plumber_document.pages[index].find_tables(table_settings=settings)
            result = _measure_strategy(tables, spans)
            row[label] = result
            for slot, value in enumerate(result):
                totals[label][slot] += value
        per_page.append(row)

    print(f"{'pagina':16s} {'lines tag/ris':>15s} {'producer tag/ris':>18s}   verdetto")
    dominates = 0
    useful = 0
    for row in per_page:
        lines_found, lines_resolved, lines_cut, _ = row["lines/lines"]  # type: ignore[misc]
        prod_found, prod_resolved, prod_cut, _ = row["text/lines (producer)"]  # type: ignore[misc]
        if lines_found == 0 and prod_found == 0:
            continue
        useful += 1
        better = lines_cut <= prod_cut and lines_resolved >= prod_resolved
        strictly = lines_cut < prod_cut or lines_resolved > prod_resolved
        verdict = "lines domina" if (better and strictly) else "producer meglio o pari"
        if better and strictly:
            dominates += 1
        print(
            f"  {row['page']:16s} {lines_cut:6d}/{lines_resolved:<8d} "
            f"{prod_cut:8d}/{prod_resolved:<8d}   {verdict}"
        )

    share = dominates / useful if useful else 0.0
    print(f"\npagine utili: {useful}   lines domina: {dominates} ({share:.0%})")
    print()
    print(f"{'strategia':24s} {'trovate':>8s} {'risolte':>8s} {'span tagliati':>18s}")
    for label, (found, resolved, cut, considered) in totals.items():
        ratio = cut / considered if considered else 0.0
        print(f"{label:24s} {found:8d} {resolved:8d} {cut:8d}/{considered:<7d} ({ratio:.0%})")


if __name__ == "__main__":
    main()
