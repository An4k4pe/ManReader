"""Build ManReader's document IR from the current extraction output.

This module is a thin adapter over the existing extractor output. It avoids
importing extractor.py directly, but it still depends on the attribute names
exposed by PageData and related extraction objects.
"""

from __future__ import annotations

import hashlib
import re

from ir_model import AssetIR, BlockIR, DocumentIR, PageIR

SCHEMA_VERSION = "1.0"

_BULLET_LIST_MARKERS = ("✦", "❖", "•", "●", "◆", "■")
_HYPHENATED_WORD_RE = re.compile(r"(?<=[A-Za-zÀ-ÖØ-öø-ÿ])-\s+(?=[a-zà-öø-ÿ])")


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

    return _renumber_blocks(_merge_callout_blocks(blocks))


def _merge_callout_blocks(blocks: list[BlockIR]) -> list[BlockIR]:
    merged: list[BlockIR] = []
    consumed_body_indexes: set[int] = set()

    for index, current in enumerate(blocks):
        if index in consumed_body_indexes:
            continue

        body_indexes = _callout_body_indexes(blocks, index, consumed_body_indexes)

        if body_indexes:
            consumed_body_indexes.update(body_indexes)
            merged.append(
                _build_callout_block(current, [blocks[body_index] for body_index in body_indexes])
            )
            continue

        merged.append(current)

    return merged


def _callout_body_indexes(
    blocks: list[BlockIR],
    title_index: int,
    consumed_body_indexes: set[int] | None = None,
) -> list[int] | None:
    title_block = blocks[title_index]
    if not _is_callout_title_block(title_block):
        return None

    region = _callout_region_for_title(blocks, title_index)
    if region is None:
        return None

    consumed_body_indexes = consumed_body_indexes or set()
    body_indexes: list[int] = []
    index = title_index + 1
    while index < len(blocks):
        if index in consumed_body_indexes:
            index += 1
            continue

        block = blocks[index]
        if block.page_num != title_block.page_num:
            return _valid_callout_body_indexes(blocks, body_indexes)

        if _is_callout_region_graphic(block, region):
            index += 1
            continue

        if block.type == "text":
            if not _block_belongs_to_region(block, region):
                if not body_indexes and _is_other_callout_title_for_different_region(
                    blocks, index, region
                ):
                    index += 1
                    continue
                return _valid_callout_body_indexes(blocks, body_indexes)
            if not _is_callout_body_fragment_block(block):
                return _valid_callout_body_indexes(blocks, body_indexes)
            body_indexes.append(index)
            index += 1
            continue

        index += 1
        continue

    return _valid_callout_body_indexes(blocks, body_indexes)


def _is_other_callout_title_for_different_region(
    blocks: list[BlockIR],
    title_index: int,
    selected_region: BlockIR,
) -> bool:
    title_block = blocks[title_index]
    if not _is_callout_title_block(title_block):
        return False
    if _block_belongs_to_region(title_block, selected_region):
        return False

    other_region = _callout_region_for_title(blocks, title_index)
    return other_region is not None and other_region is not selected_region


def _callout_region_for_title(blocks: list[BlockIR], title_index: int) -> BlockIR | None:
    title_block = blocks[title_index]
    if title_block.bbox is None:
        return None

    candidates = [
        block
        for block in blocks
        if block.page_num == title_block.page_num
        and _is_callout_region_candidate(block)
        and block.bbox is not None
        and _title_tied_to_region(title_block.bbox, block.bbox)
    ]
    if not candidates:
        return None

    return min(candidates, key=lambda block: _bbox_area(block.bbox or (0.0, 0.0, 0.0, 0.0)))


def _is_callout_title_block(block: BlockIR) -> bool:
    if block.type != "text" or block.role is not None or not block.text:
        return False

    stripped = " ".join(block.text.split())
    words = stripped.split()
    if not stripped or len(stripped) > 50:
        return False
    if stripped.startswith(("-", "–", "—")):
        return False
    if not 1 <= len(words) <= 6:
        return False
    if not any(character.isalpha() for character in stripped):
        return False
    if not stripped.isupper():
        return False
    if stripped.endswith((".", ",", ";", ":")):
        return False
    return not _looks_like_section_heading_block(block)


def _valid_callout_body_indexes(blocks: list[BlockIR], body_indexes: list[int]) -> list[int] | None:
    if not body_indexes:
        return None
    text = _joined_block_text([blocks[index] for index in body_indexes])
    return body_indexes if _is_callout_body_text(text) else None


def _is_callout_body_block(block: BlockIR) -> bool:
    return _is_callout_body_fragment_block(block) and _is_callout_body_text(block.text or "")


def _is_callout_body_fragment_block(block: BlockIR) -> bool:
    if block.type != "text" or block.role not in {None, "bullet_list"} or not block.text:
        return False
    if _looks_like_section_heading_block(block):
        return False
    return _is_callout_body_fragment_text(block.text)


def _is_callout_body_fragment_text(text: str) -> bool:
    stripped = " ".join(text.split())
    if not stripped:
        return False
    if stripped.startswith(('"', "“", "”", "-", "–", "—")):
        return False
    return not stripped.isupper()


def _is_callout_body_text(text: str) -> bool:
    stripped = " ".join(text.split())
    return len(stripped) >= 40 and _is_callout_body_fragment_text(stripped)


def _is_callout_region_candidate(block: BlockIR) -> bool:
    if block.type not in {"image", "vector"} or block.bbox is None:
        return False
    if _bbox_area(block.bbox) <= 0:
        return False
    asset = block.asset
    return asset is None or not (asset.is_background or asset.is_duplicate)


def _is_callout_region_graphic(block: BlockIR, region: BlockIR) -> bool:
    if block.type not in {"image", "vector"}:
        return False
    if block is region:
        return True
    return _block_belongs_to_region(block, region)


def _title_tied_to_region(
    title_bbox: tuple[float, float, float, float],
    region_bbox: tuple[float, float, float, float],
) -> bool:
    if _title_in_region_top_band(title_bbox, region_bbox):
        return True
    if _title_crosses_region_top_edge(title_bbox, region_bbox):
        return True
    return _title_immediately_above_region(title_bbox, region_bbox)


def _title_in_region_top_band(
    title_bbox: tuple[float, float, float, float],
    region_bbox: tuple[float, float, float, float],
) -> bool:
    title_width = max(title_bbox[2] - title_bbox[0], 0.0)
    if title_width <= 0:
        return False

    horizontal_overlap = min(title_bbox[2], region_bbox[2]) - max(title_bbox[0], region_bbox[0])
    if horizontal_overlap < title_width * 0.80:
        return False

    region_top = region_bbox[1]
    top_band_height = _region_top_band_height(region_bbox)
    title_center_y = (title_bbox[1] + title_bbox[3]) / 2.0
    return title_bbox[3] >= region_top - 3.0 and title_center_y <= region_top + top_band_height


def _title_crosses_region_top_edge(
    title_bbox: tuple[float, float, float, float],
    region_bbox: tuple[float, float, float, float],
) -> bool:
    title_width = max(title_bbox[2] - title_bbox[0], 0.0)
    if title_width <= 0:
        return False

    horizontal_overlap = min(title_bbox[2], region_bbox[2]) - max(title_bbox[0], region_bbox[0])
    if horizontal_overlap < title_width * 0.80:
        return False

    region_top = region_bbox[1]
    top_band_height = _region_top_band_height(region_bbox)
    title_center_y = (title_bbox[1] + title_bbox[3]) / 2.0

    return (
        title_bbox[1] <= region_top + 3.0
        and title_bbox[3] >= region_top - 3.0
        and title_center_y <= region_top + top_band_height
    )


def _region_top_band_height(region_bbox: tuple[float, float, float, float]) -> float:
    region_height = max(region_bbox[3] - region_bbox[1], 0.0)
    return min(24.0, max(region_height * 0.25, 12.0))


def _title_immediately_above_region(
    title_bbox: tuple[float, float, float, float],
    region_bbox: tuple[float, float, float, float],
) -> bool:
    vertical_gap = region_bbox[1] - title_bbox[3]
    if vertical_gap < -2.0 or vertical_gap > 6.0:
        return False
    title_width = max(title_bbox[2] - title_bbox[0], 0.0)
    if title_width <= 0:
        return False
    horizontal_overlap = min(title_bbox[2], region_bbox[2]) - max(title_bbox[0], region_bbox[0])
    return horizontal_overlap >= title_width * 0.80


def _block_belongs_to_region(block: BlockIR, region: BlockIR) -> bool:
    if block.bbox is None or region.bbox is None:
        return False
    if block.page_num != region.page_num:
        return False
    if _bbox_contains(region.bbox, block.bbox, tolerance=3.0):
        return True
    return _bbox_overlap_ratio(block.bbox, region.bbox) >= 0.80


def _bbox_area(bbox: tuple[float, float, float, float]) -> float:
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width <= 0 or height <= 0:
        return 0.0
    return width * height


def _bbox_intersection_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return _bbox_area((x0, y0, x1, y1))


def _bbox_contains(
    outer: tuple[float, float, float, float],
    inner: tuple[float, float, float, float],
    *,
    tolerance: float = 0.0,
) -> bool:
    return (
        outer[0] - tolerance <= inner[0]
        and outer[1] - tolerance <= inner[1]
        and outer[2] + tolerance >= inner[2]
        and outer[3] + tolerance >= inner[3]
    )


def _bbox_overlap_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    first_area = _bbox_area(first)
    if first_area <= 0:
        return 0.0
    return _bbox_intersection_area(first, second) / first_area


def _looks_like_section_heading_block(block: BlockIR) -> bool:
    text = (block.text or "").strip()
    if not text:
        return False
    if text.startswith("Scena "):
        return True

    font_size = _font_size_from_style(block.style)
    return font_size is not None and font_size >= 14.0


def _font_size_from_style(style: dict[str, str]) -> float | None:
    try:
        font_size = float(style.get("avg_font_size", ""))
    except ValueError:
        return None
    return font_size if font_size > 0 else None


def _build_callout_block(title_block: BlockIR, body_blocks: list[BlockIR]) -> BlockIR:
    bbox = title_block.bbox
    for body_block in body_blocks:
        if bbox is not None and body_block.bbox is not None:
            bbox = _union_bbox(bbox, body_block.bbox)
        elif bbox is None:
            bbox = body_block.bbox

    first_body = body_blocks[0]
    return BlockIR(
        id=title_block.id,
        type="text",
        page_num=title_block.page_num,
        order=title_block.order,
        bbox=bbox,
        text=_joined_block_text(body_blocks),
        style=first_body.style,
        role="callout",
        metadata={
            "callout_type": "info",
            "title": " ".join((title_block.text or "").split()),
        },
    )


def _joined_block_text(blocks: list[BlockIR]) -> str:
    return " ".join(" ".join((block.text or "").split()) for block in blocks if block.text)


def _renumber_blocks(blocks: list[BlockIR]) -> list[BlockIR]:
    return [
        BlockIR(
            id=block.id,
            type=block.type,
            page_num=block.page_num,
            order=order,
            bbox=block.bbox,
            text=block.text,
            style=block.style,
            asset=block.asset,
            role=block.role,
            metadata=block.metadata,
        )
        for order, block in enumerate(blocks, start=1)
    ]


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


def _normalize_text_block_text(text: str) -> str:
    return _HYPHENATED_WORD_RE.sub("", text)


def _build_text_block(block: object, page_num: int, index: int, order: int) -> BlockIR:
    raw_text = getattr(block, "text", None)
    text = (
        _normalize_text_block_text(_normalize_inline_bullet_list_text(raw_text))
        if raw_text is not None
        else None
    )
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
