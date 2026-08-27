"""La barra di regressione di `Criterio_ScalaDiValori_v1.md` §4.B.

I quattro blocchi che `Esito_Elenchi_v1.md` §5 ha giudicato **elenchi veri**
devono restare classificati elenco. E' la barra che impedisce di comprare
precisione perdendo tutto: una regola che non classificasse mai `elenco`
passerebbe meta' del veto a pieni voti.

La verita' di riferimento non e' mia: viene da un giudizio cieco gia' fatto, ed e'
l'unico pezzo di questo criterio che non ho scelto io.

Uso::

    ./venv/bin/python scripts/check_list_regression.py --pdf-dir .
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_line_start_measurements import (  # noqa: E402
    count_block_signatures,
    measure_document_line_starts,
    source_lines,
)
from document_list_policy import (  # noqa: E402
    list_item_flags,
    list_markers,
    value_scale_signatures,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

# (manuale, indice di pagina, carattere, voce dell'esito precedente). Il
# marcatore di BoB e' un codepoint di font simboli e si scrive con l'escape.
TARGETS = (
    ("FWK", 119, "\u2022", "03"),
    ("FWK", 117, "\u2022", "10"),
    ("BoB", 226, "\x8b", "05"),
    ("FW", 160, "\u2022", "08"),
)


def items_on(pdf_path: Path, index: int, character: str, window: int) -> int | None:
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - window // 2)
        pages, indices = [], []
        for position in range(first, min(len(document), first + window)):
            page = document[position]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="regression",
                page_id=f"page:{position:04d}",
                capture_id=f"regression:{position:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            indices.append(position)
        if index not in indices:
            return None
        markers = list_markers(measure_document_line_starts(pages))
        scales = value_scale_signatures(count_block_signatures(pages, markers))
        page = pages[indices.index(index)]
        lines = list(source_lines(page))
        flags = list_item_flags(lines, markers, scales)
        return sum(
            1
            for (_block, text), flag in zip(lines, flags, strict=True)
            if flag and text.strip().startswith(character)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=20)
    args = parser.parse_args()

    print("Barra §4.B — i quattro elenchi giudicati veri devono restare elenchi\n")
    print(f"{'voce':>5} {'manuale':8} {'idx':>5} {'righe ancora voci':>18}  esito")
    holds = True
    for name, index, character, label in TARGETS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"{label:>5} {name:8} MANCANTE")
            continue
        count = items_on(path, index, character, args.pagine)
        if count is None:
            print(f"{label:>5} {name:8} {index:>5} {'FUORI FINESTRA':>18}  n/d")
            continue
        good = count >= 2
        holds &= good
        print(f"{label:>5} {name:8} {index:>5} {count:>18}  {'ok' if good else 'CADE'}")
    print("\nREGGE" if holds else "\nCADE")


if __name__ == "__main__":
    main()
