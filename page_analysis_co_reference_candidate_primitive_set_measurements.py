"""Pure contextual primitive-ID relations for one explicit candidate pair."""

from __future__ import annotations

from dataclasses import dataclass

from page_analysis_co_reference_binding import BoundCoReferencedPageAnalyses
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    resolve_co_referenced_page_candidate_reference,
)


@dataclass(frozen=True, slots=True)
class CoReferencedPageCandidatePrimitiveSetMeasurements:
    """Ordered primitive-ID relations for one contextual candidate pair."""

    first_candidate_reference: CoReferencedPageCandidateReference
    second_candidate_reference: CoReferencedPageCandidateReference
    first_candidate_primitive_ids: tuple[str, ...]
    second_candidate_primitive_ids: tuple[str, ...]
    shared_primitive_ids: tuple[str, ...]
    first_only_primitive_ids: tuple[str, ...]
    second_only_primitive_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.first_candidate_reference,
            CoReferencedPageCandidateReference,
        ):
            raise ValueError(
                "first_candidate_reference must be a "
                "CoReferencedPageCandidateReference"
            )
        if not isinstance(
            self.second_candidate_reference,
            CoReferencedPageCandidateReference,
        ):
            raise ValueError(
                "second_candidate_reference must be a "
                "CoReferencedPageCandidateReference"
            )

        for field_name in (
            "first_candidate_primitive_ids",
            "second_candidate_primitive_ids",
            "shared_primitive_ids",
            "first_only_primitive_ids",
            "second_only_primitive_ids",
        ):
            _validate_primitive_ids(getattr(self, field_name), field_name)

        first_ids = self.first_candidate_primitive_ids
        second_ids = self.second_candidate_primitive_ids
        first_id_set = set(first_ids)
        second_id_set = set(second_ids)

        expected_shared = tuple(
            primitive_id
            for primitive_id in first_ids
            if primitive_id in second_id_set
        )
        expected_first_only = tuple(
            primitive_id
            for primitive_id in first_ids
            if primitive_id not in second_id_set
        )
        expected_second_only = tuple(
            primitive_id
            for primitive_id in second_ids
            if primitive_id not in first_id_set
        )

        if self.shared_primitive_ids != expected_shared:
            raise ValueError(
                "shared_primitive_ids must be the exact first-ordered "
                "filtered subsequence shared by both candidates"
            )
        if self.first_only_primitive_ids != expected_first_only:
            raise ValueError(
                "first_only_primitive_ids must be the exact first-ordered "
                "filtered subsequence absent from the second candidate"
            )
        if self.second_only_primitive_ids != expected_second_only:
            raise ValueError(
                "second_only_primitive_ids must be the exact second-ordered "
                "filtered subsequence absent from the first candidate"
            )


def measure_co_referenced_page_candidate_primitive_sets(
    bound_co_referenced_page_analyses: BoundCoReferencedPageAnalyses,
    *,
    first_candidate_reference: CoReferencedPageCandidateReference,
    second_candidate_reference: CoReferencedPageCandidateReference,
) -> CoReferencedPageCandidatePrimitiveSetMeasurements:
    """Measure ordered primitive-ID membership within one supplied binding."""

    if not isinstance(
        bound_co_referenced_page_analyses,
        BoundCoReferencedPageAnalyses,
    ):
        raise ValueError(
            "bound_co_referenced_page_analyses must be a "
            "BoundCoReferencedPageAnalyses"
        )
    if not isinstance(
        first_candidate_reference,
        CoReferencedPageCandidateReference,
    ):
        raise ValueError(
            "first_candidate_reference must be a "
            "CoReferencedPageCandidateReference"
        )
    if not isinstance(
        second_candidate_reference,
        CoReferencedPageCandidateReference,
    ):
        raise ValueError(
            "second_candidate_reference must be a "
            "CoReferencedPageCandidateReference"
        )

    first_candidate = resolve_co_referenced_page_candidate_reference(
        bound_co_referenced_page_analyses,
        reference=first_candidate_reference,
    )
    second_candidate = resolve_co_referenced_page_candidate_reference(
        bound_co_referenced_page_analyses,
        reference=second_candidate_reference,
    )

    first_ids = first_candidate.primitive_ids
    second_ids = second_candidate.primitive_ids
    first_id_set = set(first_ids)
    second_id_set = set(second_ids)

    return CoReferencedPageCandidatePrimitiveSetMeasurements(
        first_candidate_reference=first_candidate_reference,
        second_candidate_reference=second_candidate_reference,
        first_candidate_primitive_ids=first_ids,
        second_candidate_primitive_ids=second_ids,
        shared_primitive_ids=tuple(
            primitive_id
            for primitive_id in first_ids
            if primitive_id in second_id_set
        ),
        first_only_primitive_ids=tuple(
            primitive_id
            for primitive_id in first_ids
            if primitive_id not in second_id_set
        ),
        second_only_primitive_ids=tuple(
            primitive_id
            for primitive_id in second_ids
            if primitive_id not in first_id_set
        ),
    )


def _validate_primitive_ids(value: object, field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")

    seen: set[str] = set()
    for index, primitive_id in enumerate(value):
        if not isinstance(primitive_id, str) or not primitive_id:
            raise ValueError(
                f"{field_name}[{index}] must be a non-empty string"
            )
        if primitive_id in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(primitive_id)
