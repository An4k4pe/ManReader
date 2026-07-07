"""Tests for page-level layout analysis contracts."""

from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError

from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
)


class LayoutRegionTests(unittest.TestCase):
    def _region(
        self,
        *,
        region_id: str = "region-1",
        page_id: str = "page-1",
        bbox: tuple[float, float, float, float] = (0.0, 1.0, 20.0, 30.0),
        structural_kind: str = "layout.generic",
        primitive_ids: tuple[str, ...] = ("primitive-1",),
    ) -> LayoutRegion:
        return LayoutRegion(
            region_id=region_id,
            page_id=page_id,
            bbox=bbox,
            structural_kind=structural_kind,
            primitive_ids=primitive_ids,
        )

    def test_valid_construction(self) -> None:
        region = self._region()

        self.assertEqual(region.region_id, "region-1")
        self.assertEqual(region.page_id, "page-1")
        self.assertEqual(region.bbox, (0.0, 1.0, 20.0, 30.0))
        self.assertEqual(region.structural_kind, "layout.generic")
        self.assertEqual(region.primitive_ids, ("primitive-1",))

    def test_equivalent_instances_are_equal(self) -> None:
        self.assertEqual(self._region(), self._region())

    def test_dataclass_is_immutable(self) -> None:
        region = self._region()

        with self.assertRaises(FrozenInstanceError):
            region.region_id = "changed"  # type: ignore[misc]

    def test_dataclass_uses_slots(self) -> None:
        self.assertFalse(hasattr(self._region(), "__dict__"))

    def test_empty_primitive_ids_tuple_is_valid(self) -> None:
        region = self._region(primitive_ids=())

        self.assertEqual(region.primitive_ids, ())

    def test_multiple_primitive_ids_are_valid(self) -> None:
        region = self._region(primitive_ids=("primitive-1", "primitive-2"))

        self.assertEqual(region.primitive_ids, ("primitive-1", "primitive-2"))

    def test_duplicate_primitive_ids_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(primitive_ids=("primitive-1", "primitive-1"))

    def test_primitive_ids_list_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(primitive_ids=["primitive-1"])  # type: ignore[arg-type]

    def test_primitive_ids_non_string_item_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(primitive_ids=(123,))  # type: ignore[arg-type]

    def test_primitive_ids_empty_string_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(primitive_ids=("",))

    def test_empty_region_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(region_id="")

    def test_empty_page_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(page_id="")

    def test_inverted_bbox_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(bbox=(20.0, 1.0, 0.0, 30.0))

    def test_degenerate_bbox_x_axis_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(bbox=(0.0, 1.0, 0.0, 30.0))

    def test_degenerate_bbox_y_axis_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(bbox=(0.0, 1.0, 20.0, 1.0))

    def test_bbox_with_nan_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(bbox=(0.0, 1.0, math.nan, 30.0))

    def test_bbox_with_infinity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(bbox=(0.0, 1.0, math.inf, 30.0))

    def test_valid_structural_kind_is_accepted(self) -> None:
        region = self._region(structural_kind="layout.group")

        self.assertEqual(region.structural_kind, "layout.group")

    def test_structural_kind_without_namespace_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind="layout")

    def test_structural_kind_with_uppercase_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind="layout.Generic")

    def test_structural_kind_with_empty_segment_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind="layout..generic")

    def test_structural_kind_with_spaces_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind="layout generic.value")

    def test_structural_kind_with_hyphens_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind="layout.generic-value")

    def test_non_string_structural_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._region(structural_kind=123)  # type: ignore[arg-type]


class PageAnalysisTests(unittest.TestCase):
    def _region(
        self,
        *,
        region_id: str = "region-1",
        page_id: str = "page-1",
        bbox: tuple[float, float, float, float] = (0.0, 1.0, 20.0, 30.0),
        primitive_ids: tuple[str, ...] = ("primitive-1",),
    ) -> LayoutRegion:
        return LayoutRegion(
            region_id=region_id,
            page_id=page_id,
            bbox=bbox,
            structural_kind="layout.generic",
            primitive_ids=primitive_ids,
        )

    def _analysis(
        self,
        *,
        schema_version: str = PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id: str = "generation-1",
        page_id: str = "page-1",
        regions: tuple[LayoutRegion, ...] | object | None = None,
    ) -> PageAnalysis:
        actual_regions = (self._region(),) if regions is None else regions
        return PageAnalysis(
            schema_version=schema_version,
            generation_id=generation_id,
            page_id=page_id,
            regions=actual_regions,  # type: ignore[arg-type]
        )

    def test_valid_construction_with_regions(self) -> None:
        region = self._region()
        analysis = self._analysis(regions=(region,))

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.generation_id, "generation-1")
        self.assertEqual(analysis.page_id, "page-1")
        self.assertEqual(analysis.regions, (region,))

    def test_page_without_regions_is_valid(self) -> None:
        analysis = self._analysis(regions=())

        self.assertEqual(analysis.regions, ())

    def test_dataclass_is_immutable(self) -> None:
        analysis = self._analysis()

        with self.assertRaises(FrozenInstanceError):
            analysis.page_id = "changed"  # type: ignore[misc]

    def test_dataclass_uses_slots(self) -> None:
        self.assertFalse(hasattr(self._analysis(), "__dict__"))

    def test_schema_version_1_0_is_valid(self) -> None:
        analysis = self._analysis(schema_version="1.0")

        self.assertEqual(analysis.schema_version, "1.0")

    def test_different_schema_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(schema_version="2.0")

    def test_empty_generation_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(generation_id="")

    def test_empty_page_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(page_id="")

    def test_regions_list_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=[self._region()])

    def test_non_layout_region_value_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=(object(),))

    def test_region_with_different_page_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=(self._region(page_id="page-2"),))

    def test_duplicate_region_ids_are_rejected(self) -> None:
        first = self._region(region_id="region-1", bbox=(0.0, 0.0, 10.0, 10.0))
        second = self._region(region_id="region-1", bbox=(20.0, 20.0, 30.0, 30.0))

        with self.assertRaises(ValueError):
            self._analysis(regions=(first, second))

    def test_same_content_with_distinct_region_ids_is_valid(self) -> None:
        first = self._region(region_id="region-1")
        second = self._region(region_id="region-2")
        analysis = self._analysis(regions=(first, second))

        self.assertEqual(analysis.regions, (first, second))

    def test_region_order_is_preserved(self) -> None:
        first = self._region(region_id="region-1")
        second = self._region(region_id="region-2")
        third = self._region(region_id="region-3")
        analysis = self._analysis(regions=(third, first, second))

        self.assertEqual(analysis.regions, (third, first, second))


if __name__ == "__main__":
    unittest.main()
