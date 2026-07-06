"""Tests for the minimal ManReader job manifest contract."""

from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError

from job_manifest_model import (
    JOB_MANIFEST_SCHEMA_VERSION,
    JobManifest,
    JobPhase,
    JobPhaseState,
    PhaseStatus,
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

    def test_initial_manifest_has_only_authorized_pending_phases(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
        )

        self.assertEqual(manifest.schema_version, JOB_MANIFEST_SCHEMA_VERSION)
        self.assertEqual(
            manifest.phases,
            (
                JobPhaseState(JobPhase.SOURCE_SNAPSHOT, PhaseStatus.PENDING),
                JobPhaseState(JobPhase.CAPTURE, PhaseStatus.PENDING),
            ),
        )

    def test_contract_models_are_immutable(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
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
        )

        encoded = json.dumps(job_manifest_to_dict(original))
        restored = job_manifest_from_dict(json.loads(encoded))

        self.assertEqual(restored, original)
        self.assertIsInstance(restored.phases, tuple)

    def test_deserialization_rejects_wrong_scalar_types(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
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
        )

        self.assertEqual(
            set(job_manifest_to_dict(manifest)),
            {"schema_version", "job_id", "source", "workspace", "phases"},
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

    def test_manifest_rejects_duplicate_phases(self) -> None:
        duplicate = JobPhaseState(JobPhase.CAPTURE, PhaseStatus.PENDING)

        with self.assertRaises(ValueError):
            JobManifest(
                schema_version=JOB_MANIFEST_SCHEMA_VERSION,
                job_id="job-test-001",
                source=self.source,
                workspace=self.workspace,
                phases=(duplicate, duplicate),
            )

    def test_manifest_keeps_identity_source_paths_and_state_separate(self) -> None:
        manifest = initial_job_manifest(
            job_id="job-test-001",
            source=self.source,
            workspace=self.workspace,
        )

        self.assertEqual(manifest.job_id, "job-test-001")
        self.assertEqual(manifest.source.sha256, "a" * 64)
        self.assertEqual(manifest.workspace.source_snapshot, "source/manual.pdf")
        self.assertEqual(manifest.phases[0].status, PhaseStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
