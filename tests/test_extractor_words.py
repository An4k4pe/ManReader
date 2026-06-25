import unittest

from extractor import _line_text_from_words


class ExtractorWordsTest(unittest.TestCase):
    def test_reconstructs_line_from_words_without_fragment_artifacts(self):
        words = _words(
            [
                "un",
                "esemplare",
                "resistente,",
                "coriaceo,",
                "ma",
                "purtroppo",
            ]
        )

        text = _line_text_from_words(words)

        self.assertEqual(text, "un esemplare resistente, coriaceo, ma purtroppo")

    def test_preserves_spaces_between_normal_words(self):
        words = _words(["Il", "testo", "rimane", "leggibile"])

        text = _line_text_from_words(words)

        self.assertEqual(text, "Il testo rimane leggibile")

    def test_does_not_insert_space_before_separate_punctuation_word(self):
        words = _words(["ciao", ",", "mondo", "!"])

        text = _line_text_from_words(words)

        self.assertEqual(text, "ciao, mondo!")

    def test_sorts_words_left_to_right_within_line(self):
        words = [
            _word("secondo", x0=30.0),
            _word("primo", x0=10.0),
        ]

        text = _line_text_from_words(words)

        self.assertEqual(text, "primo secondo")


def _words(texts: list[str]) -> list[tuple[float, float, float, float, str, int, int, int]]:
    return [_word(text, x0=index * 10.0) for index, text in enumerate(texts)]


def _word(
    text: str,
    x0: float,
    y0: float = 10.0,
) -> tuple[float, float, float, float, str, int, int, int]:
    return (x0, y0, x0 + 8.0, y0 + 10.0, text, 0, 0, 0)


if __name__ == "__main__":
    unittest.main()
