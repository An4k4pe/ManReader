"""Il materiale per guardare le note d'asset: dieci pagine, otto manuali.

Rigenera **tutto** cio' che serve a giudicare la politica d'asset, in una cartella
che sopravvive alla sessione:

    <out>/manuali/<Man>/images/        un file per contenuto su una pagina sola
    <out>/manuali/<Man>/assets/        un file per contenuto ripetuto
    <out>/manuali/<Man>/asset_index.csv
    <out>/pagine/<Man><idx>/           l'IR 2 e il corpo reso di una pagina
    <out>/pagine/<Man><idx>.png        la pagina come la si vede, che e' il riferimento
    <out>/USCITA_dieci_pagine.md       tutto insieme, da leggere

Il campione lo legge da `Campione_UscitaIR2Minima_v1.md`, non da qui: le dieci
pagine sono sorteggiate con seed dichiarato e non si scelgono a mano.

Uso::

    ./venv/bin/python scripts/build_asset_note_material.py --pdf-dir . --out output/asset-note
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_readability_material import sample  # noqa: E402

from ir2_markdown import render_page_markdown  # noqa: E402
from ir2_serialization import document_ir2_from_dict  # noqa: E402

ETICHETTA = {
    "content": "immagine → `images/`, **nota nel corpo**",
    "recurring": "ripetuta → `assets/`, niente nota",
    "below_text_scale": "più sottile del testo → nessun file, resta nell'indice",
    "no_stored_resource": "nessuna risorsa memorizzata → nessun file, resta nell'indice",
}


def build_manual_assets(pdf: Path, out: Path) -> list[dict[str, str]]:
    """La passata di documento. Serve tutto il manuale: la ricorrenza e' su di esso."""

    index = out / "asset_index.csv"
    if not index.is_file():
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_document_assets.py"),
             "--pdf", str(pdf.resolve()), "--out", str(out)],
            capture_output=True, text=True, cwd=PROJECT_ROOT, check=False,
        )
    if not index.is_file():
        return []
    return list(csv.DictReader(index.open(encoding="utf-8")))


def build_page(pdf: Path, page_number: int, out: Path) -> None:
    """La fetta IR 2 di una pagina, con arredo ed elenchi accesi."""

    if (out / "document_ir2.json").is_file():
        return
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
         "--pdf", str(pdf.resolve()), "--page-number", str(page_number),
         "--output-dir", str(out),
         "--arredo", "--elenchi", "--arredo-pagine", "20"],
        capture_output=True, text=True, cwd=PROJECT_ROOT, check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--campione", type=Path,
        default=PROJECT_ROOT / "Campione_UscitaIR2Minima_v1.md",
    )
    arguments = parser.parse_args()

    pages = sample(arguments.campione)
    arguments.out.mkdir(parents=True, exist_ok=True)

    manuals = sorted({manual for manual, _ in pages})
    indexes: dict[str, list[dict[str, str]]] = {}
    for manual in manuals:
        pdf = arguments.pdf_dir / f"{manual}.pdf"
        if not pdf.is_file():
            continue
        print(f"  asset di {manual}...", flush=True)
        indexes[manual] = build_manual_assets(
            pdf, arguments.out / "manuali" / manual
        )

    lines = [
        "# Le note d'asset, sulle dieci pagine del campione",
        "",
        "Campione sorteggiato con seed dichiarato in `Campione_UscitaIR2Minima_v1.md`.",
        "Per ogni pagina: l'immagine della pagina, che è il riferimento; che asset il",
        "documento ci mette e **dove è finito ciascuno**; il corpo reso.",
        "",
        "Le quattro destinazioni le decide `document_asset_policy`, in quest'ordine:",
        "",
        "| destinazione | file | nota nel corpo |",
        "| --- | --- | --- |",
        "| nessuna risorsa memorizzata | no, ma **è nell'indice** | no |",
        "| più sottile del testo | no, ma **è nell'indice** | no |",
        "| ripetuta su più pagine | `assets/` | no |",
        "| su una pagina sola | `images/` | **sì** |",
        "",
        "---",
        "",
    ]
    totals: dict[str, int] = {}

    for position, (manual, page_number) in enumerate(pages, start=1):
        pdf = arguments.pdf_dir / f"{manual}.pdf"
        index = page_number - 1
        if not pdf.is_file() or manual not in indexes:
            continue
        print(f"  pagina {position}/10 — {manual} idx {index}...", flush=True)
        directory = arguments.out / "pagine" / f"{manual}{index}"
        build_page(pdf, page_number, directory)

        image = arguments.out / "pagine" / f"{manual}{index}.png"
        if not image.is_file():
            with fitz.open(pdf) as document:
                document[index].get_pixmap(dpi=110).save(image)

        serialized = directory / "document_ir2.json"
        if not serialized.is_file():
            continue
        page = document_ir2_from_dict(
            json.loads(serialized.read_text(encoding="utf-8"))
        ).pages[0]
        excluded_path = directory / "excluded_ir2.json"
        excluded = (
            frozenset(json.loads(excluded_path.read_text(encoding="utf-8")))
            if excluded_path.is_file()
            else frozenset()
        )
        rows = {row["digest"]: row for row in indexes[manual] if row["digest"]}
        notes = frozenset(d for d, r in rows.items() if r["nota_nel_corpo"] == "si")
        body = render_page_markdown(
            page, excluded_node_ids=excluded, asset_digests_with_note=notes
        )
        rendered = sum(1 for line in body.splitlines() if line.startswith("> **["))
        assets = [n for n in sorted(page.nodes, key=lambda n: n.order)
                  if n.kind == "asset.note" and n.asset is not None]

        label = page.page_label or "?"
        lines.append(
            f"## {position:02d} — {manual} idx {index}, pagina stampata «{label}»"
        )
        lines.append("")
        lines.append(f"![{manual} {index}](pagine/{image.name})")
        lines.append("")
        lines.append(f"**{len(assets)} asset sulla pagina · {rendered} note nel corpo**")
        lines.append("")
        if assets:
            lines.append("| pt | destinazione | file |")
            lines.append("| --- | --- | --- |")
            for node in assets:
                asset = node.asset
                assert asset is not None
                row = rows.get(asset.digest, {})
                destination = row.get("destinazione", "?")
                totals[destination] = totals.get(destination, 0) + 1
                width = asset.bbox[2] - asset.bbox[0]
                height = asset.bbox[3] - asset.bbox[1]
                name = row.get("nome_file") or "—"
                lines.append(
                    f"| {width:.0f}×{height:.0f} | "
                    f"{ETICHETTA.get(destination, destination)} | `{name}` |"
                )
            lines.append("")
        lines.append("### Il corpo reso")
        lines.append("")
        lines.append(body.rstrip() or "*(vuoto)*")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Riepilogo sulle dieci pagine")
    lines.append("")
    lines.append("| destinazione | asset |")
    lines.append("| --- | --- |")
    for key in ("content", "recurring", "below_text_scale", "no_stored_resource"):
        lines.append(f"| {ETICHETTA[key]} | {totals.get(key, 0)} |")
    lines.append("")
    lines.append("## I manuali per intero")
    lines.append("")
    lines.append("| manuale | contenuti distinti | `images/` | `assets/` | sotto la scala | senza risorsa |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for manual in manuals:
        rows_of = indexes.get(manual, [])
        if not rows_of:
            continue
        counted = {key: sum(1 for r in rows_of if r["destinazione"] == key)
                   for key in ETICHETTA}
        lines.append(
            f"| {manual} | {sum(counted.values())} | {counted['content']} | "
            f"{counted['recurring']} | {counted['below_text_scale']} | "
            f"{counted['no_stored_resource']} |"
        )

    target = arguments.out / "USCITA_dieci_pagine.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nscritto {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
