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
    def test_narrow_left_column_body_crossing_split_is_not_moved_after_right_column(self):
        extractor = object.__new__(PDFExtractor)
        split_x = 250.0

        blocks = [
            make_block(
                "left intro",
                (62.0, 138.0, 299.0, 247.0),
                size=10.0,
            ),
            make_block(
                "left title",
                (157.0, 281.0, 203.0, 294.0),
                size=10.0,
                bold=True,
            ),
            make_block(
                "right intro",
                (314.0, 138.0, 551.0, 223.0),
                size=10.0,
            ),
            make_block(
                "right title",
                (409.0, 239.0, 455.0, 252.0),
                size=10.0,
                bold=True,
            ),
            make_block(
                "right body",
                (332.0, 269.0, 530.0, 412.0),
                size=9.0,
            ),
            make_block(
                "left body",
                (79.0, 308.0, 278.0, 403.0),
                size=9.0,
            ),
            make_block(
                "footer",
                (225.0, 750.0, 375.0, 760.0),
                size=7.0,
            ),
        ]

        ordered = extractor._sort_double_column(
            blocks,
            split_x,
            PAGE_WIDTH,
        )

        self.assertEqual(len(ordered), len(blocks))
        self.assertEqual(
            sorted(id(block) for block in ordered),
            sorted(id(block) for block in blocks),
        )
        self.assertEqual(
            [block.text for block in ordered],
            [
                "left intro",
                "left title",
                "left body",
                "right intro",
                "right title",
                "right body",
                "footer",
            ],
        )

    def test_balanced_cross_split_non_trailing_block_is_preserved(self):
        extractor = object.__new__(PDFExtractor)
        split_x = 250.0

        balanced = make_block(
            "balanced body",
            (200.0, 300.0, 300.0, 330.0),
            size=10.0,
        )

        ordered = extractor._sort_double_column(
            [balanced],
            split_x,
            PAGE_WIDTH,
        )

        self.assertEqual([block.text for block in ordered], ["balanced body"])

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
