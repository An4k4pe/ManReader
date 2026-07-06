"""Tests for minimal ManReader job workspace creation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from job_manifest_model import (
    SourceReference,
    WorkspacePaths,
    initial_job_manifest,
)
from job_manifest_store import load_job_manifest
from job_workspace import create_job_workspace


class JobWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = initial_job_manifest(
            job_id="job-test-001",
            source=SourceReference(
                sha256="a" * 64,
                size_bytes=1234,
                original_name="manual.pdf",
            ),
            workspace=WorkspacePaths(source_snapshot="source/manual.pdf"),
        )

    def test_create_job_workspace_builds_minimal_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "job-test-001"

            manifest_path = create_job_workspace(self.manifest, job_dir)

            self.assertEqual(manifest_path, job_dir / "manifest.json")
            self.assertTrue(job_dir.is_dir())
            self.assertTrue((job_dir / "source").is_dir())
            self.assertTrue((job_dir / "raw").is_dir())
            self.assertTrue(manifest_path.is_file())

    def test_create_job_workspace_does_not_materialize_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "job-test-001"

            create_job_workspace(self.manifest, job_dir)

            self.assertFalse((job_dir / "source" / "manual.pdf").exists())

    def test_created_manifest_round_trips_through_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "job-test-001"

            manifest_path = create_job_workspace(self.manifest, job_dir)

            self.assertEqual(load_job_manifest(manifest_path), self.manifest)

    def test_create_job_workspace_rejects_existing_job_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "job-test-001"
            job_dir.mkdir()
            marker = job_dir / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                create_job_workspace(self.manifest, job_dir)

            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertEqual(tuple(job_dir.iterdir()), (marker,))

    def test_create_job_workspace_requires_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "missing-root" / "job-test-001"

            with self.assertRaises(FileNotFoundError):
                create_job_workspace(self.manifest, job_dir)

            self.assertFalse(job_dir.exists())

    def test_create_job_workspace_supports_nested_declared_paths(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-002",
            source=self.manifest.source,
            workspace=WorkspacePaths(
                source_snapshot="inputs/source/manual.pdf",
                raw_dir="artifacts/raw/capture",
                manifest_path="metadata/job/manifest.json",
            ),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "job-test-002"

            manifest_path = create_job_workspace(manifest, job_dir)

            self.assertTrue((job_dir / "inputs" / "source").is_dir())
            self.assertTrue((job_dir / "artifacts" / "raw" / "capture").is_dir())
            self.assertEqual(
                manifest_path,
                job_dir / "metadata" / "job" / "manifest.json",
            )
            self.assertTrue(manifest_path.is_file())


if __name__ == "__main__":
    unittest.main()
