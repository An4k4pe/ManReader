"""La firma dei glifi dentro un blocco sorgente. Misura, non decide.

`Criterio_ScalaDiValori_v1.md` §0 e §1. Riporta, per ogni blocco, la sequenza dei
caratteri candidati che aprono le sue righe -- la **firma** del blocco -- e
quante volte ogni firma ricorre nel documento.

**Perche' il blocco.** La regola degli elenchi decideva il marcatore a livello di
documento e poi marcava ogni riga che si apriva con esso. Ma «questo carattere
apre voci d'elenco *in questo manuale*» non implica «queste righe *qui* sono un
elenco»: su DrM `!`, `@` e `#` stanno nello stesso blocco, uno ciascuno, e sono i
tre esiti di un tiro. Il documento dice quali caratteri sono candidati; il blocco
dice che cosa sono qui.

**Non classifica.** Stampa le firme e le loro ricorrenze; quale firma sia un
elenco e quale una scala lo decide la politica, che sta altrove e che questo
criterio deve ancora mettere alla prova.

Uso::

    ./venv/bin/python scripts/measure_block_marker_signature.py --pdf-dir . --manuali DrM FWK
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

from document_line_start_measurements import measure_document_line_starts  # noqa: E402
from document_list_policy import list_markers  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION = re.compile(r"^text:(b\d+):(l\d+):s\d+$")


def block_signatures(page, markers: frozenset[str]) -> list[tuple[str, tuple[str, ...]]]:
    """(blocco, firma) per ogni blocco che apre almeno una riga con un candidato.

    La firma tiene l'**ordine** e le **ripetizioni**: `('!', '@', '#')` non e' la
    stessa cosa di `('*', '*', '*')`, ed e' esattamente la differenza che il
    criterio dice di guardare.
    """

    per_block: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match:
            per_block[match.group(1)].append((match.group(2), primitive.text))

    signatures: list[tuple[str, tuple[str, ...]]] = []
    for block, entries in per_block.items():
        by_line: dict[str, str] = defaultdict(str)
        for line, text in entries:
            by_line[line] += text
        opening: list[str] = []
        for line in sorted(by_line):
            stripped = by_line[line].strip()
            if stripped and stripped[0] in markers:
                opening.append(stripped[0])
        if opening:
            signatures.append((block, tuple(opening)))
    return signatures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuali", nargs="+", required=True)
    parser.add_argument("--pagine", type=int, default=20)
    args = parser.parse_args()

    for name in args.manuali:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        pages = []
        with fitz.open(path) as document:
            first = max(0, len(document) // 2 - args.pagine // 2)
            for index in range(first, min(len(document), first + args.pagine)):
                page = document[index]
                if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                    continue
                capture = capture_pymupdf_page(
                    page,
                    source_id="signature",
                    page_id=f"page:{index:04d}",
                    capture_id=f"signature:{index:04d}",
                )
                pages.append(normalize_backend_page_capture(capture))

        markers = list_markers(measure_document_line_starts(pages))
        counted: Counter[tuple[str, ...]] = Counter()
        for page in pages:
            for _block, signature in block_signatures(page, markers):
                counted[signature] += 1

        shown = ", ".join(f"{c!r}" for c in sorted(markers)) or "nessuno"
        print(f"\n=== {name} — candidati: {shown}")
        print(f"{'firma del blocco':<34} {'blocchi':>8}  {'distinti':>8} {'ripetuti':>9}")
        for signature, count in counted.most_common(12):
            distinct = len(set(signature))
            repeated = len(signature) > distinct
            print(
                f"{''.join(signature)[:33]!r:<34} {count:>8}  {distinct:>8} "
                f"{'si' if repeated else 'no':>9}"
            )


if __name__ == "__main__":
    main()
