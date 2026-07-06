"""Tests for coordinated initialization of a minimal ManReader job."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from job_initializer import initialize_job
from job_manifest_model import SourceReference, WorkspacePaths
from job_manifest_store import load_job_manifest


class JobInitializerTests(unittest.TestCase):
    def test_initialize_job_creates_manifest_and_verified_source_snapshot(self) -> None:
        payload = b"synthetic-pdf-content"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            job_dir = root / "jobs" / "job-test-001"
            job_dir.parent.mkdir()
            source_path.write_bytes(payload)

            manifest = initialize_job(
                source_path=source_path,
                job_dir=job_dir,
                job_id="job-test-001",
            )

            snapshot_path = job_dir / "source" / "manual.pdf"
            self.assertEqual(snapshot_path.read_bytes(), payload)
            self.assertEqual(load_job_manifest(job_dir / "manifest.json"), manifest)
            self.assertEqual(manifest.source.original_name, "manual.pdf")
            self.assertEqual(manifest.workspace.source_snapshot, "source/manual.pdf")
            self.assertTrue((job_dir / "raw").is_dir())

    def test_initialize_job_supports_explicit_workspace_paths(self) -> None:
        workspace = WorkspacePaths(
            source_snapshot="inputs/book.pdf",
            raw_dir="artifacts/raw",
            manifest_path="metadata/manifest.json",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            job_dir = root / "job-test-002"
            source_path.write_bytes(b"content")

            manifest = initialize_job(
                source_path=source_path,
                job_dir=job_dir,
                job_id="job-test-002",
                workspace=workspace,
            )

            self.assertEqual((job_dir / "inputs" / "book.pdf").read_bytes(), b"content")
            self.assertTrue((job_dir / "artifacts" / "raw").is_dir())
            self.assertEqual(
                load_job_manifest(job_dir / "metadata" / "manifest.json"),
                manifest,
            )

    def test_initialize_job_rejects_missing_source_without_creating_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job_dir = root / "job-test-001"

            with self.assertRaises(FileNotFoundError):
                initialize_job(
                    source_path=root / "missing.pdf",
                    job_dir=job_dir,
                    job_id="job-test-001",
                )

            self.assertFalse(job_dir.exists())

    def test_initialize_job_rejects_existing_job_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            job_dir = root / "job-test-001"
            source_path.write_bytes(b"content")
            job_dir.mkdir()
            marker = job_dir / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                initialize_job(
                    source_path=source_path,
                    job_dir=job_dir,
                    job_id="job-test-001",
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertEqual(tuple(job_dir.iterdir()), (marker,))

    def test_initialize_job_detects_source_change_during_copy(self) -> None:
        expected = SourceReference(
            sha256="a" * 64,
            size_bytes=7,
            original_name="manual.pdf",
        )
        copied = SourceReference(
            sha256="b" * 64,
            size_bytes=7,
            original_name="manual.pdf",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "manual.pdf"
            job_dir = root / "job-test-001"
            source_path.write_bytes(b"content")

            with (
                patch("job_initializer.inspect_source_file", return_value=expected),
                patch(
                    "job_initializer.materialize_source_snapshot",
                    return_value=copied,
                ),
                self.assertRaisesRegex(ValueError, "does not match"),
            ):
                initialize_job(
                    source_path=source_path,
                    job_dir=job_dir,
                    job_id="job-test-001",
                )


if __name__ == "__main__":
    unittest.main()
