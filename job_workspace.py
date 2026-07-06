"""Minimal filesystem creation for a ManReader job workspace."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from job_manifest_model import JobManifest
from job_manifest_store import save_job_manifest


def create_job_workspace(manifest: JobManifest, job_dir: Path) -> Path:
    """Create the minimal directory structure declared by a job manifest.

    The parent of ``job_dir`` must already exist and ``job_dir`` itself must
    not exist. This function creates directories and persists the manifest,
    but it does not create or copy the source snapshot.

    Returns the path of the written manifest.
    """

    job_dir.mkdir()

    source_snapshot = _resolve_workspace_path(
        job_dir,
        manifest.workspace.source_snapshot,
    )
    raw_dir = _resolve_workspace_path(job_dir, manifest.workspace.raw_dir)
    manifest_path = _resolve_workspace_path(
        job_dir,
        manifest.workspace.manifest_path,
    )

    source_snapshot.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    save_job_manifest(manifest, manifest_path)
    return manifest_path


def _resolve_workspace_path(job_dir: Path, relative_path: str) -> Path:
    """Resolve a validated manifest path below the explicit job directory."""

    return job_dir.joinpath(*PurePosixPath(relative_path).parts)
