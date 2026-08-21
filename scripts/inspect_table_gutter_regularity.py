"""Descrive una pagina con i suoi CORRIDOI VERTICALI, e ne misura la regolarita'.

Osservazione dell'utente da cui nasce: nelle tabelle vere si vedono sempre dei
gutter verticali che fanno le colonne -- sottili magari, ma **molto regolari** --
e dove la tabella e' tracciata (Wil) quei gutter esistono lo stesso se si
considerano i filetti verticali come gutter gia' disegnati.

Questo script non decide niente e non e' un producer. Descrive: per ogni pagina
elenca i corridoi verticali -- di bianco fra il testo, e di inchiostro quando un
filetto verticale li disegna -- con la loro **estensione verticale in bande di
riga**, e li raggruppa per estensione.

La grandezza che interessa e' il RAGGRUPPAMENTO: i gutter di una tabella
cominciano e finiscono insieme, perche' delimitano le stesse righe; un corridoio
di prosa fra due colonne di testo corre per conto suo. Se l'osservazione regge, in
una pagina con una tabella si vede un gruppo di piu' corridoi con la stessa
estensione, e in una pagina di prosa no.

Read-only. Uso:

    ./venv/bin/python scripts/inspect_table_gutter_regularity.py --pdf-dir . \
        --pages DB:75 Lan:18 Wil:77
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


def _row_bands(page: NormalizedPrimitivePage) -> list[list[_SourceLine]]:
    lines = group_source_lines([p for p in page.text_primitives if p.text.strip()])
    if not lines:
        return []
    ordered = sorted(lines, key=lambda line: min(p.bbox[1] for p in line.primitives))
    bands = [[ordered[0]]]
    anchor = max(p.bbox[3] for p in ordered[0].primitives)
    for line in ordered[1:]:
        if min(p.bbox[1] for p in line.primitives) < anchor - 1.0:
            bands[-1].append(line)
        else:
            bands.append([line])
            anchor = max(p.bbox[3] for p in line.primitives)
    return bands


def _band_extent(band: Sequence[_SourceLine]) -> tuple[float, float, float, float]:
    xs0 = min(min(p.bbox[0] for p in line.primitives) for line in band)
    xs1 = max(max(p.bbox[2] for p in line.primitives) for line in band)
    ys0 = min(min(p.bbox[1] for p in line.primitives) for line in band)
    ys1 = max(max(p.bbox[3] for p in line.primitives) for line in band)
    return xs0, ys0, xs1, ys1


def _vertical_rules(
    page: NormalizedPrimitivePage, *, min_ratio: float = 4.0, merge_gap: float = 6.0
) -> list[tuple[float, float, float, int]]:
    """I filetti verticali, FUSI per x: un gutter gia' disegnato.

    Vanno fusi perche' arrivano a segmenti: su Lan idx 18 lo stesso confine di
    colonna a `x88,7` compare come 13 filetti alti una riga ciascuno, uno per
    riga di tabella. Presi singolarmente non sono un gutter; fusi lo sono, e
    l'estensione verticale che ne risulta e' quella della tabella.

    Ritorna (x, y0, y1, quanti_segmenti).
    """

    segments: list[tuple[float, float, float]] = []
    for drawing in page.drawing_primitives:
        x0, y0, x1, y1 = drawing.bbox
        width, height = x1 - x0, y1 - y0
        if height <= 0.0 or width > height / min_ratio:
            continue
        segments.append(((x0 + x1) / 2.0, y0, y1))

    merged: list[tuple[float, float, float, int]] = []
    for x, y0, y1 in sorted(segments):
        for index, (mx, my0, my1, count) in enumerate(merged):
            if abs(mx - x) <= 1.0 and y0 <= my1 + merge_gap and y1 >= my0 - merge_gap:
                merged[index] = (mx, min(my0, y0), max(my1, y1), count + 1)
                break
        else:
            merged.append((x, y0, y1, 1))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True, help="Nome:idx0based")
    parser.add_argument("--min-bands", type=int, default=3)
    parser.add_argument("--min-width", type=float, default=2.0)
    args = parser.parse_args()

    for spec in args.pages:
        name, raw = spec.split(":")
        index = int(raw)
        document = fitz.open(args.pdf_dir / f"{name}.pdf")
        page = document[index]
        capture = capture_pymupdf_page(
            page,
            source_id="gutter-regularity",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"gutter:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        bands = _row_bands(primitive_page)
        print(f"\n### {name} idx {index} (pagina file {index + 1}) — {len(bands)} bande di riga")
        if len(bands) < args.min_bands:
            print("   troppe poche bande")
            continue

        width = primitive_page.page_geometry.width
        bin_count = int(width / BIN) + 1
        occ: list[bytearray] = []
        for band in bands:
            row = bytearray(bin_count)
            for line in band:
                for primitive in line.primitives:
                    a = max(0.0, primitive.bbox[0])
                    b = min(width, primitive.bbox[2])
                    if b <= a:
                        continue
                    for i in range(int(a / BIN), min(bin_count - 1, int(b / BIN)) + 1):
                        row[i] = 1
            occ.append(row)

        # per ogni bin, le corse verticali libere DENTRO l'inchiostro della banda
        extents = [_band_extent(band) for band in bands]
        # Il corridoio si misura dentro l'inchiostro della PAGINA, non di ogni
        # singola banda. Una riga di continuazione non ha testo nella colonna
        # delle etichette, quindi l'inchiostro della sua banda comincia a destra
        # del gutter: col test per banda quella riga dichiarava il corridoio
        # "fuori" e SPEZZAVA la corsa a meta' tabella -- BoB pagina 239 dava 4
        # bande su 7, DB pagina 62 dieci su venti. Una riga che a quella x non ha
        # testo non contraddice il corridoio: lo lascia libero.
        page_x0 = min(e[0] for e in extents)
        page_x1 = max(e[2] for e in extents)
        runs: dict[tuple[int, int], list[int]] = {}
        for i in range(bin_count):
            start = None
            for b in range(len(bands)):
                inside = page_x0 < i * BIN < page_x1
                free = inside and not occ[b][i]
                if free and start is None:
                    start = b
                elif not free and start is not None:
                    if b - start >= args.min_bands:
                        runs.setdefault((start, b), []).append(i)
                    start = None
            if start is not None and len(bands) - start >= args.min_bands:
                runs.setdefault((start, len(bands)), []).append(i)

        groups: dict[tuple[int, int], list[tuple[float, float]]] = {}
        for (b0, b1), bins in runs.items():
            bins.sort()
            run_start = bins[0]
            previous = bins[0]
            for value in bins[1:] + [None]:  # type: ignore[list-item]
                if value is not None and value == previous + 1:
                    previous = value
                    continue
                if (previous - run_start + 1) * BIN >= args.min_width:
                    groups.setdefault((b0, b1), []).append(
                        (run_start * BIN, (previous + 1) * BIN)
                    )
                if value is not None:
                    run_start = previous = value

        ordered = sorted(groups.items(), key=lambda item: -(item[0][1] - item[0][0]))
        for (b0, b1), corridors in ordered[:8]:
            y0 = extents[b0][1]
            y1 = extents[b1 - 1][3]
            marker = "  <-- gruppo" if len(corridors) >= 2 else ""
            print(
                f"   bande {b0:3d}-{b1:3d} ({b1 - b0:3d})  y {y0:6.1f}-{y1:6.1f}  "
                f"{len(corridors)} corridoi: "
                f"{[f'{a:.0f}-{b:.0f}' for a, b in corridors][:9]}{marker}"
            )

        rules = [r for r in _vertical_rules(primitive_page) if r[2] - r[1] >= 20.0]
        if rules:
            by_extent: dict[tuple[int, int], list[float]] = {}
            for x, y0, y1, _count in rules:
                by_extent.setdefault((round(y0), round(y1)), []).append(x)
            print(f"   filetti verticali fusi (gutter gia' disegnati): {len(rules)}")
            for (y0, y1), xs in sorted(by_extent.items(), key=lambda i: -(i[0][1] - i[0][0]))[:4]:
                marker = "  <-- gruppo" if len(xs) >= 2 else ""
                print(f"      y {y0:5d}-{y1:5d}  {len(xs)} filetti a x "
                      f"{[f'{x:.0f}' for x in sorted(xs)][:10]}{marker}")


if __name__ == "__main__":
    main()
