"""Backend-observation contracts for ManReader.

Identifiers intentionally have limited guarantees in this first schema:

- ``source_id`` identifies an immutable or verified source and is not a path.
- ``page_id`` identifies a page within that source and is distinct from its index.
- ``capture_id`` identifies one capture artifact and may vary by backend or configuration.
- ``observation_id`` is local to one page capture and is not a content hash.
- ``resource_ref`` is backend-local and must not cross into normalized primitives.
- ``content_digest`` identifies content, not an occurrence; its algorithm is not fixed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from geometry_model import (
    AffineMatrix,
    BBox,
    PageGeometry,
    Point,
    RGBAColor,
    _validate_affine_matrix,
    _validate_bbox,
    _validate_finite_number,
    _validate_non_empty_string,
    _validate_non_negative_int,
    _validate_point,
    _validate_rgba_color,
)

type LinkTargetKind = Literal[
    "uri",
    "page",
    "named_destination",
    "unknown",
]
type BackendOrderKind = Literal[
    "extraction",
    "paint",
    "technical",
    "unknown",
]
type SourceRotation = Literal[0, 90, 180, 270]

_VALID_LINK_TARGET_KINDS = frozenset(
    {
        "uri",
        "page",
        "named_destination",
        "unknown",
    }
)
_VALID_BACKEND_ORDER_KINDS = frozenset(
    {
        "extraction",
        "paint",
        "technical",
        "unknown",
    }
)
_VALID_SOURCE_ROTATIONS = frozenset({0, 90, 180, 270})


def _validate_tuple(value: tuple[object, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")


def _validate_optional_non_empty_string(value: str | None, field_name: str) -> None:
    if value is not None:
        _validate_non_empty_string(value, field_name)


def _validate_optional_opacity(value: float | None, field_name: str) -> None:
    if value is None:
        return
    _validate_finite_number(value, field_name)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class CaptureError:
    code: str
    message: str
    observation_id: str | None = None
    recoverable: bool = True

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.code, "code")
        _validate_non_empty_string(self.message, "message")
        _validate_optional_non_empty_string(self.observation_id, "observation_id")
        if not isinstance(self.recoverable, bool):
            raise ValueError("recoverable must be a bool")


@dataclass(frozen=True, slots=True)
class BackendTextObservation:
    """One text run exactly as observed by a backend."""

    observation_id: str
    bbox: BBox
    text: str
    font_name: str | None = None
    font_size: float | None = None
    font_flags: int | None = None
    color: RGBAColor | None = None
    direction: Point | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.observation_id, "observation_id")
        _validate_bbox(self.bbox)
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        if self.font_name is not None and not isinstance(self.font_name, str):
            raise ValueError("font_name must be a string or None")
        if self.font_size is not None:
            _validate_finite_number(self.font_size, "font_size")
            if self.font_size <= 0.0:
                raise ValueError("font_size must be greater than zero")
        if self.font_flags is not None:
            _validate_non_negative_int(self.font_flags, "font_flags")
        if self.color is not None:
            _validate_rgba_color(self.color)
        if self.direction is not None:
            _validate_point(self.direction, "direction")
            if self.direction == (0.0, 0.0):
                raise ValueError("direction must not be the zero vector")


@dataclass(frozen=True, slots=True)
class BackendImageObservation:
    """One raster occurrence, separate from any canonical asset."""

    observation_id: str
    bbox: BBox
    resource_ref: str | None = None
    content_digest: str | None = None
    pixel_width: int | None = None
    pixel_height: int | None = None
    placement_transform: AffineMatrix | None = None
    has_alpha: bool | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.observation_id, "observation_id")
        _validate_bbox(self.bbox)
        _validate_optional_non_empty_string(self.resource_ref, "resource_ref")
        _validate_optional_non_empty_string(self.content_digest, "content_digest")
        if (self.pixel_width is None) != (self.pixel_height is None):
            raise ValueError("pixel_width and pixel_height must be provided together")
        if self.pixel_width is not None:
            _validate_non_negative_int(self.pixel_width, "pixel_width")
            _validate_non_negative_int(self.pixel_height, "pixel_height")  # type: ignore[arg-type]
            if self.pixel_width == 0 or self.pixel_height == 0:
                raise ValueError("pixel dimensions must be greater than zero")
        if self.placement_transform is not None:
            _validate_affine_matrix(self.placement_transform, "placement_transform")
        if self.has_alpha is not None and not isinstance(self.has_alpha, bool):
            raise ValueError("has_alpha must be a bool or None")


@dataclass(frozen=True, slots=True)
class DrawingCommand:
    """Backend-neutral geometric drawing command.

    ``kind`` is deliberately open-ended. Typical normalized values may include
    ``line``, ``rect``, ``quad``, ``cubic_bezier`` and ``unknown``.
    """

    kind: str
    points: tuple[Point, ...] = ()
    bbox: BBox | None = None
    orientation: int | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.kind, "kind")
        _validate_tuple(self.points, "points")
        for index, point in enumerate(self.points):
            _validate_point(point, f"points[{index}]")
        if self.bbox is not None:
            _validate_bbox(self.bbox)
        if self.orientation is not None and (
            isinstance(self.orientation, bool) or not isinstance(self.orientation, int)
        ):
            raise ValueError("orientation must be an integer or None")


@dataclass(frozen=True, slots=True)
class BackendDrawingObservation:
    observation_id: str
    bbox: BBox
    commands: tuple[DrawingCommand, ...] = ()
    stroke_width: float | None = None
    stroke_color: RGBAColor | None = None
    fill_color: RGBAColor | None = None
    stroke_opacity: float | None = None
    fill_opacity: float | None = None
    is_closed: bool | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.observation_id, "observation_id")
        _validate_bbox(self.bbox)
        _validate_tuple(self.commands, "commands")
        if not all(isinstance(command, DrawingCommand) for command in self.commands):
            raise ValueError("commands must contain DrawingCommand values")
        if self.stroke_width is not None:
            _validate_finite_number(self.stroke_width, "stroke_width")
            if self.stroke_width < 0.0:
                raise ValueError("stroke_width must be greater than or equal to zero")
        if self.stroke_color is not None:
            _validate_rgba_color(self.stroke_color, "stroke_color")
        if self.fill_color is not None:
            _validate_rgba_color(self.fill_color, "fill_color")
        _validate_optional_opacity(self.stroke_opacity, "stroke_opacity")
        _validate_optional_opacity(self.fill_opacity, "fill_opacity")
        if self.is_closed is not None and not isinstance(self.is_closed, bool):
            raise ValueError("is_closed must be a bool or None")


@dataclass(frozen=True, slots=True)
class BackendLinkObservation:
    observation_id: str
    bbox: BBox
    target_kind: LinkTargetKind
    uri: str | None = None
    target_page_index: int | None = None
    named_destination: str | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.observation_id, "observation_id")
        _validate_bbox(self.bbox)
        if self.target_kind not in _VALID_LINK_TARGET_KINDS:
            raise ValueError("target_kind is not supported")
        _validate_optional_non_empty_string(self.uri, "uri")
        _validate_optional_non_empty_string(self.named_destination, "named_destination")
        if self.target_page_index is not None:
            _validate_non_negative_int(self.target_page_index, "target_page_index")

        targets_present = sum(
            target is not None
            for target in (
                self.uri,
                self.target_page_index,
                self.named_destination,
            )
        )
        if self.target_kind == "uri":
            valid = self.uri is not None and targets_present == 1
        elif self.target_kind == "page":
            valid = self.target_page_index is not None and targets_present == 1
        elif self.target_kind == "named_destination":
            valid = self.named_destination is not None and targets_present == 1
        else:
            valid = targets_present <= 1
        if not valid:
            raise ValueError("link target fields are inconsistent with target_kind")


@dataclass(frozen=True, slots=True)
class BackendAnnotationObservation:
    observation_id: str
    bbox: BBox
    annotation_kind: str
    content: str | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.observation_id, "observation_id")
        _validate_bbox(self.bbox)
        _validate_non_empty_string(self.annotation_kind, "annotation_kind")
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("content must be a string or None")


@dataclass(frozen=True, slots=True)
class BackendPageCapture:
    """Immutable capture of one backend page.

    ``page_index`` is zero-based. ``page_geometry`` defines the coordinate
    space used by observations, crop/media boxes and placement transforms.
    ``source_rotation_degrees`` records source metadata only; it does not state
    whether rotation has already been applied. ``backend_order`` is never a
    reading order and may be partial or empty.
    """

    schema_version: str
    capture_id: str
    backend_name: str
    backend_version: str
    source_id: str
    page_id: str
    page_index: int
    page_geometry: PageGeometry
    source_rotation_degrees: SourceRotation = 0
    crop_box: BBox | None = None
    media_box: BBox | None = None
    text_observations: tuple[BackendTextObservation, ...] = ()
    image_observations: tuple[BackendImageObservation, ...] = ()
    drawing_observations: tuple[BackendDrawingObservation, ...] = ()
    link_observations: tuple[BackendLinkObservation, ...] = ()
    annotation_observations: tuple[BackendAnnotationObservation, ...] = ()
    backend_order_kind: BackendOrderKind | None = None
    backend_order: tuple[str, ...] = ()
    errors: tuple[CaptureError, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "schema_version",
            "capture_id",
            "backend_name",
            "backend_version",
            "source_id",
            "page_id",
        ):
            _validate_non_empty_string(getattr(self, field_name), field_name)
        _validate_non_negative_int(self.page_index, "page_index")
        if not isinstance(self.page_geometry, PageGeometry):
            raise ValueError("page_geometry must be a PageGeometry")
        if (
            isinstance(self.source_rotation_degrees, bool)
            or self.source_rotation_degrees not in _VALID_SOURCE_ROTATIONS
        ):
            raise ValueError("source_rotation_degrees is not supported")
        if self.crop_box is not None:
            _validate_bbox(self.crop_box, "crop_box")
        if self.media_box is not None:
            _validate_bbox(self.media_box, "media_box")

        typed_collections: tuple[tuple[str, tuple[object, ...], type[object]], ...] = (
            ("text_observations", self.text_observations, BackendTextObservation),
            ("image_observations", self.image_observations, BackendImageObservation),
            ("drawing_observations", self.drawing_observations, BackendDrawingObservation),
            ("link_observations", self.link_observations, BackendLinkObservation),
            (
                "annotation_observations",
                self.annotation_observations,
                BackendAnnotationObservation,
            ),
            ("errors", self.errors, CaptureError),
        )
        for field_name, values, expected_type in typed_collections:
            _validate_tuple(values, field_name)
            if not all(isinstance(value, expected_type) for value in values):
                raise ValueError(f"{field_name} contains an invalid value")

        _validate_tuple(self.backend_order, "backend_order")
        if self.backend_order_kind is not None:
            if self.backend_order_kind not in _VALID_BACKEND_ORDER_KINDS:
                raise ValueError("backend_order_kind is not supported")
        elif self.backend_order:
            raise ValueError("backend_order_kind is required when backend_order is not empty")

        observations = (
            *self.text_observations,
            *self.image_observations,
            *self.drawing_observations,
            *self.link_observations,
            *self.annotation_observations,
        )
        observation_ids = tuple(observation.observation_id for observation in observations)
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation_id values must be unique within a capture")

        if len(self.backend_order) != len(set(self.backend_order)):
            raise ValueError("backend_order must not contain duplicate IDs")
        known_ids = set(observation_ids)
        if any(observation_id not in known_ids for observation_id in self.backend_order):
            raise ValueError("backend_order contains an unknown observation ID")
        if any(
            error.observation_id is not None and error.observation_id not in known_ids
            for error in self.errors
        ):
            raise ValueError("CaptureError refers to an unknown observation ID")
