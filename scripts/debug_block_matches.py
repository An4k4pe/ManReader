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
    TextBlock,
    TextSpan,
    _best_text_block_for_bbox,
    _best_text_for_dict_match_group,
    _DictBlockMatch,
    _fallback_text_from_dict_match_group,
    _group_consecutive_dict_block_matches,
    _is_noise_block,
    _join_text_spans,
    _overlap_ratio_against_bbox,
    _text_from_block,
)

KNOWN_FRAGMENTS = (
    "Subit",
    "resistent",
    "preternatu",
    "gl",
    "deci",
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
        _print_group_diagnostic(page)
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


def _print_group_diagnostic(page) -> None:
    text_blocks = _text_blocks_from_dict(page)
    block_hints = page.get_text("blocks")
    matches = [
        _DictBlockMatch(
            dict_bbox=text_block.bbox,
            dict_text=text_block.text,
            matched_block=_best_text_block_for_bbox(text_block.bbox, block_hints),
            source_spans=text_block.spans,
        )
        for text_block in text_blocks
    ]
    groups = _group_consecutive_dict_block_matches(matches)

    print("Grouped rebuild diagnostic")
    print(f"dict TextBlocks: {len(text_blocks)}")
    print(f"groups: {len(groups)}")
    print()

    for index, group in enumerate(groups, start=1):
        if len(group) <= 1:
            continue

        block_hint_text = _text_from_block(group[0].matched_block) if group[0].matched_block else ""
        fallback_text = _fallback_text_from_dict_match_group(group)
        chosen_text = _best_text_for_dict_match_group(block_hint_text, fallback_text)
        marker = " ***" if _known_fragments(block_hint_text, fallback_text, chosen_text) else ""

        print(f"[group {index}] len={len(group)}{marker}")
        print("    dict fragments:")
        for match in group:
            print(f"      - {_format_bbox(match.dict_bbox)} {match.dict_text}")
        print(f"    block_hint_text: {block_hint_text or '<no match>'}")
        print(f"    fallback_text  : {fallback_text}")
        print(f"    chosen_text    : {chosen_text}")
        if marker:
            print(
                "    highlighted    : "
                + ", ".join(_known_fragments(block_hint_text, fallback_text, chosen_text))
            )
        print()


def _text_blocks_from_dict(page) -> list[TextBlock]:
    raw = page.get_text("dict")
    text_blocks: list[TextBlock] = []

    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue

        spans: list[TextSpan] = []
        for line in block.get("lines", []):
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

        if spans and not _is_noise_block(spans):
            text_blocks.append(TextBlock(spans=spans, bbox=tuple(block["bbox"])))

    return text_blocks


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
    return [fragment for fragment in KNOWN_FRAGMENTS if fragment.lower() in haystack]


def _format_bbox(bbox: tuple[float, float, float, float]) -> str:
    return "(" + ", ".join(f"{value:.1f}" for value in bbox) + ")"


if __name__ == "__main__":
    raise SystemExit(main())
