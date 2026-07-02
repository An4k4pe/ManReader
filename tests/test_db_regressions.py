from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PDF = REPO_ROOT / "DB.pdf"
DB_OUTPUT_DIR = REPO_ROOT / "output" / "DB"
DB_MARKDOWN = DB_OUTPUT_DIR / "DB.md"


class DBRegressionSmokeTests(unittest.TestCase):
    """Local smoke regressions for DB.pdf cases stabilized during development.

    These tests intentionally depend on a local, non-committed DB.pdf fixture.
    If DB.pdf is not present in the repository root, the class is skipped.

    The assertions are intentionally narrow:
    - check presence;
    - check relative order;
    - check known bad fusions;
    - avoid full Markdown snapshots.
    """

    markdown: str = ""

    @classmethod
    def setUpClass(cls) -> None:
        if not DB_PDF.exists():
            raise unittest.SkipTest("DB.pdf not found in repository root")

        if DB_OUTPUT_DIR.exists():
            shutil.rmtree(DB_OUTPUT_DIR)

        started_at = time.monotonic()
        print(
            "\n[DB smoke] Generating Markdown for DB.pdf pages 8-30...",
            file=sys.stderr,
            flush=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "./DB.pdf",
                "--pages",
                "8-30",
                "--no-ai",
                "--format",
                "markdown",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        elapsed = time.monotonic() - started_at
        print(
            f"[DB smoke] Extraction finished in {elapsed:.1f}s.",
            file=sys.stderr,
            flush=True,
        )

        if result.returncode != 0:
            raise AssertionError(f"DB regression extraction failed:\n{result.stdout}")

        if not DB_MARKDOWN.exists():
            raise AssertionError(f"Expected Markdown output not found: {DB_MARKDOWN}")

        cls.markdown = DB_MARKDOWN.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_page_14_callouts_are_distinct_and_have_correct_bodies(self) -> None:
        pace = _callout_body(self.markdown, "CAPACITÀ: PACE INTERIORE")
        scontroso = _callout_body(self.markdown, "CAPACITÀ: SCONTROSO")
        palmipede = _callout_body(self.markdown, "CAPACITÀ: PALMIPEDE")

        self.assertIn("Essendo un elfo", pace)
        self.assertIn("temperamento collerico", scontroso)
        self.assertIn("Essendo un mallardo", palmipede)

        self.assertNotIn("Essendo un mallardo", pace)
        self.assertNotIn("Essendo un elfo", palmipede)

    def test_page_14_does_not_regress_to_palmipede_elf_body_fusion(self) -> None:
        page_14 = _page_slice(self.markdown, 14)

        self.assertNotRegex(
            page_14,
            r"CAPACITÀ: PALMIPEDE[\s\S]{0,240}Essendo un elfo",
        )
        self.assertRegex(
            page_14,
            r"CAPACITÀ: PACE INTERIORE[\s\S]{0,240}Essendo un elfo",
        )
        self.assertRegex(
            page_14,
            r"CAPACITÀ: PALMIPEDE[\s\S]{0,240}Essendo un mallardo",
        )

    def test_page_26_altri_metodi_order_and_table_text_deduplication(self) -> None:
        page_26 = _page_slice(self.markdown, 26)

        self.assertLess(
            page_26.index("ALTRI METODI"),
            page_26.index("Agilità (AGI):"),
        )

        self.assertIn("[Tabella: p26_tbl1.csv]", page_26)
        self.assertNotIn("1–3 Giovane", page_26)
        self.assertNotIn("6 Vecchio", page_26)

    def test_page_27_derived_values_order_is_stable(self) -> None:
        page_27 = _page_slice(self.markdown, 27)

        self.assertLess(page_27.index("MOVIMENTO"), page_27.index("DANNO BONUS"))
        self.assertLess(page_27.index("DANNO BONUS"), page_27.index("PUNTI FERITA"))
        self.assertLess(page_27.index("PUNTI FERITA"), page_27.index("PUNTI VOLONTÀ"))
        self.assertLess(page_27.index("PUNTI VOLONTÀ"), page_27.index("## ABILITÀ"))

    def test_page_27_punti_volonta_is_not_duplicated(self) -> None:
        page_27 = _page_slice(self.markdown, 27)

        self.assertEqual(page_27.count("PUNTI VOLONTÀ (PV)"), 1)
        self.assertNotIn("PVè", page_27)

    def test_page_27_column_transition_starts_new_paragraph(self) -> None:
        page_27 = _page_slice(self.markdown, 27)

        self.assertIn("AGI.\n\nDANNO BONUS", page_27)
        self.assertNotIn("AGI. DANNO BONUS", page_27)

    def test_known_callouts_from_pages_8_to_30_are_rendered(self) -> None:
        expected_titles = [
            "ABBREVIAZIONI",
            "CREARE IL TUO PERSONAGGIO",
            "CAPACITÀ: ADATTABILE",
            "CAPACITÀ: RANCOROSO",
            "CAPACITÀ: DIFFICILE DA PRENDERE",
            "CAPACITÀ: PACE INTERIORE",
            "CAPACITÀ: SCONTROSO",
            "CAPACITÀ: PALMIPEDE",
            "CAPACITÀ: ISTINTI DA CACCIATORE",
            "ALTRI METODI",
            "MAGIA",
            "DEBOLEZZA",
            "CAPACITÀ ALTERNATIVE",
        ]

        for title in expected_titles:
            with self.subTest(title=title):
                self.assertIn(f"> [!INFO] {title}", self.markdown)


def _callout_body(markdown: str, title: str) -> str:
    pattern = re.compile(
        rf"^> \[!INFO\] {re.escape(title)}\n"
        rf"(?:^>\s*$\n)?"
        rf"(?P<body>(?:^> .*(?:\n|$))+)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if match is None:
        raise AssertionError(f"Callout not found: {title}")
    return match.group("body")


def _page_slice(markdown: str, page_num: int) -> str:
    start_marker = f"<!-- page: {page_num} -->"
    next_marker = f"<!-- page: {page_num + 1} -->"

    start = markdown.find(start_marker)
    if start == -1:
        raise AssertionError(f"Page marker not found: {start_marker}")

    end = markdown.find(next_marker, start + len(start_marker))
    if end == -1:
        return markdown[start:]

    return markdown[start:end]


if __name__ == "__main__":
    unittest.main()
