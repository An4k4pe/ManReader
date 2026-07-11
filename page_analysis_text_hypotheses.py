"""Build elementary geometric text hypotheses from normalized primitives.

This module constructs one singleton ``GeometricTextHypothesis`` for each
geometrically admissible text primitive. It does not measure hypotheses, cluster
primitives, classify side-bands, or produce ``RegionCandidate`` values.

Admissible primitives are sorted by a canonical representation order based on
their visible bbox:

``(visible_y0, visible_x0, visible_y1, visible_x1, primitive_id)``.

This order is deterministic and is not a reading order.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_model import BBox
from primitive_model import NormalizedPrimitivePage, TextPrimitive

_DIRECTION_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class GeometricTextHypothesis:
    primitive_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.primitive_ids, tuple):
            raise ValueError("primitive_ids must be a tuple")
        if not self.primitive_ids:
            raise ValueError("primitive_ids must not be empty")
        for index, primitive_id in enumerate(self.primitive_ids):
            if not isinstance(primitive_id, str) or not primitive_id:
                raise ValueError(f"primitive_ids[{index}] must be a non-empty string")
        if len(self.primitive_ids) != len(set(self.primitive_ids)):
            raise ValueError("primitive_ids must not contain duplicates")


def build_geometric_text_hypotheses(
    primitive_page: NormalizedPrimitivePage,
) -> tuple[GeometricTextHypothesis, ...]:
    """Build singleton hypotheses for visible text compatible with this path."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    sortable_hypotheses: list[tuple[tuple[float, float, float, float, str], str]] = []

    for primitive in primitive_page.text_primitives:
        if not _has_compatible_orientation(primitive):
            continue
        visible_bbox = _visible_bbox(
            primitive.bbox,
            page_width=page_width,
            page_height=page_height,
        )
        if visible_bbox is None:
            continue
        sortable_hypotheses.append(
            (_canonical_order_key(visible_bbox, primitive.primitive_id), primitive.primitive_id)
        )

    return tuple(
        GeometricTextHypothesis(primitive_ids=(primitive_id,))
        for _, primitive_id in sorted(sortable_hypotheses)
    )


def _has_compatible_orientation(primitive: TextPrimitive) -> bool:
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


def _canonical_order_key(
    visible_bbox: BBox,
    primitive_id: str,
) -> tuple[float, float, float, float, str]:
    return (
        visible_bbox[1],
        visible_bbox[0],
        visible_bbox[3],
        visible_bbox[2],
        primitive_id,
    )
