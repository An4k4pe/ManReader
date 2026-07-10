"""Geometric measurements for caller-provided side-band text hypotheses.

This module measures one explicit selection of horizontal ``TextPrimitive`` IDs.
It does not search for groups, apply thresholds, classify side-bands, or produce
``RegionCandidate`` values.

For the aggregate visible bbox ``(x0, y0, x1, y1)`` on a page with dimensions
``page_width`` and ``page_height``, ratios are computed as:

- ``horizontal_center_ratio = ((x0 + x1) / 2.0) / page_width``
- ``nearest_vertical_edge_distance_ratio = min(x0, page_width - x1) / page_width``
- ``width_ratio = (x1 - x0) / page_width``
- ``height_ratio = (y1 - y0) / page_height``
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_model import BBox
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)

_DIRECTION_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class SideBandMeasurements:
    bbox: BBox
    horizontal_center_ratio: float
    nearest_vertical_edge_distance_ratio: float
    width_ratio: float
    height_ratio: float
    primitive_count: int

    def __post_init__(self) -> None:
        _validate_bbox(self.bbox)
        if self.bbox[0] >= self.bbox[2] or self.bbox[1] >= self.bbox[3]:
            raise ValueError("bbox must be non-degenerate")
        _validate_ratio(
            self.horizontal_center_ratio,
            "horizontal_center_ratio",
            minimum=0.0,
            maximum=1.0,
        )
        _validate_ratio(
            self.nearest_vertical_edge_distance_ratio,
            "nearest_vertical_edge_distance_ratio",
            minimum=0.0,
            maximum=0.5,
        )
        _validate_ratio(
            self.width_ratio,
            "width_ratio",
            minimum=0.0,
            maximum=1.0,
            exclude_minimum=True,
        )
        _validate_ratio(
            self.height_ratio,
            "height_ratio",
            minimum=0.0,
            maximum=1.0,
            exclude_minimum=True,
        )
        if (
            isinstance(self.primitive_count, bool)
            or not isinstance(self.primitive_count, int)
            or self.primitive_count <= 0
        ):
            raise ValueError("primitive_count must be a positive integer")


def measure_horizontal_text_side_band_hypothesis(
    primitive_page: NormalizedPrimitivePage,
    *,
    primitive_ids: tuple[str, ...],
) -> SideBandMeasurements:
    """Measure one explicit horizontal text hypothesis without deciding its kind."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    _validate_primitive_ids(primitive_ids)

    text_primitives = _resolve_text_primitives(primitive_page, primitive_ids)
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    visible_bboxes = tuple(
        _require_visible_bbox(
            primitive,
            page_width=page_width,
            page_height=page_height,
        )
        for primitive in text_primitives
    )
    bbox = _union_bboxes(visible_bboxes)

    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0

    return SideBandMeasurements(
        bbox=bbox,
        horizontal_center_ratio=((x0 + x1) / 2.0) / page_width,
        nearest_vertical_edge_distance_ratio=min(x0, page_width - x1) / page_width,
        width_ratio=width / page_width,
        height_ratio=height / page_height,
        primitive_count=len(primitive_ids),
    )


def _validate_primitive_ids(primitive_ids: tuple[str, ...]) -> None:
    if not isinstance(primitive_ids, tuple):
        raise ValueError("primitive_ids must be a tuple")
    if not primitive_ids:
        raise ValueError("primitive_ids must not be empty")
    for index, primitive_id in enumerate(primitive_ids):
        if not isinstance(primitive_id, str) or not primitive_id:
            raise ValueError(f"primitive_ids[{index}] must be a non-empty string")
    if len(primitive_ids) != len(set(primitive_ids)):
        raise ValueError("primitive_ids must not contain duplicates")


def _resolve_text_primitives(
    primitive_page: NormalizedPrimitivePage,
    primitive_ids: tuple[str, ...],
) -> tuple[TextPrimitive, ...]:
    by_id: dict[str, TextPrimitive | ImageOccurrencePrimitive | DrawingPrimitive] = {
        primitive.primitive_id: primitive
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    }

    resolved: list[TextPrimitive] = []
    for primitive_id in primitive_ids:
        primitive = by_id.get(primitive_id)
        if primitive is None:
            raise ValueError(f"primitive_id does not exist: {primitive_id}")
        if isinstance(primitive, ImageOccurrencePrimitive):
            raise ValueError(f"primitive_id refers to an image primitive: {primitive_id}")
        if isinstance(primitive, DrawingPrimitive):
            raise ValueError(f"primitive_id refers to a drawing primitive: {primitive_id}")
        if not isinstance(primitive, TextPrimitive):
            raise ValueError(f"primitive_id does not refer to a text primitive: {primitive_id}")
        if not _is_supported_horizontal_text(primitive):
            raise ValueError(f"text primitive has unsupported orientation: {primitive_id}")
        resolved.append(primitive)

    return tuple(resolved)


def _is_supported_horizontal_text(primitive: TextPrimitive) -> bool:
    if primitive.direction is None:
        return True
    dx, dy = primitive.direction
    is_rightward = math.isclose(
        dx,
        1.0,
        rel_tol=_DIRECTION_TOLERANCE,
        abs_tol=_DIRECTION_TOLERANCE,
    )
    is_leftward = math.isclose(
        dx,
        -1.0,
        rel_tol=_DIRECTION_TOLERANCE,
        abs_tol=_DIRECTION_TOLERANCE,
    )
    is_axis_aligned = math.isclose(
        dy,
        0.0,
        rel_tol=_DIRECTION_TOLERANCE,
        abs_tol=_DIRECTION_TOLERANCE,
    )
    return (is_rightward or is_leftward) and is_axis_aligned


def _require_visible_bbox(
    primitive: TextPrimitive,
    *,
    page_width: float,
    page_height: float,
) -> BBox:
    visible_bbox = _visible_bbox(
        primitive.bbox,
        page_width=page_width,
        page_height=page_height,
    )
    if visible_bbox is None:
        raise ValueError(
            f"text primitive has no visible intersection with the page: {primitive.primitive_id}"
        )
    return visible_bbox


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


def _union_bboxes(bboxes: tuple[BBox, ...]) -> BBox:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def _validate_bbox(value: BBox) -> None:
    if not isinstance(value, tuple) or len(value) != 4:
        raise ValueError("bbox must be a tuple with 4 items")
    for index, coordinate in enumerate(value):
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            raise ValueError(f"bbox[{index}] must be a finite number")
        if not math.isfinite(float(coordinate)):
            raise ValueError(f"bbox[{index}] must be a finite number")
    if value[0] > value[2] or value[1] > value[3]:
        raise ValueError("bbox coordinates are inverted")


def _validate_ratio(
    value: float,
    field_name: str,
    *,
    minimum: float,
    maximum: float,
    exclude_minimum: bool = False,
) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be a finite number")
    if exclude_minimum:
        if not minimum < value <= maximum:
            raise ValueError(f"{field_name} must be greater than {minimum} and <= {maximum}")
    elif not minimum <= value <= maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
