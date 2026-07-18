"""Tests for pure exact-kind candidate occurrence measurements."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import cast

from document_analysis_binding import BoundDocumentAnalysis, bind_document_analysis
from document_analysis_candidate_kind_measurements import (
    CandidateKindOccurrenceMeasurements,
    CandidateKindPageCount,
    DocumentCandidateKindOccurrenceMeasurements,
    measure_document_candidate_kind_occurrences,
)
from document_analysis_model import (
    DOCUMENT_ANALYSIS_SCHEMA_VERSION,
    DocumentAnalysis,
    DocumentAnalysisProvenance,
    PageAnalysisReference,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)


def _provenance(page_index: int, page_id: str) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id="source-1",
        source_capture_id=f"capture-{page_index}",
        source_page_id=page_id,
        source_primitive_schema_version="1.0",
        producer_name="page-producer",
        producer_version="0.1",
        configuration_id="page-config-v1",
    )


def _reference(page_index: int) -> PageAnalysisReference:
    page_id = f"page-{page_index}"
    return PageAnalysisReference(
        page_index=page_index,
        page_id=page_id,
        page_analysis_schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        page_analysis_generation_id=f"analysis-generation-{page_index}",
        provenance=_provenance(page_index, page_id),
    )


def _candidate(candidate_id: str, page_id: str, kind: str) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id=page_id,
        bbox=(0.0, 0.0, 10.0, 10.0),
        proposed_structural_kind=kind,
    )


def _analysis(
    reference: PageAnalysisReference,
    candidates: tuple[RegionCandidate, ...] = (),
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=reference.page_analysis_generation_id,
        page_id=reference.page_id,
        provenance=reference.provenance,
        candidates=candidates,
    )


def _bound_document(
    *,
    page_count: int,
    page_indices: tuple[int, ...] = (),
    candidates_by_page: dict[int, tuple[RegionCandidate, ...]] | None = None,
):
    references = tuple(_reference(page_index) for page_index in page_indices)
    document = DocumentAnalysis(
        schema_version=DOCUMENT_ANALYSIS_SCHEMA_VERSION,
        generation_id="document-generation-1",
        page_count=page_count,
        provenance=DocumentAnalysisProvenance(
            source_id="source-1",
            producer_name="document-producer",
            producer_version="0.1",
            configuration_id="document-config-v1",
        ),
        pages=references,
    )
    analyses = tuple(
        _analysis(
            reference,
            () if candidates_by_page is None else candidates_by_page.get(reference.page_index, ()),
        )
        for reference in references
    )
    return bind_document_analysis(document, analyses=analyses)


class CandidateKindPageCountTests(unittest.TestCase):
    def test_construction_equality_immutability_and_slots(self) -> None:
        page_count = CandidateKindPageCount(page_index=2, candidate_count=3)

        self.assertEqual(page_count, CandidateKindPageCount(2, 3))
        with self.assertRaises(FrozenInstanceError):
            page_count.page_index = 3  # type: ignore[misc]
        self.assertFalse(hasattr(page_count, "__dict__"))

    def test_rejects_invalid_integer_fields(self) -> None:
        for page_index in (cast(int, True), cast(int, "0"), -1):
            with self.subTest(page_index=page_index), self.assertRaises(ValueError):
                CandidateKindPageCount(page_index=page_index, candidate_count=1)
        for candidate_count in (cast(int, True), cast(int, "1"), 0, -1):
            with self.subTest(candidate_count=candidate_count), self.assertRaises(ValueError):
                CandidateKindPageCount(page_index=0, candidate_count=candidate_count)


class CandidateKindOccurrenceMeasurementsTests(unittest.TestCase):
    def test_construction_equality_immutability_and_slots(self) -> None:
        occurrence = CandidateKindOccurrenceMeasurements(
            proposed_structural_kind="layout.alpha",
            total_candidate_count=3,
            page_counts=(CandidateKindPageCount(0, 1), CandidateKindPageCount(2, 2)),
        )

        self.assertEqual(occurrence, CandidateKindOccurrenceMeasurements(
            "layout.alpha", 3, (CandidateKindPageCount(0, 1), CandidateKindPageCount(2, 2))
        ))
        with self.assertRaises(FrozenInstanceError):
            occurrence.total_candidate_count = 4  # type: ignore[misc]
        self.assertFalse(hasattr(occurrence, "__dict__"))

    def test_rejects_invalid_shape_order_and_total(self) -> None:
        valid_page_count = CandidateKindPageCount(0, 1)
        for kind in ("", cast(str, 1)):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                CandidateKindOccurrenceMeasurements(kind, 1, (valid_page_count,))
        for total in (cast(int, True), cast(int, "1"), 0, -1):
            with self.subTest(total=total), self.assertRaises(ValueError):
                CandidateKindOccurrenceMeasurements("layout.alpha", total, (valid_page_count,))
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements("layout.alpha", 1, cast(tuple[CandidateKindPageCount, ...], []))
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements("layout.alpha", 1, ())
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements("layout.alpha", 1, (object(),))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements(
                "layout.alpha", 2, (CandidateKindPageCount(1, 1), CandidateKindPageCount(0, 1))
            )
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements(
                "layout.alpha", 2, (CandidateKindPageCount(0, 1), CandidateKindPageCount(0, 1))
            )
        with self.assertRaises(ValueError):
            CandidateKindOccurrenceMeasurements("layout.alpha", 2, (valid_page_count,))


class DocumentCandidateKindOccurrenceMeasurementsTests(unittest.TestCase):
    def test_construction_equality_immutability_slots_and_no_extra_field(self) -> None:
        occurrence = CandidateKindOccurrenceMeasurements(
            "layout.alpha", 1, (CandidateKindPageCount(0, 1),)
        )
        measurements = DocumentCandidateKindOccurrenceMeasurements(
            document_page_count=2,
            included_page_indices=(0,),
            candidate_kind_occurrences=(occurrence,),
        )

        self.assertEqual(measurements, DocumentCandidateKindOccurrenceMeasurements(2, (0,), (occurrence,)))
        with self.assertRaises(FrozenInstanceError):
            measurements.document_page_count = 3  # type: ignore[misc]
        self.assertFalse(hasattr(measurements, "__dict__"))
        self.assertFalse(hasattr(measurements, "included_page_count"))
        self.assertEqual(
            set(DocumentCandidateKindOccurrenceMeasurements.__dataclass_fields__),
            {"document_page_count", "included_page_indices", "candidate_kind_occurrences"},
        )

    def test_rejects_invalid_document_shape_and_occurrences(self) -> None:
        occurrence = CandidateKindOccurrenceMeasurements(
            "layout.alpha", 1, (CandidateKindPageCount(0, 1),)
        )
        for page_count in (cast(int, True), cast(int, "1"), -1):
            with self.subTest(page_count=page_count), self.assertRaises(ValueError):
                DocumentCandidateKindOccurrenceMeasurements(page_count, (), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, cast(tuple[int, ...], [0]), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (cast(int, True),), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (-1,), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (cast(int, "0"),), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(2, (1, 0), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(2, (0, 0), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (1,), ())
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (0,), cast(tuple[CandidateKindOccurrenceMeasurements, ...], []))
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (0,), (object(),))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(2, (1,), (occurrence,))

        beta = CandidateKindOccurrenceMeasurements(
            "layout.beta", 1, (CandidateKindPageCount(0, 1),)
        )
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (0,), (beta, occurrence))
        with self.assertRaises(ValueError):
            DocumentCandidateKindOccurrenceMeasurements(1, (0,), (occurrence, occurrence))


class MeasureDocumentCandidateKindOccurrencesTests(unittest.TestCase):
    def test_empty_document_and_empty_nonzero_document(self) -> None:
        empty = _bound_document(page_count=0)
        nonzero_empty = _bound_document(page_count=4)

        self.assertEqual(
            measure_document_candidate_kind_occurrences(empty),
            DocumentCandidateKindOccurrenceMeasurements(0, (), ()),
        )
        self.assertEqual(
            measure_document_candidate_kind_occurrences(nonzero_empty),
            DocumentCandidateKindOccurrenceMeasurements(4, (), ()),
        )

    def test_included_pages_without_any_candidates_have_no_occurrences(self) -> None:
        bound = _bound_document(page_count=4, page_indices=(0, 2))

        result = measure_document_candidate_kind_occurrences(bound)

        self.assertEqual(result.document_page_count, 4)
        self.assertEqual(result.included_page_indices, (0, 2))
        self.assertEqual(result.candidate_kind_occurrences, ())

    def test_counts_all_and_only_candidates_with_partial_gaps(self) -> None:
        first_kind = "layout.alpha"
        second_kind = "layout.zeta"
        candidates_by_page = {
            1: (
                _candidate("candidate-1", "page-1", second_kind),
                _candidate("candidate-2", "page-1", first_kind),
                _candidate("candidate-3", "page-1", first_kind),
            ),
            3: (
                _candidate("candidate-4", "page-3", first_kind),
                _candidate("candidate-5", "page-3", second_kind),
            ),
        }
        bound = _bound_document(
            page_count=5,
            page_indices=(1, 3),
            candidates_by_page=candidates_by_page,
        )

        result = measure_document_candidate_kind_occurrences(bound)

        self.assertEqual(result.document_page_count, 5)
        self.assertEqual(result.included_page_indices, (1, 3))
        self.assertEqual(
            result.candidate_kind_occurrences,
            (
                CandidateKindOccurrenceMeasurements(
                    first_kind,
                    3,
                    (CandidateKindPageCount(1, 2), CandidateKindPageCount(3, 1)),
                ),
                CandidateKindOccurrenceMeasurements(
                    second_kind,
                    2,
                    (CandidateKindPageCount(1, 1), CandidateKindPageCount(3, 1)),
                ),
            ),
        )
        self.assertEqual(
            sum(
                occurrence.total_candidate_count
                for occurrence in result.candidate_kind_occurrences
            ),
            5,
        )

    def test_includes_pages_without_candidates_and_omits_unobserved_kinds(self) -> None:
        kind = "layout.side_band"
        bound = _bound_document(
            page_count=4,
            page_indices=(0, 2),
            candidates_by_page={2: (_candidate("candidate-1", "page-2", kind),)},
        )

        result = measure_document_candidate_kind_occurrences(bound)

        self.assertEqual(result.included_page_indices, (0, 2))
        self.assertEqual(
            result.candidate_kind_occurrences,
            (CandidateKindOccurrenceMeasurements(kind, 1, (CandidateKindPageCount(2, 1),)),),
        )
        self.assertNotIn("layout.unobserved", tuple(
            occurrence.proposed_structural_kind
            for occurrence in result.candidate_kind_occurrences
        ))

    def test_is_invariant_to_candidate_representation_order_and_does_not_mutate(self) -> None:
        alpha = _candidate("candidate-alpha", "page-0", "layout.alpha")
        beta = _candidate("candidate-beta", "page-0", "layout.beta")
        first = _bound_document(
            page_count=1,
            page_indices=(0,),
            candidates_by_page={0: (beta, alpha)},
        )
        second = _bound_document(
            page_count=1,
            page_indices=(0,),
            candidates_by_page={0: (alpha, beta)},
        )

        first_result = measure_document_candidate_kind_occurrences(first)

        self.assertEqual(first_result, measure_document_candidate_kind_occurrences(second))
        self.assertEqual(first, _bound_document(
            page_count=1,
            page_indices=(0,),
            candidates_by_page={0: (beta, alpha)},
        ))
        self.assertEqual(
            tuple(
                occurrence.proposed_structural_kind
                for occurrence in first_result.candidate_kind_occurrences
            ),
            ("layout.alpha", "layout.beta"),
        )

    def test_rejects_non_bound_document_analysis_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "bound_document_analysis"):
            measure_document_candidate_kind_occurrences(
                cast(BoundDocumentAnalysis, object())
            )


if __name__ == "__main__":
    unittest.main()
