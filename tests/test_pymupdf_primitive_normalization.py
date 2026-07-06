from __future__ import annotations

import base64
import unittest

import fitz

from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page

_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGP8z8Dwn4GBgYGJAQoAHxcCAk+Uzr4AAAAASUVORK5CYII="
)


class PyMuPDFPrimitiveNormalizationTest(unittest.TestCase):
    def test_real_capture_normalizes_supported_observations_one_to_one(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=300.0, height=400.0)
            page.insert_text((30.0, 50.0), "Normalization")
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

            capture = capture_pymupdf_page(
                page,
                source_id="source:synthetic",
                page_id="page:1",
                capture_id="capture:synthetic:1",
            )
            normalized = normalize_backend_page_capture(capture)
        finally:
            document.close()

        self.assertGreaterEqual(len(capture.text_observations), 1)
        self.assertGreaterEqual(len(capture.image_observations), 1)
        self.assertGreaterEqual(len(capture.drawing_observations), 1)

        self.assertEqual(
            len(normalized.text_primitives),
            len(capture.text_observations),
        )
        self.assertEqual(
            len(normalized.image_primitives),
            len(capture.image_observations),
        )
        self.assertEqual(
            len(normalized.drawing_primitives),
            len(capture.drawing_observations),
        )

        self.assertEqual(
            tuple(
                primitive.source_observation_id
                for primitive in normalized.text_primitives
            ),
            tuple(
                observation.observation_id
                for observation in capture.text_observations
            ),
        )
        self.assertEqual(
            tuple(
                primitive.source_observation_id
                for primitive in normalized.image_primitives
            ),
            tuple(
                observation.observation_id
                for observation in capture.image_observations
            ),
        )
        self.assertEqual(
            tuple(
                primitive.source_observation_id
                for primitive in normalized.drawing_primitives
            ),
            tuple(
                observation.observation_id
                for observation in capture.drawing_observations
            ),
        )

        self.assertEqual(
            normalized.capture_to_canonical_transform,
            (1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        )
        self.assertEqual(normalized.page_geometry, capture.page_geometry)
        self.assertEqual(normalized.source_capture_id, capture.capture_id)

    def test_real_capture_normalization_is_deterministic(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=200.0, height=200.0)
            page.insert_text((20.0, 40.0), "Stable")
            page.draw_line(
                fitz.Point(20.0, 60.0),
                fitz.Point(180.0, 60.0),
                color=(0.0, 0.0, 0.0),
                width=1.0,
            )

            first_capture = capture_pymupdf_page(
                page,
                source_id="source:synthetic",
                page_id="page:1",
                capture_id="capture:stable",
            )
            second_capture = capture_pymupdf_page(
                page,
                source_id="source:synthetic",
                page_id="page:1",
                capture_id="capture:stable",
            )
        finally:
            document.close()

        first = normalize_backend_page_capture(first_capture)
        second = normalize_backend_page_capture(second_capture)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
