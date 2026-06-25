import unittest

from extractor import (
    TextSpan,
    _bbox_intersection_area,
    _best_text_block_for_bbox,
    _DictBlockMatch,
    _group_consecutive_dict_block_matches,
    _overlap_ratio_against_bbox,
    _text_block_from_dict_match_group,
    _text_from_block,
)


class ExtractorBlocksTest(unittest.TestCase):
    def test_removes_trailing_newline(self):
        block = _block("Testo del blocco\n")

        text = _text_from_block(block)

        self.assertEqual(text, "Testo del blocco")

    def test_replaces_internal_newline_with_single_space(self):
        block = _block("prima riga\nseconda riga")

        text = _text_from_block(block)

        self.assertEqual(text, "prima riga seconda riga")

    def test_compresses_multiple_spaces(self):
        block = _block("prima   seconda    terza")

        text = _text_from_block(block)

        self.assertEqual(text, "prima seconda terza")

    def test_empty_block_returns_empty_string(self):
        block = _block(" \n  \t")

        text = _text_from_block(block)

        self.assertEqual(text, "")

    def test_preserves_already_correct_words_and_punctuation(self):
        block = _block("resistente, coriaceo, ma purtroppo\n")

        text = _text_from_block(block)

        self.assertEqual(text, "resistente, coriaceo, ma purtroppo")

    def test_full_overlap_ratio(self):
        ratio = _overlap_ratio_against_bbox(
            (10.0, 10.0, 30.0, 30.0),
            (10.0, 10.0, 30.0, 30.0),
        )

        self.assertEqual(ratio, 1.0)

    def test_partial_overlap_ratio(self):
        ratio = _overlap_ratio_against_bbox(
            (10.0, 10.0, 30.0, 30.0),
            (20.0, 10.0, 40.0, 30.0),
        )

        self.assertEqual(ratio, 0.5)

    def test_no_overlap_intersection_area(self):
        area = _bbox_intersection_area(
            (10.0, 10.0, 30.0, 30.0),
            (40.0, 40.0, 50.0, 50.0),
        )

        self.assertEqual(area, 0.0)

    def test_best_text_block_returns_none_without_overlap(self):
        block = _block("lontano", x0=200.0, y0=200.0, x1=300.0, y1=220.0)

        match = _best_text_block_for_bbox((10.0, 20.0, 100.0, 40.0), [block])

        self.assertIsNone(match)

    def test_best_text_block_ignores_non_text_blocks(self):
        block = _block("immagine", block_type=1)

        match = _best_text_block_for_bbox((10.0, 20.0, 100.0, 40.0), [block])

        self.assertIsNone(match)

    def test_best_text_block_ignores_empty_text_blocks(self):
        block = _block(" \n  ")

        match = _best_text_block_for_bbox((10.0, 20.0, 100.0, 40.0), [block])

        self.assertIsNone(match)

    def test_best_text_block_chooses_candidate_with_best_overlap(self):
        weaker = _block("debole", x0=10.0, y0=20.0, x1=55.0, y1=40.0)
        better = _block("migliore", x0=10.0, y0=20.0, x1=100.0, y1=40.0)

        match = _best_text_block_for_bbox(
            (10.0, 20.0, 100.0, 40.0),
            [weaker, better],
        )

        self.assertEqual(match, better)

    def test_groups_three_consecutive_dict_blocks_with_same_candidate(self):
        candidate = _block("testo completo")
        matches = [
            _match("testo", candidate),
            _match("com", candidate),
            _match("pleto", candidate),
        ]

        groups = _group_consecutive_dict_block_matches(matches)

        self.assertEqual(_group_texts(groups), [["testo", "com", "pleto"]])

    def test_different_candidates_stay_in_separate_groups(self):
        first = _block("primo", block_no=1)
        second = _block("secondo", block_no=2)
        matches = [_match("pri", first), _match("sec", second)]

        groups = _group_consecutive_dict_block_matches(matches)

        self.assertEqual(_group_texts(groups), [["pri"], ["sec"]])

    def test_none_match_interrupts_group(self):
        candidate = _block("testo completo")
        matches = [
            _match("testo", candidate),
            _match("senza match", None),
            _match("completo", candidate),
        ]

        groups = _group_consecutive_dict_block_matches(matches)

        self.assertEqual(_group_texts(groups), [["testo"], ["senza match"], ["completo"]])

    def test_non_consecutive_matches_are_not_merged(self):
        first = _block("primo", block_no=1)
        second = _block("secondo", block_no=2)
        matches = [
            _match("pri", first),
            _match("sec", second),
            _match("mo", first),
        ]

        groups = _group_consecutive_dict_block_matches(matches)

        self.assertEqual(_group_texts(groups), [["pri"], ["sec"], ["mo"]])

    def test_grouping_preserves_original_order(self):
        first = _block("primo", block_no=1)
        second = _block("secondo", block_no=2)
        matches = [
            _match("a", first),
            _match("b", first),
            _match("c", second),
            _match("d", second),
        ]

        groups = _group_consecutive_dict_block_matches(matches)

        self.assertEqual(_group_texts(groups), [["a", "b"], ["c", "d"]])

    def test_text_block_from_empty_group_returns_none(self):
        text_block = _text_block_from_dict_match_group([])

        self.assertIsNone(text_block)

    def test_text_block_from_group_with_none_match_returns_none(self):
        text_block = _text_block_from_dict_match_group([_match("testo", None)])

        self.assertIsNone(text_block)

    def test_text_block_from_group_with_different_candidates_returns_none(self):
        first = _block("primo", block_no=1)
        second = _block("secondo", block_no=2)

        text_block = _text_block_from_dict_match_group(
            [
                _match("pri", first),
                _match("sec", second),
            ]
        )

        self.assertIsNone(text_block)

    def test_text_block_from_group_with_empty_hint_text_returns_none(self):
        candidate = _block(" \n  ")

        text_block = _text_block_from_dict_match_group([_match("testo", candidate)])

        self.assertIsNone(text_block)

    def test_text_block_from_valid_group_uses_block_hint_text(self):
        candidate = _block("testo corretto dal block hint")

        text_block = _text_block_from_dict_match_group(
            [
                _match("testo cor", candidate),
                _match("retto", candidate),
            ]
        )

        self.assertIsNotNone(text_block)
        self.assertEqual(text_block.text, "testo corretto dal block hint")
        self.assertEqual(len(text_block.spans), 1)

    def test_text_block_from_group_uses_union_bbox(self):
        candidate = _block("testo completo")

        text_block = _text_block_from_dict_match_group(
            [
                _match("testo", candidate, bbox=(10.0, 20.0, 40.0, 35.0)),
                _match("completo", candidate, bbox=(35.0, 18.0, 90.0, 42.0)),
            ]
        )

        self.assertIsNotNone(text_block)
        self.assertEqual(text_block.bbox, (10.0, 18.0, 90.0, 42.0))
        self.assertEqual(text_block.spans[0].bbox, (10.0, 18.0, 90.0, 42.0))

    def test_text_block_from_group_preserves_style_from_first_source_span(self):
        candidate = _block("testo completo")
        source_span = _span(font="Serif-BoldItalic", size=13.5, bold=True, italic=True)

        text_block = _text_block_from_dict_match_group(
            [
                _match("testo", candidate, source_spans=[source_span]),
                _match("completo", candidate),
            ]
        )

        self.assertIsNotNone(text_block)
        span = text_block.spans[0]
        self.assertEqual(span.font, "Serif-BoldItalic")
        self.assertEqual(span.size, 13.5)
        self.assertTrue(span.bold)
        self.assertTrue(span.italic)

    def test_text_block_from_group_uses_fallback_style_without_source_spans(self):
        candidate = _block("testo completo")

        text_block = _text_block_from_dict_match_group([_match("testo", candidate)])

        self.assertIsNotNone(text_block)
        span = text_block.spans[0]
        self.assertEqual(span.font, "")
        self.assertEqual(span.size, 10.0)
        self.assertFalse(span.bold)
        self.assertFalse(span.italic)


def _block(
    text: str,
    x0: float = 10.0,
    y0: float = 20.0,
    x1: float = 100.0,
    y1: float = 40.0,
    block_no: int = 0,
    block_type: int = 0,
) -> tuple[float, float, float, float, str, int, int]:
    return (x0, y0, x1, y1, text, block_no, block_type)


def _match(
    text: str,
    matched_block: tuple[float, float, float, float, str, int, int] | None,
    bbox: tuple[float, float, float, float] = (10.0, 20.0, 100.0, 40.0),
    source_spans: list[TextSpan] | None = None,
) -> _DictBlockMatch:
    return _DictBlockMatch(
        dict_bbox=bbox,
        dict_text=text,
        matched_block=matched_block,
        source_spans=source_spans,
    )


def _span(
    font: str = "",
    size: float = 10.0,
    bold: bool = False,
    italic: bool = False,
) -> TextSpan:
    return TextSpan(
        text="source",
        font=font,
        size=size,
        bold=bold,
        italic=italic,
        bbox=(10.0, 20.0, 100.0, 40.0),
    )


def _group_texts(groups: list[list[_DictBlockMatch]]) -> list[list[str]]:
    return [[match.dict_text for match in group] for group in groups]


if __name__ == "__main__":
    unittest.main()
