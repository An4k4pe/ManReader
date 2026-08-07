"""Compare column-band segmentation fed by three different row-grouping
inputs, holding the band algorithm (_segment_column_bands, Milestone 32)
fixed:

  - loose: production _cluster_rows (transitive running-envelope over bbox
    overlap) -- the one shown to over-merge real lines.
  - strict: non-transitive re-clustering (compare each bbox only to the
    immediately preceding one), already used in
    compare_strict_vs_loose_column_bands.py.
  - pymupdf_line: group TextPrimitives by the (block_index, line_index)
    PyMuPDF itself already assigned during capture, recovered from
    TextPrimitive.source_observation_id (format
    "text:b{block:04d}:l{line:04d}:s{span:04d}", written in
    pymupdf_capture.py and passed through unchanged in
    primitive_normalizer.py -- verified by reading both files, not
    assumed). This uses PyMuPDF's own line/block layout analysis instead
    of reconstructing line membership from bare bbox overlap, which is
    what a human reviewer asked about directly: does something more
    reliable than home-made geometric clustering already exist in the
    pipeline. It does; this script tests whether using it instead of
    _cluster_rows changes the outcome.

Not a producer. Not wired anywhere. No RegionCandidate, no structural_kind,
no threshold ratified. If pymupdf_line performs as well as or better than
strict on the pages already inspected (26, 68, 99, 5), it is a candidate
to replace the geometric re-clustering approach entirely in the eventual
column_band producer, not just add a third option.
"""

from __future__ import annotations

import argparse
import csv
import re
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
from primitive_model import NormalizedPrimitivePage, TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6
_DEFAULT_STRICT_OVERLAP_FRACTION = 0.5

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s\d+$")

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
            visible_primitives: list[TextPrimitive] = []
            for text_primitive in primitive_page.text_primitives:
                visible_bbox = _visible_bbox(
                    text_primitive.bbox, page_width=page_width, page_height=page_height
                )
                if visible_bbox is not None:
                    visible_bboxes.append(visible_bbox)
                    visible_primitives.append(text_primitive)

            if not visible_bboxes:
                continue

            loose_rows = _cluster_rows(visible_bboxes)
            strict_rows = _strict_cluster_rows(
                visible_bboxes, overlap_fraction=strict_overlap_fraction
            )
            pymupdf_rows, unparsed_count = _pymupdf_line_rows(visible_primitives)
            if unparsed_count > 0:
                print(
                    f"page {page_number}: {unparsed_count} primitive(s) with unparseable "
                    "source_observation_id, excluded from pymupdf_line grouping",
                    file=sys.stderr,
                )

            for method_name, method_rows in (
                ("loose", loose_rows),
                ("strict", strict_rows),
                ("pymupdf_line", pymupdf_rows),
            ):
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
    """Duplicated from compare_strict_vs_loose_column_bands.py on purpose (see that
    module's docstring for the rationale)."""

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


def _pymupdf_line_rows(
    primitives: list[TextPrimitive],
) -> tuple[list[list[BBox]], int]:
    """Group TextPrimitive bboxes by the (block_index, line_index) PyMuPDF assigned
    during capture, parsed from source_observation_id ("text:b####:l####:s####").
    Groups are ordered by their minimum y0, matching the top-to-bottom order
    _cluster_rows/_strict_cluster_rows already produce, so the output is
    interchangeable as input to _segment_column_bands.
    """

    groups: dict[tuple[int, int], list[BBox]] = {}
    unparsed_count = 0
    for primitive in primitives:
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed_count += 1
            continue
        key = (int(match.group(1)), int(match.group(2)))
        groups.setdefault(key, []).append(primitive.bbox)

    ordered_groups = sorted(groups.values(), key=lambda bboxes: min(bbox[1] for bbox in bboxes))
    return ordered_groups, unparsed_count


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
