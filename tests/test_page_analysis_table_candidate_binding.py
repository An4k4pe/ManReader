"""Tests for the normalized-page/pdfplumber-page table binding."""

from __future__ import annotations

import io
import unittest

import fitz
import pdfplumber

from page_analysis_table_candidate_binding import BoundTableCandidatePage
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page


class TableCandidateBindingTests(unittest.TestCase):
    def _pages(self, *, page_id: str, plumber_page_index: int = 0):
        document = fitz.open()
        self.addCleanup(document.close)
        document.new_page(width=200.0, height=200.0)
        document.new_page(width=200.0, height=200.0)
        pdf_bytes = document.tobytes()
        capture_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.addCleanup(capture_document.close)
        capture = capture_pymupdf_page(
            capture_document[0],
            source_id="source:test",
            page_id=page_id,
            capture_id="capture:test",
        )
        plumber_document = pdfplumber.open(io.BytesIO(pdf_bytes))
        self.addCleanup(plumber_document.close)
        return normalize_backend_page_capture(capture), plumber_document.pages[plumber_page_index]

    def test_matching_page_number_is_accepted(self) -> None:
        primitive_page, plumber_page = self._pages(page_id="page:0001")

        binding = BoundTableCandidatePage(primitive_page, plumber_page)

        self.assertIs(binding.primitive_page, primitive_page)
        self.assertIs(binding.plumber_page, plumber_page)

    def test_numeric_page_number_mismatch_is_rejected(self) -> None:
        primitive_page, plumber_page = self._pages(
            page_id="page:0001",
            plumber_page_index=1,
        )

        with self.assertRaisesRegex(ValueError, "page number mismatch"):
            BoundTableCandidatePage(primitive_page, plumber_page)

    def test_unexpected_page_id_format_is_rejected(self) -> None:
        primitive_page, plumber_page = self._pages(page_id="prototype-page-1")

        with self.assertRaisesRegex(ValueError, "page_id format mismatch"):
            BoundTableCandidatePage(primitive_page, plumber_page)


if __name__ == "__main__":
    unittest.main()
