"""Tests for verified capture resume planning."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from job_capture_page_update import complete_capture_page
from job_capture_progress import (
    CapturePageState,
    CapturePageStatus,
    CaptureProgress,
)
from job_capture_resume import CaptureResumePlan, build_capture_resume_plan
from job_manifest_model import (
    SourceReference,
    WorkspacePaths,
    initial_job_manifest,
)


class JobCaptureResumeTests(unittest.TestCase):
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

    def test_all_pending_pages_require_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_capture_resume_plan(
                self.manifest,
                job_dir=Path(temp_dir),
            )

        self.assertEqual(
            plan,
            CaptureResumePlan(
                resumable_pages=(),
                pages_to_capture=(1, 2, 3),
                invalid_completed_pages=(),
            ),
        )

    def test_verified_completed_page_is_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0002.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"capture")

            manifest = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=2,
                artifact_path="raw/page-0002.json",
            )
            plan = build_capture_resume_plan(manifest, job_dir=job_dir)

        self.assertEqual(plan.resumable_pages, (2,))
        self.assertEqual(plan.pages_to_capture, (1, 3))
        self.assertEqual(plan.invalid_completed_pages, ())

    def test_missing_completed_artifact_requires_recapture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0001.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"capture")

            manifest = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=1,
                artifact_path="raw/page-0001.json",
            )
            artifact.unlink()

            plan = build_capture_resume_plan(manifest, job_dir=job_dir)

        self.assertEqual(plan.resumable_pages, ())
        self.assertEqual(plan.pages_to_capture, (1, 2, 3))
        self.assertEqual(plan.invalid_completed_pages, (1,))

    def test_corrupted_completed_artifact_requires_recapture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact = job_dir / "raw" / "page-0003.json"
            artifact.parent.mkdir()
            artifact.write_bytes(b"original")

            manifest = complete_capture_page(
                self.manifest,
                job_dir=job_dir,
                page_num=3,
                artifact_path="raw/page-0003.json",
            )
            artifact.write_bytes(b"changed")

            plan = build_capture_resume_plan(manifest, job_dir=job_dir)

        self.assertEqual(plan.resumable_pages, ())
        self.assertEqual(plan.pages_to_capture, (1, 2, 3))
        self.assertEqual(plan.invalid_completed_pages, (3,))

    def test_failed_page_requires_capture(self) -> None:
        progress = CaptureProgress(
            page_count=3,
            pages=(
                CapturePageState(1, CapturePageStatus.PENDING),
                CapturePageState(2, CapturePageStatus.FAILED),
                CapturePageState(3, CapturePageStatus.PENDING),
            ),
        )
        manifest = self.manifest.__class__(
            schema_version=self.manifest.schema_version,
            job_id=self.manifest.job_id,
            source=self.manifest.source,
            workspace=self.manifest.workspace,
            phases=self.manifest.phases,
            capture_progress=progress,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_capture_resume_plan(manifest, job_dir=Path(temp_dir))

        self.assertEqual(plan.pages_to_capture, (1, 2, 3))
        self.assertEqual(plan.invalid_completed_pages, ())

    def test_resume_plan_preserves_page_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)

            for page_num in (1, 3):
                artifact = job_dir / "raw" / f"page-{page_num:04d}.json"
                artifact.parent.mkdir(exist_ok=True)
                artifact.write_bytes(f"page-{page_num}".encode())

                self.manifest = complete_capture_page(
                    self.manifest,
                    job_dir=job_dir,
                    page_num=page_num,
                    artifact_path=f"raw/page-{page_num:04d}.json",
                )

            plan = build_capture_resume_plan(self.manifest, job_dir=job_dir)

        self.assertEqual(plan.resumable_pages, (1, 3))
        self.assertEqual(plan.pages_to_capture, (2,))
        self.assertEqual(plan.invalid_completed_pages, ())


if __name__ == "__main__":
    unittest.main()
