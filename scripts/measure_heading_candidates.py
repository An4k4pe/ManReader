"""Le dimensioni del carattere di un manuale, e i candidati titolo. Misura, non decide.

`Criterio_Titoli_v1.md` §0 e §3, committato **con** il criterio.

Riporta per ogni manuale la dimensione del **corpo** -- la piu' frequente pesata
per **caratteri**, come `ir2_builder.body_font`, perche' un font di titolo ha
poche primitive lunghe -- e quante righe la regola del §1 promuoverebbe.

**Il numero che conta non e' la media ma la dispersione**, ed e' il motivo per cui
questo script stampa per manuale e non un totale: su Apo e Vil i candidati sono 3,
su Kul 88. La differenza non e' la regola, sono le schede mostro, dentro le quali
la dimensione piu' frequente non e' la prosa ma il testo di scheda.

Uso::

    ./venv/bin/python scripts/measure_heading_candidates.py --pdf-dir . --esempi
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION = re.compile(r"^text:(b\d+):(l\d+):s\d+$")
MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag", "DrM", "DrW",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)
# Quanto una dimensione deve superare il corpo per contare come diversa. Non e'
# una soglia della regola: e' la tolleranza con cui si leggono due float che il
# backend riporta con l'arrotondamento del PDF.
_EPSILON = 0.4
MAX_LINES_IN_A_HEADING_BLOCK = 2


def blocks_of(page) -> dict[str, list[tuple[str, float]]]:
    """Per blocco, le sue righe come (testo, dimensione massima)."""

    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match:
            grouped[match.group(1)][match.group(2)].append(primitive)

    result: dict[str, list[tuple[str, float]]] = {}
    for block, lines in grouped.items():
        entries: list[tuple[str, float]] = []
        for line in sorted(lines):
            text = "".join(p.text for p in lines[line]).strip()
            sizes = [p.font_size for p in lines[line] if p.font_size]
            if text and sizes:
                entries.append((text, round(max(sizes), 1)))
        if entries:
            result[block] = entries
    return result


def scan(pdf_path: Path, window: int) -> tuple[float, list[tuple[str, float]]]:
    characters: Counter[float] = Counter()
    pages: list[dict[str, list[tuple[str, float]]]] = []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="headings",
                page_id=f"page:{index:04d}",
                capture_id=f"headings:{index:04d}",
            )
            normalized = normalize_backend_page_capture(capture)
            for primitive in normalized.text_primitives:
                if primitive.font_size:
                    characters[round(primitive.font_size, 1)] += len(primitive.text.strip())
            pages.append(blocks_of(normalized))
    if not characters:
        return (0.0, [])

    body = characters.most_common(1)[0][0]
    found: list[tuple[str, float]] = []
    for blocks in pages:
        for entries in blocks.values():
            if len(entries) > MAX_LINES_IN_A_HEADING_BLOCK:
                continue
            if any(abs(size - body) < 0.5 for _text, size in entries):
                continue
            found.extend(
                (text, size)
                for text, size in entries
                if size > body + _EPSILON and len(text) > 1
            )
    return (body, found)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=10)
    parser.add_argument("--esempi", action="store_true")
    args = parser.parse_args()

    print(f"finestra {args.pagine} pagine contigue a meta' manuale")
    print("NOTA: l'arredo non e' ancora escluso, quindi i numeri di pagina compaiono.\n")
    print(f"{'manuale':8} {'corpo':>6} {'candidati':>10}  esempi")
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        body, found = scan(path, args.pagine)
        if not body:
            continue
        shown = "; ".join(text for text, _size in found[:3])[:56] if args.esempi else ""
        print(f"{name:8} {body:>6} {len(found):>10}  {shown}")
    print("\nLa dispersione e' il numero che conta: dove il corpo misurato e' il")
    print("testo di scheda e non la prosa, la regola promuove la prosa a titolo.")


if __name__ == "__main__":
    main()
