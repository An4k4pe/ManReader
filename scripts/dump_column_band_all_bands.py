"""Dump OGNI banda (`_segment_column_bands`, Milestone 32, importata invariata),
qualunque sia il suo `column_count` -- a differenza di
``prototype_column_band_producer.py``, che emette candidate solo per
``column_count >= 2`` (v10 Sec.4.5). Qui niente RegionCandidate, niente
soglia, niente filtro: solo il dato grezzo, per misurare -- non assumere --
se le bande con `column_count` alto durano poche righe (pattern "flicker",
gia' descritto in `State.md` Milestone 32 come uno dei cinque confound noti)
oppure no.

Origine: ispezionando FWK.pdf p.6 (un sommario) sono comparse tre bande,
lunghe rispettivamente 3, 1 e 1 riga, con `column_count` 3, 2, 4 -- nessuna
banda stabile su molte righe. Ipotesi dell'utente, non ancora misurata su
piu' di una pagina: le bande "vere" (prosa a piu' colonne) durano molte
righe; le bande con `column_count` alto e `row_count` basso sono un segnale
di qualcos'altro (tabelle, liste, sommari) -- non da scartare come rumore,
ma potenzialmente da usare come indizio per un producer DIVERSO da
`column_band` (tabelle/liste rilevate da pura geometria PyMuPDF, utile in
particolare dove `table_candidate`/pdfplumber non trova nulla: su FWK.pdf
p.6 `table_candidate` non aveva prodotto alcuna candidate, mentre queste tre
bande ci sono).

Non un producer. Non wired. Nessuna soglia proposta qui: questo script
raccoglie il dato (row_count, column_count, estensione) per ogni banda di
ogni pagina, cosi' la relazione fra i due si puo' guardare su piu' pagine e
piu' manuali prima di decidere se c'e' un segnale utilizzabile.

Uso (fish o bash, comando su una riga):

    python3 scripts/dump_column_band_all_bands.py FWK.pdf --output /tmp/all_bands_fwk.csv
    python3 scripts/dump_column_band_all_bands.py Fab.pdf --output /tmp/all_bands_fab.csv
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

from prototype_column_band_producer import (  # noqa: E402
    _assemble_visual_rows,
    _flatten_row_bboxes,
    _group_by_pymupdf_line,
)
from scan_column_structure_diagnostics import _segment_column_bands  # noqa: E402

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "band_index",
    "band_count",
    "row_start",
    "row_end",
    "row_count",
    "column_count",
    "y0",
    "y1",
    "gap_boundaries",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument("--bin-width", type=float, default=_DEFAULT_BIN_WIDTH)
    parser.add_argument("--min-gap-width", type=float, default=_DEFAULT_MIN_GAP_WIDTH)
    parser.add_argument("--min-support-ratio", type=float, default=_DEFAULT_MIN_SUPPORT_RATIO)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        page_indices = list(
            [args.page - 1] if args.page is not None else range(document.page_count)
        )
        print(
            f"{pdf_path.name}: {len(page_indices)} pagina/e da processare",
            file=sys.stderr,
            flush=True,
        )
        for progress_index, page_index in enumerate(page_indices, start=1):
            if page_index < 0 or page_index >= document.page_count:
                print(f"page out of range, skipped: {page_index + 1}", file=sys.stderr)
                continue
            page_number = page_index + 1
            if (
                progress_index == 1
                or progress_index % 10 == 0
                or progress_index == len(page_indices)
            ):
                print(
                    f"  pagina {page_number} ({progress_index}/{len(page_indices)})...",
                    file=sys.stderr,
                    flush=True,
                )
            page = document.load_page(page_index)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                print(
                    f"page {page_number}: rotation/cropbox precondition failed, skipped",
                    file=sys.stderr,
                )
                continue

            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"page:{page_number:04d}",
                capture_id=f"diagnostic-all-bands-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)
            page_width = primitive_page.page_geometry.width

            groups, _unparsed = _group_by_pymupdf_line(
                primitive_page.text_primitives,
                page_width=page_width,
                page_height=primitive_page.page_geometry.height,
            )
            visual_rows = _assemble_visual_rows(groups)
            row_bboxes = [_flatten_row_bboxes(row) for row in visual_rows]

            bands = _segment_column_bands(
                row_bboxes,
                page_width=page_width,
                bin_width=args.bin_width,
                min_gap_width=args.min_gap_width,
                min_support_ratio=args.min_support_ratio,
            )
            for band_index, band in enumerate(bands):
                gaps = band["gaps"]
                rows.append(
                    {
                        "manual": pdf_path.name,
                        "page": page_number,
                        "band_index": band_index,
                        "band_count": len(bands),
                        "row_start": band["row_start"],
                        "row_end": band["row_end"],
                        "row_count": band["row_count"],
                        "column_count": band["column_count"],
                        "y0": round(cast(float, band["y0"]), 1),
                        "y1": round(cast(float, band["y1"]), 1),
                        "gap_boundaries": tuple((round(s, 1), round(e, 1)) for s, e, _r in gaps),
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
