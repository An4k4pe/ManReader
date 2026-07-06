"""Verified source snapshot materialization for a ManReader job."""

from __future__ import annotations

import shutil
from pathlib import Path

from job_manifest_model import SourceReference
from verified_file_model import inspect_verified_file, verify_file


def inspect_source_file(source_path: Path) -> SourceReference:
    """Build a verified reference without copying the source."""

    verified = inspect_verified_file(source_path)
    return SourceReference(
        sha256=verified.sha256,
        size_bytes=verified.size_bytes,
        original_name=source_path.name,
    )


def materialize_source_snapshot(source_path: Path, destination_path: Path) -> SourceReference:
    """Copy a source file and return its verified content reference.

    The destination parent directory must already exist and the destination
    file must not exist. The copied bytes are hashed after writing.
    """

    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    if destination_path.exists():
        raise FileExistsError(destination_path)

    shutil.copyfile(source_path, destination_path)
    verified = inspect_verified_file(destination_path)
    return SourceReference(
        sha256=verified.sha256,
        size_bytes=verified.size_bytes,
        original_name=source_path.name,
    )


def verify_source_snapshot(path: Path, expected: SourceReference) -> bool:
    """Return whether a snapshot still matches its recorded reference."""

    return verify_file(path, expected)
