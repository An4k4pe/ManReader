"""Tests for attested construction of document-local analysis."""

from __future__ import annotations

import inspect
import unittest
from typing import cast

from document_analysis_from_attestation import build_attested_document_analysis
from document_analysis_model import (
    DOCUMENT_ANALYSIS_SCHEMA_VERSION,
    DocumentAnalysis,
    PageAnalysisReference,
)
from document_source_attestation_model import (
    DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
    DocumentSourceAttestation,
)
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysisProvenance
from verified_file_model import VerifiedFileReference


def _attestation(*, source_id: str = "source-1", page_count: int = 3) -> DocumentSourceAttestation:
    return DocumentSourceAttestation(
        schema_version=DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
        verified_file=VerifiedFileReference(sha256="a" * 64, size_bytes=12),
        source_id=source_id,
        page_count=page_count,
    )


def _reference(
    *,
    page_index: int = 0,
    page_id: str = "page-1",
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
) -> PageAnalysisReference:
    return PageAnalysisReference(
        page_index=page_index,
        page_id=page_id,
        page_analysis_schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        page_analysis_generation_id=f"page-generation-{page_index}",
        provenance=PageAnalysisProvenance(
            source_id=source_id,
            source_capture_id=source_capture_id,
            source_page_id=page_id,
            source_primitive_schema_version="1.0",
            producer_name="page-producer",
            producer_version="0.1",
            configuration_id="page-config-v1",
        ),
    )


def _build(
    attestation: DocumentSourceAttestation,
    *,
    generation_id: str = "document-generation-1",
    producer_name: str = "document-producer",
    producer_version: str = "0.1",
    configuration_id: str = "document-config-v1",
    pages: tuple[PageAnalysisReference, ...] = (),
) -> DocumentAnalysis:
    return build_attested_document_analysis(
        attestation,
        generation_id=generation_id,
        producer_name=producer_name,
        producer_version=producer_version,
        configuration_id=configuration_id,
        pages=pages,
    )


class DocumentAnalysisFromAttestationTests(unittest.TestCase):
    def test_derives_schema_page_count_source_id_and_provenance(self) -> None:
        attestation = _attestation(source_id="attested-source", page_count=3)

        document = _build(attestation)

        self.assertEqual(document.schema_version, DOCUMENT_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(document.page_count, 3)
        self.assertEqual(document.provenance.source_id, "attested-source")
        self.assertEqual(document.provenance.producer_name, "document-producer")
        self.assertEqual(document.provenance.producer_version, "0.1")
        self.assertEqual(document.provenance.configuration_id, "document-config-v1")
        self.assertNotIn("attestation", DocumentAnalysis.__dataclass_fields__)
        self.assertNotIn("verified_file", DocumentAnalysis.__dataclass_fields__)

    def test_signature_has_only_attestation_and_authorized_keyword_arguments(self) -> None:
        signature = inspect.signature(build_attested_document_analysis)

        self.assertEqual(
            tuple(signature.parameters),
            (
                "attestation",
                "generation_id",
                "producer_name",
                "producer_version",
                "configuration_id",
                "pages",
            ),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for name, parameter in signature.parameters.items()
                if name != "attestation"
            )
        )

    def test_accepts_empty_and_partial_page_tuples_without_mutation(self) -> None:
        empty = _build(_attestation(page_count=3))
        partial_pages = (
            _reference(page_index=0),
            _reference(
                page_index=2,
                page_id="page-3",
                source_capture_id="capture-3",
            ),
        )

        partial = _build(_attestation(page_count=3), pages=partial_pages)

        self.assertEqual(empty.pages, ())
        self.assertIs(partial.pages, partial_pages)
        self.assertEqual(partial.pages, partial_pages)

    def test_accepts_zero_page_attestation_only_with_empty_tuple(self) -> None:
        zero_attestation = _attestation(page_count=0)

        self.assertEqual(_build(zero_attestation).page_count, 0)
        with self.assertRaisesRegex(ValueError, "less than page_count"):
            _build(zero_attestation, pages=(_reference(),))

    def test_rejects_wrong_attestation_type_with_stable_message(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "attestation must be a DocumentSourceAttestation",
        ):
            _build(cast(DocumentSourceAttestation, object()))

    def test_propagates_model_validation_for_metadata_and_generation_id(self) -> None:
        attestation = _attestation()

        with self.assertRaisesRegex(ValueError, "generation_id"):
            _build(attestation, generation_id="")
        with self.assertRaisesRegex(ValueError, "producer_name"):
            _build(attestation, producer_name="")

    def test_propagates_model_validation_for_invalid_pages_without_reordering(self) -> None:
        attestation = _attestation(page_count=2)
        second = _reference(
            page_index=1,
            page_id="page-2",
            source_capture_id="capture-2",
        )
        first = _reference()

        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            _build(attestation, pages=(second, first))
        with self.assertRaisesRegex(ValueError, "less than page_count"):
            _build(attestation, pages=(_reference(page_index=2),))
        with self.assertRaisesRegex(ValueError, "source_id"):
            _build(attestation, pages=(_reference(source_id="other-source"),))
        with self.assertRaisesRegex(ValueError, "pages must be a tuple"):
            _build(
                attestation,
                pages=cast(tuple[PageAnalysisReference, ...], [first]),
            )

    def test_is_deterministic_and_does_not_mutate_attestation_or_pages(self) -> None:
        attestation = _attestation()
        pages = (_reference(),)

        self.assertEqual(_build(attestation, pages=pages), _build(attestation, pages=pages))
        self.assertEqual(attestation, _attestation())
        self.assertEqual(pages, (_reference(),))


if __name__ == "__main__":
    unittest.main()
