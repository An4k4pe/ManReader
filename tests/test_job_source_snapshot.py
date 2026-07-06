"""Tests for verified ManReader source snapshot materialization."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from job_source_snapshot import (
    materialize_source_snapshot,
    verify_source_snapshot,
)


class JobSourceSnapshotTests(unittest.TestCase):
    def test_materialize_source_snapshot_copies_bytes_and_builds_reference(self) -> None:
        payload = b"synthetic-pdf-content\x00\x01"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            destination_path = root / "source" / "manual.pdf"
            destination_path.parent.mkdir()

            source_path.write_bytes(payload)
            reference = materialize_source_snapshot(source_path, destination_path)

            self.assertEqual(destination_path.read_bytes(), payload)
            self.assertEqual(reference.sha256, hashlib.sha256(payload).hexdigest())
            self.assertEqual(reference.size_bytes, len(payload))
            self.assertEqual(reference.original_name, "manual.pdf")

    def test_materialized_snapshot_verifies_against_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            destination_path = root / "source" / "manual.pdf"
            destination_path.parent.mkdir()
            source_path.write_bytes(b"content")

            reference = materialize_source_snapshot(source_path, destination_path)

            self.assertTrue(verify_source_snapshot(destination_path, reference))

    def test_verification_fails_after_snapshot_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            destination_path = root / "source" / "manual.pdf"
            destination_path.parent.mkdir()
            source_path.write_bytes(b"original")

            reference = materialize_source_snapshot(source_path, destination_path)
            destination_path.write_bytes(b"changed")

            self.assertFalse(verify_source_snapshot(destination_path, reference))

    def test_verification_fails_when_snapshot_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.pdf"
            source_path = Path(temp_dir) / "manual.pdf"
            source_path.write_bytes(b"content")
            reference = materialize_source_snapshot(
                source_path,
                Path(temp_dir) / "snapshot.pdf",
            )

            self.assertFalse(verify_source_snapshot(missing_path, reference))

    def test_materialize_source_snapshot_rejects_missing_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            destination_path = root / "source" / "manual.pdf"
            destination_path.parent.mkdir()

            with self.assertRaises(FileNotFoundError):
                materialize_source_snapshot(root / "missing.pdf", destination_path)

            self.assertFalse(destination_path.exists())

    def test_materialize_source_snapshot_rejects_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            destination_path = root / "source" / "manual.pdf"
            destination_path.parent.mkdir()
            source_path.write_bytes(b"new-content")
            destination_path.write_bytes(b"existing-content")

            with self.assertRaises(FileExistsError):
                materialize_source_snapshot(source_path, destination_path)

            self.assertEqual(destination_path.read_bytes(), b"existing-content")

    def test_materialize_source_snapshot_requires_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            destination_path = root / "missing" / "manual.pdf"
            source_path.write_bytes(b"content")

            with self.assertRaises(FileNotFoundError):
                materialize_source_snapshot(source_path, destination_path)

            self.assertFalse(destination_path.exists())


if __name__ == "__main__":
    unittest.main()
