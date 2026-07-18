"""Contextual references to candidates in co-referenced page analyses."""

from __future__ import annotations

from dataclasses import dataclass

from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_model import PageAnalysis, RegionCandidate


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class CoReferencedPageCandidateReference:
    """Exact contextual tokens identifying one candidate in one analysis stream."""

    producer_name: str
    producer_version: str
    configuration_id: str
    generation_id: str
    candidate_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "producer_name",
            "producer_version",
            "configuration_id",
            "generation_id",
            "candidate_id",
        ):
            _require_non_empty_string(getattr(self, field_name), field_name)


def build_co_referenced_page_candidate_reference(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    analysis: PageAnalysis,
    candidate: RegionCandidate,
) -> CoReferencedPageCandidateReference:
    """Build a reference only for analysis and candidate objects held by a binding."""

    if not isinstance(
        bound_co_referenced_page_analyses,
        BoundCoReferencedPageAnalyses,
    ):
        raise ValueError(
            "bound_co_referenced_page_analyses must be a "
            "BoundCoReferencedPageAnalyses"
        )
    if not isinstance(analysis, PageAnalysis):
        raise ValueError("analysis must be a PageAnalysis")
    if not isinstance(candidate, RegionCandidate):
        raise ValueError("candidate must be a RegionCandidate")

    if not any(
        held_analysis is analysis
        for held_analysis in bound_co_referenced_page_analyses.co_referenced_page_analyses.analyses
    ):
        raise ValueError("analysis must belong to bound_co_referenced_page_analyses")
    if not any(held_candidate is candidate for held_candidate in analysis.candidates):
        raise ValueError("candidate must belong to analysis")

    provenance = analysis.provenance
    return CoReferencedPageCandidateReference(
        producer_name=provenance.producer_name,
        producer_version=provenance.producer_version,
        configuration_id=provenance.configuration_id,
        generation_id=analysis.generation_id,
        candidate_id=candidate.candidate_id,
    )


def resolve_co_referenced_page_candidate_reference(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    reference: CoReferencedPageCandidateReference,
) -> RegionCandidate:
    """Resolve a reference by exact analysis stream and candidate identifiers."""

    if not isinstance(
        bound_co_referenced_page_analyses,
        BoundCoReferencedPageAnalyses,
    ):
        raise ValueError(
            "bound_co_referenced_page_analyses must be a "
            "BoundCoReferencedPageAnalyses"
        )
    if not isinstance(reference, CoReferencedPageCandidateReference):
        raise ValueError("reference must be a CoReferencedPageCandidateReference")

    for analysis in bound_co_referenced_page_analyses.co_referenced_page_analyses.analyses:
        provenance = analysis.provenance
        if (
            provenance.producer_name == reference.producer_name
            and provenance.producer_version == reference.producer_version
            and provenance.configuration_id == reference.configuration_id
            and analysis.generation_id == reference.generation_id
        ):
            for candidate in analysis.candidates:
                if candidate.candidate_id == reference.candidate_id:
                    return candidate
            raise ValueError("candidate_id is not present in the matched analysis")

    raise ValueError("analysis stream is not present in bound_co_referenced_page_analyses")
