"""Minimal Resolution contracts: per-candidate outcomes for one page.

This module defines data-only contracts. It does not run any rule, does not
resolve or interpret candidates, and does not persist anything. The exact
shape of these contracts remains explicitly open (Proposta_ResolutionDesign_v3.md
§10): no schema_version or generation_id field is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from geometry_model import _validate_non_empty_string
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
)

_VALID_REASON_TOKENS = frozenset(
    {
        "superseded_by_more_specific",
        "no_applicable_rule",
        # Una scheda proposta le cui etichette il documento non ripete nello
        # stesso posto: `Criterio_PosizioneRelativaDeiCampi_v1.md`. Il producer
        # vede una pagina sola e non puo' saperlo, quindi propone in eccesso.
        "field_combination_not_recurring",
        # Una regione di `table_candidate` in cui la strategia a filetti non
        # trova nessuna griglia piena: una tabella che non esiste, vista dove il
        # testo si allinea. `Criterio_TabellaAFiletti_v1.md`.
        "not_resolved_by_rules",
    }
)


@dataclass(frozen=True, slots=True)
class ResolvedCandidateOutcome:
    """The single outcome Resolution assigns to one contextual candidate."""

    candidate_reference: CoReferencedPageCandidateReference
    outcome: Literal["accepted", "rejected", "unresolved"]
    reason_token: str | None
    reason_detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.candidate_reference,
            CoReferencedPageCandidateReference,
        ):
            raise ValueError(
                "candidate_reference must be a CoReferencedPageCandidateReference"
            )
        if self.outcome not in ("accepted", "rejected", "unresolved"):
            raise ValueError(
                'outcome must be one of "accepted", "rejected", "unresolved"'
            )

        if self.outcome == "accepted":
            if self.reason_token is not None:
                raise ValueError("reason_token must be None when outcome is accepted")
        else:
            if self.reason_token is None:
                raise ValueError(
                    "reason_token must not be None when outcome is not accepted"
                )
            if self.reason_token not in _VALID_REASON_TOKENS:
                raise ValueError(f"unknown reason_token: {self.reason_token!r}")

        if self.reason_detail is not None and not isinstance(self.reason_detail, str):
            raise ValueError("reason_detail must be a string or None")


@dataclass(frozen=True, slots=True)
class ResolvedPageCandidates:
    """All resolved outcomes for one declared page."""

    page_id: str
    outcomes: tuple[ResolvedCandidateOutcome, ...]

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
        if not isinstance(self.outcomes, tuple):
            raise ValueError("outcomes must be a tuple")

        seen: list[CoReferencedPageCandidateReference] = []
        for index, outcome in enumerate(self.outcomes):
            if not isinstance(outcome, ResolvedCandidateOutcome):
                raise ValueError(f"outcomes[{index}] must be a ResolvedCandidateOutcome")
            if outcome.candidate_reference in seen:
                raise ValueError("outcomes must not reference the same candidate twice")
            seen.append(outcome.candidate_reference)
