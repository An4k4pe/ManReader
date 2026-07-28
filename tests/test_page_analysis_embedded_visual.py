from __future__ import annotations

import unittest
from typing import Any, cast

from geometry_model import PageGeometry
from page_analysis_embedded_visual import build_embedded_visual_page_analysis
from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION
from page_analysis_validate import validate_page_analysis_against_primitive_page
from primitive_model import DrawingPrimitive, ImageOccurrencePrimitive, NormalizedPrimitivePage


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
        text_primitives=(),
        image_primitives=images,
        drawing_primitives=drawings,
    )


def _candidate_ids(page: NormalizedPrimitivePage) -> tuple[str, ...]:
    return tuple(
        candidate.candidate_id
        for candidate in build_embedded_visual_page_analysis(
            page, generation_id="gen-1"
        ).candidates
    )


class BuildEmbeddedVisualPageAnalysisTest(unittest.TestCase):
    def test_rejects_wrong_page_type_and_empty_generation_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            build_embedded_visual_page_analysis(cast(Any, object()), generation_id="gen-1")
        with self.assertRaisesRegex(ValueError, "generation_id"):
            build_embedded_visual_page_analysis(_page(), generation_id="")

    def test_residual_raster_image_is_promoted_to_candidate(self) -> None:
        page = _page(images=(_image("wide-central", (5.0, 10.0, 95.0, 190.0)),))

        analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(analysis.candidates), 1)
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.candidate_id, "candidate:embedded-visual-raster:wide-central")
        self.assertEqual(candidate.primitive_ids, ("wide-central",))
        self.assertEqual(candidate.bbox, (5.0, 10.0, 95.0, 190.0))
        self.assertEqual(candidate.proposed_structural_kind, "layout.embedded_visual")

    def test_residual_vector_cluster_is_promoted_with_multiple_primitive_ids(self) -> None:
        page = _page(
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            )
        )

        analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(analysis.candidates), 1)
        candidate = analysis.candidates[0]
        self.assertEqual(candidate.candidate_id, "candidate:embedded-visual-vector:a")
        self.assertEqual(candidate.primitive_ids, ("a", "b"))
        self.assertEqual(candidate.proposed_structural_kind, "layout.embedded_visual")

    def test_raster_covering_and_edge_visuals_are_not_promoted(self) -> None:
        page = _page(
            images=(
                _image("full-page", (0.0, 0.0, 100.0, 200.0)),
                _image("edge", (0.0, 0.0, 80.0, 20.0)),
            )
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_edge_cluster_is_not_promoted(self) -> None:
        # Three small, individually-eligible drawings merge into one edge-shaped
        # cluster (long, thin, touching the top edge) without any single member
        # being excluded by the Milestone 26 pre-filter.
        page = _page(
            drawings=(
                _drawing("v1", (0.0, 0.0, 27.0, 15.0)),
                _drawing("v2", (30.0, 0.0, 57.0, 15.0)),
                _drawing("v3", (60.0, 0.0, 85.0, 15.0)),
            )
        )

        self.assertEqual(_candidate_ids(page), ())

    def test_vector_cluster_with_excluded_reason_is_not_promoted(self) -> None:
        page = _page(drawings=(_drawing("tiny", (10.0, 10.0, 11.0, 11.0)),))

        self.assertEqual(_candidate_ids(page), ())

    def test_page_without_visuals_has_no_candidates(self) -> None:
        analysis = build_embedded_visual_page_analysis(_page(), generation_id="gen-1")

        self.assertEqual(analysis.candidates, ())

    def test_contract_provenance_determinism_and_validation(self) -> None:
        page = _page(
            images=(_image("wide-central", (5.0, 10.0, 95.0, 190.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            ),
        )

        first = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        second = build_embedded_visual_page_analysis(page, generation_id="gen-1")

        self.assertEqual(first, second)
        self.assertEqual(first.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(first.regions, ())
        self.assertEqual(first.relations, ())
        self.assertEqual(first.provenance.producer_name, "page_analysis.embedded_visual")
        self.assertEqual(first.provenance.producer_version, "0.1")
        self.assertEqual(first.provenance.configuration_id, "embedded-visual-v1")
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in first.candidates),
            (
                "candidate:embedded-visual-raster:wide-central",
                "candidate:embedded-visual-vector:a",
            ),
        )
        self.assertTrue(
            all(
                candidate.proposed_structural_kind == "layout.embedded_visual"
                for candidate in first.candidates
            )
        )
        validate_page_analysis_against_primitive_page(first, page)


if __name__ == "__main__":
    unittest.main()
