import unittest

from extractor import PDFExtractor, TextBlock, TextSpan

PAGE_WIDTH = 1000.0
SPLIT_X = 500.0


def make_block(
    text: str,
    bbox: tuple[float, float, float, float],
    *,
    size: float = 10.0,
    bold: bool = False,
) -> TextBlock:
    return TextBlock(
        spans=[
            TextSpan(
                text=text,
                font="TestFont",
                size=size,
                bold=bold,
                italic=False,
                bbox=bbox,
            )
        ],
        bbox=bbox,
    )


class ExtractorReadingOrderTest(unittest.TestCase):
    def test_double_column_order_is_split_into_zones_by_cross_gutter_heading(self):
        extractor = object.__new__(PDFExtractor)
        blocks = [
            make_block("top heading", (250.0, 80.0, 750.0, 130.0), size=24.0, bold=True),
            make_block("left intro", (90.0, 150.0, 470.0, 210.0)),
            make_block("left movement", (90.0, 230.0, 470.0, 300.0)),
            make_block("right bonus", (530.0, 150.0, 910.0, 210.0)),
            make_block("right wounds", (530.0, 230.0, 910.0, 300.0)),
            make_block("right willpower", (530.0, 320.0, 910.0, 390.0)),
            make_block("middle heading", (360.0, 470.0, 640.0, 520.0), size=24.0, bold=True),
            make_block("left skills intro", (90.0, 540.0, 470.0, 610.0)),
            make_block("left base value", (90.0, 630.0, 470.0, 700.0)),
            make_block("left initial level", (90.0, 720.0, 470.0, 790.0)),
            make_block("right table asset text", (530.0, 540.0, 910.0, 610.0)),
            make_block("right profession", (530.0, 630.0, 910.0, 700.0)),
            make_block("right secondary", (530.0, 720.0, 910.0, 790.0)),
            make_block("footer", (360.0, 840.0, 640.0, 860.0), size=8.0),
        ]

        ordered = extractor._sort_double_column(blocks, SPLIT_X, PAGE_WIDTH)

        self.assertEqual(
            [block.text for block in ordered],
            [
                "top heading",
                "left intro",
                "left movement",
                "right bonus",
                "right wounds",
                "right willpower",
                "middle heading",
                "left skills intro",
                "left base value",
                "left initial level",
                "right table asset text",
                "right profession",
                "right secondary",
                "footer",
            ],
        )


if __name__ == "__main__":
    unittest.main()
