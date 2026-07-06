"""Coordinated initialization of a minimal ManReader job."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from job_manifest_model import JobManifest, WorkspacePaths, initial_job_manifest
from job_source_snapshot import inspect_source_file, materialize_source_snapshot
from job_workspace import create_job_workspace


def initialize_job(
    *,
    source_path: Path,
    page_count: int,
    job_dir: Path,
    job_id: str,
    workspace: WorkspacePaths | None = None,
) -> JobManifest:
    """Create a minimal job workspace with a verified source snapshot.

    The job directory must not already exist. The source is inspected before
    workspace creation, copied into the declared snapshot path, and verified
    against the reference stored in the manifest.

    This function does not implement rollback if a later step fails.
    """

    resolved_workspace = workspace or WorkspacePaths(source_snapshot=f"source/{source_path.name}")
    source_reference = inspect_source_file(source_path)
    manifest = initial_job_manifest(
        job_id=job_id,
        source=source_reference,
        workspace=resolved_workspace,
        page_count=page_count,
    )

    create_job_workspace(manifest, job_dir)

    destination_path = job_dir.joinpath(*PurePosixPath(resolved_workspace.source_snapshot).parts)
    copied_reference = materialize_source_snapshot(source_path, destination_path)

    if (
        copied_reference.sha256 != source_reference.sha256
        or copied_reference.size_bytes != source_reference.size_bytes
    ):
        raise ValueError("materialized source snapshot does not match inspected source")

    return manifest
