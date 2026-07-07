"""Tests for immutable capture-page completion."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from job_capture_page_update import complete_capture_page
from job_capture_progress import CapturePageStatus, is_capture_page_resumable
from job_manifest_model import SourceReference, WorkspacePaths, initial_job_manifest


class JobCapturePageUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = initial_job_manifest(
            job_id="job-test-001",
            source=SourceReference(
                sha256="a" * 64,
                size_bytes=1234,
                original_name="manual.pdf",
            ),
            workspace=WorkspacePaths(source_snapshot="source/manual.pdf"),
            page_count=3,
        )

    def test_complete_capture_page_returns_new_manifest(self) -> None:
        payload = b'{"page_id":"p0002"}'

        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0002.json"
            artifact.parent.mkdir()
            artifact.write_bytes(payload)

            updated = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )

        self.assertIsNot(updated, self.manifest)
        self.assertEqual(
            self.manifest.capture_progress.pages[1].status,
            CapturePageStatus.PENDING,
        )

        completed = updated.capture_progress.pages[1]
        self.assertEqual(completed.status, CapturePageStatus.COMPLETED)
        self.assertEqual(completed.artifact_path, "raw/page-0002.json")
        self.assertEqual(completed.sha256, hashlib.sha256(payload).hexdigest())
        self.assertEqual(completed.size_bytes, len(payload))

    def test_completion_preserves_other_page_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0002.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"content")

            updated = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )

        self.assertEqual(
            tuple(page.status for page in updated.capture_progress.pages),
            (
                CapturePageStatus.PENDING,
                CapturePageStatus.COMPLETED,
                CapturePageStatus.PENDING,
            ),
        )

    def test_completed_page_is_immediately_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0001.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"content")

            updated = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

            self.assertTrue(
                is_capture_page_resumable(
                    updated.capture_progress.pages[0],
                    job_dir,
                )
            )

    def test_completion_rejects_missing_artifact(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertRaises(FileNotFoundError),
        ):
            complete_capture_page(
                self.manifest,
                job_dir=Path(temp_dir),
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

    def test_completion_rejects_artifact_outside_raw_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "other" / "page-0001.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"content")

            with self.assertRaisesRegex(ValueError, "below workspace raw_dir"):
                complete_capture_page(
                    self.manifest,
                    job_dir=job_dir,
                    page_num=1,
                    artifact_path="other/page-0001.json",
                )

    def test_completion_rejects_raw_directory_itself_as_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            (job_dir / "raw").mkdir()

            with self.assertRaisesRegex(ValueError, "below workspace raw_dir"):
                complete_capture_page(
                    self.manifest,
                    job_dir=job_dir,
                    page_num=1,
                    artifact_path="raw",
                )

    def test_completion_rejects_page_outside_manifest_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)

            for page_num in (0, 4):
                with self.subTest(page_num=page_num), self.assertRaises(ValueError):
                    complete_capture_page(
                        self.manifest,
                        job_dir=job_dir,
                        page_num=page_num,
                        artifact_path="raw/page.json",
                    )

    def test_completion_rejects_overwrite_of_completed_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0001.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"first")

            completed = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

            artifact.write_bytes(b"second")

            with self.assertRaisesRegex(ValueError, "already completed"):
                complete_capture_page(
                    completed,
                    job_dir=job_dir,
                    page_num=1,
                    artifact_path="raw/page-0001.json",
                )


if __name__ == "__main__":
    unittest.main()
