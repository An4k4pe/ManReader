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

    def test_keeps_body_blocks_with_normal_vertical_gap_in_same_paragraph(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Prima frase.",
                    bbox=(10.0, 10.0, 100.0, 20.0),
                    style={"avg_font_size": "12"},
                ),
                _text(
                    "b2",
                    "Seconda frase",
                    bbox=(10.0, 24.0, 100.0, 34.0),
                    style={"avg_font_size": "12"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Prima frase. Seconda frase", markdown)
        self.assertNotIn("Prima frase.\n\nSeconda frase", markdown)

    def test_wide_vertical_gap_after_sentence_starts_new_paragraph(self):
        document = _document(
            [
                _text(
                    "b1",
                    "i suoi abitanti ridotti a orrori voraci di carne umana.",
                    bbox=(10.0, 10.0, 300.0, 20.0),
                    style={"avg_font_size": "12"},
                ),
                _text(
                    "b2",
                    "L’Inquisitore Zovyrian stava indagando...",
                    bbox=(10.0, 40.0, 300.0, 50.0),
                    style={"avg_font_size": "12"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn(
            "i suoi abitanti ridotti a orrori voraci di carne umana.\n\n"
            "L’Inquisitore Zovyrian stava indagando...",
            markdown,
        )

    def test_column_transition_with_negative_vertical_gap_starts_new_paragraph(self):
        document = _document(
            [
                _text(
                    "b1",
                    "MOVIMENTO Questo valore si basa sulla tua AGI.",
                    bbox=(62.4, 158.2, 290.8, 211.5),
                    style={"avg_font_size": "12"},
                ),
                _text(
                    "b2",
                    "DANNO BONUS Il danno bonus aumenta il danno inflitto.",
                    bbox=(314.6, 110.2, 547.3, 163.5),
                    style={"avg_font_size": "12"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn(
            "MOVIMENTO Questo valore si basa sulla tua AGI.\n\n"
            "DANNO BONUS Il danno bonus aumenta il danno inflitto.",
            markdown,
        )
        self.assertNotIn("AGI. DANNO BONUS", markdown)

    def test_same_column_fragment_with_negative_vertical_gap_stays_same_paragraph(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Prima frase.",
                    bbox=(62.4, 158.2, 290.8, 211.5),
                    style={"avg_font_size": "12"},
                ),
                _text(
                    "b2",
                    "continua nella stessa colonna",
                    bbox=(70.0, 150.0, 300.0, 163.5),
                    style={"avg_font_size": "12"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Prima frase. continua nella stessa colonna", markdown)
        self.assertNotIn("Prima frase.\n\ncontinua nella stessa colonna", markdown)

    def test_wide_vertical_gap_without_strong_punctuation_stays_same_paragraph(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Prima parte senza punto",
                    bbox=(10.0, 10.0, 200.0, 20.0),
                    style={"avg_font_size": "12"},
                ),
                _text(
                    "b2",
                    "continua sotto",
                    bbox=(10.0, 40.0, 200.0, 50.0),
                    style={"avg_font_size": "12"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Prima parte senza punto continua sotto", markdown)
        self.assertNotIn("Prima parte senza punto\n\ncontinua sotto", markdown)

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

    def test_callout_role_renders_obsidian_info_callout(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Se senti che la capacità eroica indicata nella tua professione non è adatta.",
                    role="callout",
                    metadata={"callout_type": "info", "title": "CAPACITÀ ALTERNATIVE"},
                )
            ]
        )

        markdown = build_markdown(document)

        self.assertIn(
            "> [!INFO] CAPACITÀ ALTERNATIVE\n"
            ">\n"
            "> Se senti che la capacità eroica indicata nella tua professione non è adatta.",
            markdown,
        )
        self.assertNotIn("## CAPACITÀ ALTERNATIVE", markdown)

    def test_callout_does_not_disable_following_bullet_list(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Se senti che la capacità eroica indicata nella tua professione non è adatta.",
                    role="callout",
                    metadata={"callout_type": "info", "title": "CAPACITÀ ALTERNATIVE"},
                ),
                _text(
                    "b2",
                    "✦ Abilità: Osservazione\n✦ Capacità Eroica: Colpo Preciso",
                    role="bullet_list",
                    metadata={"marker": "✦"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("> [!INFO] CAPACITÀ ALTERNATIVE", markdown)
        self.assertIn("- Abilità: Osservazione", markdown)
        self.assertIn("- Capacità Eroica: Colpo Preciso", markdown)

    def test_quote_attribution_renders_as_standalone_bold_paragraph(self):
        document = _document(
            [
                _text("b1", "“Marinai si nasce, non si diventa. Terreno solido?”"),
                _text("b2", "– FRIGGA MOGLIE DEL MARE"),
                _text("b3", "Onde schiumose e navi che solcano..."),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn(
            "“Marinai si nasce, non si diventa. Terreno solido?”\n\n"
            "**– FRIGGA MOGLIE DEL MARE**\n\n"
            "Onde schiumose e navi che solcano...",
            markdown,
        )

    def test_quote_attribution_is_not_rendered_as_heading(self):
        document = _document(
            [
                _text("b1", "“Chi guarda il mare non torna mai uguale.”"),
                _text("b2", "– FRIGGA MOGLIE DEL MARE"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("**– FRIGGA MOGLIE DEL MARE**", markdown)
        self.assertNotIn("## – FRIGGA MOGLIE DEL MARE", markdown)

    def test_uppercase_heading_still_renders_as_heading_near_quote_rules(self):
        document = _document([_text("b1", "MARINAIO")])

        markdown = build_markdown(document)

        self.assertIn("## MARINAIO", markdown)

    def test_dash_starting_line_without_previous_quote_is_not_quote_attribution(self):
        document = _document(
            [
                _text("b1", "- FRIGGA MOGLIE DEL MARE"),
            ]
        )

        markdown = build_markdown(document)

        self.assertNotIn("**- FRIGGA MOGLIE DEL MARE**", markdown)

    def test_bullet_list_rendering_is_unchanged_near_quote_rules(self):
        document = _document(
            [
                _text(
                    "b1",
                    "❖ Domanda uno ❖ Domanda due",
                    role="bullet_list",
                    metadata={"marker": "❖"},
                )
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Domanda uno\n- Domanda due", markdown)
        self.assertNotIn("❖ Domanda uno", markdown)

    def test_quote_attribution_after_asset_renders_as_standalone_bold_paragraph(self):
        document = _document(
            [
                _text("b1", "“Chi appartiene al mare non teme la tempesta.”"),
                _asset_block(),
                _text("b2", "– FRIGGA MOGLIE DEL MARE"),
                _text("b3", "Onde schiumose e navi che solcano..."),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn(
            "“Chi appartiene al mare non teme la tempesta.”\n\n"
            "<!-- asset: asset-1 | page: 1 | type: image -->\n"
            "[Immagine: Mappa](/assets/map.png)\n\n"
            "> Descrizione: Mappa del dungeon\n\n"
            "**– FRIGGA MOGLIE DEL MARE**\n\n"
            "Onde schiumose e navi che solcano...",
            markdown,
        )
        self.assertNotIn("## – FRIGGA MOGLIE DEL MARE", markdown)

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

    def test_bullet_list_role_renders_markdown_list(self):
        document = _document(
            [
                _text(
                    "b1",
                    "❖ Domanda uno ❖ Domanda due",
                    role="bullet_list",
                    metadata={"marker": "❖"},
                )
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Domanda uno\n- Domanda due", markdown)
        self.assertNotIn("❖ Domanda uno", markdown)

    def test_bullet_list_flushes_current_paragraph(self):
        document = _document(
            [
                _text("b1", "Paragrafo prima"),
                _text(
                    "b2",
                    "❖ Domanda uno ❖ Domanda due",
                    role="bullet_list",
                    metadata={"marker": "❖"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Paragrafo prima\n\n- Domanda uno\n- Domanda due", markdown)

    def test_bullet_list_normalizes_internal_newlines(self):
        document = _document(
            [
                _text(
                    "b1",
                    "❖ Prima voce con\n\nspezzatura ❖ Seconda voce",
                    role="bullet_list",
                    metadata={"marker": "❖"},
                )
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Prima voce con spezzatura\n- Seconda voce", markdown)

    def test_bullet_list_collects_consecutive_text_blocks(self):
        document = _document(
            [
                _text("b1", "❖ Prima voce", role="bullet_list", metadata={"marker": "❖"}),
                _text("b2", "continua qui ❖ Seconda"),
                _text("b3", "voce finale"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Prima voce continua qui\n- Seconda voce finale", markdown)
        rendered_list = markdown.split("<!-- page: 1 -->", 1)[1]
        self.assertNotIn("❖", rendered_list)

    def test_bullet_list_stops_before_asset(self):
        document = _document(
            [
                _text("b1", "❖ Prima voce", role="bullet_list", metadata={"marker": "❖"}),
                _text("b2", "continua"),
                _asset_block(),
                _text("b3", "Dopo asset"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Prima voce continua\n\n<!-- asset: asset-1", markdown)
        self.assertIn("> Descrizione: Mappa del dungeon\n\nDopo asset", markdown)

    def test_bullet_list_stops_before_heading(self):
        document = _document(
            [
                _text("b1", "❖ Prima voce", role="bullet_list", metadata={"marker": "❖"}),
                _text("b2", "DOMANDE"),
                _text("b3", "Paragrafo dopo"),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("- Prima voce\n\n## DOMANDE\n\nParagrafo dopo", markdown)
        self.assertNotIn("- DOMANDE", markdown)

    def test_bullet_list_uses_default_marker(self):
        document = _document([_text("b1", "❖ Uno ❖ Due", role="bullet_list")])

        markdown = build_markdown(document)

        self.assertIn("- Uno\n- Due", markdown)

    def test_invalid_font_size_uses_safe_paragraph_gap_fallback(self):
        document = _document(
            [
                _text(
                    "b1",
                    "Prima frase.",
                    bbox=(10.0, 10.0, 100.0, 20.0),
                    style={"avg_font_size": "0"},
                ),
                _text(
                    "b2",
                    "Seconda frase",
                    bbox=(10.0, 24.0, 100.0, 34.0),
                    style={"avg_font_size": "0"},
                ),
            ]
        )

        markdown = build_markdown(document)

        self.assertIn("Prima frase. Seconda frase", markdown)
        self.assertNotIn("Prima frase.\n\nSeconda frase", markdown)

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


def _text(
    block_id: str,
    text: str,
    style: dict[str, str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    role: str | None = None,
    metadata: dict[str, str] | None = None,
) -> BlockIR:
    return BlockIR(
        id=block_id,
        type="text",
        page_num=1,
        order=1,
        bbox=bbox,
        text=text,
        style=style or {},
        role=role,
        metadata=metadata or {},
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
