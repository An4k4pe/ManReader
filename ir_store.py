from __future__ import annotations

"""JSON persistence helpers for ManReader's document IR.

The IR stays plain dataclasses so it can remain local, inspectable, and easy to
revise without introducing validation frameworks or storage services.
deserialization is explicit, this avoid dependancies like pydantic
and make the scheme readable and verifiable.
"""

import json
from dataclasses import asdict
from pathlib import Path

from ir_model import AssetIR, BlockIR, DocumentIR, EntityIR, PageIR


def save_document_ir(document: DocumentIR, path: Path) -> None:
    """Save a DocumentIR to a UTF-8 JSON file.

    Parent directories are created because IR files live under each book output
    directory, which may not exist before the first extraction run.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(document), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_document_ir(path: Path) -> DocumentIR:
    """Load a DocumentIR from a JSON file produced by save_document_ir."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return DocumentIR(
        schema_version=data["schema_version"],
        # TODO:
        # validare schema_version quando verranno introdotte
        # versioni multiple della IR.
        source_path=data["source_path"],
        title=data.get("title"),
        author=data.get("author"),
        page_count=data.get("page_count", 0),
        pages=[_load_page(page) for page in data.get("pages", [])],
        toc=data.get("toc", []),
        metadata=data.get("metadata", {}),
        entities=[_load_entity(entity) for entity in data.get("entities", [])],
    )


def _load_page(data: dict) -> PageIR:
    return PageIR(
        id=data["id"],
        page_num=data["page_num"],
        width=data.get("width"),
        height=data.get("height"),
        blocks=[_load_block(block) for block in data.get("blocks", [])],
    )


def _load_block(data: dict) -> BlockIR:
    bbox = data.get("bbox")
    return BlockIR(
        id=data["id"],
        type=data["type"],
        page_num=data["page_num"],
        order=data["order"],
        bbox=tuple(bbox) if bbox is not None else None,
        text=data.get("text"),
        style=data.get("style", {}),
        asset=_load_asset(data["asset"]) if data.get("asset") else None,
    )


def _load_asset(data: dict) -> AssetIR:
    return AssetIR(
        id=data["id"],
        sha=data["sha"],
        kind=data["kind"],
        path=data["path"],
        original_name=data.get("original_name"),
        current_name=data.get("current_name"),
        ext=data.get("ext"),
        title=data.get("title"),
        description=data.get("description"),
        alt_text=data.get("alt_text"),
        classification=data.get("classification"),
        is_background=data.get("is_background", False),
        is_duplicate=data.get("is_duplicate", False),
        enrichment=data.get("enrichment", {}),
    )


def _load_entity(data: dict) -> EntityIR:
    return EntityIR(
        id=data["id"],
        name=data["name"],
        type=data["type"],
        page_num=data.get("page_num"),
        aliases=data.get("aliases", []),
        source_block_ids=data.get("source_block_ids", []),
        confidence=data.get("confidence"),
        source=data.get("source"),
    )
