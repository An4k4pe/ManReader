"""Produce conservative candidates for embedded interior visuals.

This producer reuses, unchanged, the read-only diagnostics of Milestone 25
(page_analysis_interior_visual_diagnostics.py) and Milestone 26
(page_analysis_drawing_cluster_diagnostics.py) to promote residual interior
visuals -- raster images and vector-drawing clusters that are neither
page-covering nor page-edge -- to unresolved structural candidates. It does
not classify, rank, or apply editorial policy.

Both raster and vector residuals share a single proposed_structural_kind,
layout.embedded_visual: Resolution, not this producer, decides whether a
raster image and a vector cluster mean different things.

The excluded_reason is None check on the vector branch is load-bearing, not
incidental: _cluster_diagnostics (Milestone 26) computes
is_residual_interior_visual for excluded singletons too, so without this
check every drawing fragment discarded by the Milestone 26 pre-filter
(tiny, border_like) would be promoted here as a spurious candidate.
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

_PRODUCER_NAME = "page_analysis.embedded_visual"
_PRODUCER_VERSION = "0.1"
_CONFIGURATION_ID = "embedded-visual-v1"
_STRUCTURAL_KIND = "layout.embedded_visual"
_RASTER_CANDIDATE_ID_PREFIX = "candidate:embedded-visual-raster:"
_VECTOR_CANDIDATE_ID_PREFIX = "candidate:embedded-visual-vector:"
_DEFAULT_CLUSTER_MARGIN = 5.0


def build_embedded_visual_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    cluster_margin: float = _DEFAULT_CLUSTER_MARGIN,
) -> PageAnalysis:
    """Build and validate candidates for residual interior visuals."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("generation_id must be a non-empty string")

    candidates = [
        *_raster_candidates(primitive_page, generation_id=generation_id),
        *_vector_candidates(
            primitive_page,
            generation_id=generation_id,
            cluster_margin=cluster_margin,
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
        drawing_primitive_ids = cast(list[str], entry["drawing_primitive_ids"])
        bbox = cast(list[float], entry["bbox"])
        candidates.append(
            RegionCandidate(
                candidate_id=f"{_VECTOR_CANDIDATE_ID_PREFIX}{drawing_primitive_ids[0]}",
                page_id=primitive_page.page_id,
                bbox=cast(BBox, tuple(bbox)),
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=tuple(drawing_primitive_ids),
            )
        )
    return candidates
