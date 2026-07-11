from __future__ import annotations

import unittest
from typing import Any, cast

from capture_model import DrawingCommand
from geometry_model import PageGeometry
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_side_band_candidate import (
    build_side_band_candidate_from_text_hypothesis,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page
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


def _provenance(page: NormalizedPrimitivePage) -> PageAnalysisProvenance:
    return PageAnalysisProvenance(
        source_id=page.source_id,
        source_capture_id=page.source_capture_id,
        source_page_id=page.page_id,
        source_primitive_schema_version=page.schema_version,
        producer_name="test-producer",
        producer_version="0.1",
        configuration_id="test-v1",
    )


class BuildSideBandCandidateFromTextHypothesisTest(unittest.TestCase):
    def test_builds_candidate_from_single_text_primitive(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),)
        )

        candidate = build_side_band_candidate_from_text_hypothesis(
            page,
            candidate_id="candidate:1",
            primitive_ids=("text-1",),
        )

        self.assertIsInstance(candidate, RegionCandidate)
        self.assertEqual(candidate.bbox, (10.0, 20.0, 30.0, 40.0))
        self.assertEqual(candidate.page_id, page.page_id)
        self.assertEqual(candidate.proposed_structural_kind, "layout.side_band")
        self.assertEqual(candidate.primitive_ids, ("text-1",))

    def test_uses_aggregated_visible_bbox_for_multiple_primitives(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (-5.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (50.0, 60.0, 120.0, 90.0)),
            )
        )

        candidate = build_side_band_candidate_from_text_hypothesis(
            page,
            candidate_id="candidate:1",
            primitive_ids=("text-2", "text-1"),
        )

        self.assertEqual(candidate.bbox, (0.0, 20.0, 100.0, 90.0))
        self.assertEqual(candidate.primitive_ids, ("text-2", "text-1"))

    def test_rejects_empty_candidate_id(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),)
        )

        with self.assertRaisesRegex(ValueError, "candidate_id"):
            build_side_band_candidate_from_text_hypothesis(
                page,
                candidate_id="",
                primitive_ids=("text-1",),
            )

    def test_rejects_wrong_primitive_page_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_side_band_candidate_from_text_hypothesis(
                cast(Any, object()),
                candidate_id="candidate:1",
                primitive_ids=("text-1",),
            )

    def test_propagates_empty_primitive_ids_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_ids"):
            build_side_band_candidate_from_text_hypothesis(
                _primitive_page(),
                candidate_id="candidate:1",
                primitive_ids=(),
            )

    def test_propagates_missing_primitive_id_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            build_side_band_candidate_from_text_hypothesis(
                _primitive_page(),
                candidate_id="candidate:1",
                primitive_ids=("missing",),
            )

    def test_propagates_image_and_drawing_primitive_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "image primitive"):
            build_side_band_candidate_from_text_hypothesis(
                _primitive_page(image_primitives=(_image_primitive("image-1"),)),
                candidate_id="candidate:image",
                primitive_ids=("image-1",),
            )
        with self.assertRaisesRegex(ValueError, "drawing primitive"):
            build_side_band_candidate_from_text_hypothesis(
                _primitive_page(drawing_primitives=(_drawing_primitive("drawing-1"),)),
                candidate_id="candidate:drawing",
                primitive_ids=("drawing-1",),
            )

    def test_propagates_unsupported_orientation_errors(self) -> None:
        for direction in ((0.0, 1.0), (0.7071067811865476, 0.7071067811865476)):
            with (
                self.subTest(direction=direction),
                self.assertRaisesRegex(ValueError, "unsupported orientation"),
            ):
                build_side_band_candidate_from_text_hypothesis(
                    _primitive_page(
                        text_primitives=(
                            _text_primitive(
                                "text-1", (10.0, 20.0, 30.0, 40.0), direction=direction
                            ),
                        )
                    ),
                    candidate_id="candidate:1",
                    primitive_ids=("text-1",),
                )

    def test_propagates_invisible_primitive_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "no visible intersection"):
            build_side_band_candidate_from_text_hypothesis(
                _primitive_page(
                    text_primitives=(_text_primitive("text-1", (110.0, 20.0, 120.0, 40.0)),)
                ),
                candidate_id="candidate:1",
                primitive_ids=("text-1",),
            )

    def test_does_not_modify_input_page(self) -> None:
        page = _primitive_page(
            text_primitives=(
                _text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),
                _text_primitive("text-2", (50.0, 60.0, 70.0, 80.0)),
            )
        )
        before = page

        build_side_band_candidate_from_text_hypothesis(
            page,
            candidate_id="candidate:1",
            primitive_ids=("text-2", "text-1"),
        )

        self.assertEqual(page, before)
        self.assertEqual(
            tuple(primitive.primitive_id for primitive in page.text_primitives),
            ("text-1", "text-2"),
        )

    def test_candidate_validates_in_minimal_page_analysis(self) -> None:
        page = _primitive_page(
            text_primitives=(_text_primitive("text-1", (10.0, 20.0, 30.0, 40.0)),)
        )
        candidate = build_side_band_candidate_from_text_hypothesis(
            page,
            candidate_id="candidate:1",
            primitive_ids=("text-1",),
        )
        analysis = PageAnalysis(
            schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
            generation_id="generation:1",
            page_id=page.page_id,
            provenance=_provenance(page),
            candidates=(candidate,),
        )

        validate_page_analysis_against_primitive_page(analysis, page)
        self.assertEqual(analysis.schema_version, "1.2")


if __name__ == "__main__":
    unittest.main()
