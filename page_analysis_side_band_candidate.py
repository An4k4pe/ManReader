"""Build structural side-band candidates from explicit text hypotheses.

This module does not select primitives, search a page, group text, or decide that a
candidate is accepted. The caller provides one explicit text hypothesis and this
builder converts its geometric measurements into a structural proposal.
"""

from __future__ import annotations

from page_analysis_model import RegionCandidate
from page_analysis_text_hypothesis_measurements import (
    measure_geometric_text_hypothesis,
)
from primitive_model import NormalizedPrimitivePage


def build_side_band_candidate_from_text_hypothesis(
    primitive_page: NormalizedPrimitivePage,
    *,
    candidate_id: str,
    primitive_ids: tuple[str, ...],
) -> RegionCandidate:
    """Build one structural side-band candidate from an explicit text hypothesis."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("candidate_id must be a non-empty string")

    measurements = measure_geometric_text_hypothesis(
        primitive_page,
        primitive_ids=primitive_ids,
    )
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id=primitive_page.page_id,
        bbox=measurements.bbox,
        proposed_structural_kind="layout.side_band",
        primitive_ids=primitive_ids,
    )
