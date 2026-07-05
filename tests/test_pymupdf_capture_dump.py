from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import fitz

from pymupdf_capture_dump import dump_capture, main


class PyMuPDFCaptureDumpTest(unittest.TestCase):
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

    def test_main_prints_json_to_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "sample.pdf"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()

            with redirect_stdout(stdout):
                return_code = main((str(pdf_path), "--page", "1"))

            self.assertEqual(return_code, 0)
            self.assertEqual(
                json.loads(stdout.getvalue())["text_observations"][0]["text"],
                "CLI text",
            )

    def test_main_writes_file_and_reports_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "sample.pdf"
            output_path = root / "capture.json"
            _create_pdf(pdf_path, ("CLI text",))
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                return_code = main(
                    (
                        str(pdf_path),
                        "--output",
                        str(output_path),
                    )
                )

            self.assertEqual(return_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output_path.is_file())
            self.assertIn("Wrote PyMuPDF shadow capture", stderr.getvalue())


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
