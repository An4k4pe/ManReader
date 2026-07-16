"""Tests for validated construction of document-local page analysis references."""

from __future__ import annotations

import unittest
from typing import cast

from document_analysis_reference import build_validated_page_analysis_reference
from geometry_model import PageGeometry
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _primitive_page(
    *,
    page_id: str = "page-1",
    page_index: int = 7,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    text_primitives: tuple[TextPrimitive, ...] = (),
) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id=source_capture_id,
        source_id=source_id,
        page_id=page_id,
        page_index=page_index,
        page_geometry=PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=text_primitives,
    )


def _provenance(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    source_page_id: str = "page-1",
    source_primitive_schema_version: str = "1.0",
) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id=source_id,
        source_capture_id=source_capture_id,
        source_page_id=source_page_id,
        source_primitive_schema_version=source_primitive_schema_version,
        producer_name="page-producer",
        producer_version="0.1",
        configuration_id="page-config-v1",
    )


def _analysis(
    *,
    page_id: str = "page-1",
    generation_id: str = "analysis-generation-1",
    provenance: PageAnalysisProvenance | None = None,
    candidates: tuple[RegionCandidate, ...] = (),
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=page_id,
        provenance=_provenance() if provenance is None else provenance,
        candidates=candidates,
    )


class DocumentAnalysisReferenceTests(unittest.TestCase):
    def test_builds_reference_from_non_zero_normalized_page_index(self) -> None:
        primitive_page = _primitive_page(page_index=7)
        analysis = _analysis()

        reference = build_validated_page_analysis_reference(
            primitive_page,
            analysis=analysis,
        )

        self.assertEqual(reference.page_index, 7)
        self.assertEqual(reference.page_id, analysis.page_id)
        self.assertEqual(reference.page_analysis_schema_version, analysis.schema_version)
        self.assertEqual(reference.page_analysis_generation_id, analysis.generation_id)
        self.assertIs(reference.provenance, analysis.provenance)

    def test_is_deterministic_and_does_not_modify_inputs(self) -> None:
        primitive_page = _primitive_page()
        analysis = _analysis()
        expected_page = _primitive_page()
        expected_analysis = _analysis()

        self.assertEqual(
            build_validated_page_analysis_reference(primitive_page, analysis=analysis),
            build_validated_page_analysis_reference(primitive_page, analysis=analysis),
        )
        self.assertEqual(primitive_page, expected_page)
        self.assertEqual(analysis, expected_analysis)

    def test_propagates_incoherent_page_id_rejection(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "analysis page_id must match primitive_page page_id"
        ):
            build_validated_page_analysis_reference(
                _primitive_page(page_id="page-2"),
                analysis=_analysis(),
            )

    def test_propagates_incoherent_provenance_rejection(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "provenance source_id must match primitive_page source_id"
        ):
            build_validated_page_analysis_reference(
                _primitive_page(),
                analysis=_analysis(provenance=_provenance(source_id="other-source")),
            )

    def test_propagates_deep_missing_candidate_primitive_rejection(self) -> None:
        candidate = RegionCandidate(
            candidate_id="candidate-1",
            page_id="page-1",
            bbox=(0.0, 0.0, 20.0, 20.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("missing-primitive",),
        )

        with self.assertRaisesRegex(ValueError, "candidate-1.*missing-primitive"):
            build_validated_page_analysis_reference(
                _primitive_page(),
                analysis=_analysis(candidates=(candidate,)),
            )

    def test_runtime_invalid_inputs_are_rejected_by_existing_validator(self) -> None:
        with self.assertRaisesRegex(ValueError, "analysis must be a PageAnalysis"):
            build_validated_page_analysis_reference(
                _primitive_page(),
                analysis=cast(PageAnalysis, object()),
            )
        with self.assertRaisesRegex(ValueError, "primitive_page must be a NormalizedPrimitivePage"):
            build_validated_page_analysis_reference(
                cast(NormalizedPrimitivePage, object()),
                analysis=_analysis(),
            )


if __name__ == "__main__":
    unittest.main()
