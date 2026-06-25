import unittest

from extractor import (
    _bbox_intersection_area,
    _best_text_block_for_bbox,
    _DictBlockMatch,
    _group_consecutive_dict_block_matches,
    _overlap_ratio_against_bbox,
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
) -> _DictBlockMatch:
    return _DictBlockMatch(
        dict_bbox=(10.0, 20.0, 100.0, 40.0),
        dict_text=text,
        matched_block=matched_block,
    )


def _group_texts(groups: list[list[_DictBlockMatch]]) -> list[list[str]]:
    return [[match.dict_text for match in group] for group in groups]


if __name__ == "__main__":
    unittest.main()
