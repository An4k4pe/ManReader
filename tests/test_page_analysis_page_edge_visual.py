from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
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


def _candidate_ids(page: NormalizedPrimitivePage) -> tuple[str, ...]:
    return tuple(
        candidate.candidate_id
        for candidate in build_page_edge_visual_page_analysis(
            page, generation_id="gen-1"
        ).candidates
    )


class BuildPageEdgeVisualPageAnalysisTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_page_edge_visual_page_analysis(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_page_edge_visual_page_analysis(_page(), generation_id="")

    def test_selects_top_image_and_bottom_drawing(self) -> None:
        page = _page(
            images=(_image("top", (0.0, 0.0, 80.0, 20.0)),),
            drawings=(_drawing("bottom", (20.0, 170.0, 100.0, 200.0)),),
        )

        self.assertEqual(
            _candidate_ids(page),
            (
                "candidate:page-edge-visual:bottom",
                "candidate:page-edge-visual:top",
            ),
        )

    def test_selects_left_image_and_right_drawing(self) -> None:
        page = _page(
            images=(_image("left", (0.0, 10.0, 10.0, 170.0)),),
            drawings=(_drawing("right", (90.0, 30.0, 100.0, 190.0)),),
        )

        self.assertEqual(
            _candidate_ids(page),
            (
                "candidate:page-edge-visual:left",
                "candidate:page-edge-visual:right",
            ),
        )

    def test_clips_before_applying_edge_ratios(self) -> None:
        page = _page(images=(_image("clipped", (-10.0, -10.0, 100.0, 30.0)),))

        analysis = build_page_edge_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(analysis.candidates[0].bbox, (0.0, 0.0, 100.0, 30.0))

    def test_ignores_text_central_full_page_and_thick_visuals(self) -> None:
        page = _page(
            text=(_text("text", (0.0, 0.0, 100.0, 200.0)),),
            images=(
                _image("central", (10.0, 11.0, 90.0, 31.0)),
                _image("full-page", (0.0, 0.0, 100.0, 200.0)),
            ),
            drawings=(_drawing("thick", (0.0, 0.0, 100.0, 40.0)),),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_ignores_completely_invisible_visuals(self) -> None:
        page = _page(
            images=(_image("outside-image", (110.0, 0.0, 120.0, 20.0)),),
            drawings=(_drawing("outside-drawing", (0.0, 210.0, 20.0, 220.0)),),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_contract_provenance_determinism_and_validation(self) -> None:
        page = _page(
            images=(_image("z-image", (0.0, 0.0, 80.0, 20.0)),),
            drawings=(_drawing("a-drawing", (90.0, 20.0, 100.0, 180.0)),),
        )

        first = build_page_edge_visual_page_analysis(page, generation_id="gen-1")
        second = build_page_edge_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(first, second)
        self.assertEqual(first.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(first.regions, ())
        self.assertEqual(first.relations, ())
        self.assertEqual(first.provenance.producer_name, "page_analysis.page_edge_visual")
        self.assertEqual(first.provenance.producer_version, "0.1")
        self.assertEqual(first.provenance.configuration_id, "page-edge-visual-v1")
        self.assertEqual(
            tuple(candidate.primitive_ids for candidate in first.candidates),
            (("a-drawing",), ("z-image",)),
        )
        self.assertTrue(
            all(
                candidate.proposed_structural_kind == "layout.page_edge_visual"
                for candidate in first.candidates
            )
        )
        validate_page_analysis_against_primitive_page(first, page)


if __name__ == "__main__":
    unittest.main()
