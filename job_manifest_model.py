"""Immutable, JSON-serializable contract for a minimal ManReader job manifest."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any

from job_capture_progress import (
    CapturePageStatus,
    CaptureProgress,
    capture_progress_from_dict,
    initial_capture_progress,
    require_capture_artifact_under_raw_dir,
)
from verified_file_model import VerifiedFileReference

JOB_MANIFEST_SCHEMA_VERSION = "1.0"


def _validate_non_empty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _validate_relative_posix_path(value: str, field_name: str) -> None:
    _validate_non_empty(value, field_name)

    if "\\" in value:
        raise ValueError(f"{field_name} must use POSIX '/' separators")

    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f"{field_name} must be relative to the job workspace")

    if value in {".", ".."} or any(part == ".." for part in path.parts):
        raise ValueError(f"{field_name} must not escape the job workspace")


@dataclass(frozen=True, slots=True)
class SourceReference(VerifiedFileReference):
    """Verifiable identity of the immutable source content."""

    original_name: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.original_name == "":
            raise ValueError("original_name must not be empty when provided")


@dataclass(frozen=True, slots=True)
class WorkspacePaths:
    """Paths relative to the root directory of one job workspace."""

    source_snapshot: str
    raw_dir: str = "raw"
    manifest_path: str = "manifest.json"

    def __post_init__(self) -> None:
        _validate_relative_posix_path(self.source_snapshot, "source_snapshot")
        _validate_relative_posix_path(self.raw_dir, "raw_dir")
        _validate_relative_posix_path(self.manifest_path, "manifest_path")


@dataclass(frozen=True, slots=True)
class JobManifest:
    """Minimal persistent contract for a ManReader job."""

    schema_version: str
    job_id: str
    source: SourceReference
    workspace: WorkspacePaths
    capture_progress: CaptureProgress

    def __post_init__(self) -> None:
        _validate_non_empty(self.schema_version, "schema_version")
        if self.schema_version != JOB_MANIFEST_SCHEMA_VERSION:
            raise ValueError(f"unsupported job manifest schema_version: {self.schema_version}")
        _validate_non_empty(self.job_id, "job_id")

        for page in self.capture_progress.pages:
            if page.status is CapturePageStatus.COMPLETED:
                assert page.artifact_path is not None
                require_capture_artifact_under_raw_dir(
                    artifact_path=page.artifact_path,
                    raw_dir=self.workspace.raw_dir,
                )


def initial_job_manifest(
    *,
    job_id: str,
    source: SourceReference,
    workspace: WorkspacePaths,
    page_count: int,
) -> JobManifest:
    """Build the initial declarative state without filesystem operations."""

    return JobManifest(
        schema_version=JOB_MANIFEST_SCHEMA_VERSION,
        job_id=job_id,
        source=source,
        workspace=workspace,
        capture_progress=initial_capture_progress(page_count),
    )


def job_manifest_to_dict(manifest: JobManifest) -> dict[str, Any]:
    """Convert a manifest to a JSON-compatible dictionary."""

    return asdict(manifest)


def job_manifest_from_dict(data: Mapping[str, Any]) -> JobManifest:
    """Reconstruct and validate a manifest from a decoded JSON object."""

    source_data = _require_mapping(data, "source")
    workspace_data = _require_mapping(data, "workspace")
    capture_progress_data = _require_mapping(data, "capture_progress")

    try:
        return JobManifest(
            capture_progress=capture_progress_from_dict(dict(capture_progress_data)),
            schema_version=_require_str(data, "schema_version"),
            job_id=_require_str(data, "job_id"),
            source=SourceReference(
                sha256=_require_str(source_data, "sha256"),
                size_bytes=_require_int(source_data, "size_bytes"),
                original_name=_optional_str(source_data, "original_name"),
            ),
            workspace=WorkspacePaths(
                source_snapshot=_require_str(workspace_data, "source_snapshot"),
                raw_dir=_require_str(workspace_data, "raw_dir"),
                manifest_path=_require_str(workspace_data, "manifest_path"),
            ),
        )
    except KeyError as exc:
        raise ValueError(f"manifest is missing {exc.args[0]}") from exc


def _require_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_int(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value
