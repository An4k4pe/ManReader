"""Manual diagnostic for text/table/vector overlaps on a PDF page.

This script is intentionally outside the conversion pipeline: it helps inspect
layout evidence before deciding whether extractor rules should change.
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz
import pdfplumber

KEY_PHRASES = (
    "D6 Luogo",
    "Casa di una famiglia comune",
    "La piccola cappella",
    "La stalla del maniscalco",
    "La casa del parroco",
    "Il pozzo della piazza",
)

BBox = tuple[float, float, float, float]


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/debug_table_overlaps.py test.pdf 8")
        return 2

    pdf_path = Path(sys.argv[1])
    page_number = int(sys.argv[2])
    page_index = page_number - 1

    with fitz.open(pdf_path) as document:
        page = document[page_index]
        text_blocks = _text_blocks(page)
        vector_blocks = _vector_blocks(page)

    with pdfplumber.open(pdf_path) as pdf:
        plumber_page = pdf.pages[page_index]
        tables = _tables(plumber_page)

    print(f"PDF: {pdf_path}")
    print(f"Page: {page_number}")
    print()

    _print_text_blocks(text_blocks, tables)
    _print_tables(tables)
    _print_vectors(vector_blocks, tables)
    return 0


def _text_blocks(page: fitz.Page) -> list[dict[str, object]]:
    blocks = []
    for block in page.get_text("blocks"):
        if len(block) < 7 or block[6] != 0:
            continue
        text = _normalize_text(block[4])
        if not text:
            continue
        blocks.append(
            {
                "bbox": _bbox(block[:4]),
                "text": text,
                "block_no": block[5],
                "highlight": _highlight(text),
            }
        )
    return blocks


def _tables(page: pdfplumber.page.Page) -> list[dict[str, object]]:
    tables = []
    for index, table in enumerate(page.find_tables(), start=1):
        rows = table.extract() or []
        column_count = max((len(row) for row in rows), default=0)
        text = _normalize_text(" ".join(cell or "" for row in rows for cell in row))
        tables.append(
            {
                "index": index,
                "bbox": _bbox(table.bbox),
                "rows": len(rows),
                "columns": column_count,
                "text": text,
                "highlight": _highlight(text),
            }
        )
    return tables


def _vector_blocks(page: fitz.Page) -> list[dict[str, object]]:
    vectors = []
    for index, drawing in enumerate(page.get_drawings(), start=1):
        rect = drawing.get("rect")
        if rect is None or rect.is_empty or rect.is_infinite:
            continue
        vectors.append({"index": index, "bbox": (rect.x0, rect.y0, rect.x1, rect.y1)})
    return vectors


def _print_text_blocks(
    text_blocks: list[dict[str, object]], tables: list[dict[str, object]]
) -> None:
    print('== Text blocks: page.get_text("blocks") ==')
    for block in text_blocks:
        bbox = block["bbox"]
        text = str(block["text"])
        marker = " ***" if block["highlight"] else ""
        print(f"text#{block['block_no']} bbox={_fmt_bbox(bbox)}{marker}")
        print(f"  {_short(text)}")
        for table in tables:
            ratio = _overlap_ratio(bbox, table["bbox"])
            if ratio > 0:
                print(f"  overlap text→table#{table['index']}: {ratio:.3f}")
    print()


def _print_tables(tables: list[dict[str, object]]) -> None:
    print("== Tables: pdfplumber.find_tables() ==")
    if not tables:
        print("(none)")
        print()
        return

    for table in tables:
        marker = " ***" if table["highlight"] else ""
        print(
            f"table#{table['index']} bbox={_fmt_bbox(table['bbox'])} "
            f"rows={table['rows']} cols={table['columns']} path/csv=(not written by diagnostic){marker}"
        )
        print(f"  {_short(str(table['text']))}")
    print()


def _print_vectors(vectors: list[dict[str, object]], tables: list[dict[str, object]]) -> None:
    print("== Vectors/drawings: page.get_drawings() ==")
    if not vectors:
        print("(none)")
        return

    for vector in vectors:
        bbox = vector["bbox"]
        overlaps = []
        for table in tables:
            ratio = _overlap_ratio(bbox, table["bbox"])
            if ratio > 0:
                overlaps.append(f"vector→table#{table['index']}={ratio:.3f}")
        suffix = f" | {'; '.join(overlaps)}" if overlaps else ""
        print(f"vector#{vector['index']} bbox={_fmt_bbox(bbox)}{suffix}")


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _highlight(text: str) -> bool:
    return any(phrase in text for phrase in KEY_PHRASES)


def _short(text: str, limit: int = 220) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}…"


def _bbox(values: object) -> BBox:
    x0, y0, x1, y1 = values
    return (float(x0), float(y0), float(x1), float(y1))


def _fmt_bbox(bbox: object) -> str:
    x0, y0, x1, y1 = bbox
    return f"({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})"


def _overlap_ratio(source: object, target: object) -> float:
    source_bbox = _bbox(source)
    target_bbox = _bbox(target)
    area = _area(source_bbox)
    if area == 0.0:
        return 0.0
    return _intersection_area(source_bbox, target_bbox) / area


def _intersection_area(first: BBox, second: BBox) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return _area((x0, y0, x1, y1))


def _area(bbox: BBox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


if __name__ == "__main__":
    raise SystemExit(main())
