"""Resolve one page's candidates by applying exactly one rule.

Proposta_ResolutionDesign_v3.md §8.2.1: when a layout.interior_visual_frame
candidate and a layout.embedded_visual candidate reference the exact same set
of primitives (first_only_primitive_ids == () and second_only_primitive_ids
== (), per measure_co_referenced_page_candidate_primitive_sets), the more
specific interior_visual_frame candidate is accepted and the generic
embedded_visual candidate is rejected as superseded. Every other candidate,
from any producer, is left unresolved: no other rule exists yet.
"""

from __future__ import annotations

from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_co_reference_candidate_primitive_set_measurements import (
    measure_co_referenced_page_candidate_primitive_sets,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import PageAnalysis, RegionCandidate
from resolution_model import ResolvedCandidateOutcome, ResolvedPageCandidates

_INTERIOR_VISUAL_FRAME_PRODUCER_NAME = "page_analysis.interior_visual_frame"
_EMBEDDED_VISUAL_PRODUCER_NAME = "page_analysis.embedded_visual"


def resolve_page_candidates(
    bound: BoundCoReferencedPageAnalyses,
) -> ResolvedPageCandidates:
    """Apply the single superseded-by-more-specific rule to one page's candidates."""

    if not isinstance(bound, BoundCoReferencedPageAnalyses):
        raise ValueError("bound must be a BoundCoReferencedPageAnalyses")

    entries: list[
        tuple[PageAnalysis, RegionCandidate, CoReferencedPageCandidateReference]
    ] = []
    for analysis in bound.co_referenced_page_analyses.analyses:
        for candidate in analysis.candidates:
            reference = build_co_referenced_page_candidate_reference(
                bound,
                analysis=analysis,
                candidate=candidate,
            )
            entries.append((analysis, candidate, reference))

    interior_visual_frame_entries = [
        entry
        for entry in entries
        if entry[0].provenance.producer_name == _INTERIOR_VISUAL_FRAME_PRODUCER_NAME
    ]
    embedded_visual_entries = [
        entry
        for entry in entries
        if entry[0].provenance.producer_name == _EMBEDDED_VISUAL_PRODUCER_NAME
    ]

    accepted_references: list[CoReferencedPageCandidateReference] = []
    superseded_references: list[CoReferencedPageCandidateReference] = []

    for _, _, interior_visual_frame_reference in interior_visual_frame_entries:
        for _, _, embedded_visual_reference in embedded_visual_entries:
            if embedded_visual_reference in superseded_references:
                continue
            measurement = measure_co_referenced_page_candidate_primitive_sets(
                bound,
                first_candidate_reference=interior_visual_frame_reference,
                second_candidate_reference=embedded_visual_reference,
            )
            if (
                measurement.first_only_primitive_ids == ()
                and measurement.second_only_primitive_ids == ()
            ):
                accepted_references.append(interior_visual_frame_reference)
                superseded_references.append(embedded_visual_reference)
                break

    outcomes: list[ResolvedCandidateOutcome] = []
    for _, _, reference in entries:
        if reference in accepted_references:
            outcomes.append(
                ResolvedCandidateOutcome(
                    candidate_reference=reference,
                    outcome="accepted",
                    reason_token=None,
                )
            )
        elif reference in superseded_references:
            outcomes.append(
                ResolvedCandidateOutcome(
                    candidate_reference=reference,
                    outcome="rejected",
                    reason_token="superseded_by_more_specific",
                )
            )
        else:
            outcomes.append(
                ResolvedCandidateOutcome(
                    candidate_reference=reference,
                    outcome="unresolved",
                    reason_token="no_applicable_rule",
                )
            )

    return ResolvedPageCandidates(
        page_id=bound.co_referenced_page_analyses.page_id,
        outcomes=tuple(outcomes),
    )
