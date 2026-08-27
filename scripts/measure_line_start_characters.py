"""Quali caratteri aprono le righe di un manuale, e quante volte compaiono altrove.

E' la misura del §0 e del §1 di `Criterio_Elenchi_v1.md`, committata **con** il
criterio e non dopo: `AGENTS.MD` §18, e su questo progetto il debito identico e'
gia' stato iscritto due volte e pagato tardi una volta.

**Misura e basta.** Non decide che cosa sia un marcatore d'elenco: riporta, per
ogni carattere non alfanumerico, quante righe apre (INIZ) e quante volte compare
in tutto il testo (TOT). La politica sta altrove, come per la ricorrenza
d'arredo, e legge questi due numeri.

**Perche' i due numeri e non uno.** Un elenco cablato su `•*-` prenderebbe **3
manuali su 16**: il marcatore cambia da manuale a manuale ed e' spesso il
codepoint di un font di simboli -- `✦` su DB, `\\x8b` su BoB, `!@#` su DrM, `¥£®`
su DrW. Cio' che separa un marcatore dalla punteggiatura non e' quale carattere
sia, ma **dove vive**: il marcatore vive a inizio riga, la punteggiatura vive in
mezzo alle frasi. INIZ/TOT e' quel rapporto.

Uso::

    ./venv/bin/python scripts/measure_line_start_characters.py --pdf-dir . --pagine 20
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION = re.compile(r"text:b(\d+):l(\d+):")


def source_lines(page) -> list[tuple[str, str]]:
    """(blocco, testo) per ogni riga sorgente della pagina, in ordine di x."""

    by_line: dict[tuple[str, str], list] = collections.defaultdict(list)
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match:
            by_line[(match.group(1), match.group(2))].append(primitive)
    lines = []
    for (block, _line), primitives in by_line.items():
        text = "".join(p.text for p in sorted(primitives, key=lambda z: z.bbox[0]))
        lines.append((block, text))
    return lines


def measure(pdf_path: Path, sample: int) -> tuple[collections.Counter, collections.Counter, int]:
    """(righe aperte per carattere, occorrenze totali, righe esaminate)."""

    initial: collections.Counter = collections.Counter()
    total: collections.Counter = collections.Counter()
    seen = 0
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - sample // 2)
        for index in range(first, min(len(document), first + sample)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="line-starts",
                page_id=f"page:{index:04d}",
                capture_id=f"line-starts:{index:04d}",
            )
            for _block, text in source_lines(normalize_backend_page_capture(capture)):
                for character in text:
                    if not character.isalnum() and not character.isspace():
                        total[character] += 1
                stripped = text.strip()
                if not stripped:
                    continue
                seen += 1
                head = stripped[0]
                if not head.isalnum() and not head.isspace():
                    initial[head] += 1
    return initial, total, seen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=20)
    parser.add_argument("--manuali", nargs="+")
    parser.add_argument(
        "--min-righe",
        type=int,
        default=5,
        help="quante righe un carattere deve aprire per essere STAMPATO; e' una "
             "soglia di riporto, non della regola, e la regola sta altrove",
    )
    args = parser.parse_args()

    names = args.manuali or sorted(p.stem for p in args.pdf_dir.glob("*.pdf"))
    print(f"finestra {args.pagine} pagine contigue a meta' manuale\n")
    print(f"{'manuale':10} {'car':>6} {'unicode':<9} {'INIZ':>5} {'TOT':>6} {'quota':>6}")
    grand_lines = 0
    for name in names:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        initial, total, seen = measure(path, args.pagine)
        grand_lines += seen
        rows = [
            (character, count, total[character])
            for character, count in initial.items()
            if count >= args.min_righe
        ]
        for character, count, whole in sorted(rows, key=lambda r: -r[1]):
            share = count / whole if whole else 0.0
            print(
                f"{name:10} {character!r:>6} U+{ord(character):04X}  "
                f"{count:>5} {whole:>6} {share:>6.0%}"
            )
    print(f"\nrighe sorgente esaminate: {grand_lines}")
    print("INIZ = righe aperte dal carattere, TOT = sue occorrenze nel testo.")
    print("La quota alta dice che il carattere vive a inizio riga, non nelle frasi.")


if __name__ == "__main__":
    main()
