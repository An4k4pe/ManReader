"""Tests for JSON persistence of the minimal job manifest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from job_manifest_model import (
    SourceReference,
    WorkspacePaths,
    initial_job_manifest,
)
from job_manifest_store import load_job_manifest, save_job_manifest


class JobManifestStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = initial_job_manifest(
            job_id="job-test-001",
            page_count=3,
            source=SourceReference(
                sha256="a" * 64,
                size_bytes=1234,
                original_name="manual.pdf",
            ),
            workspace=WorkspacePaths(source_snapshot="source/manual.pdf"),
        )

    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"

            save_job_manifest(self.manifest, path)
            restored = load_job_manifest(path)

        self.assertEqual(restored, self.manifest)

    def test_saved_json_is_utf8_readable_and_ends_with_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"

            save_job_manifest(self.manifest, path)
            serialized = path.read_text(encoding="utf-8")

        self.assertTrue(serialized.endswith("\n"))
        decoded = json.loads(serialized)
        self.assertEqual(decoded["job_id"], "job-test-001")
        self.assertEqual(decoded["source"]["original_name"], "manual.pdf")

    def test_saved_json_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_path = Path(temp_dir) / "first.json"
            second_path = Path(temp_dir) / "second.json"

            save_job_manifest(self.manifest, first_path)
            save_job_manifest(self.manifest, second_path)

            first = first_path.read_bytes()
            second = second_path.read_bytes()

        self.assertEqual(first, second)

    def test_save_does_not_create_missing_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing" / "manifest.json"

            with self.assertRaises(FileNotFoundError):
                save_job_manifest(self.manifest, path)

            self.assertFalse(path.parent.exists())

    def test_load_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid job manifest JSON"):
                load_job_manifest(path)

    def test_load_rejects_non_object_json_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "root must be a JSON object"):
                load_job_manifest(path)

    def test_load_rejects_invalid_manifest_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "job_id": 123,
                        "source": {
                            "sha256": "a" * 64,
                            "size_bytes": 1234,
                            "original_name": "manual.pdf",
                        },
                        "workspace": {
                            "source_snapshot": "source/manual.pdf",
                            "raw_dir": "raw",
                            "manifest_path": "manifest.json",
                        },
                        "phases": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_job_manifest(path)


if __name__ == "__main__":
    unittest.main()
