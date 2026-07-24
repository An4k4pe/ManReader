"""Pure overlap measurements between one candidate bbox and one primitive bbox."""

from __future__ import annotations


def measure_candidate_primitive_overlap_ratio(
    candidate_bbox: tuple[float, float, float, float],
    primitive_bbox: tuple[float, float, float, float],
) -> float:
    """Return candidate intersection area relative to the primitive area."""

    candidate_x0, candidate_y0, candidate_x1, candidate_y1 = candidate_bbox
    primitive_x0, primitive_y0, primitive_x1, primitive_y1 = primitive_bbox
    overlap_width = max(0.0, min(candidate_x1, primitive_x1) - max(candidate_x0, primitive_x0))
    overlap_height = max(
        0.0,
        min(candidate_y1, primitive_y1) - max(candidate_y0, primitive_y0),
    )
    primitive_area = (primitive_x1 - primitive_x0) * (primitive_y1 - primitive_y0)
    if primitive_area <= 0.0:
        return 0.0
    return (overlap_width * overlap_height) / primitive_area
