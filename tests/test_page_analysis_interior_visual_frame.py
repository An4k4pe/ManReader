from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_interior_visual_frame import build_interior_visual_frame_page_analysis
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION
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
        for candidate in build_interior_visual_frame_page_analysis(
            page, generation_id="gen-1"
        ).candidates
    )


class BuildInteriorVisualFramePageAnalysisTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_interior_visual_frame_page_analysis(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_interior_visual_frame_page_analysis(_page(), generation_id="")

    def test_residual_raster_image_with_contained_text_is_promoted(self) -> None:
        page = _page(
            text=(_text("inside", (30.0, 30.0, 50.0, 40.0)),),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
        )

        analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(analysis.candidates), 1)
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.candidate_id, "candidate:interior-visual-frame-raster:framed")
        self.assertEqual(candidate.primitive_ids, ("framed",))
        self.assertEqual(candidate.bbox, (20.0, 20.0, 80.0, 100.0))
        self.assertEqual(candidate.proposed_structural_kind, "layout.interior_visual_frame")

    def test_residual_raster_image_without_text_is_not_promoted(self) -> None:
        page = _page(images=(_image("empty", (20.0, 20.0, 80.0, 100.0)),))

        self.assertEqual(_candidate_ids(page), ())

    def test_residual_vector_cluster_with_contained_text_is_promoted(self) -> None:
        page = _page(
            text=(_text("inside", (12.0, 12.0, 18.0, 18.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            ),
        )

        analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(analysis.candidates), 1)
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.candidate_id, "candidate:interior-visual-frame-vector:a")
        self.assertEqual(candidate.primitive_ids, ("a", "b"))
        self.assertEqual(candidate.proposed_structural_kind, "layout.interior_visual_frame")

    def test_residual_vector_cluster_without_text_is_not_promoted(self) -> None:
        page = _page(
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            )
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_raster_covering_and_edge_visuals_are_not_promoted_even_with_text(self) -> None:
        page = _page(
            text=(_text("inside", (30.0, 30.0, 50.0, 40.0)),),
            images=(
                _image("full-page", (0.0, 0.0, 100.0, 200.0)),
                _image("edge", (0.0, 0.0, 80.0, 20.0)),
            ),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_edge_cluster_is_not_promoted_even_with_text(self) -> None:
        # Same edge-shaped, individually-eligible cluster as embedded_visual's
        # test, plus contained text: still excluded because it is not residual.
        page = _page(
            text=(_text("inside", (5.0, 2.0, 15.0, 10.0)),),
            drawings=(
                _drawing("v1", (0.0, 0.0, 27.0, 15.0)),
                _drawing("v2", (30.0, 0.0, 57.0, 15.0)),
                _drawing("v3", (60.0, 0.0, 85.0, 15.0)),
            ),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_cluster_with_excluded_reason_is_not_promoted(self) -> None:
        page = _page(drawings=(_drawing("tiny", (10.0, 10.0, 11.0, 11.0)),))

        self.assertEqual(_candidate_ids(page), ())

    def test_raster_below_min_area_ratio_is_not_promoted(self) -> None:
        # bbox area 25 / page area 20000 = 0.00125, below the default 0.006 floor.
        page = _page(
            text=(_text("inside", (1.0, 1.0, 4.0, 4.0)),),
            images=(_image("tiny-image", (0.0, 0.0, 5.0, 5.0)),),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_raster_above_max_area_ratio_is_not_promoted(self) -> None:
        # bbox area 16200 / page area 20000 = 0.81, above the default 0.28 ceiling.
        page = _page(
            text=(_text("inside", (10.0, 10.0, 20.0, 20.0)),),
            images=(_image("huge-image", (0.0, 0.0, 90.0, 180.0)),),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_below_min_area_ratio_is_not_promoted(self) -> None:
        # union bbox area 14 / page area 20000 = 0.0007, below the default 0.006 floor.
        page = _page(
            text=(_text("inside", (11.0, 10.0, 12.0, 11.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 13.0, 12.0)),
                _drawing("b", (14.0, 10.0, 17.0, 12.0)),
            ),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_above_max_area_ratio_is_not_promoted(self) -> None:
        # union bbox area 5880 / page area 20000 = 0.294, above the default 0.28 ceiling.
        page = _page(
            text=(_text("inside", (15.0, 15.0, 25.0, 25.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 50.0, 80.0)),
                _drawing("b", (54.0, 10.0, 94.0, 80.0)),
            ),
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_page_without_visuals_has_no_candidates(self) -> None:
        analysis = build_interior_visual_frame_page_analysis(_page(), generation_id="gen-1")

        self.assertEqual(analysis.candidates, ())

    def test_contract_provenance_determinism_and_validation(self) -> None:
        page = _page(
            text=(
                _text("in-image", (30.0, 30.0, 50.0, 40.0)),
                _text("in-cluster", (12.0, 12.0, 18.0, 18.0)),
            ),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            ),
        )

        first = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")
        second = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertEqual(first, second)
        self.assertEqual(first.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(first.regions, ())
        self.assertEqual(first.relations, ())
        self.assertEqual(first.provenance.producer_name, "page_analysis.interior_visual_frame")
        self.assertEqual(first.provenance.producer_version, "0.1")
        self.assertEqual(first.provenance.configuration_id, "interior-visual-frame-v1")
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in first.candidates),
            (
                "candidate:interior-visual-frame-raster:framed",
                "candidate:interior-visual-frame-vector:a",
            ),
        )
        self.assertTrue(
            all(
                candidate.proposed_structural_kind == "layout.interior_visual_frame"
                for candidate in first.candidates
            )
        )
        validate_page_analysis_against_primitive_page(first, page)


if __name__ == "__main__":
    unittest.main()
