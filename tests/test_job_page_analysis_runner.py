"""Tests for runtime-only PageAnalysis execution inside a job workspace."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import fitz

import job_page_analysis_runner
from job_capture_page_runner import capture_job_page
from job_initializer import initialize_job
from job_page_analysis_runner import run_job_page_analysis
from page_analysis_model import PageAnalysis


class JobPageAnalysisRunnerTests(unittest.TestCase):
    def _create_job(
        self,
        root: Path,
        *,
        rotation: int = 0,
        cropbox: fitz.Rect | None = None,
    ) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=300.0, height=220.0)
        if cropbox is not None:
            page.set_cropbox(cropbox)
        page.set_rotation(rotation)
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-001"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-001",
            page_count=1,
        )
        return job_dir, job_dir / "manifest.json"

    def _create_full_page_image_job(self, root: Path) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=300.0, height=220.0)
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10))
        pixmap.set_rect(pixmap.irect, (200, 0, 0))
        page.insert_image(page.rect, stream=pixmap.tobytes("png"))
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-page-covering-visual"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-page-covering-visual",
            page_count=1,
        )
        return job_dir, job_dir / "manifest.json"

    def _create_edge_image_job(self, root: Path) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=300.0, height=220.0)
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10))
        pixmap.set_rect(pixmap.irect, (0, 100, 200))
        page.insert_image(
            fitz.Rect(0.0, 10.0, 20.0, 210.0),
            stream=pixmap.tobytes("png"),
        )
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-page-edge-visual"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-page-edge-visual",
            page_count=1,
        )
        return job_dir, job_dir / "manifest.json"

    def _create_interior_visual_job(self, root: Path) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=300.0, height=220.0)
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10))
        pixmap.set_rect(pixmap.irect, (0, 200, 0))
        page.insert_image(
            fitz.Rect(100.0, 80.0, 200.0, 140.0),
            stream=pixmap.tobytes("png"),
        )
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-embedded-visual"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-embedded-visual",
            page_count=1,
        )
        return job_dir, job_dir / "manifest.json"

    def _create_interior_visual_frame_job(self, root: Path) -> tuple[Path, Path]:
        source_path = root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=300.0, height=220.0)
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10))
        pixmap.set_rect(pixmap.irect, (0, 200, 0))
        page.insert_image(
            fitz.Rect(100.0, 80.0, 200.0, 140.0),
            stream=pixmap.tobytes("png"),
        )
        page.insert_text((130.0, 110.0), "hi", fontsize=12, fontname="helv")
        document.save(source_path)
        document.close()

        job_dir = root / "job-test-interior-visual-frame"
        initialize_job(
            source_path=source_path,
            job_dir=job_dir,
            job_id="job-test-interior-visual-frame",
            page_count=1,
        )
        return job_dir, job_dir / "manifest.json"

    def test_rejects_page_that_has_not_been_captured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(Path(temporary_directory))

            with self.assertRaisesRegex(ValueError, "not completed"):
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:test",
                )

    def test_rejects_completed_page_with_invalid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(Path(temporary_directory))
            captured = capture_job_page(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
            )
            (job_dir / captured.artifact_path).write_text("corrupted", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "artifact is invalid"):
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:test",
                )

    def test_rejects_unknown_producer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(Path(temporary_directory))

            with self.assertRaisesRegex(ValueError, "unsupported"):
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="unknown",
                    generation_id="generation:test",
                )

    def test_rejects_rotated_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(
                Path(temporary_directory),
                rotation=180,
            )
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            with self.assertRaisesRegex(ValueError, "rotation"):
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:test",
                )

    def test_rejects_page_with_cropbox_different_from_mediabox(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(
                Path(temporary_directory),
                cropbox=fitz.Rect(20.0, 30.0, 280.0, 190.0),
            )
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            with self.assertRaisesRegex(ValueError, "cropbox != mediabox"):
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:test",
                )

    def test_runs_table_candidate_for_known_dag_page(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "Dag.pdf"
        self.assertTrue(source_path.is_file())

        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir = Path(temporary_directory) / "job-dag-001"
            manifest = initialize_job(
                source_path=source_path,
                job_dir=job_dir,
                job_id="job-dag-001",
                page_count=379,
            )
            manifest_path = job_dir / manifest.workspace.manifest_path
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=137)

            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=137,
                producer_name="table_candidate",
                generation_id="generation:first",
            )

            cache_path = job_dir / "analysis_cache" / "table_candidate" / "page-0137.json"
            self.assertTrue(cache_path.is_file())

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    side_effect=AssertionError("cache hit must not open the PDF"),
                ),
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    side_effect=AssertionError("cache hit must not recapture the page"),
                ),
            ):
                cached_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=137,
                    producer_name="table_candidate",
                    generation_id="generation:second",
                )

        self.assertEqual(
            tuple(len(candidate.primitive_ids) for candidate in first_result.analysis.candidates),
            (114, 57),
        )
        self.assertEqual(
            cached_result.analysis,
            replace_generation_id(first_result.analysis, "generation:second"),
        )

    def test_force_recompute_ignores_valid_cache_and_rewrites_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_job(Path(temporary_directory))
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)
            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                producer_name="table_candidate",
                generation_id="generation:first",
            )

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    wraps=job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source,
                ) as bind_mock,
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    wraps=job_page_analysis_runner.capture_pymupdf_page,
                ) as capture_mock,
            ):
                recomputed_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:forced",
                    force_recompute=True,
                )

            self.assertTrue(bind_mock.called)
            self.assertTrue(capture_mock.called)
            self.assertEqual(
                recomputed_result.analysis,
                replace_generation_id(first_result.analysis, "generation:forced"),
            )

    def test_runs_page_covering_visual_for_synthetic_full_page_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_full_page_image_job(Path(temporary_directory))
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                producer_name="page_covering_visual",
                generation_id="generation:first",
            )

            self.assertTrue(
                any(
                    candidate.proposed_structural_kind == "layout.page_covering_visual"
                    for candidate in first_result.analysis.candidates
                )
            )

            cache_path = job_dir / "analysis_cache" / "page_covering_visual" / "page-0001.json"
            self.assertTrue(cache_path.is_file())

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    side_effect=AssertionError("cache hit must not open the PDF"),
                ),
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    side_effect=AssertionError("cache hit must not recapture the page"),
                ),
            ):
                cached_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="page_covering_visual",
                    generation_id="generation:second",
                )

            self.assertEqual(
                cached_result.analysis,
                replace_generation_id(first_result.analysis, "generation:second"),
            )

    def test_runs_page_edge_visual_for_synthetic_edge_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_edge_image_job(Path(temporary_directory))
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                producer_name="page_edge_visual",
                generation_id="generation:first",
            )

            self.assertTrue(
                any(
                    candidate.proposed_structural_kind == "layout.page_edge_visual"
                    for candidate in first_result.analysis.candidates
                )
            )

            cache_path = job_dir / "analysis_cache" / "page_edge_visual" / "page-0001.json"
            self.assertTrue(cache_path.is_file())

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    side_effect=AssertionError("cache hit must not open the PDF"),
                ),
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    side_effect=AssertionError("cache hit must not recapture the page"),
                ),
            ):
                cached_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="page_edge_visual",
                    generation_id="generation:second",
                )

            self.assertEqual(
                cached_result.analysis,
                replace_generation_id(first_result.analysis, "generation:second"),
            )

    def test_runs_embedded_visual_for_synthetic_interior_visual(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_interior_visual_job(
                Path(temporary_directory)
            )
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                producer_name="embedded_visual",
                generation_id="generation:first",
            )

            self.assertTrue(
                any(
                    candidate.proposed_structural_kind == "layout.embedded_visual"
                    for candidate in first_result.analysis.candidates
                )
            )

            cache_path = job_dir / "analysis_cache" / "embedded_visual" / "page-0001.json"
            self.assertTrue(cache_path.is_file())

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    side_effect=AssertionError("cache hit must not open the PDF"),
                ),
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    side_effect=AssertionError("cache hit must not recapture the page"),
                ),
            ):
                cached_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="embedded_visual",
                    generation_id="generation:second",
                )

            self.assertEqual(
                cached_result.analysis,
                replace_generation_id(first_result.analysis, "generation:second"),
            )

    def test_runs_interior_visual_frame_for_synthetic_framed_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_interior_visual_frame_job(
                Path(temporary_directory)
            )
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            first_result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=1,
                producer_name="interior_visual_frame",
                generation_id="generation:first",
            )

            self.assertTrue(
                any(
                    candidate.proposed_structural_kind == "layout.interior_visual_frame"
                    for candidate in first_result.analysis.candidates
                )
            )

            cache_path = (
                job_dir / "analysis_cache" / "interior_visual_frame" / "page-0001.json"
            )
            self.assertTrue(cache_path.is_file())

            with (
                patch(
                    "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                    side_effect=AssertionError("cache hit must not open the PDF"),
                ),
                patch(
                    "job_page_analysis_runner.capture_pymupdf_page",
                    side_effect=AssertionError("cache hit must not recapture the page"),
                ),
            ):
                cached_result = run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="interior_visual_frame",
                    generation_id="generation:second",
                )

            self.assertEqual(
                cached_result.analysis,
                replace_generation_id(first_result.analysis, "generation:second"),
            )

    def test_include_pdfplumber_is_symmetric_per_producer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir, manifest_path = self._create_full_page_image_job(Path(temporary_directory))
            capture_job_page(job_dir=job_dir, manifest_path=manifest_path, page_num=1)

            with patch(
                "job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source",
                wraps=job_page_analysis_runner.bind_pymupdf_pdfplumber_document_source,
            ) as bind_mock:
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="table_candidate",
                    generation_id="generation:table",
                )
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="page_covering_visual",
                    generation_id="generation:visual",
                )
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="page_edge_visual",
                    generation_id="generation:edge",
                )
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="embedded_visual",
                    generation_id="generation:embedded",
                )
                run_job_page_analysis(
                    job_dir=job_dir,
                    manifest_path=manifest_path,
                    page_num=1,
                    producer_name="interior_visual_frame",
                    generation_id="generation:frame",
                )

            self.assertEqual(bind_mock.call_count, 5)
            (
                table_call,
                covering_call,
                edge_call,
                embedded_call,
                interior_visual_frame_call,
            ) = bind_mock.call_args_list
            self.assertTrue(table_call.kwargs.get("include_pdfplumber", True))
            self.assertFalse(covering_call.kwargs.get("include_pdfplumber", True))
            self.assertFalse(edge_call.kwargs.get("include_pdfplumber", True))
            self.assertFalse(embedded_call.kwargs.get("include_pdfplumber", True))
            self.assertFalse(
                interior_visual_frame_call.kwargs.get("include_pdfplumber", True)
            )


def replace_generation_id(analysis: PageAnalysis, generation_id: str) -> PageAnalysis:
    """Return a comparison value with only the runtime generation changed."""

    return replace(analysis, generation_id=generation_id)


if __name__ == "__main__":
    unittest.main()
