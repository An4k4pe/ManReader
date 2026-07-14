from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, asdict

from geometry_model import PageGeometry
from page_analysis_candidate_page_context_measurements import (
    CandidatePageContextMeasurements,
    measure_candidate_page_context,
)
from page_analysis_model import RegionCandidate
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


def _candidate(
    primitive_ids: tuple[str, ...] = (),
    *,
    page_id: str = "page-1",
) -> RegionCandidate:
    return RegionCandidate(
        candidate_id="candidate-1",
        page_id=page_id,
        bbox=(10.0, 10.0, 20.0, 20.0),
        proposed_structural_kind="layout.side_band",
        primitive_ids=primitive_ids,
    )


def _direct_measurements(
    *,
    candidate_id: str = "candidate-1",
    page_id: str = "page-1",
    candidate_bbox: tuple[float, float, float, float] = (10.0, 10.0, 20.0, 20.0),
    candidate_primitive_ids: tuple[str, ...] = (),
    text_count: int = 0,
    text_extent: tuple[float, float, float, float] | None = None,
    image_count: int = 0,
    image_extent: tuple[float, float, float, float] | None = None,
    drawing_count: int = 0,
    drawing_extent: tuple[float, float, float, float] | None = None,
) -> CandidatePageContextMeasurements:
    return CandidatePageContextMeasurements(
        candidate_id=candidate_id,
        page_id=page_id,
        candidate_bbox=candidate_bbox,
        candidate_primitive_ids=candidate_primitive_ids,
        non_candidate_visible_text_primitive_count=text_count,
        non_candidate_visible_text_extent_bbox=text_extent,
        non_candidate_visible_image_primitive_count=image_count,
        non_candidate_visible_image_extent_bbox=image_extent,
        non_candidate_visible_drawing_primitive_count=drawing_count,
        non_candidate_visible_drawing_extent_bbox=drawing_extent,
    )


class CandidatePageContextMeasurementsTest(unittest.TestCase):
    def test_constructs_equality_immutability_and_slots(self) -> None:
        page = _page(text=(_text("text", (10.0, 10.0, 20.0, 20.0)),))

        measurements = measure_candidate_page_context(page, candidate=_candidate())
        duplicate = measure_candidate_page_context(page, candidate=_candidate())

        self.assertIsInstance(measurements, CandidatePageContextMeasurements)
        self.assertEqual(measurements, duplicate)
        self.assertFalse(hasattr(measurements, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            measurements.candidate_id = "changed"  # type: ignore[misc]

    def test_rejects_runtime_inputs_and_mismatched_page_id(self) -> None:
        page = _page()

        with self.assertRaisesRegex(ValueError, "primitive_page"):
            measure_candidate_page_context(object(), candidate=_candidate())  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "candidate"):
            measure_candidate_page_context(page, candidate=object())  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "page_id"):
            measure_candidate_page_context(page, candidate=_candidate(page_id="other-page"))

    def test_rejects_invalid_direct_construction(self) -> None:
        with self.subTest("empty candidate ID"), self.assertRaisesRegex(
            ValueError, "candidate_id"
        ):
            _direct_measurements(candidate_id="")
        with self.subTest("empty page ID"), self.assertRaisesRegex(ValueError, "page_id"):
            _direct_measurements(page_id="")
        with self.subTest("degenerate candidate bbox"), self.assertRaisesRegex(
            ValueError, "candidate_bbox"
        ):
            _direct_measurements(candidate_bbox=(10.0, 10.0, 10.0, 20.0))
        with self.subTest("empty candidate primitive ID"), self.assertRaisesRegex(
            ValueError, "candidate_primitive_ids"
        ):
            _direct_measurements(candidate_primitive_ids=("",))
        with self.subTest("duplicate candidate primitive IDs"), self.assertRaisesRegex(
            ValueError, "candidate_primitive_ids"
        ):
            _direct_measurements(candidate_primitive_ids=("item", "item"))
        with self.subTest("negative count"), self.assertRaisesRegex(
            ValueError, "text_primitive_count"
        ):
            _direct_measurements(text_count=-1)
        with self.subTest("bool count"), self.assertRaisesRegex(
            ValueError, "image_primitive_count"
        ):
            _direct_measurements(image_count=True)  # type: ignore[arg-type]
        with self.subTest("zero count with extent"), self.assertRaisesRegex(
            ValueError, "text_extent_bbox"
        ):
            _direct_measurements(text_extent=(10.0, 10.0, 20.0, 20.0))
        with self.subTest("positive count without extent"), self.assertRaisesRegex(
            ValueError, "image_extent_bbox"
        ):
            _direct_measurements(image_count=1)
        with self.subTest("degenerate extent"), self.assertRaisesRegex(
            ValueError, "drawing_extent_bbox"
        ):
            _direct_measurements(
                drawing_count=1,
                drawing_extent=(10.0, 10.0, 20.0, 10.0),
            )

    def test_rejects_missing_candidate_primitive_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_id.*missing"):
            measure_candidate_page_context(_page(), candidate=_candidate(("missing",)))

    def test_empty_candidate_counts_all_visible_families_separately(self) -> None:
        page = _page(
            text=(_text("text", (10.0, 20.0, 30.0, 40.0)),),
            images=(_image("image", (40.0, 50.0, 70.0, 90.0)),),
            drawings=(_drawing("drawing", (5.0, 6.0, 8.0, 9.0)),),
        )

        measurements = measure_candidate_page_context(page, candidate=_candidate())

        self.assertEqual(measurements.candidate_primitive_ids, ())
        self.assertEqual(measurements.non_candidate_visible_text_primitive_count, 1)
        self.assertEqual(measurements.non_candidate_visible_text_extent_bbox, (10.0, 20.0, 30.0, 40.0))
        self.assertEqual(measurements.non_candidate_visible_image_primitive_count, 1)
        self.assertEqual(measurements.non_candidate_visible_image_extent_bbox, (40.0, 50.0, 70.0, 90.0))
        self.assertEqual(measurements.non_candidate_visible_drawing_primitive_count, 1)
        self.assertEqual(measurements.non_candidate_visible_drawing_extent_bbox, (5.0, 6.0, 8.0, 9.0))

    def test_excludes_candidate_primitives_including_an_invisible_candidate(self) -> None:
        page = _page(
            text=(
                _text("candidate-visible", (0.0, 0.0, 10.0, 10.0)),
                _text("remaining", (30.0, 30.0, 40.0, 40.0)),
            ),
            images=(_image("candidate-invisible", (110.0, 0.0, 120.0, 10.0)),),
        )

        measurements = measure_candidate_page_context(
            page,
            candidate=_candidate(("candidate-visible", "candidate-invisible")),
        )

        self.assertEqual(measurements.non_candidate_visible_text_primitive_count, 1)
        self.assertEqual(measurements.non_candidate_visible_text_extent_bbox, (30.0, 30.0, 40.0, 40.0))
        self.assertEqual(measurements.non_candidate_visible_image_primitive_count, 0)
        self.assertIsNone(measurements.non_candidate_visible_image_extent_bbox)

    def test_ignores_invisible_non_candidate_primitives_and_clips_visible_extents(self) -> None:
        page = _page(
            text=(
                _text("partial-left", (-10.0, 10.0, 20.0, 30.0)),
                _text("invisible", (110.0, 10.0, 120.0, 20.0)),
                _text("partial-bottom", (50.0, 90.0, 120.0, 120.0)),
            ),
            images=(_image("partial-image", (90.0, -10.0, 120.0, 20.0)),),
        )

        measurements = measure_candidate_page_context(page, candidate=_candidate())

        self.assertEqual(measurements.non_candidate_visible_text_primitive_count, 2)
        self.assertEqual(measurements.non_candidate_visible_text_extent_bbox, (0.0, 10.0, 100.0, 100.0))
        self.assertEqual(measurements.non_candidate_visible_image_primitive_count, 1)
        self.assertEqual(measurements.non_candidate_visible_image_extent_bbox, (90.0, 0.0, 100.0, 20.0))

    def test_returns_zero_and_none_for_family_without_visible_primitives(self) -> None:
        page = _page(
            text=(_text("invisible-text", (101.0, 0.0, 110.0, 10.0)),),
            drawings=(_drawing("drawing", (10.0, 10.0, 20.0, 20.0)),),
        )

        measurements = measure_candidate_page_context(page, candidate=_candidate())

        self.assertEqual(measurements.non_candidate_visible_text_primitive_count, 0)
        self.assertIsNone(measurements.non_candidate_visible_text_extent_bbox)
        self.assertEqual(measurements.non_candidate_visible_image_primitive_count, 0)
        self.assertIsNone(measurements.non_candidate_visible_image_extent_bbox)
        self.assertEqual(measurements.non_candidate_visible_drawing_primitive_count, 1)

    def test_does_not_mutate_input_and_is_deterministic(self) -> None:
        page = _page(
            text=(_text("text", (-5.0, 10.0, 10.0, 20.0)),),
            images=(_image("image", (20.0, 20.0, 30.0, 30.0)),),
        )
        candidate = _candidate()
        page_before = asdict(page)
        candidate_before = asdict(candidate)

        first = measure_candidate_page_context(page, candidate=candidate)
        second = measure_candidate_page_context(page, candidate=candidate)

        self.assertEqual(first, second)
        self.assertEqual(asdict(page), page_before)
        self.assertEqual(asdict(candidate), candidate_before)


if __name__ == "__main__":
    unittest.main()
