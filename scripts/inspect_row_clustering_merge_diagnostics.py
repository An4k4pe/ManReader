"""Exploratory, diagnostic-only check of a second hypothesis, pre-registered
here before running on any manual:

  H: _cluster_rows (Milestone 32, scripts/scan_column_structure_diagnostics.py)
  merges multiple real typographic lines into a single "row" whenever their
  bboxes chain-overlap transitively, because it tracks a running max
  (current_y1 = max(current_y1, y1)) rather than comparing each new bbox
  only to the immediately preceding one. Suspected from visual inspection on
  DB.pdf pages 26 and 99 (multi-line paragraphs reported as row_count=1),
  not yet quantified on any page.

Two independent, convergent checks per "loose" row (the real
_cluster_rows output, called unchanged, not reimplemented):

  A. Structural sensitivity: re-cluster the SAME bboxes with a stricter
     rule -- compare each bbox only to the immediately PRECEDING one
     (by y-overlap fraction >= --strict-overlap-fraction of the smaller
     bbox's height), instead of to a growing running envelope. This
     cannot inherit the transitive-chaining behaviour by construction.
     If a loose row splits into more than one strict sub-cluster, that is
     evidence the loose row bridged content that would not, under a
     non-transitive rule, be read as one row. Reports
     strict_subcluster_count per loose row.

  B. Font-size-normalized height: page-local body font size estimated as
     the modal TextPrimitive.font_size on the page (same method already
     validated in Milestone 35's typographic-shape work,
     scripts/inspect_image_typographic_shape.py -- reused by description,
     not by import, since that script estimates shape for images, not
     rows). estimated_line_count = row_height / (font_size_mode *
     --leading-factor). Pages with fewer than 20 text primitives are
     recorded with font_size_mode=None and estimated_line_count=None, not
     silently skipped -- same threshold and same reason already used in
     Milestone 35 (font size not reliably estimable page-locally below
     that count).

No threshold here is being proposed as a production cutoff. This reports
both signals per row so the two can be cross-checked against each other
before any threshold is discussed.

Not a producer. Not wired anywhere. Calls _cluster_rows/_visible_bbox
(Milestone 32) unchanged, no copy of that function; the strict
re-clustering is a separate, deliberately different algorithm (see A),
not a retuned copy.
"""

from __future__ import annotations

import argparse
import csv
import statistics
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

from scan_column_structure_diagnostics import _cluster_rows, _visible_bbox  # noqa: E402

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_STRICT_OVERLAP_FRACTION = 0.5
_DEFAULT_LEADING_FACTOR = 1.2
_MIN_PRIMITIVES_FOR_FONT_SIZE = 20
_FONT_SIZE_BUCKET = (
    0.5  # round to nearest 0.5pt before taking the mode, same stability trick as Milestone 35
)

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "row_index",
    "row_y0",
    "row_y1",
    "row_height",
    "primitive_count",
    "page_font_size_mode",
    "estimated_line_count",
    "strict_subcluster_count",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--strict-overlap-fraction", type=float, default=_DEFAULT_STRICT_OVERLAP_FRACTION
    )
    parser.add_argument("--leading-factor", type=float, default=_DEFAULT_LEADING_FACTOR)
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
            strict_overlap_fraction=args.strict_overlap_fraction,
            leading_factor=args.leading_factor,
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
    strict_overlap_fraction: float,
    leading_factor: float,
) -> list[dict[str, object]]:
    manual = pdf_path.name
    output_rows: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
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

            # page_font_size_mode (below) only needs the page-wide distribution of
            # font sizes, not a per-bbox lookup: estimated_line_count compares a
            # row's total height to the page's single body size, the same
            # page-local estimate already validated in Milestone 35, not to the
            # font size of any specific primitive in that row.
            visible_bboxes: list[BBox] = []
            all_font_sizes: list[float] = []
            for text_primitive in primitive_page.text_primitives:
                visible_bbox = _visible_bbox(
                    text_primitive.bbox, page_width=page_width, page_height=page_height
                )
                if visible_bbox is None:
                    continue
                visible_bboxes.append(visible_bbox)
                if text_primitive.font_size is not None:
                    all_font_sizes.append(text_primitive.font_size)

            if not visible_bboxes:
                continue

            page_font_size_mode = _estimate_page_font_size_mode(all_font_sizes)

            loose_rows = _cluster_rows(visible_bboxes)

            for row_index, row_bboxes in enumerate(loose_rows):
                row_y0 = min(bbox[1] for bbox in row_bboxes)
                row_y1 = max(bbox[3] for bbox in row_bboxes)
                row_height = row_y1 - row_y0

                if page_font_size_mode is not None and page_font_size_mode > 0:
                    estimated_line_count: float | None = row_height / (
                        page_font_size_mode * leading_factor
                    )
                else:
                    estimated_line_count = None

                strict_subclusters = _strict_cluster_rows(
                    row_bboxes, overlap_fraction=strict_overlap_fraction
                )

                output_rows.append(
                    {
                        "manual": manual,
                        "page": page_number,
                        "row_index": row_index,
                        "row_y0": row_y0,
                        "row_y1": row_y1,
                        "row_height": row_height,
                        "primitive_count": len(row_bboxes),
                        "page_font_size_mode": page_font_size_mode,
                        "estimated_line_count": estimated_line_count,
                        "strict_subcluster_count": len(strict_subclusters),
                    }
                )

    return output_rows


def _estimate_page_font_size_mode(font_sizes: list[float]) -> float | None:
    if len(font_sizes) < _MIN_PRIMITIVES_FOR_FONT_SIZE:
        return None
    bucketed = [round(size / _FONT_SIZE_BUCKET) * _FONT_SIZE_BUCKET for size in font_sizes]
    try:
        return statistics.mode(bucketed)
    except statistics.StatisticsError:
        return None


def _strict_cluster_rows(bboxes: list[BBox], *, overlap_fraction: float) -> list[list[BBox]]:
    """Cluster bboxes into rows comparing each bbox only to the immediately
    preceding one (by vertical overlap fraction of the smaller bbox's
    height), never to a growing running envelope. Deliberately different
    from _cluster_rows (Milestone 32), not a retuned copy of it: this is
    the check for whether the running-envelope chaining is what causes
    over-merging, so it must not share that mechanism.
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
        font_size_mode = row["page_font_size_mode"]
        estimated_line_count = row["estimated_line_count"]
        writer.writerow(
            [
                row["manual"],
                row["page"],
                row["row_index"],
                f"{cast(float, row['row_y0']):.1f}",
                f"{cast(float, row['row_y1']):.1f}",
                f"{cast(float, row['row_height']):.1f}",
                row["primitive_count"],
                f"{cast(float, font_size_mode):.1f}" if font_size_mode is not None else "",
                f"{cast(float, estimated_line_count):.2f}"
                if estimated_line_count is not None
                else "",
                row["strict_subcluster_count"],
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
