"""Runtime-only PageAnalysis runner above already captured job pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from job_capture_progress import CapturePageStatus, is_capture_page_resumable
from job_manifest_model import JobManifest
from job_manifest_store import load_job_manifest
from page_analysis_model import PageAnalysis
from page_analysis_table_candidate import build_table_candidate_page_analysis
from page_analysis_table_candidate_binding import BoundTableCandidatePage
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page
from pymupdf_pdfplumber_document_source_binding import (
    bind_pymupdf_pdfplumber_document_source,
)

_SUPPORTED_PRODUCERS = frozenset({"table_candidate"})


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
) -> PageAnalysisRunResult:
    """Run one supported producer for a verified, completed capture page."""

    manifest = load_job_manifest(manifest_path)
    _validate_manifest_path(
        manifest=manifest,
        job_dir=job_dir,
        manifest_path=manifest_path,
    )
    _validate_page_num(manifest, page_num)
    if producer_name not in _SUPPORTED_PRODUCERS:
        raise ValueError(f"unsupported page analysis producer: {producer_name!r}")

    capture_page = manifest.capture_progress.pages[page_num - 1]
    if capture_page.status is not CapturePageStatus.COMPLETED:
        raise ValueError(f"capture page {page_num} is not completed")
    if not is_capture_page_resumable(capture_page, job_dir):
        raise ValueError(
            f"capture page {page_num} is completed but its artifact is invalid; "
            "explicit reset is required"
        )

    snapshot_path = _workspace_path(job_dir, manifest.workspace.source_snapshot)
    bound_source = bind_pymupdf_pdfplumber_document_source(
        snapshot_path,
        expected_file=manifest.source,
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
                page_id=f"page:{page_num:04d}",
                capture_id=(
                    f"{manifest.job_id}:analysis:pymupdf:page:{page_num:04d}"
                ),
            )
        )
        if producer_name == "table_candidate":
            analysis = build_table_candidate_page_analysis(
                BoundTableCandidatePage(
                    primitive_page=primitive_page,
                    plumber_page=bound_source.plumber_pdf.pages[page_num - 1],
                ),
                generation_id=generation_id,
            )
        else:
            raise AssertionError("supported producer dispatch is incomplete")
    finally:
        bound_source.fitz_document.close()
        bound_source.plumber_pdf.close()

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
