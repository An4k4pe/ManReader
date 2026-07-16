"""PyMuPDF producer for verified transient document-source attestations."""

from __future__ import annotations

from pathlib import Path

import fitz

from document_source_attestation_model import (
    DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
    DocumentSourceAttestation,
)
from verified_file_model import VerifiedFileReference, inspect_verified_bytes


def attest_pymupdf_document_source(
    snapshot_path: Path,
    *,
    expected_file: VerifiedFileReference,
) -> DocumentSourceAttestation:
    """Attest one PDF buffer after verifying the bytes read from its snapshot path."""

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
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("PyMuPDF could not open verified PDF bytes") from exc

    try:
        if document.needs_pass:
            raise ValueError("PDF requires authentication")
        try:
            page_count = document.page_count
        except Exception as exc:
            raise ValueError("PyMuPDF could not read PDF page count") from exc
        if isinstance(page_count, bool) or not isinstance(page_count, int):
            raise ValueError("page_count must be an int")
        if page_count < 0:
            raise ValueError("page_count must be non-negative")
    finally:
        document.close()

    return DocumentSourceAttestation(
        schema_version=DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
        verified_file=observed,
        source_id=observed.sha256,
        page_count=page_count,
    )
