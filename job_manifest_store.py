"""JSON persistence for the minimal ManReader job manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from job_manifest_model import (
    JobManifest,
    job_manifest_from_dict,
    job_manifest_to_dict,
)


def save_job_manifest(manifest: JobManifest, path: Path) -> None:
    """Write a job manifest as deterministic UTF-8 JSON.

    The destination parent directory must already exist. Workspace creation
    belongs to a separate operational layer.
    """

    payload = job_manifest_to_dict(manifest)
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    path.write_text(f"{serialized}\n", encoding="utf-8")


def load_job_manifest(path: Path) -> JobManifest:
    """Read and validate a job manifest from UTF-8 JSON."""

    try:
        decoded: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid job manifest JSON: {path}") from exc

    if not isinstance(decoded, dict):
        raise ValueError("job manifest root must be a JSON object")

    return job_manifest_from_dict(decoded)
