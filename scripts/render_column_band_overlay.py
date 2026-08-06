"""Diagnostic-only overlay: renders one PDF page as a PNG with the row and
band boundaries computed by scripts/scan_column_structure_diagnostics.py
(Milestone 32) drawn on top, so band-level output can be checked against the
actual page instead of guessed from a CSV + a separately-made annotated
image.

Not a producer. Not wired anywhere. Reuses the private row/band functions
from scan_column_structure_diagnostics.py unchanged (import, no copy), same
status as every other exploratory script under scripts/ (diagnostic only,
committable in sanatoria if a cited number ever depends on it -- not the
case here, this is a one-off visual check requested in chat, not a number
going into State.md).

Draws, per page:
  - a thin blue line at every row boundary (y0/y1 of each _cluster_rows
    row) -- lets you see directly whether two visually distinct lines (e.g.
    two stacked headings, or a heading immediately above a paragraph) have
    been merged into a single "row" by the vertical-overlap clustering,
    which is the open question this script exists to answer, not assume.
  - a thick red line at every band boundary (y0/y1 of each
    _segment_column_bands band), with the band's column_count printed at
    the left margin.
  - thin green vertical segments at each persistent gap's (start, end),
    limited to the band's own y-range, so a detected "column split" can be
    checked against where it actually falls on the page.

Usage (fish shell):

    set pdf DB.pdf
    python3 render_column_band_overlay.py $pdf 99 --output page99_overlay.png

Requires PyMuPDF (fitz), same dependency already used by the script it
reuses. Run this on your machine, against your local checkout -- it is not
executed here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scan_column_structure_diagnostics import (  # noqa: E402
    _cluster_rows,
    _segment_column_bands,
    _visible_bbox,
)

from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6
_ZOOM = 2.0  # render at 2x for readability; coordinates below are scaled accordingly


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file.")
    parser.add_argument("page", type=int, help="1-indexed page number.")
    parser.add_argument("--output", type=Path, required=True, help="Output PNG path.")
    parser.add_argument("--bin-width", type=float, default=_DEFAULT_BIN_WIDTH)
    parser.add_argument("--min-gap-width", type=float, default=_DEFAULT_MIN_GAP_WIDTH)
    parser.add_argument("--min-support-ratio", type=float, default=_DEFAULT_MIN_SUPPORT_RATIO)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    page_number = cast(int, args.page)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1
    if page_number < 1:
        print("page must be 1-indexed and >= 1", file=sys.stderr)
        return 1

    with fitz.open(pdf_path) as document:
        page_index = page_number - 1
        if page_index >= document.page_count:
            print(
                f"page {page_number} out of range (document has {document.page_count} pages)",
                file=sys.stderr,
            )
            return 1

        page = document.load_page(page_index)

        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"diagnostic-page:{page_index}",
            capture_id=f"diagnostic-pymupdf-capture:{page_index}",
        )
        primitive_page: NormalizedPrimitivePage = normalize_backend_page_capture(capture)

        page_width = primitive_page.page_geometry.width
        page_height = primitive_page.page_geometry.height

        visible_bboxes = []
        for text_primitive in primitive_page.text_primitives:
            visible_bbox = _visible_bbox(
                text_primitive.bbox, page_width=page_width, page_height=page_height
            )
            if visible_bbox is not None:
                visible_bboxes.append(visible_bbox)

        rows = _cluster_rows(visible_bboxes)
        bands = _segment_column_bands(
            rows,
            page_width=page_width,
            bin_width=args.bin_width,
            min_gap_width=args.min_gap_width,
            min_support_ratio=args.min_support_ratio,
        )

        matrix = fitz.Matrix(_ZOOM, _ZOOM)
        pixmap = page.get_pixmap(matrix=matrix)
        pixmap_bytes = pixmap.tobytes("png")

        overlay_doc = fitz.open()
        overlay_page = overlay_doc.new_page(width=pixmap.width, height=pixmap.height)
        overlay_page.insert_image(overlay_page.rect, stream=pixmap_bytes)

        def scaled_y(y: float) -> float:
            return y * _ZOOM

        def scaled_x(x: float) -> float:
            return x * _ZOOM

        # Row boundaries: thin blue lines across the full page width.
        for row_bboxes in rows:
            row_y0 = min(bbox[1] for bbox in row_bboxes)
            row_y1 = max(bbox[3] for bbox in row_bboxes)
            for y in (row_y0, row_y1):
                overlay_page.draw_line(
                    fitz.Point(0, scaled_y(y)),
                    fitz.Point(scaled_x(page_width), scaled_y(y)),
                    color=(0, 0, 1),
                    width=0.6,
                )

        # Band boundaries: thick red lines, with column_count annotated.
        for band in bands:
            for y in (band["y0"], band["y1"]):
                overlay_page.draw_line(
                    fitz.Point(0, scaled_y(y)),
                    fitz.Point(scaled_x(page_width), scaled_y(y)),
                    color=(1, 0, 0),
                    width=1.4,
                )
            label_y = scaled_y((band["y0"] + band["y1"]) / 2)
            overlay_page.insert_text(
                fitz.Point(2, label_y),
                f"c={band['column_count']} r={band['row_count']}",
                fontsize=9,
                color=(1, 0, 0),
            )
            for gap_start, gap_end, _ratio in band["gaps"]:
                for x in (gap_start, gap_end):
                    overlay_page.draw_line(
                        fitz.Point(scaled_x(x), scaled_y(band["y0"])),
                        fitz.Point(scaled_x(x), scaled_y(band["y1"])),
                        color=(0, 0.6, 0),
                        width=1.0,
                    )

        overlay_pixmap = overlay_page.get_pixmap()
        overlay_pixmap.save(args.output)

    print(f"wrote {args.output}")
    print(f"page {page_number}: {len(bands)} bands, {len(rows)} rows")
    for index, band in enumerate(bands):
        print(
            f"  band {index}: rows {band['row_start']}-{band['row_end']} "
            f"({band['row_count']} rows), y {band['y0']:.1f}-{band['y1']:.1f}, "
            f"column_count={band['column_count']}, gaps={band['gaps']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
