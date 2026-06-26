"""Compare pdfplumber table detection settings on one PDF page.

This script is diagnostic only and does not affect ManReader's extraction
pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

KEY_PHRASES = (
    "D6 Luogo",
    "Casa di una famiglia comune",
    "La stalla del maniscalco",
    "Il pozzo della piazza",
)

CONFIGS = [
    ("default", {}),
    (
        "lines/lines",
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
    ),
    (
        "lines_strict/lines_strict",
        {"vertical_strategy": "lines_strict", "horizontal_strategy": "lines_strict"},
    ),
    (
        "text/text",
        {"vertical_strategy": "text", "horizontal_strategy": "text"},
    ),
    (
        "lines/text",
        {"vertical_strategy": "lines", "horizontal_strategy": "text"},
    ),
    (
        "text/lines",
        {"vertical_strategy": "text", "horizontal_strategy": "lines"},
    ),
]


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/debug_pdfplumber_table_settings.py test.pdf 8")
        return 2

    pdf_path = Path(sys.argv[1])
    page_number = int(sys.argv[2])
    summary: list[dict[str, object]] = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        print(f"PDF: {pdf_path}")
        print(f"Page: {page_number}")
        print()
        for name, settings in CONFIGS:
            summary.extend(_print_config_result(page, name, settings))

    _print_summary(summary)
    return 0


def _print_config_result(page, name: str, settings: dict[str, str]) -> list[dict[str, object]]:
    print(f"== {name} ==")
    try:
        tables = page.find_tables(table_settings=settings)
    except Exception as error:
        print(f"error: {error}")
        print()
        return []

    results = []
    print(f"tables: {len(tables)}")
    for index, table in enumerate(tables, start=1):
        rows = table.extract() or []
        row_count = len(rows)
        column_count = max((len(row) for row in rows), default=0)
        cell_count = row_count * column_count
        non_empty = sum(1 for row in rows for cell in row if (cell or "").strip())
        density = (non_empty / cell_count * 100.0) if cell_count else 0.0
        score = _table_score(non_empty, row_count, column_count)
        text = _rows_text(rows)
        hits = [phrase for phrase in KEY_PHRASES if phrase in text]
        result = {
            "strategy": name,
            "index": index,
            "bbox": table.bbox,
            "rows": row_count,
            "cols": column_count,
            "non_empty": non_empty,
            "density": density,
            "score": score,
            "hits": hits,
        }
        results.append(result)
        print(
            f"table#{index} strategy={name} bbox={_fmt_bbox(table.bbox)} "
            f"rows={row_count} cols={column_count} non_empty={non_empty} "
            f"filled={density:.1f}% score={score}"
        )
        print(f"  contains: {', '.join(hits) if hits else '-'}")
        for row_index, row in enumerate(rows[:4], start=1):
            print(f"  row{row_index}: {_short(_fmt_row(row))}")
    print()
    return results


def _table_score(non_empty: int, rows: int, columns: int) -> int:
    score = non_empty + rows * 2 + columns
    if rows < 2:
        score -= 10
    if non_empty == 0:
        score -= 20
    return score


def _print_summary(summary: list[dict[str, object]]) -> None:
    print("== Summary by score ==")
    if not summary:
        print("(no tables)")
        return

    ranked = sorted(summary, key=lambda item: int(item["score"]), reverse=True)
    for item in ranked:
        hits = item["hits"]
        print(
            f"score={item['score']:>3} strategy={item['strategy']} table#{item['index']} "
            f"bbox={_fmt_bbox(item['bbox'])} rows={item['rows']} cols={item['cols']} "
            f"non_empty={item['non_empty']} filled={item['density']:.1f}% "
            f"contains={', '.join(hits) if hits else '-'}"
        )


def _rows_text(rows: list[list[str | None]]) -> str:
    return " ".join((cell or "").replace("\n", " ").strip() for row in rows for cell in row)


def _fmt_row(row: list[str | None]) -> str:
    cells = [" ".join((cell or "").split()) for cell in row]
    return " | ".join(cells)


def _fmt_bbox(bbox: object) -> str:
    x0, y0, x1, y1 = bbox
    return f"({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})"


def _short(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}…"


if __name__ == "__main__":
    raise SystemExit(main())
