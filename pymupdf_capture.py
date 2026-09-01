"""PyMuPDF shadow capture adapter for ManReader.

This module converts one ``fitz.Page`` into an immutable
``BackendPageCapture`` without invoking legacy extraction, layout analysis,
normalization, asset export, or rendering.

Text is requested with ``sort=False``. The resulting order is preserved as
backend extraction order and must not be interpreted as canonical reading
order.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeGuard, cast

import fitz

from capture_model import (
    BackendDrawingObservation,
    BackendImageObservation,
    BackendPageCapture,
    BackendTextObservation,
    CaptureError,
    DrawingCommand,
)
from geometry_model import AffineMatrix, BBox, PageGeometry, Point, RGBAColor

CAPTURE_SCHEMA_VERSION = "1"
_BACKEND_NAME = "PyMuPDF"


def capture_pymupdf_page(
    page: fitz.Page,
    *,
    source_id: str,
    page_id: str,
    capture_id: str,
) -> BackendPageCapture:
    """Capture page geometry and raw text spans from one PyMuPDF page.

    Identity is supplied by the caller because this adapter must not invent
    source, page, or capture identity. The page index is taken from
    ``page.number`` and remains zero-based.

    The capture coordinate space is the unrotated PyMuPDF text-page space:
    points, top-left origin, Y growing downward. Source rotation is recorded
    separately and is not applied by this adapter.
    """

    text_page = cast(
        Mapping[str, Any],
        page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT, sort=False),
    )

    width = _required_positive_float(text_page, "width")
    height = _required_positive_float(text_page, "height")
    page_geometry = PageGeometry(
        width=width,
        height=height,
        unit="pt",
        coordinate_system="top_left_y_down",
    )

    observations: list[BackendTextObservation] = []
    image_observations: list[BackendImageObservation] = []
    drawing_observations: list[BackendDrawingObservation] = []
    errors: list[CaptureError] = []

    raw_blocks = text_page.get("blocks", ())
    if not _is_sequence(raw_blocks):
        raise ValueError("PyMuPDF text dictionary 'blocks' must be a sequence")

    for block_index, raw_block in enumerate(raw_blocks):
        if not isinstance(raw_block, Mapping):
            errors.append(
                CaptureError(
                    code="invalid_text_block",
                    message=f"Text block {block_index} is not a mapping",
                )
            )
            continue

        if raw_block.get("type") != 0:
            continue

        raw_lines = raw_block.get("lines", ())
        if not _is_sequence(raw_lines):
            errors.append(
                CaptureError(
                    code="invalid_text_lines",
                    message=f"Text block {block_index} has invalid lines",
                )
            )
            continue

        for line_index, raw_line in enumerate(raw_lines):
            if not isinstance(raw_line, Mapping):
                errors.append(
                    CaptureError(
                        code="invalid_text_line",
                        message=(
                            f"Text line {block_index}:{line_index} is not a mapping"
                        ),
                    )
                )
                continue

            direction = _optional_point(raw_line.get("dir"), "line direction")
            raw_spans = raw_line.get("spans", ())
            if not _is_sequence(raw_spans):
                errors.append(
                    CaptureError(
                        code="invalid_text_spans",
                        message=(
                            f"Text line {block_index}:{line_index} has invalid spans"
                        ),
                    )
                )
                continue

            for span_index, raw_span in enumerate(raw_spans):
                observation_id = (
                    f"text:b{block_index:04d}:l{line_index:04d}:s{span_index:04d}"
                )
                if not isinstance(raw_span, Mapping):
                    errors.append(
                        CaptureError(
                            code="invalid_text_span",
                            message=(
                                "Text span "
                                f"{block_index}:{line_index}:{span_index} "
                                "is not a mapping"
                            ),
                        )
                    )
                    continue

                try:
                    observation = BackendTextObservation(
                        observation_id=observation_id,
                        bbox=_required_bbox(raw_span, "bbox"),
                        text=_required_string(raw_span, "text"),
                        font_name=_optional_string(raw_span.get("font"), "font"),
                        font_size=_optional_float(raw_span.get("size"), "size"),
                        font_flags=_optional_int(raw_span.get("flags"), "flags"),
                        color=_span_rgba_color(raw_span),
                        direction=direction,
                    )
                except (TypeError, ValueError) as exc:
                    errors.append(
                        CaptureError(
                            code="invalid_text_span",
                            message=str(exc),
                        )
                    )
                    continue

                observations.append(observation)

    image_observations.extend(_capture_image_observations(page, errors))
    drawing_observations.extend(_capture_drawing_observations(page, errors))

    backend_order = tuple(observation.observation_id for observation in observations)
    page_index = page.number
    if page_index is None or page_index < 0:
        raise ValueError("PyMuPDF page must belong to an open document")

    rotation = int(page.rotation)
    if rotation not in {0, 90, 180, 270}:
        raise ValueError(f"Unsupported PyMuPDF page rotation: {rotation}")

    return BackendPageCapture(
        schema_version=CAPTURE_SCHEMA_VERSION,
        capture_id=capture_id,
        backend_name=_BACKEND_NAME,
        backend_version=fitz.VersionBind,
        source_id=source_id,
        page_id=page_id,
        page_index=page_index,
        page_geometry=page_geometry,
        source_rotation_degrees=cast(Any, rotation),
        crop_box=None,
        media_box=None,
        text_observations=tuple(observations),
        image_observations=tuple(image_observations),
        drawing_observations=tuple(drawing_observations),
        backend_order_kind="extraction" if backend_order else None,
        backend_order=backend_order,
        errors=tuple(errors),
    )


def _required_positive_float(payload: Mapping[str, Any], key: str) -> float:
    value = _required_float(payload, key)
    if value <= 0.0:
        raise ValueError(f"PyMuPDF field {key!r} must be greater than zero")
    return value


def _required_float(payload: Mapping[str, Any], key: str) -> float:
    if key not in payload:
        raise ValueError(f"PyMuPDF payload is missing field {key!r}")
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"PyMuPDF field {key!r} must be numeric")
    return float(value)


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"PyMuPDF {field_name} must be numeric or None")
    return float(value)


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"PyMuPDF {field_name} must be an integer or None")
    return value


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"PyMuPDF payload is missing field {key!r}")
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"PyMuPDF field {key!r} must be a string")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"PyMuPDF {field_name} must be a string or None")
    return value


def _required_bbox(payload: Mapping[str, Any], key: str) -> BBox:
    if key not in payload:
        raise ValueError(f"PyMuPDF payload is missing field {key!r}")
    return _bbox_from_object(payload[key], f"field {key!r}")


def _bbox_from_object(value: object, field_name: str) -> BBox:
    if isinstance(value, fitz.Rect):
        return (
            float(value.x0),
            float(value.y0),
            float(value.x1),
            float(value.y1),
        )
    if _is_sequence(value) and len(value) == 4:
        coordinates = tuple(_coordinate(component, field_name) for component in value)
        return cast(BBox, coordinates)
    raise ValueError(f"PyMuPDF {field_name} must be rect-like")


def _optional_point(value: object, field_name: str) -> Point | None:
    if value is None:
        return None
    if not _is_sequence(value) or len(value) != 2:
        raise ValueError(f"PyMuPDF {field_name} must contain two coordinates")
    coordinates = tuple(_coordinate(component, field_name) for component in value)
    return cast(Point, coordinates)


def _coordinate(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"PyMuPDF {field_name} contains a non-numeric coordinate")
    return float(value)


def _span_rgba_color(span: Mapping[str, Any]) -> RGBAColor | None:
    raw_color = span.get("color")
    if raw_color is None:
        return None
    if isinstance(raw_color, bool) or not isinstance(raw_color, int):
        raise ValueError("PyMuPDF span color must be an integer or None")
    if not 0 <= raw_color <= 0xFFFFFF:
        raise ValueError("PyMuPDF span color must be in the range 0x000000-0xFFFFFF")

    raw_alpha = span.get("alpha", 255)
    if isinstance(raw_alpha, bool) or not isinstance(raw_alpha, int):
        raise ValueError("PyMuPDF span alpha must be an integer")
    if not 0 <= raw_alpha <= 255:
        raise ValueError("PyMuPDF span alpha must be in the range 0-255")

    red = ((raw_color >> 16) & 0xFF) / 255.0
    green = ((raw_color >> 8) & 0xFF) / 255.0
    blue = (raw_color & 0xFF) / 255.0
    alpha = raw_alpha / 255.0
    return (red, green, blue, alpha)


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _capture_image_observations(
    page: fitz.Page,
    errors: list[CaptureError],
) -> tuple[BackendImageObservation, ...]:
    observations: list[BackendImageObservation] = []
    try:
        raw_images = page.get_image_info(hashes=True, xrefs=True)
    except (RuntimeError, ValueError) as exc:
        errors.append(
            CaptureError(
                code="image_capture_failed",
                message=f"PyMuPDF image capture failed: {exc}",
            )
        )
        return ()

    for image_index, raw_image in enumerate(raw_images):
        observation_id = f"image:i{image_index:04d}"
        if not isinstance(raw_image, Mapping):
            errors.append(
                CaptureError(
                    code="invalid_image_observation",
                    message=f"Image observation {image_index} is not a mapping",
                )
            )
            continue
        try:
            xref = _optional_int(raw_image.get("xref"), "image xref")
            resource_ref = f"xref:{xref}" if xref is not None and xref > 0 else None
            # `xref == 0` non e' «xref sconosciuto»: e' PyMuPDF che dichiara di
            # non avere una risorsa memorizzata per questa collocazione, perche'
            # il raster l'ha sintetizzato il renderer. Le due cose si tengono
            # separate da `xref is None`, dove il backend non dice niente.
            has_stored_resource = None if xref is None else xref > 0
            digest = _optional_digest(raw_image.get("digest"))
            has_mask = raw_image.get("has-mask")
            if has_mask is not None and not isinstance(has_mask, bool):
                raise ValueError("PyMuPDF image has-mask must be a bool or None")

            observation = BackendImageObservation(
                observation_id=observation_id,
                bbox=_required_bbox(raw_image, "bbox"),
                resource_ref=resource_ref,
                content_digest=digest,
                pixel_width=_required_positive_int(raw_image, "width"),
                pixel_height=_required_positive_int(raw_image, "height"),
                placement_transform=_required_affine_matrix(raw_image, "transform"),
                has_alpha=has_mask,
                has_stored_resource=has_stored_resource,
            )
        except (TypeError, ValueError) as exc:
            errors.append(
                CaptureError(
                    code="invalid_image_observation",
                    message=f"Image observation {image_index}: {exc}",
                )
            )
            continue
        observations.append(observation)

    return tuple(observations)


def _capture_drawing_observations(
    page: fitz.Page,
    errors: list[CaptureError],
) -> tuple[BackendDrawingObservation, ...]:
    observations: list[BackendDrawingObservation] = []
    try:
        raw_drawings = page.get_drawings()
    except (RuntimeError, ValueError) as exc:
        errors.append(
            CaptureError(
                code="drawing_capture_failed",
                message=f"PyMuPDF drawing capture failed: {exc}",
            )
        )
        return ()

    for drawing_index, raw_drawing in enumerate(raw_drawings):
        observation_id = f"drawing:p{drawing_index:04d}"
        if not isinstance(raw_drawing, Mapping):
            errors.append(
                CaptureError(
                    code="invalid_drawing_observation",
                    message=f"Drawing observation {drawing_index} is not a mapping",
                )
            )
            continue

        try:
            raw_items = raw_drawing.get("items", ())
            if not _is_sequence(raw_items):
                raise ValueError("PyMuPDF drawing items must be a sequence")
            commands = tuple(
                _drawing_command(raw_item, drawing_index, item_index)
                for item_index, raw_item in enumerate(raw_items)
            )
            observation = BackendDrawingObservation(
                observation_id=observation_id,
                bbox=_required_bbox(raw_drawing, "rect"),
                commands=commands,
                stroke_width=_optional_float(raw_drawing.get("width"), "drawing width"),
                stroke_color=_optional_rgb_color(
                    raw_drawing.get("color"),
                    "drawing stroke color",
                ),
                fill_color=_optional_rgb_color(
                    raw_drawing.get("fill"),
                    "drawing fill color",
                ),
                stroke_opacity=_optional_float(
                    raw_drawing.get("stroke_opacity"),
                    "drawing stroke opacity",
                ),
                fill_opacity=_optional_float(
                    raw_drawing.get("fill_opacity"),
                    "drawing fill opacity",
                ),
                is_closed=_optional_bool(
                    raw_drawing.get("closePath"),
                    "drawing closePath",
                ),
            )
        except (TypeError, ValueError) as exc:
            errors.append(
                CaptureError(
                    code="invalid_drawing_observation",
                    message=f"Drawing observation {drawing_index}: {exc}",
                )
            )
            continue
        observations.append(observation)

    return tuple(observations)


def _drawing_command(
    raw_item: object,
    drawing_index: int,
    item_index: int,
) -> DrawingCommand:
    if not _is_sequence(raw_item) or not raw_item:
        raise ValueError(
            f"PyMuPDF drawing item {drawing_index}:{item_index} must be a sequence"
        )
    raw_kind = raw_item[0]
    if not isinstance(raw_kind, str) or not raw_kind:
        raise ValueError(
            f"PyMuPDF drawing item {drawing_index}:{item_index} has invalid kind"
        )

    if raw_kind == "l":
        return DrawingCommand(
            kind="line",
            points=(
                _required_point_value(raw_item, 1, "line start"),
                _required_point_value(raw_item, 2, "line end"),
            ),
        )
    if raw_kind == "c":
        return DrawingCommand(
            kind="cubic_bezier",
            points=tuple(
                _required_point_value(raw_item, index, "cubic point")
                for index in range(1, 5)
            ),
        )
    if raw_kind == "re":
        return DrawingCommand(
            kind="rect",
            bbox=_required_bbox_value(raw_item, 1, "rectangle"),
            orientation=_required_int_value(raw_item, 2, "rectangle orientation"),
        )
    if raw_kind == "qu":
        quad = _required_quad_points(raw_item, 1)
        return DrawingCommand(kind="quad", points=quad)

    points = tuple(
        point
        for component in raw_item[1:]
        if (point := _optional_point_object(component)) is not None
    )
    return DrawingCommand(kind=f"unknown:{raw_kind}", points=points)


def _required_positive_int(payload: Mapping[str, Any], key: str) -> int:
    if key not in payload:
        raise ValueError(f"PyMuPDF payload is missing field {key!r}")
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"PyMuPDF field {key!r} must be a positive integer")
    return value


def _required_affine_matrix(
    payload: Mapping[str, Any],
    key: str,
) -> AffineMatrix:
    if key not in payload:
        raise ValueError(f"PyMuPDF payload is missing field {key!r}")
    value = payload[key]
    if not _is_sequence(value) or len(value) != 6:
        raise ValueError(f"PyMuPDF field {key!r} must contain six components")
    components = tuple(_coordinate(component, key) for component in value)
    return cast(AffineMatrix, components)


def _optional_digest(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"md5:{value.hex()}"
    raise ValueError("PyMuPDF image digest must be bytes or None")


def _optional_rgb_color(value: object, field_name: str) -> RGBAColor | None:
    if value is None:
        return None
    if not _is_sequence(value) or len(value) != 3:
        raise ValueError(f"PyMuPDF {field_name} must contain three components")
    components = tuple(_coordinate(component, field_name) for component in value)
    if any(component < 0.0 or component > 1.0 for component in components):
        raise ValueError(f"PyMuPDF {field_name} components must be between 0 and 1")
    return (components[0], components[1], components[2], 1.0)


def _optional_bool(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"PyMuPDF {field_name} must be a bool or None")
    return value


def _required_point_value(
    raw_item: Sequence[object],
    index: int,
    field_name: str,
) -> Point:
    if index >= len(raw_item):
        raise ValueError(f"PyMuPDF {field_name} is missing")
    point = _optional_point_object(raw_item[index])
    if point is None:
        raise ValueError(f"PyMuPDF {field_name} must be point-like")
    return point


def _required_bbox_value(
    raw_item: Sequence[object],
    index: int,
    field_name: str,
) -> BBox:
    if index >= len(raw_item):
        raise ValueError(f"PyMuPDF {field_name} is missing")
    return _bbox_from_object(raw_item[index], field_name)


def _required_int_value(
    raw_item: Sequence[object],
    index: int,
    field_name: str,
) -> int:
    if index >= len(raw_item):
        raise ValueError(f"PyMuPDF {field_name} is missing")
    value = raw_item[index]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"PyMuPDF {field_name} must be an integer")
    return value


def _required_quad_points(
    raw_item: Sequence[object],
    index: int,
) -> tuple[Point, ...]:
    if index >= len(raw_item):
        raise ValueError("PyMuPDF quad is missing")
    value = raw_item[index]
    try:
        quad = fitz.Quad(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("PyMuPDF quad must be quad-like") from exc
    return tuple(
        (float(point.x), float(point.y))
        for point in (quad.ul, quad.ur, quad.lr, quad.ll)
    )


def _optional_point_object(value: object) -> Point | None:
    if isinstance(value, fitz.Point):
        return (float(value.x), float(value.y))
    if _is_sequence(value) and len(value) == 2:
        return (
            _coordinate(value[0], "point"),
            _coordinate(value[1], "point"),
        )
    return None
