"""Tests for binding co-referenced analyses to one primitive page."""

from __future__ import annotations

import inspect
import unittest
from dataclasses import FrozenInstanceError, fields
from typing import cast

from geometry_model import PageGeometry
from page_analysis_co_reference import (
    CoReferencedPageAnalyses,
    build_co_referenced_page_analyses,
)
from page_analysis_co_reference_binding import (
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _text(primitive_id: str = "text-1") -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=(10.0, 10.0, 20.0, 20.0),
        text="text",
        source_observation_id=f"observation-{primitive_id}",
    )


def _page(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    page_id: str = "page-1",
    schema_version: str = "1.0",
    text_primitives: tuple[TextPrimitive, ...] = (),
) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version=schema_version,
        source_capture_id=source_capture_id,
        source_id=source_id,
        page_id=page_id,
        page_index=4,
        page_geometry=PageGeometry(
            width=100.0,
            height=100.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=text_primitives,
    )


def _analysis(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    page_id: str = "page-1",
    primitive_schema_version: str = "1.0",
    producer_name: str = "producer",
    producer_version: str = "0.1",
    configuration_id: str = "config-v1",
    generation_id: str = "generation-1",
    regions: tuple[LayoutRegion, ...] = (),
    candidates: tuple[RegionCandidate, ...] = (),
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=page_id,
        provenance=PageAnalysisProvenance(
            source_id=source_id,
            source_capture_id=source_capture_id,
            source_page_id=page_id,
            source_primitive_schema_version=primitive_schema_version,
            producer_name=producer_name,
            producer_version=producer_version,
            configuration_id=configuration_id,
        ),
        regions=regions,
        candidates=candidates,
    )


def _candidate(
    *,
    candidate_id: str = "candidate-1",
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 20.0, 20.0),
    primitive_ids: tuple[str, ...] = (),
) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id="page-1",
        bbox=bbox,
        proposed_structural_kind="layout.side_band",
        primitive_ids=primitive_ids,
    )


def _region(
    *,
    region_id: str = "region-1",
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 20.0, 20.0),
    primitive_ids: tuple[str, ...] = (),
) -> LayoutRegion:
    return LayoutRegion(
        region_id=region_id,
        page_id="page-1",
        bbox=bbox,
        structural_kind="layout.frame",
        primitive_ids=primitive_ids,
    )


def _collection(*analyses: PageAnalysis) -> CoReferencedPageAnalyses:
    return build_co_referenced_page_analyses(analyses)


class BoundCoReferencedPageAnalysesTests(unittest.TestCase):
    def test_direct_construction_equality_immutability_slots_and_structure(self) -> None:
        page = _page()
        collection = _collection(_analysis())
        bound = BoundCoReferencedPageAnalyses(page, collection)

        self.assertEqual(bound, BoundCoReferencedPageAnalyses(page, collection))
        self.assertEqual(
            tuple(field.name for field in fields(BoundCoReferencedPageAnalyses)),
            ("primitive_page", "co_referenced_page_analyses"),
        )
        self.assertFalse(hasattr(bound, "__dict__"))
        self.assertFalse(hasattr(bound, "page_index"))
        with self.assertRaises(FrozenInstanceError):
            bound.primitive_page = page  # type: ignore[misc]

    def test_factory_signature_and_valid_singleton_preserve_identity(self) -> None:
        page = _page()
        collection = _collection(_analysis())
        bound = bind_co_referenced_page_analyses(
            page,
            co_referenced_page_analyses=collection,
        )
        signature = inspect.signature(bind_co_referenced_page_analyses)

        self.assertEqual(tuple(signature.parameters), (
            "primitive_page",
            "co_referenced_page_analyses",
        ))
        self.assertEqual(
            signature.parameters["co_referenced_page_analyses"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(bound.primitive_page, page)
        self.assertIs(bound.co_referenced_page_analyses, collection)
        self.assertIs(bound.co_referenced_page_analyses.analyses, collection.analyses)
        self.assertIs(bound.co_referenced_page_analyses.analyses[0], collection.analyses[0])

    def test_rejects_runtime_types_and_does_not_convert_inputs(self) -> None:
        page = _page()
        collection = _collection(_analysis())

        with self.assertRaisesRegex(ValueError, "primitive_page"):
            BoundCoReferencedPageAnalyses(
                cast(NormalizedPrimitivePage, object()),
                collection,
            )
        with self.assertRaisesRegex(ValueError, "co_referenced_page_analyses"):
            BoundCoReferencedPageAnalyses(
                page,
                cast(CoReferencedPageAnalyses, object()),
            )
        for invalid_value in (
            (collection.analyses,),
            [collection],
            {"collection": collection},
            iter((collection,)),
            object(),
        ):
            with self.subTest(invalid_value=type(invalid_value).__name__), self.assertRaisesRegex(
                ValueError,
                "co_referenced_page_analyses",
            ):
                bind_co_referenced_page_analyses(
                    page,
                    co_referenced_page_analyses=cast(
                        CoReferencedPageAnalyses,
                        invalid_value,
                    ),
                )

    def test_rejects_cross_model_provenance_mismatches(self) -> None:
        mismatch_cases = (
            (
                "source_id",
                _page(),
                _collection(_analysis(source_id="other-source")),
            ),
            (
                "source_capture_id",
                _page(),
                _collection(_analysis(source_capture_id="other-capture")),
            ),
            (
                "page_id",
                _page(),
                _collection(_analysis(page_id="other-page")),
            ),
            (
                "source_primitive_schema_version",
                _page(),
                _collection(_analysis(primitive_schema_version="other-schema")),
            ),
        )

        for token, page, collection in mismatch_cases:
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                BoundCoReferencedPageAnalyses(page, collection)

    def test_rejects_missing_primitive_ids_and_incompatible_bboxes(self) -> None:
        page = _page(text_primitives=(_text(),))
        invalid_cases = (
            (
                "candidate missing primitive",
                _collection(_analysis(candidates=(_candidate(primitive_ids=("missing",)),))),
                "candidate.*primitive_id",
            ),
            (
                "region missing primitive",
                _collection(_analysis(regions=(_region(primitive_ids=("missing",)),))),
                "region.*primitive_id",
            ),
            (
                "candidate outside page",
                _collection(_analysis(candidates=(_candidate(bbox=(0.0, 0.0, 120.0, 20.0)),))),
                "candidate.*bbox",
            ),
            (
                "region outside page",
                _collection(_analysis(regions=(_region(bbox=(0.0, 0.0, 120.0, 20.0)),))),
                "region.*bbox",
            ),
        )

        for label, collection, token in invalid_cases:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, token):
                BoundCoReferencedPageAnalyses(page, collection)

    def test_validates_every_current_and_preserves_canonical_order(self) -> None:
        first = _analysis(
            producer_name="alpha",
            candidates=(_candidate(candidate_id="same", primitive_ids=("text-1",)),),
        )
        second = _analysis(
            producer_name="beta",
            regions=(_region(region_id="same", primitive_ids=("text-1",)),),
        )
        collection = _collection(second, first)
        page = _page(text_primitives=(_text(),))
        before = collection.analyses

        bound = BoundCoReferencedPageAnalyses(page, collection)

        self.assertEqual(tuple(analysis.provenance.producer_name for analysis in bound.co_referenced_page_analyses.analyses), ("alpha", "beta"))
        self.assertIs(bound.co_referenced_page_analyses.analyses[0], first)
        self.assertIs(bound.co_referenced_page_analyses.analyses[1], second)
        self.assertIs(bound.co_referenced_page_analyses.analyses, before)
        self.assertIs(bound.co_referenced_page_analyses.analyses[0].candidates[0], first.candidates[0])
        self.assertIs(bound.co_referenced_page_analyses.analyses[1].regions[0], second.regions[0])

    def test_later_invalid_current_causes_the_whole_binding_to_fail(self) -> None:
        valid = _analysis(producer_name="alpha")
        invalid = _analysis(
            producer_name="beta",
            candidates=(_candidate(primitive_ids=("missing",)),),
        )
        collection = _collection(valid, invalid)

        with self.assertRaisesRegex(ValueError, "candidate.*primitive_id"):
            BoundCoReferencedPageAnalyses(_page(), collection)
        with self.assertRaisesRegex(ValueError, "candidate.*primitive_id"):
            bind_co_referenced_page_analyses(
                _page(),
                co_referenced_page_analyses=collection,
            )

    def test_factory_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        first = _analysis(producer_name="alpha")
        second = _analysis(producer_name="beta")
        collection = _collection(second, first)
        page = _page()
        analyses_before = collection.analyses

        first_result = bind_co_referenced_page_analyses(
            page,
            co_referenced_page_analyses=collection,
        )
        second_result = bind_co_referenced_page_analyses(
            page,
            co_referenced_page_analyses=collection,
        )

        self.assertEqual(first_result, second_result)
        self.assertIs(first_result.primitive_page, page)
        self.assertIs(first_result.co_referenced_page_analyses, collection)
        self.assertIs(collection.analyses, analyses_before)
        self.assertEqual(collection.analyses, (first, second))
