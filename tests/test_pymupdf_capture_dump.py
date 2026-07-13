from __future__ import annotations

import base64
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import cast

import fitz

from page_analysis_model import PAGE_ANALYSIS_SCHEMA_VERSION
from pymupdf_capture_dump import (
    build_argument_parser,
    dump_capture,
    dump_local_fragment_side_band_page_analysis,
    dump_normalized_primitives,
    dump_page_analysis,
    dump_primitive_pair_measurements,
    dump_singleton_side_band_page_analysis,
    main,
)

_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGP8z8Dwn4GBgYGJAQoAHxcCAk+Uzr4AAAAASUVORK5CYII="
)


class PyMuPDFCaptureDumpTest(unittest.TestCase):
    def test_parser_accepts_analysis_stage(self) -> None:
        args = build_argument_parser().parse_args(("sample.pdf", "--stage", "analysis"))

        self.assertEqual(args.stage, "analysis")

    def test_parser_accepts_singleton_side_band_analysis_stage(self) -> None:
        args = build_argument_parser().parse_args(("sample.pdf", "--stage", "analysis-side-band"))

        self.assertEqual(args.stage, "analysis-side-band")

    def test_parser_accepts_local_fragment_side_band_analysis_stage(self) -> None:
        args = build_argument_parser().parse_args(
            ("sample.pdf", "--stage", "analysis-side-band-local-fragment")
        )

        self.assertEqual(args.stage, "analysis-side-band-local-fragment")

    def test_parser_accepts_primitive_pair_stage_without_ids_for_other_stages(self) -> None:
        pair_args = build_argument_parser().parse_args(("sample.pdf", "--stage", "primitive-pair"))
        capture_args = build_argument_parser().parse_args(("sample.pdf", "--stage", "capture"))

        self.assertEqual(pair_args.stage, "primitive-pair")
        self.assertIsNone(capture_args.first_primitive_id)
        self.assertIsNone(capture_args.second_primitive_id)

    def test_dump_capture_returns_pretty_json_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("First page", "Second page"))

            json_text = dump_capture(pdf_path, page_number=2)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(payload["page_index"], 1)
            self.assertEqual(payload["page_id"], "diagnostic-page:1")
            self.assertEqual(
                payload["capture_id"],
                "diagnostic-pymupdf-capture:1",
            )
            self.assertEqual(
                [item["text"] for item in payload["text_observations"]],
                ["Second page"],
            )
            self.assertEqual(list(Path(temporary_directory).glob("*.json")), [])

    def test_dump_normalized_primitives_returns_derived_page_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Normalized page",))

            json_text = dump_normalized_primitives(pdf_path)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(
                payload["source_capture_id"],
                "diagnostic-pymupdf-capture:0",
            )
            self.assertEqual(payload["source_id"], "diagnostic-source")
            self.assertEqual(payload["page_id"], "diagnostic-page:0")
            self.assertEqual(payload["page_index"], 0)
            self.assertEqual(
                payload["capture_to_canonical_transform"],
                [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            )
            self.assertEqual(
                [item["text"] for item in payload["text_primitives"]],
                ["Normalized page"],
            )
            self.assertNotIn("text_observations", payload)
            self.assertNotIn("backend_order", payload)

    def test_dump_page_analysis_returns_validated_root_region_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf_with_primitives(pdf_path)

            json_text = dump_page_analysis(pdf_path)
            payload = json.loads(json_text)
            primitives = json.loads(dump_normalized_primitives(pdf_path))
            expected_ids = _primitive_ids(primitives)
            root = payload["regions"][0]
            extent = payload["regions"][1]
            relation = payload["relations"][0]

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertEqual(payload["generation_id"], "diagnostic-page-analysis:0")
            self.assertEqual(payload["page_id"], "diagnostic-page:0")
            self.assertEqual(len(payload["regions"]), 2)
            self.assertEqual(len(payload["relations"]), 1)
            self.assertEqual(root["region_id"], "region:page-root")
            self.assertEqual(root["page_id"], "diagnostic-page:0")
            self.assertEqual(root["structural_kind"], "layout.page")
            self.assertEqual(root["bbox"], [0.0, 0.0, 200.0, 300.0])
            self.assertEqual(root["primitive_ids"], expected_ids)
            self.assertEqual(extent["region_id"], "region:primitive-extent")
            self.assertEqual(extent["page_id"], "diagnostic-page:0")
            self.assertEqual(extent["structural_kind"], "layout.primitive_extent")
            self.assertEqual(extent["bbox"], _primitive_extent_bbox(primitives))
            self.assertEqual(extent["primitive_ids"], expected_ids)
            self.assertEqual(len(extent["primitive_ids"]), _primitive_count(primitives))
            self.assertEqual(
                relation,
                {
                    "relation_id": "relation:page-root-contains-primitive-extent",
                    "relation_kind": "layout.contains",
                    "source_region_id": "region:page-root",
                    "target_region_id": "region:primitive-extent",
                },
            )
            self.assertGreater(len(primitives["text_primitives"]), 0)
            self.assertGreater(len(primitives["image_primitives"]), 0)
            self.assertGreater(len(primitives["drawing_primitives"]), 0)
            self.assertEqual(
                payload["provenance"],
                {
                    "source_id": "diagnostic-source",
                    "source_capture_id": "diagnostic-pymupdf-capture:0",
                    "source_page_id": "diagnostic-page:0",
                    "source_primitive_schema_version": "1",
                    "producer_name": "page-analysis-primitive-extent",
                    "producer_version": "0.1",
                    "configuration_id": "primitive-extent-analysis-v1",
                },
            )

    def test_dump_singleton_side_band_analysis_returns_candidate_json_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "side-band.pdf"
            _create_pdf_with_side_band_text(pdf_path)

            json_text = dump_singleton_side_band_page_analysis(pdf_path)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertIn("candidates", payload)
            self.assertEqual(payload["regions"], [])
            self.assertEqual(payload["relations"], [])
            self.assertEqual(
                payload["provenance"]["producer_name"],
                "page_analysis.singleton_side_band",
            )
            self.assertEqual(
                payload["provenance"]["configuration_id"],
                "singleton-side-band-v1",
            )
            self.assertEqual(len(payload["candidates"]), 1)
            self.assertEqual(
                payload["candidates"][0]["proposed_structural_kind"],
                "layout.side_band",
            )
            self.assertEqual(list(root.glob("*.json")), [])

    def test_local_fragment_stage_produces_multi_candidate_distinct_from_singleton_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "local-fragment-side-band.pdf"
            _create_pdf_with_local_fragment_side_band_text(pdf_path)

            local_payload = json.loads(dump_local_fragment_side_band_page_analysis(pdf_path))
            singleton_payload = json.loads(dump_singleton_side_band_page_analysis(pdf_path))

            self.assertEqual(local_payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertEqual(local_payload["regions"], [])
            self.assertEqual(local_payload["relations"], [])
            self.assertEqual(
                local_payload["provenance"]["producer_name"],
                "page_analysis.local_fragment_side_band",
            )
            self.assertEqual(
                local_payload["provenance"]["configuration_id"],
                "local-fragment-side-band-v1",
            )
            self.assertEqual(len(local_payload["candidates"]), 1)
            self.assertEqual(len(local_payload["candidates"][0]["primitive_ids"]), 2)
            self.assertEqual(
                singleton_payload["provenance"]["producer_name"],
                "page_analysis.singleton_side_band",
            )
            self.assertEqual(
                singleton_payload["provenance"]["configuration_id"],
                "singleton-side-band-v1",
            )
            self.assertEqual(len(singleton_payload["candidates"]), 2)
            self.assertTrue(
                all(
                    len(candidate["primitive_ids"]) == 1
                    for candidate in singleton_payload["candidates"]
                )
            )

    def test_local_fragment_helper_writes_compact_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "local-fragment-side-band.pdf"
            output_path = root / "diagnostics" / "local-fragment.json"
            _create_pdf_with_local_fragment_side_band_text(pdf_path)

            returned = dump_local_fragment_side_band_page_analysis(
                pdf_path,
                output_path=output_path,
                compact=True,
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertFalse(returned.endswith("\n"))
            self.assertEqual(len(json.loads(returned)["candidates"]), 1)

    def test_dump_primitive_pair_measurements_returns_geometry_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "primitives.pdf"
            _create_pdf_with_primitives(pdf_path)
            primitives = json.loads(dump_normalized_primitives(pdf_path))
            text_id = primitives["text_primitives"][0]["primitive_id"]
            image_id = primitives["image_primitives"][0]["primitive_id"]

            payload = json.loads(
                dump_primitive_pair_measurements(
                    pdf_path,
                    first_primitive_id=text_id,
                    second_primitive_id=image_id,
                )
            )

            self.assertEqual(payload["first_primitive_id"], text_id)
            self.assertEqual(payload["second_primitive_id"], image_id)
            self.assertEqual(payload["first_primitive_kind"], "text")
            self.assertEqual(payload["second_primitive_kind"], "image")
            self.assertIn("horizontal_gap", payload)
            self.assertIn("center_y_delta", payload)
            self.assertNotIn("candidates", payload)

    def test_singleton_side_band_stage_does_not_change_existing_analysis_or_legacy_diagnostics(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "side-band.pdf"
            _create_pdf_with_side_band_text(pdf_path)
            analysis_before = dump_page_analysis(pdf_path)
            capture_before = dump_capture(pdf_path)
            primitives_before = dump_normalized_primitives(pdf_path)

            dump_singleton_side_band_page_analysis(pdf_path)

            self.assertEqual(dump_page_analysis(pdf_path), analysis_before)
            self.assertEqual(dump_capture(pdf_path), capture_before)
            self.assertEqual(dump_normalized_primitives(pdf_path), primitives_before)

    def test_dump_page_analysis_clips_partially_off_page_primitives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "partial.pdf"
            _create_pdf_with_partially_off_page_drawing(pdf_path)

            payload = json.loads(dump_page_analysis(pdf_path))
            primitives = json.loads(dump_normalized_primitives(pdf_path))
            extent = payload["regions"][1]
            extent_bbox = cast(list[float], extent["bbox"])
            extent_ids = cast(list[str], extent["primitive_ids"])
            drawing_ids = [
                cast(str, primitive["primitive_id"])
                for primitive in cast(list[dict[str, object]], primitives["drawing_primitives"])
            ]

            self.assertGreater(len(drawing_ids), 0)
            self.assertTrue(all(primitive_id in extent_ids for primitive_id in drawing_ids))
            self.assertGreaterEqual(extent_bbox[0], 0.0)
            self.assertGreaterEqual(extent_bbox[1], 0.0)
            self.assertLessEqual(extent_bbox[2], 200.0)
            self.assertLessEqual(extent_bbox[3], 300.0)

    def test_dump_page_analysis_empty_page_has_root_without_primitives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "empty.pdf"
            _create_empty_pdf(pdf_path)

            payload = json.loads(dump_page_analysis(pdf_path))
            root = payload["regions"][0]

            self.assertEqual(len(payload["regions"]), 1)
            self.assertEqual(root["region_id"], "region:page-root")
            self.assertEqual(root["primitive_ids"], [])
            self.assertEqual(root["bbox"], [0.0, 0.0, 200.0, 300.0])
            self.assertEqual(payload["relations"], [])

    def test_dump_page_analysis_compact_output_has_no_final_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Compact analysis",))

            json_text = dump_page_analysis(pdf_path, compact=True)

            self.assertFalse(json_text.endswith("\n"))
            self.assertEqual(len(json.loads(json_text)["regions"]), 2)

    def test_dump_page_analysis_writes_requested_output_and_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "analysis.json"
            _create_pdf(pdf_path, ("Analysis file",))

            returned = dump_page_analysis(pdf_path, output_path=output_path)

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertTrue(returned.endswith("\n"))
            self.assertEqual(json.loads(returned)["generation_id"], "diagnostic-page-analysis:0")

    def test_dump_page_analysis_is_deterministic_for_same_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Deterministic analysis",))

            first = dump_page_analysis(pdf_path)
            second = dump_page_analysis(pdf_path)

            self.assertEqual(first, second)

    def test_analysis_stage_does_not_change_capture_or_primitives_dump(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Stable diagnostics",))
            capture_before = dump_capture(pdf_path)
            primitives_before = dump_normalized_primitives(pdf_path)

            dump_page_analysis(pdf_path)

            self.assertEqual(dump_capture(pdf_path), capture_before)
            self.assertEqual(dump_normalized_primitives(pdf_path), primitives_before)

    def test_synthetic_pdf_traverses_full_analysis_chain_without_legacy_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Full chain",))

            payload = json.loads(dump_page_analysis(pdf_path))

            self.assertEqual(payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertEqual(
                payload["provenance"]["producer_name"],
                "page-analysis-primitive-extent",
            )
            self.assertEqual(len(payload["regions"]), 2)
            self.assertEqual(len(payload["relations"]), 1)

    def test_dump_capture_writes_only_when_output_is_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "capture.json"
            _create_pdf(pdf_path, ("Text",))

            returned = dump_capture(
                pdf_path,
                output_path=output_path,
                compact=True,
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertNotIn("\n", returned)
            self.assertEqual(json.loads(returned)["page_index"], 0)

    def test_dump_normalized_primitives_writes_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "primitives.json"
            _create_pdf(pdf_path, ("Text",))

            returned = dump_normalized_primitives(
                pdf_path,
                output_path=output_path,
                compact=True,
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertIn("text_primitives", json.loads(returned))

    def test_dump_capture_rejects_missing_pdf_and_invalid_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missing = root / "missing.pdf"
            with self.assertRaises(FileNotFoundError):
                dump_capture(missing)

            pdf_path = root / "sample.pdf"
            _create_pdf(pdf_path, ("Only page",))
            with self.assertRaises(ValueError):
                dump_capture(pdf_path, page_number=0)
            with self.assertRaises(ValueError):
                dump_capture(pdf_path, page_number=2)

    def test_main_prints_capture_json_to_stdout_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--page", "1"))

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["text_observations"][0]["text"], "CLI text")
            self.assertNotIn("text_primitives", payload)

    def test_main_requires_each_primitive_pair_id_only_for_primitive_pair_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "primitives.pdf"
            _create_pdf_with_primitives(pdf_path)
            stderr = StringIO()

            with redirect_stderr(stderr), self.assertRaises(SystemExit):
                main((str(pdf_path), "--stage", "primitive-pair"))
            self.assertIn("--first-primitive-id", stderr.getvalue())

            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit):
                main(
                    (
                        str(pdf_path),
                        "--stage",
                        "primitive-pair",
                        "--first-primitive-id",
                        "first",
                    )
                )
            self.assertIn("--second-primitive-id", stderr.getvalue())

    def test_main_prints_analysis_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI analysis",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--stage", "analysis"))

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertEqual(len(payload["regions"]), 2)
            self.assertNotIn("text_observations", payload)
            self.assertNotIn("text_primitives", payload)

    def test_main_prints_singleton_side_band_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "side-band.pdf"
            _create_pdf_with_side_band_text(pdf_path)
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--stage", "analysis-side-band"))

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema_version"], PAGE_ANALYSIS_SCHEMA_VERSION)
            self.assertEqual(
                payload["provenance"]["producer_name"],
                "page_analysis.singleton_side_band",
            )
            self.assertIn("candidates", payload)

    def test_main_prints_local_fragment_side_band_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "local-fragment-side-band.pdf"
            _create_pdf_with_local_fragment_side_band_text(pdf_path)
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main(
                    (str(pdf_path), "--stage", "analysis-side-band-local-fragment")
                )

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                payload["provenance"]["producer_name"],
                "page_analysis.local_fragment_side_band",
            )
            self.assertEqual(len(payload["candidates"]), 1)

    def test_main_prints_primitive_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI primitives",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "primitives",
                    )
                )

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                payload["text_primitives"][0]["text"],
                "CLI primitives",
            )
            self.assertNotIn("text_observations", payload)

    def test_main_writes_file_and_reports_stage_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "primitives.json"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "primitives",
                        "--output",
                        str(output_path),
                    )
                )

            self.assertEqual(return_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output_path.is_file())
            self.assertIn("Wrote PyMuPDF shadow primitives", stderr.getvalue())

    def test_main_writes_analysis_file_and_reports_stage_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "analysis.json"
            _create_pdf(pdf_path, ("CLI analysis file",))
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "analysis",
                        "--output",
                        str(output_path),
                    )
                )

            self.assertEqual(return_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output_path.is_file())
            self.assertIn("Wrote PyMuPDF shadow analysis", stderr.getvalue())


def _create_pdf(path: Path, page_texts: tuple[str, ...]) -> None:
    document = fitz.open()
    try:
        for text in page_texts:
            page = document.new_page(width=200.0, height=300.0)
            page.insert_text((20.0, 40.0), text)
        document.save(path)
    finally:
        document.close()


def _create_empty_pdf(path: Path) -> None:
    document = fitz.open()
    try:
        document.new_page(width=200.0, height=300.0)
        document.save(path)
    finally:
        document.close()


def _create_pdf_with_side_band_text(path: Path) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=200.0, height=300.0)
        page.insert_text((10.0, 150.0), "Side")
        document.save(path)
    finally:
        document.close()


def _create_pdf_with_local_fragment_side_band_text(path: Path) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=200.0, height=300.0)
        page.insert_text((6.0, 150.0), "One")
        page.insert_text((27.0, 150.0), "Two", fontname="cour")
        document.save(path)
    finally:
        document.close()


def _create_pdf_with_primitives(path: Path) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=200.0, height=300.0)
        page.insert_text((20.0, 40.0), "Root analysis")
        page.insert_image(
            fitz.Rect(40.0, 80.0, 90.0, 130.0),
            stream=_ONE_PIXEL_PNG,
        )
        page.draw_rect(
            fitz.Rect(120.0, 80.0, 180.0, 140.0),
            color=(0.0, 0.0, 0.0),
            fill=(0.5, 0.5, 0.5),
            width=1.0,
        )
        document.save(path)
    finally:
        document.close()


def _create_pdf_with_partially_off_page_drawing(path: Path) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=200.0, height=300.0)
        page.insert_text((20.0, 40.0), "Partial drawing")
        page.draw_rect(
            fitz.Rect(180.0, 260.0, 240.0, 340.0),
            color=(0.0, 0.0, 0.0),
            fill=(0.5, 0.5, 0.5),
            width=1.0,
        )
        document.save(path)
    finally:
        document.close()


def _primitive_ids(primitives: dict[str, object]) -> list[str]:
    text_primitives = cast(list[dict[str, object]], primitives["text_primitives"])
    image_primitives = cast(list[dict[str, object]], primitives["image_primitives"])
    drawing_primitives = cast(list[dict[str, object]], primitives["drawing_primitives"])
    return (
        [cast(str, item["primitive_id"]) for item in text_primitives]
        + [cast(str, item["primitive_id"]) for item in image_primitives]
        + [cast(str, item["primitive_id"]) for item in drawing_primitives]
    )


def _primitive_extent_bbox(primitives: dict[str, object]) -> list[float]:
    primitive_items = (
        cast(list[dict[str, object]], primitives["text_primitives"])
        + cast(list[dict[str, object]], primitives["image_primitives"])
        + cast(list[dict[str, object]], primitives["drawing_primitives"])
    )
    page_geometry = cast(dict[str, object], primitives["page_geometry"])
    page_width = cast(float, page_geometry["width"])
    page_height = cast(float, page_geometry["height"])
    bboxes = [
        visible_bbox
        for item in primitive_items
        if (
            visible_bbox := _visible_bbox(
                cast(list[float], item["bbox"]),
                page_width=page_width,
                page_height=page_height,
            )
        )
        is not None
    ]
    return [
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    ]


def _visible_bbox(
    bbox: list[float],
    *,
    page_width: float,
    page_height: float,
) -> list[float] | None:
    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return [x0, y0, x1, y1]


def _primitive_count(primitives: dict[str, object]) -> int:
    return (
        len(cast(list[object], primitives["text_primitives"]))
        + len(cast(list[object], primitives["image_primitives"]))
        + len(cast(list[object], primitives["drawing_primitives"]))
    )


if __name__ == "__main__":
    unittest.main()
