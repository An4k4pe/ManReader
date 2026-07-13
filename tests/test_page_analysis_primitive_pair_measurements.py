from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError, asdict
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_primitive_pair_measurements import (
    PrimitivePairMeasurements,
    measure_primitive_pair,
)
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


def _text(primitive_id: str, bbox: tuple[float, float, float, float]) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=primitive_id,
        source_observation_id=f"obs:{primitive_id}",
    )


def _image(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _drawing(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> DrawingPrimitive:
    return DrawingPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _page(
    *,
    text: tuple[TextPrimitive, ...] = (),
    images: tuple[ImageOccurrencePrimitive, ...] = (),
    drawings: tuple[DrawingPrimitive, ...] = (),
) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
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
        text_primitives=text,
        image_primitives=images,
        drawing_primitives=drawings,
    )


class PrimitivePairMeasurementsContractTest(unittest.TestCase):
    def test_constructs_equality_immutability_and_slots(self) -> None:
        page = _page(
            text=(
                _text("first", (10.0, 10.0, 20.0, 20.0)),
                _text("second", (20.0, 10.0, 30.0, 20.0)),
            )
        )
        measured = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )
        constructed = PrimitivePairMeasurements(**asdict(measured))

        self.assertEqual(constructed, measured)
        self.assertEqual(constructed.first_primitive_kind, "text")
        self.assertFalse(hasattr(constructed, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            cast(Any, constructed).horizontal_gap = 1.0

    def test_rejects_invalid_direct_construction(self) -> None:
        page = _page(
            text=(
                _text("first", (10.0, 10.0, 20.0, 20.0)),
                _text("second", (20.0, 10.0, 30.0, 20.0)),
            )
        )
        valid_values = asdict(
            measure_primitive_pair(
                page,
                first_primitive_id="first",
                second_primitive_id="second",
            )
        )

        for field_name, invalid_value, error in (
            ("first_primitive_id", "", "first_primitive_id"),
            ("first_primitive_kind", "other", "first_primitive_kind"),
            ("first_visible_bbox", (10.0, 10.0, 10.0, 20.0), "non-degenerate"),
            ("horizontal_overlap_ratio", 1.1, "horizontal_overlap_ratio"),
            ("touches", 1, "touches"),
            ("center_x_delta", math.inf, "center_x_delta"),
            ("first_bbox", (20.0, 10.0, 10.0, 20.0), "inverted"),
        ):
            with self.subTest(field_name=field_name):
                values = {**valid_values, field_name: invalid_value}
                with self.assertRaisesRegex(ValueError, error):
                    PrimitivePairMeasurements(**values)


class MeasurePrimitivePairTest(unittest.TestCase):
    def test_resolves_all_supported_kind_combinations(self) -> None:
        page = _page(
            text=(
                _text("text-a", (0.0, 0.0, 10.0, 10.0)),
                _text("text-b", (20.0, 0.0, 30.0, 10.0)),
            ),
            images=(
                _image("image-a", (40.0, 0.0, 50.0, 10.0)),
                _image("image-b", (60.0, 0.0, 70.0, 10.0)),
            ),
            drawings=(
                _drawing("drawing-a", (0.0, 20.0, 10.0, 30.0)),
                _drawing("drawing-b", (20.0, 20.0, 30.0, 30.0)),
            ),
        )

        for first_id, second_id, first_kind, second_kind in (
            ("text-a", "text-b", "text", "text"),
            ("text-a", "image-a", "text", "image"),
            ("text-a", "drawing-a", "text", "drawing"),
            ("image-a", "image-b", "image", "image"),
            ("image-a", "drawing-a", "image", "drawing"),
            ("drawing-a", "drawing-b", "drawing", "drawing"),
        ):
            with self.subTest(first_id=first_id, second_id=second_id):
                measurements = measure_primitive_pair(
                    page,
                    first_primitive_id=first_id,
                    second_primitive_id=second_id,
                )
                self.assertEqual(measurements.first_primitive_kind, first_kind)
                self.assertEqual(measurements.second_primitive_kind, second_kind)

    def test_rejects_wrong_page_missing_and_equal_ids(self) -> None:
        page = _page(text=(_text("text", (0.0, 0.0, 10.0, 10.0)),))

        with self.assertRaisesRegex(ValueError, "primitive_page"):
            measure_primitive_pair(
                cast(Any, object()),
                first_primitive_id="text",
                second_primitive_id="other",
            )
        with self.assertRaisesRegex(ValueError, "does not exist"):
            measure_primitive_pair(page, first_primitive_id="text", second_primitive_id="missing")
        with self.assertRaisesRegex(ValueError, "must differ"):
            measure_primitive_pair(page, first_primitive_id="text", second_primitive_id="text")

    def test_uses_original_and_clipped_visible_bboxes(self) -> None:
        page = _page(
            text=(_text("first", (-10.0, -5.0, 20.0, 20.0)),),
            images=(_image("second", (90.0, 80.0, 110.0, 120.0)),),
        )

        measurements = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(measurements.first_bbox, (-10.0, -5.0, 20.0, 20.0))
        self.assertEqual(measurements.second_bbox, (90.0, 80.0, 110.0, 120.0))
        self.assertEqual(measurements.first_visible_bbox, (0.0, 0.0, 20.0, 20.0))
        self.assertEqual(measurements.second_visible_bbox, (90.0, 80.0, 100.0, 100.0))

    def test_rejects_completely_invisible_primitive(self) -> None:
        page = _page(
            text=(_text("visible", (0.0, 0.0, 10.0, 10.0)),),
            drawings=(_drawing("invisible", (110.0, 0.0, 120.0, 10.0)),),
        )

        with self.assertRaisesRegex(ValueError, "no visible intersection"):
            measure_primitive_pair(
                page,
                first_primitive_id="visible",
                second_primitive_id="invisible",
            )

    def test_disjoint_gaps_distances_and_edge_deltas(self) -> None:
        page = _page(
            text=(_text("first", (10.0, 20.0, 30.0, 40.0)),),
            images=(_image("second", (50.0, 60.0, 80.0, 90.0)),),
        )

        measurements = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(measurements.horizontal_gap, 20.0)
        self.assertEqual(measurements.vertical_gap, 20.0)
        self.assertEqual(measurements.horizontal_overlap, 0.0)
        self.assertEqual(measurements.vertical_overlap, 0.0)
        self.assertEqual(measurements.horizontal_overlap_ratio, 0.0)
        self.assertEqual(measurements.vertical_overlap_ratio, 0.0)
        self.assertTrue(measurements.is_disjoint)
        self.assertFalse(measurements.touches)
        self.assertFalse(measurements.intersects)
        self.assertEqual(measurements.first_page_left_distance, 10.0)
        self.assertEqual(measurements.first_page_right_distance, 70.0)
        self.assertEqual(measurements.first_page_top_distance, 20.0)
        self.assertEqual(measurements.first_page_bottom_distance, 60.0)
        self.assertEqual(measurements.second_page_left_distance, 50.0)
        self.assertEqual(measurements.second_page_right_distance, 20.0)
        self.assertEqual(measurements.second_page_top_distance, 60.0)
        self.assertEqual(measurements.second_page_bottom_distance, 10.0)
        self.assertEqual(measurements.left_edge_delta, 40.0)
        self.assertEqual(measurements.right_edge_delta, 50.0)
        self.assertEqual(measurements.top_edge_delta, 40.0)
        self.assertEqual(measurements.bottom_edge_delta, 50.0)
        self.assertEqual(measurements.center_x_delta, 45.0)
        self.assertEqual(measurements.center_y_delta, 45.0)

    def test_touching_has_zero_overlaps_and_is_not_disjoint(self) -> None:
        page = _page(
            text=(_text("first", (10.0, 10.0, 20.0, 20.0)),),
            images=(_image("second", (20.0, 20.0, 30.0, 30.0)),),
        )

        measurements = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(measurements.horizontal_gap, 0.0)
        self.assertEqual(measurements.vertical_gap, 0.0)
        self.assertEqual(measurements.horizontal_overlap, 0.0)
        self.assertEqual(measurements.vertical_overlap, 0.0)
        self.assertTrue(measurements.touches)
        self.assertFalse(measurements.is_disjoint)
        self.assertFalse(measurements.intersects)

    def test_overlap_on_one_axis_is_disjoint(self) -> None:
        page = _page(
            text=(_text("first", (10.0, 10.0, 30.0, 20.0)),),
            drawings=(_drawing("second", (20.0, 30.0, 40.0, 40.0)),),
        )

        measurements = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(measurements.horizontal_overlap, 10.0)
        self.assertEqual(measurements.vertical_gap, 10.0)
        self.assertTrue(measurements.is_disjoint)
        self.assertFalse(measurements.touches)
        self.assertFalse(measurements.intersects)

    def test_positive_area_intersection_and_overlap_ratios(self) -> None:
        page = _page(
            text=(_text("first", (10.0, 10.0, 30.0, 30.0)),),
            images=(_image("second", (20.0, 15.0, 40.0, 25.0)),),
        )

        measurements = measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(measurements.horizontal_overlap, 10.0)
        self.assertEqual(measurements.vertical_overlap, 10.0)
        self.assertEqual(measurements.horizontal_overlap_ratio, 0.5)
        self.assertEqual(measurements.vertical_overlap_ratio, 1.0)
        self.assertTrue(measurements.intersects)
        self.assertFalse(measurements.touches)
        self.assertFalse(measurements.is_disjoint)

    def test_containment_and_identical_bboxes_are_inclusive(self) -> None:
        page = _page(
            text=(
                _text("outer", (10.0, 10.0, 50.0, 50.0)),
                _text("inner", (20.0, 20.0, 30.0, 30.0)),
                _text("same", (10.0, 10.0, 50.0, 50.0)),
            )
        )

        outer_inner = measure_primitive_pair(
            page,
            first_primitive_id="outer",
            second_primitive_id="inner",
        )
        outer_same = measure_primitive_pair(
            page,
            first_primitive_id="outer",
            second_primitive_id="same",
        )

        self.assertTrue(outer_inner.first_contains_second)
        self.assertFalse(outer_inner.second_contains_first)
        self.assertTrue(outer_same.first_contains_second)
        self.assertTrue(outer_same.second_contains_first)

    def test_does_not_modify_input_page(self) -> None:
        page = _page(
            text=(_text("first", (10.0, 10.0, 20.0, 20.0)),),
            images=(_image("second", (30.0, 30.0, 40.0, 40.0)),),
        )
        before = page

        measure_primitive_pair(
            page,
            first_primitive_id="first",
            second_primitive_id="second",
        )

        self.assertEqual(page, before)


if __name__ == "__main__":
    unittest.main()
