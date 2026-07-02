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

    def test_corner_decoration_marginal_image_is_decorative(self):
        image = _image((8.0, 88.0, 92.0, 165.0))

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertEqual(image.classification, "decorative")

    def test_header_title_decoration_is_decorative(self):
        image = _image((110.0, 16.0, 300.0, 140.0))

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertEqual(image.classification, "decorative")

    def test_possible_decorated_initial_remains_unclassified(self):
        image = _image((48.0, 128.0, 92.0, 188.0))
        text = _text_block(
            "avventuriero che parte per una lunga impresa", (92.0, 126.0, 360.0, 210.0)
        )

        _classify_page_visual_assets([image], [], [text], [], 600.0, 800.0)

        self.assertIsNone(image.classification)

    def test_box_like_image_with_contained_text_is_structural(self):
        image = _image((80.0, 120.0, 320.0, 260.0))
        text = _text_block("boxed prose", (110.0, 150.0, 290.0, 210.0))

        _classify_page_visual_assets([image], [], [text], [], 600.0, 800.0)

        self.assertEqual(image.classification, "structural")

    def test_table_background_image_is_structural(self):
        image = _image((300.0, 80.0, 560.0, 200.0))
        table = _table((330.0, 92.0, 530.0, 178.0))

        _classify_page_visual_assets([image], [], [], [table], 600.0, 800.0)

        self.assertEqual(image.classification, "structural")

    def test_large_central_image_remains_unclassified(self):
        image = _image((120.0, 160.0, 520.0, 620.0))

        _classify_page_visual_assets([image], [], [], [], 600.0, 800.0)

        self.assertIsNone(image.classification)

    def test_large_illustrative_image_overlapping_text_remains_unclassified(self):
        image = _image((80.0, 80.0, 560.0, 560.0))
        text = _text_block("caption or nearby prose", (120.0, 120.0, 520.0, 180.0))

        _classify_page_visual_assets([image], [], [text], [], 600.0, 800.0)

        self.assertIsNone(image.classification)

    def test_thin_vector_associated_with_table_bbox_is_structural(self):
        vector = _vector((80.0, 200.0, 520.0, 203.0))
        table = _table((70.0, 180.0, 530.0, 300.0))

        _classify_page_visual_assets([], [vector], [], [table], 600.0, 800.0)

        self.assertEqual(vector.classification, "structural")

    def test_vector_partially_associated_with_table_bbox_is_structural(self):
        vector = _vector((300.0, 570.0, 424.0, 660.0))
        table = _table((338.0, 558.0, 526.0, 658.0))

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
