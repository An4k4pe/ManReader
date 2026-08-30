"""Tests per il ramo 4 dell'arredo: il testo che ripete, e il testo verticale.

`Criterio_ArredoPerTesto_v1.md`. Generalizza il ramo 1 -- che gia' non ha vincolo
di posizione -- da «il numero di pagina» a «qualunque testo che si ripete».
"""

from __future__ import annotations

import unittest

from document_furniture_policy import (
    repeated_text_slots,
    running_head_primitive_ids,
    running_heads,
    vertical_primitive_ids,
)
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


class VerticalPrimitivesTest(unittest.TestCase):
    """La verticalita' e' della PRIMITIVA, e di UNA pagina."""

    def test_non_horizontal_text_is_furniture(self) -> None:
        page = _page(0, ("ATTIVITÀ DI DOWNTIME", 96.0, 18.0, (0.0, -1.0)))
        self.assertEqual(len(vertical_primitive_ids(page)), 1)

    def test_horizontal_text_is_left_alone(self) -> None:
        # Il titolo vero di BiD e' l'orizzontale a corpo 30, e compare una volta
        # sola a capo del capitolo.
        page = _page(0, ("attività di downtime", 14.0, 7.0, (1.0, 0.0)))
        self.assertEqual(vertical_primitive_ids(page), frozenset())

    def test_only_the_vertical_one_of_a_page_is_taken(self) -> None:
        # Su Fab lo slot (14,57) porta `CONGEDO` in verticale su una pagina e
        # prosa orizzontale su altre: marcare lo SLOT toglieva la prosa.
        page = _page(
            0,
            ("CONGEDO", 14.0, 57.0, (0.0, -1.0)),
            ("perfetti per viaggiare, e combatte con", 14.0, 57.0, (1.0, 0.0)),
        )
        found = vertical_primitive_ids(page)
        self.assertEqual(len(found), 1)
        self.assertIn("primitive:text:p0:s0", found)

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
        self.assertEqual(vertical_primitive_ids(page), frozenset())


class RepeatedTextWithdrawnTest(unittest.TestCase):
    def test_it_is_computed_but_not_used(self) -> None:
        # Ritirata dopo il giudizio: toglieva contenuto su 7 voci su 12.
        # `all_slots` non la include piu'.
        from document_furniture_policy import FurnitureSlots

        slots = FurnitureSlots(
            from_label=frozenset(),
            from_recurrence=frozenset(),
            from_repeated_text=frozenset({(44, 2)}),
        )
        self.assertNotIn((44, 2), slots.all_slots)


class RunningHeadTest(unittest.TestCase):
    """`Criterio_TestatinaCorrente_v1.md`: parte dal TESTO, non dallo slot."""

    def test_a_text_always_in_one_place_is_a_running_head(self) -> None:
        # `Capitolo 6` di FWK, `PREMI START` di Fab: qualunque posizione.
        pages = [_page(i, ("Capitolo 6", 44.0, 2.0)) for i in range(8)]
        self.assertIn(("Capitolo 6", (44, 2)), running_heads(pages))

    def test_position_is_not_constrained(self) -> None:
        # Su Fab la testatina sta al LATO, y=43.
        pages = [_page(i, ("PREMI START", 93.0, 43.0)) for i in range(8)]
        self.assertIn(("PREMI START", (93, 43)), running_heads(pages))

    def test_a_text_that_moves_around_is_not_a_running_head(self) -> None:
        # E' la distinzione che la clausola A non faceva: `Stamina` di Draw Steel
        # compare su 16 pagine sparsa su 31 slot, perche' la scheda si sposta col
        # contenuto. Una testatina no.
        pages = [_page(i, ("Stamina", 12.0, 20.0 + i * 4.0)) for i in range(8)]
        self.assertEqual(running_heads(pages), frozenset())

    def test_the_two_mirrored_sides_are_counted_together(self) -> None:
        # Lo specchio si calcola sul CENTRO: con una larghezza di 5, il gemello
        # di `x=6` sta a `x=89`, non a `x=91`. E' la stessa correzione che su Kul
        # distingue `x=25` da `100-72`.
        pages = []
        for i in range(10):
            x = 89.0 if i % 2 else 6.0
            pages.append(_page(i, ("Il Mondo", x, 2.0)))
        found = {slot for _text, slot in running_heads(pages)}
        self.assertIn((6, 2), found)
        self.assertIn((89, 2), found)

    def test_a_text_seen_too_rarely_is_not_a_running_head(self) -> None:
        pages = [_page(i, (f"prosa della pagina {i}", 10.0, 50.0)) for i in range(12)]
        pages[0] = _page(0, ("Capitolo 6", 44.0, 2.0))
        pages[1] = _page(1, ("Capitolo 6", 44.0, 2.0))
        self.assertEqual(running_heads(pages), frozenset())


    def test_a_section_title_sharing_the_slot_is_not_removed(self) -> None:
        # Su Vil lo slot (13,11) porta `G I O C A R E` su quattro pagine e
        # TREDICI titoli di sezione diversi sulle altre. Togliere lo slot li
        # portava via tutti: si toglie la coppia (testo, slot), non la posizione.
        pages = []
        for i in range(12):
            testo = "G I O C A R E" if i % 3 == 0 else f"TITOLO NUMERO {i}"
            pages.append(_page(i, (testo, 13.0, 11.0)))
        heads = running_heads(pages)
        self.assertIn(("G I O C A R E", (13, 11)), heads)
        titolo = _page(1, ("TITOLO NUMERO 1", 13.0, 11.0))
        self.assertEqual(running_head_primitive_ids(titolo, heads), frozenset())
        testatina = _page(0, ("G I O C A R E", 13.0, 11.0))
        self.assertEqual(len(running_head_primitive_ids(testatina, heads)), 1)


if __name__ == "__main__":
    unittest.main()
