import unittest

from document_furniture_policy import (
    furniture_node_ids,
    label_slots,
    mirrored,
    mirrored_centre,
    recurrent_edge_slots,
)
from document_text_recurrence_measurements import measure_document_text_recurrence
from geometry_model import PageGeometry
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


class LabelBranchTest(unittest.TestCase):
    """Ramo 1: lo slot che porta l'etichetta della PROPRIA pagina."""

    def test_finds_the_page_number_wherever_it_sits(self) -> None:
        # BoB lo stampa sul lato destro in alto, Kul in cima: il ramo non ha
        # vincolo di posizione, e una fascia bassa li perdeva entrambi.
        pages = [(_page(i, (str(100 + i), 91.0, 18.0)), str(100 + i)) for i in range(8)]
        self.assertEqual(label_slots(pages), frozenset({(91, 18)}))

    def test_two_slots_when_the_number_alternates(self) -> None:
        pages = []
        for i in range(10):
            x = 91.0 if i % 2 else 5.0
            pages.append((_page(i, (str(200 + i), x, 94.0)), str(200 + i)))
        self.assertEqual(label_slots(pages), frozenset({(91, 94), (5, 94)}))

    def test_a_body_number_colliding_once_is_not_furniture(self) -> None:
        # Uno slot di corpo che porta sempre `6` -- un valore di scheda, per
        # dire. Combacia con l'etichetta solo sulla pagina numerata 6, cioe' una
        # volta su dieci, e una volta non fa un arredo. E' la ragione per cui la
        # guardia e' la ricorrenza dello slot e non la posizione.
        pages = [(_page(i, ("6", 50.0, 40.0)), str(100 + i)) for i in range(9)]
        pages.append((_page(9, ("6", 50.0, 40.0)), "6"))
        self.assertNotIn((50, 40), label_slots(pages))

    def test_a_slot_that_always_carries_its_own_number_is_furniture(self) -> None:
        # Il rovescio, ed e' voluto: uno slot che porta l'etichetta della propria
        # pagina pagina dopo pagina E' il numero di pagina, ovunque si trovi.
        pages = [(_page(i, (str(100 + i), 50.0, 40.0)), str(100 + i)) for i in range(9)]
        self.assertIn((50, 40), label_slots(pages))

    def test_without_declared_labels_it_removes_nothing(self) -> None:
        # Wil: stampa i numeri e non dichiara nulla. Il fatto e' la
        # dichiarazione del documento, non il numero sulla pagina.
        pages = [(_page(i, (str(100 + i), 91.0, 94.0)), "") for i in range(8)]
        self.assertEqual(label_slots(pages), frozenset())

    def test_a_bracketed_number_still_carries_its_label(self) -> None:
        # Lan stampa `[99]` per l'etichetta `99`: contenimento, non uguaglianza.
        pages = [(_page(i, (f"[{100 + i}]", 92.0, 96.0)), str(100 + i)) for i in range(8)]
        self.assertEqual(label_slots(pages), frozenset({(92, 96)}))

    def test_a_long_text_containing_the_label_is_not_the_number(self) -> None:
        pages = [
            (_page(i, (f"Capitolo {100 + i} e altro ancora", 20.0, 96.0)), str(100 + i))
            for i in range(8)
        ]
        self.assertEqual(label_slots(pages), frozenset())


class RecurrenceBranchTest(unittest.TestCase):
    """Ramo 2: ricorrente E al bordo inferiore."""

    def test_takes_a_recurrent_slot_at_the_bottom(self) -> None:
        measured = measure_document_text_recurrence(
            [_page(i, ("Andrea Bruna", 10.0, 96.0)) for i in range(8)]
        )
        self.assertEqual(recurrent_edge_slots(measured), frozenset({(10, 96)}))

    def test_leaves_a_recurrent_slot_in_the_body(self) -> None:
        # La fascia e' cio' che impedisce di prendere le voci d'indice e i
        # titoli di sezione, che ricorrono a posizione fissa ma non al bordo.
        measured = measure_document_text_recurrence(
            [_page(i, ("Abilita' 25, 30-39", 10.0, 16.0)) for i in range(8)]
        )
        self.assertEqual(recurrent_edge_slots(measured), frozenset())

    def test_leaves_a_one_off_at_the_bottom(self) -> None:
        # Su Lan la fascia SENZA ricorrenza prendeva `+1`, `.`, `La`.
        pages = [_page(i, ("Andrea Bruna", 10.0, 96.0)) for i in range(8)]
        pages.append(_page(8, ("PNU Classe Student", 40.0, 96.0)))
        measured = measure_document_text_recurrence(pages)
        self.assertEqual(recurrent_edge_slots(measured), frozenset({(10, 96)}))

    def test_the_upper_band_is_never_taken(self) -> None:
        measured = measure_document_text_recurrence(
            [_page(i, ("ARTEFICE", 12.0, 3.0)) for i in range(8)]
        )
        self.assertEqual(recurrent_edge_slots(measured), frozenset())


class NodeSelectionTest(unittest.TestCase):
    def test_a_node_entirely_in_furniture_slots_is_excluded(self) -> None:
        page = _page(0, ("329", 90.0, 95.0), ("Il Master e' una classe", 10.0, 40.0))
        nodes = [
            ("n:numero", ["primitive:text:p0:s0"]),
            ("n:prosa", ["primitive:text:p0:s1"]),
        ]
        self.assertEqual(
            furniture_node_ids(page, nodes, frozenset({(90, 95)})), frozenset({"n:numero"})
        )

    def test_a_mixed_node_stays_in_the_body(self) -> None:
        # Conservativo per la stessa ragione della barra a zero: un nodo misto
        # e' arredo fuso con contenuto, e toglierlo perderebbe il secondo.
        page = _page(0, ("329", 90.0, 95.0), ("Il Master e' una classe", 10.0, 40.0))
        nodes = [("n:misto", ["primitive:text:p0:s0", "primitive:text:p0:s1"])]
        self.assertEqual(furniture_node_ids(page, nodes, frozenset({(90, 95)})), frozenset())

    def test_an_empty_span_does_not_make_a_node_furniture(self) -> None:
        page = _page(0, ("  ", 90.0, 95.0))
        nodes = [("n:vuoto", ["primitive:text:p0:s0"])]
        self.assertEqual(furniture_node_ids(page, nodes, frozenset({(90, 95)})), frozenset())


class MirroringTest(unittest.TestCase):
    """Un arredo non centrato si specchia fra recto e verso."""

    def test_the_two_sides_share_a_key(self) -> None:
        self.assertEqual(mirrored((6, 95)), mirrored((94, 95)))

    def test_the_height_is_not_mirrored(self) -> None:
        self.assertNotEqual(mirrored((6, 95)), mirrored((6, 5)))

    def test_the_centre_mirrors_where_the_left_edge_does_not(self) -> None:
        # Kul: il numero sta a x=25 sul verso e x=72 sul recto, e `100-72` fa 28.
        # Lo specchio del bordo sinistro di un elemento allineato a destra e' il
        # suo bordo destro; il centro invece si riflette esatto.
        verso = TextPrimitive(
            primitive_id="p:verso",
            bbox=(25.0, 4.0, 28.0, 8.0),
            text="112",
            source_observation_id="text:b0000:l0000:s0000",
        )
        recto = TextPrimitive(
            primitive_id="p:recto",
            bbox=(72.0, 4.0, 75.0, 8.0),
            text="113",
            source_observation_id="text:b0000:l0000:s0000",
        )
        page = _page(0)
        self.assertNotEqual(mirrored((25, 4)), mirrored((72, 4)))
        self.assertEqual(mirrored_centre(verso, page), mirrored_centre(recto, page))

    def test_an_alternating_page_number_reaches_the_threshold(self) -> None:
        # Contate separate, le due posizioni stanno a meta' e restano sotto il
        # quarto; accoppiate arrivano sopra.
        pages = []
        for i in range(12):
            x = 72.0 if i % 2 else 25.0
            pages.append((_page(i, (str(100 + i), x, 4.0)), str(100 + i)))
        found = label_slots(pages)
        self.assertIn((25, 4), found)
        self.assertIn((72, 4), found)


if __name__ == "__main__":
    unittest.main()
