"""Safety-net test for Proposta_ResolutionDesign_v3.md §8.2.1/§9.

Every layout.interior_visual_frame candidate produced with defaults is
expected to have a twin layout.embedded_visual candidate (same page, same
defaults) with identical primitive_ids and bbox. Today this property is
guaranteed only by three independently duplicated _DEFAULT_CLUSTER_MARGIN
constants and a prose note, never by a test. This file does not implement
any Resolution rule -- it only checks the technical precondition a future
rule will depend on.
"""

from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from page_analysis_embedded_visual import build_embedded_visual_page_analysis
from page_analysis_interior_visual_frame import build_interior_visual_frame_page_analysis
from page_analysis_model import RegionCandidate
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


def _find_by_primitive_ids(
    candidates: tuple[RegionCandidate, ...],
    primitive_ids: tuple[str, ...],
) -> RegionCandidate | None:
    for candidate in candidates:
        if candidate.primitive_ids == primitive_ids:
            return candidate
    return None


class EmbeddedVisualInteriorVisualFrameSubsetPreconditionTest(unittest.TestCase):
    def test_raster_frame_candidate_has_identical_embedded_visual_twin(self) -> None:
        page = _page(
            text=(_text("inside", (30.0, 30.0, 50.0, 40.0)),),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
        )

        embedded_analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        frame_analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(frame_analysis.candidates), 1)
        frame_candidate = frame_analysis.candidates[0]

        embedded_candidate = _find_by_primitive_ids(
            embedded_analysis.candidates, frame_candidate.primitive_ids
        )
        self.assertIsNotNone(
            embedded_candidate,
            "no embedded_visual candidate found with matching primitive_ids "
            f"{frame_candidate.primitive_ids!r}",
        )
        assert embedded_candidate is not None
        self.assertEqual(embedded_candidate.bbox, frame_candidate.bbox)
        self.assertEqual(embedded_candidate.primitive_ids, frame_candidate.primitive_ids)

    def test_vector_frame_candidate_has_identical_embedded_visual_twin(self) -> None:
        page = _page(
            text=(_text("inside", (12.0, 12.0, 18.0, 18.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            ),
        )

        embedded_analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        frame_analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertEqual(len(frame_analysis.candidates), 1)
        frame_candidate = frame_analysis.candidates[0]

        embedded_candidate = _find_by_primitive_ids(
            embedded_analysis.candidates, frame_candidate.primitive_ids
        )
        self.assertIsNotNone(
            embedded_candidate,
            "no embedded_visual candidate found with matching primitive_ids "
            f"{frame_candidate.primitive_ids!r}",
        )
        assert embedded_candidate is not None
        self.assertEqual(embedded_candidate.bbox, frame_candidate.bbox)
        self.assertEqual(embedded_candidate.primitive_ids, frame_candidate.primitive_ids)

    def test_combined_page_frame_candidates_are_all_subsets_of_embedded_visual(self) -> None:
        page = _page(
            text=(
                _text("inside-image", (30.0, 30.0, 50.0, 40.0)),
                _text("inside-cluster", (12.0, 12.0, 18.0, 18.0)),
            ),
            images=(_image("framed", (20.0, 20.0, 80.0, 100.0)),),
            drawings=(
                _drawing("a", (10.0, 10.0, 20.0, 20.0)),
                _drawing("b", (24.0, 10.0, 34.0, 20.0)),
            ),
        )

        embedded_analysis = build_embedded_visual_page_analysis(page, generation_id="gen-1")
        frame_analysis = build_interior_visual_frame_page_analysis(page, generation_id="gen-1")

        self.assertTrue(len(frame_analysis.candidates) > 0)
        for frame_candidate in frame_analysis.candidates:
            embedded_candidate = _find_by_primitive_ids(
                embedded_analysis.candidates, frame_candidate.primitive_ids
            )
            self.assertIsNotNone(
                embedded_candidate,
                "no embedded_visual candidate found with matching primitive_ids "
                f"{frame_candidate.primitive_ids!r}",
            )
            assert embedded_candidate is not None
            self.assertEqual(embedded_candidate.bbox, frame_candidate.bbox)
            self.assertEqual(embedded_candidate.primitive_ids, frame_candidate.primitive_ids)


if __name__ == "__main__":
    unittest.main()
