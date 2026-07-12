"""Diagnostic JSON dump for PyMuPDF shadow capture and normalization.

This tool is intentionally disconnected from ManReader's legacy pipeline.
It opens one PDF page and can serialize the raw ``BackendPageCapture``,
the derived ``NormalizedPrimitivePage``, a primitive-extent ``PageAnalysis``,
or a singleton side-band ``PageAnalysis`` to stdout or to an explicitly
requested file.

The generated identifiers are diagnostic placeholders. They do not establish
the canonical identity policy for future workspace artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import fitz

from page_analysis_primitive_extent import build_primitive_extent_page_analysis
from page_analysis_serialization import page_analysis_to_dict
from page_analysis_side_band import build_singleton_side_band_page_analysis
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page

type DiagnosticStage = Literal["capture", "primitives", "analysis", "analysis-side-band"]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dump one PyMuPDF shadow page as diagnostic JSON.",
    )
    parser.add_argument(
        "pdf",
        type=Path,
        help="PDF file to inspect.",
    )
    parser.add_argument(
        "--page",
        type=_positive_page_number,
        default=1,
        help="One-based PDF page number. Default: 1.",
    )
    parser.add_argument(
        "--stage",
        choices=("capture", "primitives", "analysis", "analysis-side-band"),
        default="capture",
        help="Diagnostic stage to serialize. Default: capture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    return parser


def dump_capture(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture one page and return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="capture",
        output_path=output_path,
        compact=compact,
    )


def dump_normalized_primitives(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture and normalize one page, then return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="primitives",
        output_path=output_path,
        compact=compact,
    )


def dump_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, build primitive-extent analysis, then return its JSON representation."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis",
        output_path=output_path,
        compact=compact,
    )


def dump_singleton_side_band_page_analysis(
    pdf_path: Path,
    *,
    page_number: int = 1,
    output_path: Path | None = None,
    compact: bool = False,
) -> str:
    """Capture, normalize, and return singleton side-band analysis JSON."""

    return _dump_page(
        pdf_path,
        page_number=page_number,
        stage="analysis-side-band",
        output_path=output_path,
        compact=compact,
    )


def _dump_page(
    pdf_path: Path,
    *,
    page_number: int,
    stage: DiagnosticStage,
    output_path: Path | None,
    compact: bool,
) -> str:
    """Serialize one diagnostic stage for a one-based PDF page number."""

    if page_number < 1:
        raise ValueError("page_number must be greater than or equal to 1")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    page_index = page_number - 1
    with fitz.open(pdf_path) as document:
        if page_index >= document.page_count:
            raise ValueError(
                f"page {page_number} is outside the document (page count: {document.page_count})"
            )
        page = document.load_page(page_index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"diagnostic-page:{page_index}",
            capture_id=f"diagnostic-pymupdf-capture:{page_index}",
        )

    if stage == "capture":
        artifact_data = asdict(capture)
    elif stage == "primitives":
        primitive_page = normalize_backend_page_capture(capture)
        artifact_data = asdict(primitive_page)
    elif stage == "analysis":
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_primitive_extent_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-page-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)
    else:
        primitive_page = normalize_backend_page_capture(capture)
        analysis = build_singleton_side_band_page_analysis(
            primitive_page,
            generation_id=f"diagnostic-singleton-side-band-analysis:{page_index}",
        )
        artifact_data = page_analysis_to_dict(analysis)

    json_text = json.dumps(
        artifact_data,
        ensure_ascii=False,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
    )
    if not compact:
        json_text += "\n"

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")

    return json_text


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        json_text = _dump_page(
            args.pdf,
            page_number=args.page,
            stage=args.stage,
            output_path=args.output,
            compact=args.compact,
        )
    except (FileNotFoundError, OSError, ValueError, fitz.FileDataError) as exc:
        parser.error(str(exc))

    if args.output is None:
        sys.stdout.write(json_text)
    else:
        print(
            f"Wrote PyMuPDF shadow {args.stage} for page {args.page} to {args.output}",
            file=sys.stderr,
        )
    return 0


def _positive_page_number(value: str) -> int:
    try:
        page_number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("page must be an integer") from exc
    if page_number < 1:
        raise argparse.ArgumentTypeError("page must be greater than or equal to 1")
    return page_number


if __name__ == "__main__":
    raise SystemExit(main())
