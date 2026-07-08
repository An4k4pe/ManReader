"""Pure validation between page analysis and normalized primitive pages."""

from __future__ import annotations

from page_analysis_model import PageAnalysis
from primitive_model import NormalizedPrimitivePage


def validate_page_analysis_against_primitive_page(
    analysis: PageAnalysis,
    primitive_page: NormalizedPrimitivePage,
) -> None:
    """Validate page-level structural references against one normalized primitive page."""

    if not isinstance(analysis, PageAnalysis):
        raise ValueError("analysis must be a PageAnalysis")
    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")

    if analysis.page_id != primitive_page.page_id:
        raise ValueError("analysis page_id must match primitive_page page_id")
    if analysis.provenance.source_id != primitive_page.source_id:
        raise ValueError("provenance source_id must match primitive_page source_id")
    if analysis.provenance.source_capture_id != primitive_page.source_capture_id:
        raise ValueError("provenance source_capture_id must match primitive_page source_capture_id")
    if analysis.provenance.source_page_id != primitive_page.page_id:
        raise ValueError("provenance source_page_id must match primitive_page page_id")
    if analysis.provenance.source_primitive_schema_version != primitive_page.schema_version:
        raise ValueError(
            "provenance source_primitive_schema_version must match primitive_page schema_version"
        )

    primitive_ids = {
        primitive.primitive_id
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    }
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    for region in analysis.regions:
        x0, y0, x1, y1 = region.bbox
        if not (0.0 <= x0 < x1 <= page_width and 0.0 <= y0 < y1 <= page_height):
            raise ValueError(f"region {region.region_id} bbox must be contained in the page")

        for primitive_id in region.primitive_ids:
            if primitive_id not in primitive_ids:
                raise ValueError(
                    f"region {region.region_id} references missing primitive_id {primitive_id}"
                )
