"""Il giudizio esaustivo di `Criterio_ElencoNumerato_v1.md` §3.

**Non un campione.** Le righe che aprono con un numero sono ~36 su tutto il
corpus: si guardano tutte. Un campione qui sarebbe piu' debole e non piu'
economico, e lascerebbe fuori proprio i casi rari che decidono.

Stampa **due** elenchi:

- le righe che la regola **riconosce** come voci numerate;
- le righe che aprono con un numero e che la regola **scarta**, col motivo.

Il secondo e' la parte che un campione non avrebbe: e' li' che si vede se la
regola manca qualcosa.

Uso::

    ./venv/bin/python scripts/check_numbered_lists.py --pdf-dir .
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_line_start_measurements import source_lines  # noqa: E402
from document_list_policy import numbered_item_flags, split_number  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

MANUALS = (
    "Apo", "BiD", "BoB", "DB", "DIE", "Dag", "DrM", "DrW",
    "FW", "FWK", "Fab", "Kul", "Lan", "SV", "Vil", "Wil",
)


def scan(pdf_path: Path, window: int) -> tuple[list[str], list[str]]:
    taken: list[str] = []
    left: list[str] = []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        for index in range(first, min(len(document), first + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="numbered",
                page_id=f"page:{index:04d}",
                capture_id=f"numbered:{index:04d}",
            )
            lines = [
                (block, text.strip())
                for block, text in source_lines(normalize_backend_page_capture(capture))
            ]
            flags = numbered_item_flags(lines)
            for (block, text), flag in zip(lines, flags, strict=True):
                if split_number(text) is None:
                    continue
                entry = f"idx {index:>4} {block:>6}  {text[:70]!r}"
                (taken if flag else left).append(entry)
    return taken, left


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=20)
    args = parser.parse_args()

    all_taken: dict[str, list[str]] = {}
    all_left: dict[str, list[str]] = {}
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        taken, left = scan(path, args.pagine)
        if taken:
            all_taken[name] = taken
        if left:
            all_left[name] = left

    total_taken = sum(len(v) for v in all_taken.values())
    total_left = sum(len(v) for v in all_left.values())

    print(f"=== RICONOSCIUTE come voci numerate: {total_taken}\n")
    for name, entries in all_taken.items():
        print(f"  {name}")
        for entry in entries:
            print(f"    {entry}")
    if not all_taken:
        print("  nessuna")

    print(f"\n=== SCARTATE, pur aprendo con un numero: {total_left}\n")
    for name, entries in all_left.items():
        print(f"  {name}")
        for entry in entries:
            print(f"    {entry}")
    if not all_left:
        print("  nessuna")

    print(f"\ntotale righe che aprono con un numero: {total_taken + total_left}")
    print("Il §4.A chiede zero errori in ENTRAMBI gli elenchi, e non e' un campione.")


if __name__ == "__main__":
    main()
