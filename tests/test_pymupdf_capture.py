from __future__ import annotations

import ast
import unittest
from dataclasses import asdict
from pathlib import Path

import fitz

from pymupdf_capture import capture_pymupdf_page


class PyMuPDFCaptureTest(unittest.TestCase):
    def test_empty_page_capture(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=400.0)

        capture = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )

        self.assertEqual(capture.page_index, 0)
        self.assertEqual(capture.page_geometry.width, 300.0)
        self.assertEqual(capture.page_geometry.height, 400.0)
        self.assertEqual(capture.page_geometry.unit, "pt")
        self.assertEqual(
            capture.page_geometry.coordinate_system,
            "top_left_y_down",
        )
        self.assertEqual(capture.text_observations, ())
        self.assertEqual(capture.backend_order, ())
        self.assertIsNone(capture.backend_order_kind)
        self.assertEqual(capture.errors, ())
        self.assertEqual(capture.image_observations, ())
        self.assertEqual(capture.drawing_observations, ())
        self.assertEqual(capture.link_observations, ())
        self.assertEqual(capture.annotation_observations, ())
        self.assertIsNone(capture.crop_box)
        self.assertIsNone(capture.media_box)

    def test_text_runs_are_captured_without_sorting_or_joining(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=400.0)

        page.insert_text(
            (180.0, 60.0),
            "Inserted first",
            fontsize=11.0,
            fontname="helv",
            color=(1.0, 0.0, 0.0),
        )
        page.insert_text(
            (30.0, 160.0),
            "Inserted second",
            fontsize=9.0,
            fontname="cour",
            color=(0.0, 0.0, 1.0),
        )

        capture = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )

        texts = tuple(observation.text for observation in capture.text_observations)
        self.assertEqual(texts, ("Inserted first", "Inserted second"))
        self.assertEqual(
            capture.backend_order,
            tuple(
                observation.observation_id
                for observation in capture.text_observations
            ),
        )
        self.assertEqual(capture.backend_order_kind, "extraction")
        self.assertEqual(
            capture.text_observations[0].observation_id,
            "text:b0000:l0000:s0000",
        )
        self.assertEqual(
            capture.text_observations[1].observation_id,
            "text:b0001:l0000:s0000",
        )

    def test_span_typography_bbox_color_and_direction_are_propagated(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=400.0)
        page.insert_text(
            (50.0, 80.0),
            "Red text",
            fontsize=12.0,
            fontname="helv",
            color=(1.0, 0.0, 0.0),
        )

        capture = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )
        observation = capture.text_observations[0]

        self.assertEqual(observation.text, "Red text")
        self.assertEqual(observation.font_name, "Helvetica")
        self.assertAlmostEqual(observation.font_size or 0.0, 12.0)
        self.assertEqual(observation.font_flags, 0)
        self.assertEqual(observation.color, (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(observation.direction, (1.0, 0.0))
        self.assertLess(observation.bbox[0], observation.bbox[2])
        self.assertLess(observation.bbox[1], observation.bbox[3])

    def test_source_rotation_is_recorded_without_rotating_capture_geometry(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=400.0)
        page.set_rotation(90)
        page.insert_text((50.0, 80.0), "Rotated page")

        capture = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )

        self.assertEqual(capture.source_rotation_degrees, 90)
        self.assertEqual(capture.page_geometry.width, 300.0)
        self.assertEqual(capture.page_geometry.height, 400.0)
        self.assertGreater(len(capture.text_observations), 0)

    def test_capture_is_deterministic_for_the_same_page_and_identity(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=400.0)
        page.insert_text((50.0, 80.0), "Stable")

        first = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )
        second = capture_pymupdf_page(
            page,
            source_id="source:test",
            page_id="page:0",
            capture_id="capture:test:0",
        )

        self.assertEqual(asdict(first), asdict(second))

    def test_page_index_is_zero_based(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        document.new_page(width=300.0, height=400.0)
        second_page = document.new_page(width=300.0, height=400.0)

        capture = capture_pymupdf_page(
            second_page,
            source_id="source:test",
            page_id="page:1",
            capture_id="capture:test:1",
        )

        self.assertEqual(capture.page_index, 1)

    def test_adapter_does_not_import_legacy_modules(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "pymupdf_capture.py"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

        self.assertNotIn("extractor", imported_roots)
        self.assertNotIn("ir_model", imported_roots)
        self.assertNotIn("main", imported_roots)


if __name__ == "__main__":
    unittest.main()
