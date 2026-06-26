import unittest

from extractor import _bbox_overlaps_any, _find_table_regions


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


if __name__ == "__main__":
    unittest.main()
