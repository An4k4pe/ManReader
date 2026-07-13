from __future__ import annotations

import unittest
from typing import cast

from geometry_model import PageGeometry
from page_analysis_model import PageAnalysis
from page_analysis_side_band import build_local_fragment_side_band_page_analysis
from page_analysis_side_band_local_fragment_diagnostics import (
    dump_side_band_local_fragment_diagnostics,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _text(
    primitive_id: str,
    text: str,
    bbox: tuple[float, float, float, float],
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=bbox,
        text=text,
        source_observation_id=f"obs:{primitive_id}",
    )


def _page(
    text_primitives: tuple[TextPrimitive, ...],
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
    )


def _entries_by_id(diagnostics: dict[str, object]) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    for entry in _candidate_entries(diagnostics):
        candidate_id = entry["candidate_id"]
        if not isinstance(candidate_id, str):
            raise AssertionError("candidate_id must be a string")
        entries[candidate_id] = entry
    return entries


def _candidate_entries(diagnostics: dict[str, object]) -> list[dict[str, object]]:
    candidates = diagnostics["candidates"]
    if not isinstance(candidates, list):
        raise AssertionError("candidates must be a list")
    return cast(list[dict[str, object]], candidates)


class SideBandLocalFragmentDiagnosticsTest(unittest.TestCase):
    def test_produces_one_entry_for_each_source_candidate_without_page_analysis(self) -> None:
        page = _page(
            (
                _text("one", "One", (0.0, 40.0, 10.0, 50.0)),
                _text("two", "Two", (11.0, 40.0, 21.0, 50.0)),
                _text("three", "Three", (0.0, 80.0, 12.0, 90.0)),
            )
        )
        source_analysis = build_local_fragment_side_band_page_analysis(page, generation_id="gen-1")

        diagnostics = dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1")

        self.assertNotIsInstance(diagnostics, PageAnalysis)
        self.assertEqual(diagnostics["page_id"], page.page_id)
        entries = _candidate_entries(diagnostics)
        self.assertEqual(
            [entry["candidate_id"] for entry in entries],
            [candidate.candidate_id for candidate in source_analysis.candidates],
        )
        for entry, candidate in zip(entries, source_analysis.candidates, strict=True):
            self.assertEqual(entry["bbox"], list(candidate.bbox))
            self.assertEqual(entry["primitive_ids"], list(candidate.primitive_ids))
            self.assertEqual(entry["primitive_count"], len(candidate.primitive_ids))
            self.assertIn("text", entry)

    def test_measures_page_ratios_and_edge_distances(self) -> None:
        page = _page((_text("number", "12", (0.0, 50.0, 10.0, 60.0)),))

        diagnostics = dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1")
        entry = _candidate_entries(diagnostics)[0]

        self.assertEqual(entry["page_width_ratio"], 0.1)
        self.assertEqual(entry["page_height_ratio"], 0.05)
        self.assertEqual(entry["page_area_ratio"], 0.005)
        self.assertEqual(entry["distance_left"], 0.0)
        self.assertEqual(entry["distance_right"], 90.0)
        self.assertEqual(entry["distance_top"], 50.0)
        self.assertEqual(entry["distance_bottom"], 140.0)
        self.assertEqual(entry["distance_left_ratio"], 0.0)
        self.assertEqual(entry["distance_right_ratio"], 0.9)
        self.assertEqual(entry["distance_top_ratio"], 0.25)
        self.assertEqual(entry["distance_bottom_ratio"], 0.7)

    def test_reports_formal_text_flags(self) -> None:
        page = _page(
            (
                _text("numeric", "123", (0.0, 30.0, 10.0, 40.0)),
                _text("punctuation", "!", (0.0, 60.0, 10.0, 70.0)),
                _text("bullet", "•", (0.0, 90.0, 10.0, 100.0)),
                _text("hexagon", "⬣", (0.0, 120.0, 10.0, 130.0)),
                _text("uppercase", "ABC", (0.0, 150.0, 15.0, 160.0)),
            )
        )

        entries = _entries_by_id(dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1"))

        self.assertTrue(entries["candidate:side-band:local-fragment:numeric"]["is_numeric_only"])
        self.assertTrue(entries["candidate:side-band:local-fragment:punctuation"]["is_punctuation_only"])
        self.assertTrue(entries["candidate:side-band:local-fragment:punctuation"]["is_single_character"])
        self.assertTrue(entries["candidate:side-band:local-fragment:bullet"]["is_bullet_or_marker_like"])
        self.assertTrue(entries["candidate:side-band:local-fragment:hexagon"]["is_bullet_or_marker_like"])
        self.assertTrue(entries["candidate:side-band:local-fragment:uppercase"]["is_short_uppercase"])

    def test_reports_same_baseline_neighbor_without_classifying_it(self) -> None:
        page = _page(
            (
                _text("candidate", "12", (0.0, 100.0, 10.0, 110.0)),
                _text("neighbor", "Body", (30.0, 100.0, 60.0, 110.0)),
            )
        )

        diagnostics = dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1")
        entry = _candidate_entries(diagnostics)[0]

        self.assertEqual(entry["same_baseline_neighbor_count"], 1)
        self.assertEqual(entry["nearest_same_baseline_text_primitive_id"], "neighbor")
        self.assertEqual(entry["nearest_same_baseline_gap"], 20.0)
        self.assertEqual(entry["nearest_same_baseline_vertical_overlap_ratio"], 1.0)
        self.assertTrue(entry["has_same_baseline_neighbor"])
        self.assertFalse(any(key.startswith("is_body") for key in entry))

    def test_output_is_deterministic(self) -> None:
        page = _page((_text("one", "One", (0.0, 100.0, 10.0, 110.0)),))

        self.assertEqual(
            dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1"),
            dump_side_band_local_fragment_diagnostics(page, generation_id="gen-1"),
        )


if __name__ == "__main__":
    unittest.main()
