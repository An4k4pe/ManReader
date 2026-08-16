"""Confronto del READING ORDER con e senza `column_band`, sulla stessa pagina.

E' il test che nessuna misura sui CSV puo' sostituire, e che Milestone 36 indica
come il consumer reale di `column_band`: non "quante bande trova" ma "la pagina
si legge".

Cosa cambia fra i due output, e nient'altro: l'ORDINAMENTO delle TextPrimitive.

  baseline        `(y0, x0)` -- identico a
                  `prototype_vertical_slice_page.py:219-220`, copiato invariato:
                  e' cio' che la pipeline fa OGGI, non un confronto equo.
  baseline_lines  la stessa, con la sola riga tipografica presa dalla SORGENTE
                  (`block_index`/`line_index`, vedi `_source_text_lines`) e
                  NESSUNA banda. E' il termine di paragone equo: il guadagno del
                  ramo a bande va misurato contro questa, altrimenti gli si
                  attribuisce anche il merito della correzione di riga -- su
                  DIE p.127 l'85% delle primitive cambia posizione per quella
                  sola.
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
import re
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

from prototype_derived_column_bands import (  # noqa: E402
    _DEFAULT_MIN_FLANKING_CHARS,
    _process_page,
)

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


def _by_source_line(primitives: list[TextPrimitive]) -> list[TextPrimitive]:
    """Ordina per riga tipografica, prendendo la riga dalla sorgente.

    Ordinare per `(y0, x0)` sembra corretto e non lo e': gli span di una stessa
    riga hanno y leggermente diverse (corsivo, grassetto, corpo diverso) e
    finiscono mescolati con quelli delle righe vicine. Misurato su Dag p.48:
    sette span della stessa riga con y fra 410,89 e 411,01 -- 0,12pt."""

    return [p for line in _source_text_lines(primitives) for p in line]


def _source_text_lines(primitives: list[TextPrimitive]) -> list[list[TextPrimitive]]:
    """Le righe tipografiche come unita', prese da `(block_index, line_index)`.

    La riga NON si ricostruisce geometricamente: `pymupdf_capture.py:123-125`
    emette una primitiva per span e la riga sta gia' nell'id di osservazione
    (`text:b{block}:l{line}:s{span}`). Ricavarla dalla sovrapposizione delle y
    reinventa peggio un'informazione gia' disponibile -- `AGENTS.MD` §Layout e
    candidati -- ed e' anche sbagliato: la versione precedente confrontava ogni
    span solo contro il PRIMO della riga e fondeva righe di blocchi diversi.
    Misurato su Dag p.48 (54 righe geometriche contro 75 di sorgente, 21
    fusioni) e Dag p.164 (50 contro 75, 25 fusioni): su Dag p.48 il titolo
    SOTTOCLASSI DEL RANGER finiva nella stessa "riga" del corpo. Una riga a
    cavallo di due colonne non e' assegnabile a nessuna banda. Verbale in
    `scripts/inspect_span_line_identity.py`, che conserva l'implementazione
    geometrica e la rimisura contro questa.

    Dentro la riga l'ordine e' `span_index`, cioe' quello dichiarato dalla
    sorgente. Divergere da `x0` e' raro (2 righe multi-span su 6.335, 0,03% su
    cinque manuali): la scelta non e' portante.

    Le righe escono ordinate dall'alto, perche' l'ordine dei blocchi della
    sorgente non e' garantito essere quello visivo."""

    grouped: dict[tuple[int, int], list[tuple[int, TextPrimitive]]] = {}
    lines: list[list[TextPrimitive]] = []
    for primitive in primitives:
        key = _source_line_key(primitive)
        if key is None:
            # Id non interpretabile: riga a se'. Non si indovina un
            # raggruppamento, perche' sbagliarlo fonde righe di colonne diverse
            # ed e' il difetto che questa funzione esiste per non avere.
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


def _tree_aware_order(
    text_primitives: list[TextPrimitive], tree: list[dict[str, object]]
) -> tuple[list[tuple[TextPrimitive, int]], int]:
    """Ordina usando l'albero di bande: ogni primitiva va alla banda PIU'
    PROFONDA che la contiene, non alla prima.

    E' la differenza che rende sicura l'estensione delle bande. Con le bande
    piatte una banda estesa si prendeva ogni primitiva e svuotava le altre
    (misurato su 7 pagine dalla revisione architetturale); qui una banda figlia
    vince sempre sul padre, quindi il padre puo' estendersi quanto serve senza
    rubare niente a nessuno."""

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

    # Quale livello vince, quando piu' bande contengono la stessa primitiva:
    # la piu' PROFONDA.
    #
    # Ripristinata dopo essere stata rovesciata in "vince l'esterna" sulla base
    # di due argomenti di Chat A, entrambi sbagliati e corretti dall'utente.
    #
    # Primo argomento, che la banda esterna desse lettura per righe sulle
    # tabelle: falso, da' lettura per colonne al gutter piu' esterno. Ma la
    # correzione vera e' un'altra, ed e' che la domanda era mal posta:
    # `column_band` NON deve leggere le tabelle. Deve dire dove sono i confini
    # di colonna; se una regione e' una tabella la gestisce il consumer di
    # tabelle, aiutato proprio da questi gutter. Giudicare il meccanismo su
    # quanto legge male una tabella era giudicarlo su un compito che non ha, e i
    # sette gutter annidati di DB p.76 non sono una patologia: sono la
    # descrizione corretta di una tabella a nove colonne.
    #
    # Secondo argomento, che una banda estesa "rubi" le primitive alle figlie:
    # formulazione confusa. La regola non sottrae niente, sceglie soltanto quale
    # struttura di colonne ordina una primitiva. Il pericolo dello svuotamento
    # veniva dalle bande PIATTE con "vince la prima", dove non esisteva
    # gerarchia; con l'albero quel meccanismo non c'e' piu'. Era la paura di un
    # problema trasportata in un contesto dove era gia' risolto.
    #
    # Cosa fa quindi la regola, nella formulazione dell'utente: le bande piu'
    # profonde definiscono quali sono le colonne maggiori, e se dentro ne
    # compaiono altre sono tabelle o gutter subordinati -- materiale per chi di
    # dovere, non un ordine di lettura da imporre qui.
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
            # L'indice nella sequenza per riga visiva diventa la chiave di
            # ordinamento, cosi' gli span di una stessa riga restano in ordine
            # di x anche quando le loro y differiscono di frazioni di punto.
            for position, primitive in enumerate(_by_source_line(in_column)):
                here.append((float(position), 1, primitive))
            ordered_in_column = [item for item in here]
            for child in children.get(band_id, []):
                crow = rows[child]
                if col_x0 <= float(cast(float, crow["x0"])) and float(cast(float, crow["x1"])) <= col_x1:
                    # Il figlio si inserisce dove cadono le primitive alla sua y.
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

    # Anche le primitive fuori da ogni banda vanno raggruppate in righe visive:
    # senza, una pagina che non produce bande (BoB p.417, tre blocchi di prosa a
    # colonna unica) esce con gli span della stessa riga in ordine di y invece
    # che di x, e i grassetti finiscono attaccati fra loro.
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


def _baseline_order(text_primitives: list[TextPrimitive]) -> list[TextPrimitive]:
    """Copia invariata di `prototype_vertical_slice_page.py:219-220`."""

    return sorted(text_primitives, key=lambda p: (p.bbox[1], p.bbox[0]))


def _column_of(primitive: TextPrimitive, gutters: list[tuple[float, float]]) -> int:
    """Indice di colonna dentro una banda: quanti gutter stanno alla sinistra
    della primitiva. Il confronto usa il centro x, cosi' una primitiva che
    sborda leggermente su un gutter non cambia colonna."""

    center = (primitive.bbox[0] + primitive.bbox[2]) / 2.0
    return sum(1 for _, gap_end in gutters if center >= gap_end)


def _occupied_y_ranges(
    text_primitives: list[TextPrimitive],
    visuals: list[tuple[float, float, float, float]],
    *,
    gap_start: float,
    gap_end: float,
    line_height: float,
) -> list[tuple[float, float]]:
    """Fasce y in cui almeno una delle due colonne e' OCCUPATA, da testo o da un
    visuale. Serve come guardia: senza, l'estensione salda due strutture
    separate da un vuoto -- il "tunneling" misurato dalla revisione
    architetturale al 3,3% dei gutter, con casi fino a 29 righe di buco.

    Un visuale conta solo se e' alto almeno un'interlinea della pagina: le
    righe decorative da 1pt non rendono occupata una fascia. L'unita' e'
    misurata sul documento, non una costante in pt."""

    ranges: list[tuple[float, float]] = []
    for primitive in text_primitives:
        if primitive.bbox[2] <= gap_start or primitive.bbox[0] >= gap_end:
            ranges.append((primitive.bbox[1], primitive.bbox[3]))
    for x0, y0, x1, y1 in visuals:
        if y1 - y0 < line_height:
            continue
        if x1 <= gap_start or x0 >= gap_end:
            ranges.append((y0, y1))
    if not ranges:
        return []
    ranges.sort()
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + line_height:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _widen_band_over_visuals(
    band: tuple[float, float, list[tuple[float, float]]],
    text_primitives: list[TextPrimitive],
    visuals: list[tuple[float, float, float, float]],
    line_height: float,
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
    nel producer.

    **ROTTA. Non usare questa flag per trarre conclusioni.** Una versione
    precedente di questa docstring affermava che su DrW p.97 la banda si
    estende "da y 46 a 761". Misurato eseguendo il codice: si estende da
    **-9 a 792**, cioe' l'intera pagina piu' il bleed. La guardia di occupazione
    collassa in una sola fascia perche' fra i visuali che conta come occupanti
    c'e' un fondino a piena pagina: il filtro sull'altezza esclude i filetti da
    1pt ed e' cieco ai fondi. Conseguenza peggiore, misurata dalla revisione su
    7 pagine del campione: quando una banda a un gutter si estende a tutta la
    pagina, `_band_aware_order` le assegna ogni primitiva e le bande a piu'
    colonne restano VUOTE -- la struttura di tabella viene distrutta, e il
    conteggio stampato su stderr non se ne accorge perche' conta le bande
    parsate, non quelle effettive. Il caso Lan p.253, su cui la guardia era
    stata verificata e dichiarata funzionante, e' quello fortunato: li' non c'e'
    un fondo a piena pagina.

    Serve un segnale diverso da "esiste un visuale alto almeno un'interlinea".
    Non corretto: la flag resta per non perdere il caso d'uso, con questo
    avviso.

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

    # L'estensione si ferma dove la pagina smette di essere occupata: si prende
    # la sola fascia contigua che contiene gia' la banda, non l'inviluppo di
    # tutto il contenuto della pagina.
    occupied = _occupied_y_ranges(
        text_primitives,
        visuals,
        gap_start=gap_start,
        gap_end=gap_end,
        line_height=line_height,
    )
    for start, end in occupied:
        if start <= y0 and y1 <= end:
            return (min(y0, start), max(y1, end), [(gap_start, gap_end)])
    return band


def _band_aware_order(
    text_primitives: list[TextPrimitive],
    bands: list[dict[str, object]],
    *,
    widen: bool = False,
    visuals: list[tuple[float, float, float, float]] | None = None,
    line_height: float = 0.0,
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
        parsed = [
            _widen_band_over_visuals(band, text_primitives, visuals or [], line_height)
            for band in parsed
        ]
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
        # Stessa regola di `_ordered_markdown_body` nella fetta verticale, e
        # tenuta identica di proposito: una primitiva senza testo non fa da
        # termine di paragone per l'interruzione di paragrafo. Su DB p.53 gli
        # span vuoti di fine voce hanno bbox piu' alto della riga e facevano da
        # ponte fra una voce e la successiva.
        if text:
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
        "--use-tree",
        action="store_true",
        help="Usa la segmentazione GERARCHICA e assegna ogni primitiva alla banda piu' "
        "PROFONDA che la contiene, invece delle bande a fasce y.",
    )
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
        default=float(_DEFAULT_MIN_FLANKING_CHARS),
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
        _gutters, bands, tree = _process_page(
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
    # Terza uscita: la baseline CON la sola correzione per riga visiva, senza
    # bande. Serve ad attribuire il guadagno alla causa giusta. Confrontare il
    # ramo a bande (che ha la correzione) con la baseline grezza (che non ce
    # l'ha) misura le due cose insieme e le attribuisce entrambe a
    # `column_band`: su DIE p.127 l'85% delle primitive cambia posizione per la
    # sola correzione di riga. Rilievo di Chat B, verificato.
    baseline_lines = [(p, 0) for p in _by_source_line(primitives)]
    visuals = [
        (p.bbox[0], p.bbox[1], p.bbox[2], p.bbox[3])
        for p in list(primitive_page.image_primitives) + list(primitive_page.drawing_primitives)
    ]
    heights = sorted(p.bbox[3] - p.bbox[1] for p in primitives if p.bbox[3] > p.bbox[1])
    line_height = heights[len(heights) // 2] if heights else 0.0
    if args.use_tree:
        band_aware, inside = _tree_aware_order(primitives, tree)
    else:
        band_aware, inside = _band_aware_order(
            primitives, bands, widen=args.widen_bands, visuals=visuals, line_height=line_height
        )

    (output_dir / "order_baseline.md").write_text(_render(baseline), encoding="utf-8")
    (output_dir / "order_baseline_lines.md").write_text(
        _render(baseline_lines), encoding="utf-8"
    )
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
