"""Produce conservative candidates for page-covering visual primitives.

This diagnostic producer considers only image and drawing primitives. It uses
their page-visible bounding boxes and creates unresolved structural candidates;
it does not classify visual content or make editorial decisions.
"""

from __future__ import annotations

from geometry_model import BBox
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import DrawingPrimitive, ImageOccurrencePrimitive, NormalizedPrimitivePage

_PRODUCER_NAME = "page_analysis.page_covering_visual"
_PRODUCER_VERSION = "0.1"
_CONFIGURATION_ID = "page-covering-visual-v1"
_STRUCTURAL_KIND = "layout.page_covering_visual"
_CANDIDATE_ID_PREFIX = "candidate:page-covering-visual:"
_MIN_VISIBLE_WIDTH_RATIO = 0.95
_MIN_VISIBLE_HEIGHT_RATIO = 0.95

type _VisualPrimitive = ImageOccurrencePrimitive | DrawingPrimitive


def build_page_covering_visual_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build and validate candidates for page-covering visual primitives."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    candidates = []
    visual_primitives: tuple[_VisualPrimitive, ...] = (
        *primitive_page.image_primitives,
        *primitive_page.drawing_primitives,
    )
    for primitive in sorted(visual_primitives, key=lambda item: item.primitive_id):
        visible_bbox = _visible_bbox(
            primitive.bbox,
            page_width=page_width,
            page_height=page_height,
        )
        if visible_bbox is None:
            continue
        visible_width_ratio = (visible_bbox[2] - visible_bbox[0]) / page_width
        visible_height_ratio = (visible_bbox[3] - visible_bbox[1]) / page_height
        if (
            visible_width_ratio < _MIN_VISIBLE_WIDTH_RATIO
            or visible_height_ratio < _MIN_VISIBLE_HEIGHT_RATIO
        ):
            continue
        candidates.append(
            RegionCandidate(
                candidate_id=f"{_CANDIDATE_ID_PREFIX}{primitive.primitive_id}",
                page_id=primitive_page.page_id,
                bbox=visible_bbox,
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=(primitive.primitive_id,),
            )
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
            producer_name=_PRODUCER_NAME,
            producer_version=_PRODUCER_VERSION,
            configuration_id=_CONFIGURATION_ID,
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
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
