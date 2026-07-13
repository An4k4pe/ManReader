from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION
from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
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


def _text(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=primitive_id,
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
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=text,
        image_primitives=images,
        drawing_primitives=drawings,
    )


class BuildPageCoveringVisualPageAnalysisTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_page_covering_visual_page_analysis(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_page_covering_visual_page_analysis(_page(), generation_id="")

    def test_full_page_image_produces_candidate_with_expected_contract(self) -> None:
        page = _page(images=(_image("image", (0.0, 0.0, 100.0, 200.0)),))

        analysis = build_page_covering_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.regions, ())
        self.assertEqual(analysis.relations, ())
        self.assertEqual(len(analysis.candidates), 1)
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.candidate_id, "candidate:page-covering-visual:image")
        self.assertEqual(candidate.proposed_structural_kind, "layout.page_covering_visual")
        self.assertEqual(candidate.bbox, (0.0, 0.0, 100.0, 200.0))
        self.assertEqual(candidate.primitive_ids, ("image",))
        self.assertEqual(analysis.provenance.producer_name, "page_analysis.page_covering_visual")
        self.assertEqual(analysis.provenance.producer_version, "0.1")
        self.assertEqual(analysis.provenance.configuration_id, "page-covering-visual-v1")
        validate_page_analysis_against_primitive_page(analysis, page)

    def test_full_page_drawing_produces_candidate(self) -> None:
        page = _page(drawings=(_drawing("drawing", (0.0, 0.0, 100.0, 200.0)),))

        analysis = build_page_covering_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(
            tuple(candidate.candidate_id for candidate in analysis.candidates),
            ("candidate:page-covering-visual:drawing",),
        )

    def test_clips_partially_off_page_visual_before_selecting(self) -> None:
        page = _page(images=(_image("clipped", (-10.0, -10.0, 110.0, 210.0)),))

        analysis = build_page_covering_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(analysis.candidates[0].bbox, (0.0, 0.0, 100.0, 200.0))

    def test_ignores_completely_invisible_visual_primitives(self) -> None:
        page = _page(
            images=(_image("outside-image", (110.0, 0.0, 120.0, 10.0)),),
            drawings=(_drawing("outside-drawing", (0.0, 210.0, 10.0, 220.0)),),
        )

        self.assertEqual(
            build_page_covering_visual_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_rejects_non_page_covering_visual_shapes(self) -> None:
        page = _page(
            images=(_image("central", (5.0, 10.0, 95.0, 190.0)),),
            drawings=(
                _drawing("header", (0.0, 0.0, 100.0, 30.0)),
                _drawing("footer", (0.0, 170.0, 100.0, 200.0)),
            ),
        )

        self.assertEqual(
            build_page_covering_visual_page_analysis(page, generation_id="gen-1").candidates,
            (),
        )

    def test_ignores_full_page_text_and_is_deterministic(self) -> None:
        page = _page(
            text=(_text("text", (0.0, 0.0, 100.0, 200.0)),),
            images=(_image("z-image", (0.0, 0.0, 100.0, 200.0)),),
            drawings=(_drawing("a-drawing", (0.0, 0.0, 100.0, 200.0)),),
        )

        first = build_page_covering_visual_page_analysis(page, generation_id="gen-1")
        second = build_page_covering_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in first.candidates),
            (
                "candidate:page-covering-visual:a-drawing",
                "candidate:page-covering-visual:z-image",
            ),
        )
        self.assertTrue(
            all(candidate.primitive_ids != ("text",) for candidate in first.candidates)
        )


if __name__ == "__main__":
    unittest.main()
