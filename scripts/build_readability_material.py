"""Il materiale per `Criterio_DieciPagineOggi_v1.md`: uscita corrente contro pagina.

Per ognuna delle dieci pagine del campione dichiarato produce, nell'ordine in cui
le domande contano:

- **l'immagine della pagina**, che e' il riferimento -- non la base, che e'
  l'uscita vecchia;
- **il corpo reso**, per intero e senza troncamenti, con tutti i meccanismi
  accesi;
- **il canale review**, cioe' cio' che e' uscito dal corpo e dove sta -- senza,
  uno spostamento si scambia per una perdita, ed e' il difetto che ha gia'
  inquinato un giudizio.

Il numero **stampato** compare accanto all'indice posizionale: su tredici manuali
su sedici il documento lo dichiara, e chi legge non deve tradurlo a mano.

Uso::

    ./venv/bin/python scripts/build_readability_material.py --pdf-dir . --out <dir>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ir2_serialization import document_ir2_from_dict  # noqa: E402

_SAMPLE_ROW = re.compile(r"^\|\s*\d+\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", re.M)


def sample(campione: Path) -> list[tuple[str, int]]:
    """(manuale, `--page-number`) dal documento del campione, non da qui."""

    return [
        (manual, int(page_number))
        for manual, _index, page_number in _SAMPLE_ROW.findall(
            campione.read_text(encoding="utf-8")
        )
    ]


def render_page_image(pdf: Path, index: int, target: Path) -> None:
    """La pagina come la si vede, a 150 dpi."""

    with fitz.open(pdf) as document:
        pixmap = document[index].get_pixmap(dpi=150)
        pixmap.save(target)


def run_pipeline(pdf: Path, page_number: int, out: Path) -> tuple[str, str, list[str]]:
    """Corpo, numero stampato e testo uscito dal corpo. **Tutto da IR 2.**

    Rilievo dell'utente: costruire il materiale per un'altra via non ha senso.
    Una prima stesura ricavava il numero di pagina ricatturando le pagine e
    richiamando il ramo dei numeri dedotti -- quando `PageIR2.page_label` ce
    l'ha gia', serializzato -- e leggeva cio' che esce dal corpo con
    un'espressione regolare sulla prosa di `review_ir2.md`.

    Ora il corpo viene da `page_ir2.md`, cioe' dall'emettitore vero, e le altre
    due cose dall'IR serializzato piu' la lista degli id esclusi che il prototipo
    dichiara. Nessuna seconda derivazione.
    """

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
            "--pdf", str(pdf.resolve()),
            "--page-number", str(page_number),
            "--output-dir", str(out),
            "--arredo", "--elenchi", "--arredo-pagine", "20",
        ],
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    body = out / "page_ir2.md"
    serialized = out / "document_ir2.json"
    excluded = out / "excluded_ir2.json"
    if not serialized.is_file():
        return ("(corpo non prodotto)", "?", [])

    document = document_ir2_from_dict(json.loads(serialized.read_text(encoding="utf-8")))
    page = document.pages[0]
    label = page.page_label or "?"
    if page.page_label and page.page_label_deduced:
        label = f"{page.page_label} (dedotto)"

    taken = set(json.loads(excluded.read_text(encoding="utf-8"))) if excluded.is_file() else set()
    out_of_body = [
        " ".join((node.text or "").split())
        for node in sorted(page.nodes, key=lambda n: n.order)
        if node.node_id in taken and node.text
    ]
    return (
        body.read_text(encoding="utf-8") if body.is_file() else "(corpo non prodotto)",
        label,
        out_of_body,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--campione", type=Path, default=PROJECT_ROOT / "Campione_UscitaIR2Minima_v1.md"
    )
    arguments = parser.parse_args()

    arguments.out.mkdir(parents=True, exist_ok=True)
    pages = sample(arguments.campione)

    lines = [
        "# Giudizio — le dieci pagine, su quello che escono oggi",
        "",
        "`Criterio_DieciPagineOggi_v1.md`. Dieci pagine, sorteggiate a suo tempo con",
        "seed dichiarato da un pool non condizionato: nessuna scelta da chi scrive.",
        "",
        "Per ogni pagina trovi **l'immagine**, che è il riferimento, **il corpo reso**",
        "per intero, e **ciò che è uscito dal corpo**.",
        "",
        "Quattro domande, nell'ordine in cui contano:",
        "",
        "1. **Manca qualcosa** che sulla pagina c'è?",
        "2. **È stato tolto qualcosa che non doveva?** Guarda l'elenco di ciò che è uscito.",
        "3. **Si legge?** Che cosa rende la pagina confusa, brutta o faticosa.",
        "4. **C'è qualcosa marcato male?** Un titolo che è prosa, una voce che non è",
        "   una voce, un paragrafo spezzato o fuso.",
        "",
        "Le **tabelle restano fuori dal giudizio**: il producer non esiste, e giudicare",
        "un compito che non c'è sarebbe scorretto. Annotale e non contarle contro.",
        "",
        "---",
        "",
    ]

    for position, (manual, page_number) in enumerate(pages, start=1):
        pdf = arguments.pdf_dir / f"{manual}.pdf"
        index = page_number - 1
        if not pdf.is_file():
            continue
        image = arguments.out / f"{position:02d}_{manual}_{index}.png"
        render_page_image(pdf, index, image)
        body, label, taken = run_pipeline(
            pdf, page_number, arguments.out / f"run_{manual}_{index}"
        )

        lines.append(f"## Pagina {position:02d} — {manual}, pagina stampata «{label}» (idx {index})")
        lines.append("")
        lines.append(f"![{manual} {label}]({image.name})")
        lines.append("")
        lines.append("### Il corpo reso")
        lines.append("")
        lines.append("```markdown")
        lines.append(body.rstrip())
        lines.append("```")
        lines.append("")
        lines.append("### Che cosa è uscito dal corpo")
        lines.append("")
        if taken:
            for text in taken:
                lines.append(f"- `{text}`")
        else:
            lines.append("*(nessun testo è uscito dal corpo)*")
        lines.append("")
        lines.append("### Le tue risposte")
        lines.append("")
        lines.append(f"{position:02d}.1 manca qualcosa: ")
        lines.append(f"{position:02d}.2 tolto a torto: ")
        lines.append(f"{position:02d}.3 si legge: ")
        lines.append(f"{position:02d}.4 marcato male: ")
        lines.append("")
        print(f"{manual} idx {index} (stampata «{label}») pronta", file=sys.stderr)

    target = arguments.out / "GIUDIZIO_dieci_pagine.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{len(pages)} pagine → {target}")


if __name__ == "__main__":
    main()
