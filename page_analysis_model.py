"""Page-level layout analysis contracts for region graph shadow mode.

This module defines data-only contracts. It does not run detectors, persist JSON,
validate primitive existence, or integrate with the legacy pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from geometry_model import (
    BBox,
    _validate_bbox,
    _validate_non_empty_string,
)

PAGE_ANALYSIS_SCHEMA_VERSION = "1.0"

_STRUCTURAL_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


def _validate_structural_kind(value: str) -> None:
    if not isinstance(value, str) or _STRUCTURAL_KIND_PATTERN.fullmatch(value) is None:
        raise ValueError("structural_kind must be a namespaced lowercase structural kind")


def _validate_primitive_ids(value: tuple[str, ...]) -> None:
    if not isinstance(value, tuple):
        raise ValueError("primitive_ids must be a tuple")

    seen: set[str] = set()
    for index, primitive_id in enumerate(value):
        _validate_non_empty_string(primitive_id, f"primitive_ids[{index}]")
        if primitive_id in seen:
            raise ValueError("primitive_ids must not contain duplicates")
        seen.add(primitive_id)


@dataclass(frozen=True, slots=True)
class LayoutRegion:
    """Structural page-local region referencing primitive IDs only."""

    region_id: str
    page_id: str
    bbox: BBox
    structural_kind: str
    primitive_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.region_id, "region_id")
        _validate_non_empty_string(self.page_id, "page_id")
        _validate_bbox(self.bbox)
        x0, y0, x1, y1 = self.bbox
        if x0 >= x1:
            raise ValueError("bbox must be non-degenerate on the X axis")
        if y0 >= y1:
            raise ValueError("bbox must be non-degenerate on the Y axis")
        _validate_structural_kind(self.structural_kind)
        _validate_primitive_ids(self.primitive_ids)


@dataclass(frozen=True, slots=True)
class PageAnalysis:
    """Page-level structural analysis.

    The order of ``regions`` is only representation order. It is not reading
    order, geometric order, structural order, or any other structural constraint.
    """

    schema_version: str
    generation_id: str
    page_id: str
    regions: tuple[LayoutRegion, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != PAGE_ANALYSIS_SCHEMA_VERSION:
            raise ValueError("schema_version is not supported")
        _validate_non_empty_string(self.generation_id, "generation_id")
        _validate_non_empty_string(self.page_id, "page_id")
        if not isinstance(self.regions, tuple):
            raise ValueError("regions must be a tuple")

        seen: set[str] = set()
        for index, region in enumerate(self.regions):
            if not isinstance(region, LayoutRegion):
                raise ValueError(f"regions[{index}] must be a LayoutRegion")
            if region.page_id != self.page_id:
                raise ValueError("regions must belong to the same page_id")
            if region.region_id in seen:
                raise ValueError("region_id values must be unique within the page")
            seen.add(region.region_id)
