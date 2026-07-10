"""Tests for PageAnalysis JSON file store."""

from __future__ import annotations

import json
import tempfile
import unittest
from json import JSONDecodeError
from pathlib import Path
from typing import cast

from page_analysis_model import (
    LayoutRegion,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
    RegionRelation,
)
from page_analysis_serialization import page_analysis_to_dict
from page_analysis_store import load_page_analysis, save_page_analysis


class PageAnalysisStoreTests(unittest.TestCase):
    def _provenance(self) -> PageAnalysisProvenance:
        return PageAnalysisProvenance(
            source_id="source-1",
            source_capture_id="capture-1",
            source_page_id="page-1",
            source_primitive_schema_version="1.0",
            producer_name="produttore-è",
            producer_version="0.1",
            configuration_id="configurazione-à",
        )

    def _regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion(
                region_id="region-1",
                page_id="page-1",
                bbox=(0.0, 0.0, 10.0, 10.0),
                structural_kind="layout.generic",
                primitive_ids=("primitive-1", "primitive-2"),
            ),
            LayoutRegion(
                region_id="region-2",
                page_id="page-1",
                bbox=(20.0, 0.0, 30.0, 10.0),
                structural_kind="layout.group",
                primitive_ids=("primitive-3",),
            ),
        )

    def _candidates(self) -> tuple[RegionCandidate, ...]:
        return (
            RegionCandidate(
                candidate_id="candidate-1",
                page_id="page-1",
                bbox=(5.0, 5.0, 15.0, 15.0),
                proposed_structural_kind="layout.side_band",
                primitive_ids=("primitive-1", "primitive-3"),
            ),
            RegionCandidate(
                candidate_id="candidate-2",
                page_id="page-1",
                bbox=(20.0, 5.0, 30.0, 15.0),
                proposed_structural_kind="layout.edge_band",
                primitive_ids=(),
            ),
        )

    def _relations(self) -> tuple[RegionRelation, ...]:
        return (
            RegionRelation(
                relation_id="relation-1",
                relation_kind="layout.contains",
                source_region_id="region-1",
                target_region_id="region-2",
            ),
        )

    def _analysis(self) -> PageAnalysis:
        return PageAnalysis(
            schema_version="1.2",
            generation_id="generation-1",
            page_id="page-1",
            provenance=self._provenance(),
            regions=self._regions(),
            relations=self._relations(),
            candidates=self._candidates(),
        )

    def _path(self, directory: str) -> Path:
        return Path(directory) / "page-analysis.json"

    def _save(self, directory: str, analysis: PageAnalysis | None = None) -> Path:
        path = self._path(directory)
        save_page_analysis(path, self._analysis() if analysis is None else analysis)
        return path

    def test_save_creates_file_at_requested_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertTrue(path.is_file())

    def test_saved_file_is_utf8_json_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            content = path.read_text(encoding="utf-8")

            self.assertEqual(json.loads(content), page_analysis_to_dict(self._analysis()))

    def test_saved_json_keys_and_values_match_serializer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                page_analysis_to_dict(self._analysis()),
            )

    def test_saved_file_has_exactly_one_final_newline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            content = path.read_text(encoding="utf-8")

            self.assertTrue(content.endswith("\n"))
            self.assertFalse(content.endswith("\n\n"))

    def test_saved_output_is_indented(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            content = path.read_text(encoding="utf-8")

            self.assertIn('\n  "generation_id"', content)
            self.assertIn('\n    "configuration_id"', content)

    def test_saved_output_matches_deterministic_format(self) -> None:
        analysis = self._analysis()
        expected_text = (
            json.dumps(
                page_analysis_to_dict(analysis),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory, analysis)

            self.assertEqual(path.read_text(encoding="utf-8"), expected_text)

    def test_saved_output_uses_sorted_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            content = path.read_text(encoding="utf-8")

            self.assertLess(content.index('\n  "candidates"'), content.index('\n  "generation_id"'))
            self.assertLess(content.index('\n  "generation_id"'), content.index('\n  "page_id"'))
            self.assertLess(content.index('\n  "page_id"'), content.index('\n  "provenance"'))
            self.assertLess(content.index('"configuration_id"'), content.index('"producer_name"'))

    def test_saved_unicode_is_not_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            content = path.read_text(encoding="utf-8")

            self.assertIn("configurazione-à", content)
            self.assertIn("produttore-è", content)
            self.assertNotIn("\\u00e0", content)
            self.assertNotIn("\\u00e8", content)

    def test_save_overwrites_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._path(directory)
            path.write_text("old\n", encoding="utf-8")

            save_page_analysis(path, self._analysis())

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                page_analysis_to_dict(self._analysis()),
            )

    def test_two_saves_of_same_model_produce_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "first.json"
            second_path = Path(directory) / "second.json"
            analysis = self._analysis()

            save_page_analysis(first_path, analysis)
            save_page_analysis(second_path, analysis)

            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_save_rejects_wrong_path_type(self) -> None:
        with self.assertRaises(ValueError):
            save_page_analysis("page-analysis.json", self._analysis())  # type: ignore[arg-type]

    def test_save_rejects_wrong_analysis_type_via_serializer(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(ValueError, "PageAnalysis"),
        ):
            save_page_analysis(self._path(directory), object())  # type: ignore[arg-type]

    def test_save_does_not_create_missing_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing" / "page-analysis.json"

            with self.assertRaises(FileNotFoundError):
                save_page_analysis(missing_path, self._analysis())
            self.assertFalse(missing_path.parent.exists())

    def test_save_does_not_modify_input_analysis(self) -> None:
        analysis = self._analysis()
        expected = self._analysis()
        with tempfile.TemporaryDirectory() as directory:
            save_page_analysis(self._path(directory), analysis)

        self.assertEqual(analysis, expected)

    def test_load_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path), self._analysis())

    def test_load_round_trip_equals_analysis(self) -> None:
        analysis = self._analysis()
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory, analysis)

            self.assertEqual(load_page_analysis(path), analysis)

    def test_load_preserves_regions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path).regions, self._regions())

    def test_load_preserves_relations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path).relations, self._relations())

    def test_load_preserves_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path).candidates, self._candidates())

    def test_load_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path).provenance, self._provenance())

    def test_load_preserves_region_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(
                tuple(region.region_id for region in load_page_analysis(path).regions),
                ("region-1", "region-2"),
            )

    def test_load_preserves_relation_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(
                tuple(relation.relation_id for relation in load_page_analysis(path).relations),
                ("relation-1",),
            )

    def test_load_preserves_candidate_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(
                tuple(candidate.candidate_id for candidate in load_page_analysis(path).candidates),
                ("candidate-1", "candidate-2"),
            )

    def test_load_preserves_primitive_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(
                load_page_analysis(path).regions[0].primitive_ids, ("primitive-1", "primitive-2")
            )
            self.assertEqual(
                load_page_analysis(path).candidates[0].primitive_ids,
                ("primitive-1", "primitive-3"),
            )

    def test_load_preserves_candidate_bbox(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            self.assertEqual(load_page_analysis(path).candidates[0].bbox, (5.0, 5.0, 15.0, 15.0))

    def test_load_missing_file_propagates_file_not_found_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
            load_page_analysis(self._path(directory))

    def test_load_rejects_wrong_path_type(self) -> None:
        with self.assertRaises(ValueError):
            load_page_analysis("page-analysis.json")  # type: ignore[arg-type]

    def test_load_invalid_json_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._path(directory)
            path.write_text("{", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_invalid_json_error_message_contains_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._path(directory)
            path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, str(path)):
                load_page_analysis(path)

    def test_load_invalid_json_preserves_json_decode_error_cause(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._path(directory)
            path.write_text("{", encoding="utf-8")

            with self.assertRaises(ValueError) as context:
                load_page_analysis(path)

            self.assertIsInstance(context.exception.__cause__, JSONDecodeError)

    def test_load_valid_json_with_unsupported_schema_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            data["schema_version"] = "1.0"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_valid_json_with_schema_1_1_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            data["schema_version"] = "1.1"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_valid_json_with_missing_key_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            del data["regions"]
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_valid_json_without_candidates_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            del data["candidates"]
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_valid_json_with_incoherent_provenance_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            provenance = cast(dict[str, object], data["provenance"])
            provenance["source_page_id"] = "page-2"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_valid_json_with_dangling_relation_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)
            data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
            relations = cast(list[object], data["relations"])
            relation = cast(dict[str, object], relations[0])
            relation["target_region_id"] = "missing-region"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_save_directory_path_propagates_filesystem_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(OSError):
            save_page_analysis(Path(directory), self._analysis())

    def test_load_directory_path_propagates_filesystem_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(OSError):
            load_page_analysis(Path(directory))

    def test_load_valid_json_with_non_dict_root_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._path(directory)
            path.write_text("[]", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_analysis(path)

    def test_load_preserves_unicode_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(directory)

            loaded = load_page_analysis(path)

            self.assertEqual(loaded.provenance.producer_name, "produttore-è")
            self.assertEqual(loaded.provenance.configuration_id, "configurazione-à")


if __name__ == "__main__":
    unittest.main()
