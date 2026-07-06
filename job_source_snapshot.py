"""Verified source snapshot materialization for a ManReader job."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from job_manifest_model import SourceReference


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

    sha256, size_bytes = _hash_file(destination_path)
    return SourceReference(
        sha256=sha256,
        size_bytes=size_bytes,
        original_name=source_path.name,
    )


def verify_source_snapshot(path: Path, expected: SourceReference) -> bool:
    """Return whether a snapshot still matches its recorded reference."""

    if not path.is_file():
        return False

    sha256, size_bytes = _hash_file(path)
    return sha256 == expected.sha256 and size_bytes == expected.size_bytes


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size_bytes = 0

    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size_bytes += len(chunk)

    return digest.hexdigest(), size_bytes
