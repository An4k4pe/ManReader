"""Milestone 42, diagnostica: perche' `column_band` non emette bande.

Criterio pre-registrato in `Criterio_BandeMancanti_v1.md`. Diagnostica pura:
nessun producer, nessuna soglia toccata, nessun `RegionCandidate`, nessun
wiring. Stesso perimetro di Milestone 25, 29 e 32.

Il fatto che la apre non viene da qui: Milestone 38 registra «6 pagine su 10 non
producono bande» sul suo campione cieco, e il giro Markdown del 6 settembre 2026
misura 14 pagine su 47 senza bande sul Dragonbane Quickstart, con l'ordine di
lettura che su quelle pagine degrada a `y` e interlaccia le colonne.

Lo script ripercorre il corpo di `column_band_tree` **importando invariate** le
funzioni del producer, e si ferma un passo prima dell'albero: dice quanti
corridoi verticali vengono incatenati, quanti sono ammessi, e per gli scartati
il motivo di ognuno. Per le pagine che finiscono con zero bande riporta il
corridoio scartato piu' alto -- il miglior candidato a essere la colonna -- con
il suo motivo, la sua x, la sua altezza in righe di pagina e il profilo dei
fianchi.

Uso:
    python3 scripts/scan_missing_column_bands.py <file.pdf> [--pagine N --seed S]
    python3 scripts/scan_missing_column_bands.py <file.pdf> --tutte
"""

from __future__ import annotations

import argparse
import random
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

import pymupdf  # noqa: E402

from page_analysis_column_band import (  # noqa: E402
    _DEFAULT_BIN_HEIGHT_Y,
    _DEFAULT_BIN_WIDTH_X,
    _DEFAULT_MIN_COLUMN_CHARS,
    _DEFAULT_MIN_FLANKING_CHARS,
    _DEFAULT_MIN_FLANKING_GROUPS,
    _DEFAULT_MIN_GUTTER_LINES,
    _build_gap_grid,
    _chain_gutters,
    _extend_gutter_span,
    _flanking_profile,
    _group_by_pymupdf_line,
    _median_font_size,
    _median_line_height,
    _reject_reason,
    _rotated_group_ids,
    _segment_tree,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def esamina_pagina(primitive_page) -> dict:
    """Il corpo di `column_band_tree`, fermato ai motivi di scarto.

    Ogni passo e' la funzione di produzione, importata e non riscritta: se
    questa diagnostica e il producer divergessero, il verbale non varrebbe."""
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    groups, _unparsed = _group_by_pymupdf_line(
        list(primitive_page.text_primitives), page_width=page_width, page_height=page_height
    )
    if not groups:
        return {"righe": 0, "corridoi": 0, "ammessi": 0, "motivi": Counter(), "bande": 0,
                "peggiore": None, "senza_testo": True}

    grid, _n_x, _n_y = _build_gap_grid(
        groups,
        page_width=page_width,
        page_height=page_height,
        bin_width_x=_DEFAULT_BIN_WIDTH_X,
        bin_height_y=_DEFAULT_BIN_HEIGHT_Y,
    )
    rects = _chain_gutters(grid, bin_height_y=_DEFAULT_BIN_HEIGHT_Y)
    for rect in rects:
        _extend_gutter_span(grid, rect, bin_height_y=_DEFAULT_BIN_HEIGHT_Y)
    rects.sort(key=lambda r: (r.y1 - r.y0), reverse=True)

    rotated = _rotated_group_ids(groups, list(primitive_page.text_primitives))
    lunghezze = {
        p.primitive_id: len((p.text or "").strip()) for p in primitive_page.text_primitives
    }
    altezza_riga = _median_line_height(groups)

    motivi: Counter[str] = Counter()
    ammessi = []
    peggiore = None
    for rect in rects:
        profilo = _flanking_profile(
            groups,
            rect,
            bin_width_x=_DEFAULT_BIN_WIDTH_X,
            rotated_groups=rotated,
            text_length_by_id=lunghezze,
            min_chars=_DEFAULT_MIN_FLANKING_CHARS,
        )
        motivo = _reject_reason(
            profilo,
            rect,
            line_height=altezza_riga,
            min_flanking_groups=_DEFAULT_MIN_FLANKING_GROUPS,
            min_gutter_lines=_DEFAULT_MIN_GUTTER_LINES,
        )
        if motivo is None:
            ammessi.append(rect)
            motivi["ammesso"] += 1
            continue
        motivi[motivo] += 1
        if peggiore is None:  # `rects` e' gia' ordinato per altezza decrescente
            peggiore = {
                "motivo": motivo,
                "x": (
                    round(rect.x_bin_start * _DEFAULT_BIN_WIDTH_X, 1),
                    round(rect.x_bin_end * _DEFAULT_BIN_WIDTH_X, 1),
                ),
                "altezza_pt": round(rect.y1 - rect.y0, 1),
                "altezza_righe": round((rect.y1 - rect.y0) / altezza_riga, 2)
                if altezza_riga
                else None,
                "righe_per_lato": profilo.minimum,
                "righe_con_parole": profilo.wordy_minimum,
            }

    albero_finale = _segment_tree(
        ammessi,
        bin_width_x=_DEFAULT_BIN_WIDTH_X,
        page_width=page_width,
        font_size=_median_font_size(list(primitive_page.text_primitives)),
        min_column_chars=_DEFAULT_MIN_COLUMN_CHARS,
    )
    # Fase 2: dove cade il testo che nessuna banda contiene. Le tre posizioni
    # sono quelle pre-registrate (K1 sopra/sotto, K2 fuori x, K3 fra due bande).
    riquadri = [
        (
            float(riga["x0"]),
            float(riga["y0"]),
            float(riga["x1"]),
            float(riga["y1"]),
        )
        for riga in albero_finale
    ]
    # Fase 3: una riga fuori banda fa danno solo se ha righe AFFIANCATE, cioe'
    # sovrapposte in y e disgiunte in x. Titoli, tabelle a tutta larghezza e
    # prosa a colonna unica stanno fuori dalle bande e per loro l'ordine per y
    # e' quello giusto.
    estensioni = [
        (min(b[0] for b in g.bboxes), g.y0, max(b[2] for b in g.bboxes), g.y1)
        for g in groups
    ]
    affiancata_di: dict[str, bool] = {}
    for indice, (gx0, gy0, gx1, gy1) in enumerate(estensioni):
        affiancata = any(
            altro != indice
            and estensioni[altro][1] < gy1
            and estensioni[altro][3] > gy0
            and (estensioni[altro][2] <= gx0 or estensioni[altro][0] >= gx1)
            for altro in range(len(estensioni))
        )
        for pid in groups[indice].primitive_ids:
            affiancata_di[pid] = affiancata

    posizioni: Counter[str] = Counter()
    classi: Counter[str] = Counter()
    for primitiva in primitive_page.text_primitives:
        cx = (primitiva.bbox[0] + primitiva.bbox[2]) / 2.0
        cy = (primitiva.bbox[1] + primitiva.bbox[3]) / 2.0
        if any(x0 <= cx < x1 and y0 <= cy < y1 for x0, y0, x1, y1 in riquadri):
            posizioni["dentro"] += 1
            continue
        classi[
            "affiancata" if affiancata_di.get(primitiva.primitive_id) else "sola"
        ] += 1
        if not riquadri:
            posizioni["nessuna_banda"] += 1
            continue
        alto = min(y0 for _x0, y0, _x1, _y1 in riquadri)
        basso = max(y1 for _x0, _y0, _x1, y1 in riquadri)
        if cy < alto:
            posizioni["sopra_la_prima"] += 1
        elif cy >= basso:
            posizioni["sotto_l_ultima"] += 1
        elif any(y0 <= cy < y1 for _x0, y0, _x1, y1 in riquadri):
            posizioni["fuori_x"] += 1
        else:
            posizioni["fra_due_bande"] += 1

    return {
        "righe": len(groups),
        "corridoi": len(rects),
        "ammessi": len(ammessi),
        "motivi": motivi,
        "bande": len(albero_finale),
        "peggiore": peggiore,
        "altezza_riga": round(altezza_riga, 2),
        "senza_testo": False,
        "posizioni": posizioni,
        "classi": classi,
        "primitive": len(primitive_page.text_primitives),
    }


def _numero_stampato(pagina) -> str:
    """Il numero di pagina STAMPATO, letto dai margini invece che dedotto.

    `CLAUDE.md`: l'indice posizionale non e' il numero stampato e lo scostamento
    non e' lineare. Qui si legge una riga fatta di sole cifre nei 90pt in alto o
    in basso; se non c'e', si dice `?` invece di indovinare."""
    altezza = pagina.rect.height
    candidati = []
    for blocco in pagina.get_text("dict")["blocks"]:
        for riga in blocco.get("lines", []):
            testo = "".join(s["text"] for s in riga["spans"]).strip()
            y = riga["bbox"][1]
            if testo.isdigit() and (y < 90 or y > altezza - 90):
                candidati.append(testo)
    return candidati[0] if len(set(candidati)) == 1 else (candidati[0] if candidati else "?")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pagine", type=int, default=20, help="quante pagine campionare")
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--tutte", action="store_true", help="tutte le pagine, niente campione")
    parser.add_argument("--dettaglio", type=int, default=8, help="quante pagine senza bande mostrare")
    args = parser.parse_args(argv)

    with pymupdf.open(args.pdf) as documento:
        totale = documento.page_count
        if args.tutte:
            indici = list(range(totale))
        else:
            generatore = random.Random(args.seed)
            indici = sorted(generatore.sample(range(totale), min(args.pagine, totale)))

        stampata: dict[int, str] = {}
        senza_bande: list[tuple[int, dict]] = []
        con_bande: list[tuple[int, dict]] = []
        vuote = 0
        for indice in indici:
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    documento.load_page(indice),
                    source_id="milestone42",
                    page_id=f"page:{indice:04d}",
                    capture_id=f"m42:{indice}",
                )
            )
            stampata[indice] = _numero_stampato(documento.load_page(indice))
            esito = esamina_pagina(primitive_page)
            if esito["senza_testo"]:
                vuote += 1
            elif esito["bande"] == 0:
                senza_bande.append((indice, esito))
            else:
                con_bande.append((indice, esito))

    print(f"file: {args.pdf.name}   pagine esaminate: {len(indici)} su {totale}")
    print(f"   senza testo: {vuote}   senza bande: {len(senza_bande)}   con bande: {len(con_bande)}")

    def riepilogo(nome: str, elenco: list[tuple[int, dict]]) -> None:
        if not elenco:
            return
        motivi: Counter[str] = Counter()
        corridoi = 0
        senza_corridoi = 0
        for _indice, esito in elenco:
            motivi += esito["motivi"]
            corridoi += esito["corridoi"]
            senza_corridoi += 1 if esito["corridoi"] == 0 else 0
        scarti = sum(v for k, v in motivi.items() if k != "ammesso")
        print(f"\n== {nome} ({len(elenco)} pagine) ==")
        print(f"   corridoi incatenati: {corridoi}   pagine con ZERO corridoi: {senza_corridoi}")
        for motivo, quanti in motivi.most_common():
            quota = f"{quanti / scarti:5.1%}" if scarti and motivo != "ammesso" else "     "
            print(f"      {motivo:22s} {quanti:6d}  {quota}")

    riepilogo("pagine SENZA bande", senza_bande)
    riepilogo("pagine CON bande", con_bande)

    if con_bande:
        posizioni: Counter[str] = Counter()
        for _indice, esito in con_bande:
            posizioni += esito["posizioni"]
        fuori = sum(v for k, v in posizioni.items() if k != "dentro")
        totale_p = sum(posizioni.values())
        print(f"\n== Fase 2: dove sta il testo, sulle pagine CON bande "
              f"({totale_p} span) ==")
        print(f"   dentro una banda: {posizioni['dentro']} "
              f"({posizioni['dentro'] / totale_p:.1%})   fuori: {fuori} "
              f"({fuori / totale_p:.1%})")
        for posizione, quanti in posizioni.most_common():
            if posizione == "dentro":
                continue
            print(f"      {posizione:18s} {quanti:6d}  {quanti / fuori:5.1%} del fuori banda")
        classi: Counter[str] = Counter()
        for _indice, esito in con_bande:
            classi += esito["classi"]
        totale_c = sum(classi.values()) or 1
        print("   Fase 3 -- il fuori banda ha righe affiancate?")
        print(f"      affiancata (danno)   {classi['affiancata']:6d}  "
              f"{classi['affiancata'] / totale_c:5.1%}")
        print(f"      sola (y e' giusto)   {classi['sola']:6d}  "
              f"{classi['sola'] / totale_c:5.1%}")
        # Le pagine si ordinano per DANNO (span affiancati fuori banda), non per
        # testo fuori banda: un titolo o una tabella a tutta larghezza fuori
        # banda non e' un danno, e ordinare per quello propone le pagine
        # sbagliate da verificare a mano.
        peggiori = sorted(
            [t for t in con_bande + senza_bande if t[1]["classi"]["affiancata"] > 0],
            key=lambda t: -t[1]["classi"]["affiancata"],
        )[:12]
        print("   pagine con piu' DANNO (span affiancati letti senza colonna):")
        for indice, esito in peggiori:
            fuori_pagina = esito["primitive"] - esito["posizioni"]["dentro"]
            print(f"      indice {indice:4d} (stampata {stampata.get(indice, '?')}): "
                  f"danno {esito['classi']['affiancata']:4d} span, "
                  f"fuori banda {fuori_pagina:4d}/{esito['primitive']:4d}, "
                  f"{esito['bande']} bande")
        controlli = sorted(
            [t for t in con_bande if t[1]["classi"]["affiancata"] == 0
             and t[1]["primitive"] > 60],
            key=lambda t: -t[1]["primitive"],
        )[:3]
        print("   pagine di CONTROLLO (nessun danno, molto testo):")
        for indice, esito in controlli:
            print(f"      indice {indice:4d} (stampata {stampata.get(indice, '?')}): "
                  f"{esito['primitive']} span, {esito['bande']} bande")

    if senza_bande:
        print("\n== il corridoio piu' alto scartato, sulle pagine senza bande ==")
        for indice, esito in senza_bande[: args.dettaglio]:
            peggiore = esito["peggiore"]
            if peggiore is None:
                print(f"   pagina {indice:4d}: nessun corridoio incatenato "
                      f"({esito['righe']} righe di testo)")
                continue
            print(
                f"   pagina {indice:4d}: {peggiore['motivo']:20s} "
                f"x {peggiore['x'][0]:6.1f}-{peggiore['x'][1]:6.1f}  "
                f"alto {peggiore['altezza_pt']:6.1f}pt = {peggiore['altezza_righe']:5.2f} righe  "
                f"fianchi min {peggiore['righe_per_lato']:3d} righe, "
                f"{peggiore['righe_con_parole']:3d} con parole"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# --------------------------------------------------------------------------
# Modalita' `--dubbi`: NON cerca le pagine peggiori, cerca quelle su cui il
# modello corrente e' incerto. Dopo la verifica a vista di sei pagine il modello
# dice: un corridoio scartato da `too_few_wordy_lines` va tenuto se sta dentro un
# `table_candidate`, e buttato se e' arredo di margine. Le quattro categorie qui
# sotto sono i punti dove quella regola puo' rompersi, ed esistono per essere
# sottoposte a un occhio umano, non per essere contate.
# --------------------------------------------------------------------------


def _tabelle_di(primitive_page, plumber_page, generation_id: str):
    from page_analysis_table_candidate import build_table_candidate_page_analysis
    from page_analysis_table_candidate_binding import BoundTableCandidatePage

    legato = BoundTableCandidatePage(primitive_page=primitive_page, plumber_page=plumber_page)
    return [c.bbox for c in build_table_candidate_page_analysis(
        legato, generation_id=generation_id).candidates]


def corridoi_dubbi(primitive_page, tabelle) -> list[dict]:
    """I corridoi della pagina con il loro esito, il profilo e se una tabella li
    contiene. Nessun giudizio: la categoria la assegna il chiamante."""
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
        x0 = rect.x_bin_start * _DEFAULT_BIN_WIDTH_X
        x1 = rect.x_bin_end * _DEFAULT_BIN_WIDTH_X
        dentro_tabella = any(
            t[0] <= x0 and t[2] >= x1 and t[1] <= rect.y1 and t[3] >= rect.y0 for t in tabelle
        )
        fuori.append({
            "motivo": motivo, "x": (x0, x1), "y": (rect.y0, rect.y1),
            "righe": (rect.y1 - rect.y0) / altezza if altezza else 0.0,
            "fianchi": profilo.minimum, "con_parole": profilo.wordy_minimum,
            "in_tabella": dentro_tabella,
        })
    return fuori
