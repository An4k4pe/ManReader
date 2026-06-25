"""Diagnose PyMuPDF dict/block text differences for one PDF page.

This script is intentionally manual-only: it does not participate in the main
extraction pipeline and exists to inspect whether get_text("blocks") can safely
help repair fragmented get_text("dict") text in a future commit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor import (  # noqa: E402
    TextSpan,
    _best_text_block_for_bbox,
    _join_text_spans,
    _overlap_ratio_against_bbox,
    _text_from_block,
)

KNOWN_FRAGMENTS = (
    "resistent e",
    "p urtroppo",
    "preternatu rale",
    "gl i",
    "deci mata",
    "suoam ico",
)


def main() -> int:
    """Run the manual block matching diagnostic."""
    parser = argparse.ArgumentParser(
        description="Compare PyMuPDF dict text blocks with get_text('blocks') candidates."
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument("page", type=int, help="1-based page number")
    args = parser.parse_args()

    if args.page < 1:
        parser.error("page must be 1-based and greater than zero")

    doc = fitz.open(args.pdf)
    try:
        if args.page > doc.page_count:
            parser.error(f"page out of range: {args.page} > {doc.page_count}")
        page = doc[args.page - 1]
        _print_page_diagnostic(page, args.page)
    finally:
        doc.close()

    return 0


def _print_page_diagnostic(page, page_num: int) -> None:
    raw = page.get_text("dict")
    block_hints = page.get_text("blocks")

    print(f"PDF page: {page_num}")
    print(f"dict text blocks: {len([b for b in raw.get('blocks', []) if b.get('type') == 0])}")
    print(f"get_text('blocks') entries: {len(block_hints)}")
    print()

    previous_dict_text = ""
    for index, block in enumerate(raw.get("blocks", []), start=1):
        if block.get("type") != 0:
            continue

        dict_bbox = tuple(block["bbox"])
        dict_text = _dict_block_text(block)
        candidate = _best_text_block_for_bbox(dict_bbox, block_hints)
        block_text = _text_from_block(candidate) if candidate is not None else ""
        overlap = (
            _overlap_ratio_against_bbox(dict_bbox, candidate[:4]) if candidate is not None else 0.0
        )
        differs = dict_text != block_text if block_text else False
        context_text = f"{previous_dict_text} {dict_text}".strip()
        fragments = _known_fragments(dict_text, block_text, context_text)

        print(f"[{index}] bbox={_format_bbox(dict_bbox)} overlap={overlap:.2f}")
        print(f"    dict : {dict_text}")
        print(f"    block: {block_text or '<no match>'}")
        print(f"    differs: {'yes' if differs else 'no'}")
        if fragments:
            print(f"    known fragments: {', '.join(fragments)}")
        print()
        previous_dict_text = dict_text


def _dict_block_text(block: dict) -> str:
    parts = []
    for line in block.get("lines", []):
        spans = []
        for span in line.get("spans", []):
            text = span.get("text", "").strip()
            if not text:
                continue
            flags = span.get("flags", 0)
            spans.append(
                TextSpan(
                    text=text,
                    font=span.get("font", ""),
                    size=span.get("size", 10.0),
                    bold=bool(flags & 16),
                    italic=bool(flags & 2),
                    bbox=tuple(span["bbox"]),
                )
            )
        if spans:
            parts.append(_join_text_spans(spans))

    return " ".join(" ".join(parts).split())


def _known_fragments(*texts: str) -> list[str]:
    haystack = "\n".join(texts).lower()
    return [fragment for fragment in KNOWN_FRAGMENTS if fragment in haystack]


def _format_bbox(bbox: tuple[float, float, float, float]) -> str:
    return "(" + ", ".join(f"{value:.1f}" for value in bbox) + ")"


if __name__ == "__main__":
    raise SystemExit(main())
