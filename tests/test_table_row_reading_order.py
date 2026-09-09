"""La lettura per righe di una regione di tabella.

Milestone 44, Fase 3. Il caso che conta e' il primo: la riga del numero e la
prima riga della descrizione hanno `y` che differiscono di frazioni di punto, e
ordinando per `y` il numero finisce dentro la frase. Gli altri verificano che la
cella che va a capo non rompa le righe, che una riga a tutta larghezza resti al
suo posto, e che nulla venga aggiunto o perso.
"""

from __future__ import annotations

import unittest

from primitive_model import TextPrimitive
from table_row_reading_order import order_table_lines_by_rows

CONFINI = ((90.0, 100.0),)


def _riga(nome: str, x0: float, x1: float, y0: float) -> tuple[TextPrimitive, ...]:
    return (
        TextPrimitive(
            primitive_id=f"p:{nome}",
            bbox=(x0, y0, x1, y0 + 11.0),
            text=nome,
            source_observation_id="text:b0000:l0000:s0000",
        ),
    )


def _testi(righe: tuple[tuple[TextPrimitive, ...], ...]) -> list[str]:
    return [primitiva.text for riga in righe for primitiva in riga]


class OrderTableLinesByRowsTest(unittest.TestCase):
    def test_the_row_number_comes_before_its_text_despite_a_lower_y(self) -> None:
        numero = _riga("1", 76.0, 82.0, 167.0)
        testo = _riga("Goblin all'attacco!", 110.0, 540.0, 166.9)

        ordinate = order_table_lines_by_rows((testo, numero), column_boundaries=CONFINI)

        self.assertEqual(_testi(ordinate), ["1", "Goblin all'attacco!"])

    def test_a_wrapped_cell_keeps_the_reading_order(self) -> None:
        righe = (
            _riga("1", 76.0, 82.0, 167.0),
            _riga("prima riga", 110.0, 540.0, 166.9),
            _riga("seconda riga", 110.0, 540.0, 179.0),
            _riga("terza riga", 110.0, 540.0, 191.0),
            _riga("2", 76.0, 82.0, 219.4),
            _riga("altra voce", 110.0, 540.0, 219.5),
        )

        ordinate = order_table_lines_by_rows(righe, column_boundaries=CONFINI)

        self.assertEqual(
            _testi(ordinate),
            ["1", "prima riga", "seconda riga", "terza riga", "2", "altra voce"],
        )

    def test_a_full_width_line_stays_in_place(self) -> None:
        righe = (
            _riga("ATTACCHI MOSTRUOSI", 70.0, 540.0, 150.0),
            _riga("1", 76.0, 82.0, 167.0),
            _riga("descrizione", 110.0, 540.0, 166.9),
        )

        ordinate = order_table_lines_by_rows(righe, column_boundaries=CONFINI)

        self.assertEqual(_testi(ordinate), ["ATTACCHI MOSTRUOSI", "1", "descrizione"])

    def test_without_boundaries_the_order_is_vertical(self) -> None:
        righe = (_riga("seconda", 70.0, 300.0, 200.0), _riga("prima", 70.0, 300.0, 100.0))

        ordinate = order_table_lines_by_rows(righe, column_boundaries=())

        self.assertEqual(_testi(ordinate), ["prima", "seconda"])

    def test_nothing_is_added_or_lost(self) -> None:
        righe = (
            _riga("1", 76.0, 82.0, 167.0),
            _riga("a", 110.0, 540.0, 166.9),
            _riga("2", 76.0, 82.0, 219.4),
            _riga("b", 110.0, 540.0, 219.5),
        )

        ordinate = order_table_lines_by_rows(righe, column_boundaries=CONFINI)

        self.assertEqual(sorted(_testi(ordinate)), sorted(_testi(righe)))
        self.assertEqual(len(ordinate), len(righe))

    def test_an_empty_region_has_nothing_to_order(self) -> None:
        self.assertEqual(order_table_lines_by_rows((), column_boundaries=CONFINI), ())
        self.assertEqual(order_table_lines_by_rows(((),), column_boundaries=CONFINI), ())


if __name__ == "__main__":
    unittest.main()
