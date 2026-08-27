"""Tests per il marcatore d'elenco desunto dal manuale.

`Criterio_Elenchi_v2.md` §1. Ogni caso qui viene da un manuale vero, e i casi di
**rifiuto** contano quanto quelli di riconoscimento: la v1 di questo criterio e'
caduta perche' prendeva `.` di Kul e `“` di SV e perdeva `✦` di DB.
"""

from __future__ import annotations

import unittest

from document_line_start_measurements import (
    LineStartMeasurements,
    measure_document_line_starts,
)
from document_list_policy import list_markers, strip_marker
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRY = PageGeometry(
    width=100.0, height=100.0, unit="pt", coordinate_system="top_left_y_down"
)


def _page(index: int, *lines: str) -> NormalizedPrimitivePage:
    primitives = tuple(
        TextPrimitive(
            primitive_id=f"primitive:text:p{index}:s{order}",
            bbox=(0.0, float(order), 50.0, float(order) + 1.0),
            text=text,
            source_observation_id=f"text:b0000:l{order:04d}:s0000",
        )
        for order, text in enumerate(lines)
    )
    return NormalizedPrimitivePage(
        schema_version="1",
        source_capture_id="c",
        source_id="s",
        page_id=f"page:{index:04d}",
        page_index=index,
        page_geometry=GEOMETRY,
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=primitives,
    )


class ListMarkerTest(unittest.TestCase):
    def test_a_symbol_font_glyph_is_a_marker(self) -> None:
        # DB: `✦` apre 312 righe, e ogni voce e' un blocco a se'. La v1 chiedeva
        # due righe nello stesso blocco e lo perdeva del tutto.
        pages = [
            _page(i, "✦Effetto Pieno: subisci danni", "✦Effetto Limitato: diventi Esausto")
            for i in range(2)
        ]
        self.assertIn("✦", list_markers(measure_document_line_starts(pages)))

    def test_a_marker_alone_on_its_line_is_found_by_what_follows(self) -> None:
        # FW: `•` sta da solo 41 volte su 41, e il testo della voce e' la riga dopo.
        pages = [_page(i, "•", "Descrivere un'azione", "•", "Seguire le procedure") for i in range(2)]
        self.assertIn("•", list_markers(measure_document_line_starts(pages)))

    def test_a_run_of_bare_dots_is_not_a_marker(self) -> None:
        # Kul: `.` apre 1098 righe, sta da solo su 1096, e la riga dopo e' un
        # altro punto. La v1 lo prendeva, ed era il falso positivo piu' grosso.
        pages = [_page(i, ".", ".", ".", ".") for i in range(2)]
        self.assertNotIn(".", list_markers(measure_document_line_starts(pages)))

    def test_an_opening_quote_is_never_a_marker(self) -> None:
        # SV: `“` apre 84 righe di dialogo. E' punteggiatura appaiata, e lo dice
        # Unicode: non serve una lista di caratteri scritta a mano.
        pages = [
            _page(i, "“Bene, riempi una sezione", "“Ma certo, qualunque cosa")
            for i in range(2)
        ]
        self.assertNotIn("“", list_markers(measure_document_line_starts(pages)))

    def test_a_character_on_a_single_page_is_not_a_marker(self) -> None:
        # Un elenco e' un modo di comporre, non un caso: `—`×1 su BoB, `¿`×1 su Lan.
        pages = [_page(0, "—Una volta sola", "—E un'altra"), _page(1, "Prosa normale")]
        self.assertNotIn("—", list_markers(measure_document_line_starts(pages)))

    def test_a_character_that_lives_inside_sentences_is_not_a_marker(self) -> None:
        pages = [
            _page(i, "Una frase con — un inciso — dentro", "—Apre una riga sola")
            for i in range(2)
        ]
        self.assertNotIn("—", list_markers(measure_document_line_starts(pages)))


class StripMarkerTest(unittest.TestCase):
    def test_it_removes_the_marker_and_the_space_after_it(self) -> None:
        self.assertEqual(strip_marker("*\t Fumante, sudata", frozenset("*")), "Fumante, sudata")

    def test_it_removes_every_leading_marker(self) -> None:
        # FW p.168: l'ordine di lettura interlaccia due colonne d'elenco e i
        # glifi arrivano di fila. Toglierne uno ne lasciava uno nella voce.
        self.assertEqual(strip_marker("• • Afflizione", frozenset("•")), "Afflizione")

    def test_it_leaves_a_line_that_does_not_open_with_a_marker(self) -> None:
        self.assertEqual(strip_marker("Prosa normale", frozenset("•")), "Prosa normale")


class MeasurementContractTest(unittest.TestCase):
    def test_counts_cannot_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            LineStartMeasurements({"•": -1}, {}, {}, {}, 0)

    def test_keys_must_be_single_characters(self) -> None:
        with self.assertRaises(ValueError):
            LineStartMeasurements({"••": 1}, {}, {}, {}, 0)


if __name__ == "__main__":
    unittest.main()
