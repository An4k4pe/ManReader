"""Exploratory check: does the region behind each of the 8 Milestone 35 oracle clusters (or any
other cluster given its bbox) contain text matching the legacy callout pattern
(ir_builder.py: _is_callout_title_block, _is_callout_body_text) -- a short all-caps title
followed by a body paragraph of at least 40 characters?

Origin: ir_builder.py's _merge_callout_blocks (legacy pipeline, extractor.py -> ir_builder.py ->
DocumentIR 1.0, State.md "Pipeline legacy e baseline da preservare", "callout DB region-first"
listed as a protected non-regression) already recognizes callout boxes -- but by TEXT PATTERN,
tied to a nearby image/vector "region" block, not by dispersion_ratio/area/color on the region
itself. If our 8 (soon more) oracle clusters that turned out to be "box a sfondo colorato che
incornicia testo" (modulo_ui_statblock/lista/regole) match this text pattern and the genuinely
decorative ones (pannello_decorativo) do not, the discriminating signal Milestone 35 has been
looking for in geometry/color already exists in the project, just in the other pipeline.

Duplicated locally, declared explicitly, NOT imported: _is_callout_title_block and
_is_callout_body_text in ir_builder.py operate on BlockIR (block.type, block.role, block.text,
block.bbox, font-size-derived heading detection via _looks_like_section_heading_block) -- objects
this script does not build (that requires running the full legacy extractor.py pipeline, out of
scope for a quick check). This script reimplements only the pure string-level logic of those two
functions, applied to individual NormalizedPrimitivePage text_primitives inside a given bbox --
NOT the geometric title-to-region tying (_title_tied_to_region) or the section-heading exclusion
(font-size dependent, no font-size field on TextPrimitive at this layer). A positive result here
is necessary-but-weaker evidence than what ir_builder.py itself would compute; a negative result
is not proof the legacy detector would also fail, only that the simplified string check does.

Not a producer, not wired anywhere, no persistence, no PDF/pdfplumber dependency beyond fitz for
the capture already used by the other Milestone 35 scripts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from verified_file_model import inspect_verified_bytes  # noqa: E402


def _intersects(first: BBox, second: BBox) -> bool:
    return (
        first[0] < second[2]
        and second[0] < first[2]
        and first[1] < second[3]
        and second[1] < first[3]
    )


def _is_title_like(text: str) -> bool:
    """Duplicated string-level core of ir_builder.py:_is_callout_title_block. Omits the
    role!=None check (no BlockIR here) and _looks_like_section_heading_block (font-size
    dependent, not available on raw TextPrimitive)."""
    stripped = " ".join(text.split())
    if not stripped or len(stripped) > 50:
        return False
    if stripped.startswith(("-", "–", "—")):
        return False
    words = stripped.split()
    if not 1 <= len(words) <= 6:
        return False
    if not any(character.isalpha() for character in stripped):
        return False
    if not stripped.isupper():
        return False
    return not stripped.endswith((".", ",", ";", ":"))


def _is_body_fragment_like(text: str) -> bool:
    stripped = " ".join(text.split())
    if not stripped:
        return False
    if stripped.startswith(('"', "“", "”", "-", "–", "—")):
        return False
    return not stripped.isupper()


def _is_body_like(text: str) -> bool:
    stripped = " ".join(text.split())
    return len(stripped) >= 40 and _is_body_fragment_like(stripped)


def check_region(primitive_page: NormalizedPrimitivePage, *, bbox: BBox) -> dict[str, Any]:
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    def _visible(text_bbox: BBox) -> BBox | None:
        x0 = max(0.0, text_bbox[0])
        y0 = max(0.0, text_bbox[1])
        x1 = min(page_width, text_bbox[2])
        y1 = min(page_height, text_bbox[3])
        if x0 >= x1 or y0 >= y1:
            return None
        return (x0, y0, x1, y1)

    title_candidates: list[str] = []
    body_candidates: list[str] = []
    combined_text_parts: list[str] = []

    rows = sorted(
        (
            (visible[1], primitive.text)
            for primitive in primitive_page.text_primitives
            if (visible := _visible(primitive.bbox)) is not None and _intersects(bbox, visible)
        ),
        key=lambda row: row[0],
    )

    for _, text in rows:
        if not text or not text.strip():
            continue
        combined_text_parts.append(text.strip())
        if _is_title_like(text) and text.strip() not in title_candidates:
            title_candidates.append(text.strip())
        if _is_body_like(text) and text.strip() not in body_candidates:
            body_candidates.append(text.strip())

    combined_text = " ".join(combined_text_parts)
    combined_is_body_like = _is_body_like(combined_text)

    return {
        "text_primitive_count_in_region": len(rows),
        "title_like_lines": title_candidates[:5],
        "body_like_lines_individual": [text[:80] for text in body_candidates[:3]],
        "combined_text_is_body_like": combined_is_body_like,
        "has_title_and_body_pattern": bool(title_candidates)
        and (bool(body_candidates) or combined_is_body_like),
    }


def scan_one(pdf_path: Path, *, page_index: int, bbox: BBox) -> dict[str, Any]:
    pdf_bytes = pdf_path.read_bytes()
    verified_bytes = inspect_verified_bytes(pdf_bytes)
    source_id = verified_bytes.sha256
    with fitz.open(stream=pdf_bytes, filetype="pdf") as fitz_document:
        page = fitz_document.load_page(page_index)
        page_number = page_index + 1
        capture = capture_pymupdf_page(
            page,
            source_id=source_id,
            page_id=f"page:{page_number:04d}",
            capture_id=f"check-callout:pymupdf:page:{page_number:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
    return check_region(primitive_page, bbox=bbox)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("page_index", type=int, help="0-based")
    parser.add_argument("bbox", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = scan_one(args.pdf_path, page_index=args.page_index, bbox=tuple(args.bbox))
    import json

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
