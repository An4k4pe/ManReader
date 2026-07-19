"""Read-only diagnostics for candidates in co-referenced page-analysis streams."""

from __future__ import annotations

from collections.abc import Callable

from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import (
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_co_reference_candidate_reference import (
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import PageAnalysis, PageAnalysisProvenance, RegionCandidate
from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from page_analysis_side_band import (
    build_local_fragment_side_band_page_analysis,
    build_singleton_side_band_page_analysis,
)
from primitive_model import NormalizedPrimitivePage

_CANONICAL_CANDIDATE_PRODUCERS = (
    "singleton-side-band",
    "local-fragment-side-band",
    "page-edge-visual",
    "page-covering-visual",
)

type _PageAnalysisBuilder = Callable[..., PageAnalysis]

_BUILDERS: dict[str, _PageAnalysisBuilder] = {
    "singleton-side-band": build_singleton_side_band_page_analysis,
    "local-fragment-side-band": build_local_fragment_side_band_page_analysis,
    "page-edge-visual": build_page_edge_visual_page_analysis,
    "page-covering-visual": build_page_covering_visual_page_analysis,
}

_GENERATION_ID_PREFIXES = {
    "singleton-side-band": "diagnostic-singleton-side-band-analysis",
    "local-fragment-side-band": "diagnostic-local-fragment-side-band-analysis",
    "page-edge-visual": "diagnostic-page-edge-visual-analysis",
    "page-covering-visual": "diagnostic-page-covering-visual-analysis",
}


def dump_co_referenced_page_candidate_inventory(
    primitive_page: NormalizedPrimitivePage,
    *,
    candidate_producers: tuple[str, ...],
) -> dict[str, object]:
    """Return read-only JSON-compatible inventory data for requested streams."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    selected_producers = _canonical_candidate_producers(candidate_producers)

    analyses = tuple(
        _BUILDERS[candidate_producer](
            primitive_page,
            generation_id=(
                f"{_GENERATION_ID_PREFIXES[candidate_producer]}:"
                f"{primitive_page.page_index}"
            ),
        )
        for candidate_producer in selected_producers
    )
    co_referenced_page_analyses = build_co_referenced_page_analyses(analyses)
    bound_co_referenced_page_analyses = bind_co_referenced_page_analyses(
        primitive_page,
        co_referenced_page_analyses=co_referenced_page_analyses,
    )
    producer_by_analysis_id = {
        id(analysis): candidate_producer
        for candidate_producer, analysis in zip(selected_producers, analyses, strict=True)
    }

    return {
        "diagnostic_kind": "co-referenced-candidate-inventory",
        "page_id": primitive_page.page_id,
        "page_index": primitive_page.page_index,
        "source_capture_id": primitive_page.source_capture_id,
        "candidate_producers": list(selected_producers),
        "analysis_streams": [
            _analysis_stream_to_dict(
                bound_co_referenced_page_analyses,
                analysis=analysis,
                candidate_producer=producer_by_analysis_id[id(analysis)],
            )
            for analysis in co_referenced_page_analyses.analyses
        ],
    }


def _canonical_candidate_producers(
    candidate_producers: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(candidate_producers, tuple):
        raise ValueError("candidate_producers must be a tuple")
    if not candidate_producers:
        raise ValueError("candidate_producers must not be empty")

    seen_producers: set[str] = set()
    for index, candidate_producer in enumerate(candidate_producers):
        if not isinstance(candidate_producer, str) or not candidate_producer:
            raise ValueError(
                f"candidate_producers[{index}] must be a non-empty string"
            )
        if candidate_producer not in _BUILDERS:
            raise ValueError(f"unknown candidate producer: {candidate_producer}")
        if candidate_producer in seen_producers:
            raise ValueError(f"duplicate candidate producer: {candidate_producer}")
        seen_producers.add(candidate_producer)

    return tuple(
        candidate_producer
        for candidate_producer in _CANONICAL_CANDIDATE_PRODUCERS
        if candidate_producer in seen_producers
    )


def _analysis_stream_to_dict(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    analysis: PageAnalysis,
    candidate_producer: str,
) -> dict[str, object]:
    return {
        "candidate_producer": candidate_producer,
        "provenance": _provenance_to_dict(analysis.provenance),
        "generation_id": analysis.generation_id,
        "candidates": [
            _candidate_to_dict(
                bound_co_referenced_page_analyses,
                analysis=analysis,
                candidate=candidate,
            )
            for candidate in analysis.candidates
        ],
    }


def _provenance_to_dict(provenance: PageAnalysisProvenance) -> dict[str, str]:
    return {
        "source_id": provenance.source_id,
        "source_capture_id": provenance.source_capture_id,
        "source_page_id": provenance.source_page_id,
        "source_primitive_schema_version": provenance.source_primitive_schema_version,
        "producer_name": provenance.producer_name,
        "producer_version": provenance.producer_version,
        "configuration_id": provenance.configuration_id,
    }


def _candidate_to_dict(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    analysis: PageAnalysis,
    candidate: RegionCandidate,
) -> dict[str, object]:
    reference = build_co_referenced_page_candidate_reference(
        bound_co_referenced_page_analyses,
        analysis=analysis,
        candidate=candidate,
    )
    return {
        "candidate_reference": {
            "producer_name": reference.producer_name,
            "producer_version": reference.producer_version,
            "configuration_id": reference.configuration_id,
            "generation_id": reference.generation_id,
            "candidate_id": reference.candidate_id,
        },
        "bbox": list(candidate.bbox),
        "proposed_structural_kind": candidate.proposed_structural_kind,
        "primitive_ids": list(candidate.primitive_ids),
    }
