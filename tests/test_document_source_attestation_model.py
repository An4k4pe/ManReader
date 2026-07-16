"""Tests for the pure document-source attestation model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from typing import cast

from document_source_attestation_model import (
    DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
    DocumentSourceAttestation,
)
from verified_file_model import VerifiedFileReference


def _verified_file() -> VerifiedFileReference:
    return VerifiedFileReference(sha256="a" * 64, size_bytes=12)


class DocumentSourceAttestationModelTests(unittest.TestCase):
    def test_valid_construction_equality_immutability_and_slots(self) -> None:
        attestation = DocumentSourceAttestation(
            schema_version=DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
            verified_file=_verified_file(),
            source_id="independent-source-id",
            page_count=2,
        )

        self.assertEqual(
            attestation,
            DocumentSourceAttestation(
                schema_version=DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION,
                verified_file=_verified_file(),
                source_id="independent-source-id",
                page_count=2,
            ),
        )
        self.assertTrue(hasattr(DocumentSourceAttestation, "__slots__"))
        with self.assertRaises(FrozenInstanceError):
            attestation.page_count = 3  # type: ignore[misc]

    def test_page_count_zero_and_independent_source_id_are_valid(self) -> None:
        attestation = DocumentSourceAttestation(
            schema_version="1.0",
            verified_file=_verified_file(),
            source_id="not-the-digest",
            page_count=0,
        )

        self.assertEqual(attestation.page_count, 0)
        self.assertNotEqual(attestation.source_id, attestation.verified_file.sha256)

    def test_rejects_invalid_contract_values(self) -> None:
        invalid_values = (
            ("2.0", _verified_file(), "source", 1, "schema_version"),
            ("1.0", cast(VerifiedFileReference, object()), "source", 1, "verified_file"),
            ("1.0", _verified_file(), cast(str, 1), 1, "source_id"),
            ("1.0", _verified_file(), "", 1, "source_id"),
            ("1.0", _verified_file(), "source", cast(int, True), "page_count"),
            ("1.0", _verified_file(), "source", cast(int, 1.5), "page_count"),
            ("1.0", _verified_file(), "source", -1, "page_count"),
        )

        for schema, verified_file, source_id, page_count, field_name in invalid_values:
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError,
                field_name,
            ):
                DocumentSourceAttestation(
                    schema_version=schema,
                    verified_file=verified_file,
                    source_id=source_id,
                    page_count=page_count,
                )


if __name__ == "__main__":
    unittest.main()
