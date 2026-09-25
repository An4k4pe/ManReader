"""Resolve one page's candidates by applying exactly one rule.

Proposta_ResolutionDesign_v3.md §8.2.1: when a layout.interior_visual_frame
candidate and a layout.embedded_visual candidate reference the exact same set
of primitives (first_only_primitive_ids == () and second_only_primitive_ids
== (), per measure_co_referenced_page_candidate_primitive_sets), the more
specific interior_visual_frame candidate is accepted and the generic
embedded_visual candidate is rejected as superseded. Every other candidate,
from any producer, is left unresolved: no other rule exists yet.

**La seconda regola, 20 settembre 2026** (`Criterio_SchedeDalProducerAIR2_v1.md`):
un candidato `layout.stat_block` e' accettato se una delle sue righe porta una
combinazione di etichette che la policy del documento ammette, e respinto
altrimenti. `page_analysis.stat_block` vede una pagina sola e propone in
eccesso — sulla tabella dei tesori di DB propone le righe `Tira un D6. 1: …
2: …` — perche' la ripetizione nel documento e' un fatto che una pagina non
puo' conoscere. E' qui che si decide.

Senza policy la regola tace e quei candidati restano irrisolti come prima: il
parametro e' facoltativo apposta.
"""

from __future__ import annotations

from document_stat_block_policy import StatBlockFields
from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_co_reference_candidate_primitive_set_measurements import (
    measure_co_referenced_page_candidate_primitive_sets,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import PageAnalysis, RegionCandidate
from page_analysis_stat_block import declared_labels, source_lines_of_page
from resolution_model import ResolvedCandidateOutcome, ResolvedPageCandidates

_INTERIOR_VISUAL_FRAME_PRODUCER_NAME = "page_analysis.interior_visual_frame"
_EMBEDDED_VISUAL_PRODUCER_NAME = "page_analysis.embedded_visual"
_STAT_BLOCK_PRODUCER_NAME = "page_analysis.stat_block"
_TABLE_CANDIDATE_PRODUCER_NAME = "table_candidate"
_RULED_TABLE_PRODUCER_NAME = "page_analysis.ruled_table"


def _holds_a_ruled_grid(candidate: RegionCandidate, grids: list[RegionCandidate]) -> bool:
    """La regione contiene il centro di almeno una griglia a filetti."""

    x0, y0, x1, y1 = candidate.bbox
    return any(
        x0 <= (g.bbox[0] + g.bbox[2]) / 2 < x1 and y0 <= (g.bbox[1] + g.bbox[3]) / 2 < y1
        for g in grids
    )


def _carries_an_admitted_combination(
    bound: BoundCoReferencedPageAnalyses,
    candidate: RegionCandidate,
    fields: StatBlockFields,
) -> bool:
    """Il candidato porta cio' che il documento riconosce come scheda.

    Le etichette si contano su **tutto il blocco**, non su una riga
    (`Criterio_NucleoCheSiContaInsieme_v1.md`): un manuale puo' scrivere i
    campi uno per riga — `Sentieri:`, `Mostri:`, `Umani:` — e il nucleo si vede
    solo sul blocco. Una combinazione su una riga sola resta riconosciuta,
    perche' e' contenuta nel blocco che la porta."""

    suoi = set(candidate.primitive_ids)
    etichette: set[str] = set()
    for riga in source_lines_of_page(bound.primitive_page):
        if any(primitive.primitive_id in suoi for primitive in riga):
            etichette.update(declared_labels(riga))
    return bool(etichette) and fields.carried_by(frozenset(etichette))


def resolve_page_candidates(
    bound: BoundCoReferencedPageAnalyses,
    *,
    stat_block_fields: StatBlockFields | None = None,
) -> ResolvedPageCandidates:
    """Apply the two rules to one page's candidates.

    ``stat_block_fields`` e' la policy del documento. Senza, i candidati di
    scheda restano irrisolti: e' il comportamento di prima."""

    if not isinstance(bound, BoundCoReferencedPageAnalyses):
        raise ValueError("bound must be a BoundCoReferencedPageAnalyses")
    if stat_block_fields is not None and not isinstance(stat_block_fields, StatBlockFields):
        raise ValueError("stat_block_fields must be a StatBlockFields or None")

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

    # La terza regola (`Criterio_TabellaAFiletti_v1.md`): una regione di
    # `table_candidate` e' una tabella se contiene una griglia che i filetti
    # risolvono. Tace se l'analisi a filetti non c'e'.
    rejected_table_references: list[CoReferencedPageCandidateReference] = []
    ha_filetti = any(
        a.provenance.producer_name == _RULED_TABLE_PRODUCER_NAME
        for a in bound.co_referenced_page_analyses.analyses
    )
    if ha_filetti:
        griglie = [
            c for a, c, _r in entries if a.provenance.producer_name == _RULED_TABLE_PRODUCER_NAME
        ]
        for analysis, candidate, reference in entries:
            if analysis.provenance.producer_name != _TABLE_CANDIDATE_PRODUCER_NAME:
                continue
            if _holds_a_ruled_grid(candidate, griglie):
                accepted_references.append(reference)
            else:
                rejected_table_references.append(reference)

    rejected_stat_block_references: list[CoReferencedPageCandidateReference] = []
    if stat_block_fields is not None:
        for analysis, candidate, reference in entries:
            if analysis.provenance.producer_name != _STAT_BLOCK_PRODUCER_NAME:
                continue
            if _carries_an_admitted_combination(bound, candidate, stat_block_fields):
                accepted_references.append(reference)
            else:
                rejected_stat_block_references.append(reference)

    outcomes: list[ResolvedCandidateOutcome] = []
    for _, _, reference in entries:
        if reference in rejected_table_references:
            outcomes.append(
                ResolvedCandidateOutcome(
                    candidate_reference=reference,
                    outcome="rejected",
                    reason_token="not_resolved_by_rules",
                )
            )
        elif reference in rejected_stat_block_references:
            outcomes.append(
                ResolvedCandidateOutcome(
                    candidate_reference=reference,
                    outcome="rejected",
                    reason_token="field_combination_not_recurring",
                )
            )
        elif reference in accepted_references:
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
