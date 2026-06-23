"""Build ManReader's document IR from the current extraction output.

This module is a thin adapter over the existing extractor output. It avoids
importing extractor.py directly, but it still depends on the attribute names
exposed by PageData and related extraction objects.
"""

from __future__ import annotations

import hashlib

from ir_model import AssetIR, BlockIR, DocumentIR, PageIR

SCHEMA_VERSION = "1.0"


def build_document_ir(
    pages: list[object],
    source_path: str,
    title: str | None = None,
    author: str | None = None,
    toc: list[tuple[int, str, int]] | None = None,
    metadata: dict[str, str] | None = None,
) -> DocumentIR:
    """Convert extracted pages into a DocumentIR.

    The extractor dataclasses are consumed by attribute shape instead of import
    so this module can remain independent from the extraction implementation.
    """
    return DocumentIR(
        schema_version=SCHEMA_VERSION,
        source_path=source_path,
        title=title,
        author=author,
        page_count=len(pages),
        pages=[_build_page_ir(page) for page in pages],
        toc=_build_toc_ir(toc or []),
        metadata=metadata or {},
    )


def _build_page_ir(page) -> PageIR:
    page_num = int(page.page_num)
    return PageIR(
        id=_page_id(page_num),
        page_num=page_num + 1,
        width=getattr(page, "width", None),
        height=getattr(page, "height", None),
        blocks=_build_blocks(page),
    )


def _build_blocks(page) -> list[BlockIR]:
    page_num = int(page.page_num)
    elements = []

    for index, block in enumerate(getattr(page, "text_blocks", []), start=1):
        elements.append((getattr(block, "bbox", (0.0, 0.0, 0.0, 0.0))[1], "text", index, block))
    for index, asset in enumerate(getattr(page, "images", []), start=1):
        elements.append((getattr(asset, "bbox", (0.0, 0.0, 0.0, 0.0))[1], "image", index, asset))
    for index, asset in enumerate(getattr(page, "vectors", []), start=1):
        elements.append((getattr(asset, "bbox", (0.0, 0.0, 0.0, 0.0))[1], "vector", index, asset))
    for index, asset in enumerate(getattr(page, "tables", []), start=1):
        elements.append((getattr(asset, "bbox", (0.0, 0.0, 0.0, 0.0))[1], "table", index, asset))

    blocks = []
    for order, (_, kind, index, item) in enumerate(sorted(elements, key=lambda e: e[0]), start=1):
        if kind == "text":
            blocks.append(_build_text_block(item, page_num, index, order))
        else:
            blocks.append(_build_asset_block(item, kind, page_num, index, order))
    return blocks


def _build_text_block(block: object, page_num: int, index: int, order: int) -> BlockIR:
    return BlockIR(
        id=f"{_page_id(page_num)}_b{index:04d}",
        type="text",
        page_num=page_num + 1,
        order=order,
        bbox=_bbox_tuple(getattr(block, "bbox", None)),
        text=getattr(block, "text", None),
        style={
            "avg_font_size": str(getattr(block, "avg_font_size", "")),
            "bold": str(getattr(block, "is_bold", False)).lower(),
            "italic": str(getattr(block, "is_italic", False)).lower(),
        },
    )


def _build_asset_block(asset: object, kind: str, page_num: int, index: int, order: int) -> BlockIR:
    fallback_id = f"{_page_id(page_num)}_a{index:04d}_{kind}"
    sha = _asset_sha(asset, fallback_id)
    asset_ir = AssetIR(
        id=f"asset:{sha}",
        sha=sha,
        kind=kind,
        path=getattr(asset, "saved_path", None) or "",
        original_name=_file_name(getattr(asset, "saved_path", None)),
        current_name=_file_name(getattr(asset, "saved_path", None)),
        ext=getattr(asset, "ext", None),
        title=None,
        description=getattr(asset, "description", None),
        alt_text=None,
        classification=_classification_for(kind, asset),
        is_background=getattr(asset, "is_background", False),
        is_duplicate=getattr(asset, "is_duplicate", False),
    )
    return BlockIR(
        id=fallback_id,
        type=kind,
        page_num=page_num + 1,
        order=order,
        bbox=_bbox_tuple(getattr(asset, "bbox", None)),
        asset=asset_ir,
    )


def _build_toc_ir(toc: list[tuple[int, str, int]]) -> list[dict[str, str]]:
    return [
        {
            "level": str(level),
            "title": title,
            "page": str(page),
        }
        for level, title, page in toc
    ]


def _asset_sha(asset: object, fallback_id: str) -> str:
    existing_sha = getattr(asset, "sha", None)
    if existing_sha:
        return existing_sha

    saved_path = getattr(asset, "saved_path", None)
    if saved_path:
        try:
            with open(saved_path, "rb") as asset_file:
                return hashlib.md5(asset_file.read()).hexdigest()
        except OSError:
            pass

    image_data = getattr(asset, "image_data", None)
    if image_data:
        return hashlib.md5(image_data).hexdigest()

    # Temporary fallback until extractor exposes stable asset hashes.
    return hashlib.md5(fallback_id.encode("utf-8")).hexdigest()


def _classification_for(kind: str, asset: object) -> str | None:
    if getattr(asset, "is_background", False):
        return "background"
    if kind == "table":
        return "table"
    return None


def _bbox_tuple(bbox: object) -> tuple[float, float, float, float] | None:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))


def _file_name(path: str | None) -> str | None:
    if not path:
        return None
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def _page_id(page_num: int) -> str:
    return f"p{page_num + 1:04d}"
