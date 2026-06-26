"""Diagnose table-like reconstruction from aligned text blocks.

This script is intentionally manual and does not affect ManReader's extraction
pipeline. It tests whether a logical table can be reconstructed from PyMuPDF text
blocks when pdfplumber CSV extraction is fragmented.
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

import fitz
import pdfplumber

HEADER_TEXT = "D6 Luogo Ritrovamento Dettagli"
ROW_RE = re.compile(r"^(?P<num>[1-6])(?:\s+(?P<rest>.*))?$")
TEXT_LINES_SETTINGS = {"vertical_strategy": "text", "horizontal_strategy": "lines"}
WORD_REGION_PADDING = 16.0


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/debug_table_like_rebuild.py test.pdf 8")
        return 2

    pdf_path = Path(sys.argv[1])
    page_number = int(sys.argv[2])
    page_index = page_number - 1

    with pdfplumber.open(pdf_path) as pdf:
        plumb_page = pdf.pages[page_index]
        region = _choose_table_region(plumb_page)

    if region is None:
        print("No candidate table-like region found")
        return 1

    with fitz.open(pdf_path) as document:
        page = document[page_index]
        blocks = _blocks_in_region(page, region)
        words = _words_in_region(page, _padded_region(region, page.rect))

    print(f"PDF: {pdf_path}")
    print(f"Page: {page_number}")
    print(f"Chosen region bbox: {_fmt_bbox(region)}")
    print()

    _print_blocks(blocks)
    _print_words(words)
    rows = _rebuild_rows(blocks, words)
    _print_rows(rows)
    _print_csv(rows)
    return 0


def _choose_table_region(page) -> tuple[float, float, float, float] | None:
    tables = page.find_tables(table_settings=TEXT_LINES_SETTINGS)
    candidates = []
    for table in tables:
        rows = table.extract() or []
        text = _rows_text(rows)
        bbox = _bbox(table.bbox)
        score = _region_score(bbox, text, rows)
        candidates.append((score, bbox, text))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    score, bbox, text = candidates[0]
    print("== Candidate regions ==")
    for candidate_score, candidate_bbox, candidate_text in candidates:
        marker = "*" if candidate_bbox == bbox else " "
        print(
            f"{marker} score={candidate_score} bbox={_fmt_bbox(candidate_bbox)} "
            f"contains_header={HEADER_TEXT in candidate_text}"
        )
    print()
    return bbox


def _region_score(
    bbox: tuple[float, float, float, float],
    text: str,
    rows: list[list[str | None]],
) -> int:
    score = 0
    if "D6" in text or HEADER_TEXT in text:
        score += 100
    # Page-8 specific diagnostic preference: header/table starts well below top narrative text.
    if 180.0 <= bbox[1] <= 240.0:
        score += 40
    score += min(len(rows), 40)
    return score


def _padded_region(
    region: tuple[float, float, float, float], page_rect: fitz.Rect
) -> tuple[float, float, float, float]:
    # pdfplumber text/lines can be slightly narrower than PyMuPDF word bboxes.
    return (
        max(float(page_rect.x0), region[0] - WORD_REGION_PADDING),
        max(float(page_rect.y0), region[1] - WORD_REGION_PADDING),
        min(float(page_rect.x1), region[2] + WORD_REGION_PADDING),
        min(float(page_rect.y1), region[3] + WORD_REGION_PADDING),
    )


def _blocks_in_region(
    page: fitz.Page, region: tuple[float, float, float, float]
) -> list[dict[str, object]]:
    blocks = []
    for block in page.get_text("blocks"):
        if len(block) < 7 or block[6] != 0:
            continue
        text = _normalize_text(block[4])
        if not text:
            continue
        bbox = _bbox(block[:4])
        if _overlap_ratio(bbox, region) <= 0.5:
            continue
        blocks.append({"bbox": bbox, "text": text})
    return sorted(blocks, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def _words_in_region(
    page: fitz.Page, region: tuple[float, float, float, float]
) -> list[dict[str, object]]:
    words = []
    for word in page.get_text("words"):
        if len(word) < 5:
            continue
        text = str(word[4]).strip()
        if not text:
            continue
        bbox = _bbox(word[:4])
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        if not (region[0] <= center_x <= region[2] and region[1] <= center_y <= region[3]):
            continue
        words.append({"bbox": bbox, "text": text})
    return sorted(words, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def _print_blocks(blocks: list[dict[str, object]]) -> None:
    print("== Blocks used ==")
    for block in blocks:
        text = str(block["text"])
        row_marker = " row-start" if _row_start(text) is not None else ""
        header_marker = " header" if HEADER_TEXT in text else ""
        print(f"bbox={_fmt_bbox(block['bbox'])}{row_marker}{header_marker}")
        print(f"  {text}")
    print()


def _print_words(words: list[dict[str, object]]) -> None:
    print("== Words used ==")
    for word in words:
        print(
            f"bbox={_fmt_bbox(word['bbox'])} col={_column_for_x(word['bbox'][0])} text={word['text']}"
        )
    print()


def _rebuild_rows(
    blocks: list[dict[str, object]], words: list[dict[str, object]]
) -> dict[str, list[str]]:
    rows = {str(num): ["", "", "", ""] for num in range(1, 7)}
    row_bands = _row_bands(blocks)
    cell_words: dict[tuple[str, int], list[dict[str, object]]] = {}

    for word in words:
        row_num = _row_for_word(word, row_bands)
        if row_num is None:
            continue
        col = _column_for_x(word["bbox"][0])
        cell_words.setdefault((row_num, col), []).append(word)

    for (row_num, col), grouped_words in cell_words.items():
        rows[row_num][col] = _join_words(grouped_words)

    return rows


def _row_bands(blocks: list[dict[str, object]]) -> dict[str, tuple[float, float]]:
    starts = []
    for block in blocks:
        start = _row_start(str(block["text"]))
        if start is None:
            continue
        num, _ = start
        bbox = block["bbox"]
        starts.append((num, bbox[1], bbox[3]))

    starts.sort(key=lambda item: item[1])
    bands = {}
    for index, (num, y0, y1) in enumerate(starts):
        previous_mid = (starts[index - 1][1] + y0) / 2 if index > 0 else y0 - 20.0
        next_mid = (y1 + starts[index + 1][1]) / 2 if index + 1 < len(starts) else y1 + 40.0
        bands[num] = (previous_mid, next_mid)
    return bands


def _row_for_word(word: dict[str, object], bands: dict[str, tuple[float, float]]) -> str | None:
    bbox = word["bbox"]
    center_y = (bbox[1] + bbox[3]) / 2
    for num, (top, bottom) in bands.items():
        if top <= center_y <= bottom:
            return num
    return None


def _row_start(text: str) -> tuple[str, str] | None:
    match = ROW_RE.match(text.strip())
    if not match:
        return None
    return match.group("num"), (match.group("rest") or "").strip()


def _column_for_x(x0: float) -> int:
    if x0 < 74.0:
        return 0
    if x0 < 150.0:
        return 1
    if x0 < 252.0:
        return 2
    return 3


def _join_words(words: list[dict[str, object]]) -> str:
    ordered = sorted(words, key=lambda item: (item["bbox"][1], item["bbox"][0]))
    return " ".join(str(word["text"]) for word in ordered)


def _print_rows(rows: dict[str, list[str]]) -> None:
    print("== Rebuilt rows ==")
    for num in sorted(rows, key=int):
        cells = rows[num]
        print(f"row {num}: {cells}")
        for index, cell in enumerate(cells):
            if not cell:
                print(f"  WARNING empty cell row={num} col={index}")
    print()


def _print_csv(rows: dict[str, list[str]]) -> None:
    print("== Diagnostic CSV ==")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["D6", "Luogo", "Ritrovamento", "Dettagli e atmosfera"])
    for num in sorted(rows, key=int):
        writer.writerow(rows[num])
    print(output.getvalue().rstrip())


def _rows_text(rows: list[list[str | None]]) -> str:
    return " ".join((cell or "").replace("\n", " ").strip() for row in rows for cell in row)


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _bbox(values: object) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = values
    return (float(x0), float(y0), float(x1), float(y1))


def _fmt_bbox(bbox: object) -> str:
    x0, y0, x1, y1 = bbox
    return f"({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})"


def _overlap_ratio(
    source: tuple[float, float, float, float], target: tuple[float, float, float, float]
) -> float:
    area = max((source[2] - source[0]) * (source[3] - source[1]), 1.0)
    x0 = max(source[0], target[0])
    y0 = max(source[1], target[1])
    x1 = min(source[2], target[2])
    y1 = min(source[3], target[3])
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    return intersection / area


if __name__ == "__main__":
    raise SystemExit(main())
