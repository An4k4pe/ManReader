"""Tests per la deduzione del numero stampato di `scripts/measure_furniture_coverage.py`.

Eccezione dichiarata al precedente «niente test per gli script diagnostici»: qui
la funzione non riporta un numero, **produce il denominatore su cui si decide se
il pavimento di `Criterio_ArredoRicorrente_v3.md` §5 regge o cade**. Nella prima
versione sbagliava di un fattore due, il verdetto ne dipendeva, e nessun test
l'avrebbe visto.
"""

from __future__ import annotations

import unittest

from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive
from scripts.measure_furniture_coverage import deduce_printed_numbers

GEOMETRY = PageGeometry(
    width=100.0, height=100.0, unit="pt", coordinate_system="top_left_y_down"
)


def _page(index: int, *texts_at: tuple[str, float, float]) -> NormalizedPrimitivePage:
    primitives = tuple(
        TextPrimitive(
            primitive_id=f"primitive:text:p{index}:s{order}",
            bbox=(x, y, x + 5.0, y + 5.0),
            text=text,
            source_observation_id=f"text:b0000:l{order:04d}:s0000",
        )
        for order, (text, x, y) in enumerate(texts_at)
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


class DeducePrintedNumbersTest(unittest.TestCase):
    def test_merges_a_number_printed_on_alternating_sides(self) -> None:
        # FW e FWK: il numero sta al centro dei lati e cambia lato a ogni pagina,
        # quindi ogni slot ne porta meta'. Prenderne uno solo dimezzava il
        # denominatore del pavimento.
        pages = [
            _page(i, (str(140 + i), 94.0 if i % 2 else 1.0, 49.0)) for i in range(12)
        ]
        deduced = deduce_printed_numbers(pages)
        self.assertEqual(len(deduced), 12)
        self.assertEqual(deduced[0], "140")
        self.assertEqual(deduced[11], "151")

    def test_refuses_when_the_merged_sequence_is_not_monotone(self) -> None:
        # Due slot ciascuno crescente possono intrecciarsi in qualcosa che non lo
        # e': due colonne di valori di scheda, per dire. Non e' un numero di
        # pagina, e la misura non deve fingere di saperlo.
        pages = []
        for i in range(12):
            pages.append(_page(i, (str(500 + i), 20.0, 40.0), (str(100 + i), 60.0, 40.0)))
        self.assertEqual(deduce_printed_numbers(pages), {})

    def test_ignores_a_slot_that_carries_numbers_too_rarely(self) -> None:
        pages = [_page(i) for i in range(12)]
        pages[0] = _page(0, ("7", 50.0, 50.0))
        pages[1] = _page(1, ("8", 50.0, 50.0))
        self.assertEqual(deduce_printed_numbers(pages), {})

    def test_no_numbers_at_all_deduces_nothing(self) -> None:
        pages = [_page(i, ("Il Master e' una classe", 10.0, 40.0)) for i in range(12)]
        self.assertEqual(deduce_printed_numbers(pages), {})


if __name__ == "__main__":
    unittest.main()
