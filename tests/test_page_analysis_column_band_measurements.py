"""Le misure satellite di `layout.column_band`.

Contratto di Milestone 33: candidato minimale **piu'** misura satellite. Questi
test verificano che la misura porti cio' che il candidato non puo' portare -- i
gutter, il livello, il padre -- e che rifiuti stati impossibili invece di
lasciarli passare.
"""

from __future__ import annotations

import unittest

from page_analysis_column_band_measurements import (
    ColumnBandMeasurements,
    measure_column_bands,
)
from page_analysis_model import RegionCandidate


def _candidate(band_id: int, bbox: tuple[float, float, float, float]) -> RegionCandidate:
    return RegionCandidate(
        candidate_id=f"candidate:column-band:page:0001:{band_id}",
        page_id="page:0001",
        bbox=bbox,
        proposed_structural_kind="layout.column_band",
        primitive_ids=(f"p:{band_id}",),
    )


class ColumnBandMeasurementsTest(unittest.TestCase):
    def test_column_count_must_match_the_gutters(self) -> None:
        with self.assertRaises(ValueError):
            ColumnBandMeasurements(
                candidate_id="c", page_id="p", column_count=3,
                gutter_x_intervals=((10.0, 20.0),), depth=0, parent_candidate_id=None,
            )

    def test_a_nested_band_must_name_its_parent(self) -> None:
        with self.assertRaises(ValueError):
            ColumnBandMeasurements(
                candidate_id="c", page_id="p", column_count=1,
                gutter_x_intervals=(), depth=1, parent_candidate_id=None,
            )

    def test_a_first_level_band_has_no_parent(self) -> None:
        with self.assertRaises(ValueError):
            ColumnBandMeasurements(
                candidate_id="c", page_id="p", column_count=1,
                gutter_x_intervals=(), depth=0, parent_candidate_id="altro",
            )

    def test_gutters_must_be_sorted_and_disjoint(self) -> None:
        with self.assertRaises(ValueError):
            ColumnBandMeasurements(
                candidate_id="c", page_id="p", column_count=3,
                gutter_x_intervals=((100.0, 200.0), (150.0, 250.0)),
                depth=0, parent_candidate_id=None,
            )

    def test_carries_gutters_depth_and_parent(self) -> None:
        candidates = (_candidate(1, (0.0, 0.0, 600.0, 400.0)), _candidate(2, (0.0, 0.0, 300.0, 200.0)))
        tree = [
            {"band_id": 1, "parent_id": "", "depth": 0, "gutter_x_intervals": "290.0-310.0"},
            {"band_id": 2, "parent_id": 1, "depth": 1, "gutter_x_intervals": "100.0-110.0 200.0-210.0"},
        ]

        measures = measure_column_bands(candidates, tree)

        self.assertEqual(len(measures), 2)
        self.assertEqual(measures[0].column_count, 2)
        self.assertEqual(measures[0].gutter_x_intervals, ((290.0, 310.0),))
        self.assertIsNone(measures[0].parent_candidate_id)
        self.assertEqual(measures[1].column_count, 3)
        self.assertEqual(measures[1].depth, 1)
        self.assertEqual(measures[1].parent_candidate_id, candidates[0].candidate_id)

    def test_a_child_whose_parent_was_not_emitted_becomes_first_level(self) -> None:
        """Non si inventa un riferimento che nessuno puo' risolvere.

        Il padre puo' esistere nell'albero e non essere stato emesso come
        candidato -- per esempio perche' non conteneva primitive. La banda
        diventa allora osservabilmente di primo livello.
        """

        candidates = (_candidate(2, (0.0, 0.0, 300.0, 200.0)),)
        tree = [
            {"band_id": 1, "parent_id": "", "depth": 0, "gutter_x_intervals": ""},
            {"band_id": 2, "parent_id": 1, "depth": 1, "gutter_x_intervals": "100.0-110.0"},
        ]

        measures = measure_column_bands(candidates, tree)

        self.assertEqual(measures[0].depth, 0)
        self.assertIsNone(measures[0].parent_candidate_id)

    def test_ignores_candidates_of_another_kind(self) -> None:
        other = RegionCandidate(
            candidate_id="candidate:other:1", page_id="page:0001",
            bbox=(0.0, 0.0, 10.0, 10.0), proposed_structural_kind="layout.embedded_visual",
            primitive_ids=("p:1",),
        )
        self.assertEqual(measure_column_bands((other,), []), ())


if __name__ == "__main__":
    unittest.main()
