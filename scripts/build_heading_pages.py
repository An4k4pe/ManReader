"""Le pagine intere dei campioni di `Criterio_Titoli_v2.md`, per giudicarli.

**Perche' la pagina intera e non un estratto.** Il primo materiale mostrava
cinque righe di contorno attorno a ogni riga campionata, e non basta: se una riga
sia un'intestazione lo si vede da **cosa le sta sotto** e da come e' composta la
pagina, non da due righe. Rilievo dell'utente.

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
            lines.append("**La pagina come esce oggi:**")
            lines.append("")
            lines.append("```markdown")
            rendered = render_page(args.pdf_dir / f"{manual}.pdf", index, root)
            lines.extend(entry[:160] for entry in rendered.splitlines())
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(per_page)} pagine scritte in {args.out}")


if __name__ == "__main__":
    main()
