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
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 98.0, 48.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)
        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].type, "text")
        self.assertEqual(
            callouts[0].metadata,
            {"callout_type": "info", "title": "CAPACITÀ ALTERNATIVE"},
        )
        self.assertEqual(callouts[0].text, body)
        self.assertEqual(callouts[0].bbox, (10.0, 10.0, 95.0, 44.0))

    def test_does_not_merge_uppercase_title_and_body_without_graphic_region(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(
                    "Questo testo segue un titolo uppercase ma non è dentro una regione grafica condivisa.",
                    (10.0, 24.0, 95.0, 44.0),
                ),
            ]
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

    def test_merges_callout_when_title_and_body_share_vector_region(self):
        body = (
            "Se senti che la capacità eroica indicata nella tua professione non è adatta "
            "per il personaggio che vuoi creare, il GM può permetterti di sceglierne un'altra."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(body, (10.0, 24.0, 95.0, 44.0)),
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 98.0, 48.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "CAPACITÀ ALTERNATIVE")
        self.assertTrue(any(block.type == "vector" for block in ir_page.blocks))

    def test_merges_callout_when_title_is_immediately_above_body_region(self):
        body = (
            "Il tuo personaggio è un abile individuo con una debolezza importante "
            "che mette in moto complicazioni e scelte interessanti durante il gioco."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("DEBOLEZZA", (10.0, 10.0, 55.0, 20.0)),
                FakeTextBlock(body, (10.0, 26.0, 95.0, 56.0)),
            ],
            vectors=[
                FakeAsset((8.0, 22.0, 98.0, 60.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "DEBOLEZZA")
        self.assertEqual(callouts[0].text, body)

    def test_merges_callout_when_body_is_bullet_list_inside_graphic_region(self):
        body = (
            "✦ Istinti da Cacciatore: puoi seguire tracce, percepire pericoli nascosti "
            "e aiutare il gruppo quando attraversa territori selvaggi."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: ISTINTI DA CACCIATORE", (10.0, 10.0, 90.0, 20.0)),
                FakeTextBlock(body, (10.0, 26.0, 95.0, 56.0)),
            ],
            images=[FakeAsset((8.0, 8.0, 98.0, 60.0), saved_path="images/callout.jpeg")],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "CAPACITÀ: ISTINTI DA CACCIATORE")
        self.assertEqual(callouts[0].text, body)
        self.assertTrue(any(block.type == "image" for block in ir_page.blocks))

    def test_merges_callout_when_title_crosses_graphic_region_top_edge(self):
        body = (
            "✦ Istinti da Cacciatore: puoi seguire tracce, percepire pericoli nascosti "
            "e aiutare il gruppo quando attraversa territori selvaggi."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: ISTINTI DA CACCIATORE", (10.0, 345.2, 180.0, 357.9)),
                FakeTextBlock(body, (10.0, 371.7, 185.0, 455.1)),
            ],
            images=[FakeAsset((8.0, 350.7, 190.0, 472.9), saved_path="images/callout.jpeg")],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "CAPACITÀ: ISTINTI DA CACCIATORE")
        self.assertEqual(callouts[0].text, body)

    def test_does_not_merge_callout_when_title_is_too_deep_inside_graphic_region(self):
        body = (
            "✦ Scontroso: fatichi a collaborare con gli altri e tendi a rispondere "
            "in modo brusco anche quando sarebbe meglio tacere."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: SCONTROSO", (10.0, 380.0, 140.0, 392.0)),
                FakeTextBlock(body, (10.0, 402.0, 185.0, 455.0)),
            ],
            images=[FakeAsset((8.0, 350.0, 190.0, 472.0), saved_path="images/callout.jpeg")],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))
        self.assertTrue(any(block.role == "bullet_list" for block in ir_page.blocks))

    def test_merges_callout_when_unrelated_non_text_asset_sits_before_body(self):
        body = (
            "✦ Scontroso: fatichi a collaborare con gli altri e tendi a rispondere "
            "in modo brusco anche quando sarebbe meglio tacere."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: SCONTROSO", (120.0, 10.0, 190.0, 22.0)),
                FakeTextBlock(body, (120.0, 40.0, 195.0, 78.0)),
            ],
            images=[FakeAsset((118.0, 8.0, 198.0, 82.0), saved_path="images/right-callout.jpeg")],
            tables=[FakeAsset((10.0, 28.0, 80.0, 54.0), saved_path="tables/left-table.csv")],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "CAPACITÀ: SCONTROSO")
        self.assertEqual(callouts[0].text, body)
        self.assertTrue(any(block.type == "table" for block in ir_page.blocks))

    def test_does_not_skip_text_outside_region_before_callout_body(self):
        body = (
            "✦ Scontroso: fatichi a collaborare con gli altri e tendi a rispondere "
            "in modo brusco anche quando sarebbe meglio tacere."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: SCONTROSO", (120.0, 10.0, 190.0, 22.0)),
                FakeTextBlock("Testo normale fuori dalla box", (10.0, 28.0, 80.0, 40.0)),
                FakeTextBlock(body, (120.0, 44.0, 195.0, 78.0)),
            ],
            images=[FakeAsset((118.0, 8.0, 198.0, 82.0), saved_path="images/right-callout.jpeg")],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))
        self.assertTrue(any(block.role == "bullet_list" for block in ir_page.blocks))

    def test_does_not_merge_when_asset_is_skipped_but_bullet_body_is_outside_region(self):
        body = (
            "✦ Scontroso: fatichi a collaborare con gli altri e tendi a rispondere "
            "in modo brusco anche quando sarebbe meglio tacere."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: SCONTROSO", (120.0, 10.0, 190.0, 22.0)),
                FakeTextBlock(body, (10.0, 44.0, 85.0, 78.0)),
            ],
            images=[
                FakeAsset((118.0, 8.0, 198.0, 82.0), saved_path="images/right-callout.jpeg"),
                FakeAsset((10.0, 28.0, 80.0, 40.0), saved_path="images/left-decor.jpeg"),
            ],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))
        self.assertTrue(any(block.role == "bullet_list" for block in ir_page.blocks))

    def test_merges_callout_with_multiple_text_body_blocks_inside_region(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("ABBREVIAZIONI", (10.0, 10.0, 90.0, 22.0)),
                FakeTextBlock("FOR indica la Forza del personaggio.", (10.0, 30.0, 150.0, 42.0)),
                FakeTextBlock("AGI indica la sua Agilità.", (10.0, 46.0, 150.0, 58.0)),
                FakeTextBlock("INT indica la capacità di ragionare.", (10.0, 62.0, 150.0, 74.0)),
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 160.0, 80.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "ABBREVIAZIONI")
        self.assertEqual(
            callouts[0].text,
            (
                "FOR indica la Forza del personaggio. AGI indica la sua Agilità. "
                "INT indica la capacità di ragionare."
            ),
        )

    def test_callout_aggregation_stops_before_text_outside_region(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("ABBREVIAZIONI", (10.0, 10.0, 90.0, 22.0)),
                FakeTextBlock(
                    "FOR indica la Forza del personaggio durante prove fisiche e combattimento.",
                    (10.0, 30.0, 150.0, 42.0),
                ),
                FakeTextBlock("Questo paragrafo è fuori dalla box.", (180.0, 46.0, 260.0, 70.0)),
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 160.0, 80.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(
            callouts[0].text,
            "FOR indica la Forza del personaggio durante prove fisiche e combattimento.",
        )
        self.assertTrue(
            any(block.text == "Questo paragrafo è fuori dalla box." for block in ir_page.blocks)
        )

    def test_does_not_merge_when_text_outside_region_precedes_any_body_fragment(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("ABBREVIAZIONI", (10.0, 10.0, 90.0, 22.0)),
                FakeTextBlock("Questo paragrafo è fuori dalla box.", (180.0, 30.0, 260.0, 54.0)),
                FakeTextBlock("FOR indica la Forza del personaggio.", (10.0, 58.0, 150.0, 70.0)),
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 160.0, 80.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

    def test_merges_two_side_by_side_callouts_by_matching_each_region(self):
        right_body = (
            "✦ Rancoroso: quando subisci un torto, ricordi l'offesa e ottieni "
            "motivazione per rispondere al momento giusto."
        )
        left_body = (
            "✦ Difficile da Prendere: sai divincolarti rapidamente quando qualcuno "
            "prova a bloccarti o trascinarti via."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: RANCOROSO", (120.0, 10.0, 190.0, 22.0)),
                FakeTextBlock("CAPACITÀ: DIFFICILE DA PRENDERE", (10.0, 11.0, 112.0, 23.0)),
                FakeTextBlock(right_body, (122.0, 40.0, 195.0, 78.0)),
                FakeTextBlock(left_body, (12.0, 41.0, 110.0, 79.0)),
            ],
            images=[
                FakeAsset((118.0, 18.0, 198.0, 82.0), saved_path="images/right-callout.jpeg"),
                FakeAsset((8.0, 19.0, 115.0, 83.0), saved_path="images/left-callout.jpeg"),
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 2)
        callout_by_title = {block.metadata["title"]: block.text for block in callouts}
        self.assertEqual(callout_by_title["CAPACITÀ: RANCOROSO"], right_body)
        self.assertEqual(callout_by_title["CAPACITÀ: DIFFICILE DA PRENDERE"], left_body)
        self.assertNotEqual(
            callout_by_title["CAPACITÀ: RANCOROSO"],
            callout_by_title["CAPACITÀ: DIFFICILE DA PRENDERE"],
        )

    def test_does_not_merge_callout_when_bullet_list_body_is_outside_graphic_region(self):
        body = (
            "✦ Scontroso: fatichi a collaborare con gli altri e tendi a rispondere "
            "in modo brusco anche quando sarebbe meglio tacere."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ: SCONTROSO", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(body, (10.0, 52.0, 95.0, 82.0)),
            ],
            images=[FakeAsset((8.0, 8.0, 98.0, 28.0), saved_path="images/callout.jpeg")],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))
        self.assertTrue(any(block.role == "bullet_list" for block in ir_page.blocks))

    def test_does_not_merge_when_title_outside_region_and_body_inside_region(self):
        body = (
            "Il tuo personaggio è un abile individuo con una debolezza importante "
            "che mette in moto complicazioni e scelte interessanti durante il gioco."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("DEBOLEZZA", (10.0, 10.0, 55.0, 20.0)),
                FakeTextBlock(body, (10.0, 36.0, 95.0, 66.0)),
            ],
            vectors=[
                FakeAsset((8.0, 32.0, 98.0, 70.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

    def test_does_not_merge_when_title_inside_region_and_body_outside_region(self):
        body = (
            "Il tuo personaggio è un abile individuo con una debolezza importante "
            "che mette in moto complicazioni e scelte interessanti durante il gioco."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("DEBOLEZZA", (10.0, 10.0, 55.0, 20.0)),
                FakeTextBlock(body, (10.0, 52.0, 95.0, 82.0)),
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 98.0, 28.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

    def test_does_not_use_full_page_region_as_callout_evidence(self):
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock(
                    "Questo testo sarebbe compatibile, ma lo sfondo pagina non è una box callout.",
                    (10.0, 24.0, 95.0, 44.0),
                ),
            ],
            images=[FakeAsset((0.0, 0.0, 100.0, 100.0), is_background=True)],
        )

        ir_page = self.build_page(page)

        self.assertEqual(len(ir_page.blocks), 2)
        self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

    def test_heading_does_not_steal_body_from_later_box_region(self):
        body = (
            "Se senti che la capacità eroica indicata nella tua professione non è adatta "
            "per il personaggio che vuoi creare, il GM può permetterti di sceglierne un'altra."
        )
        page = FakePage(
            text_blocks=[
                FakeTextBlock("CAPACITÀ EROICHE", (10.0, 10.0, 80.0, 20.0)),
                FakeTextBlock("CAPACITÀ ALTERNATIVE", (10.0, 34.0, 80.0, 44.0)),
                FakeTextBlock(body, (10.0, 50.0, 95.0, 70.0)),
            ],
            vectors=[
                FakeAsset((8.0, 32.0, 98.0, 74.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(callouts[0].metadata["title"], "CAPACITÀ ALTERNATIVE")
        self.assertEqual(ir_page.blocks[0].text, "CAPACITÀ EROICHE")
        self.assertIsNone(ir_page.blocks[0].role)

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

    def test_known_section_headings_without_shared_region_do_not_become_callouts(self):
        for title in ["MAGO", "MAGIA", "MERCANTE", "STUDIOSO", "ABILITÀ"]:
            with self.subTest(title=title):
                page = FakePage(
                    text_blocks=[
                        FakeTextBlock(title, (10.0, 10.0, 80.0, 20.0)),
                        FakeTextBlock(
                            "Questo testo di sezione resta nel normale flusso senza una box grafica condivisa.",
                            (10.0, 24.0, 95.0, 44.0),
                        ),
                    ],
                    vectors=[
                        FakeAsset(
                            (0.0, 70.0, 100.0, 90.0), saved_path="vectors/decor.svg", ext="svg"
                        )
                    ],
                )

                ir_page = self.build_page(page)

                self.assertTrue(all(block.role != "callout" for block in ir_page.blocks))

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
            ],
            vectors=[
                FakeAsset((8.0, 8.0, 98.0, 48.0), saved_path="vectors/callout.svg", ext="svg")
            ],
        )

        ir_page = self.build_page(page)

        callouts = [block for block in ir_page.blocks if block.role == "callout"]
        bullets = [block for block in ir_page.blocks if block.role == "bullet_list"]
        self.assertEqual(len(callouts), 1)
        self.assertEqual(len(bullets), 1)
        self.assertEqual(bullets[0].metadata, {"marker": "✦"})

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
