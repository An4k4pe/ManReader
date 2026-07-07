"""Persisted capture-page completion for a ManReader job workspace."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from job_capture_page_update import complete_capture_page
from job_manifest_model import JobManifest
from job_manifest_store import load_job_manifest, save_job_manifest


def complete_capture_page_in_workspace(
    *,
    job_dir: Path,
    manifest_path: Path,
    page_num: int,
    artifact_path: str,
) -> JobManifest:
    """Complete one capture page and persist the updated manifest.

    The manifest path must match the relative path declared by the manifest.
    This function does not provide atomic publication or rollback.
    """

    manifest = load_job_manifest(manifest_path)
    expected_manifest_path = job_dir.joinpath(
        *PurePosixPath(manifest.workspace.manifest_path).parts
    )
    if manifest_path != expected_manifest_path:
        raise ValueError("manifest_path does not match workspace manifest_path")

    updated = complete_capture_page(
        manifest,
        job_dir=job_dir,
        page_num=page_num,
        artifact_path=artifact_path,
    )
    save_job_manifest(updated, manifest_path)
    return updated
