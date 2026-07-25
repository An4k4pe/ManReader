"""Tests for verified PyMuPDF/pdfplumber document-source bindings."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

from pymupdf_pdfplumber_document_source_binding import (
    bind_pymupdf_pdfplumber_document_source,
)
from verified_file_model import VerifiedFileReference, inspect_verified_bytes


def _pdf_bytes(page_count: int) -> bytes:
    document = fitz.open()
    try:
        for _ in range(page_count):
            document.new_page()
        return document.tobytes()
    finally:
        document.close()


class _MismatchedPlumberPdf:
    def __init__(self) -> None:
        self.pages = (object(), object())
        self.closed = False

    def close(self) -> None:
        self.closed = True


class PyMuPDFPdfplumberDocumentSourceBindingTests(unittest.TestCase):
    def test_rejects_digest_and_size_mismatch_before_opening_backends(self) -> None:
        payload = _pdf_bytes(1)
        with tempfile.TemporaryDirectory() as temporary_directory:
            snapshot_path = Path(temporary_directory) / "source.pdf"
            snapshot_path.write_bytes(payload)
            expected = inspect_verified_bytes(payload)
            wrong_digest = VerifiedFileReference(
                sha256="b" * 64,
                size_bytes=expected.size_bytes,
            )
            wrong_size = VerifiedFileReference(
                sha256=expected.sha256,
                size_bytes=expected.size_bytes + 1,
            )

            with patch(
                "pymupdf_pdfplumber_document_source_binding.fitz.open"
            ) as fitz_open:
                with self.assertRaisesRegex(ValueError, "digest"):
                    bind_pymupdf_pdfplumber_document_source(
                        snapshot_path,
                        expected_file=wrong_digest,
                    )
                with self.assertRaisesRegex(ValueError, "size"):
                    bind_pymupdf_pdfplumber_document_source(
                        snapshot_path,
                        expected_file=wrong_size,
                    )

            fitz_open.assert_not_called()

    def test_opens_both_backends_from_verified_bytes(self) -> None:
        payload = _pdf_bytes(2)
        with tempfile.TemporaryDirectory() as temporary_directory:
            snapshot_path = Path(temporary_directory) / "source.pdf"
            snapshot_path.write_bytes(payload)

            bound = bind_pymupdf_pdfplumber_document_source(
                snapshot_path,
                expected_file=inspect_verified_bytes(payload),
            )
            try:
                self.assertEqual(bound.fitz_document.page_count, 2)
                self.assertEqual(len(bound.plumber_pdf.pages), 2)
            finally:
                bound.fitz_document.close()
                bound.plumber_pdf.close()

    def test_rejects_and_closes_on_page_count_mismatch(self) -> None:
        payload = _pdf_bytes(1)
        mismatched = _MismatchedPlumberPdf()
        with tempfile.TemporaryDirectory() as temporary_directory:
            snapshot_path = Path(temporary_directory) / "source.pdf"
            snapshot_path.write_bytes(payload)

            with patch(
                "pymupdf_pdfplumber_document_source_binding.PDF.open",
                return_value=mismatched,
            ), self.assertRaisesRegex(ValueError, "page counts"):
                bind_pymupdf_pdfplumber_document_source(
                    snapshot_path,
                    expected_file=inspect_verified_bytes(payload),
                )

        self.assertTrue(mismatched.closed)


if __name__ == "__main__":
    unittest.main()
