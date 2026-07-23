"""Standalone diagnostics for table-candidate/TextPrimitive geometry rules."""

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

from page_analysis_model import RegionCandidate  # noqa: E402
from primitive_model import TextPrimitive  # noqa: E402
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


def _axis_gap(
    first_start: float, first_end: float, second_start: float, second_end: float
) -> float:
    if first_end < second_start:
        return second_start - first_end
    if second_end < first_start:
        return first_start - second_end
    return 0.0


def _overlap_ratio(
    candidate_bbox: tuple[float, float, float, float], primitive: TextPrimitive
) -> float:
    px0, py0, px1, py1 = primitive.bbox
    tx0, ty0, tx1, ty1 = candidate_bbox
    overlap_width = max(0.0, min(px1, tx1) - max(px0, tx0))
    overlap_height = max(0.0, min(py1, ty1) - max(py0, ty0))
    primitive_area = (px1 - px0) * (py1 - py0)
    if primitive_area <= 0.0:
        return 0.0
    return (overlap_width * overlap_height) / primitive_area


def _full_containment(
    candidate_bbox: tuple[float, float, float, float], primitive: TextPrimitive
) -> bool:
    px0, py0, px1, py1 = primitive.bbox
    tx0, ty0, tx1, ty1 = candidate_bbox
    return px0 >= tx0 and py0 >= ty0 and px1 <= tx1 and py1 <= ty1


def _center_in_bbox(
    candidate_bbox: tuple[float, float, float, float], primitive: TextPrimitive
) -> bool:
    px0, py0, px1, py1 = primitive.bbox
    tx0, ty0, tx1, ty1 = candidate_bbox
    center_x = (px0 + px1) / 2.0
    center_y = (py0 + py1) / 2.0
    return tx0 <= center_x <= tx1 and ty0 <= center_y <= ty1


def _primitive_entry(
    primitive: TextPrimitive, *, original_index: int, overlap_ratio: float
) -> dict[str, Any]:
    return {
        "primitive_id": primitive.primitive_id,
        "text": primitive.text,
        "bbox": list(primitive.bbox),
        "original_index": original_index,
        "overlap_ratio": overlap_ratio,
    }


def _candidate_report(
    candidate: RegionCandidate, text_primitives: tuple[TextPrimitive, ...]
) -> dict[str, Any]:
    full_containment: list[dict[str, Any]] = []
    center_in_bbox: list[dict[str, Any]] = []
    positive_intersection: list[dict[str, Any]] = []
    only_in_some_rules: list[dict[str, Any]] = []
    boundary_crossing: list[dict[str, Any]] = []
    nearest_external: list[dict[str, Any]] = []

    for original_index, primitive in enumerate(text_primitives):
        overlap_ratio = _overlap_ratio(candidate.bbox, primitive)
        entry = _primitive_entry(
            primitive,
            original_index=original_index,
            overlap_ratio=overlap_ratio,
        )
        included_rules: list[str] = []
        if _full_containment(candidate.bbox, primitive):
            full_containment.append(entry)
            included_rules.append("full_containment")
        if _center_in_bbox(candidate.bbox, primitive):
            center_in_bbox.append(entry)
            included_rules.append("center_in_bbox")
        if overlap_ratio > 0.0:
            positive_intersection.append(entry)
            included_rules.append("positive_intersection")

        if 0 < len(included_rules) < 3:
            only_in_some_rules.append({**entry, "rules": included_rules})
        if 0.0 < overlap_ratio < 1.0:
            boundary_crossing.append(entry)
        if overlap_ratio == 0.0:
            px0, py0, px1, py1 = primitive.bbox
            tx0, ty0, tx1, ty1 = candidate.bbox
            horizontal_gap = _axis_gap(tx0, tx1, px0, px1)
            vertical_gap = _axis_gap(ty0, ty1, py0, py1)
            nearest_external.append(
                {
                    **entry,
                    "horizontal_gap": horizontal_gap,
                    "vertical_gap": vertical_gap,
                }
            )

    nearest_external.sort(key=lambda entry: max(entry["horizontal_gap"], entry["vertical_gap"]))
    return {
        "candidate_id": candidate.candidate_id,
        "bbox": list(candidate.bbox),
        "full_containment": full_containment,
        "center_in_bbox": center_in_bbox,
        "positive_intersection": positive_intersection,
        "only_in_some_rules": only_in_some_rules,
        "boundary_crossing": boundary_crossing,
        "nearest_external": nearest_external,
        "orphan": not positive_intersection,
    }


def run(pdf_path: Path, page_number: int, generation_id: str) -> None:
    """Report independent table-candidate/TextPrimitive rule memberships."""

    del generation_id
    result: dict[str, Any] = {
        "input": {
            "pdf_path": str(pdf_path),
            "page_number": page_number,
        }
    }
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
                        candidate_id=f"candidate:prototype-table:text-lines:{raw_index:04d}",
                        page_id=primitive_page.page_id,
                        bbox=cast(
                            tuple[float, float, float, float],
                            tuple(float(coordinate) for coordinate in table.bbox),
                        ),
                        proposed_structural_kind="layout.table",
                        primitive_ids=(),
                    )
                )
            candidate_reports: list[dict[str, Any]] = []
            result["candidates"] = candidate_reports
            for candidate in candidates:
                candidate_reports.append(
                    _candidate_report(candidate, primitive_page.text_primitives)
                )
    except SystemExit:
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
