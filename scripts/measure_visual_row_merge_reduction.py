"""Answers v10 Sec.11.6: "quanto la sovra-fusione di righe misurata
pre-Milestone 36 (13,6%-45,7%) si riduca effettivamente con l'assemblaggio a
grana di gruppo di Sec.4.2" -- dichiarato non misurato in v9/v10, non un
risultato assunto qui.

Riusa, senza reimplementarlo, il Metodo A di
``inspect_row_clustering_merge_diagnostics.py`` (Milestone pre-36): re-cluster
le bbox di una riga con una regola non transitiva (confronto solo con la bbox
immediatamente precedente, per frazione di sovrapposizione verticale >=
``--strict-overlap-fraction`` dell'altezza minore) e conta i sotto-cluster.
``strict_subcluster_count > 1`` su una riga è evidenza che quella riga fonde
più righe reali distinte. La funzione è duplicata da
``inspect_row_clustering_merge_diagnostics.py``/
``compare_pymupdf_line_grouping_column_bands.py`` -- stessa dichiarazione di
quei due file: "Duplicated ... on purpose", non una copia silenziosa.

Applica lo stesso identico controllo a due input diversi per la STESSA pagina:

  - OLD: righe prodotte da ``_cluster_rows`` (Milestone 32, importata
    invariata) -- la baseline già misurata al 13,6%-45,7% di sovra-fusione.
  - NEW: righe visive prodotte da ``_group_by_pymupdf_line`` +
    ``_assemble_visual_rows`` (v10 Sec.4.1-4.2,
    ``prototype_column_band_producer.py``, importate invariate).

Il tasso di sovra-fusione per ciascun metodo è
``righe con strict_subcluster_count > 1`` / ``righe totali``, sulla STESSA
pagina, cosi' il confronto e' diretto e non richiede un secondo campione.

Limite dichiarato: verificato solo su un caso sintetico a due colonne pulite
in fase di scrittura (nessun manuale reale disponibile in
quell'ambiente) -- in quel caso OLD e NEW coincidono perche' non c'era rumore
da fondere. Non misura ancora la riduzione reale: richiede esecuzione su
DB.pdf/Fab.pdf/Kul.pdf (gli stessi tre manuali della misura originale
13,6%-45,7%) o piu' ampio.

Non un producer. Non wired. Nessuna soglia proposta come cutoff di
produzione.

Uso:

    python3 scripts/measure_visual_row_merge_reduction.py DB.pdf \\
        --output /tmp/merge_reduction_db.csv
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
from scan_column_structure_diagnostics import _cluster_rows, _visible_bbox  # noqa: E402

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_STRICT_OVERLAP_FRACTION = 0.5

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "method",
    "row_count",
    "over_merged_row_count",
    "over_merge_rate",
)


def _strict_subcluster_count(row_bboxes: list[BBox], *, overlap_fraction: float) -> int:
    """Duplicated on purpose from inspect_row_clustering_merge_diagnostics.py
    Method A / compare_pymupdf_line_grouping_column_bands.py's
    _strict_cluster_rows: non-transitive re-clustering, compares each bbox
    only to the immediately preceding one."""

    if not row_bboxes:
        return 0
    ordered = sorted(row_bboxes, key=lambda bbox: bbox[1])
    subclusters = 1
    last_y0, last_y1 = ordered[0][1], ordered[0][3]
    for bbox in ordered[1:]:
        y0, y1 = bbox[1], bbox[3]
        overlap = max(0.0, min(last_y1, y1) - max(last_y0, y0))
        min_height = min(last_y1 - last_y0, y1 - y0)
        fraction = (overlap / min_height) if min_height > 0 else 0.0
        if fraction < overlap_fraction:
            subclusters += 1
        last_y0, last_y1 = y0, y1
    return subclusters


def _over_merge_rate(rows: list[list[BBox]], *, overlap_fraction: float) -> tuple[int, int]:
    over_merged = sum(
        1 for row in rows if _strict_subcluster_count(row, overlap_fraction=overlap_fraction) > 1
    )
    return over_merged, len(rows)


def _scan_page(
    primitive_page: NormalizedPrimitivePage,
    *,
    manual: str,
    page_number: int,
    overlap_fraction: float,
) -> list[dict[str, object]]:
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    visible_bboxes: list[BBox] = []
    for text_primitive in primitive_page.text_primitives:
        visible = _visible_bbox(text_primitive.bbox, page_width=page_width, page_height=page_height)
        if visible is not None:
            visible_bboxes.append(visible)

    old_rows = _cluster_rows(visible_bboxes)

    groups, _unparsed = _group_by_pymupdf_line(
        primitive_page.text_primitives, page_width=page_width, page_height=page_height
    )
    visual_rows = _assemble_visual_rows(groups)
    new_rows = [_flatten_row_bboxes(row) for row in visual_rows]

    output_rows: list[dict[str, object]] = []
    for method_name, rows in (("old_cluster_rows", old_rows), ("new_visual_rows", new_rows)):
        over_merged, total = _over_merge_rate(rows, overlap_fraction=overlap_fraction)
        output_rows.append(
            {
                "manual": manual,
                "page": page_number,
                "method": method_name,
                "row_count": total,
                "over_merged_row_count": over_merged,
                "over_merge_rate": round(over_merged / total, 4) if total > 0 else "",
            }
        )
    return output_rows


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--strict-overlap-fraction", type=float, default=_DEFAULT_STRICT_OVERLAP_FRACTION
    )
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
                capture_id=f"diagnostic-merge-reduction-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)
            rows.extend(
                _scan_page(
                    primitive_page,
                    manual=pdf_path.name,
                    page_number=page_number,
                    overlap_fraction=args.strict_overlap_fraction,
                )
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
