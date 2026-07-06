"""Tests for generic verified-file references and hashing helpers."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from verified_file_model import (
    VerifiedFileReference,
    inspect_verified_file,
    verify_file,
)


class VerifiedFileModelTests(unittest.TestCase):
    def test_reference_is_immutable(self) -> None:
        reference = VerifiedFileReference(sha256="a" * 64, size_bytes=1)

        with self.assertRaises(FrozenInstanceError):
            reference.size_bytes = 2  # type: ignore[misc]

    def test_reference_rejects_invalid_digest_or_size(self) -> None:
        invalid_values = (
            ("a" * 63, 0),
            ("A" * 64, 0),
            ("g" * 64, 0),
            ("a" * 64, -1),
        )

        for sha256, size_bytes in invalid_values:
            with self.subTest(
                sha256=sha256,
                size_bytes=size_bytes,
            ), self.assertRaises(ValueError):
                VerifiedFileReference(sha256=sha256, size_bytes=size_bytes)

    def test_inspect_verified_file_returns_hash_and_size(self) -> None:
        payload = b"verified-content"

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(payload)

            reference = inspect_verified_file(path)

        self.assertEqual(reference.sha256, hashlib.sha256(payload).hexdigest())
        self.assertEqual(reference.size_bytes, len(payload))

    def test_inspect_verified_file_rejects_missing_file(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertRaises(FileNotFoundError),
        ):
            inspect_verified_file(Path(temp_dir) / "missing.bin")

    def test_verify_file_accepts_matching_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(b"content")
            reference = inspect_verified_file(path)

            self.assertTrue(verify_file(path, reference))

    def test_verify_file_rejects_changed_or_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(b"original")
            reference = inspect_verified_file(path)
            path.write_bytes(b"changed")

            self.assertFalse(verify_file(path, reference))
            self.assertFalse(verify_file(path.with_name("missing.bin"), reference))


if __name__ == "__main__":
    unittest.main()
