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

# Esclusioni per `Criterio_TabellaNormale_v1.md` §3: le pagine guardate mentre il
# percorso tabella veniva costruito (regione, colonne, righe). Sono il verbale di
# cosa e' gia' stato visto, non una selezione: escluderle e' cio' che rende cieco
# il campione. Indici 0-based.
NORMAL_TABLE_EXCLUSIONS = frozenset({
    # Le 16 tabelle su cui il meccanismo a massimo numero di colonne e' stato
    # costruito e misurato (`Esito_RegioneTabellaPerColonne_v1.md`), piu' quelle
    # tracciate a mano dall'utente. Escluderle e' cio' che rende cieco il
    # campione successivo.
    ("Dag", 133), ("Dag", 135), ("DB", 122), ("DrM", 32), ("DrM", 35),
    ("DrW", 32), ("DrW", 239), ("DrW", 247), ("BoB", 238), ("Wil", 73),
    ("Dag", 117), ("SV", 43), ("SV", 189), ("Fab", 280), ("Fab", 272),
    ("Lan", 284), ("Lan", 109),
    ("DB", 75),    # ARMI DA MISCHIA, 9 colonne
    ("Lan", 118), ("Lan", 40), ("Lan", 109), ("Lan", 284),
    ("Fab", 52), ("Fab", 272), ("Fab", 280), ("Fab", 256),
    ("Dag", 136), ("Dag", 194),
    ("SV", 43), ("SV", 189),
    ("Apo", 46), ("Vil", 166), ("Wil", 244), ("DrM", 267), ("FW", 62),
    # Quattro pagine di sviluppo che mancavano da questa lista, aggiunte da
    # `Criterio_FormaMancante_v3.md` §4. La lacuna NON nasce qui: lo script
    # copia `Criterio_TabellaNormale_v1.md:59-62`, che ne elenca 18 mentre il
    # criterio gemello committato nello stesso commit
    # (`Criterio_EstensioneRegioneTabella_v1.md:41-42`) ne elencava gia' 17,
    # quattro delle quali non ci sono finite. Verificato che nessuna delle
    # quattro compaia fra le 60 pagine di `Campione_TabellaNormale_v1.md`:
    # quel campione non e' contaminato e il suo verdetto regge.
    ("DB", 61), ("Lan", 18), ("Lan", 51), ("Wil", 77),
})

# Esclusioni per `Criterio_FormaMancante_v3.md` §4: le pagine su cui l'utente ha
# gia' dato un giudizio, e che quindi non possono servire a un criterio la cui
# regola che decide E' un giudizio dell'utente. Indici 0-based.
FORMA_MANCANTE_EXCLUSIONS = frozenset({
    # Il campione di verifica di Milestone 38 (`Campione_UscitaIR2Minima_v1.md`):
    # su queste l'ordine di lettura e' gia' stato giudicato 10 su 10.
    ("FWK", 122), ("BiD", 287), ("Apo", 34), ("Vil", 64), ("FWK", 31),
    ("Wil", 71), ("Dag", 199), ("Fab", 126), ("BoB", 297), ("BiD", 314),
    # Le 60 pagine di `Campione_TabellaNormale_v1.md`, sulle quali l'utente ha
    # etichettato a vista le regioni sul render. Elenco LETTERALE, estratto dal
    # verbale e non rigenerato con lo script: la riga di comando documentata in
    # quel file oggi escluderebbe 39 pagine invece delle 28 dichiarate -- le 11
    # del blocco "16 tabelle" sono state appese qui dopo l'estrazione -- e
    # rieseguirla darebbe un campione diverso da quello che documenta.
    ("FWK", 146), ("Dag", 356), ("Lan", 21), ("Lan", 282), ("BiD", 207),
    ("Vil", 69), ("Fab", 7), ("Lan", 165), ("BiD", 227), ("Fab", 106),
    ("BiD", 306), ("Wil", 173), ("Kul", 176), ("BiD", 34), ("Dag", 254),
    ("FW", 218), ("Dag", 340), ("Wil", 267), ("FW", 143), ("Apo", 117),
    ("Lan", 98), ("Dag", 139), ("DIE", 191), ("Dag", 197), ("Wil", 111),
    ("Fab", 28), ("DB", 53), ("DrM", 182), ("Fab", 11), ("DIE", 319),
    ("Wil", 109), ("Lan", 220), ("DIE", 128), ("Vil", 75), ("FW", 78),
    ("Lan", 281), ("DrW", 256), ("Kul", 195), ("SV", 67), ("BiD", 190),
    ("Lan", 173), ("BoB", 31), ("Dag", 71), ("Wil", 58), ("DrW", 275),
    ("Lan", 184), ("DIE", 222), ("Lan", 297), ("Lan", 31), ("FWK", 220),
    ("SV", 177), ("Lan", 289), ("SV", 44), ("BoB", 376), ("DrW", 327),
    ("Lan", 128), ("Fab", 253), ("BoB", 247), ("FWK", 60), ("Kul", 85),
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
    parser.add_argument(
        "--exclude-normal-table-pages",
        action="store_true",
        help="esclude le pagine di sviluppo di `Criterio_TabellaNormale_v1.md` §3",
    )
    parser.add_argument(
        "--exclude-forma-mancante-pages",
        action="store_true",
        help="esclude le pagine gia' giudicate dall'utente (`Criterio_FormaMancante_v3.md` §4)",
    )
    args = parser.parse_args()

    excluded = (
        DEVELOPMENT_PAGES
        | (TABLE_CRITERION_EXCLUSIONS if args.exclude_table_criterion_pages else frozenset())
        | (NORMAL_TABLE_EXCLUSIONS if args.exclude_normal_table_pages else frozenset())
        | (FORMA_MANCANTE_EXCLUSIONS if args.exclude_forma_mancante_pages else frozenset())
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
