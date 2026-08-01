"""Exploratory scan: table x interior-visual overlap ratio spectrum, whole manual.

Proposta_ResolutionDesign_v3.md §8.2.2 (table x box), precondition for any
future threshold: no threshold is chosen before seeing the real distribution.
This script collects every positive-overlap pair between a layout.table
candidate and an embedded_visual/interior_visual_frame candidate on the same
page, using measure_co_referenced_page_candidate_overlap_ratio (unmodified).
It does not filter, bin, or categorize anything -- raw numbers only.

Not a producer, not wired anywhere, no persistence. A failed page guard or a
ValueError from one of the three producers skips that page and continues:
scanning the whole manual is the point, not stopping at the first oddity.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any, cast

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_candidate_overlap_ratio_measurements import (  # noqa: E402
    measure_co_referenced_page_candidate_overlap_ratio,
)
from page_analysis_co_reference_candidate_reference import (  # noqa: E402
    build_co_referenced_page_candidate_reference,
)
from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from page_analysis_model import PageAnalysis, RegionCandidate  # noqa: E402
from page_analysis_table_candidate import build_table_candidate_page_analysis  # noqa: E402
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from verified_file_model import inspect_verified_bytes  # noqa: E402

_TABLE_STRUCTURAL_KIND = "layout.table"
_EMBEDDED_VISUAL_STRUCTURAL_KIND = "layout.embedded_visual"
_INTERIOR_VISUAL_FRAME_STRUCTURAL_KIND = "layout.interior_visual_frame"


def _candidates_of_kind(
    analysis: PageAnalysis,
    structural_kind: str,
) -> tuple[RegionCandidate, ...]:
    return tuple(
        candidate
        for candidate in analysis.candidates
        if candidate.proposed_structural_kind == structural_kind
    )


def _pair_reports(
    bound: Any,
    *,
    page_number: int,
    table_analysis: PageAnalysis,
    table_candidates: tuple[RegionCandidate, ...],
    box_analysis: PageAnalysis,
    box_candidates: tuple[RegionCandidate, ...],
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for table_candidate in table_candidates:
        table_reference = build_co_referenced_page_candidate_reference(
            bound,
            analysis=table_analysis,
            candidate=table_candidate,
        )
        for box_candidate in box_candidates:
            box_reference = build_co_referenced_page_candidate_reference(
                bound,
                analysis=box_analysis,
                candidate=box_candidate,
            )
            measurement = measure_co_referenced_page_candidate_overlap_ratio(
                bound,
                first_candidate_reference=table_reference,
                second_candidate_reference=box_reference,
            )
            if measurement.overlap_ratio > 0.0:
                pairs.append(
                    {
                        "page_number": page_number,
                        "table_candidate_id": table_candidate.candidate_id,
                        "table_bbox": list(table_candidate.bbox),
                        "box_candidate_id": box_candidate.candidate_id,
                        "box_bbox": list(box_candidate.bbox),
                        "overlap_ratio": measurement.overlap_ratio,
                    }
                )
    return pairs


def scan(pdf_path: Path) -> dict[str, Any]:
    pdf_bytes = pdf_path.read_bytes()
    verified_bytes = inspect_verified_bytes(pdf_bytes)
    source_id = verified_bytes.sha256

    pages_skipped: list[dict[str, Any]] = []
    pages_with_errors: list[dict[str, Any]] = []
    pages_scanned = 0
    total_table_candidates = 0
    total_embedded_visual_candidates = 0
    total_interior_visual_frame_candidates = 0
    table_x_embedded_visual_pairs: list[dict[str, Any]] = []
    table_x_interior_visual_frame_pairs: list[dict[str, Any]] = []

    with (
        fitz.open(stream=pdf_bytes, filetype="pdf") as fitz_document,
        pdfplumber.open(io.BytesIO(pdf_bytes)) as plumber_pdf,
    ):
        page_count = fitz_document.page_count

        for page_number in range(1, page_count + 1):
            page_index = page_number - 1
            page = fitz_document.load_page(page_index)

            if page.rotation != 0:
                pages_skipped.append({"page_number": page_number, "reason": "rotation"})
                continue
            if page.mediabox != page.cropbox:
                pages_skipped.append(
                    {"page_number": page_number, "reason": "cropbox_mismatch"}
                )
                continue

            generation_id = f"scan-table-box:page:{page_number:04d}"
            try:
                capture = capture_pymupdf_page(
                    page,
                    source_id=source_id,
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"scan-table-box:pymupdf:page:{page_number:04d}",
                )
                primitive_page = normalize_backend_page_capture(capture)

                table_analysis = build_table_candidate_page_analysis(
                    BoundTableCandidatePage(
                        primitive_page=primitive_page,
                        plumber_page=plumber_pdf.pages[page_index],
                    ),
                    generation_id=generation_id,
                )
                embedded_analysis = build_embedded_visual_page_analysis(
                    primitive_page,
                    generation_id=generation_id,
                )
                frame_analysis = build_interior_visual_frame_page_analysis(
                    primitive_page,
                    generation_id=generation_id,
                )
            except ValueError as exc:
                pages_with_errors.append({"page_number": page_number, "message": str(exc)})
                continue

            pages_scanned += 1

            table_candidates = _candidates_of_kind(table_analysis, _TABLE_STRUCTURAL_KIND)
            embedded_candidates = _candidates_of_kind(
                embedded_analysis, _EMBEDDED_VISUAL_STRUCTURAL_KIND
            )
            frame_candidates = _candidates_of_kind(
                frame_analysis, _INTERIOR_VISUAL_FRAME_STRUCTURAL_KIND
            )

            total_table_candidates += len(table_candidates)
            total_embedded_visual_candidates += len(embedded_candidates)
            total_interior_visual_frame_candidates += len(frame_candidates)

            if not table_candidates or not embedded_candidates:
                continue

            co_referenced = build_co_referenced_page_analyses(
                (table_analysis, embedded_analysis, frame_analysis)
            )
            bound = bind_co_referenced_page_analyses(
                primitive_page,
                co_referenced_page_analyses=co_referenced,
            )

            table_x_embedded_visual_pairs.extend(
                _pair_reports(
                    bound,
                    page_number=page_number,
                    table_analysis=table_analysis,
                    table_candidates=table_candidates,
                    box_analysis=embedded_analysis,
                    box_candidates=embedded_candidates,
                )
            )
            table_x_interior_visual_frame_pairs.extend(
                _pair_reports(
                    bound,
                    page_number=page_number,
                    table_analysis=table_analysis,
                    table_candidates=table_candidates,
                    box_analysis=frame_analysis,
                    box_candidates=frame_candidates,
                )
            )

    return {
        "input": {
            "pdf_path": str(pdf_path),
            "page_count": page_count,
            "sha256": source_id,
            "size_bytes": verified_bytes.size_bytes,
        },
        "pages_scanned": pages_scanned,
        "pages_skipped": pages_skipped,
        "pages_with_errors": pages_with_errors,
        "totals": {
            "table_candidates": total_table_candidates,
            "embedded_visual_candidates": total_embedded_visual_candidates,
            "interior_visual_frame_candidates": total_interior_visual_frame_candidates,
        },
        "table_x_embedded_visual_pairs": table_x_embedded_visual_pairs,
        "table_x_interior_visual_frame_pairs": table_x_interior_visual_frame_pairs,
        "table_x_embedded_visual_overlap_ratios_sorted": sorted(
            cast(float, pair["overlap_ratio"]) for pair in table_x_embedded_visual_pairs
        ),
        "table_x_interior_visual_frame_overlap_ratios_sorted": sorted(
            cast(float, pair["overlap_ratio"])
            for pair in table_x_interior_visual_frame_pairs
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = scan(args.pdf_path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
