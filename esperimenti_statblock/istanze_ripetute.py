"""Le schede costruite dalla struttura ripetuta, senza partire dai riquadri. Esplorazione.

Indicazione dell'utente, 13 settembre 2026: «la struttura ripetuta era la base per
costruirle, non le righe o simili»; il riquadro e' solo un elemento. Su Draw Steel
le schede non hanno riquadro, e le parti che si ripetono non sono coppie
etichetta/valore ma righe intere di uno stile solo («Size», «Stamina», «Signature
Ability»).

1. **Gettoni** di una riga: le etichette delle sue coppie (`field_labels`); se non
   ne ha e la riga e' di uno stile solo con lettere, il suo testo intero. Tutto
   normalizzato (`normalised_label`).
2. **Gettoni di struttura**: quelli presenti su almeno tre pagine («varie volte»).
3. **Istanze**, pagina per pagina nell'ordine di lettura: quando una riga porta un
   gettone di struttura gia' visto nell'istanza corrente, comincia un'istanza nuova.
4. **Schede**: istanze con almeno due gettoni di struttura che ne condividono
   almeno due con almeno due altre istanze (`recurs`).
5. **Nome**: per le schede, lo stile che compare piu' spesso nelle righe senza
   gettoni che precedono il primo gettone; l'inizio si sposta sulla riga di quello
   stile piu' vicina al primo gettone.

Uso:  python istanze_ripetute.py <pdf> <sigla> --verita CHIAVE[+CHIAVE] [--processi 6]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from multiprocessing import get_context
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import fitz  # noqa: E402
import pdfplumber  # noqa: E402
from prototype_ir2_page import capture_document, page_reading_facts, stat_block_inputs  # noqa: E402

from stat_block_regions import (  # noqa: E402
    _spans,
    _style,
    field_labels,
    normalised_label,
    recurs,
)

_PDF = ""
_HANDLES = None


def _open() -> None:
    global _HANDLES
    _HANDLES = (fitz.open(_PDF), pdfplumber.open(_PDF))


def _page(index: int) -> tuple[int, list[tuple[str, str, tuple[str, ...]]]]:
    """Per ogni riga: stile, testo, gettoni."""

    document, plumber = _HANDLES  # type: ignore[misc]
    try:
        facts = page_reading_facts(document, plumber, index)
    except SystemExit:
        return index, []
    _frames, _boxes, lines, _gutters = stat_block_inputs(facts)
    rows = []
    for line in lines:
        spans = _spans(line)
        if not spans:
            continue
        labels = [normalised_label(span.text) for span in field_labels(line)]
        text = "".join(primitive.text for primitive in line).strip()
        if not labels and len({_style(span) for span in spans}) == 1 and any(c.isalpha() for c in text):
            labels = [normalised_label(text)]
        rows.append((repr(_style(spans[0])), text, tuple(label for label in labels if label)))
    return index, rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("sigla")
    parser.add_argument("--verita", action="append", required=True)
    parser.add_argument("--processi", type=int, default=6)
    args = parser.parse_args(argv)
    truth = [[normalised_label(part) for part in value.split("+")] for value in args.verita]

    global _PDF
    _PDF = args.pdf
    with fitz.open(args.pdf) as document:
        pages = sorted(capture_document(document).pages)
    with get_context("fork").Pool(args.processi, initializer=_open) as pool:
        data = dict(pool.map(_page, pages, chunksize=1))

    presence: Counter[str] = Counter()
    for rows in data.values():
        presence.update({token for _s, _t, tokens in rows for token in tokens})
    structural = {token for token, pages_with in presence.items() if pages_with >= 3}

    instances = []  # (page, first row, last row, structural tokens)
    for index in pages:
        rows = data[index]
        start, seen = 0, set()
        for position, (_row_style, _text, tokens) in enumerate(rows):
            here = structural.intersection(tokens)
            if here & seen:
                instances.append((index, start, position - 1, frozenset(seen)))
                start, seen = position, set()
            seen |= here
        if rows:
            instances.append((index, start, len(rows) - 1, frozenset(seen)))

    signatures = tuple(tokens for *_x, tokens in instances)
    blocks = [inst for inst in instances if len(inst[3]) >= 2 and recurs(inst[3], signatures)]

    # Il nome: lo stile piu' frequente fra le righe senza gettoni prima del primo gettone.
    gap_styles: Counter[str] = Counter()
    firsts = []
    for index, start, end, _tokens in blocks:
        rows = data[index]
        first_token = next(
            (p for p in range(start, end + 1) if structural.intersection(rows[p][2])), start
        )
        firsts.append(first_token)
        gap_styles.update({rows[p][0] for p in range(start, first_token) if not rows[p][2]})
    name_style = gap_styles.most_common(1)[0][0] if gap_styles else None

    named = 0
    report_rows = []
    truth_in_blocks = 0
    fused = 0
    for (index, start, end, _tokens), first_token in zip(blocks, firsts, strict=True):
        rows = data[index]
        name_rows = [p for p in range(start, first_token) if rows[p][0] == name_style]
        name = rows[name_rows[-1]][1] if name_rows else ""
        named += bool(name)
        hits = sum(
            1
            for p in range(start, end + 1)
            if any(all(any(part in token for token in rows[p][2]) for part in parts) for parts in truth)
        )
        truth_in_blocks += min(hits, 1)
        fused += hits > 1
        report_rows.append((index, name, end - start + 1, hits))
    truth_total = sum(
        1
        for rows in data.values()
        for _s, _t, tokens in rows
        if any(all(any(part in token for token in tokens) for part in parts) for parts in truth)
    )
    print(f"{args.sigla}: {len(pages)} pagine, gettoni di struttura {len(structural)}, istanze {len(instances)}")
    print(f"  schede {len(blocks)}, con nome {named}, stile del nome {name_style}")
    print(f"  righe-verita' nel documento {truth_total}; schede con verita' {truth_in_blocks}, fuse (piu' verita') {fused}")
    print("  prime schede (idx, nome, righe, verita'):")
    for row in report_rows[:12]:
        print("    ", row)
    no_truth = [row for row in report_rows if row[3] == 0]
    print(f"  schede senza verita': {len(no_truth)}; esempi: {no_truth[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
