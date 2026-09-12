"""Confronto prima/dopo della nota dello sfondo della scheda (passo 3b).

`Criterio_NotaSfondoScheda_v1.md`, S1 e S3. Base: l'uscita di 3a; dopo:
l'uscita con la nota. Legge i due `document.md`, i due `document_ir2.json` e il
log del giro «dopo», eseguito con `--processi 1`.

  S1  le righe che cambiano sono solo righe di nota (`> **[`), solo su pagine
      con una scheda con nome, e il testo dell'IR -- nodi e celle -- e' identico
      su tutte le pagine;
  S3  le note cambiate, da leggere: pagina, riga prima e riga dopo.

Riusa la lettura delle pagine e del log di `compare_stat_block_innesto.py`:
una implementazione sola.

Uso:  python scripts/compare_stat_block_notes.py <prima/document.md>
          <dopo/document.md> <dopo.log>
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

from compare_stat_block_innesto import _SCHEDE, ir_pages, markdown_pages

_NOTE = "> **["


def main(argv: list[str]) -> int:
    before_md, after_md = Path(argv[1]), Path(argv[2])
    before, after = markdown_pages(before_md), markdown_pages(after_md)
    before_ir = ir_pages(before_md.with_name("document_ir2.json"))
    after_ir = ir_pages(after_md.with_name("document_ir2.json"))
    markers = sorted(after)
    if sorted(before) != markers:
        print(f"FAIL: pagine diverse prima {len(before)} e dopo {len(after)}")
        return 1
    log = [m.groups() for m in _SCHEDE.finditer(Path(argv[3]).read_text(encoding="utf-8"))]
    if len(log) != len(markers):
        print(f"FAIL: {len(log)} righe `schede:` nel log per {len(markers)} pagine")
        return 1
    named = {marker for marker, entry in zip(markers, log, strict=True) if int(entry[1]) > 0}

    changed: list[int] = []
    other_lines: list[tuple[int, str]] = []
    notes: list[tuple[int, str, str]] = []
    for marker in markers:
        if before[marker] == after[marker]:
            continue
        changed.append(marker)
        old_lines, new_lines = before[marker].splitlines(), after[marker].splitlines()
        matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            removed, added = old_lines[i1:i2], new_lines[j1:j2]
            other_lines.extend(
                (marker, line)
                for line in removed + added
                if line.strip() and not line.startswith(_NOTE)
            )
            notes.extend(
                (marker, old, new) for old, new in zip(removed, added, strict=False)
            )

    text_changed = [m for m in markers if before_ir.get(m) != after_ir.get(m)]
    outside = sorted(set(changed) - named)
    print(f"pagine {len(markers)}, cambiate {len(changed)}: {changed}")
    print(f"S1 righe cambiate che non sono note: {len(other_lines) or 'nessuna'}")
    for marker, line in other_lines[:12]:
        print(f"   {marker:4d}  {line[:110]}")
    print(f"   pagine cambiate senza una scheda con nome: {outside or 'nessuna'}")
    print(f"   testo dell'IR diverso su: {text_changed or 'nessuna pagina'}")
    print(f"S3 note cambiate: {len(notes)}")
    for marker, old, new in notes:
        print(f"   {marker:4d}  {old[:90]}")
        print(f"         {new[:90]}")
    return 1 if other_lines or outside or text_changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
