import unittest

from extractor import _bbox_overlaps_any, _find_table_regions


class FakeTable:
    def __init__(self, bbox):
        self.bbox = bbox


class FakePage:
    def __init__(self, tables):
        self._tables = tables

    def find_tables(self):
        return self._tables


class ExtractorTablesTest(unittest.TestCase):
    def test_find_table_regions_includes_single_row_candidate_bbox(self):
        page = FakePage([FakeTable((10, 20, 100, 40))])

        regions = _find_table_regions(page)

        self.assertEqual(regions, [(10.0, 20.0, 100.0, 40.0)])

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
