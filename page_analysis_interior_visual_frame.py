"""Produce conservative candidates for text-framing interior visuals.

This producer reuses, unchanged, the read-only diagnostics of Milestone 25
(page_analysis_interior_visual_diagnostics.py) and Milestone 26
(page_analysis_drawing_cluster_diagnostics.py), the same way embedded_visual
(Milestone 27) does. It is a stricter subset of embedded_visual: only
residual interior visuals (raster images, vector-drawing clusters) that both
fall within an explicit page-area range and frame at least one contained
text primitive are promoted to unresolved structural candidates. It does not
classify, rank, or apply editorial policy.

Three notes required by design review, kept explicit rather than left
implicit:

1. The filter is not symmetric with embedded_visual. This producer
   introduces min_area_ratio/max_area_ratio as a new axis, absent from
   embedded_visual (Milestone 27), on top of the contained-text requirement.
2. The legacy text_area_ratio <= 0.70 ceiling
   (extractor.py:_asset_is_box_like_text_region) is excluded intentionally,
   not by oversight: Milestone 29's real-manual scan
   (scripts/scan_interior_visual_frame_diagnostics.py) observed valid cases
   with contained_text_area_ratio > 1.0 (dense, overlapping text) that ceiling
   would wrongly discard.
3. The relationship to embedded_visual mirrors the one already ratified
   between layout.page_edge_visual and layout.side_band (Milestone 24): two
   independent structural producers, overlap explicitly accepted
   (AGENTS.MD, "Candidati sovrapposti e concorrenti sono ammessi"), no
   contract unification. This is not a structural/semantic analogy -- it is
   the same governance precedent applied to a different pair of producers.

The vector-branch containment helper below duplicates _contains
(page_analysis_primitive_pair_measurements.py:349, strict containment, no
tolerance) locally instead of importing it (private) or reusing
measure_primitive_pair (requires primitive_id values resolvable through
_primitives_by_id, not an arbitrary bbox such as a cluster's bbox union) --
same principle already used by Milestone 26 and by the Milestone 29 script
this producer ports the logic from (scan_interior_visual_frame_diagnostics.py,
_union_bbox_contained_text/_contains).
"""

from __future__ import annotations

from typing import cast

from geometry_model import BBox
from page_analysis_drawing_cluster_diagnostics import dump_drawing_cluster_diagnostics
from page_analysis_interior_visual_diagnostics import dump_interior_visual_diagnostics
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage

_PRODUCER_NAME = "page_analysis.interior_visual_frame"
_PRODUCER_VERSION = "0.1"
_CONFIGURATION_ID = "interior-visual-frame-v1"
_STRUCTURAL_KIND = "layout.interior_visual_frame"
_RASTER_CANDIDATE_ID_PREFIX = "candidate:interior-visual-frame-raster:"
_VECTOR_CANDIDATE_ID_PREFIX = "candidate:interior-visual-frame-vector:"
_DEFAULT_CLUSTER_MARGIN = 5.0
_DEFAULT_MIN_AREA_RATIO = 0.006
_DEFAULT_MAX_AREA_RATIO = 0.28


def build_interior_visual_frame_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    cluster_margin: float = _DEFAULT_CLUSTER_MARGIN,
    min_area_ratio: float = _DEFAULT_MIN_AREA_RATIO,
    max_area_ratio: float = _DEFAULT_MAX_AREA_RATIO,
) -> PageAnalysis:
    """Build and validate candidates for text-framing residual interior visuals."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    candidates = [
        *_raster_candidates(
            primitive_page,
            generation_id=generation_id,
            min_area_ratio=min_area_ratio,
            max_area_ratio=max_area_ratio,
        ),
        *_vector_candidates(
            primitive_page,
            generation_id=generation_id,
            cluster_margin=cluster_margin,
            min_area_ratio=min_area_ratio,
            max_area_ratio=max_area_ratio,
        ),
    ]
    candidates.sort(key=lambda candidate: candidate.candidate_id)

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=_PRODUCER_NAME,
            producer_version=_PRODUCER_VERSION,
            configuration_id=_CONFIGURATION_ID,
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)
    return analysis


def _raster_candidates(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    min_area_ratio: float,
    max_area_ratio: float,
) -> list[RegionCandidate]:
    diagnostics = dump_interior_visual_diagnostics(
        primitive_page, generation_id=generation_id
    )
    candidates: list[RegionCandidate] = []
    for visual in cast(list[object], diagnostics["visuals"]):
        entry = cast(dict[str, object], visual)
        if entry["primitive_kind"] != "image":
            continue
        if entry["is_residual_interior_visual"] is not True:
            continue
        page_area_ratio = cast(float | None, entry["page_area_ratio"])
        if page_area_ratio is None or not (min_area_ratio <= page_area_ratio <= max_area_ratio):
            continue
        contained_text_primitive_count = cast(int, entry["contained_text_primitive_count"])
        if contained_text_primitive_count <= 0:
            continue

        primitive_id = cast(str, entry["primitive_id"])
        visible_bbox = cast(list[float], entry["visible_bbox"])
        candidates.append(
            RegionCandidate(
                candidate_id=f"{_RASTER_CANDIDATE_ID_PREFIX}{primitive_id}",
                page_id=primitive_page.page_id,
                bbox=cast(BBox, tuple(visible_bbox)),
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=(primitive_id,),
            )
        )
    return candidates


def _vector_candidates(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    cluster_margin: float,
    min_area_ratio: float,
    max_area_ratio: float,
) -> list[RegionCandidate]:
    diagnostics = dump_drawing_cluster_diagnostics(
        primitive_page,
        generation_id=generation_id,
        cluster_margin=cluster_margin,
    )
    candidates: list[RegionCandidate] = []
    for cluster in cast(list[object], diagnostics["clusters"]):
        entry = cast(dict[str, object], cluster)
        if entry["excluded_reason"] is not None:
            continue
        if entry["is_residual_interior_visual"] is not True:
            continue
        page_area_ratio = cast(float | None, entry["page_area_ratio"])
        if page_area_ratio is None or not (min_area_ratio <= page_area_ratio <= max_area_ratio):
            continue

        bbox_list = cast(list[float], entry["bbox"])
        union_bbox = cast(BBox, tuple(bbox_list))
        contained_text_primitive_count, _ = _union_bbox_contained_text(
            union_bbox, primitive_page
        )
        if contained_text_primitive_count <= 0:
            continue

        drawing_primitive_ids = cast(list[str], entry["drawing_primitive_ids"])
        candidates.append(
            RegionCandidate(
                candidate_id=f"{_VECTOR_CANDIDATE_ID_PREFIX}{drawing_primitive_ids[0]}",
                page_id=primitive_page.page_id,
                bbox=union_bbox,
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=tuple(drawing_primitive_ids),
            )
        )
    return candidates


def _union_bbox_contained_text(
    union_bbox: BBox,
    primitive_page: NormalizedPrimitivePage,
) -> tuple[int, float | None]:
    """Same containment/coverage logic as Milestone 25, on an arbitrary bbox."""

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    contained_count = 0
    contained_area = 0.0
    for text_primitive in primitive_page.text_primitives:
        text_visible_bbox = _visible_bbox(
            text_primitive.bbox, page_width=page_width, page_height=page_height
        )
        if text_visible_bbox is None:
            continue
        if not _contains(union_bbox, text_visible_bbox):
            continue
        contained_count += 1
        contained_area += (text_visible_bbox[2] - text_visible_bbox[0]) * (
            text_visible_bbox[3] - text_visible_bbox[1]
        )

    if contained_count == 0:
        return 0, None
    union_area = (union_bbox[2] - union_bbox[0]) * (union_bbox[3] - union_bbox[1])
    return contained_count, (contained_area / union_area if union_area > 0 else None)


def _contains(container: BBox, contained: BBox) -> bool:
    return (
        container[0] <= contained[0]
        and container[1] <= contained[1]
        and container[2] >= contained[2]
        and container[3] >= contained[3]
    )


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
