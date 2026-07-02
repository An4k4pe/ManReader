import unittest

from extractor import (
    TextBlock,
    TextSpan,
    _deduplicate_overlapping_text_blocks,
    _rebuild_text_blocks_from_block_hints,
    _recover_missing_text_blocks_from_block_hints,
    _sort_local_two_column_zones,
    _split_text_block_by_horizontal_clusters,
)


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

    def test_rebuild_does_not_use_fused_cross_column_block_hint(self):
        title = _text_block("CAPACITÀ: PALMIPEDE", (369.0, 669.0, 495.0, 682.0), bold=True)
        body = _text_block(
            "✦ Punti Volontà: — Essendo un elfo, puoi meditare.",
            (79.0, 660.0, 276.0, 743.0),
        )
        block_hints = [
            (
                79.0,
                660.0,
                495.0,
                743.0,
                "CAPACITÀ: PALMIPEDE ✦Punti Volontà: — Essendo un elfo, puoi meditare.",
                0,
                0,
            )
        ]

        rebuilt = _rebuild_text_blocks_from_block_hints([title, body], block_hints)

        self.assertEqual([block.text for block in rebuilt], [title.text, body.text])

    def test_recovery_does_not_add_fused_hint_when_separate_blocks_cover_it(self):
        title = _text_block("CAPACITÀ: PALMIPEDE", (369.0, 669.0, 495.0, 682.0), bold=True)
        body = _text_block(
            "✦ Punti Volontà: — Essendo un elfo, puoi meditare.",
            (79.0, 660.0, 276.0, 743.0),
        )
        block_hints = [
            (
                79.0,
                660.0,
                495.0,
                743.0,
                "CAPACITÀ: PALMIPEDE ✦Punti Volontà: — Essendo un elfo, puoi meditare.",
                0,
                0,
            )
        ]

        recovered = _recover_missing_text_blocks_from_block_hints([title, body], block_hints, [])

        self.assertEqual([block.text for block in recovered], [body.text, title.text])

    def test_deduplicates_overlapping_nearly_identical_text_preferring_spaced_version(self):
        fused = _text_block(
            "PUNTI VOLONTÀ (PV) Il numero massimo di PVè pari al tuo valore.",
            (314.6, 350.2, 543.5, 415.5),
        )
        spaced = _text_block(
            "PUNTI VOLONTÀ (PV) Il numero massimo di PV è pari al tuo valore.",
            (314.6, 350.2, 543.5, 415.5),
        )

        deduplicated = _deduplicate_overlapping_text_blocks([fused, spaced])

        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(deduplicated[0].text, spaced.text)

    def test_does_not_deduplicate_nearby_different_text_blocks(self):
        first = _text_block(
            "PUNTI FERITA Questo valore determina i danni.", (314.0, 266.0, 540.0, 331.0)
        )
        second = _text_block(
            "PUNTI VOLONTÀ Questo valore serve per la magia.", (314.0, 350.0, 543.0, 415.0)
        )

        deduplicated = _deduplicate_overlapping_text_blocks([first, second])

        self.assertEqual([block.text for block in deduplicated], [first.text, second.text])

    def test_sorts_local_two_column_band_inside_single_column_page(self):
        blocks = [
            _text_block("left intro", (62.0, 460.0, 296.0, 500.0)),
            _text_block("right intro", (314.0, 462.0, 550.0, 536.0)),
            _text_block("left values", (62.0, 510.0, 296.0, 560.0)),
            _text_block("right force", (314.0, 546.0, 470.0, 560.0)),
            _text_block("right constitution", (314.0, 570.0, 500.0, 584.0)),
            _text_block("left box title", (139.0, 584.0, 221.0, 597.0)),
            _text_block("right agility", (314.0, 594.0, 549.0, 607.0)),
            _text_block("left box body", (79.0, 611.0, 279.0, 682.0)),
            _text_block("right intelligence", (314.0, 618.0, 549.0, 643.0)),
            _text_block("right will", (314.0, 654.0, 508.0, 667.0)),
            _text_block("right charisma", (314.0, 678.0, 477.0, 691.0)),
        ]

        sorted_blocks = _sort_local_two_column_zones(blocks, page_width=612.0, page_height=790.0)

        self.assertEqual(
            [block.text for block in sorted_blocks],
            [
                "left intro",
                "left values",
                "left box title",
                "left box body",
                "right intro",
                "right force",
                "right constitution",
                "right agility",
                "right intelligence",
                "right will",
                "right charisma",
            ],
        )

    def test_preserves_heading_before_local_two_column_band(self):
        blocks = [
            _text_block("heading", (200.0, 410.0, 405.0, 456.0), size=24.0),
            _text_block("left first", (62.0, 462.0, 296.0, 500.0)),
            _text_block("right first", (314.0, 462.0, 550.0, 536.0)),
            _text_block("left second", (62.0, 510.0, 296.0, 560.0)),
            _text_block("right second", (314.0, 546.0, 470.0, 560.0)),
            _text_block("right third", (314.0, 570.0, 500.0, 584.0)),
        ]

        sorted_blocks = _sort_local_two_column_zones(blocks, page_width=612.0, page_height=790.0)

        self.assertEqual(
            [block.text for block in sorted_blocks],
            ["heading", "left first", "left second", "right first", "right second", "right third"],
        )

    def test_does_not_reorder_single_column_page(self):
        blocks = [
            _text_block("line one", (62.0, 100.0, 296.0, 120.0)),
            _text_block("line two", (65.0, 130.0, 292.0, 150.0)),
            _text_block("line three", (70.0, 160.0, 298.0, 180.0)),
            _text_block("line four", (62.0, 190.0, 290.0, 210.0)),
            _text_block("line five", (68.0, 220.0, 294.0, 240.0)),
        ]

        self.assertEqual(_sort_local_two_column_zones(blocks, 612.0, 790.0), blocks)

    def test_does_not_treat_small_indents_as_two_columns(self):
        blocks = [
            _text_block("line one", (62.0, 100.0, 250.0, 120.0)),
            _text_block("line two", (90.0, 130.0, 292.0, 150.0)),
            _text_block("line three", (74.0, 160.0, 298.0, 180.0)),
            _text_block("line four", (108.0, 190.0, 290.0, 210.0)),
            _text_block("line five", (80.0, 220.0, 294.0, 240.0)),
        ]

        self.assertEqual(_sort_local_two_column_zones(blocks, 612.0, 790.0), blocks)


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


def _text_block(
    text: str,
    bbox: tuple[float, float, float, float],
    *,
    size: float = 10.0,
    bold: bool = False,
) -> TextBlock:
    return TextBlock(spans=[_span(text, bbox, size=size, bold=bold)], bbox=bbox)


def _span(
    text: str,
    bbox: tuple[float, float, float, float],
    *,
    size: float = 10.0,
    bold: bool = False,
) -> TextSpan:
    return TextSpan(
        text=text,
        font="TestFont",
        size=size,
        bold=bold,
        italic=False,
        bbox=bbox,
    )


if __name__ == "__main__":
    unittest.main()
