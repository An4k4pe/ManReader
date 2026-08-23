"""L'errore squalificante di `Criterio_RotturaParagrafo_v2.md` §5.

Confronta due uscite IR 2 della stessa pagina -- prima e dopo un cambio della
regola di rottura -- e verifica che il testo emesso **si conservi**. Una regola
che riaggrega le righe non deve poter perdere ne' inventare caratteri, e il
percorso IR 2 non ha un invariante che lo garantisca: ``ir2_validate.py:84``
verifica la copertura per **id di primitiva**, non per caratteri.

Il confronto e' sul **multiinsieme dei caratteri** di tutti i nodi
``text.paragraph``, **ignorando spazi e trattini**.

I trattini sono esclusi perche' ``ir2_builder.join_lines`` ne toglie uno a ogni
giunzione di sillabazione: unire due righe che prima erano separate **deve** far
sparire dei trattini, ed e' il comportamento voluto. Per questo il conteggio dei
trattini si riporta a parte -- un calo e' atteso e proporzionale alle giunzioni
nuove, un aumento sarebbe impossibile e andrebbe guardato.

**Limite dichiarato**: ignorare i trattini rende invisibile la perdita di un
trattino legittimo, per esempio in una parola composta. E' il prezzo di non avere
l'invariante di conservazione dei caratteri, che resta aperto.

Uso::

    ./venv/bin/python scripts/check_paragraph_conservation.py \\
        --prima dir_vecchia --dopo dir_nuova
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PARAGRAPH_KIND = "text.paragraph"
IGNORED = {" ", "\t", "\n", "\r", "-", "­"}


def paragraph_text(document_path: Path) -> str:
    document = json.loads(document_path.read_text(encoding="utf-8"))
    return "".join(
        node["text"] or ""
        for page in document["pages"]
        for node in page["nodes"]
        if node["kind"] == PARAGRAPH_KIND
    )


def multiset(text: str) -> Counter[str]:
    return Counter(character for character in text if character not in IGNORED)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prima", type=Path, required=True)
    parser.add_argument("--dopo", type=Path, required=True)
    args = parser.parse_args()

    before_dirs = sorted(p for p in args.prima.iterdir() if p.is_dir())
    failures = 0
    checked = 0
    hyphens_before = 0
    hyphens_after = 0

    for before_dir in before_dirs:
        after_dir = args.dopo / before_dir.name
        before_json = before_dir / "document_ir2.json"
        after_json = after_dir / "document_ir2.json"
        if not before_json.is_file() or not after_json.is_file():
            print(f"MANCANTE: {before_dir.name}", file=sys.stderr)
            continue
        checked += 1
        before_text = paragraph_text(before_json)
        after_text = paragraph_text(after_json)
        hyphens_before += before_text.count("-")
        hyphens_after += after_text.count("-")
        difference = multiset(before_text) - multiset(after_text)
        surplus = multiset(after_text) - multiset(before_text)
        if difference or surplus:
            failures += 1
            print(f"NON CONSERVA  {before_dir.name}")
            if difference:
                print(f"    persi:   {dict(difference.most_common(8))}")
            if surplus:
                print(f"    inventati: {dict(surplus.most_common(8))}")

    print()
    print(f"pagine confrontate: {checked}")
    print(f"trattini: prima {hyphens_before}, dopo {hyphens_after}, calo {hyphens_before - hyphens_after}")
    if failures:
        print(f"\nERRORE SQUALIFICANTE: {failures} pagine non conservano il testo")
        raise SystemExit(1)
    print("\nconservazione: OK su tutte le pagine confrontate")


if __name__ == "__main__":
    main()
