"""Capture progress contract and artifact verification for ManReader jobs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from verified_file_model import VerifiedFileReference, verify_file


class CapturePageStatus(StrEnum):
    """Persistent capture states for one source page."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


def _validate_relative_posix_path(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if "\\" in value:
        raise ValueError(f"{field_name} must use POSIX '/' separators")

    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f"{field_name} must be relative to the job workspace")
    if value in {".", ".."} or any(part == ".." for part in path.parts):
        raise ValueError(f"{field_name} must not escape the job workspace")


@dataclass(frozen=True, slots=True)
class CapturePageState:
    """Persistent capture state and optional verified artifact reference."""

    page_num: int
    status: CapturePageStatus
    artifact_path: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.page_num < 1:
            raise ValueError("page_num must be 1-based")

        if self.status is CapturePageStatus.COMPLETED:
            if self.artifact_path is None:
                raise ValueError("completed pages require artifact_path")
            if self.sha256 is None:
                raise ValueError("completed pages require sha256")
            if self.size_bytes is None:
                raise ValueError("completed pages require size_bytes")

            _validate_relative_posix_path(self.artifact_path, "artifact_path")
            VerifiedFileReference(
                sha256=self.sha256,
                size_bytes=self.size_bytes,
            )
            return

        if any(value is not None for value in (self.artifact_path, self.sha256, self.size_bytes)):
            raise ValueError("pending and failed pages must not declare a completed artifact")


@dataclass(frozen=True, slots=True)
class CaptureProgress:
    """Complete page-level state for one capture phase."""

    page_count: int
    pages: tuple[CapturePageState, ...]

    def __post_init__(self) -> None:
        if self.page_count < 0:
            raise ValueError("page_count must be greater than or equal to zero")

        page_numbers = tuple(page.page_num for page in self.pages)
        expected = tuple(range(1, self.page_count + 1))
        if page_numbers != expected:
            raise ValueError("capture pages must cover exactly 1..page_count in order")


def initial_capture_progress(page_count: int) -> CaptureProgress:
    """Build an all-pending capture progress contract."""

    return CaptureProgress(
        page_count=page_count,
        pages=tuple(
            CapturePageState(
                page_num=page_num,
                status=CapturePageStatus.PENDING,
            )
            for page_num in range(1, page_count + 1)
        ),
    )


def capture_progress_to_dict(progress: CaptureProgress) -> dict[str, Any]:
    """Convert capture progress to a JSON-compatible dictionary."""

    return asdict(progress)


def capture_progress_from_dict(data: dict[str, Any]) -> CaptureProgress:
    """Reconstruct and validate capture progress from decoded JSON."""

    page_count = _require_int(data, "page_count")
    pages_data = data.get("pages")
    if not isinstance(pages_data, list):
        raise ValueError("pages must be a list")

    pages: list[CapturePageState] = []
    for index, item in enumerate(pages_data):
        if not isinstance(item, dict):
            raise ValueError(f"pages[{index}] must be an object")

        try:
            status = CapturePageStatus(_require_str(item, "status"))
        except ValueError as exc:
            raise ValueError(f"pages[{index}] has invalid status") from exc

        pages.append(
            CapturePageState(
                page_num=_require_int(item, "page_num"),
                status=status,
                artifact_path=_optional_str(item, "artifact_path"),
                sha256=_optional_str(item, "sha256"),
                size_bytes=_optional_int(item, "size_bytes"),
            )
        )

    return CaptureProgress(page_count=page_count, pages=tuple(pages))


def is_capture_page_resumable(page: CapturePageState, job_dir: Path) -> bool:
    """Return whether a completed page artifact is present and verified."""

    if page.status is not CapturePageStatus.COMPLETED:
        return False

    assert page.artifact_path is not None
    assert page.sha256 is not None
    assert page.size_bytes is not None

    artifact_path = job_dir.joinpath(*PurePosixPath(page.artifact_path).parts)
    expected = VerifiedFileReference(
        sha256=page.sha256,
        size_bytes=page.size_bytes,
    )
    return verify_file(artifact_path, expected)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value


def _optional_int(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer or null")
    return value
