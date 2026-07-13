"""Diagnostic JSON dump for PyMuPDF shadow capture and normalization.

This tool is intentionally disconnected from ManReader's legacy pipeline.
It opens one PDF page and can serialize the raw ``BackendPageCapture``,
the derived ``NormalizedPrimitivePage``, a primitive-extent ``PageAnalysis``,
or singleton/local-fragment side-band ``PageAnalysis`` values, page-covering
visual and page-edge visual ``PageAnalysis`` values, explicit primitive-pair
measurements, or primitive-neighborhood measurements, to stdout or to an
explicitly requested file.

The generated identifiers are diagnostic placeholders. They do not establish
the canonical identity policy for future workspace artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import fitz

from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from page_analysis_primitive_extent import build_primitive_extent_page_analysis
from page_analysis_primitive_pair_measurements import (
    PrimitivePairMeasurements,
    measure_primitive_pair,
)
from page_analysis_serialization import page_analysis_to_dict
from page_analysis_side_band import (
    build_local_fragment_side_band_page_analysis,
    build_singleton_side_band_page_analysis,
)
from primitive_model import NormalizedPrimitivePage
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page

type DiagnosticStage = Literal[
    "capture",
    "primitives",
    "analysis",
    "analysis-side-band",
    "analysis-side-band-local-fragment",
    "analysis-page-edge-visual",
    "analysis-page-covering-visual",
    "primitive-pair",
    "primitive-neighborhood",
]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dump one PyMuPDF shadow page as diagnostic JSON.",
    )
    parser.add_argument(
        "pdf",
        type=Path,
        help="PDF file to inspect.",
    )
    parser.add_argument(
        "--page",
        type=_positive_page_number,
        default=1,
        help="One-based PDF page number. Default: 1.",
    )
    parser.add_argument(
        "--stage",
        choices=(
            "capture",
            "primitives",
            "analysis",
            "analysis-side-band",
            "analysis-side-band-local-fragment",
            "analysis-page-edge-visual",
            "analysis-page-covering-visual",
            "primitive-pair",
            "primitive-neighborhood",
        ),
        default="capture",
        help="Diagnostic stage to serialize. Default: capture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of stdout.",
    )
    parser.add_argument(
        "--render-page-image",
        type=Path,
        help="Render the analyzed PDF page as a PNG to this path.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    parser.add_argument(
        "--first-primitive-id",
        help="First primitive ID; required for stage primitive-pair.",
    )
    parser.add_argument(
        "--second-primitive-id",
        help="Second primitive ID; required for stage primitive-pair.",
    )
    parser.add_argument(
        "--primitive-id",
        help="Primitive ID; required for stage primitive-neighborhood.",
    )
    return parser


def dump_capture(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture one page and return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="capture",
        output_path=output_path,
        compact=compact,
    )


def dump_normalized_primitives(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture and normalize one page, then return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="primitives",
        output_path=output_path,
        compact=compact,
    )


def dump_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, build primitive-extent analysis, then return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis",
        output_path=output_path,
        compact=compact,
    )


def dump_singleton_side_band_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return singleton side-band analysis JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis-side-band",
        output_path=output_path,
        compact=compact,
    )


def dump_local_fragment_side_band_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return local-fragment side-band analysis JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis-side-band-local-fragment",
        output_path=output_path,
        compact=compact,
    )


def dump_page_covering_visual_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return page-covering visual analysis JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis-page-covering-visual",
        output_path=output_path,
        compact=compact,
    )


def dump_page_edge_visual_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return page-edge visual analysis JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis-page-edge-visual",
        output_path=output_path,
        compact=compact,
    )


def dump_primitive_pair_measurements(
    pdf_path: Path,
    *,
    first_primitive_id: str,
    second_primitive_id: str,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return explicit primitive-pair measurement JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="primitive-pair",
        output_path=output_path,
        compact=compact,
        first_primitive_id=first_primitive_id,
        second_primitive_id=second_primitive_id,
    )


def dump_primitive_neighborhood_measurements(
    pdf_path: Path,
    *,
    primitive_id: str,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return explicit primitive-neighborhood JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="primitive-neighborhood",
        output_path=output_path,
        compact=compact,
        primitive_id=primitive_id,
    )


def _dump_page(
    pdf_path: Path,
    *,
    page_number: int,
    stage: DiagnosticStage,
    output_path: Path | None,
    compact: bool,
    first_primitive_id: str | None = None,
    second_primitive_id: str | None = None,
    primitive_id: str | None = None,
    render_page_image_path: Path | None = None,
) -> str:
    """Serialize one diagnostic stage for a one-based PDF page number."""

    if page_number < 1:
        raise ValueError("page_number must be greater than or equal to 1")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    page_index = page_number - 1
    with fitz.open(pdf_path) as document:
        if page_index >= document.page_count:
            raise ValueError(
                f"page {page_number} is outside the document (page count: {document.page_count})"
            )
        page = document.load_page(page_index)
        if render_page_image_path is not None:
            _render_page_image(page, render_page_image_path)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"diagnostic-page:{page_index}",
            capture_id=f"diagnostic-pymupdf-capture:{page_index}",
        )

    if stage == "capture":
        artifact_data = asdict(capture)
    elif stage == "primitives":
        primitive_page = normalize_backend_page_capture(capture)
        artifact_data = asdict(primitive_page)
    elif stage == "analysis":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_primitive_extent_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-page-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    elif stage == "analysis-side-band":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_singleton_side_band_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-singleton-side-band-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    elif stage == "analysis-side-band-local-fragment":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_local_fragment_side_band_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-local-fragment-side-band-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    elif stage == "analysis-page-covering-visual":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_page_covering_visual_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-page-covering-visual-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    elif stage == "analysis-page-edge-visual":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_page_edge_visual_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-page-edge-visual-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    elif stage == "primitive-pair":
        if first_primitive_id is None:
            raise ValueError("first_primitive_id is required for stage primitive-pair")
        if second_primitive_id is None:
            raise ValueError("second_primitive_id is required for stage primitive-pair")
        primitive_page = normalize_backend_page_capture(capture)
        artifact_data = asdict(
            measure_primitive_pair(
                primitive_page,
                first_primitive_id=first_primitive_id,
                second_primitive_id=second_primitive_id,
            )
        )
    else:
        if primitive_id is None:
            raise ValueError("primitive_id is required for stage primitive-neighborhood")
        primitive_page = normalize_backend_page_capture(capture)
        artifact_data = _primitive_neighborhood_data(
            primitive_page,
            primitive_id=primitive_id,
        )

    json_text = json.dumps(
        artifact_data,
        ensure_ascii=False,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
    )
    if not compact:
        json_text += "\n"

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")

    return json_text


def _render_page_image(page: fitz.Page, output_path: Path) -> None:
    """Render one PDF page as a PNG side-output for diagnostics."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(page.get_pixmap().tobytes("png"))


def _primitive_neighborhood_data(
    primitive_page: NormalizedPrimitivePage,
    *,
    primitive_id: str,
) -> dict[str, object]:
    """Measure one explicit primitive against every visible page neighbor."""

    primitive_ids = _primitive_ids(primitive_page)
    if primitive_id not in primitive_ids:
        raise ValueError(f"primitive_id does not exist: {primitive_id}")

    neighbor_measurements: list[PrimitivePairMeasurements] = []
    for second_primitive_id in primitive_ids:
        if second_primitive_id == primitive_id:
            continue
        try:
            measurements = measure_primitive_pair(
                primitive_page,
                first_primitive_id=primitive_id,
                second_primitive_id=second_primitive_id,
            )
        except ValueError as exc:
            if _is_no_visible_intersection_error(
                exc,
                primitive_id=second_primitive_id,
            ):
                continue
            raise
        neighbor_measurements.append(measurements)

    neighbor_measurements.sort(key=_primitive_neighborhood_sort_key)
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    return {
        "primitive_id": primitive_id,
        "page_id": primitive_page.page_id,
        "neighbors": [
            {
                "primitive_id": measurements.second_primitive_id,
                "primitive_kind": measurements.second_primitive_kind,
                "measurements": asdict(measurements),
                **_primitive_neighborhood_coverage_ratios(
                    measurements,
                    page_width=page_width,
                    page_height=page_height,
                ),
            }
            for measurements in neighbor_measurements
        ],
    }


def _primitive_ids(primitive_page: NormalizedPrimitivePage) -> tuple[str, ...]:
    """Return all normalized primitive IDs in their canonical family order."""

    return tuple(
        primitive.primitive_id
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    )


def _is_no_visible_intersection_error(
    exc: ValueError,
    *,
    primitive_id: str,
) -> bool:
    return str(exc) == f"primitive has no visible intersection with the page: {primitive_id}"


def _primitive_neighborhood_sort_key(
    measurements: PrimitivePairMeasurements,
) -> tuple[bool, float, float, float, str]:
    return (
        measurements.is_disjoint,
        measurements.horizontal_gap + measurements.vertical_gap,
        measurements.second_visible_bbox[1],
        measurements.second_visible_bbox[0],
        measurements.second_primitive_id,
    )


def _primitive_neighborhood_coverage_ratios(
    measurements: PrimitivePairMeasurements,
    *,
    page_width: float,
    page_height: float,
) -> dict[str, float]:
    """Return page-coverage ratios from already measured visible bounding boxes."""

    first_width = measurements.first_visible_bbox[2] - measurements.first_visible_bbox[0]
    first_height = measurements.first_visible_bbox[3] - measurements.first_visible_bbox[1]
    neighbor_width = measurements.second_visible_bbox[2] - measurements.second_visible_bbox[0]
    neighbor_height = measurements.second_visible_bbox[3] - measurements.second_visible_bbox[1]
    page_area = page_width * page_height
    return {
        "first_visible_width_ratio": first_width / page_width,
        "first_visible_height_ratio": first_height / page_height,
        "first_visible_area_ratio": (first_width * first_height) / page_area,
        "neighbor_visible_width_ratio": neighbor_width / page_width,
        "neighbor_visible_height_ratio": neighbor_height / page_height,
        "neighbor_visible_area_ratio": (neighbor_width * neighbor_height) / page_area,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if args.stage == "primitive-pair":
        if args.first_primitive_id is None:
            parser.error("--first-primitive-id is required for stage primitive-pair")
        if args.second_primitive_id is None:
            parser.error("--second-primitive-id is required for stage primitive-pair")
    if args.stage == "primitive-neighborhood" and args.primitive_id is None:
        parser.error("--primitive-id is required for stage primitive-neighborhood")

    try:
        json_text = _dump_page(
            args.pdf,
            page_number=args.page,
            stage=args.stage,
            output_path=args.output,
            compact=args.compact,
            first_primitive_id=args.first_primitive_id,
            second_primitive_id=args.second_primitive_id,
            primitive_id=args.primitive_id,
            render_page_image_path=args.render_page_image,
        )
    except (FileNotFoundError, OSError, ValueError, fitz.FileDataError) as exc:
        parser.error(str(exc))

    if args.output is None:
        sys.stdout.write(json_text)
    else:
        print(
            f"Wrote PyMuPDF shadow {args.stage} for page {args.page} to {args.output}",
            file=sys.stderr,
        )
    return 0


def _positive_page_number(value: str) -> int:
    try:
        page_number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("page must be an integer") from exc
    if page_number < 1:
        raise argparse.ArgumentTypeError("page must be greater than or equal to 1")
    return page_number


if __name__ == "__main__":
    raise SystemExit(main())
