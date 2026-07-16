"""Pure technical attestation for one verified document byte sequence."""

from __future__ import annotations

from dataclasses import dataclass

from verified_file_model import VerifiedFileReference

DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class DocumentSourceAttestation:
    """Immutable local verification result for bytes and their page count.

    Direct construction validates only the data shape. Provenance that the
    count was read from the verified bytes is guaranteed by the canonical
    producer, not by this model. This is neither a signature, editorial
    authenticity claim, nor an external certification.
    """

    schema_version: str
    verified_file: VerifiedFileReference
    source_id: str
    page_count: int

    def __post_init__(self) -> None:
        if self.schema_version != DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION:
            raise ValueError("schema_version is not supported")
        if not isinstance(self.verified_file, VerifiedFileReference):
            raise ValueError("verified_file must be a VerifiedFileReference")
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if isinstance(self.page_count, bool) or not isinstance(self.page_count, int):
            raise ValueError("page_count must be an int")
        if self.page_count < 0:
            raise ValueError("page_count must be non-negative")
