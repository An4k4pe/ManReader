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
from pathlib import Path

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

    def test_a_persistent_channel_that_is_not_a_gutter_produces_no_band(self) -> None:
        """Controllo negativo che PUO' fallire, a differenza degli altri due.

        Pagina vuota e colonna singola non possono produrre bande: sono controlli
        di sanita'. Questo discende invece dalla tesi del meccanismo -- separa la
        persistenza verticale, non la larghezza -- e mette alla prova proprio
        quella: una colonna di numeri di tabella accanto a della prosa produce un
        canale bianco verticale **persistente e fiancheggiato da entrambi i
        lati**, che non e' un gutter di colonna.

        Il criterio che deve reggerlo e' `too_few_wordy_lines`: il lato dei
        numeri non porta righe con abbastanza caratteri. E' un test che fallisce
        davvero se qualcuno abbassa `min_flanking_chars` -- misurato sul progetto:
        a 2 questa classe di pagina viene accettata come banda (Lan p.84, tabella
        di dadi).
        """

        primitives: list[TextPrimitive] = []
        for index in range(14):
            y = 100.0 + index * 14.0
            primitives.append(_span(index, 0, 0, str(index + 1), (60.0, y, 74.0, y + 11.0)))
            primitives.append(
                _span(index + 100, 0, 0, "prosa continua e sufficientemente lunga",
                      (120.0, y, 540.0, y + 11.0))
            )

        analysis = build_column_band_page_analysis(_page(tuple(primitives)), generation_id="gen:1")

        self.assertEqual(analysis.candidates, ())

    def test_provenance_names_the_producer(self) -> None:
        analysis = build_column_band_page_analysis(_two_columns(), generation_id="gen:1")

        self.assertEqual(analysis.provenance.producer_name, "page_analysis.column_band")
        self.assertEqual(analysis.provenance.source_page_id, "page:0001")
        self.assertEqual(analysis.generation_id, "gen:1")


_CORPUS = Path(__file__).resolve().parents[1] / "Dag.pdf"


@unittest.skipUnless(_CORPUS.is_file(), "serve Dag.pdf accanto alla radice del repo")
class DagPage84RegressionTest(unittest.TestCase):
    """L'unica regressione documentata che il progetto possiede.

    Dag p.84 POSIZIONALE (stampata 82) e' l'unica pagina con **entrambe** le
    cose: un'aspettativa verificata a render -- prosa giustificata a due colonne
    nella meta' alta, gutter reale largo circa 8pt -- e una risposta precedente
    nota e SBAGLIATA, `column_count=1`, prodotta dal meccanismo di Fase 1/2 a
    ogni combinazione di parametri.

    Era rimasta fuori dalla verifica del producer: rilievo della revisione
    indipendente, ed era il caso di regressione piu' economico esistente.

    Il test asserisce il minimo che quella storia impone -- che le due colonne
    vengano trovate -- e non l'estensione della banda, che dipende dalla regola
    di estensione ed e' un'altra questione (il piede di pagina che ne finisce
    dentro e' assegnato alla deduplicazione).
    """

    def test_finds_the_two_columns_the_old_mechanism_missed(self) -> None:
        import fitz

        from primitive_normalizer import normalize_backend_page_capture
        from pymupdf_capture import capture_pymupdf_page

        with fitz.open(_CORPUS) as document:
            page = document.load_page(83)
            capture = capture_pymupdf_page(
                page, source_id="test", page_id="page:0084", capture_id="test:dag84"
            )
        primitive_page = normalize_backend_page_capture(capture)

        analysis = build_column_band_page_analysis(primitive_page, generation_id="gen:1")

        self.assertTrue(
            analysis.candidates,
            "Dag p.84 ha due colonne verificate a render: nessun candidato significa "
            "la stessa risposta sbagliata del meccanismo di Fase 1/2",
        )


if __name__ == "__main__":
    unittest.main()
