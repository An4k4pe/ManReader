"""Tests for pure collections of co-referenced page analyses."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, fields
from typing import cast

from page_analysis_co_reference import (
    CoReferencedPageAnalyses,
    build_co_referenced_page_analyses,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
    RegionRelation,
)


def _provenance(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    page_id: str = "page-1",
    primitive_schema_version: str = "1.0",
    producer_name: str = "producer",
    producer_version: str = "1",
    configuration_id: str = "config",
) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id=source_id,
        source_capture_id=source_capture_id,
        source_page_id=page_id,
        source_primitive_schema_version=primitive_schema_version,
        producer_name=producer_name,
        producer_version=producer_version,
        configuration_id=configuration_id,
    )


def _analysis(
    *,
    source_id: str = "source-1",
    source_capture_id: str = "capture-1",
    page_id: str = "page-1",
    primitive_schema_version: str = "1.0",
    producer_name: str = "producer",
    producer_version: str = "1",
    configuration_id: str = "config",
    generation_id: str = "generation",
    regions: tuple[LayoutRegion, ...] = (),
    relations: tuple[RegionRelation, ...] = (),
    candidates: tuple[RegionCandidate, ...] = (),
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=page_id,
        provenance=_provenance(
            source_id=source_id,
            source_capture_id=source_capture_id,
            page_id=page_id,
            primitive_schema_version=primitive_schema_version,
            producer_name=producer_name,
            producer_version=producer_version,
            configuration_id=configuration_id,
        ),
        regions=regions,
        relations=relations,
        candidates=candidates,
    )


def _container(*analyses: PageAnalysis, **overrides: object) -> CoReferencedPageAnalyses:
    first = analyses[0]
    provenance = first.provenance
    values: dict[str, object] = {
        "source_id": provenance.source_id,
        "source_capture_id": provenance.source_capture_id,
        "page_id": first.page_id,
        "source_primitive_schema_version": provenance.source_primitive_schema_version,
        "analyses": analyses,
    }
    values.update(overrides)
    return CoReferencedPageAnalyses(**values)  # type: ignore[arg-type]


class CoReferencedPageAnalysesConstructionTests(unittest.TestCase):
    def test_valid_direct_construction_with_single_analysis(self) -> None:
        analysis = _analysis()

        value = _container(analysis)

        self.assertEqual(value.source_id, analysis.provenance.source_id)
        self.assertEqual(
            value.source_capture_id,
            analysis.provenance.source_capture_id,
        )
        self.assertEqual(value.page_id, analysis.page_id)
        self.assertEqual(
            value.source_primitive_schema_version,
            analysis.provenance.source_primitive_schema_version,
        )
        self.assertEqual(value.analyses, (analysis,))
        self.assertIs(value.analyses[0], analysis)

    def test_valid_direct_construction_structure_and_value_semantics(self) -> None:
        first = _analysis(producer_name="alpha")
        second = _analysis(producer_name="beta")
        value = _container(first, second)

        self.assertEqual(value, _container(first, second))
        self.assertEqual(
            tuple(field.name for field in fields(CoReferencedPageAnalyses)),
            (
                "source_id",
                "source_capture_id",
                "page_id",
                "source_primitive_schema_version",
                "analyses",
            ),
        )
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            value.page_id = "other"  # type: ignore[misc]
        for forbidden_name in (
            "page_index",
            "analysis_count",
            "complete",
            "lookup",
            "current_identity",
        ):
            self.assertFalse(hasattr(value, forbidden_name))

    def test_rejects_invalid_explicit_fields_and_analysis_shape(self) -> None:
        analysis = _analysis()
        for field_name in (
            "source_id",
            "source_capture_id",
            "page_id",
            "source_primitive_schema_version",
        ):
            with self.subTest(field_name=field_name, value=""), self.assertRaises(ValueError):
                _container(analysis, **{field_name: ""})
            with self.subTest(field_name=field_name, value=object()), self.assertRaises(ValueError):
                _container(analysis, **{field_name: cast(str, object())})

        with self.assertRaisesRegex(ValueError, "tuple"):
            CoReferencedPageAnalyses(
                "source-1", "capture-1", "page-1", "1.0", cast(tuple[PageAnalysis, ...], [])
            )
        with self.assertRaises(ValueError):
            CoReferencedPageAnalyses("source-1", "capture-1", "page-1", "1.0", ())
        with self.assertRaisesRegex(ValueError, "analyses\\[0\\]"):
            CoReferencedPageAnalyses(
                "source-1",
                "capture-1",
                "page-1",
                "1.0",
                (cast(PageAnalysis, object()),),
            )

    def test_rejects_each_co_reference_and_schema_mismatch(self) -> None:
        first = _analysis(producer_name="alpha")
        mismatch_cases = (
            ("source_id", _analysis(source_id="other", producer_name="beta")),
            (
                "source_capture_id",
                _analysis(source_capture_id="other", producer_name="beta"),
            ),
            ("page_id", _analysis(page_id="other-page", producer_name="beta")),
            (
                "source_primitive_schema_version",
                _analysis(primitive_schema_version="2.0", producer_name="beta"),
            ),
        )
        for token, second in mismatch_cases:
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                _container(first, second)

        different_schema = _analysis(producer_name="beta")
        object.__setattr__(different_schema, "schema_version", "1.3")
        with self.assertRaisesRegex(ValueError, "schema_version"):
            _container(first, different_schema)

    def test_rejects_explicit_field_mismatches(self) -> None:
        analysis = _analysis()
        mismatches = {
            "source_id": "other-source",
            "source_capture_id": "other-capture",
            "page_id": "other-page",
            "source_primitive_schema_version": "2.0",
        }
        for field_name, value in mismatches.items():
            with (
                self.subTest(field_name=field_name),
                self.assertRaisesRegex(ValueError, field_name),
            ):
                _container(analysis, **{field_name: value})


class CoReferencedPageAnalysesCurrentTests(unittest.TestCase):
    def test_accepts_distinct_current_key_components_and_same_kind(self) -> None:
        shared_candidate = RegionCandidate(
            candidate_id="candidate-1",
            page_id="page-1",
            bbox=(0.0, 0.0, 10.0, 10.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("primitive-1",),
        )
        analyses = (
            _analysis(
                producer_name="singleton", generation_id="same", candidates=(shared_candidate,)
            ),
            _analysis(
                producer_name="local-fragment", generation_id="same", candidates=(shared_candidate,)
            ),
            _analysis(
                producer_name="same", producer_version="1", configuration_id="a", generation_id="a"
            ),
            _analysis(
                producer_name="same", producer_version="1", configuration_id="b", generation_id="a"
            ),
            _analysis(producer_name="versioned", producer_version="1", generation_id="a"),
            _analysis(producer_name="versioned", producer_version="2", generation_id="a"),
            _analysis(producer_name="generation", generation_id="a"),
            _analysis(producer_name="generation", generation_id="b"),
        )

        value = build_co_referenced_page_analyses(analyses)
        self.assertEqual(len(value.analyses), len(analyses))
        names = tuple(analysis.provenance.producer_name for analysis in value.analyses)
        self.assertEqual(names[:2], ("generation", "generation"))
        candidate_analyses = tuple(analysis for analysis in value.analyses if analysis.candidates)
        self.assertEqual(
            tuple(analysis.candidates[0] for analysis in candidate_analyses),
            (shared_candidate, shared_candidate),
        )

    def test_rejects_duplicate_current_keys_without_deduplication(self) -> None:
        analysis = _analysis()
        equal_distinct = _analysis()
        different_payload = _analysis(
            candidates=(
                RegionCandidate(
                    "candidate-2", "page-1", (0.0, 0.0, 10.0, 10.0), "layout.side_band"
                ),
            ),
        )
        for pair in (
            (analysis, analysis),
            (analysis, equal_distinct),
            (analysis, different_payload),
        ):
            with self.subTest(pair=pair), self.assertRaisesRegex(ValueError, "analysis stream key"):
                build_co_referenced_page_analyses(pair)

    def test_direct_order_uses_exact_lexicographic_strings(self) -> None:
        version_ten = _analysis(producer_version="10", generation_id="a")
        version_two = _analysis(producer_version="2", generation_id="a")
        ordered = _container(version_ten, version_two)
        self.assertEqual(ordered.analyses, (version_ten, version_two))
        with self.assertRaisesRegex(ValueError, "analysis stream key"):
            _container(version_two, version_ten)

    def test_factory_canonicalizes_permutations_and_preserves_identity(self) -> None:
        alpha = _analysis(producer_name="alpha", generation_id="z")
        beta = _analysis(producer_name="beta", generation_id="a")
        first = build_co_referenced_page_analyses((beta, alpha))
        second = build_co_referenced_page_analyses((alpha, beta))

        self.assertEqual(first, second)
        self.assertIs(first.analyses[0], alpha)
        self.assertIs(first.analyses[1], beta)
        self.assertEqual((beta, alpha), (beta, alpha))


class CoReferencedPageAnalysesContentIsolationTests(unittest.TestCase):
    def test_allows_locally_colliding_structural_content_without_copying(self) -> None:
        def structured_analysis(producer_name: str) -> PageAnalysis:
            regions = (
                LayoutRegion(
                    "region-1", "page-1", (0.0, 0.0, 10.0, 10.0), "layout.frame", ("primitive-1",)
                ),
                LayoutRegion(
                    "region-2", "page-1", (10.0, 0.0, 20.0, 10.0), "layout.frame", ("primitive-1",)
                ),
            )
            relations = (RegionRelation("relation-1", "layout.precedes", "region-1", "region-2"),)
            candidates = (
                RegionCandidate(
                    "candidate-1",
                    "page-1",
                    (0.0, 0.0, 10.0, 10.0),
                    "layout.side_band",
                    ("primitive-1",),
                ),
            )
            return _analysis(
                producer_name=producer_name,
                regions=regions,
                relations=relations,
                candidates=candidates,
            )

        alpha = structured_analysis("alpha")
        beta = structured_analysis("beta")
        result = build_co_referenced_page_analyses((beta, alpha))

        self.assertIs(result.analyses[0], alpha)
        self.assertIs(result.analyses[1], beta)
        self.assertIsNot(alpha.regions[0], beta.regions[0])
        self.assertEqual(alpha.regions[0].region_id, beta.regions[0].region_id)
        self.assertEqual(alpha.relations[0].relation_id, beta.relations[0].relation_id)
        self.assertEqual(alpha.candidates[0].candidate_id, beta.candidates[0].candidate_id)
        self.assertEqual(alpha.candidates[0].bbox, beta.candidates[0].bbox)
        self.assertIs(result.analyses[0].candidates[0], alpha.candidates[0])


class CoReferencedPageAnalysesFactoryTests(unittest.TestCase):
    def test_factory_rejects_each_co_reference_and_schema_mismatch(self) -> None:
        first = _analysis(producer_name="alpha")
        mismatch_cases = (
            ("source_id", _analysis(source_id="other", producer_name="beta")),
            (
                "source_capture_id",
                _analysis(source_capture_id="other", producer_name="beta"),
            ),
            ("page_id", _analysis(page_id="other-page", producer_name="beta")),
            (
                "source_primitive_schema_version",
                _analysis(
                    primitive_schema_version="2.0",
                    producer_name="beta",
                ),
            ),
        )

        for token, second in mismatch_cases:
            with self.subTest(token=token), self.assertRaisesRegex(
                ValueError,
                token,
            ):
                build_co_referenced_page_analyses((first, second))

        different_schema = _analysis(producer_name="beta")
        object.__setattr__(different_schema, "schema_version", "1.3")
        with self.assertRaisesRegex(ValueError, "schema_version"):
            build_co_referenced_page_analyses((first, different_schema))

    def test_factory_rejects_invalid_inputs_before_attribute_access(self) -> None:
        with self.assertRaisesRegex(ValueError, "tuple"):
            build_co_referenced_page_analyses(cast(tuple[PageAnalysis, ...], []))
        with self.assertRaisesRegex(ValueError, "empty"):
            build_co_referenced_page_analyses(())
        with self.assertRaisesRegex(ValueError, "analyses\\[0\\]"):
            build_co_referenced_page_analyses((cast(PageAnalysis, object()),))

    def test_factory_derives_fields_preserves_content_and_accepts_unlinked_analysis(self) -> None:
        alpha = _analysis(
            source_id="source-from-first",
            source_capture_id="capture-from-first",
            page_id="page-from-first",
            primitive_schema_version="primitive-from-first",
            producer_name="alpha",
            candidates=(
                RegionCandidate(
                    "candidate-1", "page-from-first", (0.0, 0.0, 10.0, 10.0), "layout.side_band"
                ),
            ),
        )
        beta = _analysis(
            source_id="source-from-first",
            source_capture_id="capture-from-first",
            page_id="page-from-first",
            primitive_schema_version="primitive-from-first",
            producer_name="beta",
        )
        received = (beta, alpha)
        result = build_co_referenced_page_analyses(received)

        self.assertEqual(result.source_id, "source-from-first")
        self.assertEqual(result.source_capture_id, "capture-from-first")
        self.assertEqual(result.page_id, "page-from-first")
        self.assertEqual(result.source_primitive_schema_version, "primitive-from-first")
        self.assertIs(result.analyses[0], alpha)
        self.assertIs(result.analyses[1], beta)
        self.assertIs(result.analyses[0].candidates[0], alpha.candidates[0])
        self.assertEqual(received, (beta, alpha))
