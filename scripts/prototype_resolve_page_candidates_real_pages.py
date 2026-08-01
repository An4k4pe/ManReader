"""Standalone validation prototype for resolve_page_candidates on real pages.

Runs embedded_visual and interior_visual_frame (defaults only, same as the
job runner) against one real PyMuPDF-captured page, binds the two analyses
into a CoReferencedPageAnalyses, and reports what resolve_page_candidates
decides. No pdfplumber (both producers have requires_pdfplumber=False), no
job/workspace, no persistence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from page_analysis_model import PageAnalysis  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_page_candidates import resolve_page_candidates  # noqa: E402
from verified_file_model import inspect_verified_bytes  # noqa: E402


def _rect_to_list(rect: fitz.Rect) -> list[float]:
    return [float(coordinate) for coordinate in rect]


def _print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def _precondition_fail(result: dict[str, Any], message: str) -> None:
    result["category"] = "PRECONDITION_FAIL"
    result["message"] = message
    _print_result(result)
    sys.exit(3)


def _analysis_report(analysis: PageAnalysis) -> dict[str, Any]:
    return {
        "candidate_count": len(analysis.candidates),
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "bbox": list(candidate.bbox),
                "primitive_ids": list(candidate.primitive_ids),
            }
            for candidate in analysis.candidates
        ],
    }


def run(pdf_path: Path, page_number: int, generation_id: str) -> None:
    """Run the prototype for one one-based page number."""

    result: dict[str, Any] = {
        "input": {
            "pdf_path": str(pdf_path),
            "page_number": page_number,
        },
    }

    validation_failed = False
    try:
        pdf_bytes = pdf_path.read_bytes()
        verified_bytes = inspect_verified_bytes(pdf_bytes)
        source_id = verified_bytes.sha256
        result["input"]["sha256"] = source_id
        result["input"]["size_bytes"] = verified_bytes.size_bytes
        result["versions"] = {"fitz": fitz.VersionBind}

        with fitz.open(stream=pdf_bytes, filetype="pdf") as fitz_document:
            result["input"]["page_count"] = fitz_document.page_count
            if not 1 <= page_number <= fitz_document.page_count:
                _precondition_fail(result, "page_number out of range")

            page_index = page_number - 1
            page = fitz_document.load_page(page_index)
            result["fitz"] = {
                "page_index": page_index,
                "width": float(page.rect.width),
                "height": float(page.rect.height),
                "rotation": page.rotation,
                "mediabox": _rect_to_list(page.mediabox),
                "cropbox": _rect_to_list(page.cropbox),
                "page.rect": _rect_to_list(page.rect),
            }
            if page.rotation != 0:
                _precondition_fail(result, "rotation must be 0")
            if page.mediabox != page.cropbox:
                _precondition_fail(result, "cropbox != mediabox")

            capture = capture_pymupdf_page(
                page,
                source_id=source_id,
                page_id=f"page:{page_number:04d}",
                capture_id=f"prototype:pymupdf:page:{page_number:04d}",
            )
            primitive_page = normalize_backend_page_capture(capture)

            embedded_analysis = build_embedded_visual_page_analysis(
                primitive_page,
                generation_id=generation_id,
            )
            frame_analysis = build_interior_visual_frame_page_analysis(
                primitive_page,
                generation_id=generation_id,
            )

            result["embedded_visual"] = _analysis_report(embedded_analysis)
            result["interior_visual_frame"] = _analysis_report(frame_analysis)

            try:
                co_referenced = build_co_referenced_page_analyses(
                    (embedded_analysis, frame_analysis)
                )
                bound = bind_co_referenced_page_analyses(
                    primitive_page,
                    co_referenced_page_analyses=co_referenced,
                )
            except ValueError as exc:
                validation_failed = True
                result["category"] = "VALIDATION_FAIL"
                result["message"] = str(exc)
                _print_result(result)
                raise

            resolved = resolve_page_candidates(bound)
            result["resolution"] = [
                {
                    "producer_name": outcome.candidate_reference.producer_name,
                    "candidate_id": outcome.candidate_reference.candidate_id,
                    "outcome": outcome.outcome,
                    "reason_token": outcome.reason_token,
                }
                for outcome in resolved.outcomes
            ]
    except SystemExit:
        raise
    except ValueError as exc:
        if validation_failed:
            raise
        result["category"] = "OPERATIONAL_ERROR"
        result["message"] = str(exc)
        _print_result(result)
        raise
    except Exception as exc:
        result["category"] = "OPERATIONAL_ERROR"
        result["message"] = str(exc)
        _print_result(result)
        raise

    result["category"] = "PASS"
    _print_result(result)


def _non_empty_string(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("generation_id must be a non-empty string")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("page_number", type=int)
    parser.add_argument("--generation-id", required=True, type=_non_empty_string)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.pdf_path, args.page_number, args.generation_id)


if __name__ == "__main__":
    main()
