"""Le righe di sorgente di una pagina, nell'ordine di lettura, da etichettare a mano.

Serve a `Criterio_RotturaParagrafo_v1.md`: la regola che decide dove si rompe un
paragrafo va giudicata contro **dove i paragrafi finiscono davvero**, e quel dato
non esiste. Il proxy ovvio -- l'ultima riga di un blocco di sorgente -- e'
inaffidabile proprio sulle pagine che contano: Milestone 38 ha misurato che su
DB p.99 i blocchi tagliano le voci di traverso, e il confine cade perfino dentro
la parola ``dimez-``/``zati``.

La griglia porta **solo numero e testo**. Nessuna geometria, nessuno scarto dal
margine, nessun suggerimento: se chi etichetta vedesse i numeri, darebbe
l'etichetta guardando quelli invece che la pagina, e la verita' a terra
diventerebbe una seconda opinione sul meccanismo.

L'ordine e' quello che il costruttore IR 2 riceve davvero -- stesso percorso di
`scripts/prototype_ir2_page.py`, `column_band` piu' ``_tree_aware_order`` -- e non
quello dell'estrattore: etichettare un ordine diverso da quello che
``breaks_paragraph`` vede renderebbe le etichette inutilizzabili.

Uso::

    ./venv/bin/python scripts/dump_source_lines.py --pdf DB.pdf --page-number 99
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for entry in (str(PROJECT_ROOT), str(SCRIPTS_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from compare_reading_order_with_column_bands import _tree_aware_order  # noqa: E402
from prototype_vertical_slice_page import _tree_rows_from_contract  # noqa: E402

from ir2_builder import group_source_lines  # noqa: E402
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--page-number", type=int, required=True)
    args = parser.parse_args()

    page_index = args.page_number - 1
    page_id = f"page:{args.page_number:04d}"

    with fitz.open(args.pdf) as document:
        page = document[page_index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            print("page guard: rotation o mediabox != cropbox", file=sys.stderr)
            raise SystemExit(3)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=page_id,
            capture_id=f"lines:pymupdf:{page_id}",
        )
        primitive_page = normalize_backend_page_capture(capture)

    analysis, measures = build_column_band_page_analysis_with_measurements(
        primitive_page, generation_id=f"generation:lines:{args.page_number:04d}"
    )
    tree = _tree_rows_from_contract(analysis.candidates, measures)
    ordered, _inside = _tree_aware_order(list(primitive_page.text_primitives), tree)
    lines = group_source_lines([primitive for primitive, _group in ordered])

    stem = args.pdf.stem
    print(f"# Griglia — {stem} pagina {args.page_number} (idx {page_index})\n")
    print(
        "Segna con `X` le righe che **chiudono un paragrafo**: quelle dopo le quali,"
        "\n**sulla pagina**, comincia qualcosa di nuovo. Lascia vuoto se il periodo"
        "\ncontinua sulla riga successiva.\n"
    )
    print("L'ultima riga della griglia chiude sempre e non va segnata.\n")
    print("| # | testo della riga | chiude? |")
    print("| --- | --- | --- |")
    for position, line in enumerate(lines, start=1):
        cell = line.text.replace("|", "\\|").replace("\n", " ").strip()
        print(f"| {position} | {cell} | |")


if __name__ == "__main__":
    main()
