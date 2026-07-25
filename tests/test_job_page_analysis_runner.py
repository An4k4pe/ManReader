"""Tests for runtime-only PageAnalysis execution inside a job workspace."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

from job_capture_page_runner import capture_job_page
from job_initializer import initialize_job
from job_page_analysis_runner import run_job_page_analysis


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

            result = run_job_page_analysis(
                job_dir=job_dir,
                manifest_path=manifest_path,
                page_num=137,
                producer_name="table_candidate",
                generation_id="generation:test",
            )

        self.assertEqual(
            tuple(len(candidate.primitive_ids) for candidate in result.analysis.candidates),
            (114, 57),
        )


if __name__ == "__main__":
    unittest.main()
