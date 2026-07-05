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

from capture_model import BackendPageCapture, BackendTextObservation, CaptureError
from geometry_model import BBox, PageGeometry, Point, RGBAColor

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
    value = payload[key]
    if not _is_sequence(value) or len(value) != 4:
        raise ValueError(f"PyMuPDF field {key!r} must contain four coordinates")
    coordinates = tuple(_coordinate(component, key) for component in value)
    return cast(BBox, coordinates)


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
