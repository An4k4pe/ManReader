"""Page-level layout analysis contracts for region graph shadow mode.

This module defines data-only contracts. It does not run detectors, persist JSON,
validate primitive existence, or integrate with the legacy pipeline.

Region relations are directed structural edges from ``source_region_id`` to
``target_region_id``. ``layout.contains`` means the source structurally contains
the target. ``layout.precedes`` means the source structurally precedes the target
as a partial structural constraint, not as final reading order or semantic order.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from geometry_model import (
    BBox,
    _validate_bbox,
    _validate_non_empty_string,
)

PAGE_ANALYSIS_SCHEMA_VERSION = "1.0"

_VALID_RELATION_KINDS = frozenset(
    {
        "layout.contains",
        "layout.precedes",
    }
)
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


def _validate_acyclic_relations(
    relations: Iterable[RegionRelation],
    relation_kind: str,
) -> None:
    graph: dict[str, list[str]] = {}
    indegree: dict[str, int] = {}
    for relation in relations:
        if relation.relation_kind == relation_kind:
            graph.setdefault(relation.source_region_id, []).append(relation.target_region_id)
            graph.setdefault(relation.target_region_id, [])
            indegree.setdefault(relation.source_region_id, 0)
            indegree[relation.target_region_id] = indegree.get(relation.target_region_id, 0) + 1

    ready = [region_id for region_id, degree in indegree.items() if degree == 0]
    processed_count = 0
    ready_index = 0

    while ready_index < len(ready):
        region_id = ready[ready_index]
        ready_index += 1
        processed_count += 1

        for target_id in graph[region_id]:
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)

    if processed_count < len(indegree):
        raise ValueError(f"{relation_kind} relations must be acyclic")


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
class RegionRelation:
    """Directed structural relation between two page-local layout regions."""

    relation_id: str
    relation_kind: str
    source_region_id: str
    target_region_id: str

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.relation_id, "relation_id")
        if self.relation_kind not in _VALID_RELATION_KINDS:
            raise ValueError("relation_kind is not supported")
        _validate_non_empty_string(self.source_region_id, "source_region_id")
        _validate_non_empty_string(self.target_region_id, "target_region_id")
        if self.source_region_id == self.target_region_id:
            raise ValueError("source_region_id and target_region_id must be different")


@dataclass(frozen=True, slots=True)
class PageAnalysis:
    """Page-level structural analysis.

    The order of ``regions`` is only representation order. It is not reading
    order, geometric order, structural order, or any other structural constraint.

    The order of ``relations`` is only representation order. It is not priority,
    reading order, or structural order.
    """

    schema_version: str
    generation_id: str
    page_id: str
    regions: tuple[LayoutRegion, ...] = ()
    relations: tuple[RegionRelation, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != PAGE_ANALYSIS_SCHEMA_VERSION:
            raise ValueError("schema_version is not supported")
        _validate_non_empty_string(self.generation_id, "generation_id")
        _validate_non_empty_string(self.page_id, "page_id")
        if not isinstance(self.regions, tuple):
            raise ValueError("regions must be a tuple")
        if not isinstance(self.relations, tuple):
            raise ValueError("relations must be a tuple")

        region_ids: set[str] = set()
        for index, region in enumerate(self.regions):
            if not isinstance(region, LayoutRegion):
                raise ValueError(f"regions[{index}] must be a LayoutRegion")
            if region.page_id != self.page_id:
                raise ValueError("regions must belong to the same page_id")
            if region.region_id in region_ids:
                raise ValueError("region_id values must be unique within the page")
            region_ids.add(region.region_id)

        relation_ids: set[str] = set()
        logical_edges: set[tuple[str, str, str]] = set()
        for index, relation in enumerate(self.relations):
            if not isinstance(relation, RegionRelation):
                raise ValueError(f"relations[{index}] must be a RegionRelation")
            if relation.source_region_id not in region_ids:
                raise ValueError("relation source_region_id must reference a page region")
            if relation.target_region_id not in region_ids:
                raise ValueError("relation target_region_id must reference a page region")
            if relation.relation_id in relation_ids:
                raise ValueError("relation_id values must be unique within the page")
            relation_ids.add(relation.relation_id)

            logical_edge = (
                relation.relation_kind,
                relation.source_region_id,
                relation.target_region_id,
            )
            if logical_edge in logical_edges:
                raise ValueError("logical relation edges must not be duplicated")
            logical_edges.add(logical_edge)

        for relation_kind in _VALID_RELATION_KINDS:
            _validate_acyclic_relations(self.relations, relation_kind)
