"""Immutable capture-page completion for a ManReader job manifest."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path, PurePosixPath

from job_capture_progress import CapturePageState, CapturePageStatus, CaptureProgress
from job_manifest_model import JobManifest
from verified_file_model import inspect_verified_file


def complete_capture_page(
    manifest: JobManifest,
    *,
    job_dir: Path,
    page_num: int,
    artifact_path: str,
) -> JobManifest:
    """Return a new manifest with one verified capture page completed.

    The artifact must already exist below the workspace raw directory.
    Existing completed pages are not overwritten.
    """

    page_index = _page_index(manifest.capture_progress, page_num)
    current = manifest.capture_progress.pages[page_index]

    if current.status is CapturePageStatus.COMPLETED:
        raise ValueError(f"capture page {page_num} is already completed")

    _require_path_under_raw_dir(
        artifact_path=artifact_path,
        raw_dir=manifest.workspace.raw_dir,
    )

    absolute_artifact_path = job_dir.joinpath(*PurePosixPath(artifact_path).parts)
    verified = inspect_verified_file(absolute_artifact_path)

    completed = CapturePageState(
        page_num=page_num,
        status=CapturePageStatus.COMPLETED,
        artifact_path=artifact_path,
        sha256=verified.sha256,
        size_bytes=verified.size_bytes,
    )

    pages = list(manifest.capture_progress.pages)
    pages[page_index] = completed

    updated_progress = CaptureProgress(
        page_count=manifest.capture_progress.page_count,
        pages=tuple(pages),
    )
    return replace(manifest, capture_progress=updated_progress)


def _page_index(progress: CaptureProgress, page_num: int) -> int:
    if page_num < 1 or page_num > progress.page_count:
        raise ValueError(f"page_num must be between 1 and {progress.page_count}")
    return page_num - 1


def _require_path_under_raw_dir(*, artifact_path: str, raw_dir: str) -> None:
    artifact = PurePosixPath(artifact_path)
    raw = PurePosixPath(raw_dir)

    if artifact == raw or not artifact.is_relative_to(raw):
        raise ValueError("capture artifact must be stored below workspace raw_dir")
