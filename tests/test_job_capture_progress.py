"""Tests for capture progress and verified page resume."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

from job_capture_progress import (
    CapturePageState,
    CapturePageStatus,
    CaptureProgress,
    capture_progress_from_dict,
    capture_progress_to_dict,
    initial_capture_progress,
    is_capture_page_resumable,
)


class JobCaptureProgressTests(unittest.TestCase):
    def test_initial_capture_progress_is_pending_and_complete(self) -> None:
        progress = initial_capture_progress(3)

        self.assertEqual(progress.page_count, 3)
        self.assertEqual(
            progress.pages,
            (
                CapturePageState(1, CapturePageStatus.PENDING),
                CapturePageState(2, CapturePageStatus.PENDING),
                CapturePageState(3, CapturePageStatus.PENDING),
            ),
        )

    def test_zero_page_progress_is_valid(self) -> None:
        self.assertEqual(initial_capture_progress(0), CaptureProgress(0, ()))

    def test_models_are_immutable(self) -> None:
        progress = initial_capture_progress(1)

        with self.assertRaises(FrozenInstanceError):
            progress.page_count = 2  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            progress.pages[0].status = CapturePageStatus.COMPLETED  # type: ignore[misc]

    def test_progress_requires_exact_ordered_page_coverage(self) -> None:
        invalid_pages = (
            (),
            (CapturePageState(2, CapturePageStatus.PENDING),),
            (
                CapturePageState(1, CapturePageStatus.PENDING),
                CapturePageState(1, CapturePageStatus.PENDING),
            ),
        )

        for pages in invalid_pages:
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                CaptureProgress(page_count=2, pages=pages)

    def test_completed_page_requires_full_artifact_reference(self) -> None:
        invalid_kwargs: tuple[dict[str, Any], ...] = (
            {},
            {"artifact_path": "raw/page-0001.json"},
            {
                "artifact_path": "raw/page-0001.json",
                "sha256": "a" * 64,
            },
        )

        for kwargs in invalid_kwargs:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                CapturePageState(
                    page_num=1,
                    status=CapturePageStatus.COMPLETED,
                    **kwargs,
                )

    def test_pending_and_failed_pages_reject_artifact_fields(self) -> None:
        for status in (
            CapturePageStatus.PENDING,
            CapturePageStatus.FAILED,
        ):
            with self.subTest(status=status), self.assertRaises(ValueError):
                CapturePageState(
                    page_num=1,
                    status=status,
                    artifact_path="raw/page-0001.json",
                )

    def test_completed_page_rejects_unsafe_artifact_path(self) -> None:
        for path in (
            "/raw/page-0001.json",
            "../page-0001.json",
            r"raw\page-0001.json",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                CapturePageState(
                    page_num=1,
                    status=CapturePageStatus.COMPLETED,
                    artifact_path=path,
                    sha256="a" * 64,
                    size_bytes=1,
                )

    def test_json_round_trip_preserves_progress(self) -> None:
        payload = b"capture-json"
        progress = CaptureProgress(
            page_count=2,
            pages=(
                CapturePageState(
                    page_num=1,
                    status=CapturePageStatus.COMPLETED,
                    artifact_path="raw/page-0001.json",
                    sha256=hashlib.sha256(payload).hexdigest(),
                    size_bytes=len(payload),
                ),
                CapturePageState(
                    page_num=2,
                    status=CapturePageStatus.PENDING,
                ),
            ),
        )

        encoded = json.dumps(capture_progress_to_dict(progress))
        restored = capture_progress_from_dict(json.loads(encoded))

        self.assertEqual(restored, progress)
        self.assertIsInstance(restored.pages, tuple)

    def test_completed_page_is_resumable_when_artifact_matches(self) -> None:
        payload = b"capture-json"

        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact_path = job_dir / "raw" / "page-0001.json"
            artifact_path.parent.mkdir()
            artifact_path.write_bytes(payload)
            page = CapturePageState(
                page_num=1,
                status=CapturePageStatus.COMPLETED,
                artifact_path="raw/page-0001.json",
                sha256=hashlib.sha256(payload).hexdigest(),
                size_bytes=len(payload),
            )

            self.assertTrue(is_capture_page_resumable(page, job_dir))

    def test_completed_page_is_not_resumable_when_artifact_changes(self) -> None:
        original = b"capture-json"

        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir)
            artifact_path = job_dir / "raw" / "page-0001.json"
            artifact_path.parent.mkdir()
            artifact_path.write_bytes(b"changed")
            page = CapturePageState(
                page_num=1,
                status=CapturePageStatus.COMPLETED,
                artifact_path="raw/page-0001.json",
                sha256=hashlib.sha256(original).hexdigest(),
                size_bytes=len(original),
            )

            self.assertFalse(is_capture_page_resumable(page, job_dir))

    def test_non_completed_page_is_not_resumable(self) -> None:
        page = CapturePageState(
            page_num=1,
            status=CapturePageStatus.PENDING,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(is_capture_page_resumable(page, Path(temp_dir)))


if __name__ == "__main__":
    unittest.main()
