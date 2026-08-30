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
from document_list_policy import (
    list_item_flags,
    list_markers,
    strip_marker,
    strippable_marker,
)
from geometry_model import PageGeometry
from ir2_builder import _SourceLine, bind_marker_glyphs
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


class StrippableMarkerTest(unittest.TestCase):
    """`Criterio_MarcatorePerPrimitiva_v1.md`. La testa si toglie o no?"""

    def test_an_alphanumeric_marker_inside_a_word_is_not_stripped(self) -> None:
        # Il caso che ha imposto la regola: su Fab pagina stampata 171 la `O` e'
        # marcatore in un font display, e la stessa `O` apre `Olivia` nel font
        # del corpo. La resa dava `- livia`.
        self.assertIsNone(strippable_marker("Olivia", "Olivia", frozenset("O")))

    def test_an_alphanumeric_marker_on_its_own_primitive_is_stripped(self) -> None:
        # Su Vil il pallino e' `h` in `NelsonOrnaments`, primitiva sua.
        self.assertEqual(
            strippable_marker("h Utilizzo. Richiede tempo", "h", frozenset("h")),
            "h ",
        )

    def test_a_symbol_marker_is_stripped_even_inside_a_primitive(self) -> None:
        # `✦Effetto Pieno:` su DB: il glifo non ha una primitiva sua e resta un
        # pallino. La condizione della primitiva vale solo per gli alfanumerici.
        self.assertEqual(
            strippable_marker("✦Effetto Pieno:", "✦Effetto Pieno:", frozenset("✦")),
            "✦",
        )

    def test_a_line_without_a_marker_has_nothing_to_strip(self) -> None:
        self.assertIsNone(strippable_marker("Prosa normale", "Prosa", frozenset("•")))


class MeasurementContractTest(unittest.TestCase):
    def test_counts_cannot_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            LineStartMeasurements({"•": -1}, {}, {}, {}, 0)

    def test_keys_must_be_single_characters(self) -> None:
        with self.assertRaises(ValueError):
            LineStartMeasurements({"••": 1}, {}, {}, {}, 0)


class BindMarkerGlyphsTest(unittest.TestCase):
    """Il glifo d'elenco riattaccato al testo della sua voce."""

    def _line(
        self, block: str, line: str, text: str, x: float = 0.0, y: float = 0.0
    ) -> _SourceLine:
        """Una riga sorgente con geometria vera.

        Serve davvero: il legame glifo-testo chiede che i due si sovrappongano in
        verticale, e senza bbox la regola non ha niente da guardare. Le y qui
        sono quelle misurate su FW p.168 -- il glifo a 499,2-515,2 e il suo testo
        a 499,2-519,7.
        """

        primitive = TextPrimitive(
            primitive_id=f"primitive:{block}:{line}",
            bbox=(x, y, x + 40.0, y + 16.0),
            text=text,
            source_observation_id=f"text:{block}:{line}:s0000",
        )
        return _SourceLine(block=block, line=line, text=text, primitives=(primitive,))

    def test_a_lone_glyph_takes_the_next_line_of_its_own_block(self) -> None:
        lines = [
            self._line("b0011", "l0000", "•\t", x=57.7, y=499.2),
            self._line("b0011", "l0001", "Afflizione", x=72.7, y=499.2),
        ]
        bound = bind_marker_glyphs(lines, frozenset("•"))
        self.assertEqual([line.text for line in bound], ["•\tAfflizione"])

    def test_it_crosses_lines_of_another_block_to_find_its_partner(self) -> None:
        # FW p.168: due colonne d'elenco affiancate. L'ordine di lettura mette il
        # glifo della seconda colonna fra il glifo della prima e il suo testo, e
        # senza il blocco il glifo di sinistra si prendeva il testo di destra.
        lines = [
            self._line("b0011", "l0000", "•\t", x=57.7, y=499.2),
            self._line("b0012", "l0000", "•\t", x=213.6, y=499.2),
            self._line("b0011", "l0001", "Afflizione", x=72.7, y=499.2),
            self._line("b0012", "l0001", "Bruti", x=228.6, y=499.2),
        ]
        bound = bind_marker_glyphs(lines, frozenset("•"))
        self.assertEqual([line.text for line in bound], ["•\tAfflizione", "•\tBruti"])

    def test_a_glyph_without_a_partner_is_left_alone(self) -> None:
        # Inventargli un compagno sarebbe la fusione di righe distinte che questo
        # builder ha gia' corretto tre volte.
        lines = [
            self._line("b0011", "l0000", "•", y=499.2),
            self._line("b0022", "l0000", "Prosa", y=499.2),
        ]
        bound = bind_marker_glyphs(lines, frozenset("•"))
        self.assertEqual([line.text for line in bound], ["•", "Prosa"])

    def test_without_markers_nothing_moves(self) -> None:
        lines = [
            self._line("b0011", "l0000", "•", y=499.2),
            self._line("b0011", "l0001", "X", y=499.2),
        ]
        self.assertEqual(bind_marker_glyphs(lines, frozenset()), lines)


    def test_a_partner_on_another_visual_line_is_not_taken(self) -> None:
        # DB: il glifo sta su una riga sua e la riga successiva dello stesso
        # blocco e' la CONTINUAZIONE della voce precedente, non il testo della
        # propria. Senza il vincolo verticale usciva `✦nel tempo.` come voce.
        lines = [
            self._line("b0016", "l0000", "✦", y=300.0),
            self._line("b0016", "l0001", "nel tempo.", y=284.0),
        ]
        bound = bind_marker_glyphs(lines, frozenset("✦"))
        self.assertEqual([line.text for line in bound], ["✦", "nel tempo."])


class ListItemFlagsTest(unittest.TestCase):
    """`Criterio_ScalaDiValori_v1.md` §1: l'unita' e' la corsa, non il blocco."""

    def test_a_run_across_consecutive_blocks_is_a_list(self) -> None:
        # DB idx 60: cinque `✦` in blocchi consecutivi, uno per blocco.
        lines = [(f"b{15 + i:04d}", f"✦Voce {i}") for i in range(5)]
        self.assertEqual(list_item_flags(lines, frozenset("✦")), [True] * 5)

    def test_a_gap_of_an_unmarked_block_breaks_the_run(self) -> None:
        # DB idx 13: le righe di costo stanno in b0001 e b0003, con b0002 in
        # mezzo che non porta marcatore. Una corsa di una riga non e' un elenco.
        lines = [
            ("b0001", "✦Punti Volontà: 3"),
            ("b0001", "Prosa che descrive la capacità"),
            ("b0002", "CAPACITÀ: SCONTROSO"),
            ("b0003", "✦Punti Volontà: —"),
        ]
        self.assertEqual(list_item_flags(lines, frozenset("✦")), [False] * 4)

    def test_a_run_inside_one_block_is_a_list(self) -> None:
        lines = [("b0007", f"*\t Voce {i}") for i in range(4)]
        self.assertEqual(list_item_flags(lines, frozenset("*")), [True] * 4)

    def test_a_scale_block_never_produces_items(self) -> None:
        # DrM: `!@#` sono i tre esiti di un tiro, e il glifo E' il valore.
        lines = [
            ("b0004", "!\t 5 fire damage"),
            ("b0004", "@\t 9 fire damage"),
            ("b0004", "#\t 11 fire damage"),
        ]
        markers = frozenset("!@#")
        # Gia' senza la firma: marcatori diversi non fanno corsa, e tre corse di
        # una riga non sono elenchi.
        self.assertEqual(list_item_flags(lines, markers), [False, False, False])
        self.assertEqual(
            list_item_flags(lines, markers, frozenset({("!", "@", "#")})),
            [False, False, False],
        )

    def test_a_graduated_character_is_not_a_marker_anywhere(self) -> None:
        # DrM, pagina di minion: sei blocchi consecutivi con un solo `!`
        # ciascuno, il tier `≤11` di sei creature diverse. Per la sola regola
        # delle corse sarebbero un elenco di sei voci.
        lines = [(f"b{10 + i:04d}", "!\t 2 damage") for i in range(6)]
        markers = frozenset("!@#")
        self.assertEqual(list_item_flags(lines, markers), [True] * 6)
        self.assertEqual(
            list_item_flags(lines, markers, frozenset({("!", "@", "#")})),
            [False] * 6,
        )


class MarkerFromFontTest(unittest.TestCase):
    """`Criterio_MarcatoreDaFont_v1.md`: il pallino puo' essere una lettera."""

    def _page_with_font(self, index: int, *entries) -> NormalizedPrimitivePage:
        primitives = []
        for order, (text, font) in enumerate(entries):
            primitives.append(
                TextPrimitive(
                    primitive_id=f"primitive:text:p{index}:s{order}",
                    bbox=(float(order) * 10.0, 10.0, float(order) * 10.0 + 5.0, 15.0),
                    text=text,
                    # Gli `s` diversi con lo stesso `l` sono i pezzi della
                    # STESSA riga: e' cosi' che il glifo e il testo della voce
                    # stanno insieme, come nel PDF.
                    source_observation_id=f"text:b0000:l0000:s{order:04d}",
                    font_name=font,
                )
            )
        return NormalizedPrimitivePage(
            schema_version="1",
            source_capture_id="c",
            source_id="s",
            page_id=f"page:{index:04d}",
            page_index=index,
            page_geometry=GEOMETRY,
            capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
            text_primitives=tuple(primitives),
        )

    def test_a_letter_in_a_symbol_font_is_a_marker(self) -> None:
        # Fab: il pallino e' `w` in Wingdings, e la condizione «non alfanumerico»
        # non puo' vederlo.
        # Il glifo e' una primitiva a se': e' cio' che lo distingue dalla prima
        # lettera di una parola in un font da titolo.
        pages = [
            self._page_with_font(
                i,
                ("w", "Wingdings-Regular"),
                (" Aumenti i tuoi Punti Mente", "PTSans-Narrow"),
            )
            for i in range(3)
        ]
        found = list_markers(measure_document_line_starts(pages, "PTSans-Narrow"))
        self.assertIn("w", found)

    def test_without_the_body_font_the_second_route_is_shut(self) -> None:
        pages = [
            self._page_with_font(
                i,
                ("w", "Wingdings-Regular"),
                (" Aumenti i tuoi Punti Mente", "PTSans-Narrow"),
            )
            for i in range(3)
        ]
        self.assertNotIn("w", list_markers(measure_document_line_starts(pages)))

    def test_a_letter_in_the_body_font_is_not_a_marker(self) -> None:
        pages = [
            self._page_with_font(
                i, ("w", "PTSans-Narrow"), (" una parola qualunque qui", "PTSans-Narrow")
            )
            for i in range(3)
        ]
        found = list_markers(measure_document_line_starts(pages, "PTSans-Narrow"))
        self.assertNotIn("w", found)

    def test_a_drop_cap_is_not_a_marker(self) -> None:
        # FWK: `Bruinloa` ha la `B` in un font decorativo, primitiva a se'. Un
        # pallino e' seguito da spazio, la prima lettera di una parola no.
        pages = [
            self._page_with_font(
                i, ("B", "Antonio-Bold"), ("ruinloa e la sua storia", "PTSans-Narrow")
            )
            for i in range(3)
        ]
        found = list_markers(measure_document_line_starts(pages, "PTSans-Narrow"))
        self.assertNotIn("B", found)


if __name__ == "__main__":
    unittest.main()
