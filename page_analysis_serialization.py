"""JSON-safe conversion helpers for PageAnalysis."""

from __future__ import annotations

from typing import cast

from page_analysis_model import LayoutRegion, PageAnalysis, RegionRelation

_ROOT_KEYS = frozenset({"schema_version", "generation_id", "page_id", "regions", "relations"})
_REGION_KEYS = frozenset({"region_id", "page_id", "bbox", "structural_kind", "primitive_ids"})
_RELATION_KEYS = frozenset({"relation_id", "relation_kind", "source_region_id", "target_region_id"})


def page_analysis_to_dict(analysis: PageAnalysis) -> dict[str, object]:
    """Convert a PageAnalysis to a deterministic JSON-safe dictionary."""

    if not isinstance(analysis, PageAnalysis):
        raise ValueError("analysis must be a PageAnalysis")

    return {
        "schema_version": analysis.schema_version,
        "generation_id": analysis.generation_id,
        "page_id": analysis.page_id,
        "regions": [
            {
                "region_id": region.region_id,
                "page_id": region.page_id,
                "bbox": list(region.bbox),
                "structural_kind": region.structural_kind,
                "primitive_ids": list(region.primitive_ids),
            }
            for region in analysis.regions
        ],
        "relations": [
            {
                "relation_id": relation.relation_id,
                "relation_kind": relation.relation_kind,
                "source_region_id": relation.source_region_id,
                "target_region_id": relation.target_region_id,
            }
            for relation in analysis.relations
        ],
    }


def page_analysis_from_dict(data: object) -> PageAnalysis:
    """Reconstruct a PageAnalysis from a strictly validated JSON-safe dictionary."""

    root = _require_dict(data, "root")
    _validate_exact_keys(root, _ROOT_KEYS, "root")

    regions_data = _require_list(root, "regions", "regions")
    relations_data = _require_list(root, "relations", "relations")

    regions = tuple(_parse_region(item, index) for index, item in enumerate(regions_data))
    relations = tuple(_parse_relation(item, index) for index, item in enumerate(relations_data))

    return PageAnalysis(
        schema_version=_require_str(root, "schema_version", "schema_version"),
        generation_id=_require_str(root, "generation_id", "generation_id"),
        page_id=_require_str(root, "page_id", "page_id"),
        regions=regions,
        relations=relations,
    )


def _require_dict(value: object, path: str) -> dict[object, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a dict")
    return cast(dict[object, object], value)


def _validate_exact_keys(
    data: dict[object, object],
    expected_keys: frozenset[str],
    path: str,
) -> None:
    for key in data:
        if not isinstance(key, str):
            raise ValueError(f"{path} keys must be strings")

    keys = cast(set[str], set(data))
    missing = expected_keys - keys
    if missing:
        raise ValueError(f"{path} is missing required keys")

    extra = keys - expected_keys
    if extra:
        raise ValueError(f"{path} has unknown keys")


def _require_str(data: dict[object, object], key: str, path: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")
    return value


def _require_list(data: dict[object, object], key: str, path: str) -> list[object]:
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return cast(list[object], value)


def _parse_region(value: object, index: int) -> LayoutRegion:
    path = f"regions[{index}]"
    data = _require_dict(value, path)
    _validate_exact_keys(data, _REGION_KEYS, path)

    primitive_ids_data = _require_list(data, "primitive_ids", f"{path}.primitive_ids")
    primitive_ids: list[str] = []
    for primitive_index, primitive_id in enumerate(primitive_ids_data):
        if not isinstance(primitive_id, str):
            raise ValueError(f"{path}.primitive_ids[{primitive_index}] must be a string")
        primitive_ids.append(primitive_id)

    return LayoutRegion(
        region_id=_require_str(data, "region_id", f"{path}.region_id"),
        page_id=_require_str(data, "page_id", f"{path}.page_id"),
        bbox=_parse_bbox(data["bbox"], f"{path}.bbox"),
        structural_kind=_require_str(data, "structural_kind", f"{path}.structural_kind"),
        primitive_ids=tuple(primitive_ids),
    )


def _parse_relation(value: object, index: int) -> RegionRelation:
    path = f"relations[{index}]"
    data = _require_dict(value, path)
    _validate_exact_keys(data, _RELATION_KEYS, path)

    return RegionRelation(
        relation_id=_require_str(data, "relation_id", f"{path}.relation_id"),
        relation_kind=_require_str(data, "relation_kind", f"{path}.relation_kind"),
        source_region_id=_require_str(
            data,
            "source_region_id",
            f"{path}.source_region_id",
        ),
        target_region_id=_require_str(
            data,
            "target_region_id",
            f"{path}.target_region_id",
        ),
    )


def _parse_bbox(value: object, path: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    if len(value) != 4:
        raise ValueError(f"{path} must contain exactly four numbers")

    coordinates: list[float] = []
    for index, coordinate in enumerate(value):
        if type(coordinate) not in {int, float}:
            raise ValueError(f"{path}[{index}] must be a number")
        coordinates.append(float(coordinate))

    return (coordinates[0], coordinates[1], coordinates[2], coordinates[3])
