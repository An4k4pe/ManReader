"""Aggrega i CSV prodotti da ``scan_intra_page_band_structure.py`` e stampa un
digest compatto -- poche decine di righe, non un dump.

Domanda a cui risponde, e sola ragione per cui esiste: le pagine con una
struttura di colonna UNIFORME sono la norma o l'eccezione? Il meccanismo di
Fase 2 (``prototype_column_gap_group_persistence.py``) assume implicitamente
una struttura per pagina -- ``--y-window`` e' manuale e di default copre tutta
l'altezza -- quindi ogni pagina a struttura mista gli diluisce il supporto e
produce un falso ``column_count=1`` senza fallire rumorosamente (v. State.md,
"Struttura di colonna variabile dentro la stessa pagina").

Tre categorie per pagina, mutuamente esclusive:

  omogenea-1col   una sola banda, column_count = 1
  omogenea-Ncol   una o piu' bande, tutte con lo STESSO column_count >= 2
  mista           bande con column_count DIVERSI sulla stessa pagina

La terza e' quella che conta: e' il caso che il meccanismo non sa gestire.

**Limite ereditato**, ripetuto qui perche' chi legge il digest potrebbe non
aver letto il driver: le bande vengono dal percorso di Milestone 32, la cui
sovra-fusione di righe (13,6%-45,7%) tende a nascondere confini fra bande, non
a inventarne. I tassi di "mista" sono quindi limiti INFERIORI.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/summarize_intra_page_band_structure.py --input-dir output/intra_page_bands
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--min-rows-per-band",
        type=int,
        default=1,
        help="Ignora le bande con row_count sotto questa soglia prima di classificare la "
        "pagina. Serve per controllare se le pagine 'miste' dipendano da bande di una "
        "riga sola (pattern 'flicker'). Default: 1, cioe' nessun filtro.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    csv_paths = sorted(args.input_dir.glob("*_all_bands.csv"))
    if not csv_paths:
        print(f"Nessun CSV in {args.input_dir}")
        return 1

    print(f"Filtro bande: row_count >= {args.min_rows_per_band}\n")
    header = f"{'manuale':<16}{'pagine':>8}{'omog-1col':>11}{'omog-Ncol':>11}{'MISTA':>9}{'%mista':>9}"
    print(header)
    print("-" * len(header))

    total_pages = 0
    total_mixed = 0
    total_homog_n = 0
    distinct_counts_hist: dict[int, int] = defaultdict(int)

    for path in csv_paths:
        per_page: dict[str, list[tuple[int, int]]] = defaultdict(list)
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    column_count = int(row["column_count"])
                    row_count = int(row["row_count"])
                except (KeyError, TypeError, ValueError):
                    continue
                if row_count < args.min_rows_per_band:
                    continue
                per_page[row["page"]].append((column_count, row_count))

        homogeneous_single = 0
        homogeneous_multi = 0
        mixed = 0
        for bands in per_page.values():
            distinct = {column_count for column_count, _ in bands}
            if len(distinct) > 1:
                mixed += 1
            elif distinct == {1}:
                homogeneous_single += 1
            else:
                homogeneous_multi += 1
            distinct_counts_hist[len(distinct)] += 1

        pages = len(per_page)
        if pages == 0:
            continue
        share = 100.0 * mixed / pages
        name = path.stem.replace("_all_bands", "")
        print(
            f"{name:<16}{pages:>8}{homogeneous_single:>11}{homogeneous_multi:>11}"
            f"{mixed:>9}{share:>8.1f}%"
        )

        total_pages += pages
        total_mixed += mixed
        total_homog_n += homogeneous_multi

    print("-" * len(header))
    if total_pages:
        print(
            f"{'TOTALE':<16}{total_pages:>8}{'':>11}{total_homog_n:>11}"
            f"{total_mixed:>9}{100.0 * total_mixed / total_pages:>8.1f}%"
        )
        print(
            "\nPagine con almeno una banda a >=2 colonne (omog-Ncol + mista): "
            f"{total_homog_n + total_mixed} su {total_pages} "
            f"({100.0 * (total_homog_n + total_mixed) / total_pages:.1f}%)"
        )
    print("\nDistinti column_count per pagina (istogramma):")
    for distinct_values in sorted(distinct_counts_hist):
        print(f"  {distinct_values} valore/i distinti: {distinct_counts_hist[distinct_values]} pagine")
    print(
        "\nLimite: bande dal percorso Milestone 32, sovra-fusione righe 13,6%-45,7%.\n"
        "I tassi di 'mista' sono limiti INFERIORI, non stime centrate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
