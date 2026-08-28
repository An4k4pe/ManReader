"""Il campione di `Criterio_ArredoRicorrente_v3.md` §3, e il materiale per giudicarlo.

**Voci, non pagine.** L'unita' campionata e' lo **slot d'arredo di un manuale**,
che e' cio' che la regola toglie. Un campione di pagine vedrebbe le decisioni
rischiose -- gli slot appena sopra la soglia -- meno spesso proprio perche' sono
rare, e il criterio ne uscirebbe con un tasso di successo ottimistico senza
saperlo. Rilievo della revisione indipendente, accolto.

**Stratificato vicino alla soglia**: meta' delle voci fra il 25% e il 40% di
ricorrenza, meta' sopra. Le decisioni rischiose stanno in basso.

**Dai dieci manuali mai usati.** I sei su cui la regola e' stata progettata sono
spesi, e la cecita' alle pagine non basta quando l'adattamento e' a una
tipografia.

Il seed e' dichiarato nel criterio prima dell'estrazione.

Uso::

    ./venv/bin/python scripts/sample_furniture_items.py \\
        --pdf-dir . --out <dir> --seed 20260829 --pagine 40
"""

from __future__ import annotations

import argparse
import random
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

# I sei di progettazione sono spesi; questi sono i dieci mai usati per l'arredo.
UNUSED_MANUALS = ("Apo", "BiD", "BoB", "Dag", "DrM", "DrW", "FW", "FWK", "Kul", "Vil")
LOW_BAND = (0.25, 0.40)
SAMPLE_PER_STRATUM = 6
RENDER_DPI = 150


def collect(pdf_path: Path, sample: int) -> list[dict]:
    """Le voci d'arredo di un manuale, con la loro quota e i loro testi."""

    items: list[dict] = []
    with fitz.open(pdf_path) as document:
        first = max(0, len(document) // 2 - sample // 2)
        pages: list = []
        indices: list[int] = []
        for index in range(first, min(len(document), first + sample)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="sample",
                page_id=f"page:{index:04d}",
                capture_id=f"furniture:{index:04d}",
            )
            pages.append(
                (normalize_backend_page_capture(capture), (page.get_label() or "").strip())
            )
            indices.append(index)
        if not pages:
            return items

        measured = measure_document_text_recurrence([p for p, _ in pages])
        slots = furniture_slots(pages, measured)
        share_of = {
            (s.x, s.y): s.page_count / measured.page_count for s in measured.slots
        }
        for slot in sorted(slots.all_slots):
            texts: list[str] = []
            first_index = None
            for (primitive_page, _label), index in zip(pages, indices, strict=True):
                for primitive in primitive_page.text_primitives:
                    text = normalize_text(primitive.text)
                    if text and slot_of(primitive, primitive_page) == slot:
                        texts.append(text)
                        if first_index is None:
                            first_index = index
            if first_index is None:
                continue
            items.append(
                {
                    "manuale": pdf_path.stem,
                    "slot": slot,
                    "quota": share_of.get(slot, 0.0),
                    # L'ordine conta: uno slot puo' stare in piu' rami, e il
                    # verbale deve dire quale lo ha deciso. I due nuovi si
                    # nominano per primi perche' sono quelli in giudizio.
                    "ramo": (
                        "verticale"
                        if slot in slots.from_vertical
                        else "testo-ripetuto"
                        if slot in slots.from_repeated_text
                        else "etichetta"
                        if slot in slots.from_label
                        else "sequenza"
                        if slot in slots.from_sequence
                        else "ricorrenza"
                    ),
                    "testi": sorted(set(texts))[:6],
                    "occorrenze": len(texts),
                    "pagina_idx": first_index,
                }
            )
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--pagine", type=int, default=40)
    parser.add_argument(
        "--manuali", nargs="+", default=list(UNUSED_MANUALS),
        help="di default i dieci mai spesi per l'arredo",
    )
    parser.add_argument(
        "--solo-ramo",
        choices=("etichetta", "ricorrenza", "sequenza", "testo-ripetuto", "verticale"),
        help="giudica solo le voci di un ramo: serve quando un ramo nuovo va "
             "provato da solo, senza che le voci dei rami gia' spediti lo diluiscano",
    )
    parser.add_argument("--voci", type=int, default=SAMPLE_PER_STRATUM)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    tutte: list[dict] = []
    for name in args.manuali:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        found = collect(path, args.pagine)
        if args.solo_ramo:
            found = [item for item in found if item["ramo"] == args.solo_ramo]
        print(f"{name}: {len(found)} voci", file=sys.stderr)
        tutte.extend(found)

    basse = [i for i in tutte if LOW_BAND[0] <= i["quota"] < LOW_BAND[1]]
    alte = [i for i in tutte if i["quota"] >= LOW_BAND[1]]
    rng = random.Random(args.seed)
    per_strato = max(1, args.voci // 2)
    scelte = rng.sample(basse, min(per_strato, len(basse))) + rng.sample(
        alte, min(per_strato, len(alte))
    )
    rng.shuffle(scelte)

    righe = [
        "# Voci da etichettare",
        "",
        "Per ognuna: **arredo**, **contenuto**, oppure **incerto**.",
        "",
        "Il render della pagina in cui la voce compare sta accanto a questo file,",
        "col nome indicato in ogni riga.",
        "",
        f"Voci: **{len(scelte)}**. Estratte con seed `{args.seed}`, dichiarato prima.",
        "",
    ]
    chiave = ["# Chiave — non aprire prima di aver etichettato", "", "| # | manuale | slot | quota | ramo |", "| --- | --- | --- | --- | --- |"]

    for position, item in enumerate(scelte, start=1):
        idx = item["pagina_idx"]
        stem = f"{item['manuale']}_pagina{idx + 1:04d}_idx{idx:04d}"
        righe.append(f"## Voce {position:02d} — render `{stem}.png`")
        righe.append("")
        righe.append(f"Compare **{item['occorrenze']} volte** nelle pagine esaminate. Testi:")
        righe.append("")
        for text in item["testi"]:
            righe.append(f"- `{text[:80]}`")
        righe.append("")
        righe.append("Giudizio: ")
        righe.append("")
        chiave.append(
            f"| {position:02d} | {item['manuale']} | {item['slot']} "
            f"| {item['quota']:.0%} | {item['ramo']} |"
        )

        with fitz.open(args.pdf_dir / f"{item['manuale']}.pdf") as document:
            pixmap = document[idx].get_pixmap(dpi=RENDER_DPI)
            (args.out / f"{stem}.png").write_bytes(pixmap.tobytes("png"))

    (args.out / "Voci_da_etichettare.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text(
        "\n".join(chiave) + "\n", encoding="utf-8"
    )
    print(f"\nvoci totali {len(tutte)}: {len(basse)} fra 25-40%, {len(alte)} sopra")
    print(f"campionate {len(scelte)}, materiale in {args.out}")


if __name__ == "__main__":
    main()
