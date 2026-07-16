"""Generic verified-file references and hashing helpers for ManReader."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VerifiedFileReference:
    """Content identity for a file verified by SHA-256 and byte size."""

    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        if len(self.sha256) != 64:
            raise ValueError("sha256 must contain exactly 64 hexadecimal characters")
        if self.sha256 != self.sha256.lower():
            raise ValueError("sha256 must use canonical lowercase hexadecimal")
        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise ValueError("sha256 must contain only hexadecimal characters") from exc

        if self.size_bytes < 0:
            raise ValueError("size_bytes must be greater than or equal to zero")


def inspect_verified_bytes(data: bytes) -> VerifiedFileReference:
    """Build a verified reference for one explicit immutable byte sequence."""

    if not isinstance(data, bytes):
        raise ValueError("data must be bytes")
    return VerifiedFileReference(
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def inspect_verified_file(path: Path) -> VerifiedFileReference:
    """Build a verified reference for an existing regular file."""

    if not path.is_file():
        raise FileNotFoundError(path)

    digest = hashlib.sha256()
    size_bytes = 0

    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size_bytes += len(chunk)

    return VerifiedFileReference(
        sha256=digest.hexdigest(),
        size_bytes=size_bytes,
    )


def verify_file(path: Path, expected: VerifiedFileReference) -> bool:
    """Return whether a file exists and matches the expected reference."""

    if not path.is_file():
        return False

    actual = inspect_verified_file(path)
    return actual.sha256 == expected.sha256 and actual.size_bytes == expected.size_bytes
