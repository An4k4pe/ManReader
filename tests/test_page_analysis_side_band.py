from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION, PageAnalysis
from page_analysis_side_band import build_singleton_side_band_page_analysis
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


if __name__ == "__main__":
    unittest.main()
