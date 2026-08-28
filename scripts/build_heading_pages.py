"""Le pagine intere dei campioni di `Criterio_Titoli_v2.md`, per giudicarli.

**Perche' la pagina intera e non un estratto.** Il primo materiale mostrava
cinque righe di contorno attorno a ogni riga campionata, e non basta: se una riga
sia un'intestazione lo si vede da **cosa le sta sotto** e da come e' composta la
pagina, non da due righe. Rilievo dell'utente.

**E niente troncamento.** La prima versione di questo script tagliava ogni riga a
160 caratteri, e su BiD idx 164 la resa e' fatta di 15 righe, una delle quali e'
un paragrafo da **1500 caratteri** che contiene `ridurre il sospetto` verso la
fine. Troncando, la riga da giudicare spariva e il resto sembrava una collezione
di estratti -- due dei tre rilievi dell'utente avevano quella sola causa.

**Ogni occorrenza, non la prima.** Il materiale precedente cercava la stringa
nella resa e mostrava la **prima** occorrenza nel documento, che spesso non era
la riga estratta: rilievo dell'etichettatore, verificato su tre righe. Qui si
stampano **tutte** le occorrenze col loro contorno.

Per ogni pagina che contiene almeno una riga campionata stampa la resa completa
del prototipo -- con arredo tolto, elenchi e titoli -- e l'elenco delle righe da
giudicare su quella pagina. **La classe che la regola ha assegnato non compare**:
il giudizio e' cieco.

Uso::

    ./venv/bin/python scripts/build_heading_pages.py --pdf-dir . --campione <dir> --out <file>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_ENTRY = re.compile(r"^## Riga (\d+) — render `(\w+)_pagina\d+_idx(\d+)\.png`$", re.M)


def render_page(pdf: Path, index: int, workspace: Path) -> str:
    out = workspace / f"{pdf.stem}_{index}"
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
            "--pdf", str(pdf),
            "--page-number", str(index + 1),
            "--output-dir", str(out),
            "--arredo", "--elenchi", "--arredo-pagine", "20",
        ],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    rendered = out / "page_ir2.md"
    return rendered.read_text(encoding="utf-8") if rendered.is_file() else "(resa non prodotta)"


def _bare(text: str) -> str:
    """Solo lettere e cifre, minuscole: cio' che sopravvive alla resa.

    La resa inserisce il grassetto e toglie i marcatori d'elenco, quindi un
    confronto letterale fra sorgente e uscita fallisce.
    """

    return "".join(character for character in text if character.isalnum()).lower()


def occurrences(rendered: str, needle: str, window: int = 110) -> list[str]:
    """Tutte le occorrenze della riga nella resa, col loro contorno.

    Il confronto normalizza i due lati -- la resa inserisce il grassetto e toglie
    i marcatori -- e restituisce **ogni** occorrenza: mostrare solo la prima era
    il difetto che ha fatto giudicare tre righe sul contorno sbagliato.
    """

    target = _bare(needle)
    if not target:
        return []
    plain = rendered
    bare_map: list[int] = []
    bare_text: list[str] = []
    for position, character in enumerate(plain):
        if character.isalnum():
            bare_text.append(character.lower())
            bare_map.append(position)
    joined = "".join(bare_text)

    found: list[str] = []
    start = 0
    while True:
        at = joined.find(target, start)
        if at < 0:
            break
        left = bare_map[max(0, at - window)]
        right = bare_map[min(len(bare_map) - 1, at + len(target) + window)]
        found.append(plain[left : right + 1].replace("\n", " "))
        start = at + 1
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--campione", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source = (args.campione / "Righe_da_etichettare.md").read_text(encoding="utf-8")
    blocks = source.split("## Riga ")
    testi: dict[str, str] = {}
    for block in blocks[1:]:
        number = block.split(" ", 1)[0]
        fenced = re.search(r"```\n(.*?)\n```", block, re.S)
        testi[number] = fenced.group(1).strip() if fenced else "?"

    per_page: dict[tuple[str, int], list[str]] = defaultdict(list)
    for number, manual, index in _ENTRY.findall(source):
        per_page[(manual, int(index))].append(number)

    lines = [
        "# Titoli da giudicare — pagine intere",
        "",
        "Per ogni **riga** numerata: **titolo**, **non titolo**, oppure **incerto**.",
        "",
        "Sotto ogni pagina c'e' la resa completa che lo script produce **oggi**:",
        "arredo tolto, elenchi riconosciuti, titoli promossi con i loro `#`.",
        "",
        "Il render della pagina sorgente sta nella cartella del campione, col nome",
        "indicato. La classe che la regola ha assegnato non e' scritta da nessuna parte.",
        "",
        f"Pagine: **{len(per_page)}**. Righe da giudicare: **{sum(len(v) for v in per_page.values())}**.",
        "",
        "---",
        "",
    ]

    with tempfile.TemporaryDirectory() as workspace:
        root = Path(workspace)
        for (manual, index) in sorted(per_page):
            numbers = sorted(per_page[(manual, index)], key=int)
            stem = f"{manual}_pagina{index + 1:04d}_idx{index:04d}"
            lines.append(f"## {manual}, pagina idx {index} — render `{stem}.png`")
            lines.append("")
            lines.append("**Righe da giudicare su questa pagina:**")
            lines.append("")
            for number in numbers:
                lines.append(f"- Riga **{number}**: `{testi[number][:96]}`")
                lines.append("  - Giudizio: ")
            lines.append("")
            rendered = render_page(args.pdf_dir / f"{manual}.pdf", index, root)

            lines.append("**Dove stanno, nella resa:**")
            lines.append("")
            for number in numbers:
                needle = testi[number]
                found = occurrences(rendered, needle)
                lines.append(f"- Riga **{number}** — {len(found)} occorrenze nella resa:")
                for excerpt in found:
                    lines.append("")
                    lines.append("  ```markdown")
                    lines.append(f"  …{excerpt}…")
                    lines.append("  ```")
                if not found:
                    lines.append("  - **non compare nella resa** (tolta come arredo, o persa)")
            lines.append("")
            lines.append("**La pagina intera come esce oggi**, senza tagli:")
            lines.append("")
            lines.append("```markdown")
            lines.extend(rendered.splitlines())
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(per_page)} pagine scritte in {args.out}")


if __name__ == "__main__":
    main()
