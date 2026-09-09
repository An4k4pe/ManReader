"""Le tre varianti del criterio di fianco a confronto. Criterio pre-registrato in
`Criterio_SommaCaratteriFianco_v1.md`.

Diagnostica: `page_analysis_column_band.py` NON viene toccato. Le varianti si
calcolano ricomponendo la decisione sopra il profilo che il producer misura, cosi'
il confronto e' fra regole e non fra implementazioni.

  V0  oggi:    scarta se meno di 2 righe per lato portano >= 5 caratteri
  V1  somma:   scarta se il lato piu' povero somma < 5 caratteri
  V2  mista:   V1 dentro un `table_candidate`, V0 fuori

La partizione dei fianchi (quali righe stanno a sinistra, quali a destra, quali
ruotate) e' copiata alla lettera da `_flanking_profile`: se divergesse, il
confronto non varrebbe niente.

Uso:  python3 scripts/compare_flanking_char_sum.py <file.pdf> [--pagine N]
      python3 scripts/compare_flanking_char_sum.py <file.pdf> --pagina N
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
for candidate_dir in [PROJECT_ROOT, *PROJECT_ROOT.parents]:
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import pdfplumber  # noqa: E402
import pymupdf  # noqa: E402
from scan_missing_column_bands import _numero_stampato, _tabelle_di  # noqa: E402

from page_analysis_column_band import (  # noqa: E402
    _DEFAULT_BIN_HEIGHT_Y,
    _DEFAULT_BIN_WIDTH_X,
    _DEFAULT_MIN_FLANKING_CHARS,
    _DEFAULT_MIN_FLANKING_GROUPS,
    _DEFAULT_MIN_GUTTER_LINES,
    _build_gap_grid,
    _chain_gutters,
    _extend_gutter_span,
    _flanking_profile,
    _group_by_pymupdf_line,
    _median_line_height,
    _reject_reason,
    _rotated_group_ids,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

SOGLIA_SOMMA = float(_DEFAULT_MIN_FLANKING_CHARS)


def somme_di_fianco(groups, rect, *, bin_width_x, rotated_groups, text_length_by_id):
    """I caratteri SOMMATI per lato. Partizione copiata da `_flanking_profile`."""
    gutter_x0 = rect.x_bin_start * bin_width_x
    gutter_x1 = (rect.x_bin_end + 1) * bin_width_x
    sinistra: list[int] = []
    destra: list[int] = []
    for group in groups:
        if group.y1 <= rect.y0 or group.y0 >= rect.y1:
            continue
        group_x0 = min(bbox[0] for bbox in group.bboxes)
        group_x1 = max(bbox[2] for bbox in group.bboxes)
        if (group.block_index, group.line_index) in rotated_groups:
            continue
        caratteri = sum(text_length_by_id.get(i, 0) for i in group.primitive_ids)
        if group_x1 <= gutter_x0:
            sinistra.append(caratteri)
        elif group_x0 >= gutter_x1:
            destra.append(caratteri)
    return sum(sinistra), sum(destra), sinistra, destra


def esamina(primitive_page, tabelle):
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    groups, _ = _group_by_pymupdf_line(
        list(primitive_page.text_primitives), page_width=page_width, page_height=page_height
    )
    if not groups:
        return []
    grid, _n_x, _n_y = _build_gap_grid(
        groups, page_width=page_width, page_height=page_height,
        bin_width_x=_DEFAULT_BIN_WIDTH_X, bin_height_y=_DEFAULT_BIN_HEIGHT_Y,
    )
    rects = _chain_gutters(grid, bin_height_y=_DEFAULT_BIN_HEIGHT_Y)
    for rect in rects:
        _extend_gutter_span(grid, rect, bin_height_y=_DEFAULT_BIN_HEIGHT_Y)
    rotated = _rotated_group_ids(groups, list(primitive_page.text_primitives))
    lunghezze = {
        p.primitive_id: len((p.text or "").strip()) for p in primitive_page.text_primitives
    }
    altezza = _median_line_height(groups)

    fuori = []
    for rect in rects:
        profilo = _flanking_profile(
            groups, rect, bin_width_x=_DEFAULT_BIN_WIDTH_X, rotated_groups=rotated,
            text_length_by_id=lunghezze, min_chars=_DEFAULT_MIN_FLANKING_CHARS,
        )
        motivo = _reject_reason(
            profilo, rect, line_height=altezza,
            min_flanking_groups=_DEFAULT_MIN_FLANKING_GROUPS,
            min_gutter_lines=_DEFAULT_MIN_GUTTER_LINES,
        )
        somma_sx, somma_dx, righe_sx, righe_dx = somme_di_fianco(
            groups, rect, bin_width_x=_DEFAULT_BIN_WIDTH_X, rotated_groups=rotated,
            text_length_by_id=lunghezze,
        )
        x0 = rect.x_bin_start * _DEFAULT_BIN_WIDTH_X
        x1 = rect.x_bin_end * _DEFAULT_BIN_WIDTH_X
        in_tabella = any(
            t[0] <= x0 and t[2] >= x1 and t[1] <= rect.y1 and t[3] >= rect.y0 for t in tabelle
        )
        # Gli altri due criteri restano quelli del producer: la variante tocca
        # SOLO `too_few_wordy_lines`. Vanno pero' RICALCOLATI, non letti dal
        # motivo: `_reject_reason` si ferma al primo che scatta, quindi un
        # corridoio non-wordy E troppo basso riporta solo `too_few_wordy_lines`.
        # Leggendo il motivo, la variante lo avrebbe promosso ignorando
        # l'altezza -- difetto trovato misurando, corridoi da 0,75 righe
        # ammessi.
        poche_righe = profilo.minimum < _DEFAULT_MIN_FLANKING_GROUPS
        troppo_basso = altezza > 0 and (rect.y1 - rect.y0) < _DEFAULT_MIN_GUTTER_LINES * altezza
        altro_scarto = poche_righe or troppo_basso
        somma_ok = min(somma_sx, somma_dx) >= SOGLIA_SOMMA
        v0 = motivo is None
        v1 = (not altro_scarto) and somma_ok
        v2 = v1 if in_tabella else v0
        # V3: nessuna soglia, solo «il lato non e' vuoto». I dati dicono che i
        # due gruppi si distinguono per SE sommano, non per quanto.
        v3 = (not altro_scarto) and min(somma_sx, somma_dx) > 0
        # V4: la somma non vuota vale SOLO dentro una tabella. Fuori resta V0,
        # perche' i punti elenco di Apo sommano 2-4 come la colonna D6 della
        # FORESTA: sul solo profilo del corridoio le due classi non si separano.
        v4 = v3 if in_tabella else v0
        fuori.append({
            "x": (x0, x1), "y": (rect.y0, rect.y1),
            "righe": (rect.y1 - rect.y0) / altezza if altezza else 0.0,
            "motivo": motivo, "in_tabella": in_tabella,
            "somma": (somma_sx, somma_dx), "fianchi": (len(righe_sx), len(righe_dx)),
            "V0": v0, "V1": v1, "V2": v2, "V3": v3, "V4": v4,
        })
    return fuori


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pagina", type=int, default=None, help="indice posizionale singolo")
    parser.add_argument("--tutte", action="store_true")
    parser.add_argument("--elenco-v3", action="store_true",
                        help="elenca i corridoi che V3 apre e V0 no, fuori dalle tabelle")
    parser.add_argument("--da", type=int, default=0)
    parser.add_argument("--a", type=int, default=10**6)
    args = parser.parse_args(argv)

    with pymupdf.open(args.pdf) as documento, pdfplumber.open(args.pdf) as plumber:
        indici = (
            [args.pagina]
            if args.pagina is not None
            else list(range(args.da, min(args.a + 1, documento.page_count)))
        )
        conta = Counter()
        nuovi: list[tuple[int, dict]] = []
        nuovi_v3: list[tuple[int, str, dict]] = []
        for indice in indici:
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    documento.load_page(indice), source_id="v1",
                    page_id=f"page:{indice + 1:04d}", capture_id=f"v1:{indice}",
                )
            )
            tabelle = _tabelle_di(primitive_page, plumber.pages[indice], f"g{indice}")
            stampata = _numero_stampato(documento.load_page(indice))
            for corridoio in esamina(primitive_page, tabelle):
                conta["corridoi"] += 1
                conta["V0"] += 1 if corridoio["V0"] else 0
                conta["V1"] += 1 if corridoio["V1"] else 0
                conta["V2"] += 1 if corridoio["V2"] else 0
                conta["V3"] += 1 if corridoio["V3"] else 0
                conta["V4"] += 1 if corridoio["V4"] else 0
                if corridoio["V4"] and not corridoio["V0"]:
                    conta["nuovi_V4_in_tabella" if corridoio["in_tabella"]
                          else "nuovi_V4_fuori_tabella"] += 1
                if corridoio["V3"] and not corridoio["V0"]:
                    conta["nuovi_V3_in_tabella" if corridoio["in_tabella"]
                          else "nuovi_V3_fuori_tabella"] += 1
                    if not corridoio["in_tabella"]:
                        nuovi_v3.append((indice, stampata, corridoio))
                if corridoio["V1"] and not corridoio["V0"]:
                    conta["nuovi_V1_in_tabella" if corridoio["in_tabella"]
                          else "nuovi_V1_fuori_tabella"] += 1
                    nuovi.append((indice, corridoio))
                if args.pagina is not None:
                    print(f"   x {corridoio['x'][0]:6.1f}-{corridoio['x'][1]:6.1f} "
                          f"{corridoio['righe']:5.2f} righe  "
                          f"fianchi {corridoio['fianchi']}  somma {corridoio['somma']}  "
                          f"{'tab' if corridoio['in_tabella'] else '  -'}  "
                          f"V0={'si' if corridoio['V0'] else 'NO'} "
                          f"V1={'si' if corridoio['V1'] else 'NO'} "
                          f"V2={'si' if corridoio['V2'] else 'NO'} "
                          f"V3={'si' if corridoio['V3'] else 'NO'} "
                          f"V4={'si' if corridoio['V4'] else 'NO'}  ({corridoio['motivo']})")

    if args.elenco_v3:
        print(f"\n== i {len(nuovi_v3)} corridoi che V3 apre FUORI da una tabella ==")
        print("   (V0 li scarta; sono quelli da guardare a vista)")
        for indice, stampata, corridoio in sorted(nuovi_v3, key=lambda t: -t[2]["righe"]):
            print(f"   indice {indice:4d} (stampata {stampata:>4}): "
                  f"x {corridoio['x'][0]:6.1f}-{corridoio['x'][1]:6.1f}  "
                  f"y {corridoio['y'][0]:6.1f}-{corridoio['y'][1]:6.1f}  "
                  f"{corridoio['righe']:5.2f} righe  "
                  f"fianchi {corridoio['fianchi']}  somma {corridoio['somma']}")
        return 0

    if args.pagina is None:
        print(f"file: {args.pdf.name}   pagine: {len(indici)}   corridoi: {conta['corridoi']}")
        print(f"   ammessi V0 {conta['V0']}   V1 {conta['V1']}   V2 {conta['V2']}   "
              f"V3 {conta['V3']}   V4 {conta['V4']}")
        print(f"   nuovi con V4: {conta['nuovi_V4_in_tabella']} dentro una tabella, "
              f"{conta['nuovi_V4_fuori_tabella']} fuori")
        print(f"   nuovi con V3: {conta['nuovi_V3_in_tabella']} dentro una tabella, "
              f"{conta['nuovi_V3_fuori_tabella']} fuori")
        print(f"   nuovi con V1: {conta['nuovi_V1_in_tabella']} dentro una tabella, "
              f"{conta['nuovi_V1_fuori_tabella']} fuori")
        fuori_tabella = [t for t in nuovi if not t[1]["in_tabella"]]
        print(f"   i {len(fuori_tabella)} nuovi FUORI da una tabella (il rischio di V1):")
        for indice, corridoio in sorted(fuori_tabella, key=lambda t: -t[1]["righe"]):
            print(f"      indice {indice:4d}: x {corridoio['x'][0]:6.1f}-{corridoio['x'][1]:6.1f} "
                  f"{corridoio['righe']:5.2f} righe  fianchi {corridoio['fianchi']}  "
                  f"somma {corridoio['somma']}")
        print("   i nuovi piu' alti:")
        for indice, corridoio in sorted(nuovi, key=lambda t: -t[1]["righe"])[:6]:
            print(f"      indice {indice:4d}: x {corridoio['x'][0]:6.1f}-{corridoio['x'][1]:6.1f} "
                  f"{corridoio['righe']:5.2f} righe  somma {corridoio['somma']}  "
                  f"{'in tabella' if corridoio['in_tabella'] else '   fuori  '}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
