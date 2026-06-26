import unittest

from extractor import (
    TableBlock,
    _bbox_contains,
    _bbox_overlaps_any,
    _find_table_regions,
    _rebuild_numbered_table_from_words,
    _table_fragments_non_empty_in_region,
)


class FakeTable:
    def __init__(self, bbox, rows=None):
        self.bbox = bbox
        self._rows = rows or [["cell"]]

    def extract(self):
        return self._rows


class FakePage:
    def __init__(self, tables, text_line_tables=None, width=200.0, height=200.0):
        self._tables = tables
        self._text_line_tables = text_line_tables or []
        self.width = width
        self.height = height

    def find_tables(self, table_settings=None):
        if table_settings == {"vertical_strategy": "text", "horizontal_strategy": "lines"}:
            return self._text_line_tables
        return self._tables


class ExtractorTablesTest(unittest.TestCase):
    def test_find_table_regions_includes_single_row_candidate_bbox(self):
        page = FakePage([FakeTable((10, 20, 100, 40))])

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(10.0, 20.0, 100.0, 40.0)])

    def test_find_table_regions_accepts_valid_text_lines_region(self):
        default = FakeTable((10, 40, 100, 60))
        text_lines = FakeTable(
            (10, 40, 100, 140),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(8.0, 38.0, 102.0, 142.0)])

    def test_find_table_regions_rejects_too_tall_text_lines_region(self):
        default = FakeTable((10, 40, 100, 60))
        text_lines = FakeTable(
            (10, 10, 100, 190),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(10.0, 40.0, 100.0, 60.0)])

    def test_find_table_regions_deduplicates_contained_regions_in_favor_of_larger_one(self):
        default = FakeTable((20, 60, 80, 80))
        text_lines = FakeTable(
            (10, 40, 100, 140),
            rows=[
                ["D6", "Luogo", "Ritrovamento"],
                ["1", "Casa", "Dettaglio"],
                ["2", "Mulino", "Dettaglio"],
            ],
        )
        page = FakePage([default], [text_lines], width=120.0, height=200.0)

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(8.0, 38.0, 102.0, 142.0)])

    def test_vector_bbox_strongly_overlapping_table_region_is_excluded(self):
        vector_bbox = (10.0, 20.0, 100.0, 40.0)
        table_regions = [(12.0, 20.0, 98.0, 40.0)]

        overlaps = _bbox_overlaps_any(vector_bbox, table_regions, threshold=0.8)

        self.assertTrue(overlaps)

    def test_vector_bbox_not_overlapping_table_region_is_kept(self):
        vector_bbox = (10.0, 20.0, 100.0, 40.0)
        table_regions = [(120.0, 20.0, 200.0, 40.0)]

        overlaps = _bbox_overlaps_any(vector_bbox, table_regions, threshold=0.8)

        self.assertFalse(overlaps)

    def test_rebuild_numbered_table_from_words_splits_fused_d6_row_by_coordinates(self):
        words = [
            (10, 10, 20, 20, "D6"),
            (30, 10, 50, 20, "Luogo"),
            (90, 10, 140, 20, "Ritrovamento"),
            (180, 10, 220, 20, "Dettagli"),
            (222, 10, 228, 20, "e"),
            (230, 10, 270, 20, "atmosfera"),
        ]
        for row_num, y in enumerate([40, 70, 100], start=1):
            words.extend(
                [
                    (10, y, 15, y + 10, str(row_num)),
                    (30, y, 38, y + 10, "Il"),
                    (40, y, 65, y + 10, f"luogo{row_num}"),
                    (90, y, 105, y + 10, "Il"),
                    (107, y, 145, y + 10, f"ritrovamento{row_num}"),
                    (180, y, 220, y + 10, f"dettaglio{row_num}"),
                ]
            )

        rows = _rebuild_numbered_table_from_words(words, (0.0, 0.0, 300.0, 130.0))

        self.assertIsNotNone(rows)
        self.assertEqual(rows[0], ["D6", "Luogo", "Ritrovamento", "Dettagli e atmosfera"])
        self.assertEqual(rows[2], ["2", "Il luogo2", "Il ritrovamento2", "dettaglio2"])

    def test_rebuild_numbered_table_from_words_rejects_missing_essential_cells(self):
        words = [
            (10, 10, 20, 20, "D6"),
            (30, 10, 50, 20, "Luogo"),
            (90, 10, 140, 20, "Ritrovamento"),
            (180, 10, 220, 20, "Dettagli"),
            (10, 40, 15, 50, "1"),
            (30, 40, 60, 50, "Casa"),
            (180, 40, 220, 50, "dettaglio"),
            (10, 70, 15, 80, "2"),
            (30, 70, 60, 80, "Mulino"),
            (90, 70, 130, 80, "registro"),
            (180, 70, 220, 80, "dettaglio"),
            (10, 100, 15, 110, "3"),
            (30, 100, 60, 110, "Pozzo"),
            (90, 100, 130, 110, "secchio"),
            (180, 100, 220, 110, "dettaglio"),
        ]

        rows = _rebuild_numbered_table_from_words(words, (0.0, 0.0, 300.0, 130.0))

        self.assertIsNone(rows)

    def test_fallback_region_can_identify_contained_pdfplumber_fragments(self):
        fallback_region = (8.0, 8.0, 220.0, 120.0)
        fragment = TableBlock(
            rows=[["1", "Casa"], ["2", "Mulino"]],
            bbox=(10.0, 20.0, 100.0, 60.0),
            page_num=0,
            index=0,
        )

        self.assertTrue(_bbox_contains(fallback_region, fragment.bbox))
        self.assertEqual(_table_fragments_non_empty_in_region([fragment], fallback_region), 4)


if __name__ == "__main__":
    unittest.main()
