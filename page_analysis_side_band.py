"""Produce conservative singleton structural side-band candidates.

This producer considers only the canonical singleton text hypotheses already built
from a normalized page. It does not group primitives or recognize a complete
side-band. Each accepted singleton becomes one unresolved ``layout.side_band``
candidate.
"""

from __future__ import annotations

from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
)
from page_analysis_side_band_candidate import (
    build_side_band_candidate_from_text_hypothesis,
)
from page_analysis_text_hypotheses import build_geometric_text_hypotheses
from page_analysis_text_hypothesis_measurements import (
    TextHypothesisMeasurements,
    measure_geometric_text_hypothesis,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage

_PRODUCER_NAME = "page_analysis.singleton_side_band"
_PRODUCER_VERSION = "0.1"
_CONFIGURATION_ID = "singleton-side-band-v1"
_SIDE_BAND_OUTER_BAND_RATIO = 0.25
_SIDE_BAND_MAX_WIDTH_RATIO = 0.22
_SIDE_BAND_VERTICAL_MARGIN_RATIO = 0.12


def build_singleton_side_band_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
) -> PageAnalysis:
    """Build page-level side-band candidates from canonical singleton hypotheses."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    candidates = []

    for hypothesis in build_geometric_text_hypotheses(primitive_page):
        primitive_ids = hypothesis.primitive_ids
        measurements = measure_geometric_text_hypothesis(
            primitive_page,
            primitive_ids=primitive_ids,
        )
        if not _is_conservative_side_band_singleton(
            measurements,
            page_width=page_width,
            page_height=page_height,
        ):
            continue

        primitive_id = primitive_ids[0]
        candidates.append(
            build_side_band_candidate_from_text_hypothesis(
                primitive_page,
                candidate_id=f"candidate:side-band:{primitive_id}",
                primitive_ids=primitive_ids,
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


def _is_conservative_side_band_singleton(
    measurements: TextHypothesisMeasurements,
    *,
    page_width: float,
    page_height: float,
) -> bool:
    x0, y0, x1, y1 = measurements.bbox
    in_vertical_corridor = (
        y0 >= page_height * _SIDE_BAND_VERTICAL_MARGIN_RATIO
        and y1 <= page_height * (1.0 - _SIDE_BAND_VERTICAL_MARGIN_RATIO)
    )
    if not in_vertical_corridor or measurements.width_ratio > _SIDE_BAND_MAX_WIDTH_RATIO:
        return False

    is_left = x0 >= 0.0 and x1 <= page_width * _SIDE_BAND_OUTER_BAND_RATIO
    is_right = x0 >= page_width * (1.0 - _SIDE_BAND_OUTER_BAND_RATIO) and x1 <= page_width
    return is_left or is_right
