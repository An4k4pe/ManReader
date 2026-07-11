from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import Any, cast

from capture_model import DrawingCommand
from geometry_model import PageGeometry
from page_analysis_text_hypotheses import (
    GeometricTextHypothesis,
    build_geometric_text_hypotheses,
)
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


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


def _image_primitive(primitive_id: str) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=(10.0, 10.0, 20.0, 20.0),
        source_observation_id=f"obs:{primitive_id}",
    )


def _drawing_primitive(primitive_id: str) -> DrawingPrimitive:
    return DrawingPrimitive(
        primitive_id=primitive_id,
        bbox=(10.0, 10.0, 20.0, 20.0),
        source_observation_id=f"obs:{primitive_id}",
        commands=(DrawingCommand(kind="line", points=((10.0, 10.0), (20.0, 20.0))),),
    )


def _primitive_page(
    *,
    text_primitives: tuple[TextPrimitive, ...] = (),
    image_primitives: tuple[ImageOccurrencePrimitive, ...] = (),
    drawing_primitives: tuple[DrawingPrimitive, ...] = (),
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
        image_primitives=image_primitives,
        drawing_primitives=drawing_primitives,
    )


def _ids(hypotheses: tuple[GeometricTextHypothesis, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(hypothesis.primitive_ids for hypothesis in hypotheses)


class GeometricTextHypothesisContractTest(unittest.TestCase):
    def test_constructs_with_single_id(self) -> None:
        hypothesis = GeometricTextHypothesis(primitive_ids=("text-1",))

        self.assertEqual(hypothesis.primitive_ids, ("text-1",))

    def test_constructs_with_multiple_ids(self) -> None:
        hypothesis = GeometricTextHypothesis(primitive_ids=("text-1", "text-2"))

        self.assertEqual(hypothesis.primitive_ids, ("text-1", "text-2"))

    def test_hypothesis_is_frozen_and_slotted(self) -> None:
        hypothesis = GeometricTextHypothesis(primitive_ids=("text-1",))
        mutable_view = cast(Any, hypothesis)

        with self.assertRaises(FrozenInstanceError):
            mutable_view.primitive_ids = ("text-2",)
        self.assertFalse(hasattr(hypothesis, "__dict__"))

    def test_equivalent_hypotheses_are_equal(self) -> None:
        self.assertEqual(
            GeometricTextHypothesis(primitive_ids=("text-1",)),
            GeometricTextHypothesis(primitive_ids=("text-1",)),
        )

    def test_rejects_non_tuple_primitive_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_ids"):
            GeometricTextHypothesis(primitive_ids=cast(Any, ["text-1"]))

    def test_rejects_empty_primitive_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_ids"):
            GeometricTextHypothesis(primitive_ids=())

    def test_rejects_empty_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            GeometricTextHypothesis(primitive_ids=("",))

    def test_rejects_non_string_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            GeometricTextHypothesis(primitive_ids=cast(Any, (123,)))

    def test_rejects_duplicate_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            GeometricTextHypothesis(primitive_ids=("text-1", "text-1"))


class BuildGeometricTextHypothesesInputTest(unittest.TestCase):
    def test_rejects_wrong_primitive_page_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_geometric_text_hypotheses(cast(Any, object()))

    def test_page_without_text_produces_empty_tuple(self) -> None:
        self.assertEqual(build_geometric_text_hypotheses(_primitive_page()), ())

    def test_images_without_text_produce_empty_tuple(self) -> None:
        page = _primitive_page(image_primitives=(_image_primitive("image-1"),))

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_drawings_without_text_produce_empty_tuple(self) -> None:
        page = _primitive_page(drawing_primitives=(_drawing_primitive("drawing-1"),))

        self.assertEqual(build_geometric_text_hypotheses(page), ())


class BuildGeometricTextHypothesesSingletonTest(unittest.TestCase):
    def test_one_admissible_primitive_produces_one_hypothesis(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 10.0, 20.0, 20.0)),)
        )

        hypotheses = build_geometric_text_hypotheses(page)

        self.assertEqual(_ids(hypotheses), (("text-1",),))

    def test_multiple_admissible_primitives_produce_one_hypothesis_each(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("text-2", (30.0, 10.0, 40.0, 20.0)),
            )
        )

        hypotheses = build_geometric_text_hypotheses(page)

        self.assertEqual(_ids(hypotheses), (("text-1",), ("text-2",)))
        self.assertTrue(all(len(hypothesis.primitive_ids) == 1 for hypothesis in hypotheses))

    def test_nearby_primitives_remain_separate(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("b", (20.1, 10.0, 30.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("a",), ("b",)))

    def test_overlapping_primitives_remain_separate(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("a", (10.0, 10.0, 30.0, 30.0)),
                _text_primitive("b", (20.0, 20.0, 40.0, 40.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("a",), ("b",)))

    def test_abc_chain_does_not_merge_or_group(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("b", (21.0, 10.0, 31.0, 20.0)),
                _text_primitive("c", (32.0, 10.0, 42.0, 20.0)),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("a",), ("b",), ("c",)),
        )


class BuildGeometricTextHypothesesOrientationTest(unittest.TestCase):
    def test_includes_direction_none(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("none", (10.0, 10.0, 20.0, 20.0), direction=None),)
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("none",),))

    def test_includes_rightward_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("right", (10.0, 10.0, 20.0, 20.0), direction=(1.0, 0.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("right",),))

    def test_includes_leftward_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("left", (10.0, 10.0, 20.0, 20.0), direction=(-1.0, 0.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("left",),))

    def test_includes_values_within_tolerance(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive(
                    "near-right",
                    (10.0, 10.0, 20.0, 20.0),
                    direction=(0.999999999999995, 0.0000001),
                ),
                _text_primitive(
                    "near-left",
                    (30.0, 10.0, 40.0, 20.0),
                    direction=(-0.999999999999995, -0.0000001),
                ),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("near-right",), ("near-left",)),
        )

    def test_excludes_vertical_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("vertical", (10.0, 10.0, 20.0, 20.0), direction=(0.0, 1.0)),
            )
        )

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_excludes_diagonal_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive(
                    "diagonal",
                    (10.0, 10.0, 20.0, 20.0),
                    direction=(0.7071067811865476, 0.7071067811865476),
                ),
            )
        )

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_excludes_values_beyond_tolerance(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive(
                    "almost-horizontal",
                    (10.0, 10.0, 20.0, 20.0),
                    direction=(0.999999999998, 0.000002),
                ),
            )
        )

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_mixed_page_produces_only_supported_primitives(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("none", (10.0, 10.0, 20.0, 20.0), direction=None),
                _text_primitive("vertical", (30.0, 10.0, 40.0, 20.0), direction=(0.0, 1.0)),
                _text_primitive("right", (50.0, 10.0, 60.0, 20.0), direction=(1.0, 0.0)),
                _text_primitive(
                    "diagonal",
                    (70.0, 10.0, 80.0, 20.0),
                    direction=(0.7071067811865476, 0.7071067811865476),
                ),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("none",), ("right",)),
        )


class BuildGeometricTextHypothesesVisibilityTest(unittest.TestCase):
    def test_includes_primitive_completely_inside_page(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("inside", (10.0, 10.0, 20.0, 20.0)),)
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("inside",),))

    def test_includes_partially_outside_left(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("left", (-5.0, 10.0, 10.0, 20.0)),))

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("left",),))

    def test_includes_partially_outside_right(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("right", (90.0, 10.0, 110.0, 20.0)),)
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("right",),))

    def test_includes_partially_outside_top(self) -> None:
        page = _primitive_page(text_primitives=(_text_primitive("top", (10.0, -5.0, 20.0, 10.0)),))

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("top",),))

    def test_includes_partially_outside_bottom(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("bottom", (10.0, 190.0, 20.0, 210.0)),)
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("bottom",),))

    def test_ignores_completely_outside_page(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("outside", (110.0, 10.0, 120.0, 20.0)),)
        )

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_ignores_bbox_touching_edge_without_positive_area(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("left-edge", (-10.0, 10.0, 0.0, 20.0)),
                _text_primitive("right-edge", (100.0, 10.0, 110.0, 20.0)),
                _text_primitive("top-edge", (10.0, -10.0, 20.0, 0.0)),
                _text_primitive("bottom-edge", (10.0, 200.0, 20.0, 210.0)),
            )
        )

        self.assertEqual(build_geometric_text_hypotheses(page), ())

    def test_mixed_visible_and_invisible_page_includes_only_visible(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("visible", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("invisible", (110.0, 10.0, 120.0, 20.0)),
                _text_primitive("partial", (-5.0, 30.0, 10.0, 40.0)),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("visible",), ("partial",)),
        )


class BuildGeometricTextHypothesesOrderingTest(unittest.TestCase):
    def test_orders_by_y0(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("second", (10.0, 20.0, 20.0, 30.0)),
                _text_primitive("first", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("first",), ("second",)))

    def test_tie_breaks_by_x0(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("right", (20.0, 10.0, 30.0, 20.0)),
                _text_primitive("left", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("left",), ("right",)))

    def test_tie_breaks_by_y1(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("taller", (10.0, 10.0, 20.0, 30.0)),
                _text_primitive("shorter", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("shorter",), ("taller",)))

    def test_tie_breaks_by_x1(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("wider", (10.0, 10.0, 30.0, 20.0)),
                _text_primitive("narrower", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("narrower",), ("wider",)))

    def test_tie_breaks_by_primitive_id(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("b", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(_ids(build_geometric_text_hypotheses(page)), (("a",), ("b",)))

    def test_output_is_same_with_reversed_input_order(self) -> None:
        first_page = _primitive_page(
            text_primitives=(
                _text_primitive("b", (20.0, 20.0, 30.0, 30.0)),
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
            )
        )
        reversed_page = _primitive_page(text_primitives=tuple(reversed(first_page.text_primitives)))

        self.assertEqual(
            build_geometric_text_hypotheses(first_page),
            build_geometric_text_hypotheses(reversed_page),
        )

    def test_repeated_calls_produce_same_output(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("b", (20.0, 20.0, 30.0, 30.0)),
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
            )
        )

        self.assertEqual(
            build_geometric_text_hypotheses(page),
            build_geometric_text_hypotheses(page),
        )

    def test_order_uses_clipped_visible_bbox(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("clipped-first", (10.0, -10.0, 20.0, 10.0)),
                _text_primitive("inside-second", (10.0, 1.0, 20.0, 10.0)),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("clipped-first",), ("inside-second",)),
        )

    def test_canonical_order_is_not_backend_or_reading_order(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("backend-first-reading-left", (10.0, 50.0, 20.0, 60.0)),
                _text_primitive("canonical-first-reading-right", (80.0, 10.0, 90.0, 20.0)),
            )
        )

        self.assertEqual(
            _ids(build_geometric_text_hypotheses(page)),
            (("canonical-first-reading-right",), ("backend-first-reading-left",)),
        )


class BuildGeometricTextHypothesesImmutabilityTest(unittest.TestCase):
    def test_input_page_and_primitives_are_not_modified(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("b", (20.0, 20.0, 30.0, 30.0)),
                _text_primitive("a", (10.0, 10.0, 20.0, 20.0)),
            )
        )
        before = page
        original_order = tuple(primitive.primitive_id for primitive in page.text_primitives)
        original_primitives = page.text_primitives

        build_geometric_text_hypotheses(page)

        self.assertEqual(page, before)
        self.assertEqual(
            tuple(primitive.primitive_id for primitive in page.text_primitives), original_order
        )
        self.assertEqual(page.text_primitives, original_primitives)


if __name__ == "__main__":
    unittest.main()
