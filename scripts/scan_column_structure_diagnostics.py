"""Exploratory scan for recurring vertical gaps in text-primitive coverage,
per page, that may indicate column boundaries (Milestone 32 proposal, Passo
2, revised after inspecting real data from DB.pdf/Lan.pdf/Apo.pdf).

Not a producer, not wired anywhere, no RegionCandidate, no PageAnalysis, no
structural_kind. Reports only a geometric signal for manual inspection
against the rendered page. Does not decide "number of columns"; does not
classify mono/multi-column.

Revision history of the signal itself, kept here because the design choice
below is a direct response to a real negative result, not a preference:

  v1 (whole-page): a single horizontal coverage histogram over the whole
  page height. Verified against real data (DB.pdf, Lan.pdf, Apo.pdf): worked
  for Lan.pdf (consistent central gap on most body pages) but failed almost
  completely on DB.pdf, a manual independently confirmed two-column by
  visual inspection -- gap_count was 0 on nearly every body page. Root
  cause, confirmed by construction of a synthetic counter-example: a single
  page-wide element (a title, a table border, a running header) that
  crosses the gutter position at any single row erases the gap for the
  *entire* page under a whole-page OR-aggregation, even if the other 95% of
  rows respect a clean column split. Lowering the gap-width threshold alone
  did not fix this: it surfaced scattered narrow (5-13pt) gaps at
  inconsistent x-positions per page on DB.pdf, consistent with ordinary
  word-spacing noise, not a column gutter.

  v2 (row-based persistence): text primitives are grouped into approximate
  typographic rows first (vertical bbox overlap clustering -- the same kind
  of approximation already used elsewhere in this repo for "same_baseline",
  State_Archive.md:139; not a verified typographic baseline). Gaps are
  computed per row, then only gaps that recur at the same x-position across
  a high fraction of the rows that could have shown them
  (``min_support_ratio``) are reported as "persistent". Verified on
  synthetic cases: survives a single page-wide bridging row (0.97 support
  ratio on 29/30 real column rows), rejects random per-row word-spacing
  noise (no persistent gap), gives no gap on a clean single-column page.
  Verified against real manuals (DB.pdf, Lan.pdf, Apo.pdf): recovers a
  clean central gap on Lan.pdf and most of DB.pdf that v1 had missed
  entirely, and reproduces on Apo.pdf (independently confirmed
  single-column) a persistent gap that turned out to be a side_band
  column, not a body-column split -- expected, given the explicit
  side_band policy below.

  v3 (this version, column-count bands): a single page-level persistence
  check still collapses pages that mix column counts -- e.g. a two-column
  body interrupted by a full-width table or heading, then two columns
  again -- into one page-wide ratio, which can wash out the real signal
  depending on how many rows each part contributes. Prompted directly by a
  real page (two-column body, full-width table, full-width heading,
  two-column body again) and by real DB.pdf pages showing many small gaps
  at once (state consistent with a table's internal columns, not a single
  body gutter). Rows are now segmented into contiguous bands of stable
  local column count (run-length grouping on gaps-per-row), and persistent
  gaps are computed within each band separately. This reports the raw
  column-count sequence per page (e.g. 2 -> 1 -> 2, or 2 -> 3 -> 2) without
  interpreting it: distinguishing a local increase inside an
  already-established column structure (an exception, e.g. a nested
  table/box, that should not by itself be read as changing the page's
  column structure) from a genuine drop to fewer columns and back (a
  transition that does affect reading order) is Resolution's job, out of
  scope here (Cosa NON fa questa milestone, Proposta_Milestone32 v3 SS2).
  Verified on synthetic cases: two-column / full-width-table+heading /
  two-column correctly segments into 3 bands with column counts [2, 1, 2];
  a local two-sub-column box nested inside one of two body columns
  correctly segments into [2, 3, 2], with the original body gutter still
  present as one of the two gaps reported in the middle band --
  distinguishing it geometrically from the drop-to-one-column case, where
  no gap survives in the middle band at all.

One capture + one normalize per page, PyMuPDF only (no pdfplumber): text
primitive bbox and page width/height both come from the same
``page.get_text("dict", ...)`` call in ``capture_pymupdf_page``
(pymupdf_capture.py), so there is no cross-backend frame mismatch of the
kind that motivated the ``rotation != 0``/``cropbox != mediabox`` guards in
``job_page_analysis_runner.py`` (pdfplumber-vs-PyMuPDF cross-reference for
table_candidate, Milestone 20-21) -- not reproduced here, different failure
mode. Rotation is already resolved by the canonical transform applied
during normalization (NormalizedPrimitivePage, primitive_model.py).

Visible bbox, not raw: every TextPrimitive bbox is clipped to the page frame
before use, via a local ``_visible_bbox`` -- the same pattern already
duplicated in twelve other modules in this repo (State_Archive.md:139), not
a new one.

side_band policy, declared explicitly rather than left implicit: this pass
does NOT exclude TextPrimitives already covered by side_band candidates
(singleton or local-fragment, Milestone 6). A page with a wide side_band
region will show up as ordinary text coverage; known, undecided confound
for the visual inspection step (Milestone 24's side_band x page_edge_visual
note extends to side_band x column signal), not resolved by this script.

All thresholds below (bin width, minimum gap width, minimum row support
ratio) are diagnostic defaults, not ratified production thresholds -- same
status as Milestone 26's ``cluster_margin`` default.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, TypedDict, cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "band_index",
    "band_count",
    "row_start",
    "row_end",
    "row_count",
    "y0",
    "y1",
    "column_count",
    "persistent_gap_count",
    "persistent_gaps",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan an entire PDF for horizontal gaps that persist across most "
            "text rows on a page, a candidate signal for column boundaries, "
            "for manual inspection. Not a producer, not a threshold decision."
        ),
    )
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write CSV to this path instead of stdout.",
    )
    parser.add_argument(
        "--bin-width",
        type=float,
        default=_DEFAULT_BIN_WIDTH,
        help=f"Histogram bin width in points. Default: {_DEFAULT_BIN_WIDTH}.",
    )
    parser.add_argument(
        "--min-gap-width",
        type=float,
        default=_DEFAULT_MIN_GAP_WIDTH,
        help=(
            "Minimum width in points for an uncovered run, within one row, to "
            f"be considered a candidate gap. Default: {_DEFAULT_MIN_GAP_WIDTH}."
        ),
    )
    parser.add_argument(
        "--min-support-ratio",
        type=float,
        default=_DEFAULT_MIN_SUPPORT_RATIO,
        help=(
            "Minimum fraction of eligible rows (rows whose own content span "
            "covers a given x-position) that must show a gap there for it to "
            f"be reported as persistent. Default: {_DEFAULT_MIN_SUPPORT_RATIO}."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    rows = list(
        _scan_document(
            pdf_path,
            bin_width=args.bin_width,
            min_gap_width=args.min_gap_width,
            min_support_ratio=args.min_support_ratio,
        )
    )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _scan_document(
    pdf_path: Path,
    *,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
) -> list[dict[str, object]]:
    manual = pdf_path.name
    rows: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page_number = page_index + 1
            page = document.load_page(page_index)

            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"diagnostic-page:{page_index}",
                capture_id=f"diagnostic-pymupdf-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)

            rows.extend(
                _page_band_rows(
                    primitive_page,
                    manual=manual,
                    page_number=page_number,
                    bin_width=bin_width,
                    min_gap_width=min_gap_width,
                    min_support_ratio=min_support_ratio,
                )
            )

    return rows


def _page_band_rows(
    primitive_page: NormalizedPrimitivePage,
    *,
    manual: str,
    page_number: int,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
) -> list[dict[str, object]]:
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    visible_bboxes: list[BBox] = []
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
        bin_width=bin_width,
        min_gap_width=min_gap_width,
        min_support_ratio=min_support_ratio,
    )

    if not bands:
        return [
            {
                "manual": manual,
                "page": page_number,
                "band_index": 0,
                "band_count": 0,
                "row_start": 0,
                "row_end": 0,
                "row_count": 0,
                "y0": None,
                "y1": None,
                "column_count": 0,
                "persistent_gap_count": 0,
                "persistent_gaps": (),
            }
        ]

    return [
        {
            "manual": manual,
            "page": page_number,
            "band_index": band_index,
            "band_count": len(bands),
            "row_start": band["row_start"],
            "row_end": band["row_end"],
            "row_count": band["row_count"],
            "y0": band["y0"],
            "y1": band["y1"],
            "column_count": band["column_count"],
            "persistent_gap_count": len(band["gaps"]),
            "persistent_gaps": tuple(band["gaps"]),
        }
        for band_index, band in enumerate(bands)
    ]


def _visible_bbox(
    bbox: BBox,
    *,
    page_width: float,
    page_height: float,
) -> BBox | None:
    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1, y1)


def _cluster_rows(visible_bboxes: list[BBox]) -> list[list[BBox]]:
    """Group visible bboxes into approximate typographic rows by vertical
    interval overlap: sort by y0, then merge a bbox into the current row if
    its y0 falls before the current row's running y1.

    Approximation, not a verified typographic baseline -- same status as
    ``same_baseline_*`` elsewhere in this repo (State_Archive.md:139).
    """

    if not visible_bboxes:
        return []

    ordered = sorted(visible_bboxes, key=lambda bbox: bbox[1])
    rows: list[list[BBox]] = [[ordered[0]]]
    current_y1 = ordered[0][3]
    for bbox in ordered[1:]:
        y0, y1 = bbox[1], bbox[3]
        if y0 < current_y1:
            rows[-1].append(bbox)
            current_y1 = max(current_y1, y1)
        else:
            rows.append([bbox])
            current_y1 = y1
    return rows


def _row_gaps(
    row_bboxes: list[BBox],
    *,
    bin_width: float,
    min_gap_width: float,
) -> tuple[list[tuple[float, float]], tuple[float, float]]:
    """Horizontal gaps within one row's own content extent."""

    content_x0 = min(bbox[0] for bbox in row_bboxes)
    content_x1 = max(bbox[2] for bbox in row_bboxes)
    bin_count = max(1, int((content_x1 - content_x0) / bin_width) + 2)

    covered = [False] * bin_count
    for x0, _y0, x1, _y1 in row_bboxes:
        start_bin = max(0, int((x0 - content_x0) // bin_width))
        end_bin = min(bin_count - 1, int((x1 - content_x0) // bin_width))
        for b in range(start_bin, end_bin + 1):
            covered[b] = True

    gaps: list[tuple[float, float]] = []
    gap_start: float | None = None
    for b in range(bin_count):
        bin_x0 = content_x0 + b * bin_width
        if covered[b]:
            if gap_start is not None:
                if bin_x0 - gap_start >= min_gap_width:
                    gaps.append((gap_start, bin_x0))
                gap_start = None
        elif gap_start is None:
            gap_start = bin_x0

    if gap_start is not None and content_x1 - gap_start >= min_gap_width:
        gaps.append((gap_start, content_x1))

    return gaps, (content_x0, content_x1)


def _persistent_gaps_for_rows(
    rows: list[list[BBox]],
    *,
    page_width: float,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
) -> list[tuple[float, float, float]]:
    """Find horizontal gaps that recur, at the same x-position, across a
    high fraction of the given rows' own content extent. Returns the
    persistent gaps as (start, end, average support ratio across the
    merged bins). Takes already-clustered rows so it can be scoped to a
    single band (``_segment_column_bands``) or to a whole page.
    """

    if not rows or bin_width <= 0.0:
        return []

    n_bins = int(page_width // bin_width) + 2
    eligible = [0] * n_bins
    gap_hit = [0] * n_bins

    for row_bboxes in rows:
        gaps, (row_x0, row_x1) = _row_gaps(
            row_bboxes, bin_width=bin_width, min_gap_width=min_gap_width
        )
        start_bin = max(0, int(row_x0 // bin_width))
        end_bin = min(n_bins - 1, int(row_x1 // bin_width))
        for b in range(start_bin, end_bin + 1):
            eligible[b] += 1
        for gap_start, gap_end in gaps:
            gap_start_bin = max(0, int(gap_start // bin_width))
            gap_end_bin = min(n_bins - 1, int(gap_end // bin_width))
            for b in range(gap_start_bin, gap_end_bin + 1):
                gap_hit[b] += 1

    persistent: list[tuple[float, float, float]] = []
    run_start: float | None = None
    run_ratios: list[float] = []
    for b in range(n_bins):
        ratio = (gap_hit[b] / eligible[b]) if eligible[b] > 0 else 0.0
        if ratio >= min_support_ratio:
            if run_start is None:
                run_start = b * bin_width
            run_ratios.append(ratio)
        else:
            if run_start is not None:
                persistent.append((run_start, b * bin_width, sum(run_ratios) / len(run_ratios)))
                run_start = None
                run_ratios = []
    if run_start is not None:
        persistent.append((run_start, n_bins * bin_width, sum(run_ratios) / len(run_ratios)))

    return persistent


class _RowInfo:
    __slots__ = ("bboxes", "y0", "y1", "column_count")

    def __init__(self, bboxes: list[BBox], y0: float, y1: float, column_count: int) -> None:
        self.bboxes = bboxes
        self.y0 = y0
        self.y1 = y1
        self.column_count = column_count


class _BandDict(TypedDict):
    row_start: int
    row_end: int
    row_count: int
    column_count: int
    y0: float
    y1: float
    gaps: list[tuple[float, float, float]]


def _segment_column_bands(
    rows: list[list[BBox]],
    *,
    page_width: float,
    bin_width: float,
    min_gap_width: float,
    min_support_ratio: float,
) -> list[_BandDict]:
    """Segment consecutive rows into bands of stable local column count
    (number of within-row gaps plus one), then compute persistent gaps
    within each band separately. Reports the raw column-count sequence per
    page (e.g. 2 -> 1 -> 2) without interpreting it -- see module docstring.
    """

    if not rows:
        return []

    row_infos: list[_RowInfo] = []
    for row_bboxes in rows:
        gaps, _extent = _row_gaps(row_bboxes, bin_width=bin_width, min_gap_width=min_gap_width)
        y0 = min(bbox[1] for bbox in row_bboxes)
        y1 = max(bbox[3] for bbox in row_bboxes)
        row_infos.append(_RowInfo(row_bboxes, y0, y1, len(gaps) + 1))

    bands: list[_BandDict] = []
    band_start = 0
    for i in range(1, len(row_infos) + 1):
        if i == len(row_infos) or row_infos[i].column_count != row_infos[band_start].column_count:
            band_rows = [info.bboxes for info in row_infos[band_start:i]]
            persistent_gaps = _persistent_gaps_for_rows(
                band_rows,
                page_width=page_width,
                bin_width=bin_width,
                min_gap_width=min_gap_width,
                min_support_ratio=min_support_ratio,
            )
            bands.append(
                {
                    "row_start": band_start,
                    "row_end": i - 1,
                    "row_count": i - band_start,
                    "column_count": row_infos[band_start].column_count,
                    "y0": row_infos[band_start].y0,
                    "y1": row_infos[i - 1].y1,
                    "gaps": persistent_gaps,
                }
            )
            band_start = i

    return bands


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        gaps = cast(tuple[tuple[float, float, float], ...], row["persistent_gaps"])
        writer.writerow(
            [
                row["manual"],
                row["page"],
                row["band_index"],
                row["band_count"],
                row["row_start"],
                row["row_end"],
                row["row_count"],
                row["y0"],
                row["y1"],
                row["column_count"],
                row["persistent_gap_count"],
                ";".join(f"{start}:{end}:{ratio:.2f}" for start, end, ratio in gaps),
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
