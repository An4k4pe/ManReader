"""Binding of verified PDF bytes opened by PyMuPDF and pdfplumber."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import fitz
from pdfplumber.pdf import PDF

from verified_file_model import VerifiedFileReference, inspect_verified_bytes


@dataclass(frozen=True, slots=True)
class BoundDocumentSource:
    """Two backend documents opened from the same verified byte buffer."""

    fitz_document: fitz.Document
    plumber_pdf: PDF


def bind_pymupdf_pdfplumber_document_source(
    snapshot_path: Path,
    *,
    expected_file: VerifiedFileReference,
) -> BoundDocumentSource:
    """Open both PDF backends from one verified, in-memory source snapshot."""

    if not isinstance(snapshot_path, Path):
        raise ValueError("snapshot_path must be a Path")
    if not isinstance(expected_file, VerifiedFileReference):
        raise ValueError("expected_file must be a VerifiedFileReference")

    data = snapshot_path.read_bytes()
    observed = inspect_verified_bytes(data)
    if observed.sha256 != expected_file.sha256:
        raise ValueError("snapshot digest does not match expected file")
    if observed.size_bytes != expected_file.size_bytes:
        raise ValueError("snapshot size does not match expected file")

    try:
        fitz_document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("PyMuPDF could not open verified PDF bytes") from exc

    try:
        plumber_pdf = PDF.open(io.BytesIO(data))
    except Exception as exc:
        fitz_document.close()
        raise ValueError("pdfplumber could not open verified PDF bytes") from exc

    if fitz_document.page_count != len(plumber_pdf.pages):
        fitz_document.close()
        plumber_pdf.close()
        raise ValueError("PyMuPDF and pdfplumber page counts do not match")

    return BoundDocumentSource(
        fitz_document=fitz_document,
        plumber_pdf=plumber_pdf,
    )
