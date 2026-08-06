"""Compare column-band segmentation fed by two different row-clustering
inputs, holding the band algorithm itself fixed: _segment_column_bands
(Milestone 32) called unchanged, once on the production _cluster_rows
(loose, transitive running-envelope) rows, once on the strict,
non-transitive re-clustering already validated against an independent
font-size signal in inspect_row_clustering_merge_diagnostics.py (95-96%
agreement across DB/Fab/Kul, divergence explained and one-directional).

Same band-segmentation function both times. Any difference in the
reported bands, gaps, or column_count sequence is therefore attributable
to which rows feed it, i.e. to the row-merging issue already quantified,
not to a different band algorithm being tried here.

Purpose: check whether the row-merging problem actually changes the
column_band-relevant output (gap positions, support ratios, column
counts) on pages already inspected by hand (DB.pdf page 26 in particular),
before deciding whether fixing _cluster_rows is a precondition for
designing the column_band producer or a separate concern.

Not a producer. Not wired anywhere. No RegionCandidate, no
structural_kind, no threshold ratified here. _strict_cluster_rows is
duplicated from inspect_row_clustering_merge_diagnostics.py, not
imported, to keep this script runnable standalone; both copies must stay
identical if either changes -- same tolerance for small duplicated
helpers already established in the project (Milestone 30 note on
_contains).
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

from scan_column_structure_diagnostics import (  # noqa: E402
    _cluster_rows,
    _segment_column_bands,
    _visible_bbox,
)

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6
_DEFAULT_STRICT_OVERLAP_FRACTION = 0.5

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "method",
    "band_index",
    "band_count",
    "row_count",
    "y0",
    "y1",
    "column_count",
    "gaps",
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

    rows = list(
        _scan_document(
            pdf_path,
            only_page=args.page,
            bin_width=args.bin_width,
            min_gap_width=args.min_gap_width,
            min_support_ratio=args.min_support_ratio,
            strict_overlap_fraction=args.strict_overlap_fraction,
        )
    )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _scan_document(
    pdf_path: Path,
    *,
    only_page: int | None,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
    strict_overlap_fraction: float,
) -> list[dict[str, object]]:
    manual = pdf_path.name
    output_rows: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        page_indices = [only_page - 1] if only_page is not None else range(document.page_count)
        for page_index in page_indices:
            if page_index < 0 or page_index >= document.page_count:
                print(f"page out of range, skipped: {page_index + 1}", file=sys.stderr)
                continue

            page_number = page_index + 1
            page = document.load_page(page_index)

            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"diagnostic-page:{page_index}",
                capture_id=f"diagnostic-pymupdf-capture:{page_index}",
            )
            primitive_page: NormalizedPrimitivePage = normalize_backend_page_capture(capture)

            page_width = primitive_page.page_geometry.width
            page_height = primitive_page.page_geometry.height

            visible_bboxes: list[BBox] = []
            for text_primitive in primitive_page.text_primitives:
                visible_bbox = _visible_bbox(
                    text_primitive.bbox, page_width=page_width, page_height=page_height
                )
                if visible_bbox is not None:
                    visible_bboxes.append(visible_bbox)

            if not visible_bboxes:
                continue

            loose_rows = _cluster_rows(visible_bboxes)
            strict_rows = _strict_cluster_rows(
                visible_bboxes, overlap_fraction=strict_overlap_fraction
            )

            for method_name, method_rows in (("loose", loose_rows), ("strict", strict_rows)):
                bands = _segment_column_bands(
                    method_rows,
                    page_width=page_width,
                    bin_width=bin_width,
                    min_gap_width=min_gap_width,
                    min_support_ratio=min_support_ratio,
                )
                for band_index, band in enumerate(bands):
                    output_rows.append(
                        {
                            "manual": manual,
                            "page": page_number,
                            "method": method_name,
                            "band_index": band_index,
                            "band_count": len(bands),
                            "row_count": band["row_count"],
                            "y0": band["y0"],
                            "y1": band["y1"],
                            "column_count": band["column_count"],
                            "gaps": tuple(band["gaps"]),
                        }
                    )

    return output_rows


def _strict_cluster_rows(bboxes: list[BBox], *, overlap_fraction: float) -> list[list[BBox]]:
    """Duplicated from inspect_row_clustering_merge_diagnostics.py on purpose
    (see module docstring): compares each bbox only to the immediately
    preceding one, never to a growing running envelope.
    """

    if not bboxes:
        return []

    ordered = sorted(bboxes, key=lambda bbox: bbox[1])
    rows: list[list[BBox]] = [[ordered[0]]]
    last_y0, last_y1 = ordered[0][1], ordered[0][3]
    for bbox in ordered[1:]:
        y0, y1 = bbox[1], bbox[3]
        overlap = max(0.0, min(last_y1, y1) - max(last_y0, y0))
        min_height = min(last_y1 - last_y0, y1 - y0)
        fraction = (overlap / min_height) if min_height > 0 else 0.0
        if fraction >= overlap_fraction:
            rows[-1].append(bbox)
        else:
            rows.append([bbox])
        last_y0, last_y1 = y0, y1
    return rows


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        gaps = cast(tuple[tuple[float, float, float], ...], row["gaps"])
        writer.writerow(
            [
                row["manual"],
                row["page"],
                row["method"],
                row["band_index"],
                row["band_count"],
                row["row_count"],
                f"{cast(float, row['y0']):.1f}",
                f"{cast(float, row['y1']):.1f}",
                row["column_count"],
                ";".join(f"{s:.1f}:{e:.1f}:{r:.2f}" for s, e, r in gaps),
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
