"""Le schede dalla struttura che si ripete: etichette che si contano insieme. Esplorazione.

Indicazione dell'utente, 13 settembre 2026: la struttura ripetuta e' la base, il
riquadro solo un aiuto. Il segnale, senza soglie: **le etichette di una stessa
struttura compaiono lo stesso numero di volte sulla stessa pagina**. Draw Steel:
4 mostri, 4 Immunity, 4 Movement, 4 Weakness, ma 11 Effect. Daggerheart: 12
avversari, 12 Difficulty, 12 Thresholds.

1. **Etichette**: quelle delle coppie etichetta/valore (`field_labels`),
   normalizzate. Una riga di uno stile solo non porta etichette.
2. **Legame**: due etichette sono legate se compaiono insieme su almeno tre pagine
   («varie volte») e, sulle pagine dove compare la piu' rara delle due, hanno lo
   stesso conteggio nella maggioranza dei casi.
3. **Strutture**: componenti connesse dei legami, con almeno due etichette.
4. **Istanze**: per pagina, nell'ordine di lettura, le righe con etichette di una
   struttura; un'istanza nuova comincia quando un'etichetta gia' vista
   nell'istanza corrente ricompare.
5. **Nome**: lo stile che precede la prima riga d'istanza nella maggioranza delle
   istanze della struttura, cercato all'indietro riga per riga; il nome e' la
   riga piu' vicina in quello stile.

Uso:  python strutture_contate.py <pdf> <sigla> --verita ETICHETTA [--processi 6]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from multiprocessing import get_context
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import fitz  # noqa: E402
import pdfplumber  # noqa: E402
from prototype_ir2_page import capture_document, page_reading_facts, stat_block_inputs  # noqa: E402

from stat_block_regions import _spans, _style, field_labels, normalised_label  # noqa: E402

_PDF = ""
_HANDLES = None


def _open() -> None:
    global _HANDLES
    _HANDLES = (fitz.open(_PDF), pdfplumber.open(_PDF))


def _page(index: int):
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
        found = [(normalised_label(s.text), s) for s in field_labels(line)]
        labels = tuple(label for label, _s in found if label)
        # x0 e larghezza di un carattere delle etichette: servono al test «tabella».
        where = tuple(
            (round(s.bbox[0], 1), (s.bbox[2] - s.bbox[0]) / max(len(s.text.strip()), 1))
            for label, s in found
            if label
        )
        style = _style(spans[0])
        box = (
            min(s.bbox[0] for s in spans), min(s.bbox[1] for s in spans),
            max(s.bbox[2] for s in spans), max(s.bbox[3] for s in spans),
        )
        rows.append((repr(style), "".join(p.text for p in line).strip(), labels, where, style[1], box))
    return index, rows


def structures(data: dict[int, list]) -> list[frozenset[str]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for index, rows in data.items():
        for _style_, _text, labels, *_rest in rows:
            for label in labels:
                counts[label][index] += 1
    labels = [label for label, per_page in counts.items() if len(per_page) >= 3]
    near: dict[str, set[str]] = {label: set() for label in labels}
    for i, a in enumerate(labels):
        pages_a = counts[a]
        for b in labels[i + 1 :]:
            pages_b = counts[b]
            together = pages_a.keys() & pages_b.keys()
            if len(together) < 3:
                continue
            rarer = pages_a if len(pages_a) <= len(pages_b) else pages_b
            equal = sum(1 for page in rarer if pages_a.get(page, 0) == pages_b.get(page, 0))
            if equal * 2 > len(rarer):
                near[a].add(b)
                near[b].add(a)
    seen: set[str] = set()
    found = []
    for start in labels:
        if start in seen or not near[start]:
            continue
        stack, group = [start], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            group.add(node)
            stack.extend(near[node] - seen)
        found.append(frozenset(group))
    return sorted(found, key=len, reverse=True)


def instances(rows: list, structure: frozenset[str]) -> list[tuple[int, int]]:
    """(prima riga, ultima riga con etichette) per ogni istanza della pagina."""

    found: list[tuple[int, int]] = []
    start = last = None
    seen: set[str] = set()
    for position, (_style_, _text, labels, *_rest) in enumerate(rows):
        here = structure.intersection(labels)
        if not here:
            continue
        if start is not None and here & seen:
            if len(seen) >= 2:
                found.append((start, last))
            start, seen = None, set()
        if start is None:
            start = position
        seen |= here
        last = position
    if start is not None and len(seen) >= 2:
        found.append((start, last))
    return found


def table_like(rows: list, a: int, b: int, structure: frozenset[str]) -> bool:
    """«Righe tutte ordinate»: ogni riga con etichette della struttura ne porta una
    sola, e ogni etichetta ha almeno un'altra etichetta dell'istanza che comincia
    alla stessa x entro un carattere -- stanno in colonna. In una scheda almeno una
    riga porta piu' etichette o un'etichetta sola nella sua x."""

    starts = []
    for p in range(a, b + 1):
        mine = [w for label, w in zip(rows[p][2], rows[p][3], strict=True) if label in structure]
        if not mine:
            continue
        if len(mine) > 1:
            return False
        starts.append(mine[0])
    if len(starts) < 2:
        return False
    return all(
        any(j != i and abs(x - other[0]) < min(w, other[1]) for j, other in enumerate(starts))
        for i, (x, w) in enumerate(starts)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("sigla")
    parser.add_argument("--verita", required=True)
    parser.add_argument("--processi", type=int, default=6)
    args = parser.parse_args(argv)
    truth = normalised_label(args.verita)

    global _PDF
    _PDF = args.pdf
    with fitz.open(args.pdf) as document:
        pages = sorted(capture_document(document).pages)
    with get_context("fork").Pool(args.processi, initializer=_open) as pool:
        data = dict(pool.map(_page, pages, chunksize=1))

    truth_lines = sum(1 for rows in data.values() for row in rows if truth in row[2])
    print(f"{args.sigla}: {len(pages)} pagine, righe con '{truth}': {truth_lines}")
    candidates = []
    for structure in structures(data):
        found = [(index, a, b) for index in pages for a, b in instances(data[index], structure)]
        if len(found) < 3:
            continue
        tables = sum(1 for index, a, b in found if table_like(data[index], a, b, structure))
        candidates.append((structure, found, tables * 2 > len(found)))
    # Le strutture con piu' istanze si prendono le righe per prime.
    candidates.sort(key=lambda c: len(c[1]), reverse=True)
    taken: dict[int, set[int]] = defaultdict(set)
    total_truth = 0
    for structure, found, is_table in candidates:
        kept = []
        for index, a, b in found:
            span = set(range(a, b + 1))
            if span & taken[index]:
                continue
            kept.append((index, a, b))
        if is_table:
            print(f"  TABELLA {sorted(structure)[:6]}: {len(kept)} istanze")
            continue
        # La scheda si prende anche la coda: fino alla riga prima dell'istanza
        # successiva della stessa struttura sulla pagina.
        by_page: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for index, a, b in kept:
            by_page[index].append((a, b))
        for index, spans in by_page.items():
            spans.sort()
            for k, (a, b) in enumerate(spans):
                end = spans[k + 1][0] - 1 if k + 1 < len(spans) else b
                taken[index].update(range(a, end + 1))
        # Il nome: fra gli stili presenti nella maggioranza degli spazi prima delle
        # istanze, il piu' grande.
        gaps = []
        previous_end: dict[int, int] = {}
        for index, a, b in sorted(kept):
            start = previous_end.get(index, -1) + 1
            gaps.append((index, start, a))
            previous_end[index] = b
        presence: Counter[tuple[str, float]] = Counter()
        for index, start, a in gaps:
            rows = data[index]
            presence.update({(rows[p][0], rows[p][4]) for p in range(start, a) if not rows[p][2]})
        majority = [key for key, n in presence.items() if n * 2 > len(gaps)]
        head = max(majority, key=lambda key: key[1])[0] if majority else None
        named, with_truth, fused, examples = 0, 0, 0, []
        for index, start, a in gaps:
            rows = data[index]
            b = next(bb for ii, aa, bb in kept if ii == index and aa == a)
            name = next((rows[p][1] for p in range(a - 1, start - 1, -1) if rows[p][0] == head), "")
            named += bool(name)
            hits = sum(1 for p in range(a, b + 1) if truth in rows[p][2])
            with_truth += hits >= 1
            fused += hits > 1
            if name and len(examples) < 8:
                examples.append((index, name[:28]))
        total_truth += with_truth
        print(
            f"  SCHEDA {sorted(structure)[:8]}\n"
            f"     istanze {len(kept)}, con nome {named}, con verita' {with_truth}, fuse {fused}\n"
            f"     nomi {examples}"
        )
    print(f"  verita' coperta da schede: {total_truth} su {truth_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
