"""One-to-one normalization of backend observations into canonical primitives.

This first Milestone 3 adapter intentionally accepts only captures whose
geometry is already canonical: points, top-left origin, Y growing downward.
That is the coordinate space currently produced by ``pymupdf_capture.py``.

No layout, reading order, semantic classification, merging, deduplication, or
legacy-pipeline integration is performed here.
"""

from __future__ import annotations

import math

from capture_model import (
    BackendDrawingObservation,
    BackendImageObservation,
    BackendPageCapture,
    BackendTextObservation,
)
from geometry_model import AffineMatrix, Point
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)

NORMALIZED_PRIMITIVE_SCHEMA_VERSION = "1"
_IDENTITY_TRANSFORM: AffineMatrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def normalize_backend_page_capture(
    capture: BackendPageCapture,
) -> NormalizedPrimitivePage:
    """Convert supported observations one-to-one into canonical primitives.

    Link and annotation observations are not part of this first normalization
    slice. A capture containing either is rejected rather than silently
    discarding observations.

    Capture errors remain attached to the source capture. They do not prevent
    normalization of observations that were captured successfully.
    """

    _validate_supported_capture(capture)

    return NormalizedPrimitivePage(
        schema_version=NORMALIZED_PRIMITIVE_SCHEMA_VERSION,
        source_capture_id=capture.capture_id,
        source_id=capture.source_id,
        page_id=capture.page_id,
        page_index=capture.page_index,
        page_geometry=capture.page_geometry,
        capture_to_canonical_transform=_IDENTITY_TRANSFORM,
        text_primitives=tuple(
            _normalize_text_observation(observation)
            for observation in capture.text_observations
        ),
        image_primitives=tuple(
            _normalize_image_observation(observation)
            for observation in capture.image_observations
        ),
        drawing_primitives=tuple(
            _normalize_drawing_observation(observation)
            for observation in capture.drawing_observations
        ),
    )


def _validate_supported_capture(capture: BackendPageCapture) -> None:
    geometry = capture.page_geometry
    if geometry.unit != "pt" or geometry.coordinate_system != "top_left_y_down":
        raise ValueError(
            "capture geometry is not directly convertible to canonical coordinates; "
            "expected points with top-left origin and downward-growing Y axis"
        )
    if capture.link_observations:
        raise ValueError(
            "link observations are not supported by the first primitive normalizer"
        )
    if capture.annotation_observations:
        raise ValueError(
            "annotation observations are not supported by the first primitive normalizer"
        )


def _normalize_text_observation(
    observation: BackendTextObservation,
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=_primitive_id("text", observation.observation_id),
        bbox=observation.bbox,
        text=observation.text,
        source_observation_id=observation.observation_id,
        font_name=observation.font_name,
        font_size=observation.font_size,
        font_traits=(),
        color=observation.color,
        direction=_normalized_direction(observation.direction),
    )


def _normalize_image_observation(
    observation: BackendImageObservation,
) -> ImageOccurrencePrimitive:
    x0, y0, x1, y1 = observation.bbox
    if x0 == x1 or y0 == y1:
        raise ValueError(
            f"image observation {observation.observation_id!r} has a degenerate bbox"
        )
    return ImageOccurrencePrimitive(
        primitive_id=_primitive_id("image", observation.observation_id),
        bbox=observation.bbox,
        source_observation_id=observation.observation_id,
        content_digest=observation.content_digest,
        intrinsic_width=observation.pixel_width,
        intrinsic_height=observation.pixel_height,
        placement_transform=observation.placement_transform,
        has_alpha=observation.has_alpha,
    )


def _normalize_drawing_observation(
    observation: BackendDrawingObservation,
) -> DrawingPrimitive:
    return DrawingPrimitive(
        primitive_id=_primitive_id("drawing", observation.observation_id),
        bbox=observation.bbox,
        source_observation_id=observation.observation_id,
        commands=observation.commands,
        stroke_width=observation.stroke_width,
        stroke_color=observation.stroke_color,
        fill_color=observation.fill_color,
        stroke_opacity=observation.stroke_opacity,
        fill_opacity=observation.fill_opacity,
        is_closed=observation.is_closed,
    )


def _primitive_id(kind: str, observation_id: str) -> str:
    return f"primitive:{kind}:{observation_id}"


def _normalized_direction(direction: Point | None) -> Point | None:
    if direction is None:
        return None
    magnitude = math.hypot(direction[0], direction[1])
    # BackendTextObservation already rejects the zero vector.
    return (direction[0] / magnitude, direction[1] / magnitude)
