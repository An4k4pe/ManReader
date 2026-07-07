"""Tests for derived capture-phase summaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from job_capture_page_update import complete_capture_page
from job_capture_phase_summary import (
    CapturePhaseSummary,
    CaptureProgressStatus,
    derive_capture_phase_summary,
)
from job_manifest_model import SourceReference, WorkspacePaths, initial_job_manifest


class JobCapturePhaseSummaryTests(unittest.TestCase):
    def _manifest(self, page_count: int = 3):
        return initial_job_manifest(
            job_id="job-test-001",
            source=SourceReference(
                sha256="a" * 64,
                size_bytes=1234,
                original_name="manual.pdf",
            ),
            workspace=WorkspacePaths(source_snapshot="source/manual.pdf"),
            page_count=page_count,
        )

    def test_zero_page_capture_is_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = derive_capture_phase_summary(
                self._manifest(page_count=0),
                job_dir=Path(temp_dir),
            )
        self.assertEqual(
            summary,
            CapturePhaseSummary(
                progress_status=CaptureProgressStatus.COMPLETED,
                resumable_pages=(),
                pages_to_capture=(),
                invalid_completed_pages=(),
            ),
        )

    def test_all_pending_capture_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = derive_capture_phase_summary(
                self._manifest(),
                job_dir=Path(temp_dir),
            )
        self.assertEqual(summary.progress_status, CaptureProgressStatus.PENDING)
        self.assertEqual(summary.pages_to_capture, (1, 2, 3))

    def test_some_verified_pages_make_capture_partial(self) -> None:
        manifest = self._manifest()
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0002.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"capture")
            manifest = complete_capture_page(
                manifest,
                job_dir=job_dir,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )
            summary = derive_capture_phase_summary(manifest, job_dir=job_dir)
        self.assertEqual(summary.progress_status, CaptureProgressStatus.PARTIAL)
        self.assertEqual(summary.resumable_pages, (2,))
        self.assertEqual(summary.pages_to_capture, (1, 3))

    def test_all_verified_pages_make_capture_completed(self) -> None:
        manifest = self._manifest(page_count=2)
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            for page_num in (1, 2):
                relative = f"raw/page-{page_num:04d}.json"
                artifact = job_dir / relative
                artifact.parent.mkdir(exist_ok=True)
                artifact.write_bytes(f"page-{page_num}".encode())
                manifest = complete_capture_page(
                    manifest,
                    job_dir=job_dir,
                    page_num=page_num,
                    artifact_path=relative,
                )
            summary = derive_capture_phase_summary(manifest, job_dir=job_dir)
        self.assertEqual(summary.progress_status, CaptureProgressStatus.COMPLETED)
        self.assertEqual(summary.resumable_pages, (1, 2))
        self.assertEqual(summary.pages_to_capture, ())

    def test_invalid_completed_artifact_makes_capture_invalid(self) -> None:
        manifest = self._manifest()
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0001.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"original")
            manifest = complete_capture_page(
                manifest,
                job_dir=job_dir,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )
            artifact.write_bytes(b"changed")
            summary = derive_capture_phase_summary(manifest, job_dir=job_dir)
        self.assertEqual(summary.progress_status, CaptureProgressStatus.INVALID)
        self.assertEqual(summary.invalid_completed_pages, (1,))

    def test_invalid_takes_precedence_over_partial(self) -> None:
        manifest = self._manifest()
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)

            valid = job_dir / "raw" / "page-0001.json"
            valid.parent.mkdir()
            valid.write_bytes(b"valid")
            manifest = complete_capture_page(
                manifest,
                job_dir=job_dir,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )

            invalid = job_dir / "raw" / "page-0002.json"
            invalid.write_bytes(b"original")
            manifest = complete_capture_page(
                manifest,
                job_dir=job_dir,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )
            invalid.unlink()

            summary = derive_capture_phase_summary(manifest, job_dir=job_dir)

        self.assertEqual(summary.progress_status, CaptureProgressStatus.INVALID)
        self.assertEqual(summary.resumable_pages, (1,))
        self.assertEqual(summary.pages_to_capture, (2, 3))
        self.assertEqual(summary.invalid_completed_pages, (2,))


if __name__ == "__main__":
    unittest.main()
