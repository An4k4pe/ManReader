"""Pure contextual overlap ratio for one explicit pair of co-referenced candidates.

This is a ratio, not a decision: overlap_area / area of the smaller candidate.
No threshold is applied here and none is implied. Proposta_ResolutionDesign_v3.md
§10.E1 reopens the Milestone 13-19 subsystem specifically for this measurement,
motivated by the Milestone 24 design note that a fixed overlap/disjoint boolean
is not enough to distinguish genuine containment from marginal coincidence --
deliberately reversing the Milestone 16 choice not to expose containment/ratio
in measure_co_referenced_page_candidate_pair.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_model import BBox
from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_co_reference_candidate_pair_measurements import (
    measure_co_referenced_page_candidate_pair,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
)


@dataclass(frozen=True, slots=True)
class CoReferencedPageCandidateOverlapRatioMeasurements:
    """Overlap-ratio-only measurements for an ordered contextual candidate pair."""

    first_candidate_reference: CoReferencedPageCandidateReference
    second_candidate_reference: CoReferencedPageCandidateReference
    first_candidate_bbox: BBox
    second_candidate_bbox: BBox
    first_candidate_area: float
    second_candidate_area: float
    overlap_area: float
    overlap_ratio: float

    def __post_init__(self) -> None:
        if not isinstance(
            self.first_candidate_reference,
            CoReferencedPageCandidateReference,
        ):
            raise ValueError(
                "first_candidate_reference must be a "
                "CoReferencedPageCandidateReference"
            )
        if not isinstance(
            self.second_candidate_reference,
            CoReferencedPageCandidateReference,
        ):
            raise ValueError(
                "second_candidate_reference must be a "
                "CoReferencedPageCandidateReference"
            )
        _validate_non_degenerate_bbox(self.first_candidate_bbox, "first_candidate_bbox")
        _validate_non_degenerate_bbox(self.second_candidate_bbox, "second_candidate_bbox")
        for field_name in (
            "first_candidate_area",
            "second_candidate_area",
            "overlap_area",
            "overlap_ratio",
        ):
            _validate_non_negative_float(getattr(self, field_name), field_name)


def measure_co_referenced_page_candidate_overlap_ratio(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    first_candidate_reference: CoReferencedPageCandidateReference,
    second_candidate_reference: CoReferencedPageCandidateReference,
) -> CoReferencedPageCandidateOverlapRatioMeasurements:
    """Measure the overlap-area-to-smaller-candidate-area ratio for one pair."""

    pair_measurements = measure_co_referenced_page_candidate_pair(
        bound_co_referenced_page_analyses,
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
    )

    first_bbox = pair_measurements.first_candidate_bbox
    second_bbox = pair_measurements.second_candidate_bbox
    first_candidate_area = (first_bbox[2] - first_bbox[0]) * (first_bbox[3] - first_bbox[1])
    second_candidate_area = (second_bbox[2] - second_bbox[0]) * (second_bbox[3] - second_bbox[1])
    overlap_area = pair_measurements.horizontal_overlap * pair_measurements.vertical_overlap
    overlap_ratio = overlap_area / min(first_candidate_area, second_candidate_area)

    return CoReferencedPageCandidateOverlapRatioMeasurements(
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
        first_candidate_bbox=first_bbox,
        second_candidate_bbox=second_bbox,
        first_candidate_area=first_candidate_area,
        second_candidate_area=second_candidate_area,
        overlap_area=overlap_area,
        overlap_ratio=overlap_ratio,
    )


def _validate_non_degenerate_bbox(bbox: BBox, field_name: str) -> None:
    if not isinstance(bbox, tuple) or len(bbox) != 4:
        raise ValueError(f"{field_name} must be a tuple with 4 items")
    for index, coordinate in enumerate(bbox):
        if (
            isinstance(coordinate, bool)
            or not isinstance(coordinate, (int, float))
            or not math.isfinite(coordinate)
        ):
            raise ValueError(f"{field_name}[{index}] must be a finite number")
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError(f"{field_name} must be non-degenerate")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    if not isinstance(value, float) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite float")
    if value < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
