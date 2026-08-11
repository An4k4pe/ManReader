"""Prepara i dati per l'ispezione visiva richiesta prima di trattare v10
Sec.4.7/Sec.11.1 come deciso -- non decide nulla da solo.

v10 Sec.4.7 propone di popolare ``unresolved_primitive_ids`` dai gruppi che
attraversano un gap persistente di banda (criterio verificato,
``test_pymupdf_block_gap_straddle.py:22-24``). Chat B (Giro 2, sottomissione
v9) ha correttamente distinto due domande: "il predicato è raro e le sue
eccezioni passate erano spiegabili" (già misurato, falsificazione v7/v8) non è
la stessa cosa di "segnare questo gruppo come irrisolto è la scelta
editorialmente corretta" (mai verificato). Questo script non risponde alla
seconda domanda -- nessuno script può, è un giudizio editoriale, non una
misura -- prepara solo i dati perché un umano possa rispondere per ispezione
diretta (``AGENTS.MD`` regola 14), con testo e contesto di banda, non solo un
conteggio.

Per ogni pagina, per ogni banda con ``column_count >= 2``: elenca i gruppi
straddle con testo concatenato, bbox, e i confini del gap che attraversano.
Nessuna soglia, nessuna decisione, nessun filtro oltre al criterio già
verificato.

Non un producer. Non wired. Riusa (import, non copia)
``prototype_column_band_producer.py`` (v10 Sec.4.1-4.7).

Uso:

    python3 scripts/inspect_column_band_straddle_groups.py Fab.pdf \\
        --output /tmp/straddle_fab.csv
    python3 scripts/inspect_column_band_straddle_groups.py FWK.pdf \\
        --page 6 --output /tmp/straddle_fwk_p6.csv
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

from prototype_column_band_producer import build_column_band_prototype  # noqa: E402

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "band_index",
    "column_count",
    "gap_boundaries",
    "unresolved_primitive_id",
    "text_snippet",
    "bbox",
)

_SNIPPET_LENGTH = 60


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
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
                capture_id=f"diagnostic-straddle-inspect-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)
            text_by_id = {
                primitive.primitive_id: (primitive.text, primitive.bbox)
                for primitive in primitive_page.text_primitives
            }

            _analysis, measurements = build_column_band_prototype(
                primitive_page,
                generation_id=f"generation:straddle-inspect:{page_number:04d}",
                bbox_mode="observed-extent",
            )
            for measurement in measurements:
                unresolved_ids = cast(
                    tuple[str, ...], measurement.get("unresolved_primitive_ids", ())
                )
                if not unresolved_ids:
                    continue
                for primitive_id in unresolved_ids:
                    text, bbox = text_by_id.get(primitive_id, ("<not found>", None))
                    snippet = text.replace("\n", "\\n")[:_SNIPPET_LENGTH]
                    rows.append(
                        {
                            "manual": pdf_path.name,
                            "page": page_number,
                            "band_index": measurement["band_index"],
                            "column_count": measurement["column_count"],
                            "gap_boundaries": measurement["gap_boundaries"],
                            "unresolved_primitive_id": primitive_id,
                            "text_snippet": snippet,
                            "bbox": tuple(round(c, 1) for c in bbox) if bbox else "",
                        }
                    )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    if not rows:
        print(
            "Nessun gruppo straddle trovato nell'intervallo scansionato "
            "(atteso: raro, 0,00%-2,24% dei gruppi sui 17 manuali gia' testati).",
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
