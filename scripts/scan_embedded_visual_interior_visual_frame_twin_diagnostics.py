"""Exploratory scan: missing IVF twins, cluster color distribution, color re-partition.

Proposta_Milestone35_ClusteringColorDiagnostics_v3.md, measures (i)/(ii)/(iv) — (iii) is a
readout of (iv), not computed separately here (see the CSV: count the "subcluster_*" rows per
original cluster).

Does not touch table_candidate or pdfplumber: embedded_visual and interior_visual_frame both have
requires_pdfplumber=False, so this scan is cheaper than the table x visual scan it originates
from (3e10304). Not a producer, not wired anywhere, no persistence.

Reuses dump_drawing_cluster_diagnostics (Milestone 26) and dump_interior_visual_diagnostics
(Milestone 25) unmodified for every field they already expose publicly: bbox, page_area_ratio,
excluded_reason, is_residual_interior_visual, and -- for the raster branch only --
contained_text_primitive_count. For the vector branch, contained_text_primitive_count is NOT
public (page_analysis_interior_visual_frame.py:204 _union_bbox_contained_text, :234 _contains,
both private): this script duplicates that containment logic locally, declared here rather than
hidden behind "reuse only" -- fourth instance of _contains in the repo after the three counted in
Milestone 30's closure, same precedent, same standard as scripts/scan_interior_visual_frame_diagnostics.py
(Milestone 29).

"Twin" is defined exactly as resolution_page_candidates.py:73-74 and test 32a3389 define it:
identical primitive_ids sets between an embedded_visual candidate and an interior_visual_frame
candidate on the same page. No partial-overlap definition.

(iv)'s color re-partition does not choose or imply any clustering default change: it re-runs the
same geometric adjacency rule as Milestone 26 (expanded-bbox intersection, same cluster_margin)
over the members of one already-computed cluster whose page_area_ratio is strictly above
max_area_ratio (not the full out-of-range union -- below-min clusters only produce smaller,
still-below-min subclusters, dead rows that dilute (iii) without adding information), adding one
constraint: identical color, separately for fill_color and stroke_color as two alternative
partitions. None is never treated as equal to None here -- a member with color=None never merges
with any other member on that color axis, including another None-colored member. The alternative
reading (None merges with None) would collapse every unfilled/untraced primitive on a page into
one subcluster regardless of position, which is not a partition, declared explicitly to not choose
it silently.

Fifth instance of _contains in the repo, not fourth: page_analysis_interior_visual_frame.py:234,
page_analysis_primitive_pair_measurements.py:349, page_analysis_candidate_extent_relation_measurements.py:164
(the three production instances counted at Milestone 30's closure), scripts/scan_interior_visual_frame_diagnostics.py:273
(Milestone 29, missed in that count), and this one -- second among scripts.

Known limitation, not fixed here: fill_color/stroke_color equality is exact float-tuple identity,
not perceptual color matching -- distinct_fill_colors counts distinct stored values, not distinct
colors a human would see.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from page_analysis_drawing_cluster_diagnostics import (  # noqa: E402
    dump_drawing_cluster_diagnostics,
)
from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_diagnostics import (  # noqa: E402
    dump_interior_visual_diagnostics,
)
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from page_analysis_model import PageAnalysis, RegionCandidate  # noqa: E402
from primitive_model import DrawingPrimitive, NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from verified_file_model import inspect_verified_bytes  # noqa: E402

_EMBEDDED_STRUCTURAL_KIND = "layout.embedded_visual"
_FRAME_STRUCTURAL_KIND = "layout.interior_visual_frame"

# Duplicati localmente da page_analysis_interior_visual_frame.py:64-65 (_DEFAULT_MIN_AREA_RATIO,
# _DEFAULT_MAX_AREA_RATIO), non importati: sono privati (underscore), importarli attraverso il
# confine di modulo violerebbe lo stesso principio per cui _contains e' duplicato sotto, non
# importato. Stesso rischio di drift gia' segnalato per cluster_margin in
# Proposta_ResolutionDesign_v3.md S:0 (tre costanti duplicate indipendentemente) -- dichiarato,
# non nascosto.
_MIN_AREA_RATIO = 0.006
_MAX_AREA_RATIO = 0.28
_CSV_FIELDS = [
    "page_index",
    "cluster_id",
    "role",
    "branch",
    "member_count",
    "page_area_ratio",
    "area_filter_result",
    "contained_text_count",
    "intersecting_text_count",
    "text_filter_result",
    "has_ivf_twin",
    "distinct_fill_colors",
    "distinct_stroke_colors",
    "none_fill_color_share",
    "bbox_x0",
    "bbox_y0",
    "bbox_x1",
    "bbox_y1",
]


def _candidates_of_kind(
    analysis: PageAnalysis, structural_kind: str
) -> tuple[RegionCandidate, ...]:
    return tuple(
        candidate
        for candidate in analysis.candidates
        if candidate.proposed_structural_kind == structural_kind
    )


def _area_filter_result(page_area_ratio: float | None) -> str:
    if page_area_ratio is None:
        return "n/a"
    if page_area_ratio < _MIN_AREA_RATIO:
        return "below_min"
    if page_area_ratio > _MAX_AREA_RATIO:
        return "above_max"
    return "in_range"


def _contains(container: BBox, contained: BBox) -> bool:
    return (
        container[0] <= contained[0]
        and container[1] <= contained[1]
        and container[2] >= contained[2]
        and container[3] >= contained[3]
    )


def _visible_bbox(bbox: BBox, *, page_width: float, page_height: float) -> BBox | None:
    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1, y1)


def _contained_text_count(bbox: BBox, primitive_page: NormalizedPrimitivePage) -> int:
    """Duplicated locally: mirrors _union_bbox_contained_text in
    page_analysis_interior_visual_frame.py (private, not reusable across modules)."""

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    count = 0
    for text_primitive in primitive_page.text_primitives:
        visible = _visible_bbox(text_primitive.bbox, page_width=page_width, page_height=page_height)
        if visible is None:
            continue
        if _contains(bbox, visible):
            count += 1
    return count


def _intersects(first: BBox, second: BBox) -> bool:
    return (
        first[0] < second[2]
        and second[0] < first[2]
        and first[1] < second[3]
        and second[1] < first[3]
    )


def _intersecting_text_count(bbox: BBox, primitive_page: NormalizedPrimitivePage) -> int:
    """Partial overlap, not full containment -- catches the case where a subcluster's
    shrunk union bbox no longer strictly contains text that was contained by the original,
    larger cluster (Chat B round 2, C1). Divergence between this and _contained_text_count
    on the same bbox is the signal that a containment-based reading is a geometric artifact
    of the subcluster's smaller bbox, not a fact about the page."""

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    count = 0
    for text_primitive in primitive_page.text_primitives:
        visible = _visible_bbox(text_primitive.bbox, page_width=page_width, page_height=page_height)
        if visible is None:
            continue
        if _intersects(bbox, visible):
            count += 1
    return count


def _union_bbox(bboxes: list[BBox]) -> BBox:
    return (
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    )


def _expanded_intersect(first: BBox, second: BBox, *, margin: float) -> bool:
    ef = (first[0] - margin, first[1] - margin, first[2] + margin, first[3] + margin)
    es = (second[0] - margin, second[1] - margin, second[2] + margin, second[3] + margin)
    return ef[0] <= es[2] and es[0] <= ef[2] and ef[1] <= es[3] and es[1] <= ef[3]


def _color_repartition(
    members: list[DrawingPrimitive],
    *,
    color_field: str,
    cluster_margin: float,
) -> list[list[DrawingPrimitive]]:
    """Same geometric adjacency rule as Milestone 26, plus identical-color constraint."""

    parent = {member.primitive_id: member.primitive_id for member in members}

    def find(primitive_id: str) -> str:
        while parent[primitive_id] != primitive_id:
            parent[primitive_id] = parent[parent[primitive_id]]
            primitive_id = parent[primitive_id]
        return primitive_id

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            first, second = members[i], members[j]
            first_color = getattr(first, color_field)
            second_color = getattr(second, color_field)
            # None non unisce mai, nemmeno con un altro None: colore ignoto non e'
            # evidenza di stesso colore. Dichiarato, non lasciato all'uguaglianza di Python.
            if first_color is None or second_color is None or first_color != second_color:
                continue
            if _expanded_intersect(first.bbox, second.bbox, margin=cluster_margin):
                union(first.primitive_id, second.primitive_id)

    groups: dict[str, list[DrawingPrimitive]] = defaultdict(list)
    for member in members:
        groups[find(member.primitive_id)].append(member)
    return list(groups.values())


def _twin_exists(
    primitive_ids: tuple[str, ...],
    frame_candidates: tuple[RegionCandidate, ...],
) -> bool:
    target = frozenset(primitive_ids)
    return any(frozenset(candidate.primitive_ids) == target for candidate in frame_candidates)


def _row(
    *,
    page_index: int,
    cluster_id: str,
    role: str,
    branch: str,
    member_count: int,
    page_area_ratio: float | None,
    contained_text_count: int | None,
    intersecting_text_count: int | None,
    has_ivf_twin: bool | str,
    distinct_fill_colors: int | str,
    distinct_stroke_colors: int | str,
    none_fill_color_share: float | str,
    bbox: BBox | None,
) -> dict[str, Any]:
    return {
        "page_index": page_index,
        "cluster_id": cluster_id,
        "role": role,
        "branch": branch,
        "member_count": member_count,
        "page_area_ratio": page_area_ratio,
        "area_filter_result": _area_filter_result(page_area_ratio),
        "contained_text_count": contained_text_count,
        "intersecting_text_count": intersecting_text_count,
        "text_filter_result": (
            "n/a"
            if contained_text_count is None
            else ("has_text" if contained_text_count > 0 else "no_text")
        ),
        "has_ivf_twin": has_ivf_twin,
        "distinct_fill_colors": distinct_fill_colors,
        "distinct_stroke_colors": distinct_stroke_colors,
        "none_fill_color_share": none_fill_color_share,
        "bbox_x0": bbox[0] if bbox else "",
        "bbox_y0": bbox[1] if bbox else "",
        "bbox_x1": bbox[2] if bbox else "",
        "bbox_y1": bbox[3] if bbox else "",
    }


def _scan_page(
    primitive_page: NormalizedPrimitivePage,
    *,
    page_index: int,
    generation_id: str,
    cluster_margin: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (cluster_rows, subcluster_rows) -- two granularities, kept separate per
    Chat B round 2 C3: (iv)'s subcluster fan-out has a variable count per original cluster,
    mixing it into one flat table with the cluster-level rows conflates two different things
    that happen to share columns. cluster_id is the join key between the two outputs."""
    embedded_analysis = build_embedded_visual_page_analysis(
        primitive_page, generation_id=generation_id
    )
    frame_analysis = build_interior_visual_frame_page_analysis(
        primitive_page, generation_id=generation_id
    )
    embedded_candidates = _candidates_of_kind(embedded_analysis, _EMBEDDED_STRUCTURAL_KIND)
    frame_candidates = _candidates_of_kind(frame_analysis, _FRAME_STRUCTURAL_KIND)

    raster_diagnostics = {
        cast(str, entry["primitive_id"]): entry
        for entry in cast(
            list[dict[str, object]],
            dump_interior_visual_diagnostics(primitive_page, generation_id=generation_id)[
                "visuals"
            ],
        )
        if entry["primitive_kind"] == "image"
    }
    vector_diagnostics_by_ids = {
        tuple(cast(list[str], entry["drawing_primitive_ids"])): entry
        for entry in cast(
            list[dict[str, object]],
            dump_drawing_cluster_diagnostics(
                primitive_page, generation_id=generation_id, cluster_margin=cluster_margin
            )["clusters"],
        )
    }
    drawing_by_id = {
        primitive.primitive_id: primitive for primitive in primitive_page.drawing_primitives
    }

    cluster_rows: list[dict[str, Any]] = []
    subcluster_rows: list[dict[str, Any]] = []
    for candidate in embedded_candidates:
        is_raster = "embedded-visual-raster:" in candidate.candidate_id
        has_twin = _twin_exists(candidate.primitive_ids, frame_candidates)

        if is_raster:
            entry = raster_diagnostics.get(candidate.primitive_ids[0])
            page_area_ratio = cast(float | None, entry["page_area_ratio"]) if entry else None
            contained_text_count = (
                cast(int, entry["contained_text_primitive_count"]) if entry else None
            )
            if not has_twin:
                cluster_rows.append(
                    _row(
                        page_index=page_index,
                        cluster_id=candidate.primitive_ids[0],
                        role="original",
                        branch="raster",
                        member_count=1,
                        page_area_ratio=page_area_ratio,
                        contained_text_count=contained_text_count,
                        intersecting_text_count=_intersecting_text_count(
                            candidate.bbox, primitive_page
                        ),
                        has_ivf_twin=has_twin,
                        distinct_fill_colors="n/a",
                        distinct_stroke_colors="n/a",
                        none_fill_color_share="n/a",
                        bbox=candidate.bbox,
                    )
                )
            continue

        # vector branch
        entry = vector_diagnostics_by_ids.get(tuple(sorted(candidate.primitive_ids)))
        page_area_ratio = cast(float | None, entry["page_area_ratio"]) if entry else None
        members = [
            drawing_by_id[primitive_id]
            for primitive_id in candidate.primitive_ids
            if primitive_id in drawing_by_id
        ]
        contained_text_count = _contained_text_count(candidate.bbox, primitive_page)

        distinct_fill = len({member.fill_color for member in members})
        distinct_stroke = len({member.stroke_color for member in members})
        none_fill_share = (
            sum(1 for member in members if member.fill_color is None) / len(members)
            if members
            else 0.0
        )

        # Riga "original" emessa se manca il gemello (misura i) O se il cluster ha >=2 membri
        # (misura ii, che vale per ogni cluster multi-membro indipendentemente dal gemello) --
        # due condizioni indipendenti, non un unico gate: un cluster con gemello e 1 solo membro
        # non ha nulla da riportare per nessuna delle due misure, quindi nessuna riga.
        if not has_twin or len(members) >= 2:
            cluster_rows.append(
                _row(
                    page_index=page_index,
                    cluster_id=candidate.primitive_ids[0],
                    role="original",
                    branch="vector",
                    member_count=len(members),
                    page_area_ratio=page_area_ratio,
                    contained_text_count=contained_text_count,
                    intersecting_text_count=_intersecting_text_count(
                        candidate.bbox, primitive_page
                    ),
                    has_ivf_twin=has_twin,
                    distinct_fill_colors=distinct_fill,
                    distinct_stroke_colors=distinct_stroke,
                    none_fill_color_share=none_fill_share,
                    bbox=candidate.bbox,
                )
            )

        # (iv): solo per cluster sopra il tetto d'area, non l'intero fuori-range. Un cluster
        # gia' sotto min_area_ratio produce, ripartito, solo sotto-cluster ancora piu' piccoli
        # e ancora sotto soglia -- righe morte, nessuna informazione, diluiscono (iii).
        above_max = _area_filter_result(page_area_ratio) == "above_max"
        if above_max and len(members) >= 2:
            for color_field, role in (
                ("fill_color", "subcluster_fill"),
                ("stroke_color", "subcluster_stroke"),
            ):
                for sub_group in _color_repartition(
                    members, color_field=color_field, cluster_margin=cluster_margin
                ):
                    sub_bboxes = [member.bbox for member in sub_group]
                    sub_union = _union_bbox(sub_bboxes)
                    page_width = primitive_page.page_geometry.width
                    page_height = primitive_page.page_geometry.height
                    sub_area_ratio = (
                        (sub_union[2] - sub_union[0])
                        * (sub_union[3] - sub_union[1])
                        / (page_width * page_height)
                        if page_width > 0 and page_height > 0
                        else None
                    )
                    subcluster_rows.append(
                        _row(
                            page_index=page_index,
                            cluster_id=candidate.primitive_ids[0],
                            role=role,
                            branch="vector",
                            member_count=len(sub_group),
                            page_area_ratio=sub_area_ratio,
                            contained_text_count=_contained_text_count(sub_union, primitive_page),
                            intersecting_text_count=_intersecting_text_count(
                                sub_union, primitive_page
                            ),
                            has_ivf_twin="n/a",
                            distinct_fill_colors="n/a",
                            distinct_stroke_colors="n/a",
                            none_fill_color_share="n/a",
                            bbox=sub_union,
                        )
                    )
    return cluster_rows, subcluster_rows


def scan(
    pdf_path: Path, *, cluster_margin: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pdf_bytes = pdf_path.read_bytes()
    verified_bytes = inspect_verified_bytes(pdf_bytes)
    source_id = verified_bytes.sha256

    cluster_rows: list[dict[str, Any]] = []
    subcluster_rows: list[dict[str, Any]] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as fitz_document:
        page_count = fitz_document.page_count
        for page_number in range(1, page_count + 1):
            page_index = page_number - 1
            page = fitz_document.load_page(page_index)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                continue
            generation_id = f"scan-ivf-twin:page:{page_number:04d}"
            try:
                capture = capture_pymupdf_page(
                    page,
                    source_id=source_id,
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"scan-ivf-twin:pymupdf:page:{page_number:04d}",
                )
                primitive_page = normalize_backend_page_capture(capture)
                page_cluster_rows, page_subcluster_rows = _scan_page(
                    primitive_page,
                    page_index=page_index,
                    generation_id=generation_id,
                    cluster_margin=cluster_margin,
                )
                cluster_rows.extend(page_cluster_rows)
                subcluster_rows.extend(page_subcluster_rows)
            except ValueError:
                continue
    return cluster_rows, subcluster_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument(
        "output_csv_prefix",
        type=Path,
        help="scrive <prefix>_clusters.csv (misure i/ii) e <prefix>_subclusters.csv "
        "(misura iv, cluster_id come chiave esterna verso il primo file)",
    )
    parser.add_argument("--cluster-margin", type=float, default=5.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cluster_rows, subcluster_rows = scan(args.pdf_path, cluster_margin=args.cluster_margin)
    cluster_path = args.output_csv_prefix.with_name(args.output_csv_prefix.name + "_clusters.csv")
    subcluster_path = args.output_csv_prefix.with_name(
        args.output_csv_prefix.name + "_subclusters.csv"
    )
    _write_csv(cluster_path, cluster_rows)
    _write_csv(subcluster_path, subcluster_rows)
    print(f"{len(cluster_rows)} righe cluster scritte in {cluster_path}")
    print(f"{len(subcluster_rows)} righe sotto-cluster scritte in {subcluster_path}")


if __name__ == "__main__":
    main()
