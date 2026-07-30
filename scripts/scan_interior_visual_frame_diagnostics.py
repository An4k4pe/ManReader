"""Exploratory scan combining Milestone 25/26 diagnostics per page, for manual
inspection (Milestone 29 proposal, §6).

Not a producer, not wired anywhere. One capture + one normalize per page; both
diagnostics (dump_interior_visual_diagnostics, dump_drawing_cluster_diagnostics)
and the new local vector-containment helper run on that same
NormalizedPrimitivePage, never recomputed.

The vector containment helper below duplicates _contains
(page_analysis_primitive_pair_measurements.py:349, strict containment, no
tolerance) locally instead of reusing measure_primitive_pair: that function
requires primitive_id values resolvable through _primitives_by_id, not an
arbitrary bbox such as a cluster's bbox union. Same local-duplication principle
already used by Milestone 26 for the covering/edge thresholds
(State_Archive.md:143). Strict containment matches the raster branch
(measure_primitive_pair via dump_interior_visual_diagnostics), not the more
permissive legacy variant (extractor.py:_asset_is_box_like_text_region,
tolerance=3.0 OR overlap_ratio>=0.90) -- kept for consistency between the two
branches of the same diagnostic, not reimplemented here.

This script is intentionally not committed to the repository.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from page_analysis_drawing_cluster_diagnostics import dump_drawing_cluster_diagnostics  # noqa: E402
from page_analysis_interior_visual_diagnostics import dump_interior_visual_diagnostics  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_MIN_AREA_RATIO = 0.006
_DEFAULT_MAX_AREA_RATIO = 0.28

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "type",
    "bbox",
    "page_area_ratio",
    "contained_text_primitive_count",
    "contained_text_area_ratio",
    "dispersion_ratio",
    "primitive_ids",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan an entire PDF for residual interior visuals (raster and "
            "vector-cluster), combining Milestone 25/26 diagnostics with a new "
            "vector-containment signal, for manual inspection."
        ),
    )
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write CSV to this path instead of stdout.",
    )
    parser.add_argument(
        "--min-area-ratio",
        type=float,
        default=_DEFAULT_MIN_AREA_RATIO,
        help=f"Minimum page_area_ratio to include a row. Default: {_DEFAULT_MIN_AREA_RATIO}.",
    )
    parser.add_argument(
        "--max-area-ratio",
        type=float,
        default=_DEFAULT_MAX_AREA_RATIO,
        help=f"Maximum page_area_ratio to include a row. Default: {_DEFAULT_MAX_AREA_RATIO}.",
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
            min_area_ratio=args.min_area_ratio,
            max_area_ratio=args.max_area_ratio,
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
    min_area_ratio: float,
    max_area_ratio: float,
) -> list[dict[str, object]]:
    manual = pdf_path.name
    rows: list[dict[str, object]] = []

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
            primitive_page = normalize_backend_page_capture(capture)

            rows.extend(
                _raster_rows(
                    primitive_page,
                    manual=manual,
                    page_number=page_number,
                    min_area_ratio=min_area_ratio,
                    max_area_ratio=max_area_ratio,
                )
            )
            rows.extend(
                _vector_rows(
                    primitive_page,
                    manual=manual,
                    page_number=page_number,
                    min_area_ratio=min_area_ratio,
                    max_area_ratio=max_area_ratio,
                )
            )

    return rows


def _raster_rows(
    primitive_page: NormalizedPrimitivePage,
    *,
    manual: str,
    page_number: int,
    min_area_ratio: float,
    max_area_ratio: float,
) -> list[dict[str, object]]:
    diagnostics = dump_interior_visual_diagnostics(
        primitive_page,
        generation_id=f"diagnostic-interior-visual-diagnostics:{page_number - 1}",
    )
    rows: list[dict[str, object]] = []
    for visual in cast(list[object], diagnostics["visuals"]):
        entry = cast(dict[str, object], visual)
        if entry["primitive_kind"] != "image":
            continue
        if entry["is_residual_interior_visual"] is not True:
            continue
        page_area_ratio = cast(float | None, entry["page_area_ratio"])
        if page_area_ratio is None or not (min_area_ratio <= page_area_ratio <= max_area_ratio):
            continue

        bbox = cast(list[float], entry["visible_bbox"])
        rows.append(
            {
                "manual": manual,
                "page": page_number,
                "type": "raster",
                "bbox": tuple(bbox),
                "page_area_ratio": page_area_ratio,
                "contained_text_primitive_count": entry["contained_text_primitive_count"],
                "contained_text_area_ratio": entry["contained_text_area_ratio"],
                "dispersion_ratio": None,
                "primitive_ids": (cast(str, entry["primitive_id"]),),
            }
        )
    return rows


def _vector_rows(
    primitive_page: NormalizedPrimitivePage,
    *,
    manual: str,
    page_number: int,
    min_area_ratio: float,
    max_area_ratio: float,
) -> list[dict[str, object]]:
    diagnostics = dump_drawing_cluster_diagnostics(
        primitive_page,
        generation_id=f"diagnostic-drawing-cluster-diagnostics:{page_number - 1}",
    )
    rows: list[dict[str, object]] = []
    for cluster in cast(list[object], diagnostics["clusters"]):
        entry = cast(dict[str, object], cluster)
        if entry["excluded_reason"] is not None:
            continue
        if entry["is_residual_interior_visual"] is not True:
            continue
        page_area_ratio = cast(float | None, entry["page_area_ratio"])
        if page_area_ratio is None or not (min_area_ratio <= page_area_ratio <= max_area_ratio):
            continue

        bbox_list = cast(list[float], entry["bbox"])
        union_bbox = cast(BBox, tuple(bbox_list))
        contained_count, contained_ratio = _union_bbox_contained_text(union_bbox, primitive_page)
        primitive_ids = cast(list[str], entry["drawing_primitive_ids"])
        rows.append(
            {
                "manual": manual,
                "page": page_number,
                "type": "vector",
                "bbox": union_bbox,
                "page_area_ratio": page_area_ratio,
                "contained_text_primitive_count": contained_count,
                "contained_text_area_ratio": contained_ratio,
                "dispersion_ratio": entry["dispersion_ratio"],
                "primitive_ids": tuple(primitive_ids),
            }
        )
    return rows


def _union_bbox_contained_text(
    union_bbox: BBox,
    primitive_page: NormalizedPrimitivePage,
) -> tuple[int, float | None]:
    """Same containment/coverage logic as Milestone 25, on an arbitrary bbox."""

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    contained_count = 0
    contained_area = 0.0
    for text_primitive in primitive_page.text_primitives:
        text_visible_bbox = _visible_bbox(
            text_primitive.bbox, page_width=page_width, page_height=page_height
        )
        if text_visible_bbox is None:
            continue
        if not _contains(union_bbox, text_visible_bbox):
            continue
        contained_count += 1
        contained_area += (text_visible_bbox[2] - text_visible_bbox[0]) * (
            text_visible_bbox[3] - text_visible_bbox[1]
        )

    if contained_count == 0:
        return 0, None
    union_area = (union_bbox[2] - union_bbox[0]) * (union_bbox[3] - union_bbox[1])
    return contained_count, (contained_area / union_area if union_area > 0 else None)


def _contains(container: BBox, contained: BBox) -> bool:
    return (
        container[0] <= contained[0]
        and container[1] <= contained[1]
        and container[2] >= contained[2]
        and container[3] >= contained[3]
    )


def _visible_bbox(
    bbox: BBox,
    *,
    page_width: float,
    page_height: float,
) -> BBox | None:
    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1, y1)


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        bbox = cast(tuple[float, float, float, float], row["bbox"])
        primitive_ids = cast(tuple[str, ...], row["primitive_ids"])
        dispersion_ratio = row["dispersion_ratio"]
        contained_area_ratio = row["contained_text_area_ratio"]
        writer.writerow(
            [
                row["manual"],
                row["page"],
                row["type"],
                ";".join(str(value) for value in bbox),
                row["page_area_ratio"],
                row["contained_text_primitive_count"],
                "" if contained_area_ratio is None else contained_area_ratio,
                "" if dispersion_ratio is None else dispersion_ratio,
                ";".join(primitive_ids),
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
