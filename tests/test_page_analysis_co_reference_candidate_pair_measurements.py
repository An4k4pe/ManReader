"""Tests for contextual geometry of co-referenced candidate pairs."""

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
from page_analysis_co_reference_candidate_pair_measurements import (
    CoReferencedPageCandidatePairMeasurements,
    measure_co_referenced_page_candidate_pair,
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
        text_primitives=(
            TextPrimitive(
                primitive_id="text-1",
                bbox=(0.0, 0.0, 100.0, 100.0),
                text="text",
                source_observation_id="observation-1",
            ),
            TextPrimitive(
                primitive_id="text-2",
                bbox=(0.0, 0.0, 100.0, 100.0),
                text="other text",
                source_observation_id="observation-2",
            ),
        ),
    )


def _candidate(
    candidate_id: str = "candidate-1",
    bbox: tuple[float, float, float, float] = (10.0, 10.0, 20.0, 20.0),
    primitive_ids: tuple[str, ...] = (),
) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=candidate_id,
        page_id="page-1",
        bbox=bbox,
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


class CoReferencedPageCandidatePairMeasurementsTests(unittest.TestCase):
    def test_structure_equality_immutability_slots_and_identity(self) -> None:
        reference = CoReferencedPageCandidateReference("a", "v", "c", "g", "id")
        first_bbox = (0.0, 0.0, 10.0, 10.0)
        second_bbox = (10.0, 10.0, 20.0, 20.0)
        value = CoReferencedPageCandidatePairMeasurements(
            reference, reference, first_bbox, second_bbox,
            0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0, 10.0,
        )

        self.assertEqual(value, CoReferencedPageCandidatePairMeasurements(
            reference, reference, first_bbox, second_bbox,
            0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0, 10.0,
        ))
        self.assertEqual(
            tuple(field.name for field in fields(CoReferencedPageCandidatePairMeasurements)),
            (
                "first_candidate_reference", "second_candidate_reference",
                "first_candidate_bbox", "second_candidate_bbox", "horizontal_gap",
                "vertical_gap", "horizontal_overlap", "vertical_overlap", "x0_delta",
                "y0_delta", "x1_delta", "y1_delta",
            ),
        )
        self.assertIs(value.first_candidate_reference, reference)
        self.assertIs(value.first_candidate_bbox, first_bbox)
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            value.x0_delta = 0.0  # type: ignore[misc]

    def test_direct_validation_rejects_invalid_fields(self) -> None:
        reference = CoReferencedPageCandidateReference("a", "v", "c", "g", "id")
        values: list[object] = [
            reference, reference,
            (0.0, 0.0, 10.0, 10.0), (0.0, 0.0, 10.0, 10.0),
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ]
        invalid_cases = (
            (0, cast(CoReferencedPageCandidateReference, object()), "first_candidate_reference"),
            (1, cast(CoReferencedPageCandidateReference, object()), "second_candidate_reference"),
            (2, cast(tuple[float, float, float, float], (0.0, 0.0, 0.0, 1.0)), "first_candidate_bbox"),
            (3, cast(tuple[float, float, float, float], (0.0, 0.0, float("nan"), 1.0)), "second_candidate_bbox"),
            (4, -1.0, "horizontal_gap"),
            (5, cast(float, 1), "vertical_gap"),
            (6, float("inf"), "horizontal_overlap"),
            (8, cast(float, 1), "x0_delta"),
            (9, float("nan"), "y0_delta"),
        )
        for index, invalid_value, token in invalid_cases:
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                invalid_values = values.copy()
                invalid_values[index] = invalid_value
                CoReferencedPageCandidatePairMeasurements(*invalid_values)  # type: ignore[arg-type]

    def test_signature_is_contextual_with_keyword_only_references(self) -> None:
        signature = inspect.signature(measure_co_referenced_page_candidate_pair)
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


class CandidatePairMeasurementFactoryTests(unittest.TestCase):
    def test_accepts_distinct_candidates_in_the_same_stream(self) -> None:
        first_candidate = _candidate("first", (0.0, 0.0, 10.0, 10.0))
        second_candidate = _candidate("second", (20.0, 0.0, 30.0, 10.0))
        analysis = _analysis(candidates=(first_candidate, second_candidate))
        bound = _bound(analysis)

        value = measure_co_referenced_page_candidate_pair(
            bound,
            first_candidate_reference=_reference(bound, analysis, first_candidate),
            second_candidate_reference=_reference(bound, analysis, second_candidate),
        )

        self.assertEqual((value.horizontal_gap, value.vertical_overlap), (10.0, 10.0))

    def test_same_stream_geometry_self_relation_and_direct_reference(self) -> None:
        candidate = _candidate(bbox=(10.0, 10.0, 30.0, 40.0))
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reference = _reference(bound, analysis, candidate)
        direct_reference = CoReferencedPageCandidateReference(
            "producer", "0.1", "config-v1", "generation-1", "candidate-1"
        )

        value = measure_co_referenced_page_candidate_pair(
            bound,
            first_candidate_reference=reference,
            second_candidate_reference=direct_reference,
        )

        self.assertIs(value.first_candidate_reference, reference)
        self.assertIs(value.second_candidate_reference, direct_reference)
        self.assertIs(value.first_candidate_bbox, candidate.bbox)
        self.assertIs(value.second_candidate_bbox, candidate.bbox)
        self.assertEqual(
            (
                value.horizontal_gap,
                value.vertical_gap,
                value.x0_delta,
                value.y0_delta,
                value.x1_delta,
                value.y1_delta,
            ),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
        self.assertEqual((value.horizontal_overlap, value.vertical_overlap), (20.0, 30.0))

    def test_geometry_cases_symmetry_and_y_coordinates_are_neutral(self) -> None:
        cases = (
            (
                "disjoint_on_both_axes",
                (0.0, 0.0, 10.0, 10.0),
                (20.0, 20.0, 30.0, 30.0),
                (10.0, 10.0, 0.0, 0.0),
                (20.0, 20.0, 20.0, 20.0),
            ),
            (
                "horizontal_gap_vertical_overlap",
                (0.0, 0.0, 10.0, 10.0),
                (20.0, 2.0, 30.0, 8.0),
                (10.0, 0.0, 0.0, 6.0),
                (20.0, 2.0, 20.0, -2.0),
            ),
            (
                "edge_touch",
                (0.0, 0.0, 10.0, 10.0),
                (10.0, 0.0, 20.0, 10.0),
                (0.0, 0.0, 0.0, 10.0),
                (10.0, 0.0, 10.0, 0.0),
            ),
            (
                "corner_touch",
                (0.0, 0.0, 10.0, 10.0),
                (10.0, 10.0, 20.0, 20.0),
                (0.0, 0.0, 0.0, 0.0),
                (10.0, 10.0, 10.0, 10.0),
            ),
            (
                "overlap",
                (0.0, 0.0, 10.0, 10.0),
                (5.0, 5.0, 15.0, 15.0),
                (0.0, 0.0, 5.0, 5.0),
                (5.0, 5.0, 5.0, 5.0),
            ),
            (
                "asymmetric_containment",
                (0.0, 0.0, 20.0, 20.0),
                (5.0, 5.0, 10.0, 10.0),
                (0.0, 0.0, 5.0, 5.0),
                (5.0, 5.0, -10.0, -10.0),
            ),
            (
                "coincident",
                (0.0, 0.0, 10.0, 10.0),
                (0.0, 0.0, 10.0, 10.0),
                (0.0, 0.0, 10.0, 10.0),
                (0.0, 0.0, 0.0, 0.0),
            ),
        )
        for label, first_bbox, second_bbox, expected_measures, expected_deltas in cases:
            with self.subTest(label=label):
                first_candidate = _candidate("first", first_bbox)
                second_candidate = _candidate("second", second_bbox)
                first = _analysis(producer_name="alpha", candidates=(first_candidate,))
                second = _analysis(producer_name="beta", candidates=(second_candidate,))
                bound = _bound(second, first)
                first_reference = _reference(bound, first, first_candidate)
                second_reference = _reference(bound, second, second_candidate)
                forward = measure_co_referenced_page_candidate_pair(
                    bound,
                    first_candidate_reference=first_reference,
                    second_candidate_reference=second_reference,
                )
                reverse = measure_co_referenced_page_candidate_pair(
                    bound,
                    first_candidate_reference=second_reference,
                    second_candidate_reference=first_reference,
                )
                self.assertEqual(
                    (
                        forward.horizontal_gap,
                        forward.vertical_gap,
                        forward.horizontal_overlap,
                        forward.vertical_overlap,
                    ),
                    expected_measures,
                )
                self.assertEqual(
                    (
                        forward.x0_delta,
                        forward.y0_delta,
                        forward.x1_delta,
                        forward.y1_delta,
                    ),
                    expected_deltas,
                )
                self.assertEqual(forward.horizontal_gap, reverse.horizontal_gap)
                self.assertEqual(forward.vertical_gap, reverse.vertical_gap)
                self.assertEqual(forward.horizontal_overlap, reverse.horizontal_overlap)
                self.assertEqual(forward.vertical_overlap, reverse.vertical_overlap)
                self.assertEqual(forward.x0_delta, -reverse.x0_delta)
                self.assertEqual(forward.y0_delta, -reverse.y0_delta)
                self.assertEqual(forward.x1_delta, -reverse.x1_delta)
                self.assertEqual(forward.y1_delta, -reverse.y1_delta)

    def test_cross_stream_collisions_shared_candidate_and_cross_binding_aliasing(self) -> None:
        alpha_collision = _candidate("collision", (0.0, 0.0, 10.0, 10.0))
        beta_collision = _candidate("collision", (20.0, 0.0, 30.0, 10.0))
        alpha = _analysis(producer_name="collision-alpha", candidates=(alpha_collision,))
        beta = _analysis(producer_name="collision-beta", candidates=(beta_collision,))
        collision_bound = _bound(beta, alpha)
        collision_value = measure_co_referenced_page_candidate_pair(
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
        self.assertIs(collision_value.first_candidate_bbox, alpha_collision.bbox)
        self.assertIs(collision_value.second_candidate_bbox, beta_collision.bbox)

        shared = _candidate("shared")
        alpha = _analysis(producer_name="alpha", candidates=(shared,))
        beta = _analysis(producer_name="beta", candidates=(shared,))
        bound = _bound(beta, alpha)
        alpha_reference = _reference(bound, alpha, shared)
        beta_reference = _reference(bound, beta, shared)
        value = measure_co_referenced_page_candidate_pair(
            bound,
            first_candidate_reference=alpha_reference,
            second_candidate_reference=beta_reference,
        )
        self.assertIs(value.first_candidate_bbox, shared.bbox)
        self.assertIs(value.second_candidate_bbox, shared.bbox)

        aliased = _candidate("shared")
        alias_bound = _bound(_analysis(producer_name="alpha", candidates=(aliased,)))
        alias_value = measure_co_referenced_page_candidate_pair(
            alias_bound,
            first_candidate_reference=alpha_reference,
            second_candidate_reference=alpha_reference,
        )
        self.assertIs(alias_value.first_candidate_bbox, aliased.bbox)

    def test_empty_disjoint_and_shared_primitives_do_not_change_measurements(self) -> None:
        for label, first_ids, second_ids in (
            ("empty", (), ()),
            ("disjoint", ("text-1",), ("text-2",)),
            ("shared", ("text-1",), ("text-1",)),
        ):
            with self.subTest(label=label):
                first_candidate = _candidate(
                    "first",
                    (0.0, 0.0, 10.0, 10.0),
                    first_ids,
                )
                second_candidate = _candidate(
                    "second",
                    (20.0, 2.0, 30.0, 8.0),
                    second_ids,
                )
                first = _analysis(producer_name="alpha", candidates=(first_candidate,))
                second = _analysis(producer_name="beta", candidates=(second_candidate,))
                bound = _bound(first, second)
                value = measure_co_referenced_page_candidate_pair(
                    bound,
                    first_candidate_reference=_reference(bound, first, first_candidate),
                    second_candidate_reference=_reference(bound, second, second_candidate),
                )
                self.assertEqual(
                    (value.horizontal_gap, value.vertical_overlap),
                    (10.0, 6.0),
                )

    def test_rejects_invalid_inputs_missing_items_and_has_no_fallback(self) -> None:
        candidate = _candidate()
        analysis = _analysis(candidates=(candidate,))
        bound = _bound(analysis)
        reference = _reference(bound, analysis, candidate)
        missing_stream = CoReferencedPageCandidateReference("missing", "v", "c", "g", "id")
        missing_candidate = CoReferencedPageCandidateReference(
            "producer", "0.1", "config-v1", "generation-1", "missing"
        )
        for invalid_bound, token in ((cast(BoundCoReferencedPageAnalyses, object()), "bound_co_referenced_page_analyses"),):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                measure_co_referenced_page_candidate_pair(
                    invalid_bound,
                    first_candidate_reference=reference,
                    second_candidate_reference=reference,
                )
        for keyword, invalid_reference in (
            ("first_candidate_reference", cast(CoReferencedPageCandidateReference, object())),
            ("second_candidate_reference", cast(CoReferencedPageCandidateReference, object())),
        ):
            with self.subTest(keyword=keyword), self.assertRaisesRegex(ValueError, keyword):
                kwargs = {
                    "first_candidate_reference": reference,
                    "second_candidate_reference": reference,
                }
                kwargs[keyword] = invalid_reference
                measure_co_referenced_page_candidate_pair(bound, **kwargs)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "analysis stream"):
            measure_co_referenced_page_candidate_pair(
                bound,
                first_candidate_reference=missing_stream,
                second_candidate_reference=reference,
            )
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            measure_co_referenced_page_candidate_pair(
                bound,
                first_candidate_reference=missing_candidate,
                second_candidate_reference=reference,
            )

        beta = _analysis(
            producer_name="beta",
            candidates=(_candidate("only-in-beta"),),
        )
        no_fallback_bound = _bound(analysis, beta)
        alpha_reference = CoReferencedPageCandidateReference(
            "producer", "0.1", "config-v1", "generation-1", "only-in-beta"
        )
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            measure_co_referenced_page_candidate_pair(
                no_fallback_bound,
                first_candidate_reference=alpha_reference,
                second_candidate_reference=alpha_reference,
            )

    def test_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        first_candidate = _candidate("first")
        second_candidate = _candidate("second", (30.0, 30.0, 40.0, 40.0))
        first = _analysis(producer_name="alpha", candidates=(first_candidate,))
        second = _analysis(producer_name="beta", candidates=(second_candidate,))
        bound = _bound(second, first)
        first_reference = _reference(bound, first, first_candidate)
        second_reference = _reference(bound, second, second_candidate)
        before = bound.co_referenced_page_analyses.analyses

        result = measure_co_referenced_page_candidate_pair(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        )
        self.assertEqual(result, measure_co_referenced_page_candidate_pair(
            bound,
            first_candidate_reference=first_reference,
            second_candidate_reference=second_reference,
        ))
        self.assertIs(bound.co_referenced_page_analyses.analyses, before)
        self.assertIs(first.candidates[0], first_candidate)
        self.assertIs(second.candidates[0], second_candidate)


if __name__ == "__main__":
    unittest.main()
