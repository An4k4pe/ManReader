"""Simple Markdown rendering from ManReader's document IR.

This module keeps Markdown export deterministic and separate from extraction,
enrichment, entity detection, cross-linking, and file persistence.
"""

from __future__ import annotations

from ir_model import AssetIR, BlockIR, DocumentIR


def build_markdown(document: DocumentIR) -> str:
    """Build a simple Markdown string from a DocumentIR."""
    parts: list[str] = []
    current_paragraph = ""

    for page in document.pages:
        if current_paragraph:
            parts.append(current_paragraph)
            current_paragraph = ""

        previous_text_block: BlockIR | None = None
        parts.append(f"<!-- page: {page.page_num} -->")

        index = 0
        while index < len(page.blocks):
            block = page.blocks[index]
            if block.type == "text" and block.text:
                if block.role == "bullet_list":
                    if current_paragraph:
                        parts.append(current_paragraph)
                        current_paragraph = ""
                    previous_text_block = None
                    bullet_text, marker, index = _collect_bullet_list_text(page.blocks, index)
                    parts.append(_render_bullet_list_text(bullet_text, marker))
                    continue
                elif _is_heading_text(block.text, block.style):
                    if current_paragraph:
                        parts.append(current_paragraph)
                        current_paragraph = ""
                    previous_text_block = None
                    level = _heading_level(block.text, block.style)
                    parts.append(f"{'#' * level} {block.text.strip()}")
                else:
                    if (
                        current_paragraph
                        and previous_text_block is not None
                        and _should_start_new_paragraph(previous_text_block, block)
                    ):
                        parts.append(current_paragraph)
                        current_paragraph = ""
                    text = _format_inline_text(block.text, block.style)
                    current_paragraph = _join_text_fragments(current_paragraph, text)
                    previous_text_block = block
            elif block.type in {"image", "vector", "table"} and block.asset is not None:
                if current_paragraph:
                    parts.append(current_paragraph)
                    current_paragraph = ""
                previous_text_block = None
                parts.append(_render_asset(block.asset, block.page_num, block.type))
            index += 1

    if current_paragraph:
        parts.append(current_paragraph)

    return "\n\n".join(part for part in parts if part).rstrip() + "\n"


def _should_start_new_paragraph(previous: BlockIR, current: BlockIR) -> bool:
    if previous.page_num != current.page_num:
        return False
    if previous.bbox is None or current.bbox is None:
        return False
    if not _ends_with_strong_punctuation(previous.text or ""):
        return False

    vertical_gap = current.bbox[1] - previous.bbox[3]
    font_size = _paragraph_font_size(previous.style, current.style)
    return vertical_gap >= font_size * 1.2


def _ends_with_strong_punctuation(text: str) -> bool:
    return text.strip().endswith((".", "?", "!", "»", ")", "…"))


def _paragraph_font_size(first_style: dict[str, str], second_style: dict[str, str]) -> float:
    for style in (first_style, second_style):
        try:
            font_size = float(style.get("avg_font_size", ""))
        except ValueError:
            continue
    if font_size > 0:
        return font_size
    return 12.0


def _is_heading_text(text: str, style: dict[str, str]) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) > 90:
        return False
    if stripped.endswith((".", ",", ";")):
        return False
    if stripped.startswith("Scena "):
        return True
    if stripped.isupper() and len(stripped) <= 40:
        return True

    try:
        return float(style.get("avg_font_size", "")) >= 14.0
    except ValueError:
        return False


def _heading_level(text: str, style: dict[str, str]) -> int:
    stripped = text.strip()
    if stripped.startswith("Scena "):
        return 2
    if stripped.isupper() and len(stripped) <= 40:
        return 2

    try:
        font_size = float(style.get("avg_font_size", ""))
    except ValueError:
        return 2

    return 1 if font_size >= 18.0 else 2


def _format_inline_text(text: str, style: dict[str, str]) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    if not _can_render_inline_style(stripped):
        return stripped

    is_bold = style.get("bold") == "true"
    is_italic = style.get("italic") == "true"

    if is_bold and is_italic:
        return f"***{stripped}***"
    if is_bold:
        return f"**{stripped}**"

    # Italic extraction is still too noisy for body text in current PDFs.
    return stripped


def _join_text_fragments(first: str, second: str) -> str:
    left = first.strip()
    right = second.strip()
    if not left:
        return right
    if not right:
        return left

    if right[0] in ",.;:!?)]»":
        return left + right
    if left[-1] in "’'":
        return left + right
    if left[-1].isalnum() and right[0].isalnum() and len(right) <= 3:
        return left + right

    return f"{left} {right}"


def _collect_bullet_list_text(blocks: list[BlockIR], start: int) -> tuple[str, str, int]:
    first_block = blocks[start]
    marker = first_block.metadata.get("marker") or "❖"
    texts: list[str] = [first_block.text or ""]
    index = start + 1

    while index < len(blocks):
        block = blocks[index]
        if not _is_bullet_list_continuation(block, texts[-1], marker):
            break
        texts.append(block.text or "")
        index += 1

    return " ".join(text.strip() for text in texts if text.strip()), marker, index


def _is_bullet_list_continuation(block: BlockIR, previous_text: str, marker: str) -> bool:
    if block.type != "text" or not block.text:
        return False
    if _is_heading_text(block.text, block.style):
        return False
    if marker in block.text:
        return True
    return not _ends_with_strong_punctuation(previous_text)


def _ends_with_strong_punctuation(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?", ":", ";"))


def _is_bullet_list_text_block(block: BlockIR) -> bool:
    if block.type != "text" or not block.text:
        return False
    return not _is_heading_text(block.text, block.style)


def _render_bullet_list_text(text: str, marker: str) -> str:
    raw_items = text.split(marker)
    items = [" ".join(item.split()) for item in raw_items if item.strip()]
    if not items:
        normalized = " ".join(text.split())
        return f"- {normalized}" if normalized else ""
    return "\n".join(f"- {item}" for item in items)


def _render_asset(asset: AssetIR, page_num: int, block_type: str) -> str:
    title = asset.title or asset.current_name or asset.original_name or asset.id
    description = asset.description or asset.alt_text or ""
    kind = asset.kind or block_type
    path = asset.path or "#"

    lines = [
        f"<!-- asset: {asset.id} | page: {page_num} | type: {kind} -->",
        f"[{_asset_label(kind)}: {title}]({path})",
    ]

    if description:
        lines.append(f"\n> Descrizione: {description}")

    return "\n".join(lines)


def _can_render_inline_style(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 4:
        return False
    if len(stripped) > 60:
        return False
    if stripped[-1].isalnum() and " " not in stripped and len(stripped) <= 4:
        return False
    if stripped.endswith(("’", "'", ",")):
        return False
    return stripped[0] not in ",.;:!?)]»"


def _asset_label(kind: str) -> str:
    labels = {
        "image": "Immagine",
        "vector": "Vettoriale",
        "table": "Tabella",
    }
    return labels.get(kind, "Asset")
