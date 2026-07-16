"""Tests for PyMuPDF document-source attestations from verified bytes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

from job_manifest_model import SourceReference
from pymupdf_document_source_attestation import attest_pymupdf_document_source
from verified_file_model import VerifiedFileReference, inspect_verified_bytes


def _pdf_bytes(page_count: int) -> bytes:
    document = fitz.open()
    try:
        for _ in range(page_count):
            document.new_page()
        return document.tobytes()
    finally:
        document.close()


def _write_payload(path: Path, payload: bytes) -> VerifiedFileReference:
    path.write_bytes(payload)
    return inspect_verified_bytes(payload)


class _Document:
    def __init__(self, *, page_count: object = 1, needs_pass: bool = False) -> None:
        self._page_count = page_count
        self.needs_pass = needs_pass
        self.closed = False

    @property
    def page_count(self) -> object:
        return self._page_count

    def close(self) -> None:
        self.closed = True


class _PageCountErrorDocument(_Document):
    @property
    def page_count(self) -> object:
        raise RuntimeError("page count failed")


class PyMuPDFDocumentSourceAttestationTests(unittest.TestCase):
    def test_valid_one_and_multiple_page_pdfs_are_attested_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            one_path = Path(temp_dir) / "one.pdf"
            many_path = Path(temp_dir) / "many.pdf"
            one_reference = _write_payload(one_path, _pdf_bytes(1))
            many_reference = _write_payload(many_path, _pdf_bytes(3))

            one = attest_pymupdf_document_source(one_path, expected_file=one_reference)
            many = attest_pymupdf_document_source(many_path, expected_file=many_reference)

            self.assertEqual(one.page_count, 1)
            self.assertEqual(many.page_count, 3)
            self.assertEqual(one, attest_pymupdf_document_source(one_path, expected_file=one_reference))
            self.assertEqual(one.source_id, one_reference.sha256)
            self.assertEqual(one.verified_file, one_reference)

    def test_source_reference_is_accepted_without_producer_importing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.pdf"
            reference = _write_payload(path, _pdf_bytes(1))
            expected = SourceReference(
                sha256=reference.sha256,
                size_bytes=reference.size_bytes,
                original_name="source.pdf",
            )

            attestation = attest_pymupdf_document_source(path, expected_file=expected)

            self.assertEqual(attestation.verified_file, reference)
            self.assertNotIsInstance(attestation.verified_file, SourceReference)

    def test_rejects_digest_and_size_mismatches_before_pymupdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.pdf"
            reference = _write_payload(path, _pdf_bytes(1))
            wrong_digest = VerifiedFileReference(sha256="b" * 64, size_bytes=reference.size_bytes)
            wrong_size = VerifiedFileReference(sha256=reference.sha256, size_bytes=reference.size_bytes + 1)

            with patch("pymupdf_document_source_attestation.fitz.open") as open_mock:
                with self.assertRaisesRegex(ValueError, "digest"):
                    attest_pymupdf_document_source(path, expected_file=wrong_digest)
                with self.assertRaisesRegex(ValueError, "size"):
                    attest_pymupdf_document_source(path, expected_file=wrong_size)

            open_mock.assert_not_called()

    def test_preserves_native_single_read_filesystem_errors_and_validates_types(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference = inspect_verified_bytes(b"anything")

            with self.assertRaises(FileNotFoundError):
                attest_pymupdf_document_source(root / "missing.pdf", expected_file=reference)
            with self.assertRaises(IsADirectoryError):
                attest_pymupdf_document_source(root, expected_file=reference)
            with self.assertRaisesRegex(ValueError, "snapshot_path must be a Path"):
                attest_pymupdf_document_source("not-a-path", expected_file=reference)  # type: ignore[arg-type]
            with self.assertRaisesRegex(ValueError, "expected_file must be a VerifiedFileReference"):
                attest_pymupdf_document_source(root / "missing.pdf", expected_file=object())  # type: ignore[arg-type]

    def test_rejects_empty_non_pdf_and_malformed_bytes_with_backend_cause(self) -> None:
        payloads = (b"", b"not a PDF", b"%PDF-1.7\nmalformed")
        with tempfile.TemporaryDirectory() as temp_dir:
            for index, payload in enumerate(payloads):
                path = Path(temp_dir) / f"invalid-{index}.pdf"
                reference = _write_payload(path, payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError) as raised:
                    attest_pymupdf_document_source(path, expected_file=reference)
                self.assertIsNotNone(raised.exception.__cause__)

    def test_rejects_authenticated_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "encrypted.pdf"
            document = fitz.open()
            try:
                document.new_page()
                document.save(
                    path,
                    encryption=fitz.PDF_ENCRYPT_AES_256,  # type: ignore[reportAttributeAccessIssue]
                    owner_pw="owner-password",
                    user_pw="user-password",
                )
            finally:
                document.close()
            reference = inspect_verified_bytes(path.read_bytes())

            with self.assertRaisesRegex(ValueError, "requires authentication"):
                attest_pymupdf_document_source(path, expected_file=reference)

    def test_page_count_backend_failures_invalid_values_and_zero_close_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.pdf"
            reference = _write_payload(path, _pdf_bytes(1))

            failing = _PageCountErrorDocument()
            with (
                patch(
                    "pymupdf_document_source_attestation.fitz.open",
                    return_value=failing,
                ),
                self.assertRaisesRegex(
                    ValueError,
                    "could not read PDF page count",
                ) as raised,
            ):
                attest_pymupdf_document_source(path, expected_file=reference)
            self.assertIsNotNone(raised.exception.__cause__)
            self.assertTrue(failing.closed)

            for invalid_count in (True, "one", -1):
                document = _Document(page_count=invalid_count)
                with self.subTest(page_count=invalid_count), patch(
                    "pymupdf_document_source_attestation.fitz.open",
                    return_value=document,
                ), self.assertRaises(ValueError):
                    attest_pymupdf_document_source(path, expected_file=reference)
                self.assertTrue(document.closed)

            zero = _Document(page_count=0)
            with patch("pymupdf_document_source_attestation.fitz.open", return_value=zero):
                attestation = attest_pymupdf_document_source(path, expected_file=reference)
            self.assertEqual(attestation.page_count, 0)
            self.assertTrue(zero.closed)

    def test_uses_original_buffer_after_path_changes_before_pymupdf_open(self) -> None:
        first = _pdf_bytes(1)
        second = _pdf_bytes(2)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.pdf"
            first_reference = _write_payload(path, first)
            original_open = fitz.open
            received_streams: list[bytes] = []

            def open_after_replacement(*, stream: bytes, filetype: str) -> fitz.Document:
                received_streams.append(stream)
                path.write_bytes(second)
                return original_open(stream=stream, filetype=filetype)

            with patch(
                "pymupdf_document_source_attestation.fitz.open",
                side_effect=open_after_replacement,
            ):
                attestation = attest_pymupdf_document_source(
                    path,
                    expected_file=first_reference,
                )

            self.assertEqual(received_streams, [first])
            self.assertEqual(attestation.verified_file, first_reference)
            self.assertEqual(attestation.source_id, first_reference.sha256)
            self.assertEqual(attestation.page_count, 1)
            self.assertEqual(path.read_bytes(), second)

    def test_does_not_modify_snapshot_or_produce_artifacts(self) -> None:
        payload = _pdf_bytes(1)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "source.pdf"
            reference = _write_payload(path, payload)

            attest_pymupdf_document_source(path, expected_file=reference)

            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual({entry.name for entry in root.iterdir()}, {"source.pdf"})


if __name__ == "__main__":
    unittest.main()
