"""Analizza i profili di gutter prodotti da
``prototype_derived_column_bands.py --emit gutters`` sull'intero corpus e
stampa un digest compatto.

## La domanda

Il prototipo trova separazioni verticali reali, ma non tutte sono colonne di
prosa. Su tre pagine ispezionate visivamente (v. `State.md` e la docstring del
prototipo) si vedono tre tipi distinti, con firme diverse:

  Dag p.140  due colonne vere   righe 46/45   larghezze 221,4/221,4   blocchi condivisi 0
  Lan p.84   tabella            righe 21/46   larghezze   9,6/499,4   blocchi condivisi 21
  Wil p.308  callout            righe  4/28   larghezze  15,6/430,8   blocchi condivisi 0

Tre pagine non sono una tassonomia. Questo script guarda se quelle firme
esistono su tutto il corpus o se erano un'impressione.

## Perche' NON classifica

Sarebbe facile scrivere "simmetria > 0,5 allora prosa" e stampare tre numeri.
Sarebbe anche il difetto che questa diagnostica ha gia' commesso: una soglia
scelta a occhio che decide il risultato e poi viene citata come se fosse una
misura. Qui si stampano le distribuzioni. Se la simmetria e' bimodale con una
valle netta, il taglio lo suggeriscono i dati e si potra' derivare; se e' un
continuo, non esistono "tre classi" e la tassonomia va abbandonata, non
tarata.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/summarize_gutter_profiles.py --input-dir output/gutter_profile
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def _histogram(title: str, counts: dict[int, int], *, labels: dict[int, str] | None = None) -> None:
    print(f"\n{title}")
    if not counts:
        print("  (vuoto)")
        return
    peak = max(counts.values())
    for key in sorted(counts):
        label = labels.get(key, str(key)) if labels else str(key)
        bar = "#" * int(50 * counts[key] / peak)
        print(f"  {label:>12}  {counts[key]:>6}  {bar}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--min-flanking",
        type=int,
        default=2,
        help="Considera solo i gutter con almeno queste righe per lato. Default: 2.",
    )
    parser.add_argument(
        "--min-y-extent",
        type=float,
        default=0.0,
        help="Considera solo i gutter almeno cosi' alti. Default: 0.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    paths = sorted(args.input_dir.glob("*.csv"))
    if not paths:
        print(f"Nessun CSV in {args.input_dir}")
        return 1

    total = 0
    kept = 0
    flanking_hist: dict[int, int] = defaultdict(int)
    symmetry_hist: dict[int, int] = defaultdict(int)
    shared_hist: dict[int, int] = defaultdict(int)
    joint: dict[tuple[int, int], int] = defaultdict(int)
    pages_with_kept: set[tuple[str, str]] = set()

    for path in paths:
        manual = path.stem
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                total += 1
                try:
                    flanking_min = int(row["flanking_min"])
                    left_width = float(row["left_width_median"])
                    right_width = float(row["right_width_median"])
                    shared = int(row["shared_blocks"])
                    extent = float(row["y_extent"])
                except (KeyError, TypeError, ValueError):
                    continue

                flanking_hist[min(flanking_min, 10)] += 1
                if flanking_min < args.min_flanking or extent < args.min_y_extent:
                    continue
                kept += 1
                pages_with_kept.add((manual, row["page"]))

                widest = max(left_width, right_width)
                symmetry = (min(left_width, right_width) / widest) if widest > 0 else 0.0
                bucket = min(int(symmetry * 10), 9)
                symmetry_hist[bucket] += 1
                shared_hist[min(shared, 5)] += 1
                joint[(bucket, 1 if shared > 0 else 0)] += 1

    print(f"Gutter totali: {total}")
    print(f"Gutter con >= {args.min_flanking} righe per lato e altezza >= {args.min_y_extent}pt: {kept}")
    print(f"Pagine che ne contengono almeno uno: {len(pages_with_kept)}")

    _histogram(
        "flanking_min (righe sul lato piu' povero), su TUTTI i gutter",
        flanking_hist,
        labels={10: ">=10"},
    )
    _histogram(
        "simmetria delle larghezze (stretta/larga), sui gutter tenuti",
        symmetry_hist,
        labels={b: f"{b / 10:.1f}-{(b + 1) / 10:.1f}" for b in range(10)},
    )
    _histogram(
        "blocchi PyMuPDF condivisi fra i due lati, sui gutter tenuti",
        shared_hist,
        labels={5: ">=5"},
    )

    print("\nCongiunta simmetria x blocchi condivisi (righe = simmetria):")
    print(f"  {'simmetria':>12}  {'0 blocchi':>10}  {'>0 blocchi':>11}")
    for bucket in range(10):
        without = joint.get((bucket, 0), 0)
        with_shared = joint.get((bucket, 1), 0)
        if without or with_shared:
            print(f"  {bucket / 10:>7.1f}-{(bucket + 1) / 10:<4.1f}  {without:>10}  {with_shared:>11}")

    print(
        "\nLettura: se la simmetria e' bimodale con una valle netta, il confine fra prosa e\n"
        "non-prosa e' nei dati e si puo' derivare. Se e' un continuo, le 'tre classi' viste\n"
        "su tre pagine non esistono nel corpus e la tassonomia va abbandonata, non tarata."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
