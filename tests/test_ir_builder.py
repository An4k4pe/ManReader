import unittest

from ir_builder import build_document_ir


class FakeTextBlock:
    def __init__(self, text: str, bbox: tuple[float, float, float, float]) -> None:
        self.text = text
        self.bbox = bbox
        self.avg_font_size = 10.0
        self.is_bold = False
        self.is_italic = False


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
        self.assertIsNotNone(ir_page.blocks[0].asset)
        self.assertEqual(ir_page.blocks[0].asset.sha, "kept-sha")
        self.assertFalse(ir_page.blocks[0].asset.is_background)
        self.assertFalse(ir_page.blocks[0].asset.is_duplicate)


if __name__ == "__main__":
    unittest.main()
