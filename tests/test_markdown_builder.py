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

    def test_heading_is_not_merged_with_following_paragraph(self):
        document = _document(
            [
                _text("b1", "Capitolo Uno", style={"avg_font_size": "16"}),
                _text("b2", "Primo paragrafo"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("## Capitolo Uno\n\nPrimo paragrafo", markdown)
        self.assertNotIn("Capitolo Uno Primo paragrafo", markdown)

    def test_scena_heading_becomes_markdown_heading(self):
        document = _document([_text("b1", "Scena 1: Briefing")])

        markdown = build_markdown(document)

        self.assertIn("## Scena 1: Briefing", markdown)

    def test_uppercase_text_becomes_markdown_heading(self):
        document = _document([_text("b1", "DOMANDE")])

        markdown = build_markdown(document)

        self.assertIn("## DOMANDE", markdown)

    def test_normal_text_stays_paragraph(self):
        document = _document(
            [
                _text("b1", "Questo è testo normale"),
                _text("b2", "con un secondo frammento"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Questo è testo normale con un secondo frammento", markdown)
        self.assertNotIn("## Questo è testo normale", markdown)

    def test_bold_inline_text_uses_markdown_strong(self):
        document = _document([_text("b1", "testo", style={"bold": "true"})])

        markdown = build_markdown(document)

        self.assertIn("**testo**", markdown)
        self.assertNotIn("## **testo**", markdown)

    def test_bold_italic_inline_text_uses_markdown_strong_emphasis(self):
        document = _document([_text("b1", "testo", style={"bold": "true", "italic": "true"})])

        markdown = build_markdown(document)

        self.assertIn("***testo***", markdown)

    def test_bold_heading_does_not_get_inline_formatting(self):
        document = _document([_text("b1", "Scena 1: Briefing", style={"bold": "true"})])

        markdown = build_markdown(document)

        self.assertIn("## Scena 1: Briefing", markdown)
        self.assertNotIn("## **Scena 1: Briefing**", markdown)

    def test_bold_inline_text_is_not_heading(self):
        document = _document(
            [
                _text("b1", "Arufex Vladaghast", style={"bold": "true"}),
                _text("b2", ", un botanico"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("**Arufex Vladaghast**, un botanico", markdown)
        self.assertNotIn("## Arufex Vladaghast", markdown)

    def test_long_styled_text_is_not_wrapped_in_emphasis(self):
        long_text = (
            "Questo è un frammento molto lungo che rappresenta una riga di corpo "
            "estratta dal PDF e non deve diventare corsivo interamente"
        )
        document = _document([_text("b1", long_text, style={"italic": "true"})])

        markdown = build_markdown(document)

        self.assertIn(long_text, markdown)
        self.assertNotIn(f"*{long_text}*", markdown)

    def test_short_split_fragment_is_not_emphasized(self):
        document = _document([_text("b1", "o", style={"italic": "true"})])

        markdown = build_markdown(document)

        self.assertIn("o", markdown)
        self.assertNotIn("*o*", markdown)

    def test_italic_only_text_is_not_emphasized_until_extraction_is_reliable(self):
        document = _document([_text("b1", "testo", style={"italic": "true"})])

        markdown = build_markdown(document)

        self.assertIn("testo", markdown)
        self.assertNotIn("*testo*", markdown)


def _document(blocks: list[BlockIR]) -> DocumentIR:
    return DocumentIR(
        schema_version="1.0",
        source_path="manual.pdf",
        page_count=1,
        pages=[PageIR(id="p1", page_num=1, blocks=blocks)],
    )


def _text(block_id: str, text: str, style: dict[str, str] | None = None) -> BlockIR:
    return BlockIR(
        id=block_id,
        type="text",
        page_num=1,
        order=1,
        text=text,
        style=style or {},
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
