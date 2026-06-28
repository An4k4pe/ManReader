import unittest

from ir_builder import build_document_ir


class FakeTextBlock:
    def __init__(
        self,
        text: str,
        bbox: tuple[float, float, float, float],
        *,
        avg_font_size: float = 10.0,
        is_bold: bool = False,
        is_italic: bool = False,
    ) -> None:
        self.text = text
        self.bbox = bbox
        self.avg_font_size = avg_font_size
        self.is_bold = is_bold
        self.is_italic = is_italic


class FakeAsset:
    def __init__(
        self,
        bbox: tuple[float, float, float, float],
        *,
        saved_path="images/asset.png",
        ext="png",
        description: str | None = None,
        is_background: bool = False,
        is_duplicate: bool = False,
        sha: str | None = None,
    ) -> None:
        self.bbox = bbox
        self.saved_path = saved_path
        self.ext = ext
        self.description = description
        self.is_background = is_background
        self.is_duplicate = is_duplicate
        self.sha = sha


class FakePage:
    def __init__(
        self,
        *,
        text_blocks: list[FakeTextBlock] | None = None,
        images: list[FakeAsset] | None = None,
        vectors: list[FakeAsset] | None = None,
        tables: list[FakeAsset] | None = None,
    ) -> None:
        self.page_num = 0
        self.width = 100.0
        self.height = 100.0
        self.text_blocks = text_blocks or []
        self.images = images or []
        self.vectors = vectors or []
        self.tables = tables or []


class IRBuilderTest(unittest.TestCase):
    from ir_model import PageIR

    ...

    def build_page(self, page: FakePage) -> PageIR:
        document = build_document_ir([page], source_path="manual.pdf")
        return document.pages[0]

    def test_orders_text_blocks_on_same_row_left_to_right(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("second", (40.0, 10.0, 50.0, 20.0)),
                FakeTextBlock("first", (10.0, 10.0, 20.0, 20.0)),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual([block.text for block in ir_page.blocks], ["first", "second"])

    def test_merges_adjacent_text_fragments_on_same_row(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("Vlada", (10.0, 10.0, 20.0, 20.0)),
                FakeTextBlock("ghast", (21.0, 10.0, 35.0, 20.0)),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 1)
        self.assertEqual(ir_page.blocks[0].text, "Vladaghast")
        self.assertEqual(ir_page.blocks[0].bbox, (10.0, 10.0, 35.0, 20.0))

    def test_does_not_merge_text_on_different_rows(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("first", (10.0, 10.0, 20.0, 20.0)),
                FakeTextBlock("second", (10.0, 14.0, 25.0, 24.0)),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual([block.text for block in ir_page.blocks], ["first", "second"])

    def test_marks_text_with_question_marker_as_bullet_list(self):
        page = FakePage(
            text_blocks=[FakeTextBlock("❖ Domanda uno ❖ Domanda due", (10.0, 10.0, 50.0, 20.0))]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].type, "text")
        self.assertEqual(ir_page.blocks[0].role, "bullet_list")
        self.assertEqual(ir_page.blocks[0].metadata, {"marker": "❖"})

    def test_merges_nearby_uppercase_title_and_body_as_callout(self):
        body = (
            "Se senti che la capacità eroica indicata nella tua professione non è adatta "
            "per il personaggio che vuoi creare, il GM può permetterti di sceglierne un'altra."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(body, (10.0, 24.0, 95.0, 44.0)),
            ]
        )

        ir_page = self.build_page(page)
        self.assertEqual(len(ir_page.blocks), 1)
        self.assertEqual(ir_page.blocks[0].type, "text")
        self.assertEqual(ir_page.blocks[0].role, "callout")
        self.assertEqual(
            ir_page.blocks[0].metadata,
            {"callout_type": "info", "title": "CAPACITÀ ALTERNATIVE"},
        )
        self.assertEqual(ir_page.blocks[0].text, body)
        self.assertEqual(ir_page.blocks[0].bbox, (10.0, 10.0, 95.0, 44.0))

    def test_merges_callout_when_graphic_asset_sits_between_title_and_body(self):
        body = (
            "Se senti che la capacità eroica indicata nella tua professione non è adatta "
            "per il personaggio che vuoi creare, il GM può permetterti di sceglierne un'altra."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(body, (10.0, 42.0, 95.0, 62.0)),
            ],
            images=[
                FakeAsset(
                    (8.0, 21.0, 98.0, 40.0),
                    saved_path="images/callout-decoration.png",
                    sha="callout-decoration-sha",
                )
            ],
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertEqual(ir_page.blocks[0].type, "text")
        self.assertEqual(ir_page.blocks[0].role, "callout")
        self.assertEqual(
            ir_page.blocks[0].metadata,
            {"callout_type": "info", "title": "CAPACITÀ ALTERNATIVE"},
        )
        self.assertEqual(ir_page.blocks[0].text, body)
        self.assertEqual(ir_page.blocks[0].bbox, (10.0, 10.0, 95.0, 62.0))
        self.assertEqual(ir_page.blocks[1].type, "image")
        self.assertEqual([block.order for block in ir_page.blocks], [1, 2])

    def test_keeps_dash_attribution_outside_callout(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("– CYRIL CHIOMA DI FUOCO", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(
                    (
                        "I maghi hanno imparato a controllare le antiche forze che permeano "
                        "la natura e le strutture primordiali del mondo."
                    ),
                    (10.0, 24.0, 95.0, 44.0),
                ),
            ]
        )

        ir_page = self.build_page(page)
        self.assertEqual(len(ir_page.blocks), 2)
        self.assertIsNone(ir_page.blocks[0].role)
        self.assertIsNone(ir_page.blocks[1].role)

    def test_keeps_large_heading_and_following_paragraph_outside_callout(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 24.0), avg_font_size=16.0),
                FakeTextBlock(
                    "Questo paragrafo descrive la sezione e deve restare nel normale flusso.",
                    (10.0, 28.0, 95.0, 48.0),
                ),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertIsNone(ir_page.blocks[0].role)
        self.assertIsNone(ir_page.blocks[1].role)

    def test_keeps_single_word_uppercase_heading_outside_callout(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("DOMANDE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(
                    "Questo paragrafo segue una heading breve e non deve diventare un callout.",
                    (10.0, 24.0, 95.0, 44.0),
                ),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertIsNone(ir_page.blocks[0].role)
        self.assertIsNone(ir_page.blocks[1].role)

    def test_callout_merge_preserves_following_bullet_list(self):
        body = (
            "Se senti che la capacità eroica indicata nella tua professione non è adatta "
            "per il personaggio che vuoi creare, il GM può permetterti di sceglierne un’altra."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(body, (10.0, 24.0, 95.0, 44.0)),
                FakeTextBlock("✦ Abilità: Osservazione, Furtività", (10.0, 60.0, 95.0, 72.0)),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertEqual(ir_page.blocks[0].role, "callout")
        self.assertEqual(ir_page.blocks[1].role, "bullet_list")
        self.assertEqual(ir_page.blocks[1].metadata, {"marker": "✦"})

    def test_splits_inline_trait_bullets_onto_separate_lines(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    (
                        "✦ Attributo Principale: AGI ✦ Abilità: Acrobazia, Coltelli "
                        "✦ Capacità Eroica: Pugnalata alle Spalle"
                    ),
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(
            ir_page.blocks[0].text,
            (
                "✦ Attributo Principale: AGI\n"
                "✦ Abilità: Acrobazia, Coltelli\n"
                "✦ Capacità Eroica: Pugnalata alle Spalle"
            ),
        )

    def test_marks_inline_trait_bullets_as_bullet_list(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    "✦ Attributo Principale: AGI ✦ Abilità: Acrobazia",
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].role, "bullet_list")
        self.assertEqual(ir_page.blocks[0].metadata, {"marker": "✦"})

    def test_keeps_single_trait_bullet_unchanged(self):
        page = FakePage(
            text_blocks=[FakeTextBlock("✦ Attributo Principale: AGI", (10.0, 10.0, 50.0, 20.0))]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].text, "✦ Attributo Principale: AGI")
        self.assertEqual(ir_page.blocks[0].role, "bullet_list")
        self.assertEqual(ir_page.blocks[0].metadata, {"marker": "✦"})

    def test_keeps_already_multiline_trait_bullets_unchanged(self):
        text = "✦ Attributo Principale: AGI\n✦ Abilità: Acrobazia"
        page = FakePage(text_blocks=[FakeTextBlock(text, (10.0, 10.0, 50.0, 20.0))])

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].text, text)
        self.assertEqual(ir_page.blocks[0].role, "bullet_list")
        self.assertEqual(ir_page.blocks[0].metadata, {"marker": "✦"})

    def test_keeps_text_with_internal_question_marker_without_role_or_metadata(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    "continuazione della frase ❖ Domanda due",
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertIsNone(ir_page.blocks[0].role)
        self.assertEqual(ir_page.blocks[0].metadata, {})

    def test_keeps_normal_text_without_role_or_metadata(self):
        page = FakePage(text_blocks=[FakeTextBlock("Testo normale", (10.0, 10.0, 50.0, 20.0))])

        ir_page = self.build_page(page)

        self.assertIsNone(ir_page.blocks[0].role)
        self.assertEqual(ir_page.blocks[0].metadata, {})

    def test_normalizes_pdf_hyphenated_words_in_normal_text_blocks(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    (
                        "È probabil- mente una acqui- sizione per lavo- rare con "
                        "individua- listi, Consape- volezza, Sgattaio- lare, "
                        "Que- sta e auto- ritari."
                    ),
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(
            ir_page.blocks[0].text,
            (
                "È probabilmente una acquisizione per lavorare con "
                "individualisti, Consapevolezza, Sgattaiolare, Questa e autoritari."
            ),
        )

    def test_normalizes_pdf_hyphenated_words_in_bullet_list_blocks(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    "✦ Capa- cità Eroica: Sgattaio- lare nell'ombra",
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(
            ir_page.blocks[0].text,
            "✦ Capacità Eroica: Sgattaiolare nell'ombra",
        )

    def test_preserves_bullet_list_role_and_metadata_after_hyphenation_normalization(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock(
                    "❖ Consapevolezza del pericolo",
                    (10.0, 10.0, 50.0, 20.0),
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].text, "❖ Consapevolezza del pericolo")
        self.assertEqual(ir_page.blocks[0].role, "bullet_list")
        self.assertEqual(ir_page.blocks[0].metadata, {"marker": "❖"})

    def test_keeps_real_hyphens_and_dashes_unchanged(self):
        text = "local-first arma - scudo – FRIGgA MOGLIE DEL MARE 1–2 D6 razioni di cibo"
        page = FakePage(text_blocks=[FakeTextBlock(text, (10.0, 10.0, 50.0, 20.0))])

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks[0].text, text)

    def test_excludes_background_image_asset(self):
        page = FakePage(
            images=[
                FakeAsset(
                    (10.0, 10.0, 20.0, 20.0),
                    is_background=True,
                    sha="background-sha",
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks, [])

    def test_excludes_duplicate_image_asset(self):
        page = FakePage(
            images=[
                FakeAsset(
                    (10.0, 10.0, 20.0, 20.0),
                    is_duplicate=True,
                    sha="duplicate-sha",
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(ir_page.blocks, [])

    def test_keeps_non_background_non_duplicate_image_asset(self):
        page = FakePage(
            images=[
                FakeAsset(
                    (10.0, 10.0, 20.0, 20.0),
                    saved_path="images/kept.png",
                    sha="kept-sha",
                )
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 1)
        self.assertEqual(ir_page.blocks[0].type, "image")
        asset = ir_page.blocks[0].asset
        assert asset is not None
        self.assertEqual(asset.sha, "kept-sha")
        self.assertFalse(asset.is_background)
        self.assertFalse(asset.is_duplicate)


if __name__ == "__main__":
    unittest.main()
