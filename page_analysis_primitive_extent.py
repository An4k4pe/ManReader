"""Deterministic visible primitive-extent PageAnalysis producer.

This producer adds one structural region covering the geometric union of
the page-visible portions of normalized primitives. Primitives with no
positive-area intersection with the canonical page are excluded from the
extent region. It performs no detection, semantic classification,
reading-order inference, ownership resolution, or editorial policy.
"""

from __future__ import annotations

from geometry_model import BBox
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionRelation,
)
from page_analysis_root import ROOT_REGION_ID, build_root_page_analysis
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage

PRIMITIVE_EXTENT_PRODUCER_NAME = "page-analysis-primitive-extent"
PRIMITIVE_EXTENT_PRODUCER_VERSION = "0.1"
PRIMITIVE_EXTENT_CONFIGURATION_ID = "primitive-extent-analysis-v1"

PRIMITIVE_EXTENT_REGION_ID = "region:primitive-extent"
PRIMITIVE_EXTENT_STRUCTURAL_KIND = "layout.primitive_extent"

ROOT_CONTAINS_EXTENT_RELATION_ID = "relation:page-root-contains-primitive-extent"


def build_primitive_extent_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build and validate a visible primitive-extent PageAnalysis."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    root_analysis = build_root_page_analysis(
        primitive_page,
        generation_id=generation_id,
    )
    provenance = PageAnalysisProvenance(
        source_id=primitive_page.source_id,
        source_capture_id=primitive_page.source_capture_id,
        source_page_id=primitive_page.page_id,
        source_primitive_schema_version=primitive_page.schema_version,
        producer_name=PRIMITIVE_EXTENT_PRODUCER_NAME,
        producer_version=PRIMITIVE_EXTENT_PRODUCER_VERSION,
        configuration_id=PRIMITIVE_EXTENT_CONFIGURATION_ID,
    )

    all_primitives = (
        primitive_page.text_primitives
        + primitive_page.image_primitives
        + primitive_page.drawing_primitives
    )
    visible_primitives = tuple(
        (primitive, visible_bbox)
        for primitive in all_primitives
        if (
            visible_bbox := _visible_bbox(
                primitive.bbox,
                page_width=primitive_page.page_geometry.width,
                page_height=primitive_page.page_geometry.height,
            )
        )
        is not None
    )
    if not visible_primitives:
        analysis = PageAnalysis(
            schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
            generation_id=generation_id,
            page_id=primitive_page.page_id,
            provenance=provenance,
            regions=root_analysis.regions,
            relations=(),
        )
        validate_page_analysis_against_primitive_page(analysis, primitive_page)
        return analysis

    visible_bboxes = tuple(visible_bbox for _, visible_bbox in visible_primitives)
    primitive_extent_bbox = (
        min(bbox[0] for bbox in visible_bboxes),
        min(bbox[1] for bbox in visible_bboxes),
        max(bbox[2] for bbox in visible_bboxes),
        max(bbox[3] for bbox in visible_bboxes),
    )
    primitive_ids = tuple(primitive.primitive_id for primitive, _ in visible_primitives)

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=provenance,
        regions=(
            root_analysis.regions[0],
            LayoutRegion(
                region_id=PRIMITIVE_EXTENT_REGION_ID,
                page_id=primitive_page.page_id,
                bbox=primitive_extent_bbox,
                structural_kind=PRIMITIVE_EXTENT_STRUCTURAL_KIND,
                primitive_ids=primitive_ids,
            ),
        ),
        relations=(
            RegionRelation(
                relation_id=ROOT_CONTAINS_EXTENT_RELATION_ID,
                relation_kind="layout.contains",
                source_region_id=ROOT_REGION_ID,
                target_region_id=PRIMITIVE_EXTENT_REGION_ID,
            ),
        ),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis


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
