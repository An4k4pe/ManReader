"""Pure occurrence counts of candidate structural kinds in bound page analyses."""

from __future__ import annotations

from dataclasses import dataclass

from document_analysis_binding import BoundDocumentAnalysis


def _validate_int(value: int, field_name: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class CandidateKindPageCount:
    """Candidate occurrences of one exact kind on one included page."""

    page_index: int
    candidate_count: int

    def __post_init__(self) -> None:
        _validate_int(self.page_index, "page_index")
        _validate_int(self.candidate_count, "candidate_count", positive=True)


@dataclass(frozen=True, slots=True)
class CandidateKindOccurrenceMeasurements:
    """Occurrences of one exact candidate kind across included pages."""

    proposed_structural_kind: str
    total_candidate_count: int
    page_counts: tuple[CandidateKindPageCount, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.proposed_structural_kind, str) or not self.proposed_structural_kind:
            raise ValueError("proposed_structural_kind must be a non-empty string")
        _validate_int(self.total_candidate_count, "total_candidate_count", positive=True)
        if not isinstance(self.page_counts, tuple):
            raise ValueError("page_counts must be a tuple")
        if not self.page_counts:
            raise ValueError("page_counts must not be empty")

        previous_page_index = -1
        total_candidate_count = 0
        for index, page_count in enumerate(self.page_counts):
            if not isinstance(page_count, CandidateKindPageCount):
                raise ValueError(
                    f"page_counts[{index}] must be a CandidateKindPageCount"
                )
            if page_count.page_index <= previous_page_index:
                raise ValueError("page_counts must be strictly increasing by page_index")
            previous_page_index = page_count.page_index
            total_candidate_count += page_count.candidate_count

        if self.total_candidate_count != total_candidate_count:
            raise ValueError("total_candidate_count must match page_counts")


@dataclass(frozen=True, slots=True)
class DocumentCandidateKindOccurrenceMeasurements:
    """Exact-kind candidate occurrence counts for one bound document analysis."""

    document_page_count: int
    included_page_indices: tuple[int, ...]
    candidate_kind_occurrences: tuple[CandidateKindOccurrenceMeasurements, ...]

    def __post_init__(self) -> None:
        _validate_int(self.document_page_count, "document_page_count")
        if not isinstance(self.included_page_indices, tuple):
            raise ValueError("included_page_indices must be a tuple")

        previous_page_index = -1
        for index, page_index in enumerate(self.included_page_indices):
            _validate_int(page_index, f"included_page_indices[{index}]")
            if page_index >= self.document_page_count:
                raise ValueError("included_page_indices must be less than document_page_count")
            if page_index <= previous_page_index:
                raise ValueError(
                    "included_page_indices must be strictly increasing by page_index"
                )
            previous_page_index = page_index

        if not isinstance(self.candidate_kind_occurrences, tuple):
            raise ValueError("candidate_kind_occurrences must be a tuple")

        previous_kind: str | None = None
        included_page_index_set = set(self.included_page_indices)
        for index, occurrence in enumerate(self.candidate_kind_occurrences):
            if not isinstance(occurrence, CandidateKindOccurrenceMeasurements):
                raise ValueError(
                    "candidate_kind_occurrences["
                    f"{index}] must be a CandidateKindOccurrenceMeasurements"
                )
            if (
                previous_kind is not None
                and occurrence.proposed_structural_kind <= previous_kind
            ):
                raise ValueError(
                    "candidate_kind_occurrences must be strictly ordered by "
                    "proposed_structural_kind"
                )
            previous_kind = occurrence.proposed_structural_kind
            for page_count in occurrence.page_counts:
                if page_count.page_index not in included_page_index_set:
                    raise ValueError("page_counts page_index must be included")


def measure_document_candidate_kind_occurrences(
    bound_document_analysis: BoundDocumentAnalysis,
) -> DocumentCandidateKindOccurrenceMeasurements:
    """Count every bound candidate by its exact structural kind and page index."""

    if not isinstance(bound_document_analysis, BoundDocumentAnalysis):
        raise ValueError("bound_document_analysis must be a BoundDocumentAnalysis")

    included_page_indices = tuple(
        bound_page.reference.page_index for bound_page in bound_document_analysis.pages
    )
    counts_by_kind: dict[str, dict[int, int]] = {}
    for bound_page in bound_document_analysis.pages:
        page_index = bound_page.reference.page_index
        for candidate in bound_page.analysis.candidates:
            counts_by_page = counts_by_kind.setdefault(
                candidate.proposed_structural_kind,
                {},
            )
            counts_by_page[page_index] = counts_by_page.get(page_index, 0) + 1

    occurrences = tuple(
        CandidateKindOccurrenceMeasurements(
            proposed_structural_kind=kind,
            total_candidate_count=sum(counts_by_page.values()),
            page_counts=tuple(
                CandidateKindPageCount(
                    page_index=page_index,
                    candidate_count=candidate_count,
                )
                for page_index, candidate_count in sorted(counts_by_page.items())
            ),
        )
        for kind, counts_by_page in sorted(counts_by_kind.items())
    )
    return DocumentCandidateKindOccurrenceMeasurements(
        document_page_count=bound_document_analysis.document_analysis.page_count,
        included_page_indices=included_page_indices,
        candidate_kind_occurrences=occurrences,
    )
