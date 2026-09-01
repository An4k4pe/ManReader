"""Canonical, immutable primitive contracts for ManReader.

Identifiers in this schema have deliberately limited semantics:

- ``primitive_id`` is local to one normalized page, is not semantic identity
  and is not a content hash.
- ``source_observation_id`` identifies the single capture observation from
  which the primitive was produced.
- ``content_digest`` identifies content rather than its page occurrence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from capture_model import DrawingCommand
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


def _validate_normalized_direction(value: Point) -> None:
    _validate_point(value, "direction")
    magnitude = math.hypot(value[0], value[1])
    if magnitude == 0.0:
        raise ValueError("direction must not be the zero vector")
    if not math.isclose(magnitude, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("direction must be normalized")


@dataclass(frozen=True, slots=True)
class TextPrimitive:
    primitive_id: str
    bbox: BBox
    text: str
    source_observation_id: str
    font_name: str | None = None
    font_size: float | None = None
    font_traits: tuple[str, ...] = ()
    color: RGBAColor | None = None
    direction: Point | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.primitive_id, "primitive_id")
        _validate_non_empty_string(self.source_observation_id, "source_observation_id")
        _validate_bbox(self.bbox)
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        if self.font_name is not None and not isinstance(self.font_name, str):
            raise ValueError("font_name must be a string or None")
        if self.font_size is not None:
            _validate_finite_number(self.font_size, "font_size")
            if self.font_size <= 0.0:
                raise ValueError("font_size must be greater than zero")
        _validate_tuple(self.font_traits, "font_traits")
        for trait in self.font_traits:
            _validate_non_empty_string(trait, "font_traits item")
        if len(self.font_traits) != len(set(self.font_traits)):
            raise ValueError("font_traits must not contain duplicates")
        if self.color is not None:
            _validate_rgba_color(self.color)
        if self.direction is not None:
            _validate_normalized_direction(self.direction)


@dataclass(frozen=True, slots=True)
class ImageOccurrencePrimitive:
    primitive_id: str
    bbox: BBox
    source_observation_id: str
    content_digest: str | None = None
    intrinsic_width: int | None = None
    intrinsic_height: int | None = None
    placement_transform: AffineMatrix | None = None
    has_alpha: bool | None = None
    # Se la sorgente conserva davvero un raster per questa collocazione.
    #
    # **Non e' una classificazione**, ed e' per questo che sta qui accanto a
    # `has_alpha` e non fra i campi vietati: dice cosa il backend ha trovato, non
    # che cosa la collocazione sia. Chi decide che farne sta a valle.
    #
    # Serve perche' `page.get_image_info()` non legge le risorse del PDF: fa
    # percorrere la pagina al renderer e registra ogni disegno di raster,
    # **compresi quelli che il renderer sintetizza** da contenuto che immagine non
    # e'. Misurato sul corpus il 31 agosto 2026: 19168 collocazioni su 39727 --
    # il 48% -- non hanno risorsa memorizzata. Su Fab sono il 91%, e sono
    # riempimenti a gradiente (`PatternType 2, ShadingType 2`); su DB il 48%, e
    # sono maschere morbide di `ExtGState` (153 voci `/SMask` = 153 collocazioni).
    # Operatori di immagine inline nel corpus: **zero**.
    has_stored_resource: bool | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.primitive_id, "primitive_id")
        _validate_non_empty_string(self.source_observation_id, "source_observation_id")
        _validate_bbox(self.bbox)
        if self.bbox[0] == self.bbox[2] or self.bbox[1] == self.bbox[3]:
            raise ValueError("image bbox must be non-degenerate")
        _validate_optional_non_empty_string(self.content_digest, "content_digest")
        if (self.intrinsic_width is None) != (self.intrinsic_height is None):
            raise ValueError(
                "intrinsic_width and intrinsic_height must be provided together"
            )
        if self.intrinsic_width is not None:
            _validate_non_negative_int(self.intrinsic_width, "intrinsic_width")
            _validate_non_negative_int(
                self.intrinsic_height,  # type: ignore[arg-type]
                "intrinsic_height",
            )
            if self.intrinsic_width == 0 or self.intrinsic_height == 0:
                raise ValueError("intrinsic dimensions must be greater than zero")
        if self.placement_transform is not None:
            _validate_affine_matrix(self.placement_transform, "placement_transform")
        if self.has_alpha is not None and not isinstance(self.has_alpha, bool):
            raise ValueError("has_alpha must be a bool or None")
        if self.has_stored_resource is not None and not isinstance(
            self.has_stored_resource, bool
        ):
            raise ValueError("has_stored_resource must be a bool or None")


@dataclass(frozen=True, slots=True)
class DrawingPrimitive:
    primitive_id: str
    bbox: BBox
    source_observation_id: str
    commands: tuple[DrawingCommand, ...] = ()
    stroke_width: float | None = None
    stroke_color: RGBAColor | None = None
    fill_color: RGBAColor | None = None
    stroke_opacity: float | None = None
    fill_opacity: float | None = None
    is_closed: bool | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.primitive_id, "primitive_id")
        _validate_non_empty_string(self.source_observation_id, "source_observation_id")
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
class NormalizedPrimitivePage:
    """One canonical primitive page.

    Canonical geometry is always in points with a top-left origin and a
    downward-growing Y axis. ``capture_to_canonical_transform`` is mandatory,
    including when it is the identity matrix.
    """

    schema_version: str
    source_capture_id: str
    source_id: str
    page_id: str
    page_index: int
    page_geometry: PageGeometry
    capture_to_canonical_transform: AffineMatrix
    text_primitives: tuple[TextPrimitive, ...] = ()
    image_primitives: tuple[ImageOccurrencePrimitive, ...] = ()
    drawing_primitives: tuple[DrawingPrimitive, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "schema_version",
            "source_capture_id",
            "source_id",
            "page_id",
        ):
            _validate_non_empty_string(getattr(self, field_name), field_name)
        _validate_non_negative_int(self.page_index, "page_index")
        if not isinstance(self.page_geometry, PageGeometry):
            raise ValueError("page_geometry must be a PageGeometry")
        if self.page_geometry.unit != "pt":
            raise ValueError("normalized page geometry must use points")
        if self.page_geometry.coordinate_system != "top_left_y_down":
            raise ValueError(
                "normalized page geometry must use top_left_y_down coordinates"
            )
        _validate_affine_matrix(
            self.capture_to_canonical_transform,
            "capture_to_canonical_transform",
        )

        typed_collections: tuple[tuple[str, tuple[object, ...], type[object]], ...] = (
            ("text_primitives", self.text_primitives, TextPrimitive),
            ("image_primitives", self.image_primitives, ImageOccurrencePrimitive),
            ("drawing_primitives", self.drawing_primitives, DrawingPrimitive),
        )
        for field_name, values, expected_type in typed_collections:
            _validate_tuple(values, field_name)
            if not all(isinstance(value, expected_type) for value in values):
                raise ValueError(f"{field_name} contains an invalid value")

        primitives = (
            *self.text_primitives,
            *self.image_primitives,
            *self.drawing_primitives,
        )
        primitive_ids = tuple(primitive.primitive_id for primitive in primitives)
        if len(primitive_ids) != len(set(primitive_ids)):
            raise ValueError("primitive_id values must be unique within a page")
