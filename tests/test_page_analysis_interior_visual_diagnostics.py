from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_interior_visual_diagnostics import dump_interior_visual_diagnostics
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


def _image(
    primitive_id: str,
    bbox: tuple[float, float, float, float],
    *,
    content_digest: str | None = None,
) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
        content_digest=content_digest,
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


def _visual(result: dict[str, object], primitive_id: str) -> dict[str, object]:
    return next(
        cast(dict[str, object], visual)
        for visual in cast(list[object], result["visuals"])
        if cast(dict[str, object], visual)["primitive_id"] == primitive_id
    )


class DumpInteriorVisualDiagnosticsTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_interior_visual_diagnostics(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            dump_interior_visual_diagnostics(_page(), generation_id="")

    def test_flags_bbox_outside_covering_and_edge_thresholds_as_residual(self) -> None:
        page = _page(
            images=(_image("wide-central", (5.0, 10.0, 95.0, 190.0)),),
            drawings=(_drawing("near-top-not-touching", (10.0, 11.0, 90.0, 31.0)),),
        )

        result = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        for primitive_id in ("wide-central", "near-top-not-touching"):
            visual = _visual(result, primitive_id)
            self.assertFalse(visual["is_page_covering_visual"])
            self.assertFalse(visual["is_page_edge_visual"])
            self.assertTrue(visual["is_residual_interior_visual"])

    def test_does_not_flag_covering_or_edge_visuals_as_residual(self) -> None:
        page = _page(
            images=(_image("full-page", (0.0, 0.0, 100.0, 200.0)),),
            drawings=(_drawing("edge", (0.0, 0.0, 80.0, 20.0)),),
        )

        result = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        covering = _visual(result, "full-page")
        self.assertTrue(covering["is_page_covering_visual"])
        self.assertFalse(covering["is_residual_interior_visual"])

        edge = _visual(result, "edge")
        self.assertTrue(edge["is_page_edge_visual"])
        self.assertFalse(edge["is_residual_interior_visual"])

    def test_completely_invisible_primitive_has_null_geometry(self) -> None:
        page = _page(images=(_image("outside", (110.0, 0.0, 120.0, 20.0)),))

        result = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        visual = _visual(result, "outside")
        self.assertIsNone(visual["visible_bbox"])
        self.assertFalse(visual["is_page_covering_visual"])
        self.assertFalse(visual["is_page_edge_visual"])
        self.assertFalse(visual["is_residual_interior_visual"])
        self.assertEqual(visual["contained_text_primitive_count"], 0)
        self.assertIsNone(visual["contained_text_area_ratio"])

    def test_counts_and_measures_fully_contained_text(self) -> None:
        page = _page(
            text=(
                _text("inside-a", (20.0, 20.0, 40.0, 30.0)),
                _text("inside-b", (50.0, 20.0, 70.0, 30.0)),
            ),
            images=(_image("box", (10.0, 10.0, 90.0, 90.0)),),
        )

        result = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        visual = _visual(result, "box")
        self.assertEqual(visual["contained_text_primitive_count"], 2)
        # (20*10 + 20*10) / (80*80) == 400 / 6400
        self.assertAlmostEqual(cast(float, visual["contained_text_area_ratio"]), 400.0 / 6400.0)

    def test_ignores_text_that_only_overlaps_without_containment(self) -> None:
        page = _page(
            text=(_text("spilling-over", (85.0, 85.0, 105.0, 95.0)),),
            images=(_image("box", (10.0, 10.0, 90.0, 90.0)),),
        )

        result = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        visual = _visual(result, "box")
        self.assertEqual(visual["contained_text_primitive_count"], 0)
        self.assertIsNone(visual["contained_text_area_ratio"])

    def test_is_deterministic(self) -> None:
        page = _page(
            images=(_image("wide-central", (5.0, 10.0, 95.0, 190.0)),),
        )

        first = dump_interior_visual_diagnostics(page, generation_id="gen-1")
        second = dump_interior_visual_diagnostics(page, generation_id="gen-1")

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
