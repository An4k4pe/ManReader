"""Tests for single-page PyMuPDF job capture."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import fitz

from job_capture_page_runner import capture_job_page
from job_capture_progress import CapturePageStatus
from job_initializer import initialize_job
from job_manifest_store import load_job_manifest


class JobCapturePageRunnerTests(unittest.TestCase):
    def _create_job(self, root: Path, *, page_count: int = 2) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        for page_index in range(page_count):
            page = document.new_page(width=300, height=400)
            page.insert_text((40, 60), f"Page {page_index + 1}")
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-001"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-001",
            page_count=page_count,
        )
        return job_dir, job_dir / "manifest.json"

    def test_capture_job_page_writes_raw_capture_and_persists_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))

            result = capture_job_page(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
            )

            artifact_path = job_dir / result.artifact_path
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            reloaded = load_job_manifest(manifest_path)

        self.assertFalse(result.skipped)
        self.assertEqual(result.artifact_path, "raw/page-0001.json")
        self.assertEqual(payload["page_index"], 0)
        self.assertEqual(payload["page_id"], "page:0001")
        self.assertEqual(payload["source_id"], reloaded.source.sha256)
        self.assertEqual(
            reloaded.capture_progress.pages[0].status,
            CapturePageStatus.COMPLETED,
        )
        self.assertEqual(result.manifest, reloaded)

    def test_capture_job_page_skips_verified_completed_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))

            first = capture_job_page(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
            )
            artifact_path = job_dir / first.artifact_path
            before = artifact_path.read_bytes()

            second = capture_job_page(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
            )

            after = artifact_path.read_bytes()

        self.assertTrue(second.skipped)
        self.assertEqual(second.artifact_path, first.artifact_path)
        self.assertEqual(after, before)

    def test_capture_job_page_rejects_invalid_completed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))
            result = capture_job_page(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
            )
            (job_dir / result.artifact_path).write_text("corrupted", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "explicit reset"):
                capture_job_page(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                )

    def test_capture_job_page_rejects_orphan_artifact_for_pending_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))
            orphan = job_dir / "raw" / "page-0001.json"
            orphan.write_text("orphan", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                capture_job_page(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                )

            self.assertEqual(orphan.read_text(encoding="utf-8"), "orphan")

    def test_capture_job_page_rejects_modified_source_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))
            snapshot = job_dir / "source" / "source.pdf"
            snapshot.write_bytes(b"not-the-original-pdf")

            with self.assertRaisesRegex(ValueError, "source snapshot"):
                capture_job_page(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                )

            self.assertFalse((job_dir / "raw" / "page-0001.json").exists())

    def test_capture_job_page_rejects_page_outside_manifest_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir))

            for page_num in (0, 3):
                with self.subTest(page_num=page_num), self.assertRaises(ValueError):
                    capture_job_page(
                        job_dir=job_dir,
                        manifest_path=manifest_path,
                        page_num=page_num,
                    )

    def test_capture_job_page_rejects_manifest_page_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir, manifest_path = self._create_job(Path(temp_dir), page_count=1)
            manifest = load_job_manifest(manifest_path)

            source_path = job_dir / "source" / "source.pdf"
            document = fitz.open()
            document.new_page()
            document.new_page()
            replacement = Path(temp_dir) / "replacement.pdf"
            document.save(replacement)
            document.close()
            source_path.write_bytes(replacement.read_bytes())

            from job_manifest_model import SourceReference
            from job_manifest_store import save_job_manifest
            from verified_file_model import inspect_verified_file

            verified = inspect_verified_file(source_path)
            changed_manifest = manifest.__class__(
                schema_version=manifest.schema_version,
                job_id=manifest.job_id,
                source=SourceReference(
                    sha256=verified.sha256,
                    size_bytes=verified.size_bytes,
                    original_name=manifest.source.original_name,
                ),
                workspace=manifest.workspace,
                capture_progress=manifest.capture_progress,
            )
            save_job_manifest(changed_manifest, manifest_path)

            with self.assertRaisesRegex(ValueError, "page count"):
                capture_job_page(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                )


if __name__ == "__main__":
    unittest.main()
