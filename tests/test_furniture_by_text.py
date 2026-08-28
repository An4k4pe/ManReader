"""Tests per il ramo 4 dell'arredo: il testo che ripete, e il testo verticale.

`Criterio_ArredoPerTesto_v1.md`. Generalizza il ramo 1 -- che gia' non ha vincolo
di posizione -- da «il numero di pagina» a «qualunque testo che si ripete».
"""

from __future__ import annotations

import unittest

from document_furniture_policy import repeated_text_slots, vertical_slots
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRY = PageGeometry(
    width=100.0, height=100.0, unit="pt", coordinate_system="top_left_y_down"
)


def _page(index: int, *entries) -> NormalizedPrimitivePage:
    primitives = []
    for order, entry in enumerate(entries):
        text, x, y = entry[:3]
        direction = entry[3] if len(entry) > 3 else (1.0, 0.0)
        primitives.append(
            TextPrimitive(
                primitive_id=f"primitive:text:p{index}:s{order}",
                bbox=(x, y, x + 5.0, y + 5.0),
                text=text,
                source_observation_id=f"text:b0000:l{order:04d}:s0000",
                direction=direction,
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


class RepeatedTextSlotsTest(unittest.TestCase):
    def test_a_slot_that_repeats_the_same_text_is_furniture_anywhere(self) -> None:
        # FWK `Capitolo 5` in cima: 3 testi distinti su 11 pagine. Nessuna fascia.
        pages = [_page(i, ("Capitolo 5", 44.0, 2.0)) for i in range(8)]
        self.assertIn((44, 2), repeated_text_slots(pages))

    def test_a_slot_whose_text_changes_every_page_is_not_furniture(self) -> None:
        # BiD: 10 testi distinti su 10 pagine all'inizio della colonna; DrM: i
        # titoli di scheda, 9 su 9. Sono contenuto e restano.
        pages = [_page(i, (f"TITOLO DIVERSO {i}", 16.0, 7.0)) for i in range(8)]
        self.assertNotIn((16, 7), repeated_text_slots(pages))

    def test_a_slot_seen_too_rarely_is_not_furniture(self) -> None:
        # Due pagine su dodici stanno sotto un quarto: la ricorrenza dello slot
        # resta la guardia, come nel ramo 1.
        pages = [_page(i, (f"prosa della pagina {i}", 50.0, 50.0)) for i in range(12)]
        pages[0] = _page(0, ("Ripetuto", 44.0, 2.0))
        pages[1] = _page(1, ("Ripetuto", 44.0, 2.0))
        self.assertNotIn((44, 2), repeated_text_slots(pages))


class VerticalSlotsTest(unittest.TestCase):
    def test_non_horizontal_text_is_furniture(self) -> None:
        # BiD: `ATTIVITÀ DI DOWNTIME` a direzione (0,-1) sul bordo destro e
        # `DOWNTIME` a (0,1) sul sinistro, specchiati fra recto e verso.
        pages = [
            _page(0, ("ATTIVITÀ DI DOWNTIME", 96.0, 18.0, (0.0, -1.0))),
            _page(1, ("DOWNTIME", 1.0, 23.0, (0.0, 1.0))),
        ]
        found = vertical_slots(pages)
        self.assertIn((96, 18), found)
        self.assertIn((1, 23), found)

    def test_horizontal_text_is_left_alone(self) -> None:
        # Il titolo vero di BiD e' l'orizzontale a corpo 30, e compare una volta
        # sola a capo del capitolo.
        pages = [_page(0, ("attività di downtime", 14.0, 7.0, (1.0, 0.0)))]
        self.assertEqual(vertical_slots(pages), frozenset())

    def test_a_primitive_without_a_direction_is_left_alone(self) -> None:
        page = NormalizedPrimitivePage(
            schema_version="1",
            source_capture_id="c",
            source_id="s",
            page_id="page:0000",
            page_index=0,
            page_geometry=GEOMETRY,
            capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
            text_primitives=(
                TextPrimitive(
                    primitive_id="p",
                    bbox=(1.0, 1.0, 6.0, 6.0),
                    text="senza direzione",
                    source_observation_id="text:b0000:l0000:s0000",
                ),
            ),
        )
        self.assertEqual(vertical_slots([page]), frozenset())


if __name__ == "__main__":
    unittest.main()
