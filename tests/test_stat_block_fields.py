"""La compilazione della scheda: `Criterio_CompilazioneScheda_v1.md`.

Casi sintetici presi dalle geometrie misurate su Draw Steel, Daggerheart e il
Dragonbane Quickstart; le verifiche sulle pagine vere stanno nell'esito.
"""

from __future__ import annotations

import unittest

from ir2_builder import StatBlockFieldsInput, StatBlockNameInput, build_page_ir2
from ir2_markdown import render_page_markdown, render_stat_block
from ir2_model import (
    KIND_STAT_BLOCK,
    KIND_TEXT_HEADING,
    DocumentIR2,
    IR2Provenance,
    StatBlockIR2,
    StatFieldIR2,
)
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict
from primitive_model import TextPrimitive
from stat_block_fields import compile_fields

BOLD = ("Slab-Bold", 7.5)
BODY = ("Slab-Regular", 7.5)
NUMBER = ("Slab-Md", 10.0)
GLYPH = ("Glyphs", 8.0)
SMALL_BOLD = ("Slab-Bold", 7.0)
SMALL_NUMBER = ("Slab-Md", 7.0)

_COUNTER = [0]


def _span(
    text: str,
    x0: float,
    x1: float,
    y0: float,
    style: tuple[str, float],
    y1: float | None = None,
    line: int | None = None,
) -> TextPrimitive:
    _COUNTER[0] += 1
    # Una riga di sorgente per span, salvo ``line``: le coppie in linea stanno
    # nella stessa riga.
    observation = f"text:b0001:l{line if line is not None else 5000 + _COUNTER[0]:04d}:s{_COUNTER[0]:04d}"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(x0, y0, x1, y1 if y1 is not None else y0 + 10.0),
        text=text,
        source_observation_id=observation,
        font_name=style[0],
        font_size=style[1],
    )


def _pairs(fields) -> list[tuple[str, str]]:
    return [(field.label, field.value) for field in fields]


class CompileFieldsTest(unittest.TestCase):
    def test_inline_pairs_follow_the_style_change(self) -> None:
        # Coordinate vere: su DrM i due span contigui si sovrappongono di 0,0006
        # pt, su DB `Movimento:` e ` 24` di 0,36.
        immunity = [
            _span("Immunity:", 51.3306999206543, 88.86068725585938, 111.1, BOLD),
            _span(" Poison 2\t", 88.86009979248047, 121.0, 111.1, BODY),
        ]
        movement = [
            _span("Movimento:", 85.03939056396484, 134.95338439941406, 561.1, ("Hideout-Bold", 9.0)),
            _span(" 24\u2003", 134.5933837890625, 148.84938049316406, 561.1, ("Hideout-Regular", 9.0)),
            _span(" Armatura:", 157.4893798828125, 202.51637268066406, 561.1, ("Hideout-Bold", 9.0)),
            _span(" —\u2003", 202.1563720703125, 213.01036071777344, 561.1, ("Hideout-Regular", 9.0)),
            _span(" PF", 221.65036010742188, 235.13031005859375, 561.1, ("Hideout-Bold", 8.1)),
            _span(":", 234.7700958251953, 237.4700927734375, 561.1, ("Hideout-Bold", 9.0)),
            _span(" 12/arpia", 237.47, 270.0, 561.1, ("Hideout-Regular", 9.0)),
        ]
        self.assertEqual(
            _pairs(compile_fields([immunity, movement], {}, 10)),
            [
                ("Immunity:", "Poison 2"),
                ("Movimento:", "24"),
                ("Armatura:", "—"),
                ("PF:", "12/arpia"),
            ],
        )

    def test_values_above_their_labels_pair_by_nearness_and_recurrence(self) -> None:
        # Draw Steel: `1S` sopra `Size`, una riga di sorgente per span.
        lines = [
            [_span("1S", 66.5, 77.6, 82.9, NUMBER, 95.9)],
            [_span("6", 116.7, 122.2, 82.9, NUMBER, 95.9)],
            [_span("Size", 65.4, 78.7, 93.3, BOLD, 104.1)],
            [_span("Speed", 109.2, 129.7, 93.3, BOLD, 104.1)],
        ]
        recurrence = {"size": 10, "speed": 10, "6": 6}
        self.assertEqual(
            _pairs(compile_fields(lines, recurrence, 10)),
            [("Size", "1S"), ("Speed", "6")],
        )

    def test_lines_before_the_first_field_stay_out(self) -> None:
        # La descrizione di un mostro di Dragonbane resta un paragrafo.
        lines = [
            [_span("Le arpie sono dei grandi rapaci", 85.0, 250.0, 500.0, BODY)],
            [_span("umanoidi e bocche piene di denti.", 85.0, 250.0, 510.0, BODY)],
            [_span("Ferocia:", 85.0, 120.0, 540.0, BOLD), _span(" 1/arpia", 120.0, 150.0, 540.0, BODY)],
            [_span("Level 1 Solo", 200.0, 250.0, 530.0, ("Newzald-Bold", 9.0))],
        ]
        fields = compile_fields(lines, {}, 10)
        self.assertEqual(_pairs(fields), [("", "Level 1 Solo"), ("Ferocia:", "1/arpia")])
        owned = {pid for field in fields for pid in field.primitive_ids}
        self.assertNotIn(lines[0][0].primitive_id, owned)

    def test_rows_that_recur_in_a_minority_do_not_pair(self) -> None:
        lines = [
            [_span("Tier 1 Skulk", 62.9, 108.7, 472.5, BOLD)],
            [_span("A large wolf.", 62.9, 260.1, 482.3, BODY)],
        ]
        self.assertEqual(compile_fields(lines, {}, 10), ())

    def test_a_label_in_two_styles_continues_before_a_third(self) -> None:
        line = [
            _span("M", 60.9, 68.9, 134.1, GLYPH),
            _span(" ight", 68.6, 81.7, 134.1, SMALL_BOLD),
            _span(" 0", 81.7, 87.1, 134.1, SMALL_NUMBER),
            _span("A", 104.4, 112.4, 134.1, GLYPH),
            _span(" gility", 112.1, 129.4, 134.1, SMALL_BOLD),
            _span(" +2", 129.4, 138.7, 134.1, SMALL_NUMBER),
        ]
        self.assertEqual(
            _pairs(compile_fields([line], {}, 10)),
            [("Might", "0"), ("Agility", "+2")],
        )

    def test_a_wrapped_value_continues_on_the_next_line(self) -> None:
        lines = [
            [
                _span("Motives & Tactics:", 62.9, 126.5, 492.2, BOLD),
                _span(" Defend territory, harry, ", 126.5, 255.1, 492.2, BODY),
            ],
            [_span("surround, trail", 62.9, 110.6, 501.7, BODY)],
        ]
        self.assertEqual(
            _pairs(compile_fields(lines, {}, 10)),
            [("Motives & Tactics:", "Defend territory, harry, surround, trail")],
        )

    def test_a_value_continues_past_the_field_part_and_no_further(self) -> None:
        # DB, i goblin: la seconda arma va a capo sotto l'ultima etichetta.
        lines = [
            [
                _span("Armi:", 85.0, 110.0, 600.0, BOLD),
                _span(" arco corto (danno D10),", 110.0, 250.0, 600.0, BODY),
            ]
        ]
        tail = [
            [_span("spada corta (danno D10)", 85.0, 200.0, 610.0, BODY)],
            [_span("Nel castello vivono dieci goblin.", 85.0, 250.0, 630.0, ("Slab-Italic", 7.5))],
        ]
        fields = compile_fields(lines, {}, 10, tail=tail)
        self.assertEqual(_pairs(fields), [("Armi:", "arco corto (danno D10), spada corta (danno D10)")])
        self.assertNotIn(tail[1][0].primitive_id, fields[0].primitive_ids)

    def test_every_primitive_of_the_taken_lines_belongs_to_one_field(self) -> None:
        line = [
            _span("\t", 5.0, 10.0, 0.0, BODY),
            _span("HP:", 10.0, 30.0, 0.0, BOLD),
            _span("\t", 30.0, 32.0, 0.0, BODY),
            _span(" 4", 32.0, 40.0, 0.0, BODY),
        ]
        fields = compile_fields([line], {}, 10)
        owned = [pid for field in fields for pid in field.primitive_ids]
        self.assertEqual(sorted(owned), sorted(span.primitive_id for span in line))


class RenderStatBlockTest(unittest.TestCase):
    def test_yaml_drops_colons_and_trailing_separators(self) -> None:
        block = StatBlockIR2(
            fields=(
                StatFieldIR2(label="", value="Tier 1 Skulk", primitive_ids=("a",)),
                StatFieldIR2(label="Difficulty:", value="12 |", primitive_ids=("b",)),
                StatFieldIR2(label="Weakness:", value="—", primitive_ids=("c",)),
                StatFieldIR2(label="Effect:", value="one", primitive_ids=("d",)),
                StatFieldIR2(label="Effect:", value="two: more", primitive_ids=("e",)),
            )
        )
        self.assertEqual(
            render_stat_block(block),
            "```yaml\n"
            "text:\n"
            "  - Tier 1 Skulk\n"
            "Difficulty: 12\n"
            "Weakness: —\n"
            "Effect:\n"
            "  - one\n"
            '  - "two: more"\n'
            "```",
        )


class StatBlockInIR2Test(unittest.TestCase):
    def _page(self):
        spans = [
            _span("Angulotl Cleaver", 50.7, 131.2, 46.8, ("Newzald-Bold", 12.0)),
            _span("Immunity:", 51.3, 88.9, 111.1, BOLD, line=2),
            _span(" Poison 2", 88.9, 121.0, 111.1, BODY, line=2),
            _span("Movement:", 51.3, 90.7, 121.1, BOLD, line=3),
            _span(" Climb, swim", 90.7, 136.7, 121.1, BODY, line=3),
            _span("Toxiferous", 60.3, 105.0, 240.9, ("Newzald-Bold", 9.0)),
        ]
        page = build_page_ir2(
            page_id="page:0041",
            ordered_text_primitives=spans,
            heading_levels={24.0: 1},
            stat_block_names=(StatBlockNameInput(primitive_ids=(spans[0].primitive_id,)),),
            stat_block_fields=(
                StatBlockFieldsInput(
                    primitive_ids=tuple(span.primitive_id for span in spans[1:5]),
                    recurrence=(("immunity", 3), ("movement", 3)),
                    instance_count=3,
                ),
            ),
        )
        return page

    def test_the_fields_become_one_node_between_name_and_free_part(self) -> None:
        page = self._page()
        self.assertEqual(
            [node.kind for node in page.nodes],
            [KIND_TEXT_HEADING, KIND_STAT_BLOCK, "text.paragraph"],
        )
        markdown = render_page_markdown(page)
        self.assertIn("```yaml\nImmunity: Poison 2\nMovement: Climb, swim\n```", markdown)

    def test_the_stat_block_survives_serialisation(self) -> None:
        document = DocumentIR2(
            provenance=IR2Provenance(source_id="s", generation_id="g", producer_names=("p",)),
            pages=(self._page(),),
        )
        self.assertEqual(document_ir2_from_dict(document_ir2_to_dict(document)), document)


if __name__ == "__main__":
    unittest.main()
