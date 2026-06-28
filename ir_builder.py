"""Build ManReader's document IR from the current extraction output.

This module is a thin adapter over the existing extractor output. It avoids
importing extractor.py directly, but it still depends on the attribute names
exposed by PageData and related extraction objects.
"""

from __future__ import annotations

import hashlib

from ir_model import AssetIR, BlockIR, DocumentIR, PageIR

SCHEMA_VERSION = "1.0"

_BULLET_LIST_MARKERS = ("✦", "❖", "•", "●", "◆", "■")


class _MergedText:
    """Small adapter that exposes the TextBlock attributes used by _build_text_block."""

    def __init__(self, source: object, bbox: tuple[float, float, float, float], text: str | None):
        self.bbox = bbox
        self.text = text
        self.avg_font_size = getattr(source, "avg_font_size", "")
        self.is_bold = getattr(source, "is_bold", False)
        self.is_italic = getattr(source, "is_italic", False)


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


def _sort_position(item: object) -> tuple[float, float]:
    bbox = _bbox_tuple(getattr(item, "bbox", None))
    if bbox is None:
        return (0.0, 0.0)

    # Ordine di lettura base: prima dall'alto verso il basso,
    # poi da sinistra verso destra per frammenti sulla stessa riga.
    return (bbox[1], bbox[0])


def _is_reading_flow_asset(asset: object) -> bool:
    # Background, decorations, and duplicates can stay in the asset index,
    # but they should not enter the IR reading flow.
    return not (getattr(asset, "is_background", False) or getattr(asset, "is_duplicate", False))


def _build_blocks(page) -> list[BlockIR]:
    page_num = int(page.page_num)
    elements = []

    for index, block in enumerate(getattr(page, "text_blocks", []), start=1):
        y, x = _sort_position(block)
        elements.append((y, x, "text", index, block))

    for index, asset in enumerate(getattr(page, "images", []), start=1):
        if _is_reading_flow_asset(asset):
            y, x = _sort_position(asset)
            elements.append((y, x, "image", index, asset))

    for index, asset in enumerate(getattr(page, "vectors", []), start=1):
        if _is_reading_flow_asset(asset):
            y, x = _sort_position(asset)
            elements.append((y, x, "vector", index, asset))

    for index, asset in enumerate(getattr(page, "tables", []), start=1):
        if _is_reading_flow_asset(asset):
            y, x = _sort_position(asset)
            elements.append((y, x, "table", index, asset))

    sorted_elements = sorted(elements, key=lambda e: (e[0], e[1]))
    merged_elements = _merge_adjacent_text_elements(sorted_elements)

    blocks = []
    for order, (_, _, kind, index, item) in enumerate(
        merged_elements,
        start=1,
    ):
        if kind == "text":
            blocks.append(_build_text_block(item, page_num, index, order))
        else:
            blocks.append(_build_asset_block(item, kind, page_num, index, order))

    return blocks


def _merge_adjacent_text_elements(
    elements: list[tuple[float, float, str, int, object]],
) -> list[tuple[float, float, str, int, object]]:
    merged: list[tuple[float, float, str, int, object]] = []

    for element in elements:
        if not merged:
            merged.append(element)
            continue

        previous = merged[-1]
        if _can_merge_text_elements(previous, element):
            merged[-1] = _merge_text_elements(previous, element)
        else:
            merged.append(element)

    return merged


def _can_merge_text_elements(
    first: tuple[float, float, str, int, object],
    second: tuple[float, float, str, int, object],
) -> bool:
    if first[2] != "text" or second[2] != "text":
        return False

    first_bbox = _bbox_tuple(getattr(first[4], "bbox", None))
    second_bbox = _bbox_tuple(getattr(second[4], "bbox", None))
    if first_bbox is None or second_bbox is None:
        return False

    horizontal_gap = second_bbox[0] - first_bbox[2]
    return (
        abs(first_bbox[1] - second_bbox[1]) <= 2.0
        and second_bbox[0] >= first_bbox[2]
        and horizontal_gap <= 12.0
    )


def _merge_text_elements(
    first: tuple[float, float, str, int, object],
    second: tuple[float, float, str, int, object],
) -> tuple[float, float, str, int, object]:
    first_bbox = _bbox_tuple(getattr(first[4], "bbox", None))
    second_bbox = _bbox_tuple(getattr(second[4], "bbox", None))
    if first_bbox is None or second_bbox is None:
        return first

    merged_bbox = _union_bbox(first_bbox, second_bbox)
    horizontal_gap = second_bbox[0] - first_bbox[2]
    merged_text = _join_text_fragments(
        getattr(first[4], "text", None),
        getattr(second[4], "text", None),
        horizontal_gap,
    )
    merged_item = _MergedText(first[4], merged_bbox, merged_text)
    return (merged_bbox[1], merged_bbox[0], "text", first[3], merged_item)


def _union_bbox(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    return (
        min(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        max(first[3], second[3]),
    )


def _join_text_fragments(first: str | None, second: str | None, horizontal_gap: float) -> str:
    left = (first or "").strip()
    right = (second or "").strip()
    if not left:
        return right
    if not right:
        return left

    if right[0] in ",.;:!?)]»":
        return left + right
    if left[-1] in "’'":
        return left + right
    if left[-1].isalnum() and right[0].isalnum() and horizontal_gap <= 1.5:
        return left + right

    return f"{left} {right}"


def _build_text_block(block: object, page_num: int, index: int, order: int) -> BlockIR:
    raw_text = getattr(block, "text", None)
    text = _normalize_inline_bullet_list_text(raw_text) if raw_text is not None else None
    role, metadata = _text_block_role_and_metadata(text or "")
    return BlockIR(
        id=f"{_page_id(page_num)}_b{index:04d}",
        type="text",
        page_num=page_num + 1,
        order=order,
        bbox=_bbox_tuple(getattr(block, "bbox", None)),
        text=text,
        style={
            "avg_font_size": str(getattr(block, "avg_font_size", "")),
            "bold": str(getattr(block, "is_bold", False)).lower(),
            "italic": str(getattr(block, "is_italic", False)).lower(),
        },
        role=role,
        metadata=metadata,
    )


def _leading_bullet_marker(text: str) -> str | None:
    normalized = text.lstrip()
    for marker in _BULLET_LIST_MARKERS:
        if normalized.startswith(marker):
            return marker
    return None


def _normalize_inline_bullet_list_text(text: str) -> str:
    marker = _leading_bullet_marker(text)
    if marker is None:
        return text

    normalized = text.lstrip()
    marker_positions = _marker_positions(normalized, marker)
    if len(marker_positions) < 2:
        return text

    has_inline_marker = any(
        not _marker_starts_line(normalized, position) for position in marker_positions[1:]
    )
    if not has_inline_marker:
        return text

    leading_whitespace = text[: len(text) - len(normalized)]
    entries = []
    for index, position in enumerate(marker_positions):
        next_position = (
            marker_positions[index + 1] if index + 1 < len(marker_positions) else len(normalized)
        )
        entry = normalized[position:next_position].strip()
        if entry:
            entries.append(entry)

    if len(entries) < 2:
        return text
    return leading_whitespace + "\n".join(entries)


def _marker_positions(text: str, marker: str) -> list[int]:
    positions = []
    start = 0
    while True:
        position = text.find(marker, start)
        if position == -1:
            return positions
        positions.append(position)
        start = position + len(marker)


def _marker_starts_line(text: str, position: int) -> bool:
    line_start = text.rfind("\n", 0, position) + 1
    return not text[line_start:position].strip()


def _text_block_role_and_metadata(text: str) -> tuple[str | None, dict[str, str]]:
    marker = _leading_bullet_marker(text)
    if marker is not None:
        return "bullet_list", {"marker": marker}
    return None, {}


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
