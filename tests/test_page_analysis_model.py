"""Tests for page-level layout analysis contracts."""

from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError

from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    LayoutRegion,
    PageAnalysis,
    RegionRelation,
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


class RegionRelationTests(unittest.TestCase):
    def _relation(
        self,
        *,
        relation_id: str = "relation-1",
        relation_kind: str = "layout.contains",
        source_region_id: str = "region-1",
        target_region_id: str = "region-2",
    ) -> RegionRelation:
        return RegionRelation(
            relation_id=relation_id,
            relation_kind=relation_kind,
            source_region_id=source_region_id,
            target_region_id=target_region_id,
        )

    def test_valid_contains_construction(self) -> None:
        relation = self._relation(relation_kind="layout.contains")

        self.assertEqual(relation.relation_kind, "layout.contains")

    def test_valid_precedes_construction(self) -> None:
        relation = self._relation(relation_kind="layout.precedes")

        self.assertEqual(relation.relation_kind, "layout.precedes")

    def test_equivalent_instances_are_equal(self) -> None:
        self.assertEqual(self._relation(), self._relation())

    def test_dataclass_is_immutable(self) -> None:
        relation = self._relation()

        with self.assertRaises(FrozenInstanceError):
            relation.relation_id = "changed"  # type: ignore[misc]

    def test_dataclass_uses_slots(self) -> None:
        self.assertFalse(hasattr(self._relation(), "__dict__"))

    def test_empty_relation_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(relation_id="")

    def test_unsupported_relation_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(relation_kind="layout.overlaps")

    def test_non_string_relation_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(relation_kind=123)  # type: ignore[arg-type]

    def test_empty_source_region_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(source_region_id="")

    def test_empty_target_region_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(target_region_id="")

    def test_same_source_and_target_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._relation(source_region_id="region-1", target_region_id="region-1")


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

    def _relation(
        self,
        *,
        relation_id: str = "relation-1",
        relation_kind: str = "layout.contains",
        source_region_id: str = "region-1",
        target_region_id: str = "region-2",
    ) -> RegionRelation:
        return RegionRelation(
            relation_id=relation_id,
            relation_kind=relation_kind,
            source_region_id=source_region_id,
            target_region_id=target_region_id,
        )

    def _regions(self) -> tuple[LayoutRegion, ...]:
        return (
            self._region(region_id="region-1", bbox=(0.0, 0.0, 10.0, 10.0)),
            self._region(region_id="region-2", bbox=(20.0, 0.0, 30.0, 10.0)),
            self._region(region_id="region-3", bbox=(40.0, 0.0, 50.0, 10.0)),
        )

    def _analysis(
        self,
        *,
        schema_version: str = PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id: str = "generation-1",
        page_id: str = "page-1",
        regions: tuple[LayoutRegion, ...] | object | None = None,
        relations: tuple[RegionRelation, ...] | object = (),
    ) -> PageAnalysis:
        actual_regions = (self._region(),) if regions is None else regions
        return PageAnalysis(
            schema_version=schema_version,
            generation_id=generation_id,
            page_id=page_id,
            regions=actual_regions,  # type: ignore[arg-type]
            relations=relations,  # type: ignore[arg-type]
        )

    def _long_regions(self, count: int) -> tuple[LayoutRegion, ...]:
        return tuple(self._region(region_id=f"region-{index:04d}") for index in range(count))

    def _long_precedes_relations(
        self,
        count: int,
        *,
        close_cycle: bool = False,
    ) -> tuple[RegionRelation, ...]:
        relations = [
            self._relation(
                relation_id=f"relation-{index:04d}",
                relation_kind="layout.precedes",
                source_region_id=f"region-{index:04d}",
                target_region_id=f"region-{index + 1:04d}",
            )
            for index in range(count - 1)
        ]
        if close_cycle:
            relations.append(
                self._relation(
                    relation_id=f"relation-{count:04d}",
                    relation_kind="layout.precedes",
                    source_region_id=f"region-{count - 1:04d}",
                    target_region_id="region-0000",
                )
            )
        return tuple(relations)

    def test_valid_construction_with_regions(self) -> None:
        region = self._region()
        analysis = self._analysis(regions=(region,))

        self.assertEqual(analysis.schema_version, PAGE_ANALYSIS_SCHEMA_VERSION)
        self.assertEqual(analysis.generation_id, "generation-1")
        self.assertEqual(analysis.page_id, "page-1")
        self.assertEqual(analysis.regions, (region,))
        self.assertEqual(analysis.relations, ())

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

    def test_page_with_valid_relations(self) -> None:
        relation = self._relation()
        analysis = self._analysis(regions=self._regions(), relations=(relation,))

        self.assertEqual(analysis.relations, (relation,))

    def test_empty_relations_tuple_is_valid(self) -> None:
        analysis = self._analysis(regions=self._regions(), relations=())

        self.assertEqual(analysis.relations, ())

    def test_relations_list_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=[self._relation()])

    def test_non_region_relation_value_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(object(),))

    def test_dangling_source_is_rejected(self) -> None:
        relation = self._relation(source_region_id="missing")

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(relation,))

    def test_dangling_target_is_rejected(self) -> None:
        relation = self._relation(target_region_id="missing")

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(relation,))

    def test_duplicate_relation_ids_are_rejected(self) -> None:
        first = self._relation(relation_id="relation-1")
        second = self._relation(
            relation_id="relation-1",
            source_region_id="region-2",
            target_region_id="region-3",
        )

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second))

    def test_duplicate_logical_edges_are_rejected(self) -> None:
        first = self._relation(relation_id="relation-1")
        second = self._relation(relation_id="relation-2")

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second))

    def test_same_endpoints_with_different_relation_kinds_are_valid(self) -> None:
        contains = self._relation(relation_id="relation-1", relation_kind="layout.contains")
        precedes = self._relation(relation_id="relation-2", relation_kind="layout.precedes")
        analysis = self._analysis(regions=self._regions(), relations=(contains, precedes))

        self.assertEqual(analysis.relations, (contains, precedes))

    def test_relation_order_is_preserved(self) -> None:
        first = self._relation(relation_id="relation-1")
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.precedes",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        third = self._relation(
            relation_id="relation-3",
            source_region_id="region-1",
            target_region_id="region-3",
        )
        analysis = self._analysis(regions=self._regions(), relations=(third, first, second))

        self.assertEqual(analysis.relations, (third, first, second))

    def test_multiple_parentage_is_valid(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            source_region_id="region-1",
            target_region_id="region-3",
        )
        second = self._relation(
            relation_id="relation-2",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        analysis = self._analysis(regions=self._regions(), relations=(first, second))

        self.assertEqual(analysis.relations, (first, second))

    def test_page_without_regions_and_without_relations_is_valid(self) -> None:
        analysis = self._analysis(regions=(), relations=())

        self.assertEqual(analysis.regions, ())
        self.assertEqual(analysis.relations, ())

    def test_page_without_regions_but_with_relation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._analysis(regions=(), relations=(self._relation(),))

    def test_contains_acyclic_chain_is_valid(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.contains",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.contains",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        analysis = self._analysis(regions=self._regions(), relations=(first, second))

        self.assertEqual(analysis.relations, (first, second))

    def test_contains_direct_cycle_is_rejected(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.contains",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.contains",
            source_region_id="region-2",
            target_region_id="region-1",
        )

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second))

    def test_contains_three_node_cycle_is_rejected(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.contains",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.contains",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        third = self._relation(
            relation_id="relation-3",
            relation_kind="layout.contains",
            source_region_id="region-3",
            target_region_id="region-1",
        )

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second, third))

    def test_precedes_acyclic_chain_is_valid(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.precedes",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.precedes",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        analysis = self._analysis(regions=self._regions(), relations=(first, second))

        self.assertEqual(analysis.relations, (first, second))

    def test_precedes_direct_cycle_is_rejected(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.precedes",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.precedes",
            source_region_id="region-2",
            target_region_id="region-1",
        )

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second))

    def test_precedes_three_node_cycle_is_rejected(self) -> None:
        first = self._relation(
            relation_id="relation-1",
            relation_kind="layout.precedes",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        second = self._relation(
            relation_id="relation-2",
            relation_kind="layout.precedes",
            source_region_id="region-2",
            target_region_id="region-3",
        )
        third = self._relation(
            relation_id="relation-3",
            relation_kind="layout.precedes",
            source_region_id="region-3",
            target_region_id="region-1",
        )

        with self.assertRaises(ValueError):
            self._analysis(regions=self._regions(), relations=(first, second, third))

    def test_long_precedes_acyclic_chain_does_not_hit_recursion_limit(self) -> None:
        region_count = 1300
        try:
            analysis = self._analysis(
                regions=self._long_regions(region_count),
                relations=self._long_precedes_relations(region_count),
            )
        except RecursionError as exc:
            self.fail(f"PageAnalysis raised RecursionError: {exc}")

        self.assertEqual(len(analysis.regions), region_count)
        self.assertEqual(len(analysis.relations), region_count - 1)

    def test_long_precedes_cycle_is_rejected(self) -> None:
        region_count = 1300

        with self.assertRaises(ValueError):
            self._analysis(
                regions=self._long_regions(region_count),
                relations=self._long_precedes_relations(region_count, close_cycle=True),
            )

    def test_mixed_relation_kinds_do_not_create_false_cycle(self) -> None:
        contains = self._relation(
            relation_id="relation-1",
            relation_kind="layout.contains",
            source_region_id="region-1",
            target_region_id="region-2",
        )
        precedes = self._relation(
            relation_id="relation-2",
            relation_kind="layout.precedes",
            source_region_id="region-2",
            target_region_id="region-1",
        )
        analysis = self._analysis(regions=self._regions(), relations=(contains, precedes))

        self.assertEqual(analysis.relations, (contains, precedes))


if __name__ == "__main__":
    unittest.main()
