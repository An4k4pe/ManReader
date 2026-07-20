"""Tests for primitive-ID relations of co-referenced candidate pairs."""

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
from page_analysis_co_reference_candidate_primitive_set_measurements import (
    CoReferencedPageCandidatePrimitiveSetMeasurements,
    measure_co_referenced_page_candidate_primitive_sets,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
    build_co_referenced_page_candidate_reference,
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
        page_index=0,
        page_geometry=PageGeometry(
            width=100.0,
            height=100.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=tuple(
            TextPrimitive(
                primitive_id=f"text-{index}",
                bbox=(0.0, 0.0, 100.0, 100.0),
                text=f"text {index}",
                source_observation_id=f"observation-{index}",
            )
            for index in range(1, 7)
        ),
    )


def _candidate(
    candidate_id: str = "candidate-1",
    primitive_ids: tuple[str, ...] = (),
) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id="page-1",
        bbox=(10.0, 10.0, 20.0, 20.0),
        proposed_structural_kind="layout.side_band",
        primitive_ids=primitive_ids,
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


def _bound(
    *analyses: PageAnalysis,
) -> BoundCoReferencedPageAnalyses:
    return bind_co_referenced_page_analyses(
        _page(),
        co_referenced_page_analyses=build_co_referenced_page_analyses(analyses),
    )


def _reference(
    bound: BoundCoReferencedPageAnalyses,
    analysis: PageAnalysis,
    candidate: RegionCandidate,
) -> CoReferencedPageCandidateReference:
    return build_co_referenced_page_candidate_reference(
        bound,
        analysis=analysis,
        candidate=candidate,
    )


class CoReferencedPageCandidatePrimitiveSetMeasurementsTests(
    unittest.TestCase
):
    def test_structure_equality_immutability_slots_and_identity(self) -> None:
        first_reference = CoReferencedPageCandidateReference(
            "alpha", "v", "c", "g", "first"
        )
        second_reference = CoReferencedPageCandidateReference(
            "beta", "v", "c", "g", "second"
        )
        first_ids = ("text-1", "text-2", "text-3")
        second_ids = ("text-2", "text-4", "text-1")
        value = CoReferencedPageCandidatePrimitiveSetMeasurements(
            first_reference,
            second_reference,
            first_ids,
            second_ids,
            ("text-1", "text-2"),
            ("text-3",),
            ("text-4",),
        )

        self.assertEqual(
            value,
            CoReferencedPageCandidatePrimitiveSetMeasurements(
                first_reference,
                second_reference,
                first_ids,
                second_ids,
                ("text-1", "text-2"),
                ("text-3",),
                ("text-4",),
            ),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in fields(
                    CoReferencedPageCandidatePrimitiveSetMeasurements
                )
            ),
            (
                "first_candidate_reference",
                "second_candidate_reference",
                "first_candidate_primitive_ids",
                "second_candidate_primitive_ids",
                "shared_primitive_ids",
                "first_only_primitive_ids",
                "second_only_primitive_ids",
            ),
        )
        self.assertIs(value.first_candidate_reference, first_reference)
        self.assertIs(value.second_candidate_reference, second_reference)
        self.assertIs(value.first_candidate_primitive_ids, first_ids)
        self.assertIs(value.second_candidate_primitive_ids, second_ids)
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            value.shared_primitive_ids = ()  # type: ignore[misc]

    def test_direct_validation_rejects_invalid_fields(self) -> None:
        reference = CoReferencedPageCandidateReference(
            "alpha", "v", "c", "g", "candidate"
        )
        values: list[object] = [
            reference,
            reference,
            ("text-1", "text-2"),
            ("text-2", "text-3"),
            ("text-2",),
            ("text-1",),
            ("text-3",),
        ]

        for index, token in (
            (0, "first_candidate_reference"),
            (1, "second_candidate_reference"),
        ):
            with (
                self.subTest(token=token),
                self.assertRaisesRegex(ValueError, token),
            ):
                invalid_values = values.copy()
                invalid_values[index] = object()
                CoReferencedPageCandidatePrimitiveSetMeasurements(
                    *invalid_values  # type: ignore[arg-type]
                )

        for index, token in (
            (2, "first_candidate_primitive_ids"),
            (3, "second_candidate_primitive_ids"),
            (4, "shared_primitive_ids"),
            (5, "first_only_primitive_ids"),
            (6, "second_only_primitive_ids"),
        ):
            for invalid_value in (
                cast(tuple[str, ...], ["text-1"]),
                ("",),
                ("text-1", "text-1"),
            ):
                with (
                    self.subTest(token=token, value=invalid_value),
                    self.assertRaisesRegex(ValueError, token),
                ):
                    invalid_values = values.copy()
                    invalid_values[index] = invalid_value
                    CoReferencedPageCandidatePrimitiveSetMeasurements(
                        *invalid_values  # type: ignore[arg-type]
                    )

    def test_direct_validation_requires_exact_filtered_subsequences(
        self,
    ) -> None:
        reference = CoReferencedPageCandidateReference(
            "alpha", "v", "c", "g", "candidate"
        )
        valid_values: list[object] = [
            reference,
            reference,
            ("text-1", "text-2", "text-3"),
            ("text-2", "text-4", "text-1"),
            ("text-1", "text-2"),
            ("text-3",),
            ("text-4",),
        ]

        for index, invalid_value, token in (
            (4, ("text-2", "text-1"), "shared_primitive_ids"),
            (5, ("text-1", "text-3"), "first_only_primitive_ids"),
            (6, ("text-2", "text-4"), "second_only_primitive_ids"),
        ):
            with (
                self.subTest(token=token),
                self.assertRaisesRegex(ValueError, token),
            ):
                invalid_values = valid_values.copy()
                invalid_values[index] = invalid_value
                CoReferencedPageCandidatePrimitiveSetMeasurements(
                    *invalid_values  # type: ignore[arg-type]
                )

    def test_signature_is_contextual_with_keyword_only_references(
        self,
    ) -> None:
        signature = inspect.signature(
            measure_co_referenced_page_candidate_primitive_sets
        )
        self.assertEqual(
            tuple(signature.parameters),
            (
                "bound_co_referenced_page_analyses",
                "first_candidate_reference",
                "second_candidate_reference",
            ),
        )
        self.assertIs(
            signature.parameters["first_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            signature.parameters["second_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )


class CandidatePrimitiveSetMeasurementFactoryTests(unittest.TestCase):
    def test_partition_cases_and_original_tuple_identity(self) -> None:
        cases = (
            ("both_empty", (), (), (), (), ()),
            (
                "first_empty",
                (),
                ("text-1",),
                (),
                (),
                ("text-1",),
            ),
            (
                "second_empty",
                ("text-1",),
                (),
                (),
                ("text-1",),
                (),
            ),
            (
                "disjoint",
                ("text-1", "text-2"),
                ("text-3", "text-4"),
                (),
                ("text-1", "text-2"),
                ("text-3", "text-4"),
            ),
            (
                "identical",
                ("text-1", "text-2"),
                ("text-1", "text-2"),
                ("text-1", "text-2"),
                (),
                (),
            ),
            (
                "same_members_different_order",
                ("text-1", "text-2"),
                ("text-2", "text-1"),
                ("text-1", "text-2"),
                (),
                (),
            ),
            (
                "proper_subset",
                ("text-1",),
                ("text-1", "text-2"),
                ("text-1",),
                (),
                ("text-2",),
            ),
            (
                "partial_overlap",
                ("text-1", "text-2", "text-3"),
                ("text-3", "text-4", "text-2"),
                ("text-2", "text-3"),
                ("text-1",),
                ("text-4",),
            ),
        )

        for (
            label,
            first_ids,
            second_ids,
            expected_shared,
            expected_first_only,
            expected_second_only,
        ) in cases:
            with self.subTest(label=label):
                first_candidate = _candidate("first", first_ids)
                second_candidate = _candidate("second", second_ids)
                first = _analysis(
                    producer_name="alpha",
                    candidates=(first_candidate,),
                )
                second = _analysis(
                    producer_name="beta",
                    candidates=(second_candidate,),
                )
                bound = _bound(second, first)
                first_reference = _reference(
                    bound,
                    first,
                    first_candidate,
                )
                second_reference = _reference(
                    bound,
                    second,
                    second_candidate,
                )

                value = (
                    measure_co_referenced_page_candidate_primitive_sets(
                        bound,
                        first_candidate_reference=first_reference,
                        second_candidate_reference=second_reference,
                    )
                )

                self.assertIs(
                    value.first_candidate_primitive_ids,
                    first_candidate.primitive_ids,
                )
                self.assertIs(
                    value.second_candidate_primitive_ids,
                    second_candidate.primitive_ids,
                )
                self.assertEqual(
                    (
                        value.shared_primitive_ids,
                        value.first_only_primitive_ids,
                        value.second_only_primitive_ids,
                    ),
                    (
                        expected_shared,
                        expected_first_only,
                        expected_second_only,
                    ),
                )

    def test_operand_swap_changes_shared_order_without_priority(self) -> None:
        first_candidate = _candidate(
            "first",
            ("text-1", "text-2", "text-3"),
        )
        second_candidate = _candidate(
            "second",
            ("text-3", "text-1", "text-2"),
        )
        first = _analysis(
            producer_name="alpha",
            candidates=(first_candidate,),
        )
        second = _analysis(
            producer_name="beta",
            candidates=(second_candidate,),
        )
        bound = _bound(first, second)
        first_reference = _reference(bound, first, first_candidate)
        second_reference = _reference(bound, second, second_candidate)

        forward = measure_co_referenced_page_candidate_primitive_sets(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        )
        reverse = measure_co_referenced_page_candidate_primitive_sets(
            bound,
            first_candidate_reference=second_reference,
            second_candidate_reference=first_reference,
        )

        self.assertEqual(
            forward.shared_primitive_ids,
            ("text-1", "text-2", "text-3"),
        )
        self.assertEqual(
            reverse.shared_primitive_ids,
            ("text-3", "text-1", "text-2"),
        )
        self.assertEqual(forward.first_only_primitive_ids, ())
        self.assertEqual(forward.second_only_primitive_ids, ())
        self.assertEqual(reverse.first_only_primitive_ids, ())
        self.assertEqual(reverse.second_only_primitive_ids, ())

    def test_self_relation_and_logically_equal_distinct_references(
        self,
    ) -> None:
        candidate = _candidate(
            primitive_ids=("text-1", "text-2"),
        )
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        built_reference = _reference(bound, analysis, candidate)
        direct_reference = CoReferencedPageCandidateReference(
            "producer",
            "0.1",
            "config-v1",
            "generation-1",
            "candidate-1",
        )

        value = measure_co_referenced_page_candidate_primitive_sets(
            bound,
            first_candidate_reference=built_reference,
            second_candidate_reference=direct_reference,
        )

        self.assertIs(value.first_candidate_reference, built_reference)
        self.assertIs(value.second_candidate_reference, direct_reference)
        self.assertIs(
            value.first_candidate_primitive_ids,
            candidate.primitive_ids,
        )
        self.assertIs(
            value.second_candidate_primitive_ids,
            candidate.primitive_ids,
        )
        self.assertEqual(
            value.shared_primitive_ids,
            candidate.primitive_ids,
        )
        self.assertEqual(value.first_only_primitive_ids, ())
        self.assertEqual(value.second_only_primitive_ids, ())

    def test_cross_stream_collisions_shared_object_and_aliasing(
        self,
    ) -> None:
        alpha_collision = _candidate(
            "collision",
            ("text-1", "text-2"),
        )
        beta_collision = _candidate(
            "collision",
            ("text-2", "text-3"),
        )
        alpha = _analysis(
            producer_name="collision-alpha",
            candidates=(alpha_collision,),
        )
        beta = _analysis(
            producer_name="collision-beta",
            candidates=(beta_collision,),
        )
        collision_bound = _bound(beta, alpha)
        collision_value = (
            measure_co_referenced_page_candidate_primitive_sets(
                collision_bound,
                first_candidate_reference=_reference(
                    collision_bound,
                    alpha,
                    alpha_collision,
                ),
                second_candidate_reference=_reference(
                    collision_bound,
                    beta,
                    beta_collision,
                ),
            )
        )
        self.assertEqual(
            (
                collision_value.shared_primitive_ids,
                collision_value.first_only_primitive_ids,
                collision_value.second_only_primitive_ids,
            ),
            (("text-2",), ("text-1",), ("text-3",)),
        )

        shared = _candidate(
            "shared",
            ("text-4", "text-5"),
        )
        shared_alpha = _analysis(
            producer_name="alpha",
            candidates=(shared,),
        )
        shared_beta = _analysis(
            producer_name="beta",
            candidates=(shared,),
        )
        shared_bound = _bound(shared_beta, shared_alpha)
        shared_value = measure_co_referenced_page_candidate_primitive_sets(
            shared_bound,
            first_candidate_reference=_reference(
                shared_bound,
                shared_alpha,
                shared,
            ),
            second_candidate_reference=_reference(
                shared_bound,
                shared_beta,
                shared,
            ),
        )
        self.assertIs(
            shared_value.first_candidate_primitive_ids,
            shared.primitive_ids,
        )
        self.assertIs(
            shared_value.second_candidate_primitive_ids,
            shared.primitive_ids,
        )

        original = _candidate("aliased", ("text-1",))
        original_analysis = _analysis(
            producer_name="alias",
            candidates=(original,),
        )
        original_bound = _bound(original_analysis)
        aliased_reference = _reference(
            original_bound,
            original_analysis,
            original,
        )

        replacement = _candidate(
            "aliased",
            ("text-2", "text-3"),
        )
        replacement_analysis = _analysis(
            producer_name="alias",
            candidates=(replacement,),
        )
        replacement_bound = _bound(replacement_analysis)
        alias_value = measure_co_referenced_page_candidate_primitive_sets(
            replacement_bound,
            first_candidate_reference=aliased_reference,
            second_candidate_reference=aliased_reference,
        )
        self.assertIs(
            alias_value.first_candidate_primitive_ids,
            replacement.primitive_ids,
        )
        self.assertEqual(
            alias_value.shared_primitive_ids,
            ("text-2", "text-3"),
        )

    def test_rejects_invalid_inputs_missing_items_and_has_no_fallback(
        self,
    ) -> None:
        candidate = _candidate(primitive_ids=("text-1",))
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reference = _reference(bound, analysis, candidate)

        with self.assertRaisesRegex(
            ValueError,
            "bound_co_referenced_page_analyses",
        ):
            measure_co_referenced_page_candidate_primitive_sets(
                cast(BoundCoReferencedPageAnalyses, object()),
                first_candidate_reference=reference,
                second_candidate_reference=reference,
            )

        for keyword in (
            "first_candidate_reference",
            "second_candidate_reference",
        ):
            with (
                self.subTest(keyword=keyword),
                self.assertRaisesRegex(ValueError, keyword),
            ):
                kwargs = {
                    "first_candidate_reference": reference,
                    "second_candidate_reference": reference,
                }
                kwargs[keyword] = cast(
                    CoReferencedPageCandidateReference,
                    object(),
                )
                measure_co_referenced_page_candidate_primitive_sets(
                    bound,
                    **kwargs,  # type: ignore[arg-type]
                )

        missing_stream = CoReferencedPageCandidateReference(
            "missing",
            "v",
            "c",
            "g",
            "candidate",
        )
        with self.assertRaisesRegex(ValueError, "analysis stream"):
            measure_co_referenced_page_candidate_primitive_sets(
                bound,
                first_candidate_reference=missing_stream,
                second_candidate_reference=reference,
            )

        missing_candidate = CoReferencedPageCandidateReference(
            "producer",
            "0.1",
            "config-v1",
            "generation-1",
            "missing",
        )
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            measure_co_referenced_page_candidate_primitive_sets(
                bound,
                first_candidate_reference=missing_candidate,
                second_candidate_reference=reference,
            )

        beta = _analysis(
            producer_name="beta",
            candidates=(
                _candidate("only-in-beta", ("text-2",)),
            ),
        )
        no_fallback_bound = _bound(analysis, beta)
        no_fallback_reference = CoReferencedPageCandidateReference(
            "producer",
            "0.1",
            "config-v1",
            "generation-1",
            "only-in-beta",
        )
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            measure_co_referenced_page_candidate_primitive_sets(
                no_fallback_bound,
                first_candidate_reference=no_fallback_reference,
                second_candidate_reference=no_fallback_reference,
            )

    def test_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        first_candidate = _candidate(
            "first",
            ("text-1", "text-2"),
        )
        second_candidate = _candidate(
            "second",
            ("text-2", "text-3"),
        )
        first = _analysis(
            producer_name="alpha",
            candidates=(first_candidate,),
        )
        second = _analysis(
            producer_name="beta",
            candidates=(second_candidate,),
        )
        bound = _bound(second, first)
        first_reference = _reference(bound, first, first_candidate)
        second_reference = _reference(bound, second, second_candidate)
        analyses_before = bound.co_referenced_page_analyses.analyses
        first_candidates_before = first.candidates
        second_candidates_before = second.candidates

        result = measure_co_referenced_page_candidate_primitive_sets(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        )
        repeated = measure_co_referenced_page_candidate_primitive_sets(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        )

        self.assertEqual(result, repeated)
        self.assertIs(
            bound.co_referenced_page_analyses.analyses,
            analyses_before,
        )
        self.assertIs(first.candidates, first_candidates_before)
        self.assertIs(second.candidates, second_candidates_before)
        self.assertIs(first.candidates[0], first_candidate)
        self.assertIs(second.candidates[0], second_candidate)


if __name__ == "__main__":
    unittest.main()
