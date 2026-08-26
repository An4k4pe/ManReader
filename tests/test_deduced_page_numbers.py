"""Tests per il ramo 3 di `document_furniture_policy`: il numero **dedotto**.

`Criterio_NumeroDedotto_v1.md` §1. La funzione ha due mestieri e li fa con lo
stesso codice: e' il denominatore della misura di copertura, ed e' la regola che
decide quali slot escono dal corpo. Nella prima versione sbagliava di un fattore
due -- prendeva un solo slot dove il numero alterna i lati -- e il verdetto sul
pavimento ne dipendeva.

I casi di **rifiuto** contano quanto quelli di successo: un meccanismo che deduce
sempre qualcosa non e' falsificabile.
"""

from __future__ import annotations

import unittest

from document_furniture_policy import deduced_number_slots
from geometry_model import PageGeometry
from ir2_model import PageIR2
from primitive_model import NormalizedPrimitivePage, TextPrimitive

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


class DeducedNumberSlotsTest(unittest.TestCase):
    def test_merges_a_number_printed_on_alternating_sides(self) -> None:
        # FW e FWK: il numero sta al centro dei lati e cambia lato a ogni pagina,
        # quindi ogni slot ne porta meta'. Prenderne uno solo dimezzava il
        # denominatore del pavimento.
        pages = [
            _page(i, (str(140 + i), 94.0 if i % 2 else 1.0, 49.0)) for i in range(12)
        ]
        found = deduced_number_slots(pages)
        self.assertEqual(found.slots, frozenset({(94, 49), (1, 49)}))
        self.assertEqual(len(found.by_page_position), 12)
        self.assertEqual(found.by_page_position[0], "140")
        self.assertEqual(found.by_page_position[11], "151")

    def test_refuses_when_the_merged_sequence_is_not_monotone(self) -> None:
        # Due slot ciascuno crescente possono intrecciarsi in qualcosa che non lo
        # e': due colonne di valori di scheda, per dire. Non e' un numero di
        # pagina, e la misura non deve fingere di saperlo.
        pages = []
        for i in range(12):
            pages.append(_page(i, (str(500 + i), 20.0, 40.0), (str(100 + i), 60.0, 40.0)))
        self.assertFalse(deduced_number_slots(pages))

    def test_ignores_a_slot_that_carries_numbers_too_rarely(self) -> None:
        pages = [_page(i) for i in range(12)]
        pages[0] = _page(0, ("7", 50.0, 50.0))
        pages[1] = _page(1, ("8", 50.0, 50.0))
        self.assertFalse(deduced_number_slots(pages))

    def test_no_numbers_at_all_deduces_nothing(self) -> None:
        pages = [_page(i, ("Il Master e' una classe", 10.0, 40.0)) for i in range(12)]
        self.assertFalse(deduced_number_slots(pages))


class DeducedLabelContractTest(unittest.TestCase):
    def test_a_deduced_flag_without_a_label_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            PageIR2(page_id="page:0001", page_label_deduced=True)


if __name__ == "__main__":
    unittest.main()
