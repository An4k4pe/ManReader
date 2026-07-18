"""Tests for contextual references to co-referenced page-analysis candidates."""

from __future__ import annotations

import inspect
import unittest
from dataclasses import FrozenInstanceError, fields
from typing import cast

from geometry_model import PageGeometry
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import (
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    build_co_referenced_page_candidate_reference,
    resolve_co_referenced_page_candidate_reference,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _page() -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page-1",
        page_index=4,
        page_geometry=PageGeometry(
            width=100.0,
            height=100.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=(
            TextPrimitive(
                primitive_id="text-1",
                bbox=(10.0, 10.0, 20.0, 20.0),
                text="text",
                source_observation_id="observation-1",
            ),
        ),
    )


def _candidate(candidate_id: str = "candidate-1") -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id="page-1",
        bbox=(10.0, 10.0, 20.0, 20.0),
        proposed_structural_kind="layout.side_band",
        primitive_ids=("text-1",),
    )


def _analysis(
    *,
    producer_name: str = "producer",
    producer_version: str = "0.1",
    configuration_id: str = "config-v1",
    generation_id: str = "generation-1",
    candidates: tuple[RegionCandidate, ...] = (),
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id="page-1",
        provenance=PageAnalysisProvenance(
            source_id="source-1",
            source_capture_id="capture-1",
            source_page_id="page-1",
            source_primitive_schema_version="1.0",
            producer_name=producer_name,
            producer_version=producer_version,
            configuration_id=configuration_id,
        ),
        candidates=candidates,
    )


def _bound(*analyses: PageAnalysis):
    collection = build_co_referenced_page_analyses(analyses)
    return bind_co_referenced_page_analyses(
        _page(),
        co_referenced_page_analyses=collection,
    )


class CoReferencedPageCandidateReferenceTests(unittest.TestCase):
    def test_structure_value_semantics_immutability_and_slots(self) -> None:
        reference = CoReferencedPageCandidateReference(
            "producer", "0.1", "config-v1", "generation-1", "candidate-1"
        )

        self.assertEqual(
            reference,
            CoReferencedPageCandidateReference(
                "producer", "0.1", "config-v1", "generation-1", "candidate-1"
            ),
        )
        self.assertEqual(
            tuple(field.name for field in fields(CoReferencedPageCandidateReference)),
            (
                "producer_name",
                "producer_version",
                "configuration_id",
                "generation_id",
                "candidate_id",
            ),
        )
        self.assertFalse(hasattr(reference, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            reference.candidate_id = "other"  # type: ignore[misc]
        for name in (
            "source_id",
            "source_capture_id",
            "page_id",
            "page_index",
            "schema_version",
            "bbox",
            "region_id",
            "proposed_structural_kind",
            "primitive_ids",
        ):
            self.assertFalse(hasattr(reference, name))

    def test_rejects_empty_and_runtime_invalid_fields(self) -> None:
        values = {
            "producer_name": "producer",
            "producer_version": "0.1",
            "configuration_id": "config-v1",
            "generation_id": "generation-1",
            "candidate_id": "candidate-1",
        }
        for field_name in values:
            with (
                self.subTest(field_name=field_name, value=""),
                self.assertRaisesRegex(ValueError, field_name),
            ):
                CoReferencedPageCandidateReference(**(values | {field_name: ""}))
            with (
                self.subTest(field_name=field_name, value="object"),
                self.assertRaisesRegex(ValueError, field_name),
            ):
                CoReferencedPageCandidateReference(**(values | {field_name: cast(str, object())}))
        exact_values = (
            " Producer ",
            "V0.1",
            "Config-V1",
            "generation-e\u0301",
            " Candidate-1 ",
        )
        exact_reference = CoReferencedPageCandidateReference(*exact_values)

        self.assertEqual(
            (
                exact_reference.producer_name,
                exact_reference.producer_version,
                exact_reference.configuration_id,
                exact_reference.generation_id,
                exact_reference.candidate_id,
            ),
            exact_values,
        )

    def test_public_function_signatures_are_contextual_and_keyword_only(self) -> None:
        build_signature = inspect.signature(build_co_referenced_page_candidate_reference)
        resolve_signature = inspect.signature(resolve_co_referenced_page_candidate_reference)

        self.assertEqual(
            tuple(build_signature.parameters),
            ("bound_co_referenced_page_analyses", "analysis", "candidate"),
        )
        self.assertIs(
            build_signature.parameters["analysis"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            build_signature.parameters["candidate"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertEqual(
            tuple(resolve_signature.parameters),
            ("bound_co_referenced_page_analyses", "reference"),
        )
        self.assertIs(
            resolve_signature.parameters["reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )


class CoReferencedPageCandidateReferenceFactoryTests(unittest.TestCase):
    def test_builds_for_single_and_multiple_streams(self) -> None:
        first_candidate = _candidate("shared")
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        singleton = _bound(first)
        singleton_reference = build_co_referenced_page_candidate_reference(
            singleton,
            analysis=first,
            candidate=first_candidate,
        )
        self.assertEqual(singleton_reference.producer_name, "alpha")
        self.assertEqual(singleton_reference.candidate_id, "shared")

        second_candidate = _candidate("shared")
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(second, first)
        reference = build_co_referenced_page_candidate_reference(
            bound,
            analysis=second,
            candidate=second_candidate,
        )
        self.assertEqual(reference.producer_name, "beta")
        self.assertIs(
            resolve_co_referenced_page_candidate_reference(bound, reference=reference),
            second_candidate,
        )

        shared_candidate = _candidate("same-object")
        shared_alpha = _analysis(
            producer_name="shared-alpha",
            candidates=(shared_candidate,),
        )
        shared_beta = _analysis(
            producer_name="shared-beta",
            candidates=(shared_candidate,),
        )
        shared_bound = _bound(shared_beta, shared_alpha)
        shared_reference = build_co_referenced_page_candidate_reference(
            shared_bound,
            analysis=shared_beta,
            candidate=shared_candidate,
        )
        self.assertEqual(shared_reference.producer_name, "shared-beta")
        self.assertIs(
            resolve_co_referenced_page_candidate_reference(
                shared_bound,
                reference=shared_reference,
            ),
            shared_candidate,
        )

    def test_rejects_runtime_types_and_logically_equal_reconstructed_objects(self) -> None:
        candidate = _candidate()
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reconstructed_analysis = _analysis(candidates=(candidate,))
        reconstructed_candidate = _candidate()

        for value, token in (
            (cast(object, object()), "bound_co_referenced_page_analyses"),
            (cast(object, object()), "analysis"),
            (cast(object, object()), "candidate"),
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                if token == "bound_co_referenced_page_analyses":
                    build_co_referenced_page_candidate_reference(
                        cast(BoundCoReferencedPageAnalyses, value),
                        analysis=analysis,
                        candidate=candidate,
                    )
                elif token == "analysis":
                    build_co_referenced_page_candidate_reference(
                        bound, analysis=cast(PageAnalysis, value), candidate=candidate
                    )
                else:
                    build_co_referenced_page_candidate_reference(
                        bound, analysis=analysis, candidate=cast(RegionCandidate, value)
                    )

        with self.assertRaisesRegex(ValueError, "analysis"):
            build_co_referenced_page_candidate_reference(
                bound,
                analysis=reconstructed_analysis,
                candidate=candidate,
            )
        with self.assertRaisesRegex(ValueError, "candidate"):
            build_co_referenced_page_candidate_reference(
                bound,
                analysis=analysis,
                candidate=reconstructed_candidate,
            )

    def test_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        candidate = _candidate()
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        analyses_before = bound.co_referenced_page_analyses.analyses
        candidates_before = analysis.candidates

        first = build_co_referenced_page_candidate_reference(
            bound, analysis=analysis, candidate=candidate
        )
        second = build_co_referenced_page_candidate_reference(
            bound, analysis=analysis, candidate=candidate
        )

        self.assertEqual(first, second)
        self.assertIs(bound.co_referenced_page_analyses.analyses, analyses_before)
        self.assertIs(analysis.candidates, candidates_before)
        self.assertIs(candidates_before[0], candidate)


class CoReferencedPageCandidateReferenceResolverTests(unittest.TestCase):
    def test_resolves_direct_reference_by_exact_stream_key_and_identity(self) -> None:
        candidate = _candidate()
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reference = CoReferencedPageCandidateReference(
            producer_name="producer",
            producer_version="0.1",
            configuration_id="config-v1",
            generation_id="generation-1",
            candidate_id="candidate-1",
        )

        resolved = resolve_co_referenced_page_candidate_reference(
            bound,
            reference=reference,
        )

        self.assertIs(resolved, candidate)

    def test_rejects_missing_stream_candidate_and_fallback_to_other_stream(self) -> None:
        first = _analysis(
            producer_name="alpha",
            candidates=(_candidate("candidate-in-alpha"),),
        )
        beta_candidate = _candidate("candidate-in-beta")
        second = _analysis(producer_name="beta", candidates=(beta_candidate,))
        bound = _bound(second, first)

        missing_stream = CoReferencedPageCandidateReference(
            "missing", "0.1", "config-v1", "generation-1", "candidate-in-beta"
        )
        with self.assertRaisesRegex(ValueError, "analysis stream"):
            resolve_co_referenced_page_candidate_reference(bound, reference=missing_stream)

        missing_candidate = CoReferencedPageCandidateReference(
            "alpha", "0.1", "config-v1", "generation-1", "candidate-in-beta"
        )
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            resolve_co_referenced_page_candidate_reference(
                bound,
                reference=missing_candidate,
            )

    def test_is_independent_of_canonical_position_and_allows_cross_binding_aliasing(
        self,
    ) -> None:
        candidate = _candidate()
        target = _analysis(producer_name="middle", candidates=(candidate,))
        first_bound = _bound(
            _analysis(producer_name="zeta", candidates=(_candidate("other"),)),
            target,
        )
        reference = build_co_referenced_page_candidate_reference(
            first_bound,
            analysis=target,
            candidate=candidate,
        )

        aliased_candidate = _candidate()
        aliased_target = _analysis(
            producer_name="middle",
            candidates=(aliased_candidate,),
        )
        second_bound = _bound(
            aliased_target,
            _analysis(producer_name="alpha", candidates=(_candidate("other"),)),
        )

        self.assertIs(
            first_bound.co_referenced_page_analyses.analyses[0],
            target,
        )
        self.assertIs(
            second_bound.co_referenced_page_analyses.analyses[1],
            aliased_target,
        )
        self.assertIs(
            resolve_co_referenced_page_candidate_reference(
                first_bound,
                reference=reference,
            ),
            candidate,
        )
        self.assertIs(
            resolve_co_referenced_page_candidate_reference(
                second_bound,
                reference=reference,
            ),
            aliased_candidate,
        )

    def test_rejects_runtime_types(self) -> None:
        candidate = _candidate()
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reference = build_co_referenced_page_candidate_reference(
            bound, analysis=analysis, candidate=candidate
        )

        with self.assertRaisesRegex(ValueError, "bound_co_referenced_page_analyses"):
            resolve_co_referenced_page_candidate_reference(
                cast(BoundCoReferencedPageAnalyses, object()),
                reference=reference,
            )
        with self.assertRaisesRegex(ValueError, "reference"):
            resolve_co_referenced_page_candidate_reference(
                bound,
                reference=cast(CoReferencedPageCandidateReference, object()),
            )


if __name__ == "__main__":
    unittest.main()
