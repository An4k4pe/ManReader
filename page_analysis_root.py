"""Deterministic root-region PageAnalysis producer.

This producer creates only the structural page root for one normalized
primitive page. It performs no detection, semantic classification,
reading-order inference, ownership resolution, or editorial policy.
"""

from __future__ import annotations

from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage

ROOT_PAGE_ANALYSIS_PRODUCER_NAME = "page-analysis-root"
ROOT_PAGE_ANALYSIS_PRODUCER_VERSION = "0.1"
ROOT_PAGE_ANALYSIS_CONFIGURATION_ID = "page-root-analysis-v1"
ROOT_REGION_ID = "region:page-root"
ROOT_STRUCTURAL_KIND = "layout.page"


def build_root_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build and validate a deterministic root-region PageAnalysis."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    primitive_ids = (
        tuple(primitive.primitive_id for primitive in primitive_page.text_primitives)
        + tuple(primitive.primitive_id for primitive in primitive_page.image_primitives)
        + tuple(primitive.primitive_id for primitive in primitive_page.drawing_primitives)
    )

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=ROOT_PAGE_ANALYSIS_PRODUCER_NAME,
            producer_version=ROOT_PAGE_ANALYSIS_PRODUCER_VERSION,
            configuration_id=ROOT_PAGE_ANALYSIS_CONFIGURATION_ID,
        ),
        regions=(
            LayoutRegion(
                region_id=ROOT_REGION_ID,
                page_id=primitive_page.page_id,
                bbox=(
                    0.0,
                    0.0,
                    primitive_page.page_geometry.width,
                    primitive_page.page_geometry.height,
                ),
                structural_kind=ROOT_STRUCTURAL_KIND,
                primitive_ids=primitive_ids,
            ),
        ),
        relations=(),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis
