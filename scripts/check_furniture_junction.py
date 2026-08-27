"""La clausola della giunzione: che cosa resta ai bordi di cio' che l'arredo toglie.

`Criterio_NumeroDedotto_v1.md` §5.D, e prima di lui
`Criterio_ArredoRicorrente_v3.md` §5 -- dove **e' rimasta in bianco**, ed e' la
ragione per cui quel criterio non e' stato dichiarato scaricato.

**Perche' serve uno strumento nuovo.** `check_paragraph_conservation.py` confronta
due `document_ir2.json`, e la politica d'arredo non tocca `document_ir2.json`: i
nodi restano, cambia la resa. Il difetto della giunzione vive **nel Markdown**.

**Come lo guarda.** Rende ogni pagina due volte col prototipo vero -- senza e con
`--arredo` -- e confronta i due Markdown. I paragrafi spariti sono cio' che
l'arredo ha tolto; per ognuno stampa il paragrafo **immediatamente sopra e sotto
nella resa senza arredo**, che e' l'ordine di lettura reale.

Far girare il prototipo invece di ricostruire la pipeline costa due passaggi per
pagina, ed e' il prezzo per non giudicare la giunzione su un ordine di lettura
diverso da quello che il lettore vedra'.

**Che cosa puo' e non puo' dire.** I paragrafi sono costruiti prima del filtro,
quindi togliere un nodo non puo' **fondere** due paragrafi: quel difetto non e'
rappresentabile, come la conservazione non e' falsificabile. Il difetto vero e' il
rovescio -- l'arredo **separava** due frammenti che erano un paragrafo solo, e
tolto di mezzo restano due paragrafi adiacenti che si leggono spezzati.

Lo script **non giudica**: segnala le giunzioni sospette -- sopra non chiude,
sotto attacca in minuscolo -- e stampa le due estremita' perche' un umano guardi.
Il criterio chiede l'occhio, non una soglia.

Uso::

    ./venv/bin/python scripts/check_furniture_junction.py --pdf FW.pdf --pagine 160 170
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_CLOSES = re.compile(r"[.!?:;»\"')\]]\s*$")
_OPENS_LOWER = re.compile(r"^\s*[a-zàèéìòù]")
_PROVENANCE = re.compile(r"^> \*\*\[pagina ")


def blocks_of(markdown: str) -> list[str]:
    """I paragrafi resi, **senza** la riga di provenienza.

    Va tolta da entrambi i lati e non solo da uno: dove il numero e' dedotto la
    riga compare solo con `--arredo`, dove e' dichiarato compare sempre, e
    filtrarla da una parte sola la faceva risultare «tolta» su ogni pagina dei
    manuali che dichiarano. Difetto di questo script, trovato su Dag.
    """

    return [
        block.strip()
        for block in markdown.split("\n\n")
        if block.strip() and not _PROVENANCE.match(block.strip())
    ]


def suspicious(before: str | None, after: str | None) -> bool:
    """Il paragrafo sopra non chiude e quello sotto attacca minuscolo."""

    if not before or not after:
        return False
    return not _CLOSES.search(before) and bool(_OPENS_LOWER.match(after))


def render(
    pdf: Path,
    page_number: int,
    out: Path,
    *,
    arredo: bool,
    sample: int,
    elenchi: bool = False,
) -> str:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
        "--pdf", str(pdf),
        "--page-number", str(page_number),
        "--output-dir", str(out),
    ]
    if arredo:
        command += ["--arredo", "--arredo-pagine", str(sample)]
    if elenchi:
        command += ["--elenchi", "--arredo-pagine", str(sample)]
    subprocess.run(command, capture_output=True, check=False, cwd=PROJECT_ROOT)
    rendered = out / "page_ir2.md"
    return rendered.read_text(encoding="utf-8") if rendered.is_file() else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument(
        "--pagine",
        type=int,
        nargs=2,
        required=True,
        metavar=("DA", "A"),
        help="numeri POSIZIONALI, come li vuole il prototipo (idx + 1)",
    )
    parser.add_argument("--arredo-pagine", type=int, default=40)
    parser.add_argument(
        "--elenchi",
        action="store_true",
        help="giudica la giunzione degli ELENCHI invece che dell'arredo: la resa "
             "modificata usa --elenchi, e cio' che 'sparisce' e' una riga che e' "
             "diventata voce (Criterio_ScalaDiValori_v1.md §4.D)",
    )
    args = parser.parse_args()

    flagged = removed_total = pages_with_removals = 0
    with tempfile.TemporaryDirectory() as workspace:
        root = Path(workspace)
        for number in range(args.pagine[0], args.pagine[1] + 1):
            base = blocks_of(
                render(
                    args.pdf, number, root / f"{number}_senza",
                    arredo=False, sample=args.arredo_pagine,
                )
            )
            kept = blocks_of(
                render(
                    args.pdf, number, root / f"{number}_con",
                    arredo=not args.elenchi, sample=args.arredo_pagine,
                    elenchi=args.elenchi,
                )
            )
            if not base:
                continue
            kept_set = set(kept)
            removed_positions = [i for i, b in enumerate(base) if b not in kept_set]
            if not removed_positions:
                continue
            pages_with_removals += 1
            removed_total += len(removed_positions)

            for position in removed_positions:
                before = next(
                    (base[i] for i in range(position - 1, -1, -1)
                     if i not in removed_positions), None
                )
                after = next(
                    (base[i] for i in range(position + 1, len(base))
                     if i not in removed_positions), None
                )
                mark = "SOSPETTA" if suspicious(before, after) else "ok"
                if mark == "SOSPETTA":
                    flagged += 1
                print(f"--- pagina {number} [{mark}] tolto: {base[position][:70]!r}")
                print(f"    sopra finisce: ...{(before or '(niente)')[-80:]!r}")
                print(f"    sotto comincia: {(after or '(niente)')[:80]!r}\n")

    print(f"pagine con rimozioni: {pages_with_removals}, voci tolte: {removed_total}")
    print(f"giunzioni sospette da guardare a occhio: {flagged}")


if __name__ == "__main__":
    main()
