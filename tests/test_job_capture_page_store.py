"""Tests for persisted capture-page completion."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from job_capture_page_store import complete_capture_page_in_workspace
from job_capture_progress import CapturePageStatus
from job_manifest_model import SourceReference, WorkspacePaths, initial_job_manifest
from job_manifest_store import load_job_manifest, save_job_manifest


class JobCapturePageStoreTests(unittest.TestCase):
    def _manifest(self, *, manifest_path: str = "manifest.json"):
        return initial_job_manifest(
            job_id="job-test-001",
            source=SourceReference(
                sha256="a" * 64,
                size_bytes=1234,
                original_name="manual.pdf",
            ),
            workspace=WorkspacePaths(
                source_snapshot="source/manual.pdf",
                manifest_path=manifest_path,
            ),
            page_count=2,
        )

    def test_completion_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            manifest_path = job_dir / "manifest.json"
            artifact_path = job_dir / "raw" / "page-0001.json"
            artifact_path.parent.mkdir()
            artifact_path.write_bytes(b"capture")
            save_job_manifest(self._manifest(), manifest_path)

            updated = complete_capture_page_in_workspace(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

            reloaded = load_job_manifest(manifest_path)

        self.assertEqual(reloaded, updated)
        self.assertEqual(
            reloaded.capture_progress.pages[0].status,
            CapturePageStatus.COMPLETED,
        )

    def test_completion_preserves_other_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            manifest_path = job_dir / "manifest.json"
            artifact_path = job_dir / "raw" / "page-0002.json"
            artifact_path.parent.mkdir()
            artifact_path.write_bytes(b"capture")
            save_job_manifest(self._manifest(), manifest_path)

            updated = complete_capture_page_in_workspace(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )

        self.assertEqual(
            tuple(page.status for page in updated.capture_progress.pages),
            (
                CapturePageStatus.PENDING,
                CapturePageStatus.COMPLETED,
            ),
        )

    def test_missing_artifact_does_not_change_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            manifest_path = job_dir / "manifest.json"
            original = self._manifest()
            save_job_manifest(original, manifest_path)

            with self.assertRaises(FileNotFoundError):
                complete_capture_page_in_workspace(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    artifact_path="raw/page-0001.json",
                )

            self.assertEqual(load_job_manifest(manifest_path), original)

    def test_manifest_path_must_match_declared_workspace_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            actual_path = job_dir / "other.json"
            manifest = self._manifest(manifest_path="metadata/manifest.json")
            save_job_manifest(manifest, actual_path)

            with self.assertRaisesRegex(ValueError, "does not match"):
                complete_capture_page_in_workspace(
                    job_dir=job_dir,
                    manifest_path=actual_path,
                    page_num=1,
                    artifact_path="raw/page-0001.json",
                )

    def test_nested_declared_manifest_path_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            manifest_path = job_dir / "metadata" / "manifest.json"
            manifest_path.parent.mkdir()
            artifact_path = job_dir / "raw" / "page-0001.json"
            artifact_path.parent.mkdir()
            artifact_path.write_bytes(b"capture")
            save_job_manifest(
                self._manifest(manifest_path="metadata/manifest.json"),
                manifest_path,
            )

            updated = complete_capture_page_in_workspace(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

        self.assertEqual(
            updated.capture_progress.pages[0].status,
            CapturePageStatus.COMPLETED,
        )


if __name__ == "__main__":
    unittest.main()
