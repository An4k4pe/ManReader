"""Il campione di `Criterio_Elenchi_v2.md` §3.A, e il materiale per giudicarlo.

**L'unita' campionata e' un elenco**, non una riga: e' cio' che la regola
produce. Un elenco e' una sequenza di righe sorgente consecutive che si aprono
con lo **stesso** marcatore.

**Al livello delle righe sorgente, non dei nodi IR 2.** La domanda del veto e'
«il carattere tolto era contenuto, e quelle righe erano un elenco»: si risponde
guardando la sorgente. Passare dai nodi ci metterebbe in mezzo l'ordine di
lettura, che ha un difetto suo gia' dichiarato sugli elenchi a due colonne, e il
giudizio misurerebbe quello invece del marcatore.

**Due casi entrano d'ufficio e non a sorteggio**, `Criterio_Elenchi_v2.md` §3.A:
le righe `…` di FW e un elenco di DB. Sono i due che so poter rompere la regola,
e un campione che potesse non pescarli la misurerebbe dove e' comoda. Si contano
**separati** dalle 12.

Uso::

    ./venv/bin/python scripts/sample_list_items.py --pdf-dir . --out <dir> --seed 20260912
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

from document_line_start_measurements import (  # noqa: E402
    measure_document_line_starts,
    source_lines,
)
from document_list_policy import list_markers, strip_marker  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

UNUSED_MANUALS = ("Apo", "BiD", "BoB", "Dag", "DrM", "DrW", "FW", "FWK", "Kul", "Vil")
COMPULSORY = (("FW", "…"), ("DB", "✦"))
SAMPLE = 12
RENDER_DPI = 150


def lists_of(pdf_path: Path, window: int, first_page: int | None = None) -> list[dict]:
    """Gli elenchi di un manuale: le righe di una pagina con lo **stesso** marcatore.

    **Non righe consecutive**, ed e' una correzione a una prima versione che le
    chiedeva tali. Misurata, sbagliava popolazione in due modi: DrM alterna tre
    marcatori -- `!`, `@`, `#`, uno per tier -- quindi non ce ne sono mai due
    uguali di fila e il manuale dava zero elenchi; e dove una voce va a capo la
    riga di continuazione spezzava la sequenza. Il campione finiva 10 su 12
    dentro un manuale solo.

    Raggruppare per pagina e marcatore e' anche cio' che la politica fa davvero:
    marca **ogni** riga che si apre con un marcatore, senza guardare l'adiacenza.
    """

    found: list[dict] = []
    with fitz.open(pdf_path) as document:
        start = (
            first_page
            if first_page is not None
            else max(0, len(document) // 2 - window // 2)
        )
        pages, indices = [], []
        for index in range(start, min(len(document), start + window)):
            page = document[index]
            if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
                continue
            capture = capture_pymupdf_page(
                page,
                source_id="lists",
                page_id=f"page:{index:04d}",
                capture_id=f"lists:{index:04d}",
            )
            pages.append(normalize_backend_page_capture(capture))
            indices.append(index)
        if not pages:
            return found

        markers = list_markers(measure_document_line_starts(pages))
        if not markers:
            return found

        for page, index in zip(pages, indices, strict=True):
            lines = [text.strip() for _block, text in source_lines(page)]
            per_marker: dict[str, list[str]] = {}
            for position, text in enumerate(lines):
                head = text[0] if text else ""
                if head not in markers:
                    continue
                # Un marcatore da solo prende con se' la riga dopo: e' li' che
                # sta il testo della voce.
                body = text
                if len(text) == 1 and position + 1 < len(lines):
                    body = f"{text} {lines[position + 1]}"
                per_marker.setdefault(head, []).append(body)
            for marker, items in per_marker.items():
                if len(items) >= 2:
                    found.append(
                        {
                            "manuale": pdf_path.stem,
                            "marcatore": marker,
                            "pagina_idx": index,
                            "righe": items[:8],
                        }
                    )
    return found


def write_entry(lines: list[str], item: dict, position: int, label: str) -> None:
    marker = item["marcatore"]
    stem = f"{item['manuale']}_pagina{item['pagina_idx'] + 1:04d}_idx{item['pagina_idx']:04d}"
    lines.append(f"## Voce {label} — render `{stem}.png`")
    lines.append("")
    lines.append(
        f"Manuale **{item['manuale']}**. Il carattere che sta per essere tolto e' "
        f"`{marker!r}` (U+{ord(marker):04X})."
    )
    lines.append("")
    lines.append("**Come sta nella sorgente:**")
    lines.append("")
    lines.append("```")
    for text in item["righe"]:
        lines.append(text[:110])
    lines.append("```")
    lines.append("")
    lines.append("**Come uscirebbe:**")
    lines.append("")
    lines.append("```markdown")
    for text in item["righe"]:
        lines.append(f"- {strip_marker(text, frozenset(marker))[:108]}")
    lines.append("```")
    lines.append("")
    lines.append("Giudizio: ")
    lines.append("")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--pagine", type=int, default=20)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    everything: list[dict] = []
    for name in UNUSED_MANUALS:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue
        found = lists_of(path, args.pagine)
        print(f"{name}: {len(found)} elenchi", file=sys.stderr)
        everything.extend(found)

    rng = random.Random(args.seed)
    chosen = rng.sample(everything, min(SAMPLE, len(everything)))
    rng.shuffle(chosen)

    compulsory: list[dict] = []
    for name, marker in COMPULSORY:
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            continue
        # Il caso d'ufficio si cerca su tutto il manuale, non nella finestra
        # centrale: `✦` di DB sta fra idx 43 e 54, fuori dal centro, e cercarlo
        # solo li' l'avrebbe dichiarato assente quando c'e'.
        matching = []
        with fitz.open(path) as document:
            total = len(document)
        for start in range(0, total, args.pagine):
            matching = [
                item
                for item in lists_of(path, args.pagine, first_page=start)
                if item["marcatore"] == marker
            ]
            if matching:
                break
        if matching:
            compulsory.append(matching[0])
        else:
            print(f"D'UFFICIO NON TROVATO: {name} {marker!r}", file=sys.stderr)

    lines = [
        "# Voci da etichettare — elenchi",
        "",
        "Per ognuna: **elenco**, **non elenco**, oppure **incerto**.",
        "",
        f"Estratte con seed `{args.seed}`, dichiarato prima. "
        f"Sorteggiate: **{len(chosen)}**. D'ufficio: **{len(compulsory)}**.",
        "",
        "Il render della pagina sta accanto a questo file.",
        "",
    ]
    for position, item in enumerate(chosen, start=1):
        write_entry(lines, item, position, f"{position:02d}")
    for position, item in enumerate(compulsory, start=1):
        write_entry(lines, item, position, f"U{position}")

    for item in chosen + compulsory:
        idx = item["pagina_idx"]
        stem = f"{item['manuale']}_pagina{idx + 1:04d}_idx{idx:04d}"
        target = args.out / f"{stem}.png"
        if target.is_file():
            continue
        with fitz.open(args.pdf_dir / f"{item['manuale']}.pdf") as document:
            target.write_bytes(document[idx].get_pixmap(dpi=RENDER_DPI).tobytes("png"))

    (args.out / "Voci_da_etichettare.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    chiave = ["# Chiave", "", "| # | manuale | marcatore | pagina idx |", "| --- | --- | --- | --- |"]
    for position, item in enumerate(chosen, start=1):
        chiave.append(
            f"| {position:02d} | {item['manuale']} | `{item['marcatore']!r}` "
            f"U+{ord(item['marcatore']):04X} | {item['pagina_idx']} |"
        )
    for position, item in enumerate(compulsory, start=1):
        chiave.append(
            f"| U{position} | {item['manuale']} | `{item['marcatore']!r}` "
            f"U+{ord(item['marcatore']):04X} | {item['pagina_idx']} |"
        )
    (args.out.parent / f"CHIAVE_{args.out.name}.md").write_text(
        "\n".join(chiave) + "\n", encoding="utf-8"
    )
    print(f"\nelenchi totali {len(everything)}, campionati {len(chosen)} + {len(compulsory)} d'ufficio")


if __name__ == "__main__":
    main()
