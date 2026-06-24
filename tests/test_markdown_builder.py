import unittest

from ir_model import AssetIR, BlockIR, DocumentIR, PageIR
from markdown_builder import build_markdown


class MarkdownBuilderTest(unittest.TestCase):
    """Regression tests for Markdown rendering from in-memory IR objects."""

    def test_aggregates_consecutive_text_blocks_into_single_paragraph(self):
        document = _document(
            [
                _text("b1", "Primo frammento"),
                _text("b2", "secondo frammento"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Primo frammento secondo frammento", markdown)
        self.assertNotIn("Primo frammento\n\nsecondo frammento", markdown)

    def test_does_not_insert_space_before_punctuation(self):
        document = _document(
            [
                _text("b1", "Ciao"),
                _text("b2", ","),
                _text("b3", "mondo"),
                _text("b4", "!"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Ciao, mondo!", markdown)
        self.assertNotIn("Ciao ,", markdown)
        self.assertNotIn("mondo !", markdown)

    def test_joins_short_split_word_fragment(self):
        document = _document(
            [
                _text("b1", "Subit"),
                _text("b2", "o"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Subito", markdown)
        self.assertNotIn("Subit o", markdown)

    def test_closes_paragraph_before_asset(self):
        document = _document(
            [
                _text("b1", "Prima frase"),
                _asset_block(),
                _text("b2", "Dopo asset"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Prima frase\n\n<!-- asset: asset-1", markdown)
        self.assertIn("[Immagine: Mappa](/assets/map.png)", markdown)
        self.assertIn("> Descrizione: Mappa del dungeon", markdown)
        self.assertIn("> Descrizione: Mappa del dungeon\n\nDopo asset", markdown)

    def test_renders_asset_as_text_link_not_markdown_embed(self):
        document = _document([_asset_block()])

        markdown = build_markdown(document)

        self.assertIn("[Immagine: Mappa](/assets/map.png)", markdown)
        self.assertNotIn("![", markdown)

    def test_inserts_page_comment(self):
        document = _document([_text("b1", "Testo")])

        markdown = build_markdown(document)

        self.assertIn("<!-- page: 1 -->", markdown)


def _document(blocks: list[BlockIR]) -> DocumentIR:
    return DocumentIR(
        schema_version="1.0",
        source_path="manual.pdf",
        page_count=1,
        pages=[PageIR(id="p1", page_num=1, blocks=blocks)],
    )


def _text(block_id: str, text: str) -> BlockIR:
    return BlockIR(
        id=block_id,
        type="text",
        page_num=1,
        order=1,
        text=text,
    )


def _asset_block() -> BlockIR:
    return BlockIR(
        id="b-asset",
        type="image",
        page_num=1,
        order=1,
        asset=AssetIR(
            id="asset-1",
            sha="sha-1",
            kind="image",
            path="/assets/map.png",
            title="Mappa",
            description="Mappa del dungeon",
        ),
    )


if __name__ == "__main__":
    unittest.main()
