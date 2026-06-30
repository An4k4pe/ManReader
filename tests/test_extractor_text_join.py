import unittest

from extractor import TextBlock, TextSpan, _split_text_block_by_horizontal_clusters


class ExtractorTextJoinTest(unittest.TestCase):
    def test_merges_adjacent_word_fragments(self):
        block = _block(
            [
                _span("resistent", (10.0, 10.0, 40.0, 20.0)),
                _span("e", (40.5, 10.0, 45.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "resistente")

    def test_merges_single_letter_fragment_with_word_rest(self):
        block = _block(
            [
                _span("p", (10.0, 10.0, 15.0, 20.0)),
                _span("urtroppo", (15.5, 10.0, 55.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "purtroppo")

    def test_merges_uppercase_drop_cap_with_uppercase_rest(self):
        block = _block(
            [
                _span("D", (10.0, 10.0, 16.0, 20.0)),
                _span("OMANDE", (18.0, 10.0, 55.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "DOMANDE")

    def test_does_not_over_merge_normal_words_with_tiny_gap(self):
        cases = [
            ("La", "Squadra", "La Squadra"),
            ("Vesper", "viene", "Vesper viene"),
            ("Dran", "este", "Dran este"),
        ]
        for first, second, expected in cases:
            with self.subTest(first=first, second=second):
                block = _block(
                    [
                        _span(first, (10.0, 10.0, 30.0, 20.0)),
                        _span(second, (30.5, 10.0, 70.0, 20.0)),
                    ]
                )

                self.assertEqual(block.text, expected)

    def test_does_not_insert_space_before_punctuation(self):
        block = _block(
            [
                _span("ciao", (10.0, 10.0, 30.0, 20.0)),
                _span(",", (35.0, 10.0, 38.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "ciao,")

    def test_keeps_space_between_words_with_wide_gap(self):
        block = _block(
            [
                _span("suo", (10.0, 10.0, 25.0, 20.0)),
                _span("amico", (36.0, 10.0, 65.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "suo amico")

    def test_keeps_space_between_different_lines(self):
        block = _block(
            [
                _span("prima", (10.0, 10.0, 35.0, 20.0)),
                _span("riga", (10.0, 24.0, 30.0, 34.0)),
            ]
        )

        self.assertEqual(block.text, "prima riga")

    def test_merges_uppercase_drop_cap_with_taller_bbox(self):
        block = _block(
            [
                _span("D", (10.0, 6.0, 18.0, 24.0)),
                _span("OMANDE", (20.0, 12.0, 60.0, 22.0)),
            ]
        )

        self.assertEqual(block.text, "DOMANDE")

    def test_splits_raw_block_with_two_distinct_horizontal_clusters(self):
        block = _block(
            [
                _span("UMANO", (62.0, 74.0, 108.0, 88.0)),
                _span("Gli umani sono recenti.", (62.0, 90.0, 290.0, 103.0)),
                _span("Cercano gloria e conoscenza.", (63.0, 106.0, 295.0, 119.0)),
                _span("di gloria, oro e conoscenza.", (63.0, 194.0, 172.0, 207.0)),
                _span("✦", (333.0, 192.0, 341.0, 203.0)),
                _span("Punti Volontà: 3", (346.0, 191.0, 418.0, 203.0)),
                _span("Quando tiri su un’abilità,", (332.0, 204.0, 524.0, 216.0)),
                _span("puoi usare un’altra abilità.", (332.0, 217.0, 523.0, 229.0)),
            ]
        )

        blocks = _split_text_block_by_horizontal_clusters(block)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(
            blocks[0].text,
            "UMANO Gli umani sono recenti. Cercano gloria e conoscenza. di gloria, oro e conoscenza.",
        )
        self.assertEqual(
            blocks[1].text,
            "✦ Punti Volontà: 3 Quando tiri su un’abilità, puoi usare un’altra abilità.",
        )
        self.assertEqual(blocks[0].bbox, (62.0, 74.0, 295.0, 207.0))
        self.assertEqual(blocks[1].bbox, (332.0, 191.0, 524.0, 229.0))

    def test_does_not_split_normal_single_column_paragraph(self):
        block = _block(
            [
                _span("Prima riga del paragrafo.", (62.0, 74.0, 285.0, 88.0)),
                _span("Seconda riga del paragrafo.", (63.0, 90.0, 290.0, 103.0)),
                _span("Terza riga del paragrafo.", (62.5, 106.0, 295.0, 119.0)),
                _span("Quarta riga del paragrafo.", (63.5, 122.0, 288.0, 135.0)),
            ]
        )

        self.assertEqual(_split_text_block_by_horizontal_clusters(block), [block])

    def test_does_not_split_small_x_variations(self):
        block = _block(
            [
                _span("Prima riga indentata.", (62.0, 74.0, 250.0, 88.0)),
                _span("Seconda riga normale.", (78.0, 90.0, 290.0, 103.0)),
                _span("Terza riga normale.", (64.0, 106.0, 295.0, 119.0)),
                _span("Quarta riga normale.", (82.0, 122.0, 288.0, 135.0)),
            ]
        )

        self.assertEqual(_split_text_block_by_horizontal_clusters(block), [block])


def test_merges_word_with_single_letter_suffix_fragment(self):
    block = _block(
        [
            _span("resistent", (10.0, 10.0, 40.0, 20.0)),
            _span("e", (40.5, 10.0, 45.0, 20.0)),
        ]
    )

    self.assertEqual(block.text, "resistente")

    def test_merges_single_letter_fragment_with_word_rest(self):
        block = _block(
            [
                _span("p", (10.0, 10.0, 15.0, 20.0)),
                _span("urtroppo", (15.5, 10.0, 55.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "purtroppo")


def test_does_not_over_merge_normal_words_with_tiny_gap(self):
    cases = [
        ("La", "Squadra", "La Squadra"),
        ("Vesper", "viene", "Vesper viene"),
        ("lunar", "Selenia", "lunar Selenia"),
    ]
    for first, second, expected in cases:
        with self.subTest(first=first, second=second):
            block = _block(
                [
                    _span(first, (10.0, 10.0, 30.0, 20.0)),
                    _span(second, (30.5, 10.0, 70.0, 20.0)),
                ]
            )

            self.assertEqual(block.text, expected)

    def test_keeps_space_between_normal_words_with_normal_gap(self):
        block = _block(
            [
                _span("Il", (10.0, 10.0, 18.0, 20.0)),
                _span("testo", (23.0, 10.0, 48.0, 20.0)),
            ]
        )

        self.assertEqual(block.text, "Il testo")


def _block(spans: list[TextSpan]) -> TextBlock:
    return TextBlock(spans=spans, bbox=(0.0, 0.0, 100.0, 100.0))


def _span(text: str, bbox: tuple[float, float, float, float]) -> TextSpan:
    return TextSpan(
        text=text,
        font="TestFont",
        size=10.0,
        bold=False,
        italic=False,
        bbox=bbox,
    )


if __name__ == "__main__":
    unittest.main()
