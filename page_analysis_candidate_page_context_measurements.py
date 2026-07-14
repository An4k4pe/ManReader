"""Pure page-context measurements for one existing region candidate.

This module observes visible non-candidate primitives by primitive family.  It
does not classify the candidate, create analysis artifacts, or persist data.
"""

from __future__ import annotations

from dataclasses import dataclass

from geometry_model import BBox, _validate_bbox, _validate_non_empty_string
from page_analysis_model import RegionCandidate
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)

type _Primitive = TextPrimitive | ImageOccurrencePrimitive | DrawingPrimitive


@dataclass(frozen=True, slots=True)
class CandidatePageContextMeasurements:
    """Visible non-candidate primitive extents, kept separate by family."""

    candidate_id: str
    page_id: str
    candidate_bbox: BBox
    candidate_primitive_ids: tuple[str, ...]
    non_candidate_visible_text_primitive_count: int
    non_candidate_visible_text_extent_bbox: BBox | None
    non_candidate_visible_image_primitive_count: int
    non_candidate_visible_image_extent_bbox: BBox | None
    non_candidate_visible_drawing_primitive_count: int
    non_candidate_visible_drawing_extent_bbox: BBox | None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.candidate_id, "candidate_id")
        _validate_non_empty_string(self.page_id, "page_id")
        _validate_non_degenerate_bbox(self.candidate_bbox, "candidate_bbox")
        _validate_candidate_primitive_ids(self.candidate_primitive_ids)
        _validate_count_and_extent(
            self.non_candidate_visible_text_primitive_count,
            self.non_candidate_visible_text_extent_bbox,
            count_field_name="non_candidate_visible_text_primitive_count",
            extent_field_name="non_candidate_visible_text_extent_bbox",
        )
        _validate_count_and_extent(
            self.non_candidate_visible_image_primitive_count,
            self.non_candidate_visible_image_extent_bbox,
            count_field_name="non_candidate_visible_image_primitive_count",
            extent_field_name="non_candidate_visible_image_extent_bbox",
        )
        _validate_count_and_extent(
            self.non_candidate_visible_drawing_primitive_count,
            self.non_candidate_visible_drawing_extent_bbox,
            count_field_name="non_candidate_visible_drawing_primitive_count",
            extent_field_name="non_candidate_visible_drawing_extent_bbox",
        )


def measure_candidate_page_context(
    primitive_page: NormalizedPrimitivePage,
    *,
    candidate: RegionCandidate,
) -> CandidatePageContextMeasurements:
    """Measure page-visible primitives that are not referenced by ``candidate``."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(candidate, RegionCandidate):
        raise ValueError("candidate must be a RegionCandidate")
    if candidate.page_id != primitive_page.page_id:
        raise ValueError("candidate page_id must match primitive_page page_id")

    primitives_by_id = _primitives_by_id(primitive_page)
    for primitive_id in candidate.primitive_ids:
        if primitive_id not in primitives_by_id:
            raise ValueError(f"candidate primitive_id does not exist: {primitive_id}")

    excluded_primitive_ids = set(candidate.primitive_ids)
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    text_count, text_extent = _visible_non_candidate_extent(
        primitive_page.text_primitives,
        excluded_primitive_ids=excluded_primitive_ids,
        page_width=page_width,
        page_height=page_height,
    )
    image_count, image_extent = _visible_non_candidate_extent(
        primitive_page.image_primitives,
        excluded_primitive_ids=excluded_primitive_ids,
        page_width=page_width,
        page_height=page_height,
    )
    drawing_count, drawing_extent = _visible_non_candidate_extent(
        primitive_page.drawing_primitives,
        excluded_primitive_ids=excluded_primitive_ids,
        page_width=page_width,
        page_height=page_height,
    )

    return CandidatePageContextMeasurements(
        candidate_id=candidate.candidate_id,
        page_id=primitive_page.page_id,
        candidate_bbox=candidate.bbox,
        candidate_primitive_ids=candidate.primitive_ids,
        non_candidate_visible_text_primitive_count=text_count,
        non_candidate_visible_text_extent_bbox=text_extent,
        non_candidate_visible_image_primitive_count=image_count,
        non_candidate_visible_image_extent_bbox=image_extent,
        non_candidate_visible_drawing_primitive_count=drawing_count,
        non_candidate_visible_drawing_extent_bbox=drawing_extent,
    )


def _primitives_by_id(primitive_page: NormalizedPrimitivePage) -> dict[str, _Primitive]:
    return {
        primitive.primitive_id: primitive
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    }


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


def _validate_count_and_extent(
    count: int,
    extent: BBox | None,
    *,
    count_field_name: str,
    extent_field_name: str,
) -> None:
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError(f"{count_field_name} must be a non-negative int")
    if extent is not None:
        _validate_non_degenerate_bbox(extent, extent_field_name)
    if count == 0 and extent is not None:
        raise ValueError(f"{extent_field_name} must be None when {count_field_name} is 0")
    if count > 0 and extent is None:
        raise ValueError(f"{extent_field_name} is required when {count_field_name} is positive")


def _visible_non_candidate_extent(
    primitives: tuple[_Primitive, ...],
    *,
    excluded_primitive_ids: set[str],
    page_width: float,
    page_height: float,
) -> tuple[int, BBox | None]:
    visible_bboxes = tuple(
        visible_bbox
        for primitive in primitives
        if primitive.primitive_id not in excluded_primitive_ids
        if (
            visible_bbox := _visible_bbox(
                primitive.bbox,
                page_width=page_width,
                page_height=page_height,
            )
        )
        is not None
    )
    if not visible_bboxes:
        return (0, None)
    return (len(visible_bboxes), _extent_bbox(visible_bboxes))


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


def _extent_bbox(bboxes: tuple[BBox, ...]) -> BBox:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )
