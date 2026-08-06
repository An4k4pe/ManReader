"""Exploratory, diagnostic-only check of one hypothesis, pre-registered here
before running it on any manual beyond the one that produced it:

  H: when a column-count>=2 band's persistent gap does not agree with the
  page's own established gutter, that disagreement co-occurs with an
  embedded_visual or interior_visual_frame candidate (Milestone 27/30)
  overlapping the band, at a higher rate than for bands whose gap DOES
  agree with the gutter.

Origin case (must reproduce, or the measure is wrong, not the hypothesis):
DB.pdf, page 26 (1-indexed page argument, i.e. PDF page_index 25 -- printed
page 24, +2 offset confirmed separately), band index 6 (rows 11-15,
y 584.0-774.5): column_count=2, gaps (221.0,232.0,0.60) and
(276.0,314.0,0.78), neither matching the page's own gutter established by
band 0 (298.0,315.0,1.00) and band 4 (297.0,315.0,1.00). The "ALTRI METODI"
box sits in the left half of that band.

Falsification criterion, fixed before running on Kul.pdf/Fab.pdf: if, on
Fab.pdf and Kul.pdf (the two manuals already documented in Milestone 29 as
having frequent box-like interior visuals -- scripts/scan_interior_visual_frame_diagnostics.py),
the overlap rate with embedded_visual/interior_visual_frame candidates is
NOT higher for deviant (non-aligned) bands than for aligned bands, the
hypothesis is retracted for this mechanism, not re-fitted with a different
threshold. No manual besides Fab/Kul is required to retract; agreement on
other manuals does not rescue a failure on these two, per the lesson
registered in State.md about criteria that do not bind the case they were
built to explain.

Definitions (fixed, not tuned per manual):

  - "page reference gutter": among all gaps, in bands with
    column_count >= 2, whose support_ratio >= 0.95, the (start, end)
    interval whose midpoint is closest to the median midpoint of all such
    intervals on the page. A page with no gap reaching 0.95 support
    contributes no reference and its bands are recorded as unclassifiable,
    not silently dropped and not counted as either aligned or deviant.
  - a band is "aligned" if at least one of its own gaps has
    support_ratio >= 0.95 AND overlaps the page reference gutter by at
    least 50% of the gap's own width. Otherwise "deviant".
  - a band "overlaps" a candidate (embedded_visual or
    interior_visual_frame, computed separately, reported separately) if the
    candidate's bbox has any vertical (y) overlap with the band's
    [y0, y1]. Coarser than a true geometric overlap ratio (Milestone
    13-19 has a real one) on purpose: this is a first pass to see if the
    signal exists at all before spending the more expensive measure on it.

Not a producer. Not wired anywhere. No RegionCandidate emitted, no
structural_kind, no threshold ratified. Reuses
_cluster_rows/_segment_column_bands (Milestone 32) and
build_embedded_visual_page_analysis/build_interior_visual_frame_page_analysis
(Milestone 27/30) unchanged, no copies.
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

from scan_column_structure_diagnostics import (  # noqa: E402
    _cluster_rows,
    _segment_column_bands,
    _visible_bbox,
)

from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6
_REFERENCE_MIN_SUPPORT = 0.95
_ALIGNMENT_MIN_SUPPORT = 0.95
_ALIGNMENT_OVERLAP_FRACTION = 0.5

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "band_index",
    "column_count",
    "y0",
    "y1",
    "gaps",
    "reference_gutter",
    "alignment",
    "overlaps_embedded_visual",
    "overlaps_interior_visual_frame",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
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

    rows = list(
        _scan_document(
            pdf_path,
            bin_width=args.bin_width,
            min_gap_width=args.min_gap_width,
            min_support_ratio=args.min_support_ratio,
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
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
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

            visible_bboxes = []
            for text_primitive in primitive_page.text_primitives:
                visible_bbox = _visible_bbox(
                    text_primitive.bbox, page_width=page_width, page_height=page_height
                )
                if visible_bbox is not None:
                    visible_bboxes.append(visible_bbox)

            clustered_rows = _cluster_rows(visible_bboxes)
            bands = _segment_column_bands(
                clustered_rows,
                page_width=page_width,
                bin_width=bin_width,
                min_gap_width=min_gap_width,
                min_support_ratio=min_support_ratio,
            )

            indexed_multi_column_bands = [
                (band_index, band)
                for band_index, band in enumerate(bands)
                if band["column_count"] >= 2
            ]
            if not indexed_multi_column_bands:
                continue
            multi_column_bands = [band for _band_index, band in indexed_multi_column_bands]

            generation_id = f"diagnostic-generation:{page_index}"
            embedded_visual_candidates = build_embedded_visual_page_analysis(
                primitive_page, generation_id=generation_id
            ).candidates
            interior_visual_frame_candidates = build_interior_visual_frame_page_analysis(
                primitive_page, generation_id=generation_id
            ).candidates

            reference = _page_reference_gutter(multi_column_bands)

            for band_index, band in indexed_multi_column_bands:
                if reference is None:
                    alignment = "unclassifiable"
                else:
                    alignment = "aligned" if _band_is_aligned(band, reference) else "deviant"

                output_rows.append(
                    {
                        "manual": manual,
                        "page": page_number,
                        "band_index": band_index,
                        "column_count": band["column_count"],
                        "y0": band["y0"],
                        "y1": band["y1"],
                        "gaps": tuple(band["gaps"]),
                        "reference_gutter": reference,
                        "alignment": alignment,
                        "overlaps_embedded_visual": _band_overlaps_any(
                            band, embedded_visual_candidates
                        ),
                        "overlaps_interior_visual_frame": _band_overlaps_any(
                            band, interior_visual_frame_candidates
                        ),
                    }
                )

    return output_rows


def _page_reference_gutter(
    multi_column_bands: list[dict[str, object]],
) -> tuple[float, float] | None:
    candidates: list[tuple[float, float]] = []
    for band in multi_column_bands:
        for start, end, ratio in band["gaps"]:  # type: ignore[misc]
            if ratio >= _REFERENCE_MIN_SUPPORT:
                candidates.append((start, end))

    if not candidates:
        return None

    midpoints = sorted((start + end) / 2 for start, end in candidates)
    median = statistics.median(midpoints)
    best_index = min(
        range(len(candidates)),
        key=lambda i: (abs(((candidates[i][0] + candidates[i][1]) / 2) - median), i),
    )
    return candidates[best_index]


def _overlap_fraction(gap: tuple[float, float], reference: tuple[float, float]) -> float:
    start, end = gap
    ref_start, ref_end = reference
    intersection = max(0.0, min(end, ref_end) - max(start, ref_start))
    width = end - start
    return intersection / width if width > 0 else 0.0


def _band_is_aligned(band: dict[str, object], reference: tuple[float, float]) -> bool:
    for start, end, ratio in band["gaps"]:  # type: ignore[misc]
        if ratio >= _ALIGNMENT_MIN_SUPPORT and (
            _overlap_fraction((start, end), reference) >= _ALIGNMENT_OVERLAP_FRACTION
        ):
            return True
    return False


def _band_overlaps_any(band: dict[str, object], candidates: tuple[object, ...]) -> bool:
    band_y0 = cast(float, band["y0"])
    band_y1 = cast(float, band["y1"])
    for region_candidate in candidates:
        _cx0, cy0, _cx1, cy1 = region_candidate.bbox  # type: ignore[attr-defined]
        if cy0 < band_y1 and cy1 > band_y0:
            return True
    return False


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        gaps = cast(tuple[tuple[float, float, float], ...], row["gaps"])
        reference = cast(tuple[float, float] | None, row["reference_gutter"])
        writer.writerow(
            [
                row["manual"],
                row["page"],
                row["band_index"],
                row["column_count"],
                f"{cast(float, row['y0']):.1f}",
                f"{cast(float, row['y1']):.1f}",
                ";".join(f"{s:.1f}:{e:.1f}:{r:.2f}" for s, e, r in gaps),
                f"{reference[0]:.1f}:{reference[1]:.1f}" if reference is not None else "",
                row["alignment"],
                row["overlaps_embedded_visual"],
                row["overlaps_interior_visual_frame"],
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
