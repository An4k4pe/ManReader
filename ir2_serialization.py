"""JSON-safe conversion helpers for DocumentIR 2, with validation on the way in.

Follows the **validating** shape of ``page_analysis_serialization`` rather than
the permissive round-trip of ``ir_store``: IR 2 is the artifact that persists
human corrections and AI proposals, and a contract that accepts unvalidated
input would let a corrupted file through to the thing that must survive
regeneration.

Every key is checked exactly -- missing keys and unknown keys both raise -- so a
schema change cannot pass silently as a partially-read file.
"""

from __future__ import annotations

from typing import cast

from geometry_model import BBox
from ir2_model import (
    AssetRefIR2,
    DocumentIR2,
    IR2Provenance,
    NodeIR2,
    PageIR2,
)

_ROOT_KEYS = frozenset({"schema_version", "provenance", "pages"})
_PROVENANCE_KEYS = frozenset({"source_id", "generation_id", "producer_names"})
_PAGE_KEYS = frozenset({"page_id", "nodes"})
_NODE_KEYS = frozenset(
    {
        "node_id",
        "order",
        "kind",
        "primitive_ids",
        "page_ids",
        "text",
        "asset",
        "candidate_ids",
        "resolution",
    }
)
_ASSET_KEYS = frozenset(
    {"digest", "file_name", "bbox", "occurrence_count", "proposed_structural_kind"}
)


def document_ir2_to_dict(document: DocumentIR2) -> dict[str, object]:
    """Convert one DocumentIR 2 to a JSON-safe dict."""

    if not isinstance(document, DocumentIR2):
        raise ValueError("document must be a DocumentIR2")

    return {
        "schema_version": document.schema_version,
        "provenance": {
            "source_id": document.provenance.source_id,
            "generation_id": document.provenance.generation_id,
            "producer_names": list(document.provenance.producer_names),
        },
        "pages": [
            {
                "page_id": page.page_id,
                "nodes": [_node_to_dict(node) for node in page.nodes],
            }
            for page in document.pages
        ],
    }


def _node_to_dict(node: NodeIR2) -> dict[str, object]:
    return {
        "node_id": node.node_id,
        "order": node.order,
        "kind": node.kind,
        "primitive_ids": list(node.primitive_ids),
        "page_ids": list(node.page_ids),
        "text": node.text,
        "asset": None if node.asset is None else _asset_to_dict(node.asset),
        "candidate_ids": list(node.candidate_ids),
        "resolution": node.resolution,
    }


def _asset_to_dict(asset: AssetRefIR2) -> dict[str, object]:
    return {
        "digest": asset.digest,
        "file_name": asset.file_name,
        "bbox": list(asset.bbox),
        "occurrence_count": asset.occurrence_count,
        "proposed_structural_kind": asset.proposed_structural_kind,
    }


def document_ir2_from_dict(data: object) -> DocumentIR2:
    """Rebuild one DocumentIR 2 from a dict, validating as it goes."""

    root = _require_dict(data, "document")
    _validate_exact_keys(root, _ROOT_KEYS, "document")

    return DocumentIR2(
        schema_version=_require_str(root, "schema_version", "document.schema_version"),
        provenance=_parse_provenance(root["provenance"]),
        pages=tuple(
            _parse_page(value, index)
            for index, value in enumerate(_require_list(root, "pages", "document.pages"))
        ),
    )


def _parse_provenance(value: object) -> IR2Provenance:
    data = _require_dict(value, "document.provenance")
    _validate_exact_keys(data, _PROVENANCE_KEYS, "document.provenance")
    return IR2Provenance(
        source_id=_require_str(data, "source_id", "document.provenance.source_id"),
        generation_id=_require_str(data, "generation_id", "document.provenance.generation_id"),
        producer_names=_parse_str_tuple(
            data, "producer_names", "document.provenance.producer_names"
        ),
    )


def _parse_page(value: object, index: int) -> PageIR2:
    path = f"document.pages[{index}]"
    data = _require_dict(value, path)
    _validate_exact_keys(data, _PAGE_KEYS, path)
    return PageIR2(
        page_id=_require_str(data, "page_id", f"{path}.page_id"),
        nodes=tuple(
            _parse_node(node_value, path, node_index)
            for node_index, node_value in enumerate(_require_list(data, "nodes", f"{path}.nodes"))
        ),
    )


def _parse_node(value: object, page_path: str, index: int) -> NodeIR2:
    path = f"{page_path}.nodes[{index}]"
    data = _require_dict(value, path)
    _validate_exact_keys(data, _NODE_KEYS, path)

    order = data["order"]
    if type(order) is not int:
        raise ValueError(f"{path}.order must be an int")

    return NodeIR2(
        node_id=_require_str(data, "node_id", f"{path}.node_id"),
        order=order,
        kind=_require_str(data, "kind", f"{path}.kind"),
        primitive_ids=_parse_str_tuple(data, "primitive_ids", f"{path}.primitive_ids"),
        page_ids=_parse_str_tuple(data, "page_ids", f"{path}.page_ids"),
        text=_optional_str(data, "text", f"{path}.text"),
        asset=None if data["asset"] is None else _parse_asset(data["asset"], f"{path}.asset"),
        candidate_ids=_parse_str_tuple(data, "candidate_ids", f"{path}.candidate_ids"),
        resolution=_optional_str(data, "resolution", f"{path}.resolution"),
    )


def _parse_asset(value: object, path: str) -> AssetRefIR2:
    data = _require_dict(value, path)
    _validate_exact_keys(data, _ASSET_KEYS, path)

    occurrence_count = data["occurrence_count"]
    if type(occurrence_count) is not int:
        raise ValueError(f"{path}.occurrence_count must be an int")

    return AssetRefIR2(
        digest=_require_str(data, "digest", f"{path}.digest"),
        file_name=_require_str(data, "file_name", f"{path}.file_name"),
        bbox=_parse_bbox(data["bbox"], f"{path}.bbox"),
        occurrence_count=occurrence_count,
        proposed_structural_kind=_optional_str(
            data, "proposed_structural_kind", f"{path}.proposed_structural_kind"
        ),
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


def _optional_str(data: dict[object, object], key: str, path: str) -> str | None:
    value = data[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string or null")
    return value


def _require_list(data: dict[object, object], key: str, path: str) -> list[object]:
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return cast(list[object], value)


def _parse_str_tuple(data: dict[object, object], key: str, path: str) -> tuple[str, ...]:
    items: list[str] = []
    for index, item in enumerate(_require_list(data, key, path)):
        if not isinstance(item, str):
            raise ValueError(f"{path}[{index}] must be a string")
        items.append(item)
    return tuple(items)


def _parse_bbox(value: object, path: str) -> BBox:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    if len(value) != 4:
        raise ValueError(f"{path} must contain exactly four numbers")

    coordinates: list[float] = []
    for index, coordinate in enumerate(cast(list[object], value)):
        if type(coordinate) not in {int, float}:
            raise ValueError(f"{path}[{index}] must be a number")
        coordinates.append(float(cast(float, coordinate)))

    return (coordinates[0], coordinates[1], coordinates[2], coordinates[3])
