"""Tests for the standalone pdfplumber table candidate prototype."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "prototype_table_candidate_producer.py"


class PrototypeTableCandidateProducerTests(unittest.TestCase):
    def _run_script(self, pdf_bytes: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "fixture.pdf"
            pdf_path.write_bytes(pdf_bytes)
            return subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(pdf_path),
                    "1",
                    "--generation-id",
                    "test-generation",
                ],
                check=False,
                capture_output=True,
                cwd=PROJECT_ROOT,
                text=True,
            )

    def _rotated_pdf_bytes(self) -> bytes:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=400.0, height=600.0)
        page.set_rotation(180)
        return document.tobytes()

    def _cropped_pdf_bytes(self) -> bytes:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=400.0, height=600.0)
        page.set_cropbox(fitz.Rect(20.0, 30.0, 380.0, 580.0))
        return document.tobytes()

    def test_rotation_180_is_explicitly_rejected(self) -> None:
        completed = self._run_script(self._rotated_pdf_bytes())

        self.assertEqual(completed.returncode, 3)
        result = json.loads(completed.stdout)
        self.assertEqual(result["category"], "PRECONDITION_FAIL")
        self.assertIn("rotation", result["message"])
        self.assertEqual(result["fitz"]["rotation"], 180)

    def test_translated_cropbox_is_explicitly_rejected(self) -> None:
        completed = self._run_script(self._cropped_pdf_bytes())

        self.assertEqual(completed.returncode, 3)
        result = json.loads(completed.stdout)
        self.assertEqual(result["category"], "PRECONDITION_FAIL")
        self.assertIn("cropbox != mediabox", result["message"])
        self.assertEqual(result["fitz"]["rotation"], 0)


if __name__ == "__main__":
    unittest.main()
