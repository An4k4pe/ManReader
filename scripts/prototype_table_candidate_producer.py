"""Standalone validation prototype for pdfplumber text/lines table candidates."""

from __future__ import annotations

import argparse
import io
import json
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from page_analysis_model import (  # noqa: E402
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from verified_file_model import inspect_verified_bytes  # noqa: E402

_TEXT_LINES_TABLE_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "lines",
}


def _rect_to_list(rect: fitz.Rect) -> list[float]:
    return [float(coordinate) for coordinate in rect]


def _print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def _precondition_fail(result: dict[str, Any], message: str) -> None:
    result["category"] = "PRECONDITION_FAIL"
    result["message"] = message
    _print_result(result)
    sys.exit(3)


def _table_has_non_whitespace_cell(table: Any) -> bool:
    extracted = table.extract()
    return any(isinstance(cell, str) and cell.strip() for row in extracted for cell in row)


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
        result["versions"] = {
            "fitz": fitz.VersionBind,
            "pdfplumber": version("pdfplumber"),
        }
        with (
            fitz.open(stream=pdf_bytes, filetype="pdf") as fitz_document,
            pdfplumber.open(io.BytesIO(pdf_bytes)) as plumber_pdf,
        ):
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

            plumber_page = plumber_pdf.pages[page_index]
            result["pdfplumber"] = {
                "width": float(plumber_page.width),
                "height": float(plumber_page.height),
                "rotation": plumber_page.rotation,
                "mediabox": plumber_page.mediabox,
                "cropbox": plumber_page.cropbox,
                "bbox": plumber_page.bbox,
            }

            capture = capture_pymupdf_page(
                page,
                source_id=source_id,
                page_id=f"page:{page_number:04d}",
                capture_id=f"prototype:pymupdf:page:{page_number:04d}",
            )
            primitive_page = normalize_backend_page_capture(capture)
            tables = plumber_page.find_tables(table_settings=_TEXT_LINES_TABLE_SETTINGS)
            excluded_empty_raw_indices: list[int] = []
            candidates: list[RegionCandidate] = []
            result["detection"] = {
                "total_raw_tables": len(tables),
                "excluded_empty_raw_indices": excluded_empty_raw_indices,
            }
            for raw_index, table in enumerate(tables, start=0):
                if not _table_has_non_whitespace_cell(table):
                    excluded_empty_raw_indices.append(raw_index)
                    continue
                candidates.append(
                    RegionCandidate(
                        candidate_id=(f"candidate:prototype-table:text-lines:{raw_index:04d}"),
                        page_id=primitive_page.page_id,
                        bbox=cast(
                            tuple[float, float, float, float],
                            tuple(float(coordinate) for coordinate in table.bbox),
                        ),
                        proposed_structural_kind="layout.table",
                        primitive_ids=(),
                    )
                )

            result["candidates"] = [
                {"candidate_id": candidate.candidate_id, "bbox": list(candidate.bbox)}
                for candidate in candidates
            ]
            provenance = PageAnalysisProvenance(
                source_id=primitive_page.source_id,
                source_capture_id=primitive_page.source_capture_id,
                source_page_id=primitive_page.page_id,
                source_primitive_schema_version=primitive_page.schema_version,
                producer_name="prototype.pdfplumber_table_candidate",
                producer_version="0.1",
                configuration_id="pdfplumber-text-lines-v1",
            )
            analysis = PageAnalysis(
                schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
                generation_id=generation_id,
                page_id=primitive_page.page_id,
                provenance=provenance,
                regions=(),
                relations=(),
                candidates=tuple(candidates),
            )
            try:
                validate_page_analysis_against_primitive_page(analysis, primitive_page)
            except ValueError as exc:
                validation_failed = True
                result["category"] = "VALIDATION_FAIL"
                result["message"] = str(exc)
                _print_result(result)
                raise
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
