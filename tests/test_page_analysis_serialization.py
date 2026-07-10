"""Tests for PageAnalysis JSON-safe serialization."""

from __future__ import annotations

import unittest
from typing import cast

from page_analysis_model import (
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
    RegionRelation,
)
from page_analysis_serialization import page_analysis_from_dict, page_analysis_to_dict


class PageAnalysisSerializationTests(unittest.TestCase):
    def _region(
        self,
        region_id: str,
        *,
        bbox: tuple[float, float, float, float] = (0.0, 0.0, 10.0, 10.0),
        primitive_ids: tuple[str, ...] = (),
        page_id: str = "page-1",
        structural_kind: str = "layout.generic",
    ) -> LayoutRegion:
        return LayoutRegion(
            region_id=region_id,
            page_id=page_id,
            bbox=bbox,
            structural_kind=structural_kind,
            primitive_ids=primitive_ids,
        )

    def _candidate(
        self,
        candidate_id: str,
        *,
        bbox: tuple[float, float, float, float] = (0.0, 0.0, 10.0, 10.0),
        primitive_ids: tuple[str, ...] = (),
        page_id: str = "page-1",
        proposed_structural_kind: str = "layout.side_band",
    ) -> RegionCandidate:
        return RegionCandidate(
            candidate_id=candidate_id,
            page_id=page_id,
            bbox=bbox,
            proposed_structural_kind=proposed_structural_kind,
            primitive_ids=primitive_ids,
        )

    def _relation(
        self,
        relation_id: str,
        *,
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

    def _provenance(self) -> PageAnalysisProvenance:
        return PageAnalysisProvenance(
            source_id="source-1",
            source_capture_id="capture-1",
            source_page_id="page-1",
            source_primitive_schema_version="1.0",
            producer_name="region-graph",
            producer_version="0.1",
            configuration_id="config-default-v1",
        )

    def _provenance_data(self) -> dict[str, object]:
        return {
            "source_id": "source-1",
            "source_capture_id": "capture-1",
            "source_page_id": "page-1",
            "source_primitive_schema_version": "1.0",
            "producer_name": "region-graph",
            "producer_version": "0.1",
            "configuration_id": "config-default-v1",
        }

    def _analysis(self) -> PageAnalysis:
        return PageAnalysis(
            schema_version="1.2",
            generation_id="generation-1",
            page_id="page-1",
            provenance=self._provenance(),
            regions=(
                self._region(
                    "region-1",
                    bbox=(0.0, 0.0, 100.0, 200.0),
                    primitive_ids=("primitive-1", "primitive-2"),
                ),
                self._region(
                    "region-2",
                    bbox=(10.0, 10.0, 20.0, 20.0),
                    primitive_ids=("primitive-3",),
                    structural_kind="layout.group",
                ),
            ),
            relations=(
                self._relation("relation-1"),
                self._relation(
                    "relation-2",
                    relation_kind="layout.precedes",
                    source_region_id="region-1",
                    target_region_id="region-2",
                ),
            ),
            candidates=(
                self._candidate(
                    "candidate-1",
                    bbox=(5.0, 5.0, 15.0, 25.0),
                    primitive_ids=("primitive-1", "primitive-3"),
                ),
                self._candidate(
                    "candidate-2",
                    bbox=(20.0, 5.0, 30.0, 25.0),
                    primitive_ids=(),
                    proposed_structural_kind="layout.edge_band",
                ),
            ),
        )

    def _empty_analysis(self) -> PageAnalysis:
        return PageAnalysis(
            schema_version="1.2",
            generation_id="generation-1",
            page_id="page-1",
            provenance=self._provenance(),
            regions=(),
            relations=(),
            candidates=(),
        )

    def _analysis_data(self) -> dict[str, object]:
        return {
            "schema_version": "1.2",
            "generation_id": "generation-1",
            "page_id": "page-1",
            "provenance": self._provenance_data(),
            "regions": [
                {
                    "region_id": "region-1",
                    "page_id": "page-1",
                    "bbox": [0.0, 0.0, 100.0, 200.0],
                    "structural_kind": "layout.generic",
                    "primitive_ids": ["primitive-1", "primitive-2"],
                },
                {
                    "region_id": "region-2",
                    "page_id": "page-1",
                    "bbox": [10.0, 10.0, 20.0, 20.0],
                    "structural_kind": "layout.group",
                    "primitive_ids": ["primitive-3"],
                },
            ],
            "relations": [
                {
                    "relation_id": "relation-1",
                    "relation_kind": "layout.contains",
                    "source_region_id": "region-1",
                    "target_region_id": "region-2",
                },
                {
                    "relation_id": "relation-2",
                    "relation_kind": "layout.precedes",
                    "source_region_id": "region-1",
                    "target_region_id": "region-2",
                },
            ],
            "candidates": [
                {
                    "candidate_id": "candidate-1",
                    "page_id": "page-1",
                    "bbox": [5.0, 5.0, 15.0, 25.0],
                    "proposed_structural_kind": "layout.side_band",
                    "primitive_ids": ["primitive-1", "primitive-3"],
                },
                {
                    "candidate_id": "candidate-2",
                    "page_id": "page-1",
                    "bbox": [20.0, 5.0, 30.0, 25.0],
                    "proposed_structural_kind": "layout.edge_band",
                    "primitive_ids": [],
                },
            ],
        }

    def _empty_data(self) -> dict[str, object]:
        return {
            "schema_version": "1.2",
            "generation_id": "generation-1",
            "page_id": "page-1",
            "provenance": self._provenance_data(),
            "regions": [],
            "relations": [],
            "candidates": [],
        }

    def test_deserialization_rejects_provenance_page_id_mismatch(self) -> None:
        data = self._analysis_data()
        self._provenance_dict(data)["source_page_id"] = "page-2"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def _provenance_dict(self, data: dict[str, object]) -> dict[str, object]:
        return cast(dict[str, object], data["provenance"])

    def _regions_data(self, data: dict[str, object]) -> list[object]:
        return cast(list[object], data["regions"])

    def _relations_data(self, data: dict[str, object]) -> list[object]:
        return cast(list[object], data["relations"])

    def _candidates_data(self, data: dict[str, object]) -> list[object]:
        return cast(list[object], data["candidates"])

    def _region_data(self, data: dict[str, object], index: int = 0) -> dict[str, object]:
        return cast(dict[str, object], self._regions_data(data)[index])

    def _relation_data(self, data: dict[str, object], index: int = 0) -> dict[str, object]:
        return cast(dict[str, object], self._relations_data(data)[index])

    def _candidate_data(self, data: dict[str, object], index: int = 0) -> dict[str, object]:
        return cast(dict[str, object], self._candidates_data(data)[index])

    def test_serializes_valid_page_analysis_with_regions_and_relations(self) -> None:
        self.assertEqual(page_analysis_to_dict(self._analysis()), self._analysis_data())

    def test_serializes_empty_page_with_empty_lists(self) -> None:
        self.assertEqual(page_analysis_to_dict(self._empty_analysis()), self._empty_data())

    def test_serializes_provenance(self) -> None:
        self.assertEqual(
            page_analysis_to_dict(self._analysis())["provenance"], self._provenance_data()
        )

    def test_serialized_provenance_dict_is_independent_from_model(self) -> None:
        analysis = self._analysis()
        data = page_analysis_to_dict(analysis)
        self._provenance_dict(data)["source_id"] = "changed"

        self.assertEqual(analysis.provenance.source_id, "source-1")

    def test_serialization_always_includes_provenance(self) -> None:
        self.assertIn("provenance", page_analysis_to_dict(self._empty_analysis()))

    def test_serialization_always_includes_candidates(self) -> None:
        self.assertIn("candidates", page_analysis_to_dict(self._empty_analysis()))

    def test_serializes_candidates(self) -> None:
        self.assertEqual(
            page_analysis_to_dict(self._analysis())["candidates"],
            self._analysis_data()["candidates"],
        )

    def test_serializes_empty_candidate_list(self) -> None:
        self.assertEqual(page_analysis_to_dict(self._empty_analysis())["candidates"], [])

    def test_serializes_bbox_as_list(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertIsInstance(self._region_data(data)["bbox"], list)

    def test_serializes_primitive_ids_as_list(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(self._region_data(data)["primitive_ids"], ["primitive-1", "primitive-2"])

    def test_serializes_candidate_bbox_as_list(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertIsInstance(self._candidate_data(data)["bbox"], list)

    def test_serializes_candidate_primitive_ids_as_list(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(
            self._candidate_data(data)["primitive_ids"],
            ["primitive-1", "primitive-3"],
        )

    def test_serialization_preserves_region_order(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(
            [cast(dict[str, object], item)["region_id"] for item in self._regions_data(data)],
            ["region-1", "region-2"],
        )

    def test_serialization_preserves_relation_order(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(
            [cast(dict[str, object], item)["relation_id"] for item in self._relations_data(data)],
            ["relation-1", "relation-2"],
        )

    def test_serialization_preserves_candidate_order(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(
            [cast(dict[str, object], item)["candidate_id"] for item in self._candidates_data(data)],
            ["candidate-1", "candidate-2"],
        )

    def test_serialization_preserves_primitive_id_order(self) -> None:
        data = page_analysis_to_dict(self._analysis())

        self.assertEqual(self._region_data(data)["primitive_ids"], ["primitive-1", "primitive-2"])

    def test_serialization_rejects_wrong_analysis_type(self) -> None:
        with self.assertRaises(ValueError):
            page_analysis_to_dict(object())  # type: ignore[arg-type]

    def test_serialization_does_not_modify_input(self) -> None:
        analysis = self._analysis()
        expected = self._analysis()

        page_analysis_to_dict(analysis)

        self.assertEqual(analysis, expected)

    def test_serialized_dict_is_independent_from_model(self) -> None:
        analysis = self._analysis()
        data = page_analysis_to_dict(analysis)
        cast(list[object], self._region_data(data)["primitive_ids"]).append("changed")
        cast(list[object], self._region_data(data)["bbox"])[0] = 99.0
        cast(list[object], self._candidate_data(data)["primitive_ids"]).append("changed")
        cast(list[object], self._candidate_data(data)["bbox"])[0] = 99.0

        self.assertEqual(analysis.regions[0].primitive_ids, ("primitive-1", "primitive-2"))
        self.assertEqual(analysis.regions[0].bbox, (0.0, 0.0, 100.0, 200.0))
        self.assertEqual(analysis.candidates[0].primitive_ids, ("primitive-1", "primitive-3"))
        self.assertEqual(analysis.candidates[0].bbox, (5.0, 5.0, 15.0, 25.0))

    def test_deserializes_complete_dictionary(self) -> None:
        self.assertEqual(page_analysis_from_dict(self._analysis_data()), self._analysis())

    def test_deserializes_empty_page(self) -> None:
        self.assertEqual(page_analysis_from_dict(self._empty_data()), self._empty_analysis())

    def test_model_round_trip(self) -> None:
        analysis = self._analysis()

        self.assertEqual(page_analysis_from_dict(page_analysis_to_dict(analysis)), analysis)

    def test_model_round_trip_preserves_provenance(self) -> None:
        analysis = self._analysis()

        self.assertEqual(
            page_analysis_from_dict(page_analysis_to_dict(analysis)).provenance,
            analysis.provenance,
        )

    def test_model_round_trip_preserves_candidates(self) -> None:
        analysis = self._analysis()

        self.assertEqual(
            page_analysis_from_dict(page_analysis_to_dict(analysis)).candidates,
            analysis.candidates,
        )

    def test_data_round_trip_preserves_provenance(self) -> None:
        data = self._analysis_data()

        self.assertEqual(
            page_analysis_to_dict(page_analysis_from_dict(data))["provenance"], data["provenance"]
        )

    def test_deserializes_complete_provenance(self) -> None:
        self.assertEqual(
            page_analysis_from_dict(self._analysis_data()).provenance, self._provenance()
        )

    def test_deserializes_complete_candidates(self) -> None:
        self.assertEqual(
            page_analysis_from_dict(self._analysis_data()).candidates,
            self._analysis().candidates,
        )

    def test_data_round_trip_normalizes_bbox_numbers_to_float(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = [0, 1.5, 20, 30.0]
        expected = self._analysis_data()
        self._region_data(expected)["bbox"] = [0.0, 1.5, 20.0, 30.0]

        self.assertEqual(page_analysis_to_dict(page_analysis_from_dict(data)), expected)

    def test_deserialization_preserves_multiple_region_and_relation_order(self) -> None:
        analysis = page_analysis_from_dict(self._analysis_data())

        self.assertEqual(
            tuple(region.region_id for region in analysis.regions), ("region-1", "region-2")
        )
        self.assertEqual(
            tuple(relation.relation_id for relation in analysis.relations),
            ("relation-1", "relation-2"),
        )
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in analysis.candidates),
            ("candidate-1", "candidate-2"),
        )

    def test_deserializes_region_without_primitives(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["primitive_ids"] = []

        self.assertEqual(page_analysis_from_dict(data).regions[0].primitive_ids, ())

    def test_deserializes_page_without_relations(self) -> None:
        data = self._analysis_data()
        data["relations"] = []

        self.assertEqual(page_analysis_from_dict(data).relations, ())

    def test_deserialization_rejects_non_dict_root(self) -> None:
        with self.assertRaises(ValueError):
            page_analysis_from_dict([])

    def test_deserialization_rejects_missing_root_key(self) -> None:
        data = self._analysis_data()
        del data["regions"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_extra_root_key(self) -> None:
        data = self._analysis_data()
        data["extra"] = None

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_string_root_key(self) -> None:
        data = cast(dict[object, object], dict(self._analysis_data()))
        data[1] = "extra"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_list_regions(self) -> None:
        data = self._analysis_data()
        data["regions"] = "not-list"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_list_relations(self) -> None:
        data = self._analysis_data()
        data["relations"] = "not-list"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_candidates_root_key(self) -> None:
        data = self._analysis_data()
        del data["candidates"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_list_candidates(self) -> None:
        data = self._analysis_data()
        data["candidates"] = "not-list"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_wrong_root_string_field_type(self) -> None:
        data = self._analysis_data()
        data["generation_id"] = 123

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_accepts_schema_1_2(self) -> None:
        data = self._analysis_data()
        data["schema_version"] = "1.2"

        self.assertEqual(page_analysis_from_dict(data).schema_version, "1.2")

    def test_deserialization_rejects_schema_1_1_via_model(self) -> None:
        data = self._analysis_data()
        data["schema_version"] = "1.1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_schema_1_0_via_model(self) -> None:
        data = self._analysis_data()
        data["schema_version"] = "1.0"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_unsupported_schema_via_model(self) -> None:
        data = self._analysis_data()
        data["schema_version"] = "2.0"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_provenance(self) -> None:
        data = self._analysis_data()
        del data["provenance"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_dict_provenance(self) -> None:
        data = self._analysis_data()
        data["provenance"] = []

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_provenance_key(self) -> None:
        data = self._analysis_data()
        del self._provenance_dict(data)["source_id"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_extra_provenance_key(self) -> None:
        data = self._analysis_data()
        self._provenance_dict(data)["extra"] = None

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_string_provenance_key(self) -> None:
        data = self._analysis_data()
        data["provenance"] = cast(dict[object, object], dict(self._provenance_data()))
        cast(dict[object, object], data["provenance"])[1] = "extra"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_string_provenance_values(self) -> None:
        field_names = tuple(self._provenance_data())
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                data = self._analysis_data()
                self._provenance_dict(data)[field_name] = 123

                with self.assertRaises(ValueError):
                    page_analysis_from_dict(data)

    def test_deserialization_rejects_empty_provenance_value_via_model(self) -> None:
        data = self._analysis_data()
        self._provenance_dict(data)["producer_name"] = ""

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_dict_region_item(self) -> None:
        data = self._analysis_data()
        self._regions_data(data)[0] = []

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_region_key(self) -> None:
        data = self._analysis_data()
        del self._region_data(data)["bbox"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_extra_region_key(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["extra"] = None

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_list_bbox(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = "0,0,1,1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_wrong_bbox_length(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = [0.0, 0.0, 1.0]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_string_bbox_coordinate(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = [0.0, "1.0", 2.0, 3.0]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_boolean_bbox_coordinate(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = [0.0, True, 2.0, 3.0]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_list_primitive_ids(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["primitive_ids"] = "primitive-1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_string_primitive_id(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["primitive_ids"] = ["primitive-1", 2]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_invalid_structural_kind(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["structural_kind"] = "layout"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_degenerate_bbox(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["bbox"] = [0.0, 0.0, 0.0, 1.0]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_duplicate_region_id(self) -> None:
        data = self._analysis_data()
        self._region_data(data, 1)["region_id"] = "region-1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_incoherent_region_page_id(self) -> None:
        data = self._analysis_data()
        self._region_data(data)["page_id"] = "page-2"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_dict_relation_item(self) -> None:
        data = self._analysis_data()
        self._relations_data(data)[0] = []

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_relation_key(self) -> None:
        data = self._analysis_data()
        del self._relation_data(data)["relation_kind"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_extra_relation_key(self) -> None:
        data = self._analysis_data()
        self._relation_data(data)["extra"] = None

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_string_relation_field(self) -> None:
        data = self._analysis_data()
        self._relation_data(data)["relation_id"] = 123

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_unsupported_relation_kind(self) -> None:
        data = self._analysis_data()
        self._relation_data(data)["relation_kind"] = "layout.overlaps"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_self_edge(self) -> None:
        data = self._analysis_data()
        self._relation_data(data)["target_region_id"] = "region-1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_dangling_endpoint(self) -> None:
        data = self._analysis_data()
        self._relation_data(data)["target_region_id"] = "missing-region"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_duplicate_relation_id(self) -> None:
        data = self._analysis_data()
        self._relation_data(data, 1)["relation_id"] = "relation-1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_duplicate_logical_edge(self) -> None:
        data = self._analysis_data()
        self._relation_data(data, 1)["relation_kind"] = "layout.contains"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_cycle(self) -> None:
        data = self._analysis_data()
        self._relations_data(data).append(
            {
                "relation_id": "relation-3",
                "relation_kind": "layout.contains",
                "source_region_id": "region-2",
                "target_region_id": "region-1",
            }
        )

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_non_dict_candidate_item(self) -> None:
        data = self._analysis_data()
        self._candidates_data(data)[0] = []

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_missing_candidate_key(self) -> None:
        data = self._analysis_data()
        del self._candidate_data(data)["bbox"]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_extra_candidate_key(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data)["extra"] = None

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_invalid_candidate_bbox(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data)["bbox"] = [0.0, 0.0, 0.0, 1.0]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_invalid_candidate_primitive_ids(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data)["primitive_ids"] = ["primitive-1", 2]

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_invalid_candidate_kind(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data)["proposed_structural_kind"] = "layout.side-band"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_incoherent_candidate_page_id(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data)["page_id"] = "page-2"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)

    def test_deserialization_rejects_duplicate_candidate_id(self) -> None:
        data = self._analysis_data()
        self._candidate_data(data, 1)["candidate_id"] = "candidate-1"

        with self.assertRaises(ValueError):
            page_analysis_from_dict(data)


if __name__ == "__main__":
    unittest.main()
