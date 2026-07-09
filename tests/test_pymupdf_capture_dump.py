from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import fitz

from pymupdf_capture_dump import (
    build_argument_parser,
    dump_capture,
    dump_normalized_primitives,
    dump_page_analysis,
    main,
)


class PyMuPDFCaptureDumpTest(unittest.TestCase):
    def test_parser_accepts_analysis_stage(self) -> None:
        args = build_argument_parser().parse_args(("sample.pdf", "--stage", "analysis"))

        self.assertEqual(args.stage, "analysis")

    def test_dump_capture_returns_pretty_json_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("First page", "Second page"))

            json_text = dump_capture(pdf_path, page_number=2)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(payload["page_index"], 1)
            self.assertEqual(payload["page_id"], "diagnostic-page:1")
            self.assertEqual(
                payload["capture_id"],
                "diagnostic-pymupdf-capture:1",
            )
            self.assertEqual(
                [item["text"] for item in payload["text_observations"]],
                ["Second page"],
            )
            self.assertEqual(list(Path(temporary_directory).glob("*.json")), [])

    def test_dump_normalized_primitives_returns_derived_page_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Normalized page",))

            json_text = dump_normalized_primitives(pdf_path)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(
                payload["source_capture_id"],
                "diagnostic-pymupdf-capture:0",
            )
            self.assertEqual(payload["source_id"], "diagnostic-source")
            self.assertEqual(payload["page_id"], "diagnostic-page:0")
            self.assertEqual(payload["page_index"], 0)
            self.assertEqual(
                payload["capture_to_canonical_transform"],
                [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            )
            self.assertEqual(
                [item["text"] for item in payload["text_primitives"]],
                ["Normalized page"],
            )
            self.assertNotIn("text_observations", payload)
            self.assertNotIn("backend_order", payload)

    def test_dump_page_analysis_returns_empty_validated_analysis_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Analysis page",))

            json_text = dump_page_analysis(pdf_path)
            payload = json.loads(json_text)

            self.assertTrue(json_text.endswith("\n"))
            self.assertEqual(payload["schema_version"], "1.1")
            self.assertEqual(payload["generation_id"], "diagnostic-page-analysis:0")
            self.assertEqual(payload["page_id"], "diagnostic-page:0")
            self.assertEqual(payload["regions"], [])
            self.assertEqual(payload["relations"], [])
            self.assertEqual(
                payload["provenance"],
                {
                    "source_id": "diagnostic-source",
                    "source_capture_id": "diagnostic-pymupdf-capture:0",
                    "source_page_id": "diagnostic-page:0",
                    "source_primitive_schema_version": "1",
                    "producer_name": "pymupdf-capture-dump",
                    "producer_version": "0.1",
                    "configuration_id": "empty-page-analysis-v1",
                },
            )

    def test_dump_page_analysis_compact_output_has_no_final_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Compact analysis",))

            json_text = dump_page_analysis(pdf_path, compact=True)

            self.assertFalse(json_text.endswith("\n"))
            self.assertEqual(json.loads(json_text)["regions"], [])

    def test_dump_page_analysis_writes_requested_output_and_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "analysis.json"
            _create_pdf(pdf_path, ("Analysis file",))

            returned = dump_page_analysis(pdf_path, output_path=output_path)

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertTrue(returned.endswith("\n"))
            self.assertEqual(json.loads(returned)["generation_id"], "diagnostic-page-analysis:0")

    def test_dump_page_analysis_is_deterministic_for_same_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Deterministic analysis",))

            first = dump_page_analysis(pdf_path)
            second = dump_page_analysis(pdf_path)

            self.assertEqual(first, second)

    def test_analysis_stage_does_not_change_capture_or_primitives_dump(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Stable diagnostics",))
            capture_before = dump_capture(pdf_path)
            primitives_before = dump_normalized_primitives(pdf_path)

            dump_page_analysis(pdf_path)

            self.assertEqual(dump_capture(pdf_path), capture_before)
            self.assertEqual(dump_normalized_primitives(pdf_path), primitives_before)

    def test_synthetic_pdf_traverses_full_analysis_chain_without_legacy_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("Full chain",))

            payload = json.loads(dump_page_analysis(pdf_path))

            self.assertEqual(payload["schema_version"], "1.1")
            self.assertEqual(payload["provenance"]["producer_name"], "pymupdf-capture-dump")
            self.assertEqual(payload["regions"], [])
            self.assertEqual(payload["relations"], [])

    def test_dump_capture_writes_only_when_output_is_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "capture.json"
            _create_pdf(pdf_path, ("Text",))

            returned = dump_capture(
                pdf_path,
                output_path=output_path,
                compact=True,
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertNotIn("\n", returned)
            self.assertEqual(json.loads(returned)["page_index"], 0)

    def test_dump_normalized_primitives_writes_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "diagnostics" / "primitives.json"
            _create_pdf(pdf_path, ("Text",))

            returned = dump_normalized_primitives(
                pdf_path,
                output_path=output_path,
                compact=True,
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(output_path.read_text(encoding="utf-8"), returned)
            self.assertIn("text_primitives", json.loads(returned))

    def test_dump_capture_rejects_missing_pdf_and_invalid_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missing = root / "missing.pdf"
            with self.assertRaises(FileNotFoundError):
                dump_capture(missing)

            pdf_path = root / "sample.pdf"
            _create_pdf(pdf_path, ("Only page",))
            with self.assertRaises(ValueError):
                dump_capture(pdf_path, page_number=0)
            with self.assertRaises(ValueError):
                dump_capture(pdf_path, page_number=2)

    def test_main_prints_capture_json_to_stdout_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--page", "1"))

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["text_observations"][0]["text"], "CLI text")
            self.assertNotIn("text_primitives", payload)

    def test_main_prints_analysis_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI analysis",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--stage", "analysis"))

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema_version"], "1.1")
            self.assertEqual(payload["regions"], [])
            self.assertNotIn("text_observations", payload)
            self.assertNotIn("text_primitives", payload)

    def test_main_prints_primitive_json_for_requested_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI primitives",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "primitives",
                    )
                )

            self.assertEqual(return_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                payload["text_primitives"][0]["text"],
                "CLI primitives",
            )
            self.assertNotIn("text_observations", payload)

    def test_main_writes_file_and_reports_stage_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "primitives.json"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "primitives",
                        "--output",
                        str(output_path),
                    )
                )

            self.assertEqual(return_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output_path.is_file())
            self.assertIn("Wrote PyMuPDF shadow primitives", stderr.getvalue())

    def test_main_writes_analysis_file_and_reports_stage_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "analysis.json"
            _create_pdf(pdf_path, ("CLI analysis file",))
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                return_code = main(
                    (
                        str(pdf_path),
                        "--stage",
                        "analysis",
                        "--output",
                        str(output_path),
                    )
                )

            self.assertEqual(return_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output_path.is_file())
            self.assertIn("Wrote PyMuPDF shadow analysis", stderr.getvalue())


def _create_pdf(path: Path, page_texts: tuple[str, ...]) -> None:
    document = fitz.open()
    try:
        for text in page_texts:
            page = document.new_page(width=200.0, height=300.0)
            page.insert_text((20.0, 40.0), text)
        document.save(path)
    finally:
        document.close()


if __name__ == "__main__":
    unittest.main()
