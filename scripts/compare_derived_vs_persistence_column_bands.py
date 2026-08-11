"""Confronto testa a testa dei due meccanismi di rilevazione colonne su
esattamente le stesse pagine, per rispondere a una domanda che due casi
singoli non possono decidere: il meccanismo a confini ricavati e' meglio,
peggio, o semplicemente diverso?

I due meccanismi:

  persistence  `prototype_column_gap_group_persistence.py` (Fase 2). Griglia y
               fine, gap valido se largo >= --min-gap-width (default 15pt),
               colonna valida se persiste su >= --min-support-ratio (default
               0,6) dell'ALTEZZA PAGINA.
  derived      `prototype_derived_column_bands.py`. Nessuna delle due soglie:
               l'estensione y del gutter e' essa stessa il confine della banda.

Entrambi vanno eseguiti prima, sull'intero corpus, e i loro CSV passati qui:
questo script non li invoca, cosi' il confronto si puo' rifare su output gia'
raccolti senza ripagare la scansione.

## Perche' il confronto non e' simmetrico, e va letto sapendolo

Nessuno dei due meccanismi ha una ground truth. "Accordo" non significa
"corretto": i due potrebbero sbagliare insieme, e su prosa a due colonne
banale e' probabile che concordino a prescindere. L'informazione sta nei
**disaccordi**, che sono le sole pagine su cui vale la pena spendere un render.
Percio' l'output elenca i disaccordi, non solo li conta.

Asimmetria nota, dichiarata perche' altrimenti falsa la lettura: `derived` non
ha soglia, quindi emette una banda per ogni gutter che trova, anche di pochi
punti. Confrontarlo con `persistence` senza dire nulla lo farebbe sembrare
sistematicamente piu' "generoso". Per questo l'opzione `--min-band-extent`
esiste: NON come taratura del meccanismo -- il meccanismo non ne ha bisogno --
ma come parametro del confronto, da far variare per vedere se una conclusione
regge o dipende da dove lo si mette. Stessa disciplina usata per la misura di
copertura in `State.md`: e' l'insensibilita' al parametro che rende citabile un
risultato, non il valore.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/compare_derived_vs_persistence_column_bands.py \\
        --persistence-dir output/compare_mechanisms/persistence \\
        --derived-dir output/compare_mechanisms/derived
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def _read_persistence(directory: Path) -> dict[tuple[str, str], int]:
    """(manuale, pagina) -> massimo column_count trovato."""

    best: dict[tuple[str, str], int] = {}
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    column_count = int(row["column_count"])
                except (KeyError, TypeError, ValueError):
                    continue
                key = (path.stem, row["page"])
                best[key] = max(best.get(key, 0), column_count)
    return best


def _read_derived(directory: Path, *, min_band_extent: float) -> dict[tuple[str, str], tuple[int, float]]:
    """(manuale, pagina) -> (massimo column_count, estensione della banda che
    lo realizza). Le bande sotto ``min_band_extent`` sono ignorate."""

    best: dict[tuple[str, str], tuple[int, float]] = {}
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    column_count = int(row["column_count"])
                    extent = float(row["y_extent"])
                except (KeyError, TypeError, ValueError):
                    continue
                if extent < min_band_extent:
                    continue
                key = (path.stem, row["page"])
                current = best.get(key)
                if current is None or column_count > current[0]:
                    best[key] = (column_count, extent)
    return best


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persistence-dir", type=Path, required=True)
    parser.add_argument("--derived-dir", type=Path, required=True)
    parser.add_argument(
        "--min-band-extent",
        type=float,
        default=0.0,
        help="Ignora le bande di derived sotto questa estensione y. Parametro DEL "
        "CONFRONTO, non del meccanismo: farlo variare serve a vedere se una "
        "conclusione regge. Default: 0, cioe' nessun filtro.",
    )
    parser.add_argument(
        "--list-disagreements",
        type=int,
        default=0,
        help="Stampa fino a N pagine di disaccordo per categoria, da ispezionare a render.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)

    persistence = _read_persistence(args.persistence_dir)
    derived = _read_derived(args.derived_dir, min_band_extent=args.min_band_extent)
    pages = sorted(set(persistence) | set(derived))
    if not pages:
        print("Nessun dato: controlla le due cartelle.")
        return 1

    both = 0
    only_persistence: list[tuple[str, str]] = []
    only_derived: list[tuple[str, str]] = []
    neither = 0
    per_manual: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])

    for key in pages:
        p_multi = persistence.get(key, 0) >= 2
        d_multi = derived.get(key, (0, 0.0))[0] >= 2
        bucket = per_manual[key[0]]
        if p_multi and d_multi:
            both += 1
            bucket[0] += 1
        elif p_multi:
            only_persistence.append(key)
            bucket[1] += 1
        elif d_multi:
            only_derived.append(key)
            bucket[2] += 1
        else:
            neither += 1
            bucket[3] += 1

    total = len(pages)
    print(f"Filtro confronto: bande derived con y_extent >= {args.min_band_extent}pt")
    print(f"Pagine confrontate: {total}\n")
    header = f"{'manuale':<10}{'entrambi':>10}{'solo pers':>11}{'solo deriv':>12}{'nessuno':>10}"
    print(header)
    print("-" * len(header))
    for manual in sorted(per_manual):
        counts = per_manual[manual]
        print(f"{manual:<10}{counts[0]:>10}{counts[1]:>11}{counts[2]:>12}{counts[3]:>10}")
    print("-" * len(header))
    print(f"{'TOTALE':<10}{both:>10}{len(only_persistence):>11}{len(only_derived):>12}{neither:>10}")

    decided = both + len(only_persistence) + len(only_derived)
    if decided:
        agreement = 100.0 * both / decided
        print(
            f"\nAccordo sulle pagine dove almeno uno trova >=2 colonne: "
            f"{both}/{decided} ({agreement:.1f}%)"
        )
    print(
        "\nATTENZIONE: nessuno dei due meccanismi ha una ground truth. L'accordo non e'\n"
        "correttezza -- possono sbagliare insieme. Solo i disaccordi sono informativi,\n"
        "e vanno decisi a render, una pagina alla volta."
    )

    if args.list_disagreements:
        for label, items in (
            ("solo persistence (derived non trova nulla)", only_persistence),
            ("solo derived (persistence non trova nulla)", only_derived),
        ):
            print(f"\n{label}, primi {args.list_disagreements}:")
            for manual, page in items[: args.list_disagreements]:
                print(f"  {manual}.pdf --page {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
