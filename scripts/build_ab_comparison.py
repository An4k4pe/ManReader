"""Costruisce il confronto A/B cieco di `Criterio_RotturaParagrafo_v2.md` §3.

Per ogni pagina prende le due uscite -- prima e dopo il cambio -- e le scrive
come **A** e **B**, con l'assegnazione estratta a sorte **per pagina** dal seed
dichiarato nel criterio. Chi giudica non sa quale sia la nuova.

La corrispondenza A/B → vecchio/nuovo finisce in un file **separato**, che non va
aperto finche' tutte le risposte non sono date. Sta in un file e non a schermo di
proposito: un elenco stampato accanto alle pagine sarebbe cecita' solo di nome.

Le pagine identiche fra le due versioni si segnalano e **non entrano nel
confronto**: chiedere quale si legga meglio fra due file uguali non e' una
domanda, e lasciarle dentro gonfierebbe i pareggi.

Uso::

    ./venv/bin/python scripts/build_ab_comparison.py \\
        --prima dir_vecchia --dopo dir_nuova --out dir_confronto \\
        --seed 20260825 --pagine DrW_idx0227 DIE_idx0379 ...
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

MARKDOWN = "page_ir2.md"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prima", type=Path, required=True)
    parser.add_argument("--dopo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--pagine", nargs="+", required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    key_lines = [
        f"# Chiave A/B — seed {args.seed}",
        "",
        "**Non aprire finche' tutte le risposte non sono date.**",
        "",
        "| # | pagina | A | B |",
        "| --- | --- | --- | --- |",
    ]
    identical: list[str] = []
    position = 0

    for name in args.pagine:
        before = (args.prima / name / MARKDOWN).read_text(encoding="utf-8")
        after = (args.dopo / name / MARKDOWN).read_text(encoding="utf-8")
        if before == after:
            identical.append(name)
            continue
        position += 1
        new_is_a = rng.random() < 0.5
        a_text, b_text = (after, before) if new_is_a else (before, after)
        stem = f"{position:02d}_{name}"
        (args.out / f"{stem}_A.md").write_text(a_text, encoding="utf-8")
        (args.out / f"{stem}_B.md").write_text(b_text, encoding="utf-8")
        key_lines.append(
            f"| {position:02d} | {name} | "
            f"{'NUOVO' if new_is_a else 'vecchio'} | {'vecchio' if new_is_a else 'NUOVO'} |"
        )

    key_lines += ["", f"Pagine identiche fra le due versioni, escluse: {len(identical)}"]
    key_lines += [f"- {name}" for name in identical]
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text(
        "\n".join(key_lines) + "\n", encoding="utf-8"
    )

    print(f"coppie da giudicare: {position}")
    print(f"pagine identiche, escluse: {len(identical)}")
    for name in identical:
        print(f"    {name}")
    print(f"chiave in CHIAVE_{args.out.name}.md — non aprirla prima")


if __name__ == "__main__":
    main()
