"""Pre-registered falsification test for the hypothesis raised in
Proposta_ColumnBandProducer_v6.md Sec.0 and reviewed by Chat B (Giro 2):
"PyMuPDF's own (block_index, line_index) grouping never straddles a real
column gap" -- verified so far on exactly one page (DB.pdf p.26). This
script tests it exhaustively (no sampling, no seed needed) across every
page of a manual that has independently-established column structure.

METHOD, fixed before running on any manual:

1. For every page, compute `strict` rows (_strict_cluster_rows, already
   used and committed in compare_strict_vs_loose_column_bands.py /
   inspect_row_clustering_merge_diagnostics.py) and feed them to the
   unmodified _segment_column_bands (Milestone 32). This gives, per page,
   zero or more bands with column_count>=2 and their persistent gaps
   (start, end, support_ratio) -- an independent ground truth for "where
   the column gutter is", established without reference to pymupdf_line
   grouping at all.
2. For every such band, take every pymupdf_line group ((block_index,
   line_index), recovered from TextPrimitive.source_observation_id --
   verified format in pymupdf_capture.py:124) whose vertical extent
   overlaps the band's y-range.
3. A group "straddles" a gap only if its [x0, x1] bbox extends past BOTH
   edges of the gap (x0 < gap_start AND x1 > gap_end) -- i.e. it has
   content on both sides of the whole empty zone. Corrected from a first
   version of this script that flagged ANY partial overlap: that version
   produced straddle rates of 44-50% on all three manuals, which turned
   out to be an artifact, not a signal -- verified against
   _persistent_gaps_for_rows (scan_column_structure_diagnostics.py:386-439):
   min_support_ratio=0.6 already tolerates up to 40% of the underlying
   `strict` rows having content inside the reported gap zone (ragged-right
   line endings, documented spread 22-47pt across pages, wider than the
   gap zone's own typical width), so partial overlap between a
   pymupdf_line group's edge and the nominal gap is expected and common
   regardless of whether PyMuPDF's grouping does anything wrong. Only a
   group that spans past both edges is evidence it actually merged
   left-column and right-column content into one group.

FALSIFICATION CRITERION, declared before seeing any result on any manual:
the working hypothesis ("PyMuPDF block boundaries reliably track column
membership") is RETRACTED as a general, reliable signal if the straddle
rate (straddling groups / qualifying groups) is non-negligible -- fixed
here as >2% -- on more than one of the three manuals tested (DB.pdf,
Fab.pdf, Kul.pdf). A rate at or below that bar on at most one manual is
treated as isolated, not as evidence against the hypothesis. This mirrors
the bar-based falsification style already used in the project (Milestone
35: dispersion_ratio excluded after failing against a 3x bar; the
interior_visual_frame containment test's own pre-registered bar).

No sampling: every page of every manual is scanned, so no seed is needed
and the pool-conditioning objections raised twice already in this
proposal's history (v3 Sec.0 B-nuova-1, v5 Sec.0) do not apply here --
there is no selection step to condition on.

Not a producer. Not wired anywhere. No RegionCandidate, no structural_kind,
no threshold ratified by this script alone.
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
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scan_column_structure_diagnostics import (  # noqa: E402
    _segment_column_bands,
    _visible_bbox,
)

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage, TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6
_DEFAULT_STRICT_OVERLAP_FRACTION = 0.5

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s\d+$")

_SUMMARY_FIELDNAMES = (
    "manual",
    "page",
    "band_y0",
    "band_y1",
    "column_count",
    "qualifying_groups",
    "straddling_groups",
)
_DETAIL_FIELDNAMES = (
    "manual",
    "page",
    "band_y0",
    "band_y1",
    "gap_start",
    "gap_end",
    "gap_ratio",
    "block_index",
    "line_index",
    "group_x0",
    "group_x1",
    "overlap",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--detail-output", type=Path, required=True)
    parser.add_argument("--bin-width", type=float, default=_DEFAULT_BIN_WIDTH)
    parser.add_argument("--min-gap-width", type=float, default=_DEFAULT_MIN_GAP_WIDTH)
    parser.add_argument("--min-support-ratio", type=float, default=_DEFAULT_MIN_SUPPORT_RATIO)
    parser.add_argument(
        "--strict-overlap-fraction", type=float, default=_DEFAULT_STRICT_OVERLAP_FRACTION
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    summary_rows, detail_rows = _scan_document(
        pdf_path,
        bin_width=args.bin_width,
        min_gap_width=args.min_gap_width,
        min_support_ratio=args.min_support_ratio,
        strict_overlap_fraction=args.strict_overlap_fraction,
    )

    with args.summary_output.open("w", newline="", encoding="utf-8") as handle:
        _write_summary(handle, summary_rows)
    with args.detail_output.open("w", newline="", encoding="utf-8") as handle:
        _write_detail(handle, detail_rows)

    total_qualifying = sum(cast(int, r["qualifying_groups"]) for r in summary_rows)
    total_straddling = sum(cast(int, r["straddling_groups"]) for r in summary_rows)
    rate = (total_straddling / total_qualifying * 100.0) if total_qualifying else 0.0
    pages_scanned = len({r["page"] for r in summary_rows})
    print(
        f"{pdf_path.name}: {pages_scanned} page(s) with >=1 column_count>=2 strict band, "
        f"{total_qualifying} qualifying pymupdf_line group(s), "
        f"{total_straddling} straddling ({rate:.2f}%)",
        file=sys.stderr,
    )
    return 0


def _scan_document(
    pdf_path: Path,
    *,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
    strict_overlap_fraction: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    manual = pdf_path.name
    summary_rows: list[dict[str, object]] = []
    detail_rows: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page_number = page_index + 1
            page = document.load_page(page_index)

            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"diagnostic-page:{page_index}",
                capture_id=f"diagnostic-straddle-capture:{page_index}",
            )
            primitive_page: NormalizedPrimitivePage = normalize_backend_page_capture(capture)

            page_width = primitive_page.page_geometry.width
            page_height = primitive_page.page_geometry.height

            visible_bboxes: list[BBox] = []
            visible_primitives: list[TextPrimitive] = []
            for text_primitive in primitive_page.text_primitives:
                visible_bbox = _visible_bbox(
                    text_primitive.bbox, page_width=page_width, page_height=page_height
                )
                if visible_bbox is not None:
                    visible_bboxes.append(visible_bbox)
                    visible_primitives.append(text_primitive)

            if not visible_bboxes:
                continue

            strict_rows = _strict_cluster_rows(
                visible_bboxes, overlap_fraction=strict_overlap_fraction
            )
            bands = _segment_column_bands(
                strict_rows,
                page_width=page_width,
                bin_width=bin_width,
                min_gap_width=min_gap_width,
                min_support_ratio=min_support_ratio,
            )
            multi_column_bands = [b for b in bands if b["column_count"] >= 2 and b["gaps"]]
            if not multi_column_bands:
                continue

            pymupdf_groups, _unparsed = _pymupdf_line_groups(visible_primitives)

            for band in multi_column_bands:
                band_y0 = cast(float, band["y0"])
                band_y1 = cast(float, band["y1"])
                gaps = cast(tuple[tuple[float, float, float], ...], band["gaps"])

                qualifying = 0
                straddling = 0
                for (block_index, line_index), bboxes in pymupdf_groups.items():
                    group_y0 = min(b[1] for b in bboxes)
                    group_y1 = max(b[3] for b in bboxes)
                    if max(group_y0, band_y0) >= min(group_y1, band_y1):
                        continue  # no vertical overlap with this band
                    qualifying += 1
                    group_x0 = min(b[0] for b in bboxes)
                    group_x1 = max(b[2] for b in bboxes)
                    for gap_start, gap_end, gap_ratio in gaps:
                        # A group only counts as straddling if it extends past BOTH
                        # edges of the gap -- i.e. it has content on both sides of the
                        # whole empty zone. Any partial overlap (a line's ragged right
                        # edge merely reaching into the zone, which min_support_ratio=0.6
                        # already tolerates for up to 40% of rows by construction of
                        # _persistent_gaps_for_rows) is NOT evidence the group merges
                        # both columns, and must not be counted as such.
                        spans_gap = group_x0 < gap_start and group_x1 > gap_end
                        if spans_gap:
                            overlap = min(group_x1, gap_end) - max(group_x0, gap_start)
                            straddling += 1
                            detail_rows.append(
                                {
                                    "manual": manual,
                                    "page": page_number,
                                    "band_y0": band_y0,
                                    "band_y1": band_y1,
                                    "gap_start": gap_start,
                                    "gap_end": gap_end,
                                    "gap_ratio": gap_ratio,
                                    "block_index": block_index,
                                    "line_index": line_index,
                                    "group_x0": group_x0,
                                    "group_x1": group_x1,
                                    "overlap": overlap,
                                }
                            )
                            break  # count the group once even if it straddles >1 gap

                summary_rows.append(
                    {
                        "manual": manual,
                        "page": page_number,
                        "band_y0": band_y0,
                        "band_y1": band_y1,
                        "column_count": band["column_count"],
                        "qualifying_groups": qualifying,
                        "straddling_groups": straddling,
                    }
                )

    return summary_rows, detail_rows


def _strict_cluster_rows(bboxes: list[BBox], *, overlap_fraction: float) -> list[list[BBox]]:
    """Duplicated on purpose, same rationale as compare_strict_vs_loose_column_bands.py
    and test_pymupdf_block_gap_straddle.py's own docstring."""

    if not bboxes:
        return []

    ordered = sorted(bboxes, key=lambda bbox: bbox[1])
    rows: list[list[BBox]] = [[ordered[0]]]
    last_y0, last_y1 = ordered[0][1], ordered[0][3]
    for bbox in ordered[1:]:
        y0, y1 = bbox[1], bbox[3]
        overlap = max(0.0, min(last_y1, y1) - max(last_y0, y0))
        min_height = min(last_y1 - last_y0, y1 - y0)
        fraction = (overlap / min_height) if min_height > 0 else 0.0
        if fraction >= overlap_fraction:
            rows[-1].append(bbox)
        else:
            rows.append([bbox])
        last_y0, last_y1 = y0, y1
    return rows


def _pymupdf_line_groups(
    primitives: list[TextPrimitive],
) -> tuple[dict[tuple[int, int], list[BBox]], int]:
    groups: dict[tuple[int, int], list[BBox]] = {}
    unparsed_count = 0
    for primitive in primitives:
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed_count += 1
            continue
        key = (int(match.group(1)), int(match.group(2)))
        groups.setdefault(key, []).append(primitive.bbox)
    return groups, unparsed_count


def _write_summary(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_SUMMARY_FIELDNAMES)
    for row in rows:
        writer.writerow(
            [
                row["manual"],
                row["page"],
                f"{cast(float, row['band_y0']):.1f}",
                f"{cast(float, row['band_y1']):.1f}",
                row["column_count"],
                row["qualifying_groups"],
                row["straddling_groups"],
            ]
        )


def _write_detail(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_DETAIL_FIELDNAMES)
    for row in rows:
        writer.writerow(
            [
                row["manual"],
                row["page"],
                f"{cast(float, row['band_y0']):.1f}",
                f"{cast(float, row['band_y1']):.1f}",
                f"{cast(float, row['gap_start']):.1f}",
                f"{cast(float, row['gap_end']):.1f}",
                f"{cast(float, row['gap_ratio']):.2f}",
                row["block_index"],
                row["line_index"],
                f"{cast(float, row['group_x0']):.1f}",
                f"{cast(float, row['group_x1']):.1f}",
                f"{cast(float, row['overlap']):.1f}",
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
