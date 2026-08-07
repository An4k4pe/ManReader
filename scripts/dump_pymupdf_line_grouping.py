"""Raw diagnostic dump: print (block_index, line_index, bbox, text snippet) for
every TextPrimitive on one page, ordered by y0 then x0, parsed from
source_observation_id ("text:b####:l####:s####", pymupdf_capture.py, verified
unchanged through primitive_normalizer.py -- same parsing already used in
compare_pymupdf_line_grouping_column_bands.py).

Purpose: verify or falsify, on raw data, the hypothesis raised to explain why
pymupdf_line grouping collapsed pages 26/68/85 into one column_count=1 band
each -- that PyMuPDF assigns a DIFFERENT block_index (or line_index) to
left-column and right-column text even when they sit at the same y, so no
single (block_index, line_index) group ever contains both sides of a gap.

Not a producer. Not wired anywhere. Read-only inspection script, output goes
to stdout/CSV for visual inspection, no threshold, no claim asserted here.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_model import NormalizedPrimitivePage, TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s\d+$")

_CSV_FIELDNAMES = (
    "block_index",
    "line_index",
    "x0",
    "y0",
    "x1",
    "y1",
    "text_snippet",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to inspect.")
    parser.add_argument("--page", type=int, required=True, help="1-indexed page number.")
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--snippet-length", type=int, default=24, help="Characters of primitive text to show."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    page_index = args.page - 1

    with fitz.open(pdf_path) as document:
        if page_index < 0 or page_index >= document.page_count:
            print(f"page out of range: {args.page}", file=sys.stderr)
            return 1

        page = document.load_page(page_index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"diagnostic-page:{page_index}",
            capture_id=f"diagnostic-dump-capture:{page_index}",
        )
        primitive_page: NormalizedPrimitivePage = normalize_backend_page_capture(capture)

    rows = list(_build_rows(primitive_page.text_primitives, snippet_length=args.snippet_length))

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _build_rows(primitives: list[TextPrimitive], *, snippet_length: int):
    unparsed_count = 0
    parsed: list[tuple[int, int, float, float, float, float, str]] = []
    for primitive in primitives:
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed_count += 1
            continue
        block_index = int(match.group(1))
        line_index = int(match.group(2))
        x0, y0, x1, y1 = primitive.bbox
        snippet = primitive.text.replace("\n", "\\n")[:snippet_length]
        parsed.append((block_index, line_index, x0, y0, x1, y1, snippet))

    if unparsed_count > 0:
        print(
            f"{unparsed_count} primitive(s) with unparseable source_observation_id, excluded",
            file=sys.stderr,
        )

    parsed.sort(key=lambda row: (row[3], row[2]))  # y0 then x0
    return parsed


def _write_rows(
    handle: TextIO, rows: list[tuple[int, int, float, float, float, float, str]]
) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for block_index, line_index, x0, y0, x1, y1, snippet in rows:
        writer.writerow(
            [block_index, line_index, f"{x0:.1f}", f"{y0:.1f}", f"{x1:.1f}", f"{y1:.1f}", snippet]
        )


if __name__ == "__main__":
    raise SystemExit(main())
