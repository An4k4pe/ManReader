"""Le righe visive ricostruite geometricamente contro le righe della sorgente.

Domanda: `_group_visual_lines` in `compare_reading_order_with_column_bands.py`
ricava la riga tipografica dalla sovrapposizione delle y, buttando via il
`l{line_index}` che `pymupdf_capture.py:123-125` mette gia' nel
`source_observation_id` di ogni span. Questo script confronta i due
raggruppamenti sulle stesse primitive e riporta dove divergono.

Serve a decidere se l'assemblaggio geometrico aggiunga qualcosa o reinventi
peggio un'informazione gia' disponibile. Non giudica il reading order fra
righe, che e' un problema diverso e di competenza di `column_band`.

`--page` e' un indice POSIZIONALE (`page_index = N - 1`), non il numero
stampato: vedi `CLAUDE.md`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from compare_reading_order_with_column_bands import _group_visual_lines  # noqa: E402
from primitive_model import TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION_ID = re.compile(r"^text:b(\d+):l(\d+):s(\d+)$")


def _source_line_key(primitive: TextPrimitive) -> tuple[int, int] | None:
    """La riga secondo la sorgente: `(block_index, line_index)` dall'id."""

    match = _OBSERVATION_ID.match(primitive.source_observation_id or "")
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _source_lines(
    primitives: list[TextPrimitive],
) -> tuple[list[list[TextPrimitive]], int]:
    grouped: dict[tuple[int, int], list[TextPrimitive]] = {}
    unparsed = 0
    for primitive in primitives:
        key = _source_line_key(primitive)
        if key is None:
            unparsed += 1
            continue
        grouped.setdefault(key, []).append(primitive)
    lines = [
        sorted(line, key=lambda p: p.bbox[0])
        for _key, line in sorted(grouped.items(), key=lambda item: item[0])
    ]
    return lines, unparsed


def _partition(lines: list[list[TextPrimitive]]) -> set[frozenset[int]]:
    return {frozenset(id(primitive) for primitive in line) for line in lines}


def _describe(line: list[TextPrimitive]) -> str:
    keys = sorted({_source_line_key(p) for p in line} - {None})
    # In ordine di sorgente (`b:l:s`), non nell'ordine in cui capitano: una
    # versione precedente iterava un insieme e stampava testo scombinato,
    # facendolo sembrare un difetto dei dati.
    ordered = sorted(line, key=lambda p: p.source_observation_id or "")
    text = "".join(p.text for p in ordered)
    if len(text) > 90:
        text = text[:87] + "..."
    y0 = min(p.bbox[1] for p in line)
    y1 = max(p.bbox[3] for p in line)
    key_label = " ".join(f"b{b}:l{ln}" for b, ln in cast(list, keys))
    return f"y {y0:.2f}-{y1:.2f}  [{key_label}]  {text!r}"


def run(pdf_path: Path, page_number: int, y_range: tuple[float, float] | None) -> int:
    page_index = page_number - 1
    with fitz.open(pdf_path) as document:
        if not 0 <= page_index < document.page_count:
            print(f"pagina fuori range: {page_number}", file=sys.stderr)
            return 1
        page = document.load_page(page_index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{page_number:04d}",
            capture_id=f"span-line-identity:{page_index}",
        )

    primitives = list(normalize_backend_page_capture(capture).text_primitives)
    if y_range is not None:
        low, high = y_range
        primitives = [p for p in primitives if p.bbox[1] < high and p.bbox[3] > low]

    if not primitives:
        print("nessuna primitiva testuale nel perimetro richiesto")
        return 0

    geometric = _group_visual_lines(primitives)
    source, unparsed = _source_lines(primitives)

    print(f"{pdf_path.name} pagina posizionale {page_number} (indice {page_index})")
    if y_range is not None:
        print(f"finestra y: {y_range[0]}-{y_range[1]}")
    print(f"span: {len(primitives)}   id non interpretabili: {unparsed}")
    print(f"righe geometriche: {len(geometric)}   righe da sorgente: {len(source)}")

    geometric_partition = _partition(geometric)
    source_partition = _partition(source)
    if geometric_partition == source_partition:
        print("\nI due raggruppamenti COINCIDONO: partizione identica.")
        return 0

    only_geometric = geometric_partition - source_partition
    only_source = source_partition - geometric_partition
    print(
        f"\nI due raggruppamenti DIVERGONO: "
        f"{len(only_geometric)} righe solo geometriche, "
        f"{len(only_source)} righe solo da sorgente."
    )

    by_id = {id(p): p for p in primitives}
    print("\n-- righe prodotte SOLO dall'assemblaggio geometrico --")
    for group in sorted(only_geometric, key=lambda g: min(by_id[i].bbox[1] for i in g)):
        print("  " + _describe([by_id[i] for i in group]))
    print("\n-- righe prodotte SOLO dalla sorgente --")
    for group in sorted(only_source, key=lambda g: min(by_id[i].bbox[1] for i in g)):
        print("  " + _describe([by_id[i] for i in group]))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="indice POSIZIONALE (page_index = N - 1), non il numero stampato",
    )
    parser.add_argument(
        "--y-range",
        type=float,
        nargs=2,
        metavar=("Y0", "Y1"),
        default=None,
        help="limita l'analisi agli span che intersecano questa fascia y",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1
    y_range = tuple(args.y_range) if args.y_range else None
    return run(pdf_path, args.page, cast("tuple[float, float] | None", y_range))


if __name__ == "__main__":
    raise SystemExit(main())
