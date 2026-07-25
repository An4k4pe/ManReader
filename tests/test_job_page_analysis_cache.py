"""Tests for the opportunistic PageAnalysis cache."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from job_page_analysis_cache import (
    read_cached_page_analysis,
    write_page_analysis_cache,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
)
from page_analysis_store import load_page_analysis


class JobPageAnalysisCacheTests(unittest.TestCase):
    def _analysis(self) -> PageAnalysis:
        return PageAnalysis(
            schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
            generation_id="generation:cached",
            page_id="page:0007",
            provenance=PageAnalysisProvenance(
                source_id="source-id",
                source_capture_id="job:analysis:pymupdf:page:0007",
                source_page_id="page:0007",
                source_primitive_schema_version="1",
                producer_name="table_candidate",
                producer_version="1.0",
                configuration_id="pdfplumber-text-lines-v1",
            ),
        )

    def _read(self, job_dir: Path) -> PageAnalysis | None:
        return read_cached_page_analysis(
            job_dir=job_dir,
            producer_name="table_candidate",
            page_num=7,
            expected_source_id="source-id",
            expected_source_capture_id="job:analysis:pymupdf:page:0007",
            expected_source_page_id="page:0007",
            expected_source_primitive_schema_version="1",
            expected_producer_name="table_candidate",
            expected_producer_version="1.0",
            expected_configuration_id="pdfplumber-text-lines-v1",
        )

    def _cache_path(self, job_dir: Path) -> Path:
        return job_dir / "analysis_cache" / "table_candidate" / "page-0007.json"

    def test_read_returns_none_when_cache_file_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(self._read(Path(directory)))

    def test_read_returns_none_for_corrupt_cache_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            job_dir = Path(directory)
            path = self._cache_path(job_dir)
            path.parent.mkdir(parents=True)
            path.write_text("not JSON", encoding="utf-8")

            self.assertIsNone(self._read(job_dir))

    def test_read_returns_none_for_provenance_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            job_dir = Path(directory)
            analysis = self._analysis()
            mismatches = (
                replace(analysis.provenance, producer_version="2.0"),
                replace(analysis.provenance, configuration_id="other-config"),
            )

            for provenance in mismatches:
                write_page_analysis_cache(
                    job_dir=job_dir,
                    producer_name="table_candidate",
                    page_num=7,
                    analysis=replace(analysis, provenance=provenance),
                )

                self.assertIsNone(self._read(job_dir))

    def test_read_returns_analysis_when_all_provenance_fields_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            job_dir = Path(directory)
            analysis = self._analysis()
            write_page_analysis_cache(
                job_dir=job_dir,
                producer_name="table_candidate",
                page_num=7,
                analysis=analysis,
            )

            self.assertEqual(self._read(job_dir), analysis)

    def test_write_creates_parent_directories_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            job_dir = Path(directory) / "missing-job-dir"
            analysis = self._analysis()

            write_page_analysis_cache(
                job_dir=job_dir,
                producer_name="table_candidate",
                page_num=7,
                analysis=analysis,
            )

            path = self._cache_path(job_dir)
            self.assertTrue(path.is_file())
            self.assertEqual(load_page_analysis(path), analysis)


if __name__ == "__main__":
    unittest.main()
