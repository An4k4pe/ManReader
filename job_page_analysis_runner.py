"""Runtime-only PageAnalysis runner above already captured job pages."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from job_capture_progress import CapturePageStatus, is_capture_page_resumable
from job_manifest_model import JobManifest
from job_manifest_store import load_job_manifest
from job_page_analysis_cache import (
    read_cached_page_analysis,
    write_page_analysis_cache,
)
from page_analysis_model import PageAnalysis
from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from page_analysis_table_candidate import build_table_candidate_page_analysis
from page_analysis_table_candidate_binding import BoundTableCandidatePage
from primitive_normalizer import (
    NORMALIZED_PRIMITIVE_SCHEMA_VERSION,
    normalize_backend_page_capture,
)
from pymupdf_capture import capture_pymupdf_page
from pymupdf_pdfplumber_document_source_binding import (
    bind_pymupdf_pdfplumber_document_source,
)


@dataclass(frozen=True, slots=True)
class _ProducerSpec:
    """Static per-producer identity used for dispatch, caching and backend needs."""

    internal_producer_name: str
    producer_version: str
    configuration_id: str
    requires_pdfplumber: bool


_PRODUCER_SPECS: dict[str, _ProducerSpec] = {
    "table_candidate": _ProducerSpec(
        internal_producer_name="table_candidate",
        producer_version="1.0",
        configuration_id="pdfplumber-text-lines-v1",
        requires_pdfplumber=True,
    ),
    "page_covering_visual": _ProducerSpec(
        internal_producer_name="page_analysis.page_covering_visual",
        producer_version="0.1",
        configuration_id="page-covering-visual-v1",
        requires_pdfplumber=False,
    ),
    "page_edge_visual": _ProducerSpec(
        internal_producer_name="page_analysis.page_edge_visual",
        producer_version="0.1",
        configuration_id="page-edge-visual-v1",
        requires_pdfplumber=False,
    ),
}


@dataclass(frozen=True, slots=True)
class PageAnalysisRunResult:
    """Result of one runtime-only job-page analysis."""

    manifest: JobManifest
    analysis: PageAnalysis


def run_job_page_analysis(
    *,
    job_dir: Path,
    manifest_path: Path,
    page_num: int,
    producer_name: str,
    generation_id: str,
    force_recompute: bool = False,
) -> PageAnalysisRunResult:
    """Run one supported producer for a verified, completed capture page."""

    manifest = load_job_manifest(manifest_path)
    _validate_manifest_path(
        manifest=manifest,
        job_dir=job_dir,
        manifest_path=manifest_path,
    )
    _validate_page_num(manifest, page_num)
    if producer_name not in _PRODUCER_SPECS:
        raise ValueError(f"unsupported page analysis producer: {producer_name!r}")

    capture_page = manifest.capture_progress.pages[page_num - 1]
    if capture_page.status is not CapturePageStatus.COMPLETED:
        raise ValueError(f"capture page {page_num} is not completed")
    if not is_capture_page_resumable(capture_page, job_dir):
        raise ValueError(
            f"capture page {page_num} is completed but its artifact is invalid; "
            "explicit reset is required"
        )

    source_page_id = f"page:{page_num:04d}"
    source_capture_id = f"{manifest.job_id}:analysis:pymupdf:page:{page_num:04d}"
    producer_spec = _PRODUCER_SPECS[producer_name]
    if not force_recompute:
        cached_analysis = read_cached_page_analysis(
            job_dir=job_dir,
            producer_name=producer_name,
            page_num=page_num,
            expected_source_id=manifest.source.sha256,
            expected_source_capture_id=source_capture_id,
            expected_source_page_id=source_page_id,
            expected_source_primitive_schema_version=NORMALIZED_PRIMITIVE_SCHEMA_VERSION,
            expected_producer_name=producer_spec.internal_producer_name,
            expected_producer_version=producer_spec.producer_version,
            expected_configuration_id=producer_spec.configuration_id,
        )
        if cached_analysis is not None:
            return PageAnalysisRunResult(
                manifest=manifest,
                analysis=replace(cached_analysis, generation_id=generation_id),
            )

    snapshot_path = _workspace_path(job_dir, manifest.workspace.source_snapshot)
    bound_source = bind_pymupdf_pdfplumber_document_source(
        snapshot_path,
        expected_file=manifest.source,
        include_pdfplumber=producer_spec.requires_pdfplumber,
    )
    try:
        if bound_source.fitz_document.page_count != manifest.capture_progress.page_count:
            raise ValueError("PDF page count does not match manifest capture progress")

        page = bound_source.fitz_document.load_page(page_num - 1)
        if page.rotation != 0:
            raise ValueError("page rotation must be 0")
        if page.mediabox != page.cropbox:
            raise ValueError("page cropbox != mediabox")

        primitive_page = normalize_backend_page_capture(
            capture_pymupdf_page(
                page,
                source_id=manifest.source.sha256,
                page_id=source_page_id,
                capture_id=source_capture_id,
            )
        )
        if producer_name == "table_candidate":
            if bound_source.plumber_pdf is None:
                raise AssertionError("table_candidate requires an open pdfplumber document")
            analysis = build_table_candidate_page_analysis(
                BoundTableCandidatePage(
                    primitive_page=primitive_page,
                    plumber_page=bound_source.plumber_pdf.pages[page_num - 1],
                ),
                generation_id=generation_id,
            )
        elif producer_name == "page_covering_visual":
            analysis = build_page_covering_visual_page_analysis(
                primitive_page,
                generation_id=generation_id,
            )
        elif producer_name == "page_edge_visual":
            analysis = build_page_edge_visual_page_analysis(
                primitive_page,
                generation_id=generation_id,
            )
        else:
            raise AssertionError("supported producer dispatch is incomplete")
    finally:
        bound_source.fitz_document.close()
        if bound_source.plumber_pdf is not None:
            bound_source.plumber_pdf.close()

    write_page_analysis_cache(
        job_dir=job_dir,
        producer_name=producer_name,
        page_num=page_num,
        analysis=analysis,
    )
    return PageAnalysisRunResult(manifest=manifest, analysis=analysis)


def _validate_manifest_path(
    *,
    manifest: JobManifest,
    job_dir: Path,
    manifest_path: Path,
) -> None:
    expected = _workspace_path(job_dir, manifest.workspace.manifest_path)
    if manifest_path != expected:
        raise ValueError("manifest_path does not match workspace manifest_path")


def _validate_page_num(manifest: JobManifest, page_num: int) -> None:
    page_count = manifest.capture_progress.page_count
    if page_num < 1 or page_num > page_count:
        raise ValueError(f"page_num must be between 1 and {page_count}")


def _workspace_path(job_dir: Path, relative_path: str) -> Path:
    return job_dir.joinpath(*PurePosixPath(relative_path).parts)
