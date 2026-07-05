"""Shared geometry value types for ManReader capture and primitive contracts.

Affine matrices use the six-value convention ``(a, b, c, d, e, f)``:

    x' = a*x + c*y + e
    y' = b*x + d*y + f
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

type BBox = tuple[float, float, float, float]
type Point = tuple[float, float]
type AffineMatrix = tuple[float, float, float, float, float, float]
type RGBAColor = tuple[float, float, float, float]

type Unit = Literal["pt", "px"]
type CoordinateSystem = Literal[
    "top_left_y_down",
    "bottom_left_y_up",
]

_VALID_UNITS = frozenset({"pt", "px"})
_VALID_COORDINATE_SYSTEMS = frozenset(
    {
        "top_left_y_down",
        "bottom_left_y_up",
    }
)


def _validate_finite_number(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be a finite number")


def _validate_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _validate_tuple_length(value: tuple[object, ...], length: int, field_name: str) -> None:
    if not isinstance(value, tuple) or len(value) != length:
        raise ValueError(f"{field_name} must be a tuple with {length} items")


def _validate_bbox(value: BBox, field_name: str = "bbox") -> None:
    _validate_tuple_length(value, 4, field_name)
    for index, coordinate in enumerate(value):
        _validate_finite_number(coordinate, f"{field_name}[{index}]")
    x0, y0, x1, y1 = value
    if x0 > x1 or y0 > y1:
        raise ValueError(f"{field_name} coordinates are inverted")


def _validate_point(value: Point, field_name: str = "point") -> None:
    _validate_tuple_length(value, 2, field_name)
    for index, coordinate in enumerate(value):
        _validate_finite_number(coordinate, f"{field_name}[{index}]")


def _validate_affine_matrix(
    value: AffineMatrix,
    field_name: str = "affine_matrix",
) -> None:
    _validate_tuple_length(value, 6, field_name)
    for index, component in enumerate(value):
        _validate_finite_number(component, f"{field_name}[{index}]")


def _validate_rgba_color(value: RGBAColor, field_name: str = "color") -> None:
    _validate_tuple_length(value, 4, field_name)
    for index, component in enumerate(value):
        _validate_finite_number(component, f"{field_name}[{index}]")
        if not 0.0 <= component <= 1.0:
            raise ValueError(f"{field_name}[{index}] must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class PageGeometry:
    """Geometry of a page coordinate space, without source or page identity."""

    width: float
    height: float
    unit: Unit
    coordinate_system: CoordinateSystem

    def __post_init__(self) -> None:
        _validate_finite_number(self.width, "width")
        _validate_finite_number(self.height, "height")
        if self.width <= 0.0:
            raise ValueError("width must be greater than zero")
        if self.height <= 0.0:
            raise ValueError("height must be greater than zero")
        if self.unit not in _VALID_UNITS:
            raise ValueError("unit is not supported")
        if self.coordinate_system not in _VALID_COORDINATE_SYSTEMS:
            raise ValueError("coordinate_system is not supported")
