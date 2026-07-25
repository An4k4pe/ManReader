"""Opportunistic on-disk cache for runtime-only page analyses."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from page_analysis_model import PageAnalysis
from page_analysis_store import load_page_analysis, save_page_analysis

_LOGGER = logging.getLogger(__name__)


def _cache_path(*, job_dir: Path, producer_name: str, page_num: int) -> Path:
    """Return the conventional cache path below one job workspace."""

    if page_num < 1:
        raise ValueError("page_num must be 1-based")
    if not producer_name or "\\" in producer_name:
        raise ValueError("producer_name must be a non-empty POSIX path component")

    producer_path = PurePosixPath(producer_name)
    if producer_path.is_absolute() or any(part == ".." for part in producer_path.parts):
        raise ValueError("producer_name must not escape the job workspace")

    relative_path = (
        PurePosixPath("analysis_cache")
        / producer_path
        / f"page-{page_num:04d}.json"
    )
    return job_dir.joinpath(*relative_path.parts)


def read_cached_page_analysis(
    *,
    job_dir: Path,
    producer_name: str,
    page_num: int,
    expected_source_id: str,
    expected_source_capture_id: str,
    expected_source_page_id: str,
    expected_source_primitive_schema_version: str,
    expected_producer_name: str,
    expected_producer_version: str,
    expected_configuration_id: str,
) -> PageAnalysis | None:
    """Return a matching cached analysis, or ``None`` for every cache miss."""

    path = _cache_path(
        job_dir=job_dir,
        producer_name=producer_name,
        page_num=page_num,
    )
    try:
        if not path.is_file():
            return None
        analysis = load_page_analysis(path)
    except Exception:
        return None

    provenance = analysis.provenance
    expected = (
        expected_source_id,
        expected_source_capture_id,
        expected_source_page_id,
        expected_source_primitive_schema_version,
        expected_producer_name,
        expected_producer_version,
        expected_configuration_id,
    )
    actual = (
        provenance.source_id,
        provenance.source_capture_id,
        provenance.source_page_id,
        provenance.source_primitive_schema_version,
        provenance.producer_name,
        provenance.producer_version,
        provenance.configuration_id,
    )
    if actual != expected:
        return None

    _LOGGER.info(
        "PageAnalysis cache hit for producer=%s page_num=%s path=%s",
        producer_name,
        page_num,
        path,
    )
    return analysis


def write_page_analysis_cache(
    *,
    job_dir: Path,
    producer_name: str,
    page_num: int,
    analysis: PageAnalysis,
) -> None:
    """Persist one analysis at the conventional cache location."""

    path = _cache_path(
        job_dir=job_dir,
        producer_name=producer_name,
        page_num=page_num,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    save_page_analysis(path, analysis)
