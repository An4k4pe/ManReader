import unittest

from ir2_builder import (
    AssetNoteInput,
    breaks_paragraph,
    build_page_ir2,
    group_source_lines,
    join_lines,
)
from primitive_model import TextPrimitive

PAGE = "page:0099"


def _span(block: int, line: int, span: int, text: str, y: float = 0.0, x: float = 0.0):
    observation = f"text:b{block:04d}:l{line:04d}:s{span:04d}"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(x, y, x + 10.0, y + 10.0),
        text=text,
        source_observation_id=observation,
    )


class GroupSourceLinesTest(unittest.TestCase):
    def test_concatenates_spans_without_adding_a_separator(self) -> None:
        # Il caso misurato su DB p.99: gli span portano gia' la loro spaziatura.
        spans = [_span(5, 0, 0, "a "), _span(5, 0, 1, "PERSUADERE"), _span(5, 0, 2, ".")]
        lines = group_source_lines(spans)
        self.assertEqual([line.text for line in lines], ["a PERSUADERE."])

    def test_orders_spans_by_span_index_not_by_arrival(self) -> None:
        spans = [_span(7, 2, 2, " 8"), _span(7, 2, 0, "PF"), _span(7, 2, 1, ":")]
        self.assertEqual([line.text for line in group_source_lines(spans)], ["PF: 8"])

    def test_splits_on_a_new_line_index(self) -> None:
        spans = [_span(3, 0, 0, "prima"), _span(3, 1, 0, "seconda")]
        self.assertEqual(len(group_source_lines(spans)), 2)

    def test_an_unreadable_observation_id_becomes_its_own_line(self) -> None:
        odd = TextPrimitive(
            primitive_id="primitive:text:weird",
            bbox=(0.0, 0.0, 1.0, 1.0),
            text="x",
            source_observation_id="weird",
        )
        self.assertEqual(len(group_source_lines([_span(1, 0, 0, "a"), odd])), 2)


class BreaksParagraphTest(unittest.TestCase):
    def test_breaks_on_a_full_stop_before_an_uppercase_start(self) -> None:
        self.assertTrue(breaks_paragraph("… come normali PNG.", "Resistenza: tutti i danni"))

    def test_joins_when_the_sentence_continues_in_lowercase(self) -> None:
        self.assertFalse(breaks_paragraph("gli scheletri non", "contano come mostri"))

    def test_a_colon_does_not_terminate(self) -> None:
        self.assertFalse(breaks_paragraph("Non-Mostri:", "in combattimento"))

    def test_a_colon_before_a_list_marker_does_terminate(self) -> None:
        self.assertTrue(breaks_paragraph("Armi:", "- spada corta"))
        self.assertTrue(breaks_paragraph("Armi:", "1 spada corta"))

    def test_breaks_before_an_uppercase_start_even_without_punctuation(self) -> None:
        self.assertTrue(breaks_paragraph("Movimento: 8", "Armatura: cuoio"))

    def test_breaks_on_exclamation_and_question_marks(self) -> None:
        self.assertTrue(breaks_paragraph("Davvero!", "Poi"))
        self.assertTrue(breaks_paragraph("Davvero?", "Poi"))

    def test_does_not_break_on_an_empty_next_line(self) -> None:
        self.assertFalse(breaks_paragraph("qualcosa.", ""))


class JoinLinesTest(unittest.TestCase):
    def test_rejoins_a_hyphenated_word(self) -> None:
        self.assertEqual(join_lines("sono dimez-", "zati (per eccesso)"), "sono dimezzati (per eccesso)")

    def test_joins_with_a_single_space_when_there_is_no_hyphen(self) -> None:
        self.assertEqual(join_lines("gli scheletri non", "contano"), "gli scheletri non contano")

    def test_does_not_rejoin_when_the_next_starts_uppercase(self) -> None:
        # La guardia della regex: lettera prima, minuscola dopo.
        self.assertEqual(join_lines("nord-", "Ovest"), "nord- Ovest")


class BuildPageIR2Test(unittest.TestCase):
    def test_builds_the_three_entries_of_a_hanging_indent_box(self) -> None:
        # Il box Non-Mostri di DB p.99, dove il blocco taglia le voci di traverso.
        spans = [
            _span(2, 0, 0, "Non-Mostri: in combattimento, gli scheletri non ", y=0),
            _span(3, 0, 0, "contano come mostri, ma come normali PNG.", y=10),
            _span(3, 1, 0, "Resistenza: tutti i danni sono dimez-", y=20),
            _span(4, 0, 0, "zati (arrotondando per eccesso).", y=30),
            _span(4, 1, 0, "Immunità: gli scheletri sono immuni alla paura e ", y=40),
            _span(5, 0, 0, "a PERSUADERE.", y=50),
        ]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual(
            [node.text for node in page.nodes],
            [
                "Non-Mostri: in combattimento, gli scheletri non contano come mostri, "
                "ma come normali PNG.",
                "Resistenza: tutti i danni sono dimezzati (arrotondando per eccesso).",
                "Immunità: gli scheletri sono immuni alla paura e a PERSUADERE.",
            ],
        )

    def test_every_primitive_lands_in_exactly_one_node(self) -> None:
        spans = [_span(1, 0, 0, "una frase."), _span(2, 0, 0, "Altra frase.")]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        covered = [pid for node in page.nodes for pid in node.primitive_ids]
        self.assertEqual(sorted(covered), sorted(s.primitive_id for s in spans))

    def test_an_empty_span_is_still_covered(self) -> None:
        spans = [_span(1, 0, 0, "testo"), _span(1, 0, 1, "")]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        covered = {pid for node in page.nodes for pid in node.primitive_ids}
        self.assertIn(spans[1].primitive_id, covered)

    def test_node_id_is_page_qualified_and_derived_from_the_source(self) -> None:
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=[_span(3, 1, 0, "testo")])
        self.assertEqual(page.nodes[0].node_id, "page:0099:b0003:l0001")

    def test_order_is_a_permutation_and_follows_the_received_order(self) -> None:
        spans = [_span(1, 0, 0, "prima.", y=0), _span(2, 0, 0, "Seconda.", y=10)]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual([node.order for node in page.nodes], [0, 1])

    def test_interleaves_an_asset_note_at_its_sort_key(self) -> None:
        spans = [_span(1, 0, 0, "prima.", y=0), _span(2, 0, 0, "Seconda.", y=100)]
        note = AssetNoteInput(
            primitive_id="primitive:image:image:i0001",
            digest="md5:abc",
            file_name="md5_abc.png",
            bbox=(0.0, 50.0, 10.0, 60.0),
            occurrence_count=1,
            sort_key=(50.0, 0.0),
            proposed_structural_kind="layout.embedded_visual",
            resolution="unresolved",
        )
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans, asset_notes=[note])
        self.assertEqual([node.kind for node in page.nodes], [
            "text.paragraph", "asset.note", "text.paragraph",
        ])

    def test_an_empty_page_builds(self) -> None:
        self.assertEqual(build_page_ir2(page_id=PAGE, ordered_text_primitives=[]).nodes, ())


if __name__ == "__main__":
    unittest.main()
