import unittest

from extractor import _text_from_block


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


def _block(text: str) -> tuple[float, float, float, float, str, int, int]:
    return (10.0, 20.0, 100.0, 40.0, text, 0, 0)


if __name__ == "__main__":
    unittest.main()
