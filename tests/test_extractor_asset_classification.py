import unittest

from extractor import (
    ImageBlock,
    TableBlock,
    TextBlock,
    TextSpan,
    VectorBlock,
    _classify_page_visual_assets,
)


class ExtractorAssetClassificationTest(unittest.TestCase):
    def test_small_footer_image_without_contained_text_is_decorative(self):
        image = _image((20.0, 760.0, 45.0, 785.0))

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertEqual(image.classification, "decorative")

    def test_box_like_image_with_contained_text_is_structural(self):
        image = _image((80.0, 120.0, 320.0, 260.0))
        text = _text_block("boxed prose", (110.0, 150.0, 290.0, 210.0))

        _classify_page_visual_assets([image], [], [text], [], 600.0, 800.0)

        self.assertEqual(image.classification, "structural")

    def test_large_central_image_remains_unclassified(self):
        image = _image((120.0, 160.0, 520.0, 620.0))

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertIsNone(image.classification)

    def test_thin_vector_associated_with_table_bbox_is_structural(self):
        vector = _vector((80.0, 200.0, 520.0, 203.0))
        table = _table((70.0, 180.0, 530.0, 300.0))

        _classify_page_visual_assets([], [vector], [], [table], 600.0, 800.0)

        self.assertEqual(vector.classification, "structural")

    def test_large_central_non_thin_vector_remains_unclassified(self):
        vector = _vector((120.0, 160.0, 520.0, 520.0))

        _classify_page_visual_assets([], [vector], [], [], 600.0, 800.0)

        self.assertIsNone(vector.classification)

    def test_table_csv_is_not_marked_decorative(self):
        table = _table((70.0, 180.0, 530.0, 300.0))

        _classify_page_visual_assets([], [], [], [table], 600.0, 800.0)

        self.assertNotEqual(getattr(table, "classification", None), "decorative")

    def test_existing_asset_classification_is_not_overwritten(self):
        image = _image((20.0, 760.0, 45.0, 785.0), classification="readable")

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertEqual(image.classification, "readable")


def _image(
    bbox: tuple[float, float, float, float],
    *,
    classification: str | None = None,
) -> ImageBlock:
    return ImageBlock(
        image_data=b"",
        ext="png",
        bbox=bbox,
        page_num=0,
        index=0,
        classification=classification,
    )


def _vector(
    bbox: tuple[float, float, float, float],
    *,
    classification: str | None = None,
) -> VectorBlock:
    return VectorBlock(
        bbox=bbox,
        page_num=0,
        index=0,
        classification=classification,
    )


def _table(bbox: tuple[float, float, float, float]) -> TableBlock:
    return TableBlock(rows=[["A", "B"], ["1", "2"]], bbox=bbox, page_num=0, index=0)


def _text_block(text: str, bbox: tuple[float, float, float, float]) -> TextBlock:
    return TextBlock(
        spans=[
            TextSpan(
                text=text,
                font="TestFont",
                size=10.0,
                bold=False,
                italic=False,
                bbox=bbox,
            )
        ],
        bbox=bbox,
    )


if __name__ == "__main__":
    unittest.main()
