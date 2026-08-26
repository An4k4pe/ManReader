"""Il veto di verita' di `Criterio_NumeroDedotto_v1.md` §5.A.

**Il controllo non e' sui manuali bersaglio.** FW, FWK e Wil sono gli unici tre
senza etichetta dichiarata: sono insieme il bersaglio e l'intero universo, e non
esiste un campione non speso su cui riprovare il ramo 3. Quindi il controllo si
esegue dove la verita' di riferimento **esiste** -- i 13 manuali che dichiarano --
facendo girare la deduzione **senza farle vedere le etichette** e confrontando.

E' il rovescio esatto del difetto del giro precedente, dove il campione era
estratto da cio' che la regola toglieva e poteva solo confermarla.

> Cade se su una sola pagina la deduzione produce un numero **diverso** da quello
> dichiarato. Astenersi non e' sbagliare: un manuale su cui rifiuta si conta e si
> riporta.

Si esegue anche il **modello nullo** ``idx + 1``. Se il modello nullo passasse, la
barra sarebbe finta e il criterio andrebbe riscritto invece che dichiarato
scaricato.

Uso::

    ./venv/bin/python scripts/check_deduced_numbers.py --pdf-dir . --pagine 40
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_furniture_policy import deduced_number_slots  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def load(pdf_path: Path, sample: int) -> tuple[list, list[str], list[int]]:
    pages, labels, indices = [], [], []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - sample // 2)
        for index in range(first, min(len(document), first + sample)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="veto",
                page_id=f"page:{index:04d}",
                capture_id=f"veto:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            labels.append((page.get_label() or "").strip())
            indices.append(index)
    return pages, labels, indices


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pagine", type=int, default=40)
    args = parser.parse_args()

    print(f"finestra {args.pagine} pagine contigue a meta' manuale\n")
    header = f"{'manuale':8} {'confronti':>10} {'accordi':>8} {'DISACCORDI':>11}  esito"
    print(header)

    disagreements: list[str] = []
    null_disagreements: list[str] = []
    abstained: list[str] = []
    without_labels: list[str] = []
    checked = 0

    for path in sorted(args.pdf_dir.glob("*.pdf")):
        name = path.stem
        try:
            pages, labels, indices = load(path, args.pagine)
        except Exception as error:  # noqa: BLE001 - un PDF illeggibile si riporta
            print(f"{name:8} ILLEGGIBILE: {error}")
            continue
        if not pages:
            continue
        if not any(labels):
            without_labels.append(name)
            continue

        checked += 1
        deduced = deduced_number_slots(pages)
        if not deduced:
            abstained.append(name)
            print(f"{name:8} {'-':>10} {'-':>8} {'-':>11}  si astiene")
            continue

        compared = agreed = 0
        for position, (label, index) in enumerate(zip(labels, indices, strict=True)):
            got = deduced.by_page_position.get(position)
            if not label or got is None:
                continue
            compared += 1
            if got == label:
                agreed += 1
            else:
                disagreements.append(f"{name} idx {index}: dedotto {got!r}, dichiarato {label!r}")
            # Modello nullo: il numero fisico al posto di quello stampato.
            if str(index + 1) != label:
                null_disagreements.append(f"{name} idx {index}: nullo {index + 1}, dichiarato {label!r}")

        bad = compared - agreed
        verdict = "ok" if bad == 0 else "CADE"
        print(f"{name:8} {compared:>10} {agreed:>8} {bad:>11}  {verdict}")

    print(f"\nmanuali con etichette dichiarate ed esaminati: {checked}")
    print(f"senza etichette (fuori dal controllo, sono il bersaglio): {', '.join(without_labels) or 'nessuno'}")
    print(f"su cui la deduzione si astiene: {', '.join(abstained) or 'nessuno'}")

    print(f"\n=== VETO §5.A: {len(disagreements)} disaccordi ===")
    for line in disagreements[:20]:
        print(f"  {line}")
    if len(disagreements) > 20:
        print(f"  ... e altri {len(disagreements) - 20}")
    print("REGGE" if not disagreements else "CADE")

    print(f"\n=== modello nullo `idx + 1`: {len(null_disagreements)} disaccordi ===")
    for line in null_disagreements[:5]:
        print(f"  {line}")
    if null_disagreements:
        print("il nullo FALLISCE la barra, quindi la barra ha i denti")
    else:
        print("ATTENZIONE: il nullo PASSA, la barra e' finta e il criterio va riscritto")


if __name__ == "__main__":
    main()
