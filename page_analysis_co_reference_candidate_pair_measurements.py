"""Pure contextual geometry for one explicit pair of co-referenced candidates."""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_model import BBox
from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    resolve_co_referenced_page_candidate_reference,
)


@dataclass(frozen=True, slots=True)
class CoReferencedPageCandidatePairMeasurements:
    """Geometry-only measurements for an ordered contextual candidate pair."""

    first_candidate_reference: CoReferencedPageCandidateReference
    second_candidate_reference: CoReferencedPageCandidateReference
    first_candidate_bbox: BBox
    second_candidate_bbox: BBox
    horizontal_gap: float
    vertical_gap: float
    horizontal_overlap: float
    vertical_overlap: float
    x0_delta: float
    y0_delta: float
    x1_delta: float
    y1_delta: float

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
            "horizontal_gap",
            "vertical_gap",
            "horizontal_overlap",
            "vertical_overlap",
        ):
            _validate_non_negative_float(getattr(self, field_name), field_name)
        for field_name in ("x0_delta", "y0_delta", "x1_delta", "y1_delta"):
            _validate_finite_float(getattr(self, field_name), field_name)


def measure_co_referenced_page_candidate_pair(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    first_candidate_reference: CoReferencedPageCandidateReference,
    second_candidate_reference: CoReferencedPageCandidateReference,
) -> CoReferencedPageCandidatePairMeasurements:
    """Measure two references resolved exactly within one supplied binding."""

    if not isinstance(
        bound_co_referenced_page_analyses,
        BoundCoReferencedPageAnalyses,
    ):
        raise ValueError(
            "bound_co_referenced_page_analyses must be a "
            "BoundCoReferencedPageAnalyses"
        )
    if not isinstance(
        first_candidate_reference,
        CoReferencedPageCandidateReference,
    ):
        raise ValueError(
            "first_candidate_reference must be a "
            "CoReferencedPageCandidateReference"
        )
    if not isinstance(
        second_candidate_reference,
        CoReferencedPageCandidateReference,
    ):
        raise ValueError(
            "second_candidate_reference must be a "
            "CoReferencedPageCandidateReference"
        )

    first_candidate = resolve_co_referenced_page_candidate_reference(
        bound_co_referenced_page_analyses,
        reference=first_candidate_reference,
    )
    second_candidate = resolve_co_referenced_page_candidate_reference(
        bound_co_referenced_page_analyses,
        reference=second_candidate_reference,
    )
    first_bbox = first_candidate.bbox
    second_bbox = second_candidate.bbox

    return CoReferencedPageCandidatePairMeasurements(
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
        first_candidate_bbox=first_bbox,
        second_candidate_bbox=second_bbox,
        horizontal_gap=_axis_gap(first_bbox[0], first_bbox[2], second_bbox[0], second_bbox[2]),
        vertical_gap=_axis_gap(first_bbox[1], first_bbox[3], second_bbox[1], second_bbox[3]),
        horizontal_overlap=_axis_overlap(
            first_bbox[0], first_bbox[2], second_bbox[0], second_bbox[2]
        ),
        vertical_overlap=_axis_overlap(
            first_bbox[1], first_bbox[3], second_bbox[1], second_bbox[3]
        ),
        x0_delta=float(second_bbox[0] - first_bbox[0]),
        y0_delta=float(second_bbox[1] - first_bbox[1]),
        x1_delta=float(second_bbox[2] - first_bbox[2]),
        y1_delta=float(second_bbox[3] - first_bbox[3]),
    )


def _axis_gap(first_start: float, first_end: float, second_start: float, second_end: float) -> float:
    if first_end < second_start:
        return float(second_start - first_end)
    if second_end < first_start:
        return float(first_start - second_end)
    return 0.0


def _axis_overlap(
    first_start: float,
    first_end: float,
    second_start: float,
    second_end: float,
) -> float:
    return float(max(0.0, min(first_end, second_end) - max(first_start, second_start)))


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


def _validate_finite_float(value: float, field_name: str) -> None:
    if not isinstance(value, float) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite float")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    _validate_finite_float(value, field_name)
    if value < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
