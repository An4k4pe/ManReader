"""Piano di misura di v10 Sec.11.3 (overlap banda/table_candidate, Milestone
33 punto bloccante 2) eseguito -- non chiude il punto bloccante, lo misura.
Serve anche v10 Sec.11.7 (bbox del candidate `column_band`): calcola
entrambe le varianti (full-width, observed-extent) sulla stessa pagina cosi'
la scelta puo' essere informata dai dati invece che decisa a priori.

Costruisce, per ogni pagina: il prototipo `column_band` (v10 Sec.4,
``prototype_column_band_producer.py``, entrambe le varianti di bbox) e il
producer REALE `table_candidate` (Milestone 20-21,
``build_table_candidate_page_analysis``, non reimplementato). Lega i due con
il sottosistema Milestone 13-19 e misura l'overlap con la funzione di
PRODUZIONE gia' verificata, non con una formula inline:
``measure_co_referenced_page_candidate_overlap_ratio`` (Milestone 34 SS.E1).

Avvertenza portata esplicitamente da v10 Sec.11.3, che la cita dalla chiusura
di Milestone 35 in ``State.md``: "qualunque misura di contenimento
geometrico contro table_candidate e' quasi priva di informazione se non
accompagnata dal tasso di base" -- `table_candidate` copre spesso un terzo-
due terzi dell'area di pagina dove compare. **Limite dichiarato di questa
prima versione**: nessun controllo di permutazione (i due nulli usati per il
contenimento IVF-EV in Milestone 35, `measure_cross_producer_candidate_
coverage.py --permutations`) -- non incluso qui per tenere lo script
verificabile in un solo giro; il tasso grezzo riportato NON e' di per se'
evidenza di arricchimento reale, solo un primo numero da guardare insieme al
bbox-mode prima di decidere se vale la pena costruire il controllo di
permutazione per questa coppia di producer specifica.

**Precondizione dichiarata da v10, non soddisfatta da questo script**: il
criterio di falsificazione per l'overlap banda/table_candidate va registrato
per iscritto PRIMA di guardare il risultato (`AGENTS.MD` regola 15),
vincolato al caso concreto da cui l'ipotesi e' nata (Fab.pdf, liste numerate
con icona; FWK.pdf, sommario p.6-9). Questo script produce solo il dato;
la registrazione del criterio resta un passo separato, da fare PRIMA di
eseguirlo su quelle pagine specifiche.

Non un producer. Non wired. Nessuna regola di Resolution proposta o
implicata da questo script.

Uso:

    python3 scripts/measure_column_band_table_candidate_overlap.py Fab.pdf \\
        --output /tmp/overlap_fab.csv
    python3 scripts/measure_column_band_table_candidate_overlap.py FWK.pdf \\
        --page 6 --output /tmp/overlap_fwk_p6.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz
import pdfplumber

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

from prototype_column_band_producer import build_column_band_prototype  # noqa: E402

from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_candidate_overlap_ratio_measurements import (  # noqa: E402
    measure_co_referenced_page_candidate_overlap_ratio,
)
from page_analysis_co_reference_candidate_reference import (  # noqa: E402
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import PageAnalysis  # noqa: E402
from page_analysis_table_candidate import build_table_candidate_page_analysis  # noqa: E402
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "bbox_mode",
    "column_band_candidate_id",
    "column_band_bbox",
    "table_candidate_id",
    "table_candidate_bbox",
    "overlap_ratio",
    "overlap_area",
    "column_band_area",
    "table_candidate_area",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    return parser


def _scan_page(
    *,
    manual: str,
    page_number: int,
    fitz_document: fitz.Document,
    plumber_pdf: pdfplumber.pdf.PDF,
) -> list[dict[str, object]]:
    page = fitz_document.load_page(page_number - 1)
    if page.rotation != 0 or page.mediabox != page.cropbox:
        print(
            f"page {page_number}: rotation/cropbox precondition failed, skipped",
            file=sys.stderr,
        )
        return []

    capture = capture_pymupdf_page(
        page,
        source_id="diagnostic-source",
        page_id=f"page:{page_number:04d}",
        capture_id=f"diagnostic-overlap-capture:{page_number:04d}",
    )
    primitive_page = normalize_backend_page_capture(capture)

    # find_tables (pdfplumber, vertical_strategy="text") e' il passo lento di
    # questo script -- puo' richiedere diversi secondi su una pagina fitta,
    # ed e' l'unico posto dove uno scan su un intero manuale puo' restare
    # visibilmente fermo a lungo fra due righe di log.
    print(f"    pagina {page_number}: find_tables (pdfplumber)...", file=sys.stderr, flush=True)
    table_analysis = build_table_candidate_page_analysis(
        BoundTableCandidatePage(
            primitive_page=primitive_page,
            plumber_page=plumber_pdf.pages[page_number - 1],
        ),
        generation_id=f"generation:overlap:table:{page_number:04d}",
    )

    output_rows: list[dict[str, object]] = []
    if not table_analysis.candidates:
        return output_rows

    for bbox_mode in ("full-width", "observed-extent"):
        column_band_analysis, _measurements = build_column_band_prototype(
            primitive_page,
            generation_id=f"generation:overlap:column-band:{page_number:04d}:{bbox_mode}",
            bbox_mode=bbox_mode,
        )
        if not column_band_analysis.candidates:
            continue

        analyses: tuple[PageAnalysis, ...] = (column_band_analysis, table_analysis)
        bound = bind_co_referenced_page_analyses(
            primitive_page,
            co_referenced_page_analyses=build_co_referenced_page_analyses(analyses),
        )

        for band_candidate in column_band_analysis.candidates:
            band_reference = build_co_referenced_page_candidate_reference(
                bound, analysis=column_band_analysis, candidate=band_candidate
            )
            for table_candidate in table_analysis.candidates:
                table_reference = build_co_referenced_page_candidate_reference(
                    bound, analysis=table_analysis, candidate=table_candidate
                )
                measurement = measure_co_referenced_page_candidate_overlap_ratio(
                    bound,
                    first_candidate_reference=band_reference,
                    second_candidate_reference=table_reference,
                )
                output_rows.append(
                    {
                        "manual": manual,
                        "page": page_number,
                        "bbox_mode": bbox_mode,
                        "column_band_candidate_id": band_candidate.candidate_id,
                        "column_band_bbox": tuple(round(c, 1) for c in band_candidate.bbox),
                        "table_candidate_id": table_candidate.candidate_id,
                        "table_candidate_bbox": tuple(round(c, 1) for c in table_candidate.bbox),
                        "overlap_ratio": round(measurement.overlap_ratio, 4),
                        "overlap_area": round(measurement.overlap_area, 1),
                        "column_band_area": round(measurement.first_candidate_area, 1),
                        "table_candidate_area": round(measurement.second_candidate_area, 1),
                    }
                )
    return output_rows


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    rows: list[dict[str, object]] = []
    with (
        fitz.open(pdf_path) as fitz_document,
        pdfplumber.open(str(pdf_path)) as plumber_pdf,
    ):
        page_indices = list(
            [args.page] if args.page is not None else range(1, fitz_document.page_count + 1)
        )
        print(
            f"{pdf_path.name}: {len(page_indices)} pagina/e da processare "
            "(find_tables e' lento, attendersi diversi secondi a pagina su manuali interi)",
            file=sys.stderr,
            flush=True,
        )
        for progress_index, page_number in enumerate(page_indices, start=1):
            if page_number < 1 or page_number > fitz_document.page_count:
                print(f"page out of range, skipped: {page_number}", file=sys.stderr)
                continue
            print(
                f"  pagina {page_number} ({progress_index}/{len(page_indices)})...",
                file=sys.stderr,
                flush=True,
            )
            rows.extend(
                _scan_page(
                    manual=pdf_path.name,
                    page_number=page_number,
                    fitz_document=fitz_document,
                    plumber_pdf=plumber_pdf,
                )
            )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    if not rows:
        print(
            "Nessuna coppia column_band/table_candidate trovata nell'intervallo "
            "scansionato (nessuna pagina aveva entrambi i producer con candidate).",
            file=sys.stderr,
        )

    return 0


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        writer.writerow([row[name] for name in _CSV_FIELDNAMES])


if __name__ == "__main__":
    raise SystemExit(main())
