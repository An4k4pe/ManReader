"""Righe di una pagina in ordine di colonna, dalle bande del producer di produzione.

**Correzione 3** di `PASSAGGIO_DI_CONSEGNE.md` §5, criterio in
`CRITERIO_CORREZIONI_2_3.md`. Sostituisce `COL_GAP = 30.0` di `pila.py`: una
costante in punti tarata su un impaginato a quattro colonne, che su una pagina a
colonna singola da 612pt inventa 2-4 colonne (`VERDETTO_MANUALE2.md`, causa 3).

I confini di colonna vengono da `page_analysis_column_band.py` (Milestone 37),
che li ricava dal documento e non da soglie in punti. Il consumo passa dal
**contratto** -- candidati piu' misura satellite -- non dalle strutture interne
del producer: e' lo stesso percorso del consumer della fetta verticale.

## Codice copiato, e perche' non importato
`_source_line_key`, `_source_text_lines`, `_by_source_line` e `_tree_aware_order`
sono copie invariate di `scripts/compare_reading_order_with_column_bands.py`;
`_tree_rows_from_contract` e' copia invariata di
`scripts/prototype_vertical_slice_page.py`. Nel repo gli script non importano da
altri script (`prototype_vertical_slice_page.py:10-12`), ed e' la ragione per cui
quelle due funzioni sono gia' duplicate fra i due script citati. Qui vale lo
stesso: `esperimenti_statblock/` e' materiale esplorativo e non deve diventare un
consumatore di script diagnostici. Cio' che NON si duplica -- ed e' il punto
della correzione -- e' il **meccanismo**: le bande arrivano dal producer di
produzione, non da una seconda implementazione.

Il resto del pacchetto (`pila.py`, `real5.py`, ...) resta senza dipendenze dal
repo; questo file e' l'unico che ne ha, ed e' una scelta dichiarata.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, cast

import pymupdf

_QUI = Path(__file__).resolve()
for _cand in _QUI.parents:
    if (_cand / "primitive_model.py").is_file():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break

from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from page_analysis_model import RegionCandidate  # noqa: E402
from primitive_model import TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_OBSERVATION_ID = re.compile(r"^text:b(\d+):l(\d+):s(\d+)$")


def _source_line_key(primitive: TextPrimitive) -> tuple[int, int, int] | None:
    """`(block_index, line_index, span_index)` letti dall'id di osservazione."""

    match = _OBSERVATION_ID.match(primitive.source_observation_id or "")
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _source_text_lines(primitives: list[TextPrimitive]) -> list[list[TextPrimitive]]:
    """Le righe tipografiche come unita', prese da `(block_index, line_index)`.

    La riga NON si ricostruisce geometricamente: la cattura emette una primitiva
    per span e la riga sta gia' nell'id di osservazione. Ricavarla dalla
    sovrapposizione delle y reinventa peggio un'informazione gia' disponibile, e
    fonde righe di blocchi diversi (misurato su Dag p.48: 54 righe geometriche
    contro 75 di sorgente)."""

    grouped: dict[tuple[int, int], list[tuple[int, TextPrimitive]]] = {}
    lines: list[list[TextPrimitive]] = []
    for primitive in primitives:
        key = _source_line_key(primitive)
        if key is None:
            lines.append([primitive])
            continue
        grouped.setdefault((key[0], key[1]), []).append((key[2], primitive))

    lines.extend(
        [primitive for _span_index, primitive in sorted(spans, key=lambda item: item[0])]
        for spans in grouped.values()
    )
    lines.sort(
        key=lambda line: (
            min(p.bbox[1] for p in line),
            min(p.bbox[0] for p in line),
        )
    )
    return lines


def _by_source_line(primitives: list[TextPrimitive]) -> list[TextPrimitive]:
    """Ordina per riga tipografica, prendendo la riga dalla sorgente."""

    return [p for line in _source_text_lines(primitives) for p in line]


def _tree_rows_from_contract(
    candidates: tuple[RegionCandidate, ...],
    measurements: tuple[Any, ...],
) -> list[dict[str, object]]:
    """Le righe che l'ordinatore vuole, ricostruite da candidati e misure.

    Dal candidato bbox e primitive, dalla misura gutter, livello e padre.
    Nessuna struttura interna del producer attraversa questo confine."""

    band_id_by_candidate = {c.candidate_id: index + 1 for index, c in enumerate(candidates)}
    measure_by_candidate = {m.candidate_id: m for m in measurements}

    rows: list[dict[str, object]] = []
    for candidate in candidates:
        measure = measure_by_candidate.get(candidate.candidate_id)
        if measure is None:
            continue
        parent: object = ""
        if measure.parent_candidate_id is not None:
            parent = band_id_by_candidate.get(measure.parent_candidate_id, "")
        rows.append(
            {
                "band_id": band_id_by_candidate[candidate.candidate_id],
                "parent_id": parent,
                "depth": measure.depth,
                "x0": candidate.bbox[0],
                "y0": candidate.bbox[1],
                "x1": candidate.bbox[2],
                "y1": candidate.bbox[3],
                "column_count": measure.column_count,
                "gutter_x_intervals": " ".join(
                    f"{a:.1f}-{b:.1f}" for a, b in measure.gutter_x_intervals
                ),
            }
        )
    return rows


def _tree_aware_order(
    text_primitives: list[TextPrimitive], tree: list[dict[str, object]]
) -> tuple[list[tuple[TextPrimitive, int]], int]:
    """Ordina usando l'albero di bande: ogni primitiva va alla banda PIU'
    PROFONDA che la contiene, non alla prima. Le bande piu' profonde definiscono
    quali sono le colonne maggiori; se dentro ne compaiono altre sono tabelle o
    gutter subordinati."""

    rows = {int(cast(int, r["band_id"])): r for r in tree}
    children: dict[int, list[int]] = {}
    roots: list[int] = []
    for band_id, row in rows.items():
        parent = row.get("parent_id")
        if parent in ("", None):
            roots.append(band_id)
        else:
            children.setdefault(int(cast(int, parent)), []).append(band_id)

    def contains(band_id: int, primitive: TextPrimitive) -> bool:
        row = rows[band_id]
        cx = (primitive.bbox[0] + primitive.bbox[2]) / 2.0
        cy = (primitive.bbox[1] + primitive.bbox[3]) / 2.0
        return (
            float(cast(float, row["x0"])) <= cx < float(cast(float, row["x1"]))
            and float(cast(float, row["y0"])) <= cy < float(cast(float, row["y1"]))
        )

    owner: dict[int, int | None] = {}
    for index, primitive in enumerate(text_primitives):
        best: int | None = None
        best_depth = -1
        for band_id, row in rows.items():
            depth_here = int(cast(int, row["depth"]))
            if not contains(band_id, primitive):
                continue
            if best is None or depth_here > best_depth:
                best, best_depth = band_id, depth_here
        owner[index] = best

    ordered: list[tuple[TextPrimitive, int]] = []
    group = [0]
    inside = [0]

    def gutters_of(band_id: int) -> list[tuple[float, float]]:
        out: list[tuple[float, float]] = []
        for chunk in str(rows[band_id].get("gutter_x_intervals") or "").split():
            start, _, end = chunk.partition("-")
            try:
                out.append((float(start), float(end)))
            except ValueError:
                continue
        return sorted(out)

    def emit_band(band_id: int) -> None:
        row = rows[band_id]
        bounds = (
            [float(cast(float, row["x0"]))]
            + [edge for pair in gutters_of(band_id) for edge in pair]
            + [float(cast(float, row["x1"]))]
        )
        own = [text_primitives[i] for i, b in owner.items() if b == band_id]
        for index in range(0, len(bounds) - 1, 2):
            col_x0, col_x1 = bounds[index], bounds[index + 1]
            group[0] += 1
            here: list[tuple[float, int, object]] = []
            in_column = [
                primitive
                for primitive in own
                if col_x0 <= (primitive.bbox[0] + primitive.bbox[2]) / 2.0 < col_x1
            ]
            inside[0] += len(in_column)
            for position, primitive in enumerate(_by_source_line(in_column)):
                here.append((float(position), 1, primitive))
            ordered_in_column = [item for item in here]
            for child in children.get(band_id, []):
                crow = rows[child]
                if (
                    col_x0 <= float(cast(float, crow["x0"]))
                    and float(cast(float, crow["x1"])) <= col_x1
                ):
                    before = sum(
                        1
                        for _pos, _kind, prim in ordered_in_column
                        if cast(TextPrimitive, prim).bbox[1] < float(cast(float, crow["y0"]))
                    )
                    here.append((before - 0.5, 0, child))
            here.sort(key=lambda item: (item[0], item[1]))
            for _y, kind, payload in here:
                if kind == 1:
                    ordered.append((cast(TextPrimitive, payload), group[0]))
                else:
                    emit_band(cast(int, payload))
                    group[0] += 1

    loose = [text_primitives[i] for i, b in owner.items() if b is None]
    entries: list[tuple[float, int, object]] = []
    for band_id in roots:
        entries.append((float(cast(float, rows[band_id]["y0"])), 0, band_id))
    for line in _source_text_lines(loose):
        entries.append((min(p.bbox[1] for p in line), 1, line))
    entries.sort(key=lambda item: (item[0], item[1]))
    for _y, kind, payload in entries:
        if kind == 1:
            for primitive in cast(list, payload):
                ordered.append((primitive, group[0]))
        else:
            emit_band(cast(int, payload))
            group[0] += 1
    return ordered, inside[0]


def _stile(primitive: TextPrimitive) -> tuple[str, float, object]:
    """Lo stile come identita', nella stessa forma di `pila.py`.

    `pila.py` legge `(font senza prefisso di sottoinsieme, dimensione a un
    decimale, colore)` dagli span PyMuPDF. La primitiva normalizzata porta gli
    stessi tre campi -- il colore come RGBA invece che come intero, ma qui conta
    solo l'uguaglianza fra stili, non il valore."""

    nome = (primitive.font_name or "").split("+")[-1]
    return (nome, round(primitive.font_size or 0.0, 1), primitive.color)


def righe_per_pagina(path: str) -> list[list[dict]]:
    """Le righe di ogni pagina, in ordine di colonna, nella forma di `pila.py`.

    Ogni riga e' `{y0, x0, testo, stili, span, colonna}`. `colonna` e' in piu'
    rispetto a `pila.py` e serve alla misura M3 del criterio: e' l'identificativo
    di colonna assegnato dall'ordinatore a bande, non una coordinata.
    """

    pagine: list[list[dict]] = []
    with pymupdf.open(path) as documento:
        for indice in range(documento.page_count):
            pagina = documento.load_page(indice)
            try:
                cattura = capture_pymupdf_page(
                    pagina,
                    source_id="esperimenti-statblock",
                    page_id=f"page:{indice:04d}",
                    capture_id=f"pila2:{indice}",
                )
                primitive_page = normalize_backend_page_capture(cattura)
                analisi, misure = build_column_band_page_analysis_with_measurements(
                    primitive_page, generation_id=f"pila2:{indice}"
                )
                albero = _tree_rows_from_contract(analisi.candidates, misure)
                ordinate, _dentro = _tree_aware_order(
                    list(primitive_page.text_primitives), albero
                )
            except Exception as errore:  # noqa: BLE001
                # Degrado dichiarato, mai silenzioso: la pagina che la cattura o
                # il producer rifiutano esce comunque, ordinata per riga di
                # sorgente e senza colonne, e il motivo finisce su stderr.
                print(
                    f"pagina {indice}: bande non disponibili ({type(errore).__name__}: {errore}); "
                    "ordine per riga di sorgente, nessuna colonna",
                    file=sys.stderr,
                )
                try:
                    cattura = capture_pymupdf_page(
                        pagina,
                        source_id="esperimenti-statblock",
                        page_id=f"page:{indice:04d}",
                        capture_id=f"pila2-fallback:{indice}",
                    )
                    primitive_page = normalize_backend_page_capture(cattura)
                except Exception as secondo:  # noqa: BLE001
                    print(
                        f"pagina {indice}: nemmeno la cattura riesce "
                        f"({type(secondo).__name__}: {secondo}); pagina vuota",
                        file=sys.stderr,
                    )
                    pagine.append([])
                    continue
                ordinate = [
                    (p, 0) for p in _by_source_line(list(primitive_page.text_primitives))
                ]

            righe: list[dict] = []
            corrente: list[TextPrimitive] = []
            chiave_corrente: tuple[int, tuple[int, int] | None] | None = None
            for primitiva, colonna in ordinate:
                if not primitiva.text.strip():
                    continue
                sorgente = _source_line_key(primitiva)
                chiave = (colonna, sorgente[:2] if sorgente is not None else None)
                if chiave_corrente is not None and chiave != chiave_corrente:
                    righe.append(_riga(corrente, chiave_corrente[0]))
                    corrente = []
                chiave_corrente = chiave
                corrente.append(primitiva)
            if corrente and chiave_corrente is not None:
                righe.append(_riga(corrente, chiave_corrente[0]))
            pagine.append(righe)
    return pagine


def _riga(primitive: list[TextPrimitive], colonna: int) -> dict:
    # `x1`/`y1` non servono al rilevatore e non erano nel dizionario di
    # `pila.py`: le porta la resa Markdown, perche' `markdown_builder` decide
    # gli a-capo di paragrafo sul bbox completo. Nessun consumatore esistente
    # cambia comportamento per una chiave in piu'.
    sorgente = _source_line_key(primitive[0])
    return {
        # Il blocco di sorgente e' il PARAGRAFO (`text:b{block}:l{line}:s{span}`),
        # non una deduzione geometrica: serve alla resa, che senza di esso
        # fonde in un paragrafo solo righe di elenchi diversi.
        "blocco": sorgente[0] if sorgente is not None else -1,
        "y0": min(p.bbox[1] for p in primitive),
        "x0": min(p.bbox[0] for p in primitive),
        "y1": max(p.bbox[3] for p in primitive),
        "x1": max(p.bbox[2] for p in primitive),
        "testo": "".join(p.text for p in primitive),
        "stili": [_stile(p) for p in primitive],
        "span": [p.text for p in primitive],
        "colonna": colonna,
    }


def visuali_per_pagina(path: str) -> list[list[tuple[float, float, float, float]]]:
    """I bbox delle primitive visive per pagina, dalla stessa catena di cattura.

    Serve solo a CONTARE quante visuali cadono dentro le regioni di scheda: la
    nota che sostituisce sfondi e cornici e' fuori dallo scope del giro Markdown,
    e questo numero e' cio' che il prossimo giro trova gia' misurato."""

    fuori: list[list[tuple[float, float, float, float]]] = []
    with pymupdf.open(path) as documento:
        for indice in range(documento.page_count):
            pagina = documento.load_page(indice)
            try:
                cattura = capture_pymupdf_page(
                    pagina,
                    source_id="esperimenti-statblock",
                    page_id=f"page:{indice:04d}",
                    capture_id=f"visuali:{indice}",
                )
                primitive_page = normalize_backend_page_capture(cattura)
            except Exception as errore:  # noqa: BLE001
                print(
                    f"pagina {indice}: cattura fallita ({type(errore).__name__}: {errore})",
                    file=sys.stderr,
                )
                fuori.append([])
                continue
            fuori.append(
                [
                    p.bbox
                    for p in list(primitive_page.image_primitives)
                    + list(primitive_page.drawing_primitives)
                ]
            )
    return fuori
