"""Il nome di una scheda diventa un titolo: `Criterio_SchedaInIR2_v1.md`.

Quali righe sono il nome lo decide `stat_block_regions`; se diventa titolo, e a
quale livello, lo decide lo script dei titoli
(`document_heading_policy.structure_name_level`), come eccezione dichiarata alla
regola della dimensione. Il costruttore fa del nome **un** nodo `text.heading` e
chiude il paragrafo prima e dopo. Senza nomi la pagina non cambia.
"""

from __future__ import annotations

import unittest

from ir2_builder import StatBlockNameInput, build_page_ir2
from ir2_model import KIND_TEXT_HEADING, KIND_TEXT_PARAGRAPH
from primitive_model import TextPrimitive

PAGE = "page:0030"
# Le fasce di Daggerheart (h1 28 pt, h2 17 pt) e di DB (h1, h2, h3): i nomi
# prendono il livello sotto la piu' profonda.
TWO_BANDS = {28.0: 1, 17.0: 2}
THREE_BANDS = {34.0: 1, 30.0: 2, 20.0: 3}


def _span(block: int, line: int, text: str, y: float) -> TextPrimitive:
    observation = f"text:b{block:04d}:l{line:04d}:s0000"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(10.0, y, 200.0, y + 10.0),
        text=text,
        source_observation_id=observation,
        font_name="Body",
        font_size=9.0,
    )


def _name(*spans: TextPrimitive) -> StatBlockNameInput:
    return StatBlockNameInput(primitive_ids=tuple(span.primitive_id for span in spans))


def _shape(page) -> list[tuple[str, str | None, int | None]]:
    return [(node.kind, node.text, node.heading_level) for node in page.nodes]


class StatBlockNameTest(unittest.TestCase):
    def test_without_names_the_page_is_unchanged(self) -> None:
        spans = [_span(1, 0, "RAGNO GIGANTE", 0.0), _span(1, 1, "Ferocia: 2", 12.0)]
        self.assertEqual(
            build_page_ir2(page_id=PAGE, ordered_text_primitives=spans),
            build_page_ir2(page_id=PAGE, ordered_text_primitives=spans, stat_block_names=()),
        )

    def test_the_name_becomes_a_heading_and_closes_the_paragraph(self) -> None:
        # Nome e riga dopo nello stesso blocco: senza la scheda escono incollati,
        # ed e' cio' che succedeva a `COURTIER` su Daggerheart.
        spans = [_span(1, 0, "COURTIER", 0.0), _span(1, 1, "Tier 1 Social", 12.0)]
        before = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual(_shape(before), [(KIND_TEXT_PARAGRAPH, "COURTIER Tier 1 Social", None)])

        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            stat_block_names=(_name(spans[0]),),
            heading_levels=TWO_BANDS,
        )
        self.assertEqual(
            _shape(page),
            [(KIND_TEXT_HEADING, "COURTIER", 3), (KIND_TEXT_PARAGRAPH, "Tier 1 Social", None)],
        )

    def test_the_name_is_cut_from_the_line_before(self) -> None:
        spans = [
            _span(1, 0, "physical damage.", 0.0),
            _span(1, 1, "DIRE WOLF", 12.0),
            _span(1, 2, "Tier 1 Skulk", 24.0),
        ]
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            stat_block_names=(_name(spans[1]),),
            heading_levels=TWO_BANDS,
        )
        self.assertEqual(
            _shape(page),
            [
                (KIND_TEXT_PARAGRAPH, "physical damage.", None),
                (KIND_TEXT_HEADING, "DIRE WOLF", 3),
                (KIND_TEXT_PARAGRAPH, "Tier 1 Skulk", None),
            ],
        )

    def test_a_wrapped_name_is_one_heading_even_across_blocks(self) -> None:
        # Due blocchi e una maiuscola: la regola dei paragrafi li spezzerebbe.
        spans = [
            _span(1, 0, "FALLEN WARLORD:", 0.0),
            _span(2, 0, "UNDEFEATED CHAMPION", 12.0),
            _span(2, 1, "Tier 4 Solo", 24.0),
        ]
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            stat_block_names=(_name(spans[0], spans[1]),),
            heading_levels=THREE_BANDS,
        )
        self.assertEqual(
            _shape(page),
            [
                (KIND_TEXT_HEADING, "FALLEN WARLORD: UNDEFEATED CHAMPION", 4),
                (KIND_TEXT_PARAGRAPH, "Tier 4 Solo", None),
            ],
        )

    def test_two_names_in_a_row_are_two_headings(self) -> None:
        spans = [_span(1, 0, "GIANT RAT", 0.0), _span(1, 1, "GIANT SCORPION", 12.0)]
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            stat_block_names=(_name(spans[0]), _name(spans[1])),
            heading_levels=TWO_BANDS,
        )
        self.assertEqual(
            _shape(page),
            [(KIND_TEXT_HEADING, "GIANT RAT", 3), (KIND_TEXT_HEADING, "GIANT SCORPION", 3)],
        )

    def test_a_name_longer_than_a_prose_line_is_not_a_heading(self) -> None:
        # Il titolo falso dei goblin su DB: un paragrafo di prosa preso per nome.
        # Lo script dei titoli lo rifiuta, e il paragrafo resta com'era.
        spans = [
            _span(1, 0, "riposa nelle nicchie del sotterraneo mentre gli altri", 0.0),
            _span(1, 1, "vagano affaccendati per il castello.", 12.0),
        ]
        without = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=spans,
            stat_block_names=(_name(spans[0], spans[1]),),
            heading_levels=TWO_BANDS,
            heading_max_length=40.0,
        )
        self.assertEqual(_shape(page), _shape(without))


if __name__ == "__main__":
    unittest.main()
