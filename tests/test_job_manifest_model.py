"""Tests for the minimal ManReader job manifest contract."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from job_capture_phase_summary import CaptureProgressStatus, derive_capture_phase_summary
from job_capture_progress import CapturePageState, CapturePageStatus, CaptureProgress
from job_manifest_model import (
    JOB_MANIFEST_SCHEMA_VERSION,
    JobManifest,
    SourceReference,
    WorkspacePaths,
    initial_job_manifest,
    job_manifest_from_dict,
    job_manifest_to_dict,
)


class JobManifestModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceReference(
            sha256="a" * 64,
            size_bytes=1234,
            original_name="manual.pdf",
        )
        self.workspace = WorkspacePaths(source_snapshot="source/manual.pdf")

    def test_initial_manifest_has_schema_and_capture_progress(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            page_count=3,
            source=self.source,
            workspace=self.workspace,
        )

        self.assertEqual(manifest.schema_version, JOB_MANIFEST_SCHEMA_VERSION)
        self.assertEqual(manifest.capture_progress.page_count, 3)

    def test_contract_models_are_immutable(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        with self.assertRaises(FrozenInstanceError):
            manifest.job_id = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            self.source.size_bytes = 0  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            self.workspace.raw_dir = "changed"  # type: ignore[misc]

    def test_json_round_trip_preserves_manifest(self) -> None:
        original = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        encoded = json.dumps(job_manifest_to_dict(original))
        restored = job_manifest_from_dict(json.loads(encoded))

        self.assertEqual(restored, original)

    def test_serialized_manifest_omits_derived_state_field(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        self.assertNotIn("phases", job_manifest_to_dict(manifest))

    def test_overall_capture_state_is_derived_from_capture_progress(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=2,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            summary = derive_capture_phase_summary(manifest, job_dir=Path(temp_dir))

        self.assertEqual(summary.progress_status, CaptureProgressStatus.PENDING)
        self.assertEqual(summary.pages_to_capture, (1, 2))

    def test_manifest_rejects_unknown_schema_version_directly(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=1,
        )

        with self.assertRaisesRegex(
            ValueError,
            "unsupported job manifest schema_version",
        ):
            JobManifest(
                schema_version="2.0",
                job_id="job-test-001",
                source=self.source,
                workspace=self.workspace,
                capture_progress=manifest.capture_progress,
            )

    def test_manifest_from_dict_rejects_unknown_schema_version(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=1,
        )
        data = json.loads(json.dumps(job_manifest_to_dict(manifest)))
        data["schema_version"] = "2.0"

        with self.assertRaisesRegex(
            ValueError,
            "unsupported job manifest schema_version",
        ):
            job_manifest_from_dict(data)

    def test_manifest_rejects_completed_artifact_outside_raw_dir(self) -> None:
        with self.assertRaisesRegex(ValueError, "below workspace raw_dir"):
            JobManifest(
                schema_version=JOB_MANIFEST_SCHEMA_VERSION,
                job_id="job-test-001",
                source=self.source,
                workspace=self.workspace,
                capture_progress=CaptureProgress(
                    page_count=1,
                    pages=(
                        CapturePageState(
                            page_num=1,
                            status=CapturePageStatus.COMPLETED,
                            artifact_path="other/page-0001.json",
                            sha256="a" * 64,
                            size_bytes=1,
                        ),
                    ),
                ),
            )

    def test_manifest_accepts_nested_raw_dir_completed_artifact(self) -> None:
        manifest = JobManifest(
            schema_version=JOB_MANIFEST_SCHEMA_VERSION,
            job_id="job-test-001",
            source=self.source,
            workspace=WorkspacePaths(
                source_snapshot="source/manual.pdf",
                raw_dir="artifacts/raw/capture",
            ),
            capture_progress=CaptureProgress(
                page_count=1,
                pages=(
                    CapturePageState(
                        page_num=1,
                        status=CapturePageStatus.COMPLETED,
                        artifact_path="artifacts/raw/capture/page-0001.json",
                        sha256="a" * 64,
                        size_bytes=1,
                    ),
                ),
            ),
        )

        self.assertEqual(
            manifest.capture_progress.pages[0].artifact_path,
            "artifacts/raw/capture/page-0001.json",
        )

    def test_deserialization_rejects_wrong_scalar_types(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )
        data = job_manifest_to_dict(manifest)
        data["job_id"] = 123

        with self.assertRaises(ValueError):
            job_manifest_from_dict(data)

    def test_serialized_contract_has_only_minimal_top_level_fields(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        self.assertEqual(
            set(job_manifest_to_dict(manifest)),
            {"schema_version", "job_id", "source", "workspace", "capture_progress"},
        )

    def test_source_reference_rejects_invalid_sha256(self) -> None:
        invalid_values = (
            "a" * 63,
            "A" * 64,
            "g" * 64,
        )

        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                SourceReference(sha256=value, size_bytes=0)

    def test_source_reference_rejects_negative_size(self) -> None:
        with self.assertRaises(ValueError):
            SourceReference(sha256="a" * 64, size_bytes=-1)

    def test_workspace_paths_reject_absolute_or_escaping_paths(self) -> None:
        invalid_paths = (
            "/source/manual.pdf",
            "../manual.pdf",
            "source/../../manual.pdf",
            ".",
            r"source\manual.pdf",
        )

        for path in invalid_paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                WorkspacePaths(source_snapshot=path)

    def test_workspace_paths_accept_relative_posix_paths(self) -> None:
        paths = WorkspacePaths(
            source_snapshot="source/manual.pdf",
            raw_dir="raw/capture",
            manifest_path="metadata/manifest.json",
        )

        self.assertEqual(paths.source_snapshot, "source/manual.pdf")
        self.assertEqual(paths.raw_dir, "raw/capture")
        self.assertEqual(paths.manifest_path, "metadata/manifest.json")

    def test_initial_manifest_contains_pending_capture_progress(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        self.assertEqual(manifest.capture_progress.page_count, 3)
        self.assertEqual(len(manifest.capture_progress.pages), 3)
        self.assertTrue(
            all(
                page.status is CapturePageStatus.PENDING for page in manifest.capture_progress.pages
            )
        )

    def test_manifest_keeps_identity_source_paths_and_state_separate(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
            page_count=3,
        )

        self.assertEqual(manifest.job_id, "job-test-001")
        self.assertEqual(manifest.source.sha256, "a" * 64)
        self.assertEqual(manifest.workspace.source_snapshot, "source/manual.pdf")
        self.assertEqual(
            manifest.capture_progress.pages[0].status,
            CapturePageStatus.PENDING,
        )


if __name__ == "__main__":
    unittest.main()
