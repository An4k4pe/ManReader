"""Tests for the production pdfplumber table candidate producer."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

import fitz
import pdfplumber

from page_analysis_candidate_primitive_overlap_measurements import (
    measure_candidate_primitive_overlap_ratio,
)
from page_analysis_table_candidate import build_table_candidate_page_analysis
from page_analysis_table_candidate_binding import BoundTableCandidatePage
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page


class _OutOfBoundsTable:
    bbox = (-10.0, 20.0, 120.0, 140.0)

    def extract(self) -> list[list[str]]:
        return [["outside"]]


class TableCandidateProducerTests(unittest.TestCase):
    def _bound_page(self) -> BoundTableCandidatePage:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=300.0, height=220.0)
        for x_coordinate in (20.0, 140.0, 260.0):
            page.draw_line((x_coordinate, 20.0), (x_coordinate, 140.0))
        for y_coordinate in (20.0, 60.0, 100.0, 140.0):
            page.draw_line((20.0, y_coordinate), (260.0, y_coordinate))
        for y_coordinate, left_text, right_text in (
            (45.0, "A", "B"),
            (85.0, "C", "D"),
            (125.0, "E", "F"),
        ):
            page.insert_text((35.0, y_coordinate), left_text)
            page.insert_text((155.0, y_coordinate), right_text)
        pdf_bytes = document.tobytes()
        capture_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.addCleanup(capture_document.close)
        capture = capture_pymupdf_page(
            capture_document[0],
            source_id="source:test",
            page_id="page:0001",
            capture_id="capture:test",
        )
        plumber_document = pdfplumber.open(io.BytesIO(pdf_bytes))
        self.addCleanup(plumber_document.close)
        return BoundTableCandidatePage(
            normalize_backend_page_capture(capture),
            plumber_document.pages[0],
        )

    def test_populates_primitive_ids_for_positive_overlap(self) -> None:
        bound_page = self._bound_page()

        analysis = build_table_candidate_page_analysis(
            bound_page,
            generation_id="generation:test",
        )

        self.assertGreater(len(analysis.candidates), 0)
        for candidate in analysis.candidates:
            expected_primitive_ids = tuple(
                primitive.primitive_id
                for primitive in bound_page.primitive_page.text_primitives
                if measure_candidate_primitive_overlap_ratio(candidate.bbox, primitive.bbox)
                > 0.0
            )
            self.assertEqual(candidate.primitive_ids, expected_primitive_ids)
            self.assertNotEqual(candidate.primitive_ids, ())

    def test_discards_only_the_out_of_bounds_candidate(self) -> None:
        bound_page = self._bound_page()
        valid_tables = bound_page.plumber_page.find_tables(
            table_settings={"vertical_strategy": "text", "horizontal_strategy": "lines"}
        )
        self.assertGreater(len(valid_tables), 0)

        with patch.object(
            bound_page.plumber_page,
            "find_tables",
            return_value=[valid_tables[0], _OutOfBoundsTable()],
        ), self.assertLogs("page_analysis_table_candidate", level="WARNING") as logs:
            analysis = build_table_candidate_page_analysis(
                bound_page,
                generation_id="generation:test",
            )

        self.assertEqual(len(analysis.candidates), 1)
        self.assertEqual(analysis.candidates[0].candidate_id, "candidate:table:text-lines:0000")
        self.assertIn("candidate:table:text-lines:0001", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
