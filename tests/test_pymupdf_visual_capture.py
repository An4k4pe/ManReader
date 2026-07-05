from __future__ import annotations

import io
import unittest

import fitz
from PIL import Image

from pymupdf_capture import capture_pymupdf_page


class PyMuPDFVisualCaptureTest(unittest.TestCase):
    def test_captures_raster_occurrence_without_exporting(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=300.0, height=400.0)
            image_bytes = _png_bytes()
            page.insert_image(
                fitz.Rect(100.0, 120.0, 160.0, 240.0),
                stream=image_bytes,
            )

            capture = capture_pymupdf_page(
                page,
                source_id="source:1",
                page_id="page:1",
                capture_id="capture:1",
            )

            self.assertEqual(len(capture.image_observations), 1)
            image = capture.image_observations[0]
            self.assertEqual(image.observation_id, "image:i0000")
            self.assertEqual(image.bbox, (100.0, 120.0, 160.0, 240.0))
            self.assertEqual((image.pixel_width, image.pixel_height), (10, 20))
            self.assertEqual(
                image.placement_transform,
                (60.0, 0.0, -0.0, 120.0, 100.0, 120.0),
            )
            resource_ref = image.resource_ref
            content_digest = image.content_digest

            assert resource_ref is not None
            assert content_digest is not None

            self.assertTrue(resource_ref.startswith("xref:"))
            self.assertTrue(content_digest.startswith("md5:"))
            self.assertTrue(image.has_alpha)
            self.assertEqual(capture.backend_order, ())
            self.assertIsNone(capture.backend_order_kind)
        finally:
            document.close()

    def test_repeated_image_resource_creates_distinct_occurrences(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=300.0, height=400.0)
            image_bytes = _png_bytes()
            first_xref = page.insert_image(
                fitz.Rect(10.0, 10.0, 60.0, 110.0),
                stream=image_bytes,
            )
            page.insert_image(
                fitz.Rect(100.0, 10.0, 150.0, 110.0),
                xref=first_xref,
            )

            capture = capture_pymupdf_page(
                page,
                source_id="source:1",
                page_id="page:1",
                capture_id="capture:1",
            )

            self.assertEqual(len(capture.image_observations), 2)
            first, second = capture.image_observations
            self.assertNotEqual(first.observation_id, second.observation_id)
            self.assertEqual(first.resource_ref, second.resource_ref)
            self.assertEqual(first.content_digest, second.content_digest)
            self.assertNotEqual(first.bbox, second.bbox)
        finally:
            document.close()

    def test_captures_line_rectangle_curve_and_style(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=300.0, height=400.0)
            shape = page.new_shape()
            shape.draw_line((10.0, 10.0), (100.0, 10.0))
            shape.draw_rect(fitz.Rect(20.0, 20.0, 80.0, 60.0))
            shape.draw_bezier(
                (10.0, 100.0),
                (20.0, 80.0),
                (50.0, 120.0),
                (80.0, 100.0),
            )
            shape.finish(
                color=(1.0, 0.0, 0.0),
                fill=(0.0, 1.0, 0.0),
                width=2.0,
                closePath=False,
                stroke_opacity=0.5,
                fill_opacity=0.25,
            )
            shape.commit()

            capture = capture_pymupdf_page(
                page,
                source_id="source:1",
                page_id="page:1",
                capture_id="capture:1",
            )

            self.assertEqual(len(capture.drawing_observations), 1)
            drawing = capture.drawing_observations[0]
            self.assertEqual(drawing.observation_id, "drawing:p0000")
            self.assertEqual(
                tuple(command.kind for command in drawing.commands),
                ("line", "rect", "cubic_bezier"),
            )
            self.assertEqual(drawing.stroke_width, 2.0)
            self.assertEqual(drawing.stroke_color, (1.0, 0.0, 0.0, 1.0))
            self.assertEqual(drawing.fill_color, (0.0, 1.0, 0.0, 1.0))
            self.assertEqual(drawing.stroke_opacity, 0.5)
            self.assertEqual(drawing.fill_opacity, 0.25)
            self.assertFalse(drawing.is_closed)
            self.assertEqual(capture.backend_order, ())
        finally:
            document.close()

    def test_text_order_remains_text_only_when_visuals_are_present(self) -> None:
        document = fitz.open()
        try:
            page = document.new_page(width=300.0, height=400.0)
            page.insert_text((20.0, 40.0), "Text")
            page.insert_image(
                fitz.Rect(100.0, 100.0, 150.0, 200.0),
                stream=_png_bytes(),
            )
            shape = page.new_shape()
            shape.draw_line((10.0, 250.0), (100.0, 250.0))
            shape.finish(color=(0.0, 0.0, 0.0))
            shape.commit()

            capture = capture_pymupdf_page(
                page,
                source_id="source:1",
                page_id="page:1",
                capture_id="capture:1",
            )

            self.assertEqual(capture.backend_order_kind, "extraction")
            self.assertEqual(
                capture.backend_order,
                tuple(item.observation_id for item in capture.text_observations),
            )
            self.assertTrue(all(item.startswith("text:") for item in capture.backend_order))
            self.assertEqual(len(capture.image_observations), 1)
            self.assertEqual(len(capture.drawing_observations), 1)
        finally:
            document.close()


def _png_bytes() -> bytes:
    image = Image.new("RGBA", (10, 20), (255, 0, 0, 128))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
