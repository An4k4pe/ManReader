"""Le due regole di estensione dei gutter, nella formulazione dell'utente.

Regola, come e' stata data:

1. **Tutte le linee gutter estese si stendono finche' non incontrano del testo; a
   quel punto si fermano TUTTE — ne basta una.**
2. **Si estendono finche' intorno ad almeno una linea gutter, alla distanza a cui
   di solito si trova del testo nella stessa riga, c'e' del testo. Quando nessuna
   linea ha testo ai lati, l'estensione si ferma.**

Poi tutti i gutter si rendono uguali in estensione e si legge la tabella.

Due precisazioni dell'utente, entrambe verificate su render e non dedotte:

- le illustrazioni **non** devono allungare la corsa: sotto la tabella di Lan
  pagina 19 i gutter veri proseguono attraverso quattro ritratti, perche' per una
  griglia di sola occupazione testuale li' e' vuoto;
- ma i **filetti** che a volte attraversano una tabella **non devono bloccarla**,
  quindi entrano nella griglia le immagini e i disegni compatti, non le righe
  sottili.

La «distanza a cui di solito si trova del testo» non e' una costante: si misura
sul seme, per ogni gutter, come la distanza massima osservata dal bordo del gutter
al testo piu' vicino nelle righe della tabella.

Read-only. Uso:

    ./venv/bin/python scripts/prototype_table_gutter_extension.py --pdf-dir . \
        --pages Lan:18 BoB:238 DB:75
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ir2_builder import _SourceLine, group_source_lines  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

BIN = 1.0
MIN_BANDS = 3
MIN_GUTTER = 2.0
THIN_RULE_RATIO = 6.0


def _is_rotated(primitive: object) -> bool:
    """Testo scritto in verticale, da `TextPrimitive.direction`.

    Stessa definizione gia' in produzione in `page_analysis_column_band.py`
    (`_rotated_group_ids`), dove serve a escludere le **linguette di capitolo**,
    «la causa verificata dei falsi positivi».

    Qui serve per la stessa ragione, vista da un altro lato: su Lan pagina 19 la
    linguetta ruotata da' due righe di sorgente alte 116 e 90 punti, e il
    raggruppamento in bande ancora tutto a loro -- titolo, intestazione e prima
    riga di dati finiscono in un'unica banda, e con esse il livello `0`.
    """

    direction = getattr(primitive, "direction", None)
    if direction is None:
        return False
    return abs(direction[1]) > abs(direction[0])


def _row_bands(page: NormalizedPrimitivePage) -> list[list[_SourceLine]]:
    lines = group_source_lines(
        [p for p in page.text_primitives if p.text.strip() and not _is_rotated(p)]
    )
    if not lines:
        return []
    ordered = sorted(lines, key=lambda line: min(p.bbox[1] for p in line.primitives))

    # Il confine di banda si misura sull'INTERLINEA DELLA PAGINA, non sul fondo
    # della riga di ancoraggio. Con il fondo, una riga alta inghiotte tutte
    # quelle che le stanno sotto: su Lan pagina 19 il `1` del capitolo e' un
    # numero display alto 115pt -- orizzontale, quindi la regola sul testo
    # ruotato non lo prende -- e trascina nella stessa banda titolo,
    # intestazione e prima riga di dati, e con esse il livello `0`.
    heights = sorted(
        max(p.bbox[3] for p in line.primitives) - min(p.bbox[1] for p in line.primitives)
        for line in ordered
    )
    step = heights[len(heights) // 2] if heights else 0.0

    bands = [[ordered[0]]]
    anchor_top = min(p.bbox[1] for p in ordered[0].primitives)
    for line in ordered[1:]:
        top = min(p.bbox[1] for p in line.primitives)
        bottom = max(p.bbox[3] for p in line.primitives)
        anchor_bottom = max(
            max(p.bbox[3] for p in member.primitives) for member in bands[-1]
        )
        same = top < anchor_bottom - 1.0 and top - anchor_top < step
        if same or (top < anchor_bottom - 1.0 and bottom - top >= step * 2):
            bands[-1].append(line)
        else:
            bands.append([line])
            anchor_top = top
    return bands


def _blockers(page: NormalizedPrimitivePage) -> list[tuple[float, float, float, float]]:  # noqa: C901
    """Immagini e disegni compatti: bloccano un gutter. I filetti sottili no.

    Un filetto orizzontale attraversa la tabella per disegnarne le righe: se
    bloccasse, nessun gutter potrebbe estendersi in una tabella tracciata.
    """

    width = page.page_geometry.width
    height = page.page_geometry.height

    def covers_page(bbox: tuple[float, float, float, float]) -> bool:
        """Un fondo di pagina non interrompe mai un corridoio.

        Regola gia' ratificata nel repo: `State.md` la scrive in questi termini
        -- «il corridoio e' interrotto da testo che lo attraversa o da un
        `embedded_visual` che lo attraversa; un `page_covering_visual` non lo
        interrompe mai» -- e registra la trappola con le stesse coordinate che si
        sono ripresentate qui: su DB pagina 76 il primo bloccante e'
        `(-8, -8, 613, 799)`, il fondo, che occupa ogni bin di ogni banda e
        annulla l'estensione.
        """

        return (bbox[2] - bbox[0]) >= width * 0.9 and (bbox[3] - bbox[1]) >= height * 0.9

    def holds_text(bbox: tuple[float, float, float, float]) -> bool:
        """Dentro questo visivo vive del testo: allora non e' un ostacolo.

        Discriminante gia' misurato nel repo — `State.md`: «il discriminante
        misurato e' il testo che vive dentro il bbox — chiusure di riquadro 0,
        fondi 21-63». Un fregio con sopra il titolo, o un fondino sotto una riga,
        non spinge via il testo: ci sta sotto. Un'illustrazione no.

        Serve perche' su DB pagina 76 il fregio `ARMI DA MISCHIA` sta dietro la
        riga d'intestazione e bloccava tutti e otto i gutter: la banda
        `POR- DURA- DISPO-` restava fuori dalla regione pur non toccando nulla.
        """

        return any(
            bbox[0] <= (p.bbox[0] + p.bbox[2]) / 2.0 <= bbox[2]
            and bbox[1] <= (p.bbox[1] + p.bbox[3]) / 2.0 <= bbox[3]
            for p in page.text_primitives
            if p.text.strip()
        )

    images = [
        tuple(float(v) for v in p.bbox)
        for p in page.image_primitives
        if not covers_page(tuple(float(v) for v in p.bbox))
        and not holds_text(tuple(float(v) for v in p.bbox))
    ]
    # I frammenti di uno stesso fregio vanno raggruppati prima di chiedersi se ci
    # vive del testo: presi uno per uno, i pezzi laterali non contengono il
    # titolo, che sta in mezzo, e restano bloccanti.
    #
    # Il raggruppamento lo fa `embedded_visual`, producer wired da Milestone 27,
    # che usa il clustering di Milestone 26. Una fusione locale scritta qui e'
    # stata provata e non basta: i due pezzi del fregio di DB pagina 76 non si
    # toccano fra loro e fra `x261` e `x352` non c'e' nessun frammento che faccia
    # da ponte -- li' c'e' solo il testo del titolo.
    def embedded_visuals() -> list[tuple[float, float, float, float]]:
        from page_analysis_embedded_visual import build_embedded_visual_page_analysis

        try:
            analysis = build_embedded_visual_page_analysis(
                page, generation_id="table-gutter-extension"
            )
        except Exception:
            return []
        return [tuple(float(v) for v in c.bbox) for c in analysis.candidates]

    lively = {box for box in embedded_visuals() if holds_text(box)}

    def in_lively_cluster(box: tuple[float, float, float, float]) -> bool:
        """Il frammento tocca un visivo che porta testo: stesso arredo, non blocca.

        Il test e' la SOVRAPPOSIZIONE, non il contenimento: `embedded_visual` non
        fonde il fregio in un candidato solo, e i pezzi laterali sporgono da
        quello che contiene il titolo. Su DB pagina 76 il candidato
        `(229.8, 50.9, 383.8, 90.9)` porta `ARMI DA MISCHIA`, e i due pezzi a
        `x181-261` e `x352-432` lo toccano senza starci dentro.

        E' `positive_intersection`, la regola senza soglia gia' ratificata in
        Milestone 20.
        """

        return any(
            box[0] < c[2] and box[2] > c[0] and box[1] < c[3] and box[3] > c[1]
            for c in lively
        )

    out = [box for box in images if not in_lively_cluster(box)]
    for drawing in page.drawing_primitives:
        box = tuple(float(v) for v in drawing.bbox)
        if covers_page(box) or holds_text(box) or in_lively_cluster(box):
            continue
        x0, y0, x1, y1 = drawing.bbox
        width, height = x1 - x0, y1 - y0
        if width <= 0 or height <= 0:
            continue
        if width / height >= THIN_RULE_RATIO or height / width >= THIN_RULE_RATIO:
            continue  # filetto: non blocca
        out.append((x0, y0, x1, y1))
    return out  # type: ignore[return-value]


def _mark(row: bytearray, x0: float, x1: float, width: float, bins: int) -> None:
    a, b = max(0.0, x0), min(width, x1)
    if b <= a:
        return
    for i in range(int(a / BIN), min(bins - 1, int(b / BIN)) + 1):
        row[i] = 1


def analyse(page: NormalizedPrimitivePage) -> list[dict[str, object]]:
    bands = _row_bands(page)
    if len(bands) < MIN_BANDS:
        return []
    width = page.page_geometry.width
    bins = int(width / BIN) + 1

    text_occ: list[bytearray] = []
    spans: list[tuple[float, float]] = []
    for band in bands:
        row = bytearray(bins)
        lo, hi = width, 0.0
        for line in band:
            for primitive in line.primitives:
                _mark(row, primitive.bbox[0], primitive.bbox[2], width, bins)
                lo = min(lo, primitive.bbox[0])
                hi = max(hi, primitive.bbox[2])
        text_occ.append(row)
        spans.append((lo, hi))

    blockers = _blockers(page)
    blocked: list[bytearray] = []
    for band in bands:
        top = min(min(p.bbox[1] for p in line.primitives) for line in band)
        bottom = max(max(p.bbox[3] for p in line.primitives) for line in band)
        row = bytearray(bins)
        for bx0, by0, bx1, by1 in blockers:
            if by1 <= top or by0 >= bottom:
                continue
            _mark(row, bx0, bx1, width, bins)
        blocked.append(row)

    # L'estensione x entro cui cercare i corridoi e' quella del SEME, non della
    # pagina: fuori dal seme stanno la linguetta di capitolo, il numero di pagina
    # e la filigrana, e con gli estremi di pagina il MARGINE diventava un
    # corridoio interno -- la causa vista sui render di BoB pagina 239
    # (`x395-414`, fino alla linguetta `227`) e Lan pagina 52 (`x48-59`, fino a
    # `[50]`).

    def corridors(free: bytearray, body_x0: float, body_x1: float) -> list[tuple[int, int]]:
        found: list[tuple[int, int]] = []
        start = None
        for i in range(bins + 1):
            open_here = i < bins and free[i] and body_x0 < i * BIN < body_x1
            if open_here and start is None:
                start = i
            elif not open_here and start is not None:
                if (i - start) * BIN >= MIN_GUTTER:
                    found.append((start, i))
                start = None
        return found

    results: list[dict[str, object]] = []
    for seed in range(len(bands)):
        # I gutter si identificano su un seme MINIMO e poi si estendono: e' la
        # formulazione dell'utente («una volta identificati i gutter, estendili
        # finche'...»).
        #
        # Prima il seme cresceva finche' sopravviveva un corridoio qualsiasi, e
        # solo dopo si leggevano i gutter -- quindi le due regole di estensione
        # giravano su un insieme gia' rovinato. Misurato su DB pagina 76: gli
        # otto corridoi sopravvivono a tutte e 41 le bande della tabella e
        # collassano a quattro alla banda 43, `CAPITOLO 6 - ATTREZZATURA`, cioe'
        # il PIEDE DI PAGINA, che la corsa aveva gia' inghiottito.
        end = seed + MIN_BANDS
        if end > len(bands):
            continue
        free = bytearray(1 if not text_occ[seed][i] else 0 for i in range(bins))
        lo, hi = spans[seed]
        for band in range(seed + 1, end):
            free = bytearray(1 if free[i] and not text_occ[band][i] else 0 for i in range(bins))
            lo, hi = min(lo, spans[band][0]), max(hi, spans[band][1])
        gutters = corridors(free, lo, hi)
        # Un gutter sta FRA DUE COLONNE: deve avere testo da entrambi i lati
        # nella stessa banda, almeno una volta. Un margine ne ha da un lato solo.
        #
        # Serve perche' il corpo si misura sul testo, e una banda che contiene
        # solo l'arredo di bordo lo allarga: su BoB pagina 239 la linguetta `227`
        # e' testo, sta in una banda sua, e porta il bordo destro del corpo da
        # 394 a 432 -- il margine `395-414` diventava un corridoio interno ed era
        # l'unico gutter emesso. Su DB pagina 76 non succede, e la differenza fra
        # le due pagine e' proprio questa: rilievo dell'utente.
        gutters = [
            (x0, x1)
            for x0, x1 in gutters
            if any(
                any(text_occ[band][k] for k in range(0, x0))
                and any(text_occ[band][k] for k in range(x1, bins))
                for band in range(seed, end)
            )
        ]
        if not gutters:
            continue

        # distanza a cui di solito si trova il testo, misurata sul seme
        # Le CELLE: gli intervalli fra due gutter consecutivi, con i BORDI della
        # tabella come gutter esterni. Sostituisce la «distanza a cui di solito
        # si trova il testo», che era una mediana e quindi un parametro:
        # chiedere se una cella contiene testo e' geometrico e non ha soglie.
        # Indicazione dell'utente, che nota anche la conseguenza: i bordi vanno
        # trattati come gutter, altrimenti la prima e l'ultima colonna non hanno
        # cella.
        edges = [int(lo / BIN)] + [g[1] for g in gutters]
        rights = [g[0] for g in gutters] + [int(hi / BIN) + 1]
        cells = [(a, b) for a, b in zip(edges, rights, strict=False) if b > a]

        # Il gutter si RESTRINGE per adattarsi allo spazio, non spezza la
        # regione: «se vedi che viene interrotto prova una linea piu' piccola;
        # se non puoi allungarlo o restringerlo, non crearne un altro nella
        # stessa tabella». Indicazione dell'utente.
        #
        # Serve perche' il corridoio del seme e' largo quanto lo lascia
        # l'intestazione -- `149-164` su DB pagina 76, dove `ARMA` e' corta -- e
        # nel corpo `IM` ne tocca il bordo per UN punto. Chiedendo tutto il
        # corridoio libero la regione si spezzava in tre tronconi.
        #
        # Un primo tentativo col restringimento era stato ritirato, ma la causa
        # non era il restringimento: era il SEME. Preso il primo disponibile,
        # partiva dal titolo `ARMI DA MISCHIA`, i cui corridoi sono larghissimi
        # (`146-243`, `369-432`) e sopravvivono a tutta la pagina. Ora il seme e'
        # quello che da' PIU' colonne, che sulla stessa pagina e' la tabella.
        live = [bytearray(1 for _ in range(x1 - x0)) for x0, x1 in gutters]

        def admits(
            band: int,
            gutters: Sequence[tuple[int, int]] = gutters,
            cells: Sequence[tuple[int, int]] = cells,
            live: list[bytearray] = live,
        ) -> bool:
            trial = []
            for index, (x0, x1) in enumerate(gutters):
                mask = bytearray(
                    1
                    if live[index][k]
                    and not (text_occ[band][x0 + k] or blocked[band][x0 + k])
                    else 0
                    for k in range(x1 - x0)
                )
                if not any(mask):
                    return False
                trial.append(mask)
            if not any(
                any(text_occ[band][k] for k in range(max(0, a), min(bins, b)))
                for a, b in cells
            ):
                return False
            for index, mask in enumerate(trial):
                live[index] = mask
            return True

        b0, b1 = seed, end
        while b1 < len(bands) and admits(b1):
            b1 += 1
        live[:] = [bytearray(1 for _ in range(x1 - x0)) for x0, x1 in gutters]
        while b0 > 0 and admits(b0 - 1):
            b0 -= 1
        if b1 - b0 < MIN_BANDS:
            continue
        # Il restringimento va ricalcolato sull'intervallo FINALE. Le due passate
        # -- in giu' e in su -- azzerano la maschera l'una dell'altra, quindi il
        # gutter emesso rifletteva solo l'ultima: su DB pagina 76 usciva
        # `113-164`, cioe' la larghezza che ha nella sola banda d'intestazione,
        # e con confini cosi' larghi 17 righe restavano a cavallo.
        narrowed = []
        for x0, x1 in gutters:
            mask = bytearray(1 for _ in range(x1 - x0))
            for band in range(b0, b1):
                for k in range(x1 - x0):
                    if text_occ[band][x0 + k] or blocked[band][x0 + k]:
                        mask[k] = 0
            if not any(mask):
                continue
            first = next(k for k in range(len(mask)) if mask[k])
            last = next(k for k in range(len(mask) - 1, -1, -1) if mask[k])
            narrowed.append((x0 + first, x0 + last + 1))
        if not narrowed:
            continue
        gutters = narrowed

        members = [line for band in bands[b0:b1] for line in band]
        results.append(
            {
                "bands": (b0, b1),
                "cells": len(cells),
                "gutters": [(x0 * BIN, x1 * BIN) for x0, x1 in gutters],
                "bbox": (
                    min(min(p.bbox[0] for p in line.primitives) for line in members),
                    min(min(p.bbox[1] for p in line.primitives) for line in members),
                    max(max(p.bbox[2] for p in line.primitives) for line in members),
                    max(max(p.bbox[3] for p in line.primitives) for line in members),
                ),
            }
        )
    # Ogni seme che ricade nella stessa tabella produce la stessa regione: si
    # tiene la piu' lunga e si scartano quelle che vi si sovrappongono. La
    # sovrapposizione e' `positive_intersection` sulle bande, la regola senza
    # soglia gia' ratificata dal repo in Milestone 20.
    # Si tiene il seme che da' PIU' colonne, poi il piu' esteso: su una pagina
    # con una tabella il seme del titolo ne da' due, quello della tabella nove.
    results.sort(
        key=lambda r: (-len(r["gutters"]), r["bands"][0] - r["bands"][1])  # type: ignore[index,arg-type]
    )
    kept: list[dict[str, object]] = []
    for result in results:
        b0, b1 = result["bands"]  # type: ignore[misc]
        if any(b0 < k["bands"][1] and b1 > k["bands"][0] for k in kept):  # type: ignore[index]
            continue
        kept.append(result)
    kept.sort(key=lambda r: r["bands"][0])  # type: ignore[index]
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True)
    parser.add_argument("--outdir", type=Path, help="se dato, rende ogni pagina")
    args = parser.parse_args()

    for spec in args.pages:
        name, raw = spec.split(":")
        index = int(raw)
        document = fitz.open(args.pdf_dir / f"{name}.pdf")
        page = document[index]
        capture = capture_pymupdf_page(
            page,
            source_id="gutter-extension",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"ext:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        print(f"\n### {name} idx {index} (pagina file {index + 1})")
        for result in analyse(primitive_page):
            b0, b1 = result["bands"]  # type: ignore[misc]
            x0, y0, x1, y1 = result["bbox"]  # type: ignore[misc]
            gutters = result["gutters"]  # type: ignore[assignment]
            print(
                f"   bande {b0}-{b1}  y {y0:6.1f}-{y1:6.1f}  x {x0:6.1f}-{x1:6.1f}  "
                f"colonne={result['cells']}"
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
