"""Le pagine dove un subordinato entra in una banda che solo il suo SPAN tocca.

`_is_subordinate` decide la nidificazione sugli estremi probatori dal
16 agosto 2026. La **collocazione** del subordinato dentro una colonna del padre
no: `_segment_tree` la filtra ancora con `span_y0`/`span_y1`
(`prototype_derived_column_bands.py:918-919`). Sono due meta' della stessa
decisione prese con due grandezze diverse, ed e' il difetto di DB p.53 un livello
piu' in basso -- una figlia che eredita un confine x appartenente a una struttura
che, nella fascia dove e' dimostrata, non la contiene affatto.

Rilievo della revisione indipendente (giro architetturale). Questo script lo
riproduce per conto proprio e, soprattutto, **stampa le pagine**: la revisione
aveva misurato 23 casi senza guardarne nessuno, che e' lo stesso errore in cui
questa diagnostica e' gia' caduta quattro volte.

LIMITE DICHIARATO: il filtro delle righe 914-919 e' **copiato**, non richiamato,
perche' vive dentro una closure di `_segment_tree` e non e' raggiungibile
dall'esterno. Una copia puo' divergere dall'originale: se `_segment_tree` cambia,
questo script va riletto. Il numero prodotto va confrontato con quello della
revisione indipendente proprio per questo -- due percorsi diversi che danno lo
stesso numero valgono piu' di uno solo.

I numeri di pagina sono POSIZIONALI. Non un producer. Non wired. Sola lettura.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
for candidate_dir in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate_dir) not in sys.path:
        sys.path.insert(0, str(candidate_dir))

import prototype_derived_column_bands as M  # noqa: E402


def scan_page(document: fitz.Document, page_index: int, manual: str) -> list[dict[str, object]]:
    """Rileva la condizione al PRIMO livello, che e' dove l'effetto si vede."""

    calls: list[tuple[list, list]] = []
    original = M._segment_bands

    def spy(rects, *, bin_width_x):  # type: ignore[no-untyped-def]
        bands = original(rects, bin_width_x=bin_width_x)
        calls.append((list(rects), list(bands)))
        return bands

    M._segment_bands = spy  # type: ignore[assignment]
    try:
        M._process_page(
            document,
            page_index,
            manual=manual,
            bin_width_x=1.0,
            bin_height_y=2.0,
            min_flanking_groups=2,
            min_flanking_chars=M._DEFAULT_MIN_FLANKING_CHARS,
            min_gutter_lines=3.0,
        )
    except Exception:  # noqa: BLE001
        return []
    finally:
        M._segment_bands = original  # type: ignore[assignment]

    if not calls:
        return []

    # I rect passati alla PRIMA chiamata sono i massimali di primo livello; le
    # bande che ne escono sono quelle in cui i subordinati vengono collocati.
    top_rects, top_bands = calls[0]
    all_rects = {id(r): r for rects, _ in calls for r in rects}
    subordinate = [r for r in all_rects.values() if r not in top_rects]

    findings: list[dict[str, object]] = []
    for band_y0, band_y1, crossing in top_bands:
        bounds = [0.0] + [edge for pair in crossing for edge in pair] + [1e9]
        for index in range(0, len(bounds) - 1, 2):
            col_x0, col_x1 = bounds[index], bounds[index + 1]
            for r in subordinate:
                rx0 = r.x_bin_start * 1.0
                rx1 = (r.x_bin_end + 1) * 1.0
                if not (rx0 >= col_x0 and rx1 <= col_x1):
                    continue
                # copia delle righe 918-919
                placed_by_span = r.span_y0 < band_y1 and band_y0 < r.span_y1
                overlaps_probative = r.y0 < band_y1 and band_y0 < r.y1
                if placed_by_span and not overlaps_probative:
                    findings.append(
                        {
                            "manual": manual,
                            "page_positional": page_index + 1,
                            "band_y0": round(band_y0, 1),
                            "band_y1": round(band_y1, 1),
                            "sub_x": f"{rx0:.0f}-{rx1:.0f}",
                            "sub_probative": f"{r.y0:.0f}-{r.y1:.0f}",
                            "sub_span": f"{r.span_y0:.0f}-{r.span_y1:.0f}",
                            "dove": "sopra" if r.y1 <= band_y0 else "sotto",
                        }
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuals", nargs="+", required=True)
    parser.add_argument("--first-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=60)
    args = parser.parse_args(argv)

    rows: list[dict[str, object]] = []
    for manual in args.manuals:
        pdf_path = cast(Path, args.pdf_dir) / f"{manual}.pdf"
        if not pdf_path.is_file():
            continue
        with fitz.open(pdf_path) as document:
            start = args.first_page - 1
            for page_index in range(start, min(start + args.max_pages, document.page_count)):
                rows.extend(scan_page(document, page_index, manual))

    pages = sorted({(cast(str, r["manual"]), cast(int, r["page_positional"])) for r in rows})
    print(f"casi: {len(rows)}   pagine distinte: {len(pages)}")
    print()
    print(f"{'pagina':<12} {'banda y':>14}  {'subordinato x':>14} {'probatorio':>12} {'span':>12}  dove")
    for r in rows:
        print(
            f"{r['manual'] + ' p.' + str(r['page_positional']):<12} "
            f"{str(r['band_y0']) + '-' + str(r['band_y1']):>14}  "
            f"{r['sub_x']:>14} {r['sub_probative']:>12} {r['sub_span']:>12}  {r['dove']}"
        )
    print()
    print("DA GUARDARE: " + " ".join(f"{m},{p}" for m, p in pages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
