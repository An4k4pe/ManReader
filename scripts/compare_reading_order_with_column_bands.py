"""Confronto del READING ORDER con e senza `column_band`, sulla stessa pagina.

E' il test che nessuna misura sui CSV puo' sostituire, e che Milestone 36 indica
come il consumer reale di `column_band`: non "quante bande trova" ma "la pagina
si legge".

Cosa cambia fra i due output, e nient'altro: l'ORDINAMENTO delle TextPrimitive.

  baseline   `(y0, x0)` -- identico a `prototype_vertical_slice_page.py:219-220`,
             copiato qui invariato perche' il confronto sia equo.
  a bande    dentro ogni banda di `prototype_derived_column_bands.py` le
             primitive sono divise in colonne dai gutter e ogni colonna viene
             emessa per intero prima della successiva; fuori dalle bande resta
             `(y0, x0)`.

Tutto il resto -- cattura, normalizzazione, regola di interruzione di paragrafo
-- e' identico nei due rami.

Non un producer. Non wired. Nessun `RegionCandidate`. Diagnostica pura: mostra
cosa farebbe un consumer, non lo introduce nella pipeline.

Limite dichiarato: la regola di paragrafo e' quella della fetta verticale
(nuovo paragrafo quando le y di due primitive consecutive non si sovrappongono),
duplicata qui e adattata su un punto solo -- il cambio di colonna forza un
paragrafo, altrimenti l'ultima riga di una colonna si fonderebbe con la prima
della successiva. Senza quell'adattamento il confronto sarebbe truccato a
sfavore del ramo a bande.

Uso:

    python3 scripts/compare_reading_order_with_column_bands.py DIE.pdf --page 127 --output-dir output/order_die127
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prototype_derived_column_bands import _process_page  # noqa: E402

from primitive_model import TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def _baseline_order(text_primitives: list[TextPrimitive]) -> list[TextPrimitive]:
    """Copia invariata di `prototype_vertical_slice_page.py:219-220`."""

    return sorted(text_primitives, key=lambda p: (p.bbox[1], p.bbox[0]))


def _column_of(primitive: TextPrimitive, gutters: list[tuple[float, float]]) -> int:
    """Indice di colonna dentro una banda: quanti gutter stanno alla sinistra
    della primitiva. Il confronto usa il centro x, cosi' una primitiva che
    sborda leggermente su un gutter non cambia colonna."""

    center = (primitive.bbox[0] + primitive.bbox[2]) / 2.0
    return sum(1 for _, gap_end in gutters if center >= gap_end)


def _widen_band_over_visuals(
    band: tuple[float, float, list[tuple[float, float]]],
    text_primitives: list[TextPrimitive],
) -> tuple[float, float, list[tuple[float, float]]]:
    """Estende verticalmente una banda a UNA sola colonna di stacco, finche' il
    corridoio del gutter resta libero da testo.

    Perche' serve, misurato su DrW p.97: la banda si ferma dove una delle due
    colonne smette di avere TESTO, ma li' la colonna non e' finita -- e'
    occupata da un'immagine (x 57-299, y 45-386). Il producer non puo'
    accorgersene, perche' un gutter richiede testo da entrambe le parti; il
    consumer si', perche' vede tutta la pagina. E' l'invariante di
    `AGENTS.MD` §Layout e candidati applicato: la combinazione fra regioni di
    producer diversi si fa qui, non dentro il producer.

    Il corridoio viene RISTRETTO al piu' largo sotto-intervallo che nessuna
    primitiva di testo attraversa -- stesso principio di `_largest_free_run`
    nel producer. Su DrW p.97 il gutter dichiarato e' x 299-323 ma sei righe
    della colonna destra cominciano a 313; ristretto a 299-313 il corridoio e'
    libero sull'intera pagina e la banda si estende da y 46 a 761 invece che
    396-652.

    Limite dichiarato: si applica solo alle bande con UN gutter. Le bande a piu'
    colonne restano invariate -- estenderle richiederebbe restringere piu'
    corridoi insieme, non misurato."""

    y0, y1, gutters = band
    if len(gutters) != 1:
        return band
    gap_start, gap_end = gutters[0]

    crossing = [
        p for p in text_primitives if p.bbox[0] < gap_end and p.bbox[2] > gap_start
    ]
    while crossing and gap_end - gap_start > 1.0:
        # Restringe dal lato da cui il testo sborda di meno.
        left_push = max((p.bbox[2] for p in crossing if p.bbox[2] <= (gap_start + gap_end) / 2), default=None)
        right_push = min((p.bbox[0] for p in crossing if p.bbox[0] > (gap_start + gap_end) / 2), default=None)
        if left_push is not None and (right_push is None or left_push - gap_start <= gap_end - right_push):
            gap_start = left_push
        elif right_push is not None:
            gap_end = right_push
        else:
            return band
        crossing = [
            p for p in text_primitives if p.bbox[0] < gap_end and p.bbox[2] > gap_start
        ]
    if crossing:
        return band

    flanking = [p for p in text_primitives if p.bbox[2] <= gap_start or p.bbox[0] >= gap_end]
    if not flanking:
        return band
    return (
        min(y0, min(p.bbox[1] for p in flanking)),
        max(y1, max(p.bbox[3] for p in flanking)),
        [(gap_start, gap_end)],
    )


def _band_aware_order(
    text_primitives: list[TextPrimitive],
    bands: list[dict[str, object]],
    *,
    widen: bool = False,
) -> tuple[list[tuple[TextPrimitive, int]], int]:
    """Ordine a bande. Restituisce (primitiva, id_colonna) dove id_colonna
    cambia a ogni cambio di colonna o di banda, cosi' il renderer sa dove
    forzare un paragrafo. Il secondo valore e' quante primitive sono cadute
    dentro una banda."""

    parsed: list[tuple[float, float, list[tuple[float, float]]]] = []
    for band in bands:
        intervals: list[tuple[float, float]] = []
        raw = cast(str, band.get("gutter_x_intervals") or "")
        for chunk in raw.split():
            start, _, end = chunk.partition("-")
            try:
                intervals.append((float(start), float(end)))
            except ValueError:
                continue
        parsed.append((float(cast(float, band["y0"])), float(cast(float, band["y1"])), sorted(intervals)))
    if widen:
        parsed = [_widen_band_over_visuals(band, text_primitives) for band in parsed]
    parsed.sort()

    assigned: dict[int, list[TextPrimitive]] = {}
    outside: list[TextPrimitive] = []
    for primitive in text_primitives:
        center_y = (primitive.bbox[1] + primitive.bbox[3]) / 2.0
        for band_index, (y0, y1, _intervals) in enumerate(parsed):
            if y0 <= center_y < y1:
                assigned.setdefault(band_index, []).append(primitive)
                break
        else:
            outside.append(primitive)

    entries: list[tuple[float, int, object]] = []
    for band_index, (y0, _y1, _intervals) in enumerate(parsed):
        if band_index in assigned:
            entries.append((y0, 0, band_index))
    for primitive in outside:
        entries.append((primitive.bbox[1], 1, primitive))
    entries.sort(key=lambda item: (item[0], item[1]))

    ordered: list[tuple[TextPrimitive, int]] = []
    group_id = 0
    inside_count = 0
    for _y, kind, payload in entries:
        if kind == 1:
            ordered.append((cast(TextPrimitive, payload), group_id))
            continue
        band_index = cast(int, payload)
        _y0, _y1, intervals = parsed[band_index]
        members = assigned[band_index]
        inside_count += len(members)
        by_column: dict[int, list[TextPrimitive]] = {}
        for primitive in members:
            by_column.setdefault(_column_of(primitive, intervals), []).append(primitive)
        for column_index in sorted(by_column):
            group_id += 1
            for primitive in sorted(by_column[column_index], key=lambda p: (p.bbox[1], p.bbox[0])):
                ordered.append((primitive, group_id))
        group_id += 1
    return ordered, inside_count


def _render(ordered: list[tuple[TextPrimitive, int]]) -> str:
    """Regola di paragrafo della fetta verticale (nuovo paragrafo quando le y
    di due primitive consecutive non si sovrappongono), piu' un solo
    adattamento dichiarato: il cambio di colonna forza un paragrafo."""

    paragraphs: list[str] = []
    words: list[str] = []
    previous: TextPrimitive | None = None
    previous_group: int | None = None

    for primitive, group in ordered:
        text = (primitive.text or "").strip()
        starts_new = previous is None or previous_group != group
        if previous is not None and not starts_new:
            overlaps = primitive.bbox[1] < previous.bbox[3] and previous.bbox[1] < primitive.bbox[3]
            starts_new = not overlaps
        if starts_new and words:
            paragraphs.append(" ".join(words))
            words = []
        if text:
            words.append(text)
        previous = primitive
        previous_group = group
    if words:
        paragraphs.append(" ".join(words))
    return "\n\n".join(paragraphs) + "\n"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="Indice POSIZIONALE nel PDF (page_index = N-1), non il numero stampato. "
        "Stessa convenzione di tutti gli altri script diagnostici.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--widen-bands",
        action="store_true",
        help="Estende ogni banda a un gutter finche' il corridoio resta libero da testo. "
        "Recupera le colonne in cui una delle due e' occupata da un'immagine invece che "
        "da testo -- combinazione fra regioni, quindi lavoro del consumer e non del producer.",
    )
    parser.add_argument(
        "--min-flanking-chars",
        type=float,
        default=5.0,
        help="Passato invariato al meccanismo. A 0 il criterio dei caratteri e' "
        "disattivato: serve per vedere l'effetto del bug della mediana su pagine a "
        "elenco puntato, dove i marcatori sono righe di un carattere.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    output_dir = cast(Path, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    page_index = args.page - 1

    with fitz.open(pdf_path) as document:
        if not 0 <= page_index < document.page_count:
            print(f"pagina fuori range: {args.page}", file=sys.stderr)
            return 1
        _gutters, bands = _process_page(
            document,
            page_index,
            manual=pdf_path.name,
            bin_width_x=1.0,
            bin_height_y=2.0,
            min_flanking_groups=2,
            min_flanking_chars=args.min_flanking_chars,
            min_gutter_lines=3.0,
        )
        page = document.load_page(page_index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{args.page:04d}",
            capture_id=f"reading-order-compare:{page_index}",
        )

    primitive_page = normalize_backend_page_capture(capture)
    primitives = list(primitive_page.text_primitives)

    baseline = [(p, 0) for p in _baseline_order(primitives)]
    band_aware, inside = _band_aware_order(primitives, bands, widen=args.widen_bands)

    (output_dir / "order_baseline.md").write_text(_render(baseline), encoding="utf-8")
    (output_dir / "order_with_column_bands.md").write_text(_render(band_aware), encoding="utf-8")

    base_chars = sum(len((p.text or "").strip()) for p, _ in baseline)
    band_chars = sum(len((p.text or "").strip()) for p, _ in band_aware)
    print(
        f"{pdf_path.name} p.{args.page}: {len(bands)} bande, "
        f"{inside}/{len(primitives)} primitive dentro una banda",
        file=sys.stderr,
    )
    if base_chars != band_chars:
        print(
            f"INVARIANTE VIOLATA: caratteri baseline {base_chars} != a bande {band_chars}",
            file=sys.stderr,
        )
        return 1
    print(f"conservazione del contenuto ok ({base_chars} caratteri)", file=sys.stderr)
    print(f"scritti {output_dir}/order_baseline.md e {output_dir}/order_with_column_bands.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
