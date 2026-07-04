import unittest

import fitz

from extractor import (
    TableBlock,
    TextBlock,
    TextSpan,
    _asset_may_be_unresolved_dropcap,
    _dropcap_bboxes,
    _starts_like_missing_initial,
)


class _FakePage:
    def __init__(
        self,
        *,
        image_rects: list[tuple[float, float, float, float]] | None = None,
        drawings: list[tuple[float, float, float, float]] | None = None,
    ) -> None:
        self._image_rects = image_rects or []
        self._drawings = drawings or []

    def get_images(self, full: bool = False) -> list[tuple[int]]:
        return [(index + 1,) for index in range(len(self._image_rects))]

    def get_image_rects(self, xref: int) -> list[fitz.Rect]:
        index = xref - 1
        return [fitz.Rect(*self._image_rects[index])]

    def get_drawings(self) -> list[dict[str, fitz.Rect]]:
        return [{"rect": fitz.Rect(*bbox)} for bbox in self._drawings]


class ExtractorDropcapTest(unittest.TestCase):
    def test_starts_like_missing_initial_with_apostrophe(self):
        self.assertTrue(_starts_like_missing_initial("’avventuriero che interpreti"))

    def test_starts_like_missing_initial_with_lowercase(self):
        self.assertTrue(_starts_like_missing_initial("avventuriero che interpreti"))

    def test_starts_like_missing_initial_rejects_normal_uppercase(self):
        self.assertFalse(_starts_like_missing_initial("L’avventuriero che interpreti"))

    def test_asset_may_be_unresolved_dropcap_near_suspicious_body_start(self):
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        self.assertTrue(
            _asset_may_be_unresolved_dropcap(
                (18.0, 96.0, 38.0, 136.0),
                [text],
                [],
                600.0,
                800.0,
            )
        )

    def test_asset_dropcap_rejects_normal_uppercase_body_start(self):
        text = _text_block(
            "L’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        self.assertFalse(
            _asset_may_be_unresolved_dropcap(
                (18.0, 96.0, 38.0, 136.0),
                [text],
                [],
                600.0,
                800.0,
            )
        )

    def test_raw_drawing_rect_compatible_produces_dropcap_candidate(self):
        page = _FakePage(drawings=[(18.0, 96.0, 38.0, 136.0)])
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(bboxes, [(18.0, 96.0, 38.0, 136.0)])

    def test_asset_dropcap_rejects_header_region(self):
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 30.0, 180.0, 42.0),
        )

        self.assertFalse(
            _asset_may_be_unresolved_dropcap(
                (18.0, 24.0, 38.0, 64.0),
                [text],
                [],
                600.0,
                800.0,
            )
        )

    def test_overlapping_candidates_keep_best_first_line_alignment(self):
        worse_bbox = (60.3622, 126.0550, 94.0881, 176.4853)
        better_bbox = (57.7910, 136.9830, 96.7910, 177.9830)
        page = _FakePage(drawings=[worse_bbox, better_bbox])
        text = _text_block(
            "’avventuriero che interpreti",
            (90.62, 137.85, 260.0, 149.85),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(bboxes, [better_bbox])

    def test_separate_candidates_remain_distinct(self):
        upper_bbox = (18.0, 80.0, 38.0, 102.0)
        lower_bbox = (18.0, 110.0, 38.0, 140.0)
        page = _FakePage(drawings=[upper_bbox, lower_bbox])
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(bboxes, [upper_bbox, lower_bbox])

    def test_raw_image_and_drawing_for_same_dropcap_keep_best_aligned_bbox(self):
        worse_bbox = (60.3622, 126.0550, 94.0881, 176.4853)
        better_bbox = (57.7910, 136.9830, 96.7910, 177.9830)
        page = _FakePage(
            image_rects=[worse_bbox],
            drawings=[better_bbox],
        )
        text = _text_block(
            "’avventuriero che interpreti",
            (90.62, 137.85, 260.0, 149.85),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(bboxes, [better_bbox])

    def test_dropcap_geometry_uses_first_line_not_full_paragraph_bbox(self):
        text = TextBlock(
            spans=[
                TextSpan(
                    text="’avventuriero che interpreti",
                    font="",
                    size=10.0,
                    bold=False,
                    italic=False,
                    bbox=(40.0, 100.0, 180.0, 112.0),
                ),
                TextSpan(
                    text="seconda riga molto più larga",
                    font="",
                    size=10.0,
                    bold=False,
                    italic=False,
                    bbox=(80.0, 118.0, 300.0, 130.0),
                ),
            ],
            bbox=(40.0, 100.0, 300.0, 130.0),
        )

        self.assertTrue(
            _asset_may_be_unresolved_dropcap(
                (18.0, 96.0, 38.0, 136.0),
                [text],
                [],
                600.0,
                800.0,
            )
        )

    def test_asset_dropcap_rejects_table_associated_asset(self):
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )
        table = _table((10.0, 90.0, 200.0, 150.0))

        self.assertFalse(
            _asset_may_be_unresolved_dropcap(
                (18.0, 96.0, 38.0, 136.0),
                [text],
                [table],
                600.0,
                800.0,
            )
        )

    def test_asset_dropcap_rejects_large_asset(self):
        text = _text_block(
            "’avventuriero che interpreti",
            (160.0, 100.0, 300.0, 112.0),
        )

        self.assertFalse(
            _asset_may_be_unresolved_dropcap(
                (20.0, 80.0, 150.0, 220.0),
                [text],
                [],
                600.0,
                800.0,
            )
        )

    def test_raw_image_rect_compatible_produces_dropcap_bbox(self):
        page = _FakePage(image_rects=[(18.0, 96.0, 38.0, 136.0)])
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(bboxes, [(18.0, 96.0, 38.0, 136.0)])

    def test_overlapping_raw_image_and_drawing_rects_produce_one_dropcap_bbox(self):
        page = _FakePage(
            image_rects=[(18.0, 96.0, 38.0, 136.0)],
            drawings=[(18.5, 96.5, 38.5, 136.5)],
        )
        text = _text_block(
            "’avventuriero che interpreti",
            (40.0, 100.0, 180.0, 112.0),
        )

        bboxes = _dropcap_bboxes(
            page,
            [text],
            [],
            600.0,
            800.0,
        )

        self.assertEqual(len(bboxes), 1)


def _text_block(text: str, bbox: tuple[float, float, float, float]) -> TextBlock:
    return TextBlock(
        spans=[
            TextSpan(
                text=text,
                font="",
                size=10.0,
                bold=False,
                italic=False,
                bbox=bbox,
            )
        ],
        bbox=bbox,
    )


def _table(bbox: tuple[float, float, float, float]) -> TableBlock:
    return TableBlock(
        rows=[["A", "B"], ["1", "2"]],
        bbox=bbox,
        page_num=0,
        index=0,
    )


if __name__ == "__main__":
    unittest.main()
