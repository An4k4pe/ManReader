"""Tests for the pure document-local analysis reference contracts."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import cast

from document_analysis_model import (
    DOCUMENT_ANALYSIS_SCHEMA_VERSION,
    DocumentAnalysis,
    DocumentAnalysisProvenance,
    PageAnalysisReference,
)
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysisProvenance


def _page_provenance(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    source_page_id: str = "page-1",
    source_primitive_schema_version: str = "1.0",
    producer_name: str = "page-producer",
    producer_version: str = "0.1",
    configuration_id: str = "page-config-v1",
) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id=source_id,
        source_capture_id=source_capture_id,
        source_page_id=source_page_id,
        source_primitive_schema_version=source_primitive_schema_version,
        producer_name=producer_name,
        producer_version=producer_version,
        configuration_id=configuration_id,
    )


def _reference(
    *,
    page_index: int = 0,
    page_id: str = "page-1",
    page_analysis_schema_version: str = PAGE_ANALYSIS_SCHEMA_VERSION,
    page_analysis_generation_id: str = "page-generation-1",
    provenance: PageAnalysisProvenance | None = None,
) -> PageAnalysisReference:
    return PageAnalysisReference(
        page_index=page_index,
        page_id=page_id,
        page_analysis_schema_version=page_analysis_schema_version,
        page_analysis_generation_id=page_analysis_generation_id,
        provenance=(
            _page_provenance(source_page_id=page_id)
            if provenance is None
            else provenance
        ),
    )


def _document_provenance(
    *,
    source_id: str = "source-1",
    producer_name: str = "document-producer",
    producer_version: str = "0.1",
    configuration_id: str = "document-config-v1",
) -> DocumentAnalysisProvenance:
    return DocumentAnalysisProvenance(
        source_id=source_id,
        producer_name=producer_name,
        producer_version=producer_version,
        configuration_id=configuration_id,
    )


def _document(
    *,
    schema_version: str = DOCUMENT_ANALYSIS_SCHEMA_VERSION,
    generation_id: str = "document-generation-1",
    page_count: int = 1,
    provenance: DocumentAnalysisProvenance | object | None = None,
    pages: tuple[PageAnalysisReference, ...] | object = (),
) -> DocumentAnalysis:
    return DocumentAnalysis(
        schema_version=schema_version,
        generation_id=generation_id,
        page_count=page_count,
        provenance=_document_provenance() if provenance is None else provenance,  # type: ignore[arg-type]
        pages=pages,  # type: ignore[arg-type]
    )


class DocumentAnalysisProvenanceTests(unittest.TestCase):
    def test_construction_equality_immutability_and_slots(self) -> None:
        provenance = _document_provenance()

        self.assertEqual(provenance, _document_provenance())
        with self.assertRaises(FrozenInstanceError):
            provenance.source_id = "other"  # type: ignore[misc]
        self.assertFalse(hasattr(provenance, "__dict__"))

    def test_empty_and_runtime_invalid_fields_are_rejected(self) -> None:
        for field_name in (
            "source_id",
            "producer_name",
            "producer_version",
            "configuration_id",
        ):
            with self.subTest(field_name=field_name), self.assertRaises(ValueError):
                _document_provenance(**{field_name: ""})
            with self.subTest(field_name=f"{field_name}-type"), self.assertRaises(ValueError):
                _document_provenance(**{field_name: cast(str, 123)})


class PageAnalysisReferenceTests(unittest.TestCase):
    def test_construction_equality_immutability_and_slots(self) -> None:
        reference = _reference()

        self.assertEqual(reference, _reference())
        with self.assertRaises(FrozenInstanceError):
            reference.page_id = "other"  # type: ignore[misc]
        self.assertFalse(hasattr(reference, "__dict__"))
        self.assertEqual(reference.page_index, 0)

    def test_schema_version_is_fixed_to_page_analysis_schema(self) -> None:
        self.assertEqual(_reference().page_analysis_schema_version, "1.2")
        with self.assertRaises(ValueError):
            _reference(page_analysis_schema_version="1.3")

    def test_invalid_page_index_and_generation_id_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _reference(page_index=-1)
        with self.assertRaises(ValueError):
            _reference(page_index=cast(int, True))
        with self.assertRaises(ValueError):
            _reference(page_index=cast(int, "0"))
        with self.assertRaises(ValueError):
            _reference(page_analysis_generation_id="")
        with self.assertRaises(ValueError):
            _reference(page_id="")
        with self.assertRaises(ValueError):
            _reference(page_id=cast(str, 123))

    def test_page_provenance_type_and_page_id_must_match(self) -> None:
        with self.assertRaises(ValueError):
            _reference(provenance=cast(PageAnalysisProvenance, object()))
        with self.assertRaises(ValueError):
            _reference(provenance=_page_provenance(source_page_id="other-page"))


class DocumentAnalysisTests(unittest.TestCase):
    def test_valid_document_equality_immutability_and_slots(self) -> None:
        document = _document(pages=(_reference(),))

        self.assertEqual(document, _document(pages=(_reference(),)))
        with self.assertRaises(FrozenInstanceError):
            document.generation_id = "other"  # type: ignore[misc]
        self.assertFalse(hasattr(document, "__dict__"))
        self.assertFalse(hasattr(document, "document_id"))

    def test_document_schema_constant_and_empty_documents_are_valid(self) -> None:
        self.assertEqual(DOCUMENT_ANALYSIS_SCHEMA_VERSION, "1.0")
        self.assertEqual(_document(page_count=0).pages, ())
        self.assertEqual(_document(page_count=4).pages, ())

    def test_partial_pages_with_initial_internal_and_final_gaps_are_valid(self) -> None:
        references = (
            _reference(
                page_index=1,
                page_id="page-2",
                provenance=_page_provenance(
                    source_capture_id="capture-2",
                    source_page_id="page-2",
                ),
            ),
            _reference(
                page_index=3,
                page_id="page-4",
                provenance=_page_provenance(
                    source_capture_id="capture-4",
                    source_page_id="page-4",
                ),
            ),
        )

        document = _document(page_count=5, pages=references)

        self.assertEqual(document.pages, references)

    def test_document_general_runtime_errors_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _document(schema_version="2.0")
        with self.assertRaises(ValueError):
            _document(generation_id="")
        with self.assertRaises(ValueError):
            _document(page_count=-1)
        with self.assertRaises(ValueError):
            _document(page_count=cast(int, True))
        with self.assertRaises(ValueError):
            _document(page_count=cast(int, "1"))
        with self.assertRaises(ValueError):
            _document(provenance=object())
        with self.assertRaises(ValueError):
            _document(pages=cast(tuple[PageAnalysisReference, ...], []))
        with self.assertRaises(ValueError):
            _document(pages=cast(tuple[PageAnalysisReference, ...], (object(),)))

    def test_page_count_zero_rejects_references_and_out_of_range_indices(self) -> None:
        with self.assertRaises(ValueError):
            _document(page_count=0, pages=(_reference(),))
        with self.assertRaises(ValueError):
            _document(page_count=1, pages=(_reference(page_index=1),))

    def test_pages_must_be_strictly_ordered_and_unique(self) -> None:
        second = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
            ),
        )
        first = _reference()
        with self.assertRaises(ValueError):
            _document(page_count=2, pages=(second, first))
        with self.assertRaises(ValueError):
            _document(page_count=2, pages=(first, first))

    def test_page_id_and_capture_id_must_be_unique(self) -> None:
        first = _reference()
        duplicate_page_id = _reference(
            page_index=1,
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-1",
            ),
        )
        duplicate_capture_id = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-1",
                source_page_id="page-2",
            ),
        )
        with self.assertRaises(ValueError):
            _document(page_count=2, pages=(first, duplicate_page_id))
        with self.assertRaises(ValueError):
            _document(page_count=2, pages=(first, duplicate_capture_id))

    def test_source_and_page_analysis_provenance_must_be_coherent(self) -> None:
        reference = _reference(
            provenance=_page_provenance(source_id="other-source")
        )
        with self.assertRaises(ValueError):
            _document(pages=(reference,))

        first = _reference()
        different_producer_name = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
                producer_name="other-producer",
            ),
        )
        different_producer_version = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
                producer_version="0.2",
            ),
        )
        different_configuration = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
                configuration_id="page-config-v2",
            ),
        )
        different_primitive_schema = _reference(
            page_index=1,
            page_id="page-2",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
                source_primitive_schema_version="2.0",
            ),
        )
        for inconsistent_reference in (
            different_producer_name,
            different_producer_version,
            different_configuration,
            different_primitive_schema,
        ):
            with self.subTest(reference=inconsistent_reference), self.assertRaises(ValueError):
                _document(page_count=2, pages=(first, inconsistent_reference))

    def test_capture_and_page_generation_ids_may_differ_or_match(self) -> None:
        first = _reference(page_analysis_generation_id="same-generation")
        second = _reference(
            page_index=1,
            page_id="page-2",
            page_analysis_generation_id="same-generation",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
            ),
        )
        self.assertEqual(_document(page_count=2, pages=(first, second)).pages, (first, second))

        different_generation = _reference(
            page_index=1,
            page_id="page-2",
            page_analysis_generation_id="different-generation",
            provenance=_page_provenance(
                source_capture_id="capture-2",
                source_page_id="page-2",
            ),
        )
        self.assertEqual(
            _document(page_count=2, pages=(first, different_generation)).pages,
            (first, different_generation),
        )

    def test_document_producer_may_differ_from_page_analysis_producer(self) -> None:
        document = _document(
            provenance=_document_provenance(producer_name="document-only-producer"),
            pages=(_reference(),),
        )

        self.assertEqual(document.provenance.producer_name, "document-only-producer")

    def test_no_resolution_semantic_or_scoring_fields_are_public(self) -> None:
        forbidden_terms = (
            "resolution",
            "semantic",
            "score",
            "confidence",
            "ranking",
            "ownership",
            "coverage",
        )
        public_fields = {
            *DocumentAnalysisProvenance.__dataclass_fields__,
            *PageAnalysisReference.__dataclass_fields__,
            *DocumentAnalysis.__dataclass_fields__,
        }
        for forbidden_term in forbidden_terms:
            self.assertFalse(any(forbidden_term in field for field in public_fields))


if __name__ == "__main__":
    unittest.main()
