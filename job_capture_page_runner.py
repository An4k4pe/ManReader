"""Single-page PyMuPDF capture runner for a ManReader job workspace."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

import fitz

from job_capture_page_store import complete_capture_page_in_workspace
from job_capture_progress import CapturePageStatus, is_capture_page_resumable
from job_manifest_model import JobManifest
from job_manifest_store import load_job_manifest
from job_source_snapshot import verify_source_snapshot
from pymupdf_capture import capture_pymupdf_page


@dataclass(frozen=True, slots=True)
class CapturePageRunResult:
    """Result of one requested job-page capture."""

    manifest: JobManifest
    artifact_path: str
    skipped: bool


def capture_job_page(
    *,
    job_dir: Path,
    manifest_path: Path,
    page_num: int,
) -> CapturePageRunResult:
    """Capture one page from the verified job snapshot and persist progress.

    A valid completed page is skipped. A completed page with a missing or
    corrupted artifact requires an explicit repair/reset operation and is not
    overwritten by this runner.
    """

    manifest = load_job_manifest(manifest_path)
    _validate_manifest_path(
        manifest=manifest,
        job_dir=job_dir,
        manifest_path=manifest_path,
    )
    _validate_page_num(manifest, page_num)

    current = manifest.capture_progress.pages[page_num - 1]
    if current.status is CapturePageStatus.COMPLETED:
        if is_capture_page_resumable(current, job_dir):
            assert current.artifact_path is not None
            return CapturePageRunResult(
                manifest=manifest,
                artifact_path=current.artifact_path,
                skipped=True,
            )
        raise ValueError(
            f"capture page {page_num} is completed but its artifact is invalid; "
            "explicit reset is required"
        )

    snapshot_path = _workspace_path(
        job_dir,
        manifest.workspace.source_snapshot,
    )
    if not verify_source_snapshot(snapshot_path, manifest.source):
        raise ValueError("job source snapshot does not match manifest source reference")

    artifact_relative_path = (
        f"{manifest.workspace.raw_dir}/page-{page_num:04d}.json"
    )
    artifact_path = _workspace_path(job_dir, artifact_relative_path)
    if artifact_path.exists():
        raise FileExistsError(artifact_path)

    with fitz.open(snapshot_path) as document:
        if document.page_count != manifest.capture_progress.page_count:
            raise ValueError(
                "PDF page count does not match manifest capture progress"
            )
        page = document.load_page(page_num - 1)
        capture = capture_pymupdf_page(
            page,
            source_id=manifest.source.sha256,
            page_id=f"page:{page_num:04d}",
            capture_id=f"{manifest.job_id}:pymupdf:page:{page_num:04d}",
        )

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        asdict(capture),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    artifact_path.write_text(f"{serialized}\n", encoding="utf-8")

    updated = complete_capture_page_in_workspace(
        job_dir=job_dir,
        manifest_path=manifest_path,
        page_num=page_num,
        artifact_path=artifact_relative_path,
    )
    return CapturePageRunResult(
        manifest=updated,
        artifact_path=artifact_relative_path,
        skipped=False,
    )


def _validate_manifest_path(
    *,
    manifest: JobManifest,
    job_dir: Path,
    manifest_path: Path,
) -> None:
    expected = _workspace_path(job_dir, manifest.workspace.manifest_path)
    if manifest_path != expected:
        raise ValueError("manifest_path does not match workspace manifest_path")


def _validate_page_num(manifest: JobManifest, page_num: int) -> None:
    page_count = manifest.capture_progress.page_count
    if page_num < 1 or page_num > page_count:
        raise ValueError(f"page_num must be between 1 and {page_count}")


def _workspace_path(job_dir: Path, relative_path: str) -> Path:
    return job_dir.joinpath(*PurePosixPath(relative_path).parts)
