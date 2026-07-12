from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysis
from page_analysis_side_band import (
    _build_local_horizontal_fragment_hypotheses,
    build_singleton_side_band_page_analysis,
)
from page_analysis_text_hypotheses import GeometricTextHypothesis
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _text_primitive(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
    *,
    direction: tuple[float, float] | None = None,
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=primitive_id,
        source_observation_id=f"obs:{primitive_id}",
        direction=direction,
    )


def _primitive_page(
    *,
    text_primitives: tuple[TextPrimitive, ...] = (),
) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page-1",
        page_index=0,
        page_geometry=PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=text_primitives,
    )


def _candidate_ids(analysis: PageAnalysis) -> tuple[str, ...]:
    return tuple(candidate.candidate_id for candidate in analysis.candidates)


def _fragment_ids(
    hypotheses: tuple[GeometricTextHypothesis, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(hypothesis.primitive_ids for hypothesis in hypotheses)


class BuildSingletonSideBandPageAnalysisInputTest(unittest.TestCase):
    def test_rejects_wrong_primitive_page_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_singleton_side_band_page_analysis(cast(Any, object()), generation_id="gen-1")

    def test_rejects_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_singleton_side_band_page_analysis(_primitive_page(), generation_id="")

    def test_page_without_text_produces_no_candidates(self) -> None:
        analysis = build_singleton_side_band_page_analysis(_primitive_page(), generation_id="gen-1")

        self.assertEqual(analysis.candidates, ())
        self.assertEqual(analysis.regions, ())
        self.assertEqual(analysis.relations, ())


class BuildSingletonSideBandPageAnalysisContractTest(unittest.TestCase):
    def test_returns_current_schema_and_coherent_provenance(self) -> None:
        page = _primitive_page()

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.generation_id, "gen-1")
        self.assertEqual(analysis.page_id, page.page_id)
        self.assertEqual(analysis.provenance.source_id, page.source_id)
        self.assertEqual(analysis.provenance.source_capture_id, page.source_capture_id)
        self.assertEqual(analysis.provenance.source_page_id, page.page_id)
        self.assertEqual(analysis.provenance.source_primitive_schema_version, page.schema_version)
        self.assertEqual(analysis.provenance.producer_name, "page_analysis.singleton_side_band")
        self.assertEqual(analysis.provenance.producer_version, "0.1")
        self.assertEqual(analysis.provenance.configuration_id, "singleton-side-band-v1")

    def test_result_validates_against_primitive_page(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("left", (0.0, 50.0, 20.0, 60.0)),))

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        validate_page_analysis_against_primitive_page(analysis, page)

    def test_does_not_modify_input_page(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("right", (80.0, 50.0, 100.0, 60.0)),
                _text_primitive("left", (0.0, 80.0, 20.0, 90.0)),
            )
        )
        before = page
        original_order = page.text_primitives

        build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(page, before)
        self.assertEqual(page.text_primitives, original_order)


class BuildSingletonSideBandPageAnalysisSelectionTest(unittest.TestCase):
    def test_left_singleton_produces_side_band_candidate(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("left", (0.0, 50.0, 20.0, 60.0)),))

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(_candidate_ids(analysis), ("candidate:side-band:left",))
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.proposed_structural_kind, "layout.side_band")
        self.assertEqual(candidate.primitive_ids, ("left",))

    def test_right_singleton_produces_side_band_candidate(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("right", (80.0, 50.0, 100.0, 60.0)),)
        )

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(_candidate_ids(analysis), ("candidate:side-band:right",))
        self.assertEqual(analysis.candidates[0].proposed_structural_kind, "layout.side_band")
        self.assertEqual(analysis.candidates[0].primitive_ids, ("right",))

    def test_multiple_accepted_singletons_remain_independent(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("right", (80.0, 80.0, 100.0, 90.0)),
                _text_primitive("left", (0.0, 50.0, 20.0, 60.0)),
            )
        )

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(
            _candidate_ids(analysis),
            ("candidate:side-band:left", "candidate:side-band:right"),
        )
        self.assertEqual(
            tuple(candidate.primitive_ids for candidate in analysis.candidates),
            (("left",), ("right",)),
        )

    def test_candidate_bbox_uses_visible_measurement_bbox(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("clipped", (-5.0, 50.0, 20.0, 60.0)),)
        )

        analysis = build_singleton_side_band_page_analysis(page, generation_id="gen-1")

        self.assertEqual(analysis.candidates[0].bbox, (0.0, 50.0, 20.0, 60.0))

    def test_central_narrow_singleton_does_not_produce_candidate(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("central", (40.0, 50.0, 50.0, 60.0)),)
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_edge_touching_but_too_wide_singleton_does_not_produce_candidate(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("wide", (0.0, 50.0, 24.0, 60.0)),))

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_lateral_header_and_footer_do_not_produce_candidates(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("header", (0.0, 10.0, 20.0, 20.0)),
                _text_primitive("footer", (80.0, 180.0, 100.0, 190.0)),
            )
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_wide_column_line_does_not_produce_candidate(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("column", (20.0, 50.0, 70.0, 60.0)),)
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_vertical_diagonal_and_invisible_text_do_not_produce_candidates(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("vertical", (0.0, 50.0, 20.0, 60.0), direction=(0.0, 1.0)),
                _text_primitive(
                    "diagonal",
                    (80.0, 50.0, 100.0, 60.0),
                    direction=(0.7071067811865476, 0.7071067811865476),
                ),
                _text_primitive("outside", (110.0, 50.0, 120.0, 60.0)),
            )
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )


class BuildSingletonSideBandPageAnalysisDeterminismTest(unittest.TestCase):
    def test_reversed_input_uses_same_canonical_candidate_order(self) -> None:
        first_page = _primitive_page(
            text_primitives=(
                _text_primitive("right", (80.0, 80.0, 100.0, 90.0)),
                _text_primitive("left", (0.0, 50.0, 20.0, 60.0)),
            )
        )
        reversed_page = _primitive_page(text_primitives=tuple(reversed(first_page.text_primitives)))

        first = build_singleton_side_band_page_analysis(first_page, generation_id="gen-1")
        second = build_singleton_side_band_page_analysis(reversed_page, generation_id="gen-1")

        self.assertEqual(_candidate_ids(first), _candidate_ids(second))
        self.assertEqual(first.candidates, second.candidates)

    def test_repeated_calls_produce_same_page_analysis(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("left", (0.0, 50.0, 20.0, 60.0)),))

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1"),
            build_singleton_side_band_page_analysis(page, generation_id="gen-1"),
        )


class BuildSingletonSideBandPageAnalysisBoundaryTest(unittest.TestCase):
    def test_outer_band_boundary_is_inclusive(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("boundary", (5.0, 50.0, 25.0, 60.0)),)
        )

        self.assertEqual(
            _candidate_ids(build_singleton_side_band_page_analysis(page, generation_id="gen-1")),
            ("candidate:side-band:boundary",),
        )

    def test_just_outside_outer_band_does_not_pass(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("outside", (5.0, 50.0, 25.001, 60.0)),)
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_width_boundary_is_inclusive(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("width", (0.0, 50.0, 22.0, 60.0)),))

        self.assertEqual(
            _candidate_ids(build_singleton_side_band_page_analysis(page, generation_id="gen-1")),
            ("candidate:side-band:width",),
        )

    def test_width_just_above_boundary_does_not_pass(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("wide", (0.0, 50.0, 22.001, 60.0)),)
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_vertical_corridor_boundaries_are_inclusive(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("top", (0.0, 24.0, 20.0, 34.0)),
                _text_primitive("bottom", (80.0, 166.0, 100.0, 176.0)),
            )
        )

        self.assertEqual(
            _candidate_ids(build_singleton_side_band_page_analysis(page, generation_id="gen-1")),
            ("candidate:side-band:top", "candidate:side-band:bottom"),
        )

    def test_vertical_corridor_just_outside_boundaries_do_not_pass(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("above", (0.0, 23.999, 20.0, 34.0)),
                _text_primitive("below", (80.0, 166.0, 100.0, 176.001)),
            )
        )

        self.assertEqual(
            build_singleton_side_band_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )


class LocalHorizontalFragmentHypothesesTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_page(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            _build_local_horizontal_fragment_hypotheses(cast(Any, object()))
        self.assertEqual(_build_local_horizontal_fragment_hypotheses(_primitive_page()), ())

    def test_returns_hypotheses_without_mutating_page(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("solo", (10.0, 50.0, 20.0, 60.0)),))
        before = page

        hypotheses = _build_local_horizontal_fragment_hypotheses(page)

        self.assertEqual(_fragment_ids(hypotheses), (("solo",),))
        self.assertTrue(
            all(isinstance(hypothesis, GeometricTextHypothesis) for hypothesis in hypotheses)
        )
        self.assertEqual(page, before)

    def test_merges_two_and_three_local_fragments_left_to_right(self) -> None:
        two = _primitive_page(
            text_primitives=(
                _text_primitive("left", (10.0, 50.0, 20.0, 60.0)),
                _text_primitive("right", (21.0, 50.0, 31.0, 60.0)),
            )
        )
        three = _primitive_page(
            text_primitives=(
                _text_primitive("third", (32.0, 51.0, 42.0, 61.0)),
                _text_primitive("first", (10.0, 50.0, 20.0, 60.0)),
                _text_primitive("second", (21.0, 50.0, 31.0, 60.0)),
            )
        )

        self.assertEqual(
            _fragment_ids(_build_local_horizontal_fragment_hypotheses(two)),
            (("left", "right"),),
        )
        self.assertEqual(
            _fragment_ids(_build_local_horizontal_fragment_hypotheses(three)),
            (("first", "second", "third"),),
        )

    def test_output_is_independent_of_input_order_and_keeps_isolated_singleton(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("isolated", (10.0, 90.0, 20.0, 100.0)),
                _text_primitive("second", (21.0, 50.0, 31.0, 60.0)),
                _text_primitive("first", (10.0, 50.0, 20.0, 60.0)),
            )
        )
        reversed_page = _primitive_page(text_primitives=tuple(reversed(page.text_primitives)))

        hypotheses = _build_local_horizontal_fragment_hypotheses(page)

        self.assertEqual(_fragment_ids(hypotheses), (("first", "second"), ("isolated",)))
        self.assertEqual(hypotheses, _build_local_horizontal_fragment_hypotheses(reversed_page))
        self.assertEqual(
            tuple(
                primitive_id
                for hypothesis in hypotheses
                for primitive_id in hypothesis.primitive_ids
            ),
            ("first", "second", "isolated"),
        )

    def test_does_not_cross_gutters_columns_or_opposite_page_sides(self) -> None:
        for primitives in (
            (
                _text_primitive("left", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("right", (30.0, 50.0, 40.0, 60.0)),
            ),
            (
                _text_primitive("column-a", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("column-b", (50.0, 50.0, 60.0, 60.0)),
            ),
            (
                _text_primitive("page-left", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("page-right", (90.0, 50.0, 100.0, 60.0)),
            ),
        ):
            with self.subTest(primitives=primitives):
                hypotheses = _build_local_horizontal_fragment_hypotheses(
                    _primitive_page(text_primitives=primitives)
                )
                self.assertTrue(
                    all(len(hypothesis.primitive_ids) == 1 for hypothesis in hypotheses)
                )

    def test_stops_before_gutter_and_allows_centered_local_fragments(self) -> None:
        chain = _primitive_page(
            text_primitives=(
                _text_primitive("a", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("b", (11.0, 50.0, 21.0, 60.0)),
                _text_primitive("c", (40.0, 50.0, 50.0, 60.0)),
            )
        )
        title = _primitive_page(
            text_primitives=(
                _text_primitive("title-a", (40.0, 50.0, 50.0, 60.0)),
                _text_primitive("title-b", (51.0, 50.0, 61.0, 60.0)),
            )
        )

        self.assertEqual(
            _fragment_ids(_build_local_horizontal_fragment_hypotheses(chain)),
            (("a", "b"), ("c",)),
        )
        self.assertEqual(
            _fragment_ids(_build_local_horizontal_fragment_hypotheses(title)),
            (("title-a", "title-b"),),
        )

    def test_does_not_connect_text_separated_like_boxes_or_ambiguous_choices(self) -> None:
        separated = _primitive_page(
            text_primitives=(
                _text_primitive("outside", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("box", (30.0, 50.0, 40.0, 60.0)),
                _text_primitive("other-box", (60.0, 50.0, 70.0, 60.0)),
            )
        )
        ambiguous = _primitive_page(
            text_primitives=(
                _text_primitive("left", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("choice-a", (11.0, 50.0, 21.0, 60.0)),
                _text_primitive("choice-b", (11.0, 50.0, 21.0, 60.0)),
            )
        )

        self.assertTrue(
            all(
                len(hypothesis.primitive_ids) == 1
                for hypothesis in _build_local_horizontal_fragment_hypotheses(separated)
            )
        )
        self.assertTrue(
            all(
                len(hypothesis.primitive_ids) == 1
                for hypothesis in _build_local_horizontal_fragment_hypotheses(ambiguous)
            )
        )

    def test_requires_common_vertical_corridor_and_total_gap_budget(self) -> None:
        incompatible_chain = _primitive_page(
            text_primitives=(
                _text_primitive("a", (0.0, 0.0, 10.0, 10.0)),
                _text_primitive("b", (11.0, 4.0, 21.0, 14.0)),
                _text_primitive("c", (22.0, 8.0, 32.0, 18.0)),
            )
        )
        excessive_budget = _primitive_page(
            text_primitives=(
                _text_primitive("a", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("b", (16.0, 50.0, 26.0, 60.0)),
                _text_primitive("c", (32.0, 50.0, 42.0, 60.0)),
                _text_primitive("d", (48.0, 50.0, 58.0, 60.0)),
            )
        )

        self.assertTrue(
            all(
                len(hypothesis.primitive_ids) == 1
                for hypothesis in _build_local_horizontal_fragment_hypotheses(incompatible_chain)
            )
        )
        self.assertTrue(
            all(
                len(hypothesis.primitive_ids) == 1
                for hypothesis in _build_local_horizontal_fragment_hypotheses(excessive_budget)
            )
        )

    def test_excludes_unsupported_or_invisible_text_and_does_not_change_producer(self) -> None:
        excluded = _primitive_page(
            text_primitives=(
                _text_primitive("vertical", (0.0, 50.0, 10.0, 60.0), direction=(0.0, 1.0)),
                _text_primitive(
                    "diagonal",
                    (11.0, 50.0, 21.0, 60.0),
                    direction=(0.7071067811865476, 0.7071067811865476),
                ),
                _text_primitive("outside", (110.0, 50.0, 120.0, 60.0)),
            )
        )
        singleton_page = _primitive_page(
            text_primitives=(
                _text_primitive("a", (0.0, 50.0, 10.0, 60.0)),
                _text_primitive("b", (11.0, 50.0, 21.0, 60.0)),
            )
        )

        self.assertEqual(_build_local_horizontal_fragment_hypotheses(excluded), ())
        analysis = build_singleton_side_band_page_analysis(singleton_page, generation_id="gen-1")
        self.assertEqual(
            _candidate_ids(analysis), ("candidate:side-band:a", "candidate:side-band:b")
        )
        self.assertEqual(analysis.provenance.configuration_id, "singleton-side-band-v1")
        self.assertEqual(analysis.provenance.producer_name, "page_analysis.singleton_side_band")


if __name__ == "__main__":
    unittest.main()
