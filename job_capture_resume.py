"""Capture resume planning for a ManReader job."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from job_capture_progress import CapturePageStatus, is_capture_page_resumable
from job_manifest_model import JobManifest


@dataclass(frozen=True, slots=True)
class CaptureResumePlan:
    """Verified page selection for resuming capture."""

    resumable_pages: tuple[int, ...]
    pages_to_capture: tuple[int, ...]
    invalid_completed_pages: tuple[int, ...]


def build_capture_resume_plan(
    manifest: JobManifest,
    *,
    job_dir: Path,
) -> CaptureResumePlan:
    """Classify every capture page using manifest state and artifact verification."""

    resumable_pages: list[int] = []
    pages_to_capture: list[int] = []
    invalid_completed_pages: list[int] = []

    for page in manifest.capture_progress.pages:
        if page.status is CapturePageStatus.COMPLETED:
            if is_capture_page_resumable(page, job_dir):
                resumable_pages.append(page.page_num)
            else:
                invalid_completed_pages.append(page.page_num)
            continue

        pages_to_capture.append(page.page_num)

    return CaptureResumePlan(
        resumable_pages=tuple(resumable_pages),
        pages_to_capture=tuple(pages_to_capture),
        invalid_completed_pages=tuple(invalid_completed_pages),
    )
