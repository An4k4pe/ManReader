"""Le funzioni che decidono struttura del testo e nidificazione delle bande.

Stessa eccezione dichiarata di `tests/test_prototype_vertical_slice_page.py` al
precedente "niente test per gli script diagnostici": queste funzioni non
producono un numero riportato, **decidono**, e la revisione indipendente del
16 agosto 2026 ha rilevato che nessuno dei 1237 test le toccava -- quindi
"suite verde" non diceva nulla sui quattro cambi della sessione.

Metà di questi test sono **controlli negativi**: mostrano che la guardia
FALLISCE quando deve. Erano il rilievo centrale della revisione — quattro
criteri superati e nessuna guardia mai vista fallire non si distingue
dall'assenza di guardia.
"""

from __future__ import annotations

import unittest

from primitive_model import TextPrimitive
from scripts.compare_reading_order_with_column_bands import (
    _source_line_key,
    _source_text_lines,
)
from scripts.prototype_derived_column_bands import _GapRect, _is_subordinate
from scripts.prototype_vertical_slice_page import _source_block


def _span(
    block: int,
    line: int,
    span: int,
    text: str,
    bbox: tuple[float, float, float, float],
) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=f"p:{block}:{line}:{span}",
        bbox=bbox,
        text=text,
        source_observation_id=f"text:b{block:04d}:l{line:04d}:s{span:04d}",
    )


class SourceStructureTest(unittest.TestCase):
    """Riga e paragrafo vengono dall'id, non dalla geometria."""

    def test_line_groups_by_block_and_line_not_by_geometry(self) -> None:
        # Due span alla STESSA y ma in blocchi diversi: sono due colonne, e la
        # ricostruzione geometrica li fondeva (Dag p.48, 21 fusioni).
        left = _span(8, 1, 0, "sinistra", (50.0, 100.0, 200.0, 112.0))
        right = _span(24, 1, 0, "destra", (350.0, 100.0, 500.0, 112.0))

        lines = _source_text_lines([left, right])

        self.assertEqual(len(lines), 2)
        self.assertEqual([[p.text for p in line] for line in lines], [["sinistra"], ["destra"]])

    def test_line_keeps_spans_of_one_source_line_together(self) -> None:
        # Sette span della stessa riga con y che differiscono di frazioni di
        # punto: e' il caso di Dag p.48 y 410,89-411,01.
        spans = [
            _span(8, 2, 0, "il vostro ", (306.0, 411.01, 338.2, 422.2)),
            _span(8, 2, 1, "Focus", (338.3, 411.01, 359.6, 422.2)),
            _span(8, 2, 2, ", potete ", (359.6, 410.90, 391.1, 422.1)),
        ]

        lines = _source_text_lines(list(reversed(spans)))

        self.assertEqual(len(lines), 1)
        self.assertEqual("".join(p.text for p in lines[0]), "il vostro Focus, potete ")

    def test_line_never_merges_primitives_with_unreadable_ids(self) -> None:
        # Non si indovina: un id non interpretabile e' una riga a se'.
        a = TextPrimitive(
            primitive_id="a", bbox=(0.0, 0.0, 10.0, 10.0), text="a", source_observation_id="?"
        )
        b = TextPrimitive(
            primitive_id="b", bbox=(0.0, 0.0, 10.0, 10.0), text="b", source_observation_id="?"
        )

        self.assertEqual(len(_source_text_lines([a, b])), 2)

    def test_block_is_the_paragraph(self) -> None:
        self.assertEqual(_source_block(_span(3, 0, 0, "x", (0.0, 0.0, 1.0, 1.0))), 3)

    def test_block_is_none_when_the_id_is_not_a_text_observation(self) -> None:
        primitive = TextPrimitive(
            primitive_id="p", bbox=(0.0, 0.0, 1.0, 1.0), text="x", source_observation_id="image:i0"
        )
        self.assertIsNone(_source_block(primitive))

    def test_line_key_returns_all_three_levels(self) -> None:
        self.assertEqual(_source_line_key(_span(4, 5, 6, "x", (0.0, 0.0, 1.0, 1.0))), (4, 5, 6))


class IsSubordinateTest(unittest.TestCase):
    """La nidificazione si decide sui probatori, non sullo span."""

    @staticmethod
    def _rect(x0: int, x1: int, y0: float, y1: float, span: tuple[float, float]) -> _GapRect:
        rect = _GapRect(x0, x1, y0, y1)
        rect.span_y0, rect.span_y1 = span
        return rect

    def test_disjoint_probative_extents_are_not_subordinate(self) -> None:
        """Il caso DB p.53, ed e' il motivo del cambio.

        Le due strutture sono impilate con quaranta punti di vuoto fra loro; solo
        l'estensione li colma. Con lo span il box diventava figlio della tabella
        ed ereditava un confine x che nel box non esiste.
        """

        box = self._rect(295, 313, 60.0, 120.0, (46.0, 176.0))
        table = self._rect(167, 177, 160.0, 504.0, (120.0, 582.0))

        self.assertFalse(_is_subordinate(box, table))

    def test_overlapping_probative_extents_are_still_subordinate(self) -> None:
        """Controllo negativo del controllo: il cambio non spegne la funzione.

        Il caso di DB p.18 citato dalla docstring -- un gutter di tabella
        interamente a destra di un gutter di pagina, con le y che si
        sovrappongono davvero -- deve restare subordinato.
        """

        inner = self._rect(338, 342, 500.0, 640.0, (498.0, 650.0))
        outer = self._rect(301, 319, 488.0, 668.0, (486.0, 670.0))

        self.assertTrue(_is_subordinate(inner, outer))

    def test_overlapping_x_is_never_subordinate(self) -> None:
        inner = self._rect(300, 320, 500.0, 640.0, (498.0, 650.0))
        outer = self._rect(310, 330, 488.0, 668.0, (486.0, 670.0))

        self.assertFalse(_is_subordinate(inner, outer))

    def test_the_less_extended_one_is_never_the_parent(self) -> None:
        inner = self._rect(338, 342, 400.0, 700.0, (398.0, 702.0))
        outer = self._rect(301, 319, 488.0, 668.0, (486.0, 670.0))

        self.assertFalse(_is_subordinate(inner, outer))


if __name__ == "__main__":
    unittest.main()
