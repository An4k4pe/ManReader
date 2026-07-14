"""Pure geometric measurements for one explicit pair of normalized primitives.

This module resolves two caller-provided primitive IDs and measures only their
original and page-visible bounding boxes. It does not classify, cluster, create
candidates, or persist any result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from geometry_model import BBox
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)

type PrimitiveKind = Literal["text", "image", "drawing"]
type _Primitive = TextPrimitive | ImageOccurrencePrimitive | DrawingPrimitive


class PrimitiveNotVisibleOnPageError(ValueError):
    """A requested primitive has no positive-area visible page intersection."""

    def __init__(self, primitive_id: str) -> None:
        self.primitive_id = primitive_id
        super().__init__(f"primitive has no visible intersection with the page: {primitive_id}")


@dataclass(frozen=True, slots=True)
class PrimitivePairMeasurements:
    """Geometry-only measurements for an ordered explicit primitive pair."""

    first_primitive_id: str
    second_primitive_id: str
    first_primitive_kind: PrimitiveKind
    second_primitive_kind: PrimitiveKind
    first_bbox: BBox
    second_bbox: BBox
    first_visible_bbox: BBox
    second_visible_bbox: BBox
    horizontal_gap: float
    vertical_gap: float
    horizontal_overlap: float
    vertical_overlap: float
    horizontal_overlap_ratio: float
    vertical_overlap_ratio: float
    is_disjoint: bool
    touches: bool
    intersects: bool
    first_contains_second: bool
    second_contains_first: bool
    first_page_left_distance: float
    first_page_right_distance: float
    first_page_top_distance: float
    first_page_bottom_distance: float
    second_page_left_distance: float
    second_page_right_distance: float
    second_page_top_distance: float
    second_page_bottom_distance: float
    left_edge_delta: float
    right_edge_delta: float
    top_edge_delta: float
    bottom_edge_delta: float
    center_x_delta: float
    center_y_delta: float

    def __post_init__(self) -> None:
        _validate_primitive_id(self.first_primitive_id, "first_primitive_id")
        _validate_primitive_id(self.second_primitive_id, "second_primitive_id")
        if self.first_primitive_id == self.second_primitive_id:
            raise ValueError("first_primitive_id and second_primitive_id must differ")
        _validate_primitive_kind(self.first_primitive_kind, "first_primitive_kind")
        _validate_primitive_kind(self.second_primitive_kind, "second_primitive_kind")
        _validate_bbox(self.first_bbox, "first_bbox")
        _validate_bbox(self.second_bbox, "second_bbox")
        _validate_visible_bbox(self.first_visible_bbox, "first_visible_bbox")
        _validate_visible_bbox(self.second_visible_bbox, "second_visible_bbox")

        for field_name in (
            "horizontal_gap",
            "vertical_gap",
            "horizontal_overlap",
            "vertical_overlap",
            "first_page_left_distance",
            "first_page_right_distance",
            "first_page_top_distance",
            "first_page_bottom_distance",
            "second_page_left_distance",
            "second_page_right_distance",
            "second_page_top_distance",
            "second_page_bottom_distance",
        ):
            _validate_non_negative_number(getattr(self, field_name), field_name)

        for field_name in (
            "left_edge_delta",
            "right_edge_delta",
            "top_edge_delta",
            "bottom_edge_delta",
            "center_x_delta",
            "center_y_delta",
        ):
            _validate_finite_number(getattr(self, field_name), field_name)

        _validate_ratio(self.horizontal_overlap_ratio, "horizontal_overlap_ratio")
        _validate_ratio(self.vertical_overlap_ratio, "vertical_overlap_ratio")
        for field_name in (
            "is_disjoint",
            "touches",
            "intersects",
            "first_contains_second",
            "second_contains_first",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a bool")


def measure_primitive_pair(
    primitive_page: NormalizedPrimitivePage,
    *,
    first_primitive_id: str,
    second_primitive_id: str,
) -> PrimitivePairMeasurements:
    """Measure one ordered pair of visible normalized primitives."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    _validate_primitive_id(first_primitive_id, "first_primitive_id")
    _validate_primitive_id(second_primitive_id, "second_primitive_id")
    if first_primitive_id == second_primitive_id:
        raise ValueError("first_primitive_id and second_primitive_id must differ")

    primitives_by_id = _primitives_by_id(primitive_page)
    first_primitive = _require_primitive(primitives_by_id, first_primitive_id)
    second_primitive = _require_primitive(primitives_by_id, second_primitive_id)

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    first_visible_bbox = _require_visible_bbox(
        first_primitive,
        page_width=page_width,
        page_height=page_height,
    )
    second_visible_bbox = _require_visible_bbox(
        second_primitive,
        page_width=page_width,
        page_height=page_height,
    )

    first_width, first_height = _size(first_visible_bbox)
    second_width, second_height = _size(second_visible_bbox)
    horizontal_gap = _axis_gap(
        first_visible_bbox[0],
        first_visible_bbox[2],
        second_visible_bbox[0],
        second_visible_bbox[2],
    )
    vertical_gap = _axis_gap(
        first_visible_bbox[1],
        first_visible_bbox[3],
        second_visible_bbox[1],
        second_visible_bbox[3],
    )
    horizontal_overlap = _axis_overlap(
        first_visible_bbox[0],
        first_visible_bbox[2],
        second_visible_bbox[0],
        second_visible_bbox[2],
    )
    vertical_overlap = _axis_overlap(
        first_visible_bbox[1],
        first_visible_bbox[3],
        second_visible_bbox[1],
        second_visible_bbox[3],
    )
    intersects = horizontal_overlap > 0.0 and vertical_overlap > 0.0

    return PrimitivePairMeasurements(
        first_primitive_id=first_primitive_id,
        second_primitive_id=second_primitive_id,
        first_primitive_kind=_primitive_kind(first_primitive),
        second_primitive_kind=_primitive_kind(second_primitive),
        first_bbox=first_primitive.bbox,
        second_bbox=second_primitive.bbox,
        first_visible_bbox=first_visible_bbox,
        second_visible_bbox=second_visible_bbox,
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
        horizontal_overlap=horizontal_overlap,
        vertical_overlap=vertical_overlap,
        horizontal_overlap_ratio=horizontal_overlap / min(first_width, second_width),
        vertical_overlap_ratio=vertical_overlap / min(first_height, second_height),
        is_disjoint=horizontal_gap > 0.0 or vertical_gap > 0.0,
        touches=not intersects and horizontal_gap == 0.0 and vertical_gap == 0.0,
        intersects=intersects,
        first_contains_second=_contains(first_visible_bbox, second_visible_bbox),
        second_contains_first=_contains(second_visible_bbox, first_visible_bbox),
        first_page_left_distance=first_visible_bbox[0],
        first_page_right_distance=page_width - first_visible_bbox[2],
        first_page_top_distance=first_visible_bbox[1],
        first_page_bottom_distance=page_height - first_visible_bbox[3],
        second_page_left_distance=second_visible_bbox[0],
        second_page_right_distance=page_width - second_visible_bbox[2],
        second_page_top_distance=second_visible_bbox[1],
        second_page_bottom_distance=page_height - second_visible_bbox[3],
        left_edge_delta=second_visible_bbox[0] - first_visible_bbox[0],
        right_edge_delta=second_visible_bbox[2] - first_visible_bbox[2],
        top_edge_delta=second_visible_bbox[1] - first_visible_bbox[1],
        bottom_edge_delta=second_visible_bbox[3] - first_visible_bbox[3],
        center_x_delta=_center(second_visible_bbox, axis=0) - _center(first_visible_bbox, axis=0),
        center_y_delta=_center(second_visible_bbox, axis=1) - _center(first_visible_bbox, axis=1),
    )


def _validate_primitive_id(primitive_id: str, field_name: str) -> None:
    if not isinstance(primitive_id, str) or not primitive_id:
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_primitive_kind(primitive_kind: PrimitiveKind, field_name: str) -> None:
    if primitive_kind not in {"text", "image", "drawing"}:
        raise ValueError(f"{field_name} must be text, image, or drawing")


def _validate_bbox(bbox: BBox, field_name: str) -> None:
    if not isinstance(bbox, tuple) or len(bbox) != 4:
        raise ValueError(f"{field_name} must be a tuple with 4 items")
    for index, coordinate in enumerate(bbox):
        _validate_finite_number(coordinate, f"{field_name}[{index}]")
    if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        raise ValueError(f"{field_name} coordinates are inverted")


def _validate_visible_bbox(bbox: BBox, field_name: str) -> None:
    _validate_bbox(bbox, field_name)
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError(f"{field_name} must be non-degenerate")
    if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        raise ValueError(f"{field_name} coordinates are inverted")


def _validate_finite_number(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite number")


def _validate_non_negative_number(value: float, field_name: str) -> None:
    _validate_finite_number(value, field_name)
    if value < 0.0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_ratio(value: float, field_name: str) -> None:
    _validate_finite_number(value, field_name)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _primitives_by_id(
    primitive_page: NormalizedPrimitivePage,
) -> dict[str, _Primitive]:
    return {
        primitive.primitive_id: primitive
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    }


def _require_primitive(
    primitives_by_id: dict[str, _Primitive],
    primitive_id: str,
) -> _Primitive:
    primitive = primitives_by_id.get(primitive_id)
    if primitive is None:
        raise ValueError(f"primitive_id does not exist: {primitive_id}")
    return primitive


def _primitive_kind(primitive: _Primitive) -> PrimitiveKind:
    if isinstance(primitive, TextPrimitive):
        return "text"
    if isinstance(primitive, ImageOccurrencePrimitive):
        return "image"
    return "drawing"


def _require_visible_bbox(
    primitive: _Primitive,
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
        raise PrimitiveNotVisibleOnPageError(primitive.primitive_id)
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


def _size(bbox: BBox) -> tuple[float, float]:
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _axis_gap(
    first_start: float, first_end: float, second_start: float, second_end: float
) -> float:
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


def _contains(container: BBox, contained: BBox) -> bool:
    return (
        container[0] <= contained[0]
        and container[1] <= contained[1]
        and container[2] >= contained[2]
        and container[3] >= contained[3]
    )


def _center(bbox: BBox, *, axis: Literal[0, 1]) -> float:
    return (bbox[axis] + bbox[axis + 2]) / 2.0
