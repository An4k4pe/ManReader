"""Dump diretto, senza binning ne' soglia: per ogni gruppo (block_index,
line_index), i suoi bordi x0 (inizio) e x1 (fine) veri -- gli stessi valori
usati da `prototype_column_gap_group_persistence.py`, qui esposti senza
passare dalla griglia y/bin coperti-scoperti.

Motivo per cui esiste: su Dag.pdf p.84 (prosa a 2 colonne confermata da
render) `_measure_group_persistent_gaps` non trova alcun gap persistente,
nemmeno a `--min-support-ratio 0.3` ne' restringendo la finestra y al solo
corpo di paragrafo (v. scambio in sessione). Prima di continuare a
sospettare la soglia, questo script mostra il dato crudo: per ogni y-slice
approssimata a riga (raggruppando i gruppi per fasce y che si sovrappongono
fra loro), i gruppi attivi ordinati per x0 e il gap fra ciascuna coppia
consecutiva (`successivo.x0 - precedente.x1`). Se il gap fra colonna
sinistra e destra e' quasi sempre positivo e nell'ordine di grandezza atteso
(qualche decina di pt), il problema e' nell'implementazione del binning, non
nel dato. Se il gap risulta spesso negativo o vicino a zero, le due colonne
si toccano/sovrappongono in x su questa pagina e il fallimento del metodo a
griglia e' corretto, non un bug.

Non un producer. Non wired. Nessuna soglia, nessuna aggregazione: solo il
dato per riga, cosi' si vede a occhio prima di ipotizzare qualunque causa
(AGENTS.MD regola 14).

Uso:

    python3 scripts/dump_raw_group_gaps.py Dag.pdf --page 84 --output /tmp/raw_gaps_dag_p84.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prototype_column_band_producer import _group_by_pymupdf_line  # noqa: E402

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "y_slice_start",
    "y_slice_end",
    "active_group_count",
    "active_groups_x0_x1",
    "gap_index",
    "gap_start_x",
    "gap_end_x",
    "gap_width",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument("--page", type=int, required=True, help="1-indexed page number.")
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--sample-height",
        type=float,
        default=6.0,
        help="Altezza (pt) di ogni fetta y campionata, presa al centro di ogni gruppo "
        "cosi' da non richiedere una griglia fine su tutta la pagina. Default: 6.0.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    page_index = args.page - 1
    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        if page_index < 0 or page_index >= document.page_count:
            print(f"page out of range: {args.page}", file=sys.stderr)
            return 1
        page = document.load_page(page_index)
        if page.rotation != 0 or page.mediabox != page.cropbox:
            print("rotation/cropbox precondition failed", file=sys.stderr)
            return 1

        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{args.page:04d}",
            capture_id=f"diagnostic-raw-gaps-capture:{page_index}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        page_width = primitive_page.page_geometry.width
        page_height = primitive_page.page_geometry.height

        groups, _unparsed = _group_by_pymupdf_line(
            primitive_page.text_primitives, page_width=page_width, page_height=page_height
        )
        print(
            f"{len(groups)} gruppi (block,line) su {pdf_path.name} p.{args.page}", file=sys.stderr
        )

        # Campiona una fetta y al centro verticale di ogni gruppo (invece di
        # scandire l'intera pagina con un passo fisso): ogni riga tipografica
        # reale genera cosi' esattamente una fetta campionata, indipendente
        # dalla granularita' del bin usato dal metodo a griglia.
        sample_centers = sorted({(g.y0 + g.y1) / 2.0 for g in groups})

        for center_y in sample_centers:
            active = [g for g in groups if g.y0 <= center_y < g.y1]
            if len(active) < 2:
                continue
            active_sorted = sorted(active, key=lambda g: min(b[0] for b in g.bboxes))
            extents = [
                (min(b[0] for b in g.bboxes), max(b[2] for b in g.bboxes)) for g in active_sorted
            ]
            extents_repr = ";".join(f"({x0:.1f},{x1:.1f})" for x0, x1 in extents)
            y_slice_start = center_y - args.sample_height / 2.0
            y_slice_end = center_y + args.sample_height / 2.0
            for gap_index in range(len(extents) - 1):
                _prev_x0, prev_x1 = extents[gap_index]
                next_x0, _next_x1 = extents[gap_index + 1]
                gap_width = next_x0 - prev_x1
                rows.append(
                    {
                        "manual": pdf_path.name,
                        "page": args.page,
                        "y_slice_start": round(y_slice_start, 1),
                        "y_slice_end": round(y_slice_end, 1),
                        "active_group_count": len(active),
                        "active_groups_x0_x1": extents_repr,
                        "gap_index": gap_index,
                        "gap_start_x": round(prev_x1, 1),
                        "gap_end_x": round(next_x0, 1),
                        "gap_width": round(gap_width, 1),
                    }
                )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        writer.writerow([row[name] for name in _CSV_FIELDNAMES])


if __name__ == "__main__":
    raise SystemExit(main())
