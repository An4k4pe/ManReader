"""Derived capture-phase summary for a ManReader job."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from job_capture_resume import CaptureResumePlan, build_capture_resume_plan
from job_manifest_model import JobManifest


class CaptureProgressStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class CapturePhaseSummary:
    progress_status: CaptureProgressStatus
    resumable_pages: tuple[int, ...]
    pages_to_capture: tuple[int, ...]
    invalid_completed_pages: tuple[int, ...]


def derive_capture_phase_summary(
    manifest: JobManifest,
    *,
    job_dir: Path,
) -> CapturePhaseSummary:
    plan = build_capture_resume_plan(manifest, job_dir=job_dir)
    status = _derive_progress_status(
        page_count=manifest.capture_progress.page_count,
        plan=plan,
    )
    return CapturePhaseSummary(
        progress_status=status,
        resumable_pages=plan.resumable_pages,
        pages_to_capture=plan.pages_to_capture,
        invalid_completed_pages=plan.invalid_completed_pages,
    )


def _derive_progress_status(
    *,
    page_count: int,
    plan: CaptureResumePlan,
) -> CaptureProgressStatus:
    if page_count == 0 or not plan.pages_to_capture:
        return CaptureProgressStatus.COMPLETED
    if plan.invalid_completed_pages:
        return CaptureProgressStatus.INVALID
    if plan.resumable_pages:
        return CaptureProgressStatus.PARTIAL
    return CaptureProgressStatus.PENDING
