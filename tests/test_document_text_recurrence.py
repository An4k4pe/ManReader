import unittest

from document_text_recurrence_measurements import (
    DocumentTextRecurrenceMeasurements,
    TextSlotRecurrence,
    measure_document_text_recurrence,
    normalize_text,
)
from geometry_model import PageGeometry
from primitive_model import NormalizedPrimitivePage, TextPrimitive

GEOMETRY = PageGeometry(
    width=100.0,
    height=100.0,
    unit="pt",
    coordinate_system="top_left_y_down",
)


def _page(index: int, *texts_at: tuple[str, float, float]) -> NormalizedPrimitivePage:
    primitives = tuple(
        TextPrimitive(
            primitive_id=f"primitive:text:p{index}:s{order}",
            bbox=(x, y, x + 5.0, y + 5.0),
            text=text,
            source_observation_id=f"text:b0000:l0000:s{order:04d}",
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


class NormalizeTextTest(unittest.TestCase):
    def test_strips_and_collapses_only(self) -> None:
        self.assertEqual(normalize_text("  Capitolo   7 \n"), "Capitolo 7")

    def test_case_and_punctuation_survive(self) -> None:
        # Ogni pulizia in piu' sarebbe un giudizio su cosa sia "lo stesso testo".
        self.assertEqual(normalize_text("CAPITOLO 7 – Bestiario"), "CAPITOLO 7 – Bestiario")


class MeasureRecurrenceTest(unittest.TestCase):
    def test_a_constant_watermark_occupies_one_slot_with_one_text(self) -> None:
        pages = [_page(i, ("Andrea Bruna", 10.0, 96.0)) for i in range(4)]
        measured = measure_document_text_recurrence(pages)
        self.assertEqual(len(measured.slots), 1)
        slot = measured.slots[0]
        self.assertEqual(slot.page_count, 4)
        self.assertEqual(slot.texts, ("Andrea Bruna",))

    def test_a_page_number_occupies_one_slot_with_many_texts(self) -> None:
        # Il caso che una chiave sul TESTO renderebbe invisibile: stesso punto,
        # testo diverso a ogni pagina. Misurato su DIE, 30 testi in uno slot.
        pages = [_page(i, (str(100 + i), 90.0, 95.0)) for i in range(5)]
        measured = measure_document_text_recurrence(pages)
        self.assertEqual(len(measured.slots), 1)
        self.assertEqual(measured.slots[0].page_count, 5)
        self.assertEqual(len(measured.slots[0].texts), 5)

    def test_content_repeating_at_different_places_does_not_pile_up(self) -> None:
        # `Movimento:` si ripete su ogni pagina di bestiario ed e' contenuto:
        # si ripete pero' a y qualsiasi, ed e' la posizione a fare il lavoro.
        pages = [_page(i, ("Movimento:", 10.0, 20.0 + i * 10)) for i in range(4)]
        measured = measure_document_text_recurrence(pages)
        self.assertEqual(len(measured.slots), 4)
        self.assertTrue(all(slot.page_count == 1 for slot in measured.slots))

    def test_the_share_helper_never_applies_a_threshold_of_its_own(self) -> None:
        pages = [_page(i, ("fisso", 10.0, 96.0)) for i in range(4)]
        pages.append(_page(4, ("altro", 50.0, 50.0)))
        measured = measure_document_text_recurrence(pages)
        self.assertEqual(len(measured.occupied_on_at_least(0.5)), 1)
        self.assertEqual(len(measured.occupied_on_at_least(1.0)), 0)
        self.assertEqual(len(measured.occupied_on_at_least(0.2)), 2)

    def test_empty_text_contributes_nothing(self) -> None:
        measured = measure_document_text_recurrence([_page(0, ("  ", 10.0, 10.0))])
        self.assertEqual(measured.slots, ())

    def test_a_repeated_page_index_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            measure_document_text_recurrence([_page(0, ("a", 1.0, 1.0)), _page(0, ("b", 1.0, 1.0))])

    def test_no_pages_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            measure_document_text_recurrence([])


class ContractTest(unittest.TestCase):
    def test_a_slot_cannot_claim_more_pages_than_the_document_has(self) -> None:
        slot = TextSlotRecurrence(x=1, y=1, page_count=3, page_indices=(0, 1, 2), texts=("a",))
        with self.assertRaises(ValueError):
            DocumentTextRecurrenceMeasurements(page_count=2, slots=(slot,))

    def test_page_indices_must_match_the_count(self) -> None:
        with self.assertRaises(ValueError):
            TextSlotRecurrence(x=0, y=0, page_count=2, page_indices=(0,), texts=("a",))


if __name__ == "__main__":
    unittest.main()


class OffPageSlotTest(unittest.TestCase):
    def test_a_slot_outside_the_page_is_a_position_not_an_error(self) -> None:
        # Il vivo di stampa: un testo puo' stare oltre il bordo. Una prima
        # versione validava x e y non-negativi e falliva su Apo alla prima
        # esecuzione fuori dai manuali di progettazione.
        slot = TextSlotRecurrence(x=-3, y=-1, page_count=1, page_indices=(0,), texts=("a",))
        self.assertEqual((slot.x, slot.y), (-3, -1))

    def test_a_primitive_above_the_page_top_is_measured(self) -> None:
        page = _page(0, ("bleed", 10.0, -4.0))
        measured = measure_document_text_recurrence([page])
        self.assertEqual(len(measured.slots), 1)
        self.assertLess(measured.slots[0].y, 0)
