"""Production table-candidate producer for an already opened pdfplumber page."""

from __future__ import annotations

import logging
from typing import Any, cast

from page_analysis_candidate_primitive_overlap_measurements import (
    measure_candidate_primitive_overlap_ratio,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_table_candidate_binding import BoundTableCandidatePage
from page_analysis_validate import validate_page_analysis_against_primitive_page

_TEXT_LINES_TABLE_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "lines",
}
_LOGGER = logging.getLogger(__name__)


def _table_has_non_whitespace_cell(table: Any) -> bool:
    extracted = table.extract()
    return any(isinstance(cell, str) and cell.strip() for row in extracted for cell in row)


def _bbox_is_contained_in_page(
    bbox: tuple[float, float, float, float], *, page_width: float, page_height: float
) -> bool:
    x0, y0, x1, y1 = bbox
    return 0.0 <= x0 < x1 <= page_width and 0.0 <= y0 < y1 <= page_height


def build_table_candidate_page_analysis(
    bound_page: BoundTableCandidatePage, *, generation_id: str
) -> PageAnalysis:
    """Build page-local table candidates without opening files or persisting data."""

    primitive_page = bound_page.primitive_page
    tables = bound_page.plumber_page.find_tables(table_settings=_TEXT_LINES_TABLE_SETTINGS)
    candidates: list[RegionCandidate] = []
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    for raw_index, table in enumerate(tables, start=0):
        if not _table_has_non_whitespace_cell(table):
            continue

        candidate_id = f"candidate:table:text-lines:{raw_index:04d}"
        bbox = cast(
            tuple[float, float, float, float],
            tuple(float(coordinate) for coordinate in table.bbox),
        )
        if not _bbox_is_contained_in_page(
            bbox,
            page_width=page_width,
            page_height=page_height,
        ):
            _LOGGER.warning(
                "Discarding table candidate %s with bbox %r outside page bounds "
                "width=%r height=%r",
                candidate_id,
                bbox,
                page_width,
                page_height,
            )
            continue

        primitive_ids = tuple(
            primitive.primitive_id
            for primitive in primitive_page.text_primitives
            if measure_candidate_primitive_overlap_ratio(bbox, primitive.bbox) > 0.0
        )
        candidates.append(
            RegionCandidate(
                candidate_id=candidate_id,
                page_id=primitive_page.page_id,
                bbox=bbox,
                proposed_structural_kind="layout.table",
                primitive_ids=primitive_ids,
            )
        )

    provenance = PageAnalysisProvenance(
        source_id=primitive_page.source_id,
        source_capture_id=primitive_page.source_capture_id,
        source_page_id=primitive_page.page_id,
        source_primitive_schema_version=primitive_page.schema_version,
        producer_name="table_candidate",
        producer_version="1.0",
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
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis
