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
    Dove l'etichetta manca, il numero stampato viene **dedotto** con
    ``document_furniture_policy.deduced_number_slots``.

**Una circolarita' da dichiarare, non da nascondere.** Da quando
`Criterio_NumeroDedotto_v1.md` ha reso quella deduzione anche una **regola di
rimozione** (ramo 3), sui manuali senza etichetta numeratore e denominatore
vengono dalla stessa funzione, e la loro copertura tende al 100% per costruzione.
Non e' un difetto occulto della misura: e' cio' che il §5.B del criterio ammette,
ed e' il motivo per cui il numero informativo resta la copertura sui manuali con
etichetta **dichiarata**, dove la verita' di riferimento e' indipendente.

La deduzione **non** e' pero' arbitraria: il veto §5.A la confronta con le
etichette dichiarate di 13 manuali (`scripts/check_deduced_numbers.py`). E la
circolarita' non e' totale nemmeno qui -- il denominatore conta il numero ovunque
compaia sulla pagina, la regola toglie solo i nodi **interamente** dentro gli slot
dedotti -- ma e' abbastanza stretta da non poterne ricavare una conferma.

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

from document_furniture_policy import (  # noqa: E402
    deduced_number_slots,
    furniture_slots,
    slot_of,
)
from document_text_recurrence_measurements import (  # noqa: E402
    measure_document_text_recurrence,
    normalize_text,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

UNUSED_MANUALS = ("Apo", "BiD", "BoB", "Dag", "DrM", "DrW", "FW", "FWK", "Kul", "Vil")

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
            found = deduced_number_slots(pages)
            truth = [
                found.by_page_position.get(position, "") for position in range(len(pages))
            ]

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
