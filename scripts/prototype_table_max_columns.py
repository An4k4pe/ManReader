"""La tabella e' dove si forma il maggior numero di colonne coerenti fra loro.

Ribaltamento proposto dall'utente. Finora: scegli delle bande, ricava i gutter --
e per scegliere le bande giuste bisognerebbe gia' sapere dov'e' la tabella.
Qui si cerca **l'insieme di gutter piu' numeroso che regge**, e le bande che quei
gutter attraversano SONO la tabella. La regione non si sceglie: si deduce.

Regole, come sono state date:

- vince **piu' colonne**, non piu' altezza: due gutter che sopravvivono a tutta la
  pagina eliminando quelli interni descrivono l'impaginazione, non una tabella;
- servono **almeno 3 gutter compresi gli esterni**, cioe' almeno due colonne:
  sotto e' testo semplice;
- servono **almeno 3 righe**: sotto si descrive meglio con un elenco o del testo.

I candidati non vengono da una fonte sola: corridoi di bianco, gutter di
`column_band`, filetti verticali disegnati.

Read-only. Uso:

    ./venv/bin/python scripts/prototype_table_max_columns.py --pdf-dir . \
        --pages Lan:18 BoB:238 DB:75 --outdir output/max
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prototype_table_gutter_extension import (  # noqa: E402
    BIN,
    _blockers,
    _mark,
    _row_bands,
)

from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

MIN_ROWS = 3
MIN_GUTTERS = 3  # esterni compresi
MIN_WIDTH = 2.0


def _column_band_gutters(page: NormalizedPrimitivePage) -> list[tuple[float, float]]:
    """I gutter che `column_band` segnala: un'altra fonte di candidati."""

    from page_analysis_column_band import build_column_band_page_analysis_with_measurements

    try:
        _analysis, measures = build_column_band_page_analysis_with_measurements(
            page, generation_id="max-columns"
        )
    except Exception:
        return []
    return [interval for measure in measures for interval in measure.gutter_x_intervals]


def _drawn_rules(page: NormalizedPrimitivePage) -> list[tuple[float, float]]:
    """I filetti verticali, fusi per x: gutter gia' tracciati."""

    merged: list[list[float]] = []
    for drawing in page.drawing_primitives:
        x0, y0, x1, y1 = drawing.bbox
        if y1 - y0 <= 0 or (x1 - x0) > (y1 - y0) / 4.0:
            continue
        centre = (x0 + x1) / 2.0
        for entry in merged:
            if abs(entry[0] - centre) <= 1.0:
                break
        else:
            merged.append([centre])
    return [(c[0] - 0.5, c[0] + 0.5) for c in merged]


def analyse(page: NormalizedPrimitivePage) -> list[dict[str, object]]:
    bands = _row_bands(page)
    if len(bands) < MIN_ROWS:
        return []
    width = page.page_geometry.width
    bins = int(width / BIN) + 1

    occ: list[bytearray] = []
    spans: list[tuple[float, float]] = []
    for band in bands:
        row = bytearray(bins)
        lo, hi = width, 0.0
        for line in band:
            for primitive in line.primitives:
                _mark(row, primitive.bbox[0], primitive.bbox[2], width, bins)
                lo = min(lo, primitive.bbox[0])
                hi = max(hi, primitive.bbox[2])
        occ.append(row)
        spans.append((lo, hi))

    blockers = _blockers(page)
    blocked: list[bytearray] = []
    for band in bands:
        top = min(min(p.bbox[1] for p in line.primitives) for line in band)
        bottom = max(max(p.bbox[3] for p in line.primitives) for line in band)
        row = bytearray(bins)
        for bx0, by0, bx1, by1 in blockers:
            if by1 > top and by0 < bottom:
                _mark(row, bx0, bx1, width, bins)
        blocked.append(row)

    hinted = _column_band_gutters(page) + _drawn_rules(page)
    hint_bins = {
        i
        for a, b in hinted
        for i in range(max(0, int(a / BIN)), min(bins, int(b / BIN) + 1))
    }

    def evaluate(b0: int, b1: int) -> tuple[int, list[tuple[int, int]], float, float] | None:
        """Quante colonne coerenti si formano su questa corsa di bande."""

        lo = min(spans[b][0] for b in range(b0, b1))
        hi = max(spans[b][1] for b in range(b0, b1))
        free = bytearray(1 for _ in range(bins))
        for b in range(b0, b1):
            for i in range(bins):
                if occ[b][i] or blocked[b][i]:
                    free[i] = 0
        internal: list[tuple[int, int]] = []
        start = None
        for i in range(bins + 1):
            open_here = i < bins and free[i] and lo < i * BIN < hi
            if open_here and start is None:
                start = i
            elif not open_here and start is not None:
                if (i - start) * BIN >= MIN_WIDTH:
                    internal.append((start, i))
                start = None
        # una colonna vuota su tutte le righe non descrive niente: il gutter che
        # la delimita non fa parte del pattern
        edges = [int(lo / BIN)] + [g[1] for g in internal]
        rights = [g[0] for g in internal] + [int(hi / BIN) + 1]
        def rows_with_text(a: int, b: int) -> int:
            return sum(
                1
                for band in range(b0, b1)
                if any(occ[band][k] for k in range(max(0, a), min(bins, b)))
            )

        rows = b1 - b0
        keep: list[tuple[int, int]] = []
        fill: list[float] = []
        for index, gutter in enumerate(internal):
            left = rows_with_text(edges[index], gutter[0])
            right = rows_with_text(gutter[1], rights[index + 1])
            if left and right:
                keep.append(gutter)
                fill.append(min(left, right) / rows)
        # SCARTO DEL BORDINO, regola gia' in produzione in
        # `page_analysis_column_band.py:764` (`wide_enough`), formulata
        # dall'utente: «il minimo di larghezza si applica SOLO alle colonne che
        # toccano il bordo della pagina -- una linguetta di capitolo produce una
        # colonna strettissima AL BORDO, una tabella la produce ALL'INTERNO».
        #
        # E' il discriminante che mancava per BoB pagina 239, dove il gutter
        # `395-414` lascia a destra una colonna strettissima che tocca il bordo:
        # e' la linguetta `227`, non una colonna di tabella.
        from page_analysis_column_band import _AVERAGE_CHAR_WIDTH_RATIO, _median_font_size

        font_size = _median_font_size(list(page.text_primitives))
        min_column_width = 10.0 * font_size * _AVERAGE_CHAR_WIDTH_RATIO if font_size > 0 else 0.0
        if min_column_width > 0 and keep:
            first = keep[0]
            if (
                lo <= 0.5 + BIN
                and first[0] * BIN - lo < min_column_width
            ):
                keep = keep[1:]
            if keep and (
                hi >= width - 0.5 - BIN
                and hi - keep[-1][1] * BIN < min_column_width
            ):
                keep = keep[:-1]
        if not keep:
            return None
        # VINCOLO DI BANDA — PROVATO E RITIRATO nella forma «un gutter di
        # `column_band` dentro la regione dev'essere fra i suoi confini di
        # colonna». Non scatta dove serve e fa perdere una pagina dove non
        # serviva:
        #
        # - su DrW pagina 248 il gutter di pagina `292-307`, quello che separa la
        #   prosa dalla tabella, **e' anche uno dei sei gutter che la regione
        #   trova**, quindi il confronto lo dichiara corrispondente e passa.
        #   Stesso esito su DrM pagina 36 (`245-264`) e Dag pagina 136
        #   (`296-306`): il confine di pagina e' un corridoio come gli altri e la
        #   regione lo adotta come colonna;
        # - DB pagina 123 passava da 6 colonne al 100% di pienezza a NESSUNA
        #   regione.
        #
        # Il vincolo giusto deve distinguere un gutter che separa DUE BANDE da
        # uno che separa due colonne della stessa tabella, e su DB pagina 76 il
        # gutter di `column_band` a profondita' 0 e' proprio una colonna della
        # tabella -- quindi la profondita' non basta.
        bonus = sum(1 for g in keep if any(k in hint_bins for k in range(g[0], g[1])))
        # Quanto le colonne sono PIENE: e' il «pattern coerente». A parita' di
        # numero di colonne, un insieme in cui ogni colonna porta testo su quasi
        # tutte le righe descrive una tabella; uno in cui una colonna ha testo su
        # una riga sola descrive un accostamento.
        #
        # Serve su BoB pagina 239, dove non c'e' ne' un gutter di `column_band`
        # ne' un filetto: i due candidati danno entrambi due colonne, e senza
        # questo vince il piu' alto, che e' il MARGINE -- la sua colonna destra
        # ha testo su una banda sola, quella della linguetta `227`.
        coherence = sum(fill) / len(fill)
        return len(keep) + 2, keep, lo, hi, bonus, coherence  # type: ignore[return-value]

    best: tuple[tuple[int, int, int], tuple[int, int], list[tuple[int, int]], float, float] | None
    best = None
    for b0 in range(len(bands)):
        for b1 in range(b0 + MIN_ROWS, len(bands) + 1):
            result = evaluate(b0, b1)
            if result is None:
                continue
            count, keep, lo, hi, bonus, coherence = result  # type: ignore[misc]
            if count < MIN_GUTTERS:
                continue
            score = (count, bonus, round(coherence, 2), b1 - b0)
            if best is None or score > best[0]:
                best = (score, (b0, b1), keep, lo, hi)
    if best is None:
        return []

    (count, bonus, coherence, height), (b0, b1), keep, lo, hi = best

    # Trovati i gutter, si ESTENDONO con le due regole:
    #  1. si fermano tutti quando uno incontra testo o un bloccante;
    #  2. si estendono finche' almeno una cella fra due gutter contiene testo.
    # Il gutter si RESTRINGE per adattarsi invece di spezzare la regione.
    edges = [int(lo / BIN)] + [g[1] for g in keep]
    rights = [g[0] for g in keep] + [int(hi / BIN) + 1]
    cells = [(a, b) for a, b in zip(edges, rights, strict=False) if b > a]

    # PROVATO E RITIRATO: far partecipare i gutter ESTERNI alla clausola 1.
    # L'idea e' giusta -- sopra una tabella la prosa e' piu' larga della tabella,
    # tocca i bordi e chiude tutto, ed e' «l'altezza massima delle colonne» che
    # l'utente ha disegnato su BoB pagina 239 -- ma messo a filo dell'inchiostro
    # il gutter esterno viene toccato dalle righe stesse: BoB passa da bande
    # 12-22, che sono la tabella intera, a 15-22. Servirebbe collocarlo nel
    # margine, e dove sia il margine e' la domanda aperta di BoB.
    extended = list(keep)
    live = [bytearray(1 for _ in range(x1 - x0)) for x0, x1 in extended]

    def admits(band: int) -> bool:
        trial = []
        for index, (x0, x1) in enumerate(extended):
            mask = bytearray(
                1
                if live[index][k] and not (occ[band][x0 + k] or blocked[band][x0 + k])
                else 0
                for k in range(x1 - x0)
            )
            if not any(mask):
                return False
            trial.append(mask)
        if not any(
            any(occ[band][k] for k in range(max(0, a), min(bins, b))) for a, b in cells
        ):
            return False
        for index, mask in enumerate(trial):
            live[index] = mask
        return True

    while b1 < len(bands) and admits(b1):
        b1 += 1
    live[:] = [bytearray(1 for _ in range(x1 - x0)) for x0, x1 in extended]
    while b0 > 0 and admits(b0 - 1):
        b0 -= 1

    narrowed: list[tuple[int, int]] = []
    for x0, x1 in keep:
        mask = bytearray(1 for _ in range(x1 - x0))
        for band in range(b0, b1):
            for k in range(x1 - x0):
                if occ[band][x0 + k] or blocked[band][x0 + k]:
                    mask[k] = 0
        if not any(mask):
            continue
        first = next(k for k in range(len(mask)) if mask[k])
        last = next(k for k in range(len(mask) - 1, -1, -1) if mask[k])
        narrowed.append((x0 + first, x0 + last + 1))
    if narrowed:
        keep = narrowed

    members = [line for band in bands[b0:b1] for line in band]
    return [
        {
            "bands": (b0, b1),
            "gutters": [(a * BIN, b * BIN) for a, b in keep],
            "columns": count - 1,
            "hinted": bonus,
            "coherence": coherence,
            "bbox": (
                min(min(p.bbox[0] for p in line.primitives) for line in members),
                min(min(p.bbox[1] for p in line.primitives) for line in members),
                max(max(p.bbox[2] for p in line.primitives) for line in members),
                max(max(p.bbox[3] for p in line.primitives) for line in members),
            ),
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True)
    parser.add_argument("--outdir", type=Path)
    args = parser.parse_args()

    for spec in args.pages:
        name, raw = spec.split(":")
        index = int(raw)
        document = fitz.open(args.pdf_dir / f"{name}.pdf")
        page = document[index]
        capture = capture_pymupdf_page(
            page,
            source_id="max-columns",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"max:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        print(f"\n### {name} idx {index} (pagina file {index + 1})")
        for result in analyse(primitive_page):
            b0, b1 = result["bands"]  # type: ignore[misc]
            x0, y0, x1, y1 = result["bbox"]  # type: ignore[misc]
            gutters = result["gutters"]  # type: ignore[assignment]
            print(
                f"   bande {b0}-{b1}  y {y0:6.1f}-{y1:6.1f}  "
                f"colonne={result['columns']}  confermati={result['hinted']}  "
                f"pienezza={result['coherence']:.0%}"
            )
            print(f"      gutter: {[f'{a:.0f}-{b:.0f}' for a, b in gutters]}")
            if args.outdir is not None:
                shape = page.new_shape()
                shape.draw_rect(fitz.Rect(x0, y0, x1, y1))
                shape.finish(color=(0, 0, 0.9), width=2.0, dashes="[4 3] 0")
                shape.commit()
                for gx0, gx1 in gutters:
                    shape = page.new_shape()
                    shape.draw_rect(fitz.Rect(gx0, y0, gx1, y1))
                    shape.finish(fill=(0.9, 0, 0), fill_opacity=0.55, width=0)
                    shape.commit()
        if args.outdir is not None:
            args.outdir.mkdir(parents=True, exist_ok=True)
            out = args.outdir / f"{name}_pagina{index + 1:04d}.png"
            page.get_pixmap(dpi=110).save(out)
            print(f"   reso: {out}")


if __name__ == "__main__":
    main()
