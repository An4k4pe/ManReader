from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch

from geometry_model import PageGeometry
from page_analysis_candidate_extent_relation_diagnostics import (
    dump_local_fragment_side_band_candidate_extent_relations,
)
from page_analysis_candidate_extent_relation_measurements import (
    measure_candidate_non_candidate_extent_relations as _measure_candidate_non_candidate_extent_relations,
)
from page_analysis_candidate_page_context_measurements import (
    measure_candidate_page_context as _measure_candidate_page_context,
)
from page_analysis_model import PageAnalysis
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
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


def _image(primitive_id: str, bbox: tuple[float, float, float, float]) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        source_observation_id=f"obs:{primitive_id}",
    )


def _drawing(primitive_id: str, bbox: tuple[float, float, float, float]) -> DrawingPrimitive:
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


class CandidateExtentRelationDiagnosticsTest(unittest.TestCase):
    def test_returns_empty_candidates_without_page_analysis(self) -> None:
        diagnostics = dump_local_fragment_side_band_candidate_extent_relations(
            _page(text=(_text("body", (40.0, 40.0, 60.0, 50.0)),)),
            generation_id="gen-1",
        )

        self.assertNotIsInstance(diagnostics, PageAnalysis)
        self.assertEqual(
            diagnostics,
            {"generation_id": "gen-1", "page_id": "page-1", "candidates": []},
        )

    def test_single_candidate_serializes_separate_extents_and_relations(self) -> None:
        diagnostics = dump_local_fragment_side_band_candidate_extent_relations(
            _page(
                text=(
                    _text("side", (0.0, 40.0, 10.0, 50.0)),
                    _text("body", (35.0, 40.0, 65.0, 50.0)),
                ),
                images=(_image("image", (70.0, 60.0, 80.0, 70.0)),),
                drawings=(_drawing("drawing", (45.0, 90.0, 55.0, 100.0)),),
            ),
            generation_id="gen-1",
        )

        entry = _candidate_entries(diagnostics)[0]
        self.assertEqual(entry["candidate_id"], "candidate:side-band:local-fragment:side")
        self.assertEqual(entry["candidate_bbox"], [0.0, 40.0, 10.0, 50.0])
        self.assertEqual(entry["candidate_primitive_ids"], ["side"])
        self.assertEqual(entry["non_candidate_visible_text_extent_bbox"], [35.0, 40.0, 65.0, 50.0])
        self.assertEqual(
            entry["non_candidate_visible_text_extent_relation"],
            {
                "horizontal_gap": 25.0,
                "vertical_gap": 0.0,
                "horizontal_overlap": 0.0,
                "vertical_overlap": 10.0,
                "candidate_contains_extent": False,
                "extent_contains_candidate": False,
            },
        )
        self.assertEqual(entry["non_candidate_visible_image_extent_bbox"], [70.0, 60.0, 80.0, 70.0])
        self.assertEqual(entry["non_candidate_visible_drawing_extent_bbox"], [45.0, 90.0, 55.0, 100.0])
        self.assertNotEqual(
            entry["non_candidate_visible_image_extent_relation"],
            entry["non_candidate_visible_drawing_extent_relation"],
        )

    def test_multi_primitive_candidate_excludes_all_members(self) -> None:
        diagnostics = dump_local_fragment_side_band_candidate_extent_relations(
            _page(
                text=(
                    _text("left", (0.0, 40.0, 10.0, 50.0)),
                    _text("right", (11.0, 40.0, 21.0, 50.0)),
                    _text("body", (35.0, 40.0, 65.0, 50.0)),
                )
            ),
            generation_id="gen-1",
        )

        entries = _candidate_entries(diagnostics)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["candidate_primitive_ids"], ["left", "right"])
        self.assertEqual(entries[0]["non_candidate_visible_text_extent_bbox"], [35.0, 40.0, 65.0, 50.0])

    def test_absent_family_has_none_extent_and_relation(self) -> None:
        entry = _candidate_entries(
            dump_local_fragment_side_band_candidate_extent_relations(
                _page(text=(_text("side", (0.0, 40.0, 10.0, 50.0)),)),
                generation_id="gen-1",
            )
        )[0]

        for family in ("text", "image", "drawing"):
            self.assertIsNone(entry[f"non_candidate_visible_{family}_extent_bbox"])
            self.assertIsNone(entry[f"non_candidate_visible_{family}_extent_relation"])

    def test_candidate_order_and_measurement_call_counts_match_source_producer(self) -> None:
        page = _page(
            text=(
                _text("one", (0.0, 40.0, 10.0, 50.0)),
                _text("two", (0.0, 80.0, 10.0, 90.0)),
            )
        )
        source_analysis = build_local_fragment_side_band_page_analysis(page, generation_id="gen-1")

        with (
            patch(
                "page_analysis_candidate_extent_relation_diagnostics."
                "build_local_fragment_side_band_page_analysis",
                wraps=build_local_fragment_side_band_page_analysis,
            ) as builder,
            patch(
                "page_analysis_candidate_extent_relation_diagnostics.measure_candidate_page_context",
                wraps=_measure_candidate_page_context,
            ) as context_measure,
            patch(
                "page_analysis_candidate_extent_relation_diagnostics."
                "measure_candidate_non_candidate_extent_relations",
                wraps=_measure_candidate_non_candidate_extent_relations,
            ) as relation_measure,
        ):
            diagnostics = dump_local_fragment_side_band_candidate_extent_relations(
                page,
                generation_id="gen-1",
            )

        self.assertEqual(builder.call_count, 1)
        self.assertEqual(context_measure.call_count, len(source_analysis.candidates))
        self.assertEqual(relation_measure.call_count, len(source_analysis.candidates))
        self.assertEqual(
            [entry["candidate_id"] for entry in _candidate_entries(diagnostics)],
            [candidate.candidate_id for candidate in source_analysis.candidates],
        )

    def test_rejects_runtime_inputs_and_emits_only_authorized_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_local_fragment_side_band_candidate_extent_relations(
                cast(NormalizedPrimitivePage, object()),
                generation_id="gen-1",
            )
        with self.assertRaisesRegex(ValueError, "generation_id"):
            dump_local_fragment_side_band_candidate_extent_relations(_page(), generation_id="")

        entry = _candidate_entries(
            dump_local_fragment_side_band_candidate_extent_relations(
                _page(text=(_text("side", (0.0, 40.0, 10.0, 50.0)),)),
                generation_id="gen-1",
            )
        )[0]
        self.assertIsInstance(entry["candidate_bbox"], list)
        self.assertIsInstance(entry["candidate_primitive_ids"], list)
        self.assertEqual(
            set(entry),
            {
                "candidate_id",
                "page_id",
                "candidate_bbox",
                "candidate_primitive_ids",
                "non_candidate_visible_text_extent_bbox",
                "non_candidate_visible_text_extent_relation",
                "non_candidate_visible_image_extent_bbox",
                "non_candidate_visible_image_extent_relation",
                "non_candidate_visible_drawing_extent_bbox",
                "non_candidate_visible_drawing_extent_relation",
            },
        )
        relation = entry["non_candidate_visible_text_extent_relation"]
        self.assertIsNone(relation)
        self.assertFalse(
            any(
                token in key
                for key in entry
                for token in (
                    "count",
                    "intersects",
                    "ratio",
                    "distance",
                    "direction",
                    "score",
                    "confidence",
                    "ranking",
                    "evidence",
                    "class",
                    "provenance",
                    "structural_kind",
                    "schema",
                )
            )
        )

    def test_output_is_deterministic(self) -> None:
        page = _page(text=(_text("side", (0.0, 40.0, 10.0, 50.0)),))

        self.assertEqual(
            dump_local_fragment_side_band_candidate_extent_relations(page, generation_id="gen-1"),
            dump_local_fragment_side_band_candidate_extent_relations(page, generation_id="gen-1"),
        )


if __name__ == "__main__":
    unittest.main()
