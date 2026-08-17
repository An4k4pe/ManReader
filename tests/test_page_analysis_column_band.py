"""Il producer `layout.column_band`.

Testa cio' che DECIDE: la forma del candidato secondo il contratto di
Milestone 33, l'appartenenza delle primitive, il ritaglio alla pagina, e il
rifiuto di un `generation_id` vuoto. Il meccanismo geometrico che produce le
bande ha i propri test in `test_column_band_source_structure.py`
(`_is_subordinate`) ed e' stato verificato a vista sulle ancore della
diagnostica pre-milestone.
"""

from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from page_analysis_column_band import build_column_band_page_analysis
from primitive_model import NormalizedPrimitivePage, TextPrimitive


def _span(block: int, line: int, span: int, text: str, bbox) -> TextPrimitive:  # type: ignore[no-untyped-def]
    return TextPrimitive(
        primitive_id=f"p:{block}:{line}:{span}",
        bbox=bbox,
        text=text,
        source_observation_id=f"text:b{block:04d}:l{line:04d}:s{span:04d}",
    )


def _page(primitives: tuple[TextPrimitive, ...]) -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page:0001",
        page_index=0,
        page_geometry=PageGeometry(
            width=600.0, height=800.0, unit="pt", coordinate_system="top_left_y_down"
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=primitives,
        image_primitives=(),
        drawing_primitives=(),
    )


def _two_columns() -> NormalizedPrimitivePage:
    """Due colonne separate da un corridoio, con righe abbastanza lunghe."""

    primitives: list[TextPrimitive] = []
    for index in range(12):
        y = 100.0 + index * 14.0
        primitives.append(
            _span(index, 0, 0, "colonna sinistra con testo lungo", (60.0, y, 280.0, y + 11.0))
        )
        primitives.append(
            _span(index + 100, 0, 0, "colonna destra con testo lungo", (320.0, y, 540.0, y + 11.0))
        )
    return _page(tuple(primitives))


class BuildColumnBandPageAnalysisTest(unittest.TestCase):
    def test_rejects_empty_generation_id(self) -> None:
        with self.assertRaises(ValueError):
            build_column_band_page_analysis(_two_columns(), generation_id="")

    def test_emits_column_band_candidates_with_the_contract_kind(self) -> None:
        analysis = build_column_band_page_analysis(_two_columns(), generation_id="gen:1")

        self.assertTrue(analysis.candidates)
        for candidate in analysis.candidates:
            self.assertEqual(candidate.proposed_structural_kind, "layout.column_band")
            self.assertEqual(candidate.page_id, "page:0001")
            self.assertTrue(candidate.primitive_ids)

    def test_candidates_stay_inside_the_page(self) -> None:
        page = _two_columns()
        analysis = build_column_band_page_analysis(page, generation_id="gen:1")

        for candidate in analysis.candidates:
            self.assertGreaterEqual(candidate.bbox[0], 0.0)
            self.assertGreaterEqual(candidate.bbox[1], 0.0)
            self.assertLessEqual(candidate.bbox[2], page.page_geometry.width)
            self.assertLessEqual(candidate.bbox[3], page.page_geometry.height)

    def test_primitives_of_a_candidate_have_their_centre_inside_it(self) -> None:
        page = _two_columns()
        analysis = build_column_band_page_analysis(page, generation_id="gen:1")
        by_id = {p.primitive_id: p for p in page.text_primitives}

        for candidate in analysis.candidates:
            for primitive_id in candidate.primitive_ids:
                primitive = by_id[primitive_id]
                centre_x = (primitive.bbox[0] + primitive.bbox[2]) / 2.0
                centre_y = (primitive.bbox[1] + primitive.bbox[3]) / 2.0
                self.assertTrue(candidate.bbox[0] <= centre_x < candidate.bbox[2])
                self.assertTrue(candidate.bbox[1] <= centre_y < candidate.bbox[3])

    def test_single_column_page_emits_no_candidate(self) -> None:
        """Controllo negativo: senza corridoio non si inventa una banda."""

        primitives = tuple(
            _span(index, 0, 0, "una sola colonna di testo continuo", (60.0, 100.0 + index * 14.0, 540.0, 111.0 + index * 14.0))
            for index in range(12)
        )
        analysis = build_column_band_page_analysis(_page(primitives), generation_id="gen:1")

        self.assertEqual(analysis.candidates, ())

    def test_empty_page_emits_no_candidate(self) -> None:
        analysis = build_column_band_page_analysis(_page(()), generation_id="gen:1")

        self.assertEqual(analysis.candidates, ())

    def test_provenance_names_the_producer(self) -> None:
        analysis = build_column_band_page_analysis(_two_columns(), generation_id="gen:1")

        self.assertEqual(analysis.provenance.producer_name, "page_analysis.column_band")
        self.assertEqual(analysis.provenance.source_page_id, "page:0001")
        self.assertEqual(analysis.generation_id, "gen:1")


if __name__ == "__main__":
    unittest.main()
