from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import Any, cast

from capture_model import DrawingCommand
from geometry_model import PageGeometry
from page_analysis_side_band_measurements import (
    SideBandMeasurements,
    measure_horizontal_text_side_band_hypothesis,
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


class SideBandMeasurementsContractTest(unittest.TestCase):
    def test_constructs_valid_measurements(self) -> None:
        measurements = SideBandMeasurements(
            bbox=(10.0, 20.0, 30.0, 60.0),
            horizontal_center_ratio=0.2,
            nearest_vertical_edge_distance_ratio=0.1,
            width_ratio=0.2,
            height_ratio=0.2,
            primitive_count=1,
        )

        self.assertEqual(measurements.bbox, (10.0, 20.0, 30.0, 60.0))
        self.assertEqual(measurements.horizontal_center_ratio, 0.2)
        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.1)
        self.assertEqual(measurements.width_ratio, 0.2)
        self.assertEqual(measurements.height_ratio, 0.2)
        self.assertEqual(measurements.primitive_count, 1)

    def test_measurements_are_frozen_and_slotted(self) -> None:
        measurements = SideBandMeasurements(
            bbox=(10.0, 20.0, 30.0, 60.0),
            horizontal_center_ratio=0.2,
            nearest_vertical_edge_distance_ratio=0.1,
            width_ratio=0.2,
            height_ratio=0.2,
            primitive_count=1,
        )

        mutable_view = cast(Any, measurements)
        with self.assertRaises(FrozenInstanceError):
            mutable_view.primitive_count = 2
        self.assertFalse(hasattr(measurements, "__dict__"))

    def test_equivalent_measurements_are_equal(self) -> None:
        first = SideBandMeasurements(
            bbox=(10.0, 20.0, 30.0, 60.0),
            horizontal_center_ratio=0.2,
            nearest_vertical_edge_distance_ratio=0.1,
            width_ratio=0.2,
            height_ratio=0.2,
            primitive_count=1,
        )
        second = SideBandMeasurements(
            bbox=(10.0, 20.0, 30.0, 60.0),
            horizontal_center_ratio=0.2,
            nearest_vertical_edge_distance_ratio=0.1,
            width_ratio=0.2,
            height_ratio=0.2,
            primitive_count=1,
        )

        self.assertEqual(first, second)

    def test_float_values_are_not_rounded(self) -> None:
        measurements = SideBandMeasurements(
            bbox=(1.25, 2.5, 33.75, 44.125),
            horizontal_center_ratio=0.175,
            nearest_vertical_edge_distance_ratio=0.0125,
            width_ratio=0.325,
            height_ratio=0.208125,
            primitive_count=1,
        )

        self.assertEqual(measurements.bbox, (1.25, 2.5, 33.75, 44.125))
        self.assertEqual(measurements.height_ratio, 0.208125)


class MeasureHorizontalTextSideBandHypothesisTest(unittest.TestCase):
    def test_single_primitive_measurements_use_visible_bbox(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 20.0, 30.0, 60.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (10.0, 20.0, 30.0, 60.0))
        self.assertEqual(measurements.horizontal_center_ratio, 0.2)
        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.1)
        self.assertEqual(measurements.width_ratio, 0.2)
        self.assertEqual(measurements.height_ratio, 0.2)
        self.assertEqual(measurements.primitive_count, 1)

    def test_multiple_primitives_use_union_and_count(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (5.0, 50.0, 20.0, 70.0)),
            )
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1", "text-2"),
        )

        self.assertEqual(measurements.bbox, (5.0, 20.0, 30.0, 70.0))
        self.assertEqual(measurements.primitive_count, 2)
        self.assertEqual(measurements.horizontal_center_ratio, 0.175)
        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.05)
        self.assertEqual(measurements.width_ratio, 0.25)
        self.assertEqual(measurements.height_ratio, 0.25)

    def test_primitive_id_order_is_irrelevant(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (5.0, 50.0, 20.0, 70.0)),
            )
        )

        first = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1", "text-2"),
        )
        second = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-2", "text-1"),
        )

        self.assertEqual(first, second)

    def test_measurements_are_deterministic_between_repeated_calls(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (5.0, 50.0, 20.0, 70.0)),
            )
        )

        first = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1", "text-2"),
        )
        second = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1", "text-2"),
        )

        self.assertEqual(first, second)

    def test_clips_left_edge(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (-5.0, 10.0, 10.0, 20.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (0.0, 10.0, 10.0, 20.0))

    def test_clips_right_edge(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (90.0, 10.0, 110.0, 20.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (90.0, 10.0, 100.0, 20.0))

    def test_clips_top_edge(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, -5.0, 20.0, 10.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (10.0, 0.0, 20.0, 10.0))

    def test_clips_bottom_edge(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 190.0, 20.0, 210.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (10.0, 190.0, 20.0, 200.0))

    def test_unions_visible_portions_after_clipping(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("left", (-5.0, 10.0, 10.0, 20.0)),
                _text_primitive("right", (90.0, 190.0, 110.0, 210.0)),
            )
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("left", "right"),
        )

        self.assertEqual(measurements.bbox, (0.0, 10.0, 100.0, 200.0))

    def test_rejects_wrong_primitive_page_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            measure_horizontal_text_side_band_hypothesis(
                cast(Any, object()),
                primitive_ids=("text-1",),
            )

    def test_rejects_non_tuple_primitive_ids(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 10.0, 20.0, 20.0)),)
        )

        with self.assertRaisesRegex(ValueError, "primitive_ids"):
            measure_horizontal_text_side_band_hypothesis(
                page,
                primitive_ids=cast(Any, ["text-1"]),
            )

    def test_rejects_empty_primitive_ids(self) -> None:
        page = _primitive_page()

        with self.assertRaisesRegex(ValueError, "primitive_ids"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=())

    def test_rejects_empty_primitive_id(self) -> None:
        page = _primitive_page()

        with self.assertRaisesRegex(ValueError, "non-empty string"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("",))

    def test_rejects_duplicate_primitive_ids(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 10.0, 20.0, 20.0)),)
        )

        with self.assertRaisesRegex(ValueError, "duplicates"):
            measure_horizontal_text_side_band_hypothesis(
                page,
                primitive_ids=("text-1", "text-1"),
            )

    def test_rejects_missing_primitive_id(self) -> None:
        page = _primitive_page()

        with self.assertRaisesRegex(ValueError, "does not exist"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("missing",))

    def test_rejects_image_primitive_id(self) -> None:
        page = _primitive_page(image_primitives=(_image_primitive("image-1"),))

        with self.assertRaisesRegex(ValueError, "image primitive"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("image-1",))

    def test_rejects_drawing_primitive_id(self) -> None:
        page = _primitive_page(drawing_primitives=(_drawing_primitive("drawing-1"),))

        with self.assertRaisesRegex(ValueError, "drawing primitive"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("drawing-1",))

    def test_rejects_completely_off_page_primitive(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (110.0, 10.0, 120.0, 20.0)),)
        )

        with self.assertRaisesRegex(ValueError, "no visible intersection"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("text-1",))

    def test_rejects_group_containing_invisible_primitive(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("visible", (10.0, 10.0, 20.0, 20.0)),
                _text_primitive("invisible", (110.0, 10.0, 120.0, 20.0)),
            )
        )

        with self.assertRaisesRegex(ValueError, "invisible"):
            measure_horizontal_text_side_band_hypothesis(
                page,
                primitive_ids=("visible", "invisible"),
            )

    def test_accepts_direction_none(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 10.0, 20.0, 20.0), direction=None),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.primitive_count, 1)

    def test_accepts_rightward_horizontal_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 10.0, 20.0, 20.0), direction=(1.0, 0.0)),
            )
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.primitive_count, 1)

    def test_accepts_leftward_horizontal_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 10.0, 20.0, 20.0), direction=(-1.0, 0.0)),
            )
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.primitive_count, 1)

    def test_rejects_vertical_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 10.0, 20.0, 20.0), direction=(0.0, 1.0)),
            )
        )

        with self.assertRaisesRegex(ValueError, "unsupported orientation"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("text-1",))

    def test_rejects_diagonal_direction(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive(
                    "text-1",
                    (10.0, 10.0, 20.0, 20.0),
                    direction=(0.7071067811865476, 0.7071067811865476),
                ),
            )
        )

        with self.assertRaisesRegex(ValueError, "unsupported orientation"):
            measure_horizontal_text_side_band_hypothesis(page, primitive_ids=("text-1",))

    def test_rejects_mixed_horizontal_and_vertical_group(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("horizontal", (10.0, 10.0, 20.0, 20.0), direction=(1.0, 0.0)),
                _text_primitive("vertical", (30.0, 10.0, 40.0, 20.0), direction=(0.0, 1.0)),
            )
        )

        with self.assertRaisesRegex(ValueError, "unsupported orientation"):
            measure_horizontal_text_side_band_hypothesis(
                page,
                primitive_ids=("horizontal", "vertical"),
            )

    def test_left_edge_bbox_has_zero_nearest_edge_ratio(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (0.0, 10.0, 20.0, 20.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.0)

    def test_right_edge_bbox_has_zero_nearest_edge_ratio(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (80.0, 10.0, 100.0, 20.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.0)

    def test_central_bbox_has_positive_nearest_edge_ratio(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (40.0, 10.0, 60.0, 20.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertGreater(measurements.nearest_vertical_edge_distance_ratio, 0.0)
        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.4)

    def test_full_page_bbox_ratios(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (0.0, 0.0, 100.0, 200.0)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (0.0, 0.0, 100.0, 200.0))
        self.assertEqual(measurements.horizontal_center_ratio, 0.5)
        self.assertEqual(measurements.nearest_vertical_edge_distance_ratio, 0.0)
        self.assertEqual(measurements.width_ratio, 1.0)
        self.assertEqual(measurements.height_ratio, 1.0)

    def test_decimal_coordinates_are_preserved(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (1.25, 2.5, 33.75, 44.125)),)
        )

        measurements = measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-1",),
        )

        self.assertEqual(measurements.bbox, (1.25, 2.5, 33.75, 44.125))
        self.assertEqual(measurements.width_ratio, 0.325)
        self.assertEqual(measurements.height_ratio, 0.208125)

    def test_input_page_is_not_modified(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (5.0, 50.0, 20.0, 70.0)),
            )
        )
        before = page

        measure_horizontal_text_side_band_hypothesis(
            page,
            primitive_ids=("text-2", "text-1"),
        )

        self.assertEqual(page, before)
        self.assertEqual(page.text_primitives[0].primitive_id, "text-1")
        self.assertEqual(page.text_primitives[1].primitive_id, "text-2")


if __name__ == "__main__":
    unittest.main()
