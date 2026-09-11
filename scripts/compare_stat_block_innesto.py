"""Confronto prima/dopo dell'innesto delle schede in IR 2.

`Criterio_SchedaInIR2_v1.md`, predizioni R2, R3 e R4. Legge due uscite di
`main_ir2.py` sullo stesso intervallo -- prima e dopo l'innesto, ciascuna con il
suo `document.md` e il suo `document_ir2.json` -- e il log del giro «dopo»,
eseguito con `--processi 1` perche' le righe `schede:` escano nell'ordine delle
pagine.

  R3  le pagine che cambiano stanno fra quelle dove l'innesto ha trovato
      almeno una scheda; senza tabelle, ogni pagina con un nome cambia;
  R4  sulle pagine che cambiano, i caratteri non-spazio del TESTO dell'IR --
      nodi e celle, non la sintassi del Markdown -- sono gli stessi prima e
      dopo. La versione sul Markdown, tolti `#` e `*`, si riporta anche: su
      una tabella non costruita conta come «persi» i `|` della sintassi, ed e'
      la ragione per cui il controllo che decide e' quello sull'IR;
  R2  i titoli nuovi, con il loro livello, da leggere.

Uso:  python scripts/compare_stat_block_innesto.py <prima/document.md>
          <dopo/document.md> <dopo.log>
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

_PAGE = re.compile(r"^<!-- page:(\d+) -->\n", re.MULTILINE)
_SCHEDE = re.compile(
    r"^schede: (\d+) regioni, (\d+) con nome, titolo h(\d)(?:, (\d+) tabelle attraverso una scheda)?",
    re.MULTILINE,
)


def markdown_pages(path: Path) -> dict[int, str]:
    parts = _PAGE.split(path.read_text(encoding="utf-8"))
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def _texts(value: object) -> list[str]:
    """Le stringhe `text` di una struttura, a qualunque profondita'."""

    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            if key == "text" and isinstance(item, str):
                found.append(item)
            else:
                found.extend(_texts(item))
        return found
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return []


def ir_pages(path: Path) -> dict[int, Counter[str]]:
    """Per pagina, i caratteri non-spazio del testo dei nodi e delle celle.

    I `runs` ripetono il testo del nodo e si saltano; le note d'asset non
    portano testo."""

    document = json.loads(path.read_text(encoding="utf-8"))
    pages: dict[int, Counter[str]] = {}
    for page in document["pages"]:
        counter: Counter[str] = Counter()
        for node in page["nodes"]:
            texts = [node["text"]] if isinstance(node.get("text"), str) else []
            texts.extend(_texts(node.get("structure")))
            for text in texts:
                counter.update(c for c in text if not c.isspace())
        pages[int(page["page_id"].split(":")[1])] = counter
    return pages


def markdown_characters(text: str) -> Counter[str]:
    return Counter(c for c in text if not c.isspace() and c not in "#*")


def main(argv: list[str]) -> int:
    before_md, after_md = Path(argv[1]), Path(argv[2])
    before, after = markdown_pages(before_md), markdown_pages(after_md)
    before_ir = ir_pages(before_md.with_name("document_ir2.json"))
    after_ir = ir_pages(after_md.with_name("document_ir2.json"))
    log = [match.groups() for match in _SCHEDE.finditer(Path(argv[3]).read_text(encoding="utf-8"))]
    markers = sorted(after)
    if sorted(before) != markers:
        print(f"FAIL: pagine diverse prima {len(before)} e dopo {len(after)}")
        return 1
    if len(log) != len(markers):
        print(f"FAIL: {len(log)} righe `schede:` nel log per {len(markers)} pagine")
        return 1

    tables_on = any(entry[3] is not None for entry in log)
    with_regions = [m for m, entry in zip(markers, log, strict=True) if int(entry[0]) > 0]
    named = [m for m, entry in zip(markers, log, strict=True) if int(entry[1]) > 0]
    changed = [m for m in markers if before[m] != after[m]]
    print(
        f"pagine {len(markers)}, regioni scheda {sum(int(e[0]) for e in log)}, "
        f"pagine con una scheda {len(with_regions)}, con un nome {len(named)}, "
        f"cambiate {len(changed)}, livelli {sorted({e[2] for e in log})}"
    )
    if tables_on:
        crossing = sum(int(entry[3]) for entry in log if entry[3] is not None)
        print(f"tabelle non costruite perche' attraversano una scheda: {crossing}")

    unexpected = sorted(set(changed) - set(with_regions))
    print(f"R3 cambiate senza schede: {unexpected or 'nessuna'}")
    unchanged = sorted(set(named) - set(changed))
    if not tables_on:
        print(f"   con un nome e non cambiate: {unchanged or 'nessuna'}")
    print(f"   con una scheda senza nome e cambiate: {sorted(set(changed) - set(named)) or 'nessuna'}")

    losses = [m for m in changed if before_ir.get(m) != after_ir.get(m)]
    print(f"R4 conservazione sull'IR: {'REGGE' if not losses else 'CADE su ' + str(losses)}")
    for marker in losses:
        lost = before_ir[marker] - after_ir[marker]
        gained = after_ir[marker] - before_ir[marker]
        print(f"   pagina {marker}: persi {lost.most_common(6)}, in piu' {gained.most_common(6)}")
    md_losses = [m for m in changed if markdown_characters(before[m]) != markdown_characters(after[m])]
    print(f"   sul Markdown (informativo): {'uguale' if not md_losses else 'diverso su ' + str(md_losses)}")

    headings: list[tuple[int, str]] = []
    for marker in changed:
        old = {line for line in before[marker].splitlines() if line.startswith("#")}
        headings.extend(
            (marker, line)
            for line in after[marker].splitlines()
            if line.startswith("#") and line not in old
        )
    levels = Counter(line.split(" ", 1)[0] for _marker, line in headings)
    print(f"R2 titoli nuovi: {len(headings)}, per livello {dict(levels)}")
    for marker, line in headings:
        print(f"   {marker:4d}  {line}")
    failed = bool(unexpected or losses or (unchanged and not tables_on))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
