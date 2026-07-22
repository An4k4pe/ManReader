"""Read-only diagnostics for candidates in co-referenced page-analysis streams."""

from __future__ import annotations

from collections.abc import Callable

from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import (
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_co_reference_candidate_pair_measurements import (
    measure_co_referenced_page_candidate_pair,
)
from page_analysis_co_reference_candidate_primitive_set_measurements import (
    measure_co_referenced_page_candidate_primitive_sets,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
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

_CANDIDATE_PRODUCER_BY_NAME = {
    "page_analysis.singleton_side_band": "singleton-side-band",
    "page_analysis.local_fragment_side_band": "local-fragment-side-band",
    "page_analysis.page_edge_visual": "page-edge-visual",
    "page_analysis.page_covering_visual": "page-covering-visual",
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


def dump_co_referenced_page_candidate_pair_measurements(
    primitive_page: NormalizedPrimitivePage,
    *,
    first_candidate_reference: CoReferencedPageCandidateReference,
    second_candidate_reference: CoReferencedPageCandidateReference,
) -> dict[str, object]:
    """Measure one explicit candidate pair as read-only JSON-compatible data."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    references = (first_candidate_reference, second_candidate_reference)
    for field_name, reference in zip(
        ("first_candidate_reference", "second_candidate_reference"),
        references,
        strict=True,
    ):
        if not isinstance(reference, CoReferencedPageCandidateReference):
            raise ValueError(
                f"{field_name} must be a CoReferencedPageCandidateReference"
            )

    analyses = _build_required_analyses(primitive_page, references=references)
    collection = build_co_referenced_page_analyses(analyses)
    binding = bind_co_referenced_page_analyses(
        primitive_page,
        co_referenced_page_analyses=collection,
    )
    measurements = measure_co_referenced_page_candidate_pair(
        binding,
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
    )
    return {
        "diagnostic_kind": "co-referenced-candidate-pair-measurements",
        "page_id": primitive_page.page_id,
        "page_index": primitive_page.page_index,
        "source_capture_id": primitive_page.source_capture_id,
        "first_candidate_reference": _reference_to_dict(first_candidate_reference),
        "second_candidate_reference": _reference_to_dict(second_candidate_reference),
        "first_candidate_bbox": list(measurements.first_candidate_bbox),
        "second_candidate_bbox": list(measurements.second_candidate_bbox),
        "horizontal_gap": measurements.horizontal_gap,
        "vertical_gap": measurements.vertical_gap,
        "horizontal_overlap": measurements.horizontal_overlap,
        "vertical_overlap": measurements.vertical_overlap,
        "x0_delta": measurements.x0_delta,
        "y0_delta": measurements.y0_delta,
        "x1_delta": measurements.x1_delta,
        "y1_delta": measurements.y1_delta,
    }


def dump_co_referenced_page_candidate_primitive_set_measurements(
    primitive_page: NormalizedPrimitivePage,
    *,
    first_candidate_reference: CoReferencedPageCandidateReference,
    second_candidate_reference: CoReferencedPageCandidateReference,
) -> dict[str, object]:
    """Measure one explicit candidate primitive-ID relation as read-only JSON-compatible data."""

    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")
    references = (first_candidate_reference, second_candidate_reference)
    for field_name, reference in zip(
        ("first_candidate_reference", "second_candidate_reference"),
        references,
        strict=True,
    ):
        if not isinstance(reference, CoReferencedPageCandidateReference):
            raise ValueError(
                f"{field_name} must be a CoReferencedPageCandidateReference"
            )

    analyses = _build_required_analyses(primitive_page, references=references)
    collection = build_co_referenced_page_analyses(analyses)
    binding = bind_co_referenced_page_analyses(
        primitive_page,
        co_referenced_page_analyses=collection,
    )
    measurements = measure_co_referenced_page_candidate_primitive_sets(
        binding,
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
    )
    return {
        "diagnostic_kind": "co-referenced-candidate-primitive-set-measurements",
        "page_id": primitive_page.page_id,
        "page_index": primitive_page.page_index,
        "source_capture_id": primitive_page.source_capture_id,
        "first_candidate_reference": _reference_to_dict(first_candidate_reference),
        "second_candidate_reference": _reference_to_dict(second_candidate_reference),
        "first_candidate_primitive_ids": list(measurements.first_candidate_primitive_ids),
        "second_candidate_primitive_ids": list(measurements.second_candidate_primitive_ids),
        "shared_primitive_ids": list(measurements.shared_primitive_ids),
        "first_only_primitive_ids": list(measurements.first_only_primitive_ids),
        "second_only_primitive_ids": list(measurements.second_only_primitive_ids),
    }


def _build_required_analyses(
    primitive_page: NormalizedPrimitivePage,
    *,
    references: tuple[
        CoReferencedPageCandidateReference,
        CoReferencedPageCandidateReference,
    ],
) -> tuple[PageAnalysis, ...]:
    references_by_stream: dict[
        tuple[str, str], list[CoReferencedPageCandidateReference]
    ] = {}
    for reference in references:
        if reference.producer_name not in _CANDIDATE_PRODUCER_BY_NAME:
            raise ValueError(f"unsupported producer_name: {reference.producer_name}")
        stream_key = (reference.producer_name, reference.generation_id)
        references_by_stream.setdefault(stream_key, []).append(reference)

    analyses: list[PageAnalysis] = []
    for (producer_name, generation_id), stream_references in references_by_stream.items():
        candidate_producer = _CANDIDATE_PRODUCER_BY_NAME[producer_name]
        analysis = _BUILDERS[candidate_producer](
            primitive_page,
            generation_id=generation_id,
        )
        for reference in stream_references:
            _validate_produced_analysis_stream(analysis, reference=reference)
        analyses.append(analysis)
    return tuple(analyses)


def _validate_produced_analysis_stream(
    analysis: PageAnalysis,
    *,
    reference: CoReferencedPageCandidateReference,
) -> None:
    provenance = analysis.provenance
    if provenance.producer_name != reference.producer_name:
        raise ValueError("producer_name does not match the produced analysis")
    if provenance.producer_version != reference.producer_version:
        raise ValueError("producer_version does not match the produced analysis")
    if provenance.configuration_id != reference.configuration_id:
        raise ValueError("configuration_id does not match the produced analysis")
    if analysis.generation_id != reference.generation_id:
        raise ValueError("generation_id does not match the produced analysis")

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
        "candidate_reference": _reference_to_dict(reference),
        "bbox": list(candidate.bbox),
        "proposed_structural_kind": candidate.proposed_structural_kind,
        "primitive_ids": list(candidate.primitive_ids),
    }


def _reference_to_dict(
    reference: CoReferencedPageCandidateReference,
) -> dict[str, str]:
    return {
        "producer_name": reference.producer_name,
        "producer_version": reference.producer_version,
        "configuration_id": reference.configuration_id,
        "generation_id": reference.generation_id,
        "candidate_id": reference.candidate_id,
    }
