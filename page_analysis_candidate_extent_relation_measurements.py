"""Pure relations between a candidate bbox and existing page-context extents.

The module derives geometry solely from ``CandidatePageContextMeasurements``.
It neither revisits page primitives nor makes any structural decision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_model import BBox, _validate_bbox, _validate_non_empty_string
from page_analysis_candidate_page_context_measurements import (
    CandidatePageContextMeasurements,
)


@dataclass(frozen=True, slots=True)
class CandidateExtentRelationMeasurements:
    """Geometry-only relation with the candidate bbox as the first operand."""

    horizontal_gap: float
    vertical_gap: float
    horizontal_overlap: float
    vertical_overlap: float
    candidate_contains_extent: bool
    extent_contains_candidate: bool

    def __post_init__(self) -> None:
        for field_name in (
            "horizontal_gap",
            "vertical_gap",
            "horizontal_overlap",
            "vertical_overlap",
        ):
            _validate_non_negative_number(getattr(self, field_name), field_name)
        for field_name in (
            "candidate_contains_extent",
            "extent_contains_candidate",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a bool")


@dataclass(frozen=True, slots=True)
class CandidateNonCandidateExtentRelationMeasurements:
    """Per-family relations derived from one candidate page-context measurement."""

    candidate_id: str
    page_id: str
    candidate_bbox: BBox
    candidate_primitive_ids: tuple[str, ...]
    non_candidate_visible_text_extent_bbox: BBox | None
    non_candidate_visible_text_extent_relation: CandidateExtentRelationMeasurements | None
    non_candidate_visible_image_extent_bbox: BBox | None
    non_candidate_visible_image_extent_relation: CandidateExtentRelationMeasurements | None
    non_candidate_visible_drawing_extent_bbox: BBox | None
    non_candidate_visible_drawing_extent_relation: CandidateExtentRelationMeasurements | None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.candidate_id, "candidate_id")
        _validate_non_empty_string(self.page_id, "page_id")
        _validate_non_degenerate_bbox(self.candidate_bbox, "candidate_bbox")
        _validate_candidate_primitive_ids(self.candidate_primitive_ids)
        _validate_extent_and_relation(
            self.non_candidate_visible_text_extent_bbox,
            self.non_candidate_visible_text_extent_relation,
            extent_field_name="non_candidate_visible_text_extent_bbox",
            relation_field_name="non_candidate_visible_text_extent_relation",
        )
        _validate_extent_and_relation(
            self.non_candidate_visible_image_extent_bbox,
            self.non_candidate_visible_image_extent_relation,
            extent_field_name="non_candidate_visible_image_extent_bbox",
            relation_field_name="non_candidate_visible_image_extent_relation",
        )
        _validate_extent_and_relation(
            self.non_candidate_visible_drawing_extent_bbox,
            self.non_candidate_visible_drawing_extent_relation,
            extent_field_name="non_candidate_visible_drawing_extent_bbox",
            relation_field_name="non_candidate_visible_drawing_extent_relation",
        )


def measure_candidate_non_candidate_extent_relations(
    measurements: CandidatePageContextMeasurements,
) -> CandidateNonCandidateExtentRelationMeasurements:
    """Derive per-family candidate-to-extent geometry from page-context data."""

    if not isinstance(measurements, CandidatePageContextMeasurements):
        raise ValueError("measurements must be a CandidatePageContextMeasurements")

    candidate_bbox = measurements.candidate_bbox
    text_extent = measurements.non_candidate_visible_text_extent_bbox
    image_extent = measurements.non_candidate_visible_image_extent_bbox
    drawing_extent = measurements.non_candidate_visible_drawing_extent_bbox
    return CandidateNonCandidateExtentRelationMeasurements(
        candidate_id=measurements.candidate_id,
        page_id=measurements.page_id,
        candidate_bbox=candidate_bbox,
        candidate_primitive_ids=measurements.candidate_primitive_ids,
        non_candidate_visible_text_extent_bbox=text_extent,
        non_candidate_visible_text_extent_relation=_relation(candidate_bbox, text_extent),
        non_candidate_visible_image_extent_bbox=image_extent,
        non_candidate_visible_image_extent_relation=_relation(candidate_bbox, image_extent),
        non_candidate_visible_drawing_extent_bbox=drawing_extent,
        non_candidate_visible_drawing_extent_relation=_relation(candidate_bbox, drawing_extent),
    )


def _relation(
    candidate_bbox: BBox,
    extent_bbox: BBox | None,
) -> CandidateExtentRelationMeasurements | None:
    if extent_bbox is None:
        return None
    return CandidateExtentRelationMeasurements(
        horizontal_gap=_axis_gap(
            candidate_bbox[0],
            candidate_bbox[2],
            extent_bbox[0],
            extent_bbox[2],
        ),
        vertical_gap=_axis_gap(
            candidate_bbox[1],
            candidate_bbox[3],
            extent_bbox[1],
            extent_bbox[3],
        ),
        horizontal_overlap=_axis_overlap(
            candidate_bbox[0],
            candidate_bbox[2],
            extent_bbox[0],
            extent_bbox[2],
        ),
        vertical_overlap=_axis_overlap(
            candidate_bbox[1],
            candidate_bbox[3],
            extent_bbox[1],
            extent_bbox[3],
        ),
        candidate_contains_extent=_contains(candidate_bbox, extent_bbox),
        extent_contains_candidate=_contains(extent_bbox, candidate_bbox),
    )


def _axis_gap(first_start: float, first_end: float, second_start: float, second_end: float) -> float:
    if first_end < second_start:
        return second_start - first_end
    if second_end < first_start:
        return first_start - second_end
    return 0.0


def _axis_overlap(
    first_start: float,
    first_end: float,
    second_start: float,
    second_end: float,
) -> float:
    return max(0.0, min(first_end, second_end) - max(first_start, second_start))


def _contains(outer_bbox: BBox, inner_bbox: BBox) -> bool:
    return (
        outer_bbox[0] <= inner_bbox[0]
        and outer_bbox[1] <= inner_bbox[1]
        and outer_bbox[2] >= inner_bbox[2]
        and outer_bbox[3] >= inner_bbox[3]
    )


def _validate_non_degenerate_bbox(bbox: BBox, field_name: str) -> None:
    _validate_bbox(bbox, field_name)
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError(f"{field_name} must be non-degenerate")


def _validate_candidate_primitive_ids(primitive_ids: tuple[str, ...]) -> None:
    if not isinstance(primitive_ids, tuple):
        raise ValueError("candidate_primitive_ids must be a tuple")

    seen: set[str] = set()
    for index, primitive_id in enumerate(primitive_ids):
        _validate_non_empty_string(primitive_id, f"candidate_primitive_ids[{index}]")
        if primitive_id in seen:
            raise ValueError("candidate_primitive_ids must not contain duplicates")
        seen.add(primitive_id)


def _validate_extent_and_relation(
    extent: BBox | None,
    relation: CandidateExtentRelationMeasurements | None,
    *,
    extent_field_name: str,
    relation_field_name: str,
) -> None:
    if extent is not None:
        _validate_non_degenerate_bbox(extent, extent_field_name)
    if relation is not None and not isinstance(relation, CandidateExtentRelationMeasurements):
        raise ValueError(f"{relation_field_name} must be a CandidateExtentRelationMeasurements")
    if (extent is None) != (relation is None):
        raise ValueError(f"{extent_field_name} and {relation_field_name} must both be None or present")


def _validate_non_negative_number(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite number")
    if value < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
