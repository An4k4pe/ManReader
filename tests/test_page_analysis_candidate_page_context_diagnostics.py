from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch

from geometry_model import PageGeometry
from page_analysis_candidate_page_context_diagnostics import (
    dump_local_fragment_side_band_candidate_page_context,
)
from page_analysis_model import PageAnalysis
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
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
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=text,
        image_primitives=images,
        drawing_primitives=drawings,
    )


def _candidate_entries(diagnostics: dict[str, object]) -> list[dict[str, object]]:
    candidates = diagnostics["candidates"]
    if not isinstance(candidates, list):
        raise AssertionError("candidates must be a list")
    return cast(list[dict[str, object]], candidates)


class CandidatePageContextDiagnosticsTest(unittest.TestCase):
    def test_returns_empty_candidates_without_page_analysis(self) -> None:
        page = _page(text=(_text("body", (40.0, 40.0, 60.0, 50.0)),))

        diagnostics = dump_local_fragment_side_band_candidate_page_context(
            page,
            generation_id="gen-1",
        )

        self.assertNotIsInstance(diagnostics, PageAnalysis)
        self.assertEqual(
            diagnostics,
            {
                "generation_id": "gen-1",
                "page_id": "page-1",
                "candidates": [],
            },
        )

    def test_measures_a_single_local_fragment_candidate(self) -> None:
        page = _page(
            text=(
                _text("side", (0.0, 40.0, 10.0, 50.0)),
                _text("body", (35.0, 40.0, 65.0, 50.0)),
            ),
            images=(_image("image", (70.0, 60.0, 80.0, 70.0)),),
            drawings=(_drawing("drawing", (45.0, 90.0, 55.0, 100.0)),),
        )

        entry = _candidate_entries(
            dump_local_fragment_side_band_candidate_page_context(
                page,
                generation_id="gen-1",
            )
        )[0]

        if not isinstance(entry, dict):
            self.fail("candidate diagnostics entry must be a dictionary")
        self.assertEqual(entry["candidate_id"], "candidate:side-band:local-fragment:side")
        self.assertEqual(entry["candidate_bbox"], [0.0, 40.0, 10.0, 50.0])
        self.assertEqual(entry["candidate_primitive_ids"], ["side"])
        self.assertEqual(entry["non_candidate_visible_text_primitive_count"], 1)
        self.assertEqual(entry["non_candidate_visible_text_extent_bbox"], [35.0, 40.0, 65.0, 50.0])
        self.assertEqual(entry["non_candidate_visible_image_primitive_count"], 1)
        self.assertEqual(entry["non_candidate_visible_image_extent_bbox"], [70.0, 60.0, 80.0, 70.0])
        self.assertEqual(entry["non_candidate_visible_drawing_primitive_count"], 1)
        self.assertEqual(entry["non_candidate_visible_drawing_extent_bbox"], [45.0, 90.0, 55.0, 100.0])

    def test_multi_primitive_candidate_excludes_all_members_and_keeps_family_extents_separate(
        self,
    ) -> None:
        page = _page(
            text=(
                _text("left", (0.0, 40.0, 10.0, 50.0)),
                _text("right", (11.0, 40.0, 21.0, 50.0)),
                _text("body", (35.0, 40.0, 65.0, 50.0)),
            ),
            images=(_image("image", (70.0, 60.0, 80.0, 70.0)),),
            drawings=(_drawing("drawing", (45.0, 90.0, 55.0, 100.0)),),
        )

        entries = _candidate_entries(
            dump_local_fragment_side_band_candidate_page_context(
                page,
                generation_id="gen-1",
            )
        )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        if not isinstance(entry, dict):
            self.fail("candidate diagnostics entry must be a dictionary")
        self.assertEqual(entry["candidate_primitive_ids"], ["left", "right"])
        self.assertEqual(entry["non_candidate_visible_text_primitive_count"], 1)
        self.assertEqual(entry["non_candidate_visible_text_extent_bbox"], [35.0, 40.0, 65.0, 50.0])
        self.assertEqual(entry["non_candidate_visible_image_extent_bbox"], [70.0, 60.0, 80.0, 70.0])
        self.assertEqual(entry["non_candidate_visible_drawing_extent_bbox"], [45.0, 90.0, 55.0, 100.0])

    def test_candidate_order_matches_the_source_producer_and_builder_runs_once(self) -> None:
        page = _page(
            text=(
                _text("one", (0.0, 40.0, 10.0, 50.0)),
                _text("two", (0.0, 80.0, 10.0, 90.0)),
            )
        )
        source_analysis = build_local_fragment_side_band_page_analysis(page, generation_id="gen-1")

        with patch(
            "page_analysis_candidate_page_context_diagnostics."
            "build_local_fragment_side_band_page_analysis",
            wraps=build_local_fragment_side_band_page_analysis,
        ) as builder:
            diagnostics = dump_local_fragment_side_band_candidate_page_context(
                page,
                generation_id="gen-1",
            )

        self.assertEqual(builder.call_count, 1)
        candidates = _candidate_entries(diagnostics)
        self.assertEqual(
            [entry["candidate_id"] for entry in candidates if isinstance(entry, dict)],
            [candidate.candidate_id for candidate in source_analysis.candidates],
        )

    def test_rejects_runtime_inputs_and_has_no_interpretive_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_local_fragment_side_band_candidate_page_context(
                cast(NormalizedPrimitivePage, object()),
                generation_id="gen-1",
            )
        with self.assertRaisesRegex(ValueError, "generation_id"):
            dump_local_fragment_side_band_candidate_page_context(_page(), generation_id="")

        entry = _candidate_entries(
            dump_local_fragment_side_band_candidate_page_context(
                _page(text=(_text("side", (0.0, 40.0, 10.0, 50.0)),)),
                generation_id="gen-1",
            )
        )[0]
        if not isinstance(entry, dict):
            self.fail("candidate diagnostics entry must be a dictionary")
        self.assertEqual(
            set(entry),
            {
                "candidate_id",
                "page_id",
                "candidate_bbox",
                "candidate_primitive_ids",
                "non_candidate_visible_text_primitive_count",
                "non_candidate_visible_text_extent_bbox",
                "non_candidate_visible_image_primitive_count",
                "non_candidate_visible_image_extent_bbox",
                "non_candidate_visible_drawing_primitive_count",
                "non_candidate_visible_drawing_extent_bbox",
            },
        )
        self.assertFalse(
            any(
                token in key
                for key in entry
                for token in ("score", "confidence", "ranking", "evidence", "class")
            )
        )

    def test_output_is_deterministic(self) -> None:
        page = _page(text=(_text("side", (0.0, 40.0, 10.0, 50.0)),))

        self.assertEqual(
            dump_local_fragment_side_band_candidate_page_context(page, generation_id="gen-1"),
            dump_local_fragment_side_band_candidate_page_context(page, generation_id="gen-1"),
        )


if __name__ == "__main__":
    unittest.main()
