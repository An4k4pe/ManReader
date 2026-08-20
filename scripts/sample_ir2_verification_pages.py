"""Estrae il campione di verifica per IR 2 minima.

Implementa la regola di `Criterio_UscitaIR2Minima_v1.md` §4, e nient'altro. Il
seed e le esclusioni stanno nel criterio, committato insieme a questo file e
prima dell'estrazione: se fossero scelti dopo aver visto le pagine, il campione
non sarebbe cieco.

Read-only sui PDF, nessuna scrittura. Stampa il campione su stdout.

Le etichette di manuale e i numeri di pagina esclusi qui sotto sono il verbale
di cosa era gia' stato guardato mentre il meccanismo veniva costruito, non una
soluzione: `AGENTS.MD` §Aggiornamento documenti ammette esplicitamente questa
forma negli script committati in quanto verbale.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import fitz

# --- Regola di estrazione, da Criterio_UscitaIR2Minima_v1.md §4 --------------

SEED = "20260818"
SAMPLE_SIZE = 10
MIN_MANUALS = 4

# Esclusioni aggiuntive per il criterio della tabella
# (`Criterio_TabellaRisolvibile_v1.md` §4, ripreso da `Criterio_TabellaInIR2_v1.md`):
# le pagine gia' guardate nella sessione sulle schede mostro.
TABLE_CRITERION_EXCLUSIONS = frozenset({
    ("DB", 89), ("DrM", 86), ("Vil", 222),
})

# I 16 manuali del corpus. TabellaManGrafic.pdf e test.pdf non sono manuali e
# non entrano nel pool.
MANUALS = (
    "Apo", "BiD", "BoB", "Dag", "DB", "DIE", "DrM", "DrW",
    "Fab", "FW", "FWK", "Kul", "Lan", "SV", "Vil", "Wil",
)

# Pagine di sviluppo, escluse per costruzione: gia' guardate mentre il
# meccanismo veniva costruito. Indici 0-based.
DEVELOPMENT_PAGES = frozenset({
    ("DB", 98),    # p.99 posizionale, stampata 97
    ("DB", 17),    # p.18 posizionale
    ("DB", 52),    # p.53 posizionale
    ("DB", 49),    # p.50 posizionale
    ("Dag", 83),   # p.84 posizionale
    ("Dag", 163),  # p.164 posizionale
    ("DrW", 96),   # p.97 posizionale
})


def _is_admissible(page: fitz.Page) -> tuple[bool, str]:
    """Guardie dei producer piu' presenza di testo (criterio §4)."""

    if page.rotation != 0:
        return False, "rotation"
    if tuple(page.mediabox) != tuple(page.cropbox):
        return False, "mediabox!=cropbox"
    if not page.get_text("text").strip():
        return False, "nessun testo"
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument(
        "--seed",
        default=SEED,
        help=f"seed dichiarato nel criterio (default: {SEED}, quello gia' a verbale)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=SAMPLE_SIZE,
        help=f"pagine da estrarre (default: {SAMPLE_SIZE})",
    )
    parser.add_argument(
        "--exclude-table-criterion-pages",
        action="store_true",
        help="esclude anche le pagine gia' guardate nella sessione sulle schede mostro",
    )
    args = parser.parse_args()

    excluded = DEVELOPMENT_PAGES | (
        TABLE_CRITERION_EXCLUSIONS if args.exclude_table_criterion_pages else frozenset()
    )

    documents: dict[str, fitz.Document] = {}
    pool: list[tuple[str, int]] = []
    for name in MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        document = fitz.open(path)
        documents[name] = document
        pool.extend(
            (name, index) for index in range(len(document)) if (name, index) not in excluded
        )

    print(f"pool: {len(pool)} pagine da {len(documents)} manuali")
    print(f"escluse per costruzione: {len(excluded)}")
    print(f"seed: {args.seed}")
    print()

    rng = random.Random(args.seed)
    order = rng.sample(pool, len(pool))

    sample: list[tuple[str, int]] = []
    discarded: list[tuple[str, int, str]] = []
    extension = 0

    for name, index in order:
        if len(sample) >= args.size:
            if len({n for n, _ in sample}) >= MIN_MANUALS:
                break
            extension += 1
        admissible, reason = _is_admissible(documents[name][index])
        if not admissible:
            discarded.append((name, index, reason))
            continue
        sample.append((name, index))

    manuals = sorted({name for name, _ in sample})
    print(f"campione: {len(sample)} pagine, {len(manuals)} manuali ({', '.join(manuals)})")
    if extension:
        print(f"estensione per raggiungere {MIN_MANUALS} manuali: {extension} estrazioni")
    print(f"scarti (guardia o pagina vuota): {len(discarded)}")
    for name, index, reason in discarded:
        print(f"    scartata {name} idx={index}: {reason}")
    print()
    print("manuale  idx(0-based)  --page-number(1-based)")
    for name, index in sample:
        print(f"{name:8s} {index:12d}  {index + 1:22d}")


if __name__ == "__main__":
    main()
