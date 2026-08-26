"""Quante occorrenze del numero di pagina l'arredo toglie dal corpo, e quante ne restano.

E' il **pavimento** di `Criterio_ArredoRicorrente_v3.md` §5, e questo script
esiste perche' senza di lui il numero non e' ricontrollabile: il §7 del criterio
si era gia' iscritto il debito, e `AGENTS.MD` §18 chiede che un numero citato in
un esito porti con se' cio' che permette di rifarlo.

**Il denominatore e' la parte difficile, e la prima versione l'ha sbagliato.**
Contare le occorrenze del numero stampato richiede di sapere qual e' il numero
stampato. Dove il PDF lo dichiara (``page.get_label()``) e' un fatto del
documento. Dove non lo dichiara -- FW, FWK, Wil -- la prima misura **saltava le
pagine**, quindi quei manuali contribuivano zero sia sopra sia sotto la frazione,
e il loro essere scoperti spariva dalla copertura invece di abbassarla.

Da qui i due modi, ed entrambi si stampano:

``--modo dichiarato``
    Solo le pagine con etichetta dichiarata. E' la misura difettosa, tenuta per
    poterla riprodurre e mostrare di quanto sbagliava.

``--modo completo``
    Dove l'etichetta manca, il numero stampato viene **dedotto** da uno slot che
    porta un numero su almeno meta' delle pagine e la cui sequenza e' strettamente
    crescente. E' una deduzione, non una dichiarazione, e sta qui come **verita' di
    riferimento per la misura**, non come regola di rimozione: dedurre per contare
    cio' che la regola manca e' lecito, dedurre per togliere sarebbe il terzo ramo,
    che va scritto in un criterio prima di essere eseguito.

Uso::

    ./venv/bin/python scripts/measure_furniture_coverage.py --pdf-dir . --pagine 40
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_furniture_policy import furniture_slots, slot_of  # noqa: E402
from document_text_recurrence_measurements import (  # noqa: E402
    measure_document_text_recurrence,
    normalize_text,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

UNUSED_MANUALS = ("Apo", "BiD", "BoB", "Dag", "DrM", "DrW", "FW", "FWK", "Kul", "Vil")
# Uno slot deve portare un numero su almeno questa frazione delle pagine per
# essere candidato. E' larga di proposito: serve a scartare il rumore, non a
# selezionare, e la monotonia e' il vero filtro.
#
# **Un quarto e non meta'**, ed e' un difetto che questa misura ha trovato da
# sola: FW e FWK stampano il numero **a lati alterni**, quindi ogni slot ne porta
# meta' -- 20 e 20 su FW, 18 e 16 su FWK. Una soglia a meta' ne prendeva uno solo,
# e il denominatore restava dimezzato dopo che era gia' stato azzerato una volta.
DEDUCED_MIN_SHARE = 0.25


def _as_number(text: str) -> int | None:
    stripped = normalize_text(text).strip("[]() .-")
    return int(stripped) if stripped.isdigit() else None


def deduce_printed_numbers(pages: list) -> dict[int, str]:
    """Il numero stampato per posizione, dedotto da una sequenza crescente.

    Torna vuoto se nessuno slot qualifica: preferisce non sapere a indovinare.
    """

    per_slot: dict[tuple[int, int], dict[int, int]] = {}
    for position, page in enumerate(pages):
        for primitive in page.text_primitives:
            value = _as_number(primitive.text)
            if value is not None:
                per_slot.setdefault(slot_of(primitive, page), {})[position] = value

    def monotone(values: dict[int, int]) -> bool:
        ordered = [values[k] for k in sorted(values)]
        return all(b > a for a, b in zip(ordered, ordered[1:], strict=False))

    merged: dict[int, int] = {}
    for values in per_slot.values():
        if len(values) < len(pages) * DEDUCED_MIN_SHARE or not monotone(values):
            continue
        # Gli slot si **fondono** invece di competere: un numero a lati alterni
        # vive in due slot che sono la stessa cosa, e sceglierne uno perderebbe
        # meta' delle pagine.
        #
        # Ma due slot che rivendicano la **stessa** pagina con valori diversi non
        # sono un numero a lati alterni: sono due colonne, e qui non c'e' modo di
        # sapere quale sia la pagina. Rifiutare e' l'unica risposta onesta, e
        # senza questa guardia `update` ne sceglieva una in silenzio.
        if any(merged.get(k, v) != v for k, v in values.items()):
            return {}
        merged.update(values)
    # La fusione va comunque rimessa alla prova: due slot disgiunti e ciascuno
    # crescente possono intrecciarsi in una sequenza che non lo e'.
    return {p: str(v) for p, v in merged.items()} if monotone(merged) else {}


def measure(pdf_path: Path, sample: int, complete: bool) -> tuple[int, int, int]:
    """(presenti, tolte, pagine esaminate) per un manuale."""

    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - sample // 2)
        pages, labels = [], []
        for index in range(first, min(len(document), first + sample)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="coverage",
                page_id=f"page:{index:04d}",
                capture_id=f"coverage:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            labels.append((page.get_label() or "").strip())
        if not pages:
            return (0, 0, 0)

        # La POLITICA gira sempre sulle etichette **dichiarate**: e' la regola in
        # giudizio, e darle quelle dedotte le farebbe eseguire il terzo ramo, che
        # non esiste ancora. La verita' di riferimento e' un'altra cosa e sta
        # sotto: serve a contare cio' che la regola manca, non ad aiutarla.
        measured = measure_document_text_recurrence(pages)
        slots = furniture_slots(list(zip(pages, labels, strict=True)), measured).all_slots

        truth = labels
        if complete and not any(labels):
            deduced = deduce_printed_numbers(pages)
            truth = [deduced.get(position, "") for position in range(len(pages))]

        present = removed = 0
        for page, label in zip(pages, truth, strict=True):
            if not label:
                continue
            for primitive in page.text_primitives:
                if normalize_text(primitive.text).strip("[]() .-") != label:
                    continue
                present += 1
                if slot_of(primitive, page) in slots:
                    removed += 1
        return (present, removed, len(pages))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=40)
    parser.add_argument("--modo", choices=("dichiarato", "completo"), default="completo")
    parser.add_argument(
        "--manuali",
        nargs="+",
        default=list(UNUSED_MANUALS),
        help="di default i dieci mai spesi per l'arredo",
    )
    args = parser.parse_args()

    complete = args.modo == "completo"
    print(f"modo: {args.modo}, finestra {args.pagine} pagine contigue a meta' manuale\n")
    print(f"{'manuale':8} {'pagine':>7} {'presenti':>9} {'tolte':>7} {'copertura':>10}")
    total_present = total_removed = 0
    for name in args.manuali:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"{name:8} MANCANTE")
            continue
        present, removed, seen = measure(path, args.pagine, complete)
        total_present += present
        total_removed += removed
        share = f"{removed / present:.0%}" if present else "n/d"
        print(f"{name:8} {seen:>7} {present:>9} {removed:>7} {share:>10}")
    share = total_removed / total_present if total_present else 0.0
    print(f"\n{'TOTALE':8} {'':>7} {total_present:>9} {total_removed:>7} {share:>9.1%}")
    print(f"barra del criterio: tre quarti. {'REGGE' if share >= 0.75 else 'CADE'}")


if __name__ == "__main__":
    main()
