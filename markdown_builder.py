"""Simple Markdown rendering from ManReader's document IR.

This module keeps Markdown export deterministic and separate from extraction,
enrichment, entity detection, cross-linking, and file persistence.
"""

from __future__ import annotations

from ir_model import AssetIR, DocumentIR


def build_markdown(document: DocumentIR) -> str:
    """Build a simple Markdown string from a DocumentIR."""
    parts: list[str] = []

    for page in document.pages:
        parts.append(f"<!-- page: {page.page_num} -->")

        for block in page.blocks:
            if block.type == "text" and block.text:
                parts.append(block.text.strip())
            elif block.type in {"image", "vector", "table"} and block.asset is not None:
                parts.append(_render_asset(block.asset, block.page_num, block.type))

    return "\n\n".join(part for part in parts if part).rstrip() + "\n"


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


def _asset_label(kind: str) -> str:
    labels = {
        "image": "Immagine",
        "vector": "Vettoriale",
        "table": "Tabella",
    }
    return labels.get(kind, "Asset")
