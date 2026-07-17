"""Tests for pure positional document analysis binding."""

from __future__ import annotations

import inspect
import unittest
from dataclasses import FrozenInstanceError
from typing import cast

from document_analysis_binding import (
    BoundDocumentAnalysis,
    BoundPageAnalysis,
    bind_document_analysis,
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
)


def _page_provenance(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-0",
    source_page_id: str = "page-0",
    producer_name: str = "page-producer",
) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id=source_id,
        source_capture_id=source_capture_id,
        source_page_id=source_page_id,
        source_primitive_schema_version="1.0",
        producer_name=producer_name,
        producer_version="0.1",
        configuration_id="page-config-v1",
    )


def _reference(
    *,
    page_index: int = 0,
    page_id: str = "page-0",
    generation_id: str | None = None,
    provenance: PageAnalysisProvenance | None = None,
) -> PageAnalysisReference:
    return PageAnalysisReference(
        page_index=page_index,
        page_id=page_id,
        page_analysis_schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        page_analysis_generation_id=(
            f"analysis-generation-{page_index}"
            if generation_id is None
            else generation_id
        ),
        provenance=(
            _page_provenance(
                source_capture_id=f"capture-{page_index}",
                source_page_id=page_id,
            )
            if provenance is None
            else provenance
        ),
    )


def _analysis(
    *,
    page_id: str = "page-0",
    generation_id: str = "analysis-generation-0",
    provenance: PageAnalysisProvenance | None = None,
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=page_id,
        provenance=(
            _page_provenance(source_page_id=page_id) if provenance is None else provenance
        ),
    )


def _document(
    *,
    page_count: int = 1,
    pages: tuple[PageAnalysisReference, ...] = (),
) -> DocumentAnalysis:
    return DocumentAnalysis(
        schema_version=DOCUMENT_ANALYSIS_SCHEMA_VERSION,
        generation_id="document-generation-1",
        page_count=page_count,
        provenance=DocumentAnalysisProvenance(
            source_id="source-1",
            producer_name="document-producer",
            producer_version="0.1",
            configuration_id="document-config-v1",
        ),
        pages=pages,
    )


def _matching_pair(
    *,
    page_index: int = 0,
    page_id: str | None = None,
) -> tuple[PageAnalysisReference, PageAnalysis]:
    resolved_page_id = f"page-{page_index}" if page_id is None else page_id
    provenance = _page_provenance(
        source_capture_id=f"capture-{page_index}",
        source_page_id=resolved_page_id,
    )
    generation_id = f"analysis-generation-{page_index}"
    return (
        _reference(
            page_index=page_index,
            page_id=resolved_page_id,
            generation_id=generation_id,
            provenance=provenance,
        ),
        _analysis(
            page_id=resolved_page_id,
            generation_id=generation_id,
            provenance=provenance,
        ),
    )


class BoundPageAnalysisTests(unittest.TestCase):
    def test_valid_construction_equality_immutability_and_slots(self) -> None:
        reference, analysis = _matching_pair()
        bound = BoundPageAnalysis(reference=reference, analysis=analysis)

        self.assertEqual(bound, BoundPageAnalysis(reference=reference, analysis=analysis))
        with self.assertRaises(FrozenInstanceError):
            bound.reference = reference  # type: ignore[misc]
        self.assertFalse(hasattr(bound, "__dict__"))

    def test_rejects_runtime_types(self) -> None:
        reference, analysis = _matching_pair()

        with self.assertRaisesRegex(ValueError, "reference"):
            BoundPageAnalysis(
                reference=cast(PageAnalysisReference, object()), analysis=analysis
            )
        with self.assertRaisesRegex(ValueError, "analysis"):
            BoundPageAnalysis(
                reference=reference, analysis=cast(PageAnalysis, object())
            )

    def test_rejects_each_logical_reference_analysis_mismatch(self) -> None:
        reference, analysis = _matching_pair()

        with self.assertRaisesRegex(ValueError, "page_id"):
            BoundPageAnalysis(
                reference=reference,
                analysis=_analysis(
                    page_id="other-page",
                    generation_id=analysis.generation_id,
                    provenance=_page_provenance(source_page_id="other-page"),
                ),
            )

        altered_schema = _analysis(
            page_id=analysis.page_id,
            generation_id=analysis.generation_id,
            provenance=analysis.provenance,
        )
        object.__setattr__(altered_schema, "schema_version", "1.3")
        with self.assertRaisesRegex(ValueError, "schema_version"):
            BoundPageAnalysis(reference=reference, analysis=altered_schema)

        with self.assertRaisesRegex(ValueError, "generation_id"):
            BoundPageAnalysis(
                reference=reference,
                analysis=_analysis(
                    page_id=analysis.page_id,
                    generation_id="other-generation",
                    provenance=analysis.provenance,
                ),
            )

        with self.assertRaisesRegex(ValueError, "provenance"):
            BoundPageAnalysis(
                reference=reference,
                analysis=_analysis(
                    page_id=analysis.page_id,
                    generation_id=analysis.generation_id,
                    provenance=_page_provenance(
                        source_capture_id="other-capture",
                        source_page_id=analysis.page_id,
                    ),
                ),
            )


class BoundDocumentAnalysisTests(unittest.TestCase):
    def test_accepts_zero_one_and_multiple_pages(self) -> None:
        empty_document = _document(page_count=0)
        self.assertEqual(
            BoundDocumentAnalysis(document_analysis=empty_document, pages=()).pages,
            (),
        )

        first_reference, first_analysis = _matching_pair(page_index=0)
        one_document = _document(page_count=1, pages=(first_reference,))
        one_bound = BoundDocumentAnalysis(
            document_analysis=one_document,
            pages=(BoundPageAnalysis(first_reference, first_analysis),),
        )
        self.assertEqual(one_bound.pages[0].analysis, first_analysis)

        second_reference, second_analysis = _matching_pair(page_index=2)
        multi_document = _document(
            page_count=3,
            pages=(first_reference, second_reference),
        )
        multi_bound = BoundDocumentAnalysis(
            document_analysis=multi_document,
            pages=(
                BoundPageAnalysis(first_reference, first_analysis),
                BoundPageAnalysis(second_reference, second_analysis),
            ),
        )
        self.assertEqual(len(multi_bound.pages), 2)

    def test_accepts_logically_equal_but_distinct_reference(self) -> None:
        reference, analysis = _matching_pair()
        document = _document(pages=(reference,))
        reconstructed_reference = _reference(
            page_index=reference.page_index,
            page_id=reference.page_id,
            generation_id=reference.page_analysis_generation_id,
            provenance=reference.provenance,
        )

        bound = BoundDocumentAnalysis(
            document_analysis=document,
            pages=(BoundPageAnalysis(reconstructed_reference, analysis),),
        )

        self.assertIsNot(reconstructed_reference, reference)
        self.assertEqual(bound.pages[0].reference, document.pages[0])

    def test_rejects_direct_invalid_document_pages_and_references(self) -> None:
        reference, analysis = _matching_pair()
        document = _document(pages=(reference,))
        bound_page = BoundPageAnalysis(reference, analysis)

        with self.assertRaisesRegex(ValueError, "document_analysis"):
            BoundDocumentAnalysis(
                document_analysis=cast(DocumentAnalysis, object()), pages=()
            )
        with self.assertRaisesRegex(ValueError, "pages"):
            BoundDocumentAnalysis(
                document_analysis=document,
                pages=cast(tuple[BoundPageAnalysis, ...], [bound_page]),
            )
        with self.assertRaisesRegex(ValueError, "length"):
            BoundDocumentAnalysis(document_analysis=document, pages=())
        with self.assertRaisesRegex(ValueError, "length"):
            BoundDocumentAnalysis(
                document_analysis=_document(page_count=2, pages=()),
                pages=(bound_page,),
            )
        with self.assertRaisesRegex(ValueError, r"pages\[0\]"):
            BoundDocumentAnalysis(
                document_analysis=document,
                pages=cast(tuple[BoundPageAnalysis, ...], (object(),)),
            )

        other_reference, other_analysis = _matching_pair(page_index=1)
        other_document = _document(page_count=2, pages=(reference, other_reference))
        with self.assertRaisesRegex(ValueError, "reference"):
            BoundDocumentAnalysis(
                document_analysis=other_document,
                pages=(
                    BoundPageAnalysis(other_reference, other_analysis),
                    BoundPageAnalysis(reference, analysis),
                ),
            )

    def test_equality_immutability_slots_determinism_and_no_mutation(self) -> None:
        reference, analysis = _matching_pair()
        document = _document(pages=(reference,))
        pages = (BoundPageAnalysis(reference, analysis),)
        bound = BoundDocumentAnalysis(document_analysis=document, pages=pages)

        self.assertEqual(bound, BoundDocumentAnalysis(document_analysis=document, pages=pages))
        with self.assertRaises(FrozenInstanceError):
            bound.pages = ()  # type: ignore[misc]
        self.assertFalse(hasattr(bound, "__dict__"))
        self.assertEqual(document, _document(pages=(reference,)))
        self.assertEqual(pages, (BoundPageAnalysis(reference, analysis),))


class BindDocumentAnalysisTests(unittest.TestCase):
    def test_binds_by_position_and_preserves_identity(self) -> None:
        first_reference, first_analysis = _matching_pair(page_index=0)
        second_reference, second_analysis = _matching_pair(page_index=2)
        document = _document(
            page_count=3,
            pages=(first_reference, second_reference),
        )
        analyses = (first_analysis, second_analysis)

        result = bind_document_analysis(document, analyses=analyses)

        self.assertIs(result.document_analysis, document)
        self.assertIs(result.pages[0].reference, document.pages[0])
        self.assertIs(result.pages[1].reference, document.pages[1])
        self.assertIs(result.pages[0].analysis, analyses[0])
        self.assertIs(result.pages[1].analysis, analyses[1])
        self.assertEqual(result, bind_document_analysis(document, analyses=analyses))

    def test_accepts_empty_pages_and_partial_document_gaps(self) -> None:
        empty_document = _document(page_count=4)
        self.assertEqual(bind_document_analysis(empty_document, analyses=()).pages, ())
        _, unexpected_analysis = _matching_pair()
        with self.assertRaisesRegex(ValueError, "length"):
            bind_document_analysis(empty_document, analyses=(unexpected_analysis,))

        first_reference, first_analysis = _matching_pair(page_index=1)
        second_reference, second_analysis = _matching_pair(page_index=3)
        partial_document = _document(
            page_count=5,
            pages=(first_reference, second_reference),
        )
        result = bind_document_analysis(
            partial_document,
            analyses=(first_analysis, second_analysis),
        )
        self.assertEqual(
            tuple(bound.reference.page_index for bound in result.pages), (1, 3)
        )

    def test_rejects_incomplete_wrong_type_and_reordered_inputs(self) -> None:
        first_reference, first_analysis = _matching_pair(page_index=0)
        second_reference, second_analysis = _matching_pair(page_index=1)
        document = _document(
            page_count=2,
            pages=(first_reference, second_reference),
        )

        with self.assertRaisesRegex(ValueError, "length"):
            bind_document_analysis(document, analyses=(first_analysis,))
        with self.assertRaisesRegex(ValueError, "length"):
            bind_document_analysis(
                document,
                analyses=(first_analysis, second_analysis, second_analysis),
            )
        with self.assertRaisesRegex(ValueError, "analyses"):
            bind_document_analysis(
                document,
                analyses=cast(tuple[PageAnalysis, ...], [first_analysis, second_analysis]),
            )
        with self.assertRaisesRegex(ValueError, r"analyses\[1\]"):
            bind_document_analysis(
                document,
                analyses=(first_analysis, cast(PageAnalysis, object())),
            )
        with self.assertRaisesRegex(ValueError, "document_analysis"):
            bind_document_analysis(cast(DocumentAnalysis, object()), analyses=())
        with self.assertRaisesRegex(ValueError, "page_id"):
            bind_document_analysis(
                document,
                analyses=(second_analysis, first_analysis),
            )

    def test_signature_is_exact_and_has_no_extra_parameters(self) -> None:
        signature = inspect.signature(bind_document_analysis)

        self.assertEqual(tuple(signature.parameters), ("document_analysis", "analyses"))
        self.assertIs(
            signature.parameters["analyses"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )


if __name__ == "__main__":
    unittest.main()
