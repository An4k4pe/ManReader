"""Render a PDF page with an overlay box per (block_index, line_index) group,
colored by block_index, plus a "b{block}:l{line}" label -- visual counterpart
to dump_pymupdf_line_grouping.py, to check by eye whether PyMuPDF's own block
boundaries follow the left/right column split instead of reading raw numbers.

Not a producer. Not wired anywhere. Read-only inspection script.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

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

_ZOOM = 2.0

# Distinct, high-contrast palette, cycled by block_index. Kept short and
# readable rather than procedurally generated, so colors stay distinguishable
# on a printed manual page.
_PALETTE = [
    (0.85, 0.10, 0.10),  # red
    (0.10, 0.45, 0.85),  # blue
    (0.10, 0.65, 0.20),  # green
    (0.90, 0.55, 0.05),  # orange
    (0.55, 0.15, 0.75),  # purple
    (0.85, 0.75, 0.05),  # yellow
    (0.05, 0.70, 0.70),  # teal
    (0.85, 0.30, 0.55),  # pink
]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to render.")
    parser.add_argument("--page", type=int, required=True, help="1-indexed page number.")
    parser.add_argument("--output", type=Path, required=True, help="Output PNG path.")
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
            capture_id=f"diagnostic-overlay-capture:{page_index}",
        )
        primitive_page: NormalizedPrimitivePage = normalize_backend_page_capture(capture)

        groups = _group_by_block_line(primitive_page.text_primitives)

        pixmap = page.get_pixmap(matrix=fitz.Matrix(_ZOOM, _ZOOM))
        overlay_doc = fitz.open()
        overlay_page = overlay_doc.new_page(width=pixmap.width, height=pixmap.height)
        overlay_page.insert_image(overlay_page.rect, pixmap=pixmap)

        for (block_index, line_index), bboxes in groups.items():
            x0 = min(b[0] for b in bboxes)
            y0 = min(b[1] for b in bboxes)
            x1 = max(b[2] for b in bboxes)
            y1 = max(b[3] for b in bboxes)
            color = _PALETTE[block_index % len(_PALETTE)]
            rect = fitz.Rect(x0 * _ZOOM, y0 * _ZOOM, x1 * _ZOOM, y1 * _ZOOM)
            overlay_page.draw_rect(rect, color=color, width=1.2)
            overlay_page.insert_text(
                (rect.x0, max(rect.y0 - 2, 0)),
                f"b{block_index}:l{line_index}",
                fontsize=6,
                color=color,
            )

        out_pixmap = overlay_page.get_pixmap()
        out_pixmap.save(str(args.output))

    print(f"wrote {args.output}")
    return 0


def _group_by_block_line(
    primitives: list[TextPrimitive],
) -> dict[tuple[int, int], list[tuple[float, float, float, float]]]:
    groups: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    unparsed_count = 0
    for primitive in primitives:
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed_count += 1
            continue
        key = (int(match.group(1)), int(match.group(2)))
        groups.setdefault(key, []).append(primitive.bbox)

    if unparsed_count > 0:
        print(
            f"{unparsed_count} primitive(s) with unparseable source_observation_id, excluded",
            file=sys.stderr,
        )

    return groups


if __name__ == "__main__":
    raise SystemExit(main())
