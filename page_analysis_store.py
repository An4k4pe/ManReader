"""Minimal JSON file store for PageAnalysis."""

from __future__ import annotations

import json
from pathlib import Path

from page_analysis_model import PageAnalysis
from page_analysis_serialization import (
    page_analysis_from_dict,
    page_analysis_to_dict,
)


def save_page_analysis(
    path: Path,
    analysis: PageAnalysis,
) -> None:
    """Write a PageAnalysis as deterministic UTF-8 JSON."""

    if not isinstance(path, Path):
        raise ValueError("path must be a Path")

    data = page_analysis_to_dict(analysis)
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    path.write_text(serialized + "\n", encoding="utf-8")


def load_page_analysis(
    path: Path,
) -> PageAnalysis:
    """Read and validate a PageAnalysis from UTF-8 JSON."""

    if not isinstance(path, Path):
        raise ValueError("path must be a Path")

    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid page analysis JSON: {path}") from exc

    return page_analysis_from_dict(data)
