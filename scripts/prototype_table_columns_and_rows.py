"""Prototipo: colonne da regole ad hoc dentro la regione, righe dalla regola del paragrafo.

Due idee dell'utente, provate insieme e separatamente:

1. **Dove si suppone ci sia una tabella**, le colonne si cercano con regole
   PROPRIE dentro la regione, non con quelle di `column_band`, che sono tarate
   per la prosa e per l'ordine di lettura. Il criterio ad hoc qui e' la
   PERSISTENZA: un corridoio verticale libero in (quasi) tutte le righe della
   regione e' un confine di colonna. Dentro una tabella il confound della prosa
   non si pone, perche' si e' gia' supposto che sia una tabella.

2. **Il testo delle celle** usa lo stesso metodo che il produttore di Markdown usa
   per i paragrafi -- `breaks_paragraph` e `join_lines` di `ir2_builder` --
   invece della giunzione con spazio che `build_table` fa oggi. E la stessa
   regola decide se una riga di sorgente e' una RIGA NUOVA della tabella o la
   continuazione della cella sopra.

Read-only, nessuna scrittura. Non e' un producer e non tocca niente.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ir2_builder import (  # noqa: E402
    _SourceLine,  # noqa: E402
    breaks_paragraph,
    group_source_lines,
    join_lines,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

BBox = tuple[float, float, float, float]

LINES = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
TEXT_LINES = {"vertical_strategy": "text", "horizontal_strategy": "lines"}


# ---------------------------------------------------------------- 1. le colonne


def _lines_in_region(page: NormalizedPrimitivePage, bbox: BBox) -> list[_SourceLine]:
    """Le righe di sorgente della regione, nell'ordine della sorgente."""

    x0, y0, x1, y1 = bbox
    inside: list[TextPrimitive] = []
    for primitive in page.text_primitives:
        if not primitive.text.strip():
            continue
        cx = (primitive.bbox[0] + primitive.bbox[2]) / 2.0
        cy = (primitive.bbox[1] + primitive.bbox[3]) / 2.0
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            inside.append(primitive)
    return group_source_lines(inside)


def table_column_gutters(
    lines: Sequence[_SourceLine],
    bbox: BBox,
    *,
    bin_width: float = 1.0,
    min_persistence: float = 1.0,
    min_gutter_width: float = 2.0,
) -> list[tuple[float, float]]:
    """I confini di colonna dentro una regione supposta tabella.

    `min_persistence` e' la frazione di righe della regione in cui il corridoio
    deve essere libero. A 1.0 significa TUTTE: e' una definizione, non una
    taratura -- in una tabella ogni riga rispetta i confini di colonna. Si abbassa
    solo se si osserva una pagina in cui una cella unita lo richiede, e allora il
    valore va dichiarato.
    """

    x0, _y0, x1, _y1 = bbox
    if x1 <= x0 or not lines:
        return []
    bin_count = max(1, int((x1 - x0) / bin_width) + 1)

    free_counts = [0] * bin_count
    for line in lines:
        occupied = bytearray(bin_count)
        for primitive in line.primitives:
            px0 = max(x0, primitive.bbox[0])
            px1 = min(x1, primitive.bbox[2])
            if px1 <= px0:
                continue
            start = int((px0 - x0) / bin_width)
            end = min(bin_count - 1, int((px1 - x0) / bin_width))
            for index in range(start, end + 1):
                occupied[index] = 1
        for index in range(bin_count):
            if not occupied[index]:
                free_counts[index] += 1

    threshold = len(lines) * min_persistence
    gutters: list[tuple[float, float]] = []
    run_start: int | None = None
    for index in range(bin_count):
        free = free_counts[index] >= threshold - 1e-9
        if free and run_start is None:
            run_start = index
        elif not free and run_start is not None:
            gutters.append((run_start, index))
            run_start = None
    if run_start is not None:
        gutters.append((run_start, bin_count))

    result: list[tuple[float, float]] = []
    for start, end in gutters:
        gx0 = x0 + start * bin_width
        gx1 = x0 + end * bin_width
        if gx0 <= x0 + 1e-9 or gx1 >= x1 - 1e-9:
            continue  # margine, non corridoio interno
        if gx1 - gx0 < min_gutter_width:
            continue
        result.append((gx0, gx1))
    return result


def bounds_from_gutters(
    bbox: BBox, gutters: Sequence[tuple[float, float]], *, at_middle: bool = True
) -> list[tuple[float, float]]:
    """Le colonne: il gutter si stringe al suo CENTRO, non ai suoi bordi.

    Il gutter misurato e' l'intervallo libero **massimo** fra due colonne, ed e'
    largo quanto lo spazio che le righe di dati lasciano. Usare i suoi bordi
    stringe le colonne a quanto occupa il corpo, e un'INTESTAZIONE composta piu'
    larga del corpo resta fuori da entrambe. Misurato su DB idx 75: `IMP.` occupa
    `x164,4-182,6` e invade i gutter `159-166` e `181-195`, `DANNO` e `COSTO`
    fanno lo stesso -- nessun rettangolo poteva contenerla mantenendo 9 colonne.
    Il confine sta a meta' del corridoio, dove non toglie niente ai dati e lascia
    posto alle etichette.
    """

    x0, _y0, x1, _y1 = bbox
    bounds: list[tuple[float, float]] = []
    edge = x0
    for gx0, gx1 in sorted(gutters):
        left = (gx0 + gx1) / 2.0 if at_middle else gx0
        right = (gx0 + gx1) / 2.0 if at_middle else gx1
        if left > edge:
            bounds.append((edge, left))
        edge = max(edge, right)
    if x1 > edge:
        bounds.append((edge, x1))
    return bounds


def _regions_from_bands(page: NormalizedPrimitivePage) -> list[BBox]:
    """Le bande di `column_band`, ritagliate all'inchiostro delle loro primitive.

    La banda eredita l'estensione x dal padre, quindi arriva larga quanto la
    pagina anche quando la tabella occupa un terzo del foglio. Il ritaglio non
    tocca `column_band`: e' fatto qui, dal consumatore.
    """

    from page_analysis_column_band import build_column_band_page_analysis_with_measurements

    analysis, _ = build_column_band_page_analysis_with_measurements(
        page, generation_id="prototype-table"
    )
    regions: list[BBox] = []
    for candidate in analysis.candidates:
        members = [
            p
            for p in page.text_primitives
            if p.text.strip()
            and candidate.bbox[0] <= (p.bbox[0] + p.bbox[2]) / 2.0 <= candidate.bbox[2]
            and candidate.bbox[1] <= (p.bbox[1] + p.bbox[3]) / 2.0 <= candidate.bbox[3]
        ]
        if len(members) < 2:
            continue
        regions.append(
            (
                min(p.bbox[0] for p in members),
                min(p.bbox[1] for p in members),
                max(p.bbox[2] for p in members),
                max(p.bbox[3] for p in members),
            )
        )
    return regions


def _row_bands(page: NormalizedPrimitivePage) -> list[list[_SourceLine]]:
    """Le righe della pagina: righe di sorgente che si sovrappongono in y."""

    lines = group_source_lines(
        [p for p in page.text_primitives if p.text.strip()]
    )
    return _row_clusters(lines)


def regions_from_gutter_runs(
    page: NormalizedPrimitivePage,
    *,
    bin_width: float = 1.0,
    min_gutter_width: float = 2.0,
    min_rows: int = 3,
) -> list[BBox]:
    """Le regioni tabella come CORSE di righe che condividono un corridoio.

    Nessuna chiamata a pdfplumber, nessuna banda: la regione viene dalla stessa
    proprieta' che gia' definisce le colonne -- un corridoio verticale che
    nessuna riga attraversa -- applicata all'asse verticale. Una corsa cresce
    finche' l'intersezione dei corridoi delle sue righe resta non vuota; la riga
    che la svuota la chiude, ed e' cosi' che la prosa a piena larghezza esce da
    sola dalla regione.

    Esisteva per togliere la scelta `--region`. **E' CADUTA**, ed e' peggio di
    tutte e tre le sorgenti che voleva sostituire: misurato su sette pagine,
    DB idx 75 da' 5 colonne invece di 9, Lan idx 118 tre righe invece di 22,
    Lan idx 284 tre invece di 34.

    La causa e' nel criterio di crescita: la corsa si allarga finche'
    l'intersezione dei corridoi resta **non vuota**, e su una pagina a due
    colonne il corridoio di pagina non muore mai, quindi la corsa ingoia il
    foglio. Fermarsi quando l'intersezione si SVUOTA e' la condizione sbagliata:
    quella giusta e' quando la sua STRUTTURA cambia, che e' esattamente cio' che
    `_segment_bands` di `column_band` gia' fa -- e riscriverlo qui sarebbe
    riderivare quel modulo peggio.

    Resta nel file come `--region auto` perche' il tentativo sia rieseguibile,
    non perche' serva.
    """

    width = page.page_geometry.width
    bin_count = max(1, int(width / bin_width) + 1)
    bands = _row_bands(page)

    def occupancy(band: Sequence[_SourceLine]) -> tuple[bytearray, float, float]:
        occupied = bytearray(bin_count)
        x0, x1 = width, 0.0
        for line in band:
            for primitive in line.primitives:
                a = max(0.0, primitive.bbox[0])
                b = min(width, primitive.bbox[2])
                if b <= a:
                    continue
                x0, x1 = min(x0, a), max(x1, b)
                for index in range(int(a / bin_width), min(bin_count - 1, int(b / bin_width)) + 1):
                    occupied[index] = 1
        return occupied, x0, x1

    profiles = [occupancy(band) for band in bands]

    def shared_gutters(free: bytearray, x0: float, x1: float) -> int:
        start = int(x0 / bin_width)
        end = min(bin_count - 1, int(x1 / bin_width))
        found = 0
        run = 0
        for index in range(start, end + 1):
            if free[index]:
                run += 1
            else:
                if run * bin_width >= min_gutter_width:
                    found += 1
                run = 0
        return found

    regions: list[BBox] = []
    index = 0
    while index < len(bands):
        free = bytearray(1 for _ in range(bin_count))
        x0, x1 = width, 0.0
        end = index
        while end < len(bands):
            occupied, bx0, bx1 = profiles[end]
            candidate = bytearray(
                1 if free[i] and not occupied[i] else 0 for i in range(bin_count)
            )
            nx0, nx1 = min(x0, bx0), max(x1, bx1)
            if end > index and shared_gutters(candidate, nx0, nx1) == 0:
                break
            free, x0, x1 = candidate, nx0, nx1
            end += 1
        if end - index >= min_rows:
            members = [line for band in bands[index:end] for line in band]
            regions.append(
                (
                    min(min(p.bbox[0] for p in line.primitives) for line in members),
                    min(min(p.bbox[1] for p in line.primitives) for line in members),
                    max(max(p.bbox[2] for p in line.primitives) for line in members),
                    max(max(p.bbox[3] for p in line.primitives) for line in members),
                )
            )
            index = end
        else:
            index += 1
    return regions


def regions_from_corridors(
    page: NormalizedPrimitivePage,
    *,
    bin_width: float = 1.0,
    min_bands: int = 3,
    min_corridor_width: float = 1.0,
) -> list[BBox]:
    """La regione dai CORRIDOI VERTICALI, bianchi o disegnati.

    Descrizione dell'utente, verificata sui suoi tracciamenti: un confine di
    colonna e' un corridoio verticale -- bianco persistente fra il testo, oppure
    un filetto, che e' un gutter gia' tracciato -- e una tabella e' un insieme di
    corridoi che condividono l'estensione verticale.

    Il corridoio si misura dentro l'inchiostro della PAGINA, non di ogni banda:
    una riga di continuazione non ha testo nella colonna delle etichette, e col
    test per banda spezzava la corsa a meta' tabella.

    **L'intestazione NON e' ancora inclusa**, e va inclusa: decisione dell'utente,
    anche quando non rispetta le colonne, perche' le etichette sono spesso
    composte piu' larghe del corpo. Qui la regione e' la sola corsa dei corridoi,
    quindi su Lan pagina 19 escono le 13 righe di dati e non la riga
    `LL | GRINTA | ...`. Da fare, non fatto.
    """

    bands = [b for b in _row_clusters(
        group_source_lines([p for p in page.text_primitives if p.text.strip()])
    )]
    if len(bands) < min_bands:
        return []

    width = page.page_geometry.width
    bin_count = int(width / bin_width) + 1
    extents = []
    occ: list[bytearray] = []
    for band in bands:
        row = bytearray(bin_count)
        x0, x1 = width, 0.0
        for line in band:
            for primitive in line.primitives:
                a = max(0.0, primitive.bbox[0])
                b = min(width, primitive.bbox[2])
                if b <= a:
                    continue
                x0, x1 = min(x0, a), max(x1, b)
                for i in range(int(a / bin_width), min(bin_count - 1, int(b / bin_width)) + 1):
                    row[i] = 1
        occ.append(row)
        extents.append((x0, x1))
    page_x0 = min(e[0] for e in extents)
    page_x1 = max(e[1] for e in extents)

    # SESTO TENTATIVO, RITIRATO. La linea si ALLINEAVA man mano che la corsa
    # cresceva -- «una linea continua che attraversa la tabella senza toccare
    # nulla», precisazione dell'utente sui suoi tracciamenti -- invece di essere
    # fissata sul seme e poi verificata. E' l'implementazione fedele della sua
    # descrizione, e discrimina MENO, non di piu': una linea che puo' spostarsi
    # di lato trova sempre un passaggio, quindi la corsa attraversa anche la
    # prosa. Lan pagina 19 da 7x13 a 5x3, Lan pagina 52 da due tabelle a una da
    # 80 righe, BoB pagina 239 da 2x7 a 2x44, Wil pagina 78 da 4x6 a 1x1,
    # DrW pagina 248 da 4x44 a 3x251. Migliora due pagine (Wil pagina 74 da 17 a
    # 22 righe su 20 attese, DB pagina 62 perde una regione spuria) e il
    # `Criterio_EstensioneRegioneTabella_v1.md` §5 dice che una sola regressione
    # ferma il giro.
    #
    # La lettura: l'utente traccia la linea DENTRO una tabella che ha gia' visto.
    # La linea mobile descrive bene com'e' fatto un gutter e non dice dove
    # finisce la tabella, perche' passa anche dove tabella non c'e'.
    best_run: list[tuple[int, int] | None] = []
    for i in range(bin_count):
        if not (page_x0 < i * bin_width < page_x1):
            best_run.append(None)
            continue
        longest = None
        run_start = None
        for b in range(len(bands) + 1):
            free = b < len(bands) and not occ[b][i]
            if free and run_start is None:
                run_start = b
            elif not free and run_start is not None:
                if longest is None or b - run_start > longest[1] - longest[0]:
                    longest = (run_start, b)
                run_start = None
        best_run.append(longest if longest and longest[1] - longest[0] >= min_bands else None)

    corridors: list[tuple[int, int, int, int]] = []  # bin0, bin1, banda0, banda1
    i = 0
    while i < bin_count:
        if best_run[i] is None:
            i += 1
            continue
        b0, b1 = best_run[i]
        first = i
        j = i + 1
        while j < bin_count and best_run[j] is not None:
            nb0, nb1 = best_run[j]
            if nb0 >= b1 or nb1 <= b0:
                break
            b0, b1 = max(b0, nb0), min(b1, nb1)
            j += 1
        if (j - first) * bin_width >= min_corridor_width and b1 - b0 >= min_bands:
            corridors.append((first, j, b0, b1))
        i = j if j > i else i + 1

    if not corridors:
        return []

    groups: list[list[tuple[int, int, int, int]]] = []
    for corridor in sorted(corridors, key=lambda c: c[2]):
        for group in groups:
            if any(corridor[2] < g[3] and corridor[3] > g[2] for g in group):
                group.append(corridor)
                break
        else:
            groups.append([corridor])

    regions: list[BBox] = []
    for group in groups:
        b0 = min(c[2] for c in group)
        b1 = max(c[3] for c in group)
        members = [line for band in bands[b0:b1] for line in band]
        if not members:
            continue
        regions.append(
            (
                min(min(p.bbox[0] for p in line.primitives) for line in members),
                min(min(p.bbox[1] for p in line.primitives) for line in members),
                max(max(p.bbox[2] for p in line.primitives) for line in members),
                max(max(p.bbox[3] for p in line.primitives) for line in members),
            )
        )
    return regions


# ------------------------------------------------------- 1-bis. la riparazione


def repair_region_x(page: NormalizedPrimitivePage, bbox: BBox) -> BBox:
    """Allarga la regione in x finche' non taglia piu' nessuna riga a meta'.

    Il principio e' di conservazione, non di geometria: **una riga di sorgente che
    COMINCIA dentro la regione le appartiene, e la regione deve contenerla
    intera**. Oggi non e' cosi' -- su Dag idx 136 la regione `text/lines` si ferma
    a `x1=234,6` e lascia fuori tutta la colonna DESCRIZIONE, e su DB idx 75 sei
    righe escono dal bordo destro e diventano paragrafi sciolti dopo la tabella.

    Si itera perche' allargare puo' far entrare righe che cominciano nella parte
    nuova; converge quando nessuna riga sporge.
    """

    x0, y0, x1, y1 = bbox
    for _ in range(8):
        grown_x0, grown_x1 = x0, x1
        for line in _lines_in_region(page, (x0, y0, x1, y1)):
            grown_x0 = min(grown_x0, min(p.bbox[0] for p in line.primitives))
            grown_x1 = max(grown_x1, max(p.bbox[2] for p in line.primitives))
        if grown_x0 >= x0 - 0.01 and grown_x1 <= x1 + 0.01:
            break
        x0, x1 = grown_x0, grown_x1
    return (x0, y0, x1, y1)


def _row_clusters(lines: Sequence[_SourceLine]) -> list[list[_SourceLine]]:
    """Righe candidate: righe di sorgente che si sovrappongono in y.

    Stesso ancoraggio alla prima riga usato per le righe di tabella, per la stessa
    ragione: estendere il fondo concatena per transitivita'.
    """

    if not lines:
        return []
    ordered = sorted(lines, key=lambda line: min(p.bbox[1] for p in line.primitives))
    clusters = [[ordered[0]]]
    anchor_bottom = [max(p.bbox[3] for p in ordered[0].primitives)]
    for line in ordered[1:]:
        if min(p.bbox[1] for p in line.primitives) < anchor_bottom[-1] - 1.0:
            clusters[-1].append(line)
        else:
            clusters.append([line])
            anchor_bottom.append(max(p.bbox[3] for p in line.primitives))
    return clusters


def _respects(
    cluster: Sequence[_SourceLine],
    bounds: Sequence[tuple[float, float]],
    *,
    in_column: bool = True,
) -> bool:
    """Ogni riga del cluster cade dentro una colonna: la riga rispetta la griglia.

    Il predicato di AMMISSIONE e quello di ASSEGNAZIONE devono essere lo stesso,
    altrimenti si ammette una riga che poi diventa residuo, o si scarta una riga
    che sarebbe stata collocata bene. E' successo due volte:

    - la prima versione chiedeva che la riga ATTRAVERSASSE il gutter, piu' debole
      della persistenza, e su Lan idx 118 ammetteva righe che cominciano dentro
      il corridoio: tre gutter su quattro morivano e la tabella passava da 5
      colonne a 2;
    - la seconda chiedeva di non TOCCARE il gutter, piu' forte
      dell'assegnazione, e teneva fuori l'INTESTAZIONE di DB idx 75, le cui
      etichette sono composte piu' larghe del corpo (`IMP.` sta a
      `x164,4-182,6`, sopra i gutter `159-166` e `181-195`).

    Ora e' `_column_of` sulle colonne vere, quelle prese dal centro del gutter.
    """

    if in_column:
        return all(_column_of(line, bounds) is not None for line in cluster)
    for line in cluster:
        a = min(p.bbox[0] for p in line.primitives)
        b = max(p.bbox[2] for p in line.primitives)
        for left, right in zip([b0 for _, b0 in bounds][:-1], [a0 for a0, _ in bounds][1:], strict=False):
            if a < right and b > left:
                return False
    return True


def repair_region_y(
    page: NormalizedPrimitivePage, bbox: BBox, *, admit_in_column: bool = True
) -> BBox:
    """Estende e ritira la regione in y sulle righe che rispettano le colonne.

    Le colonne si calcolano una volta sul seme, poi si guarda **una riga alla
    volta** sopra e sotto: una riga che non attraversa nessun gutter appartiene
    alla tabella, una che ne attraversa uno la chiude. E' cio' che recupera
    l'INTESTAZIONE -- su DB idx 75 rispetta tutti e otto i gutter -- e cio' che
    tiene fuori la prosa introduttiva, che li attraversa tutti.

    Si ferma alla prima riga che non rispetta: e' una corsa contigua, non una
    selezione sparsa.
    """

    seed_lines = _lines_in_region(page, bbox)
    if len(seed_lines) < 2:
        return bbox
    gutters = table_column_gutters(seed_lines, bbox)
    if not gutters:
        return bbox
    bounds = bounds_from_gutters(bbox, gutters, at_middle=admit_in_column)

    page_lines = [
        line
        for line in _row_clusters(
            _lines_in_region(page, (bbox[0], 0.0, bbox[2], page.page_geometry.height))
        )
    ]
    inside = [
        index
        for index, cluster in enumerate(page_lines)
        if any(
            bbox[1] <= (min(p.bbox[1] for p in line.primitives)
                        + max(p.bbox[3] for p in line.primitives)) / 2.0 <= bbox[3]
            for line in cluster
        )
    ]
    if not inside:
        return bbox

    first, last = inside[0], inside[-1]
    while first > 0 and _respects(page_lines[first - 1], bounds, in_column=admit_in_column):
        first -= 1
    while last + 1 < len(page_lines) and _respects(page_lines[last + 1], bounds, in_column=admit_in_column):
        last += 1

    kept = [line for cluster in page_lines[first : last + 1] for line in cluster]
    if not kept:
        return bbox
    return (
        bbox[0],
        min(min(p.bbox[1] for p in line.primitives) for line in kept),
        bbox[2],
        max(max(p.bbox[3] for p in line.primitives) for line in kept),
    )


# ------------------------------------------------- 2. le righe e il testo cella


def _column_of(line: _SourceLine, bounds: Sequence[tuple[float, float]]) -> int | None:
    lx0 = min(p.bbox[0] for p in line.primitives)
    lx1 = max(p.bbox[2] for p in line.primitives)
    for index, (left, right) in enumerate(bounds):
        if lx0 >= left - 0.5 and lx1 <= right + 0.5:
            return index
    return None


def build_rows_ad_hoc(
    lines: Sequence[_SourceLine],
    bounds: Sequence[tuple[float, float]],
    *,
    multi_column: bool = True,
    align_top: bool = False,
) -> tuple[list[list[str]], list[_SourceLine]]:
    """Righe della tabella con la regola ad hoc per gli «a capo».

    Dentro una cella **un ritorno a capo non e' mai un paragrafo nuovo**:
    `breaks_paragraph` e' la regola giusta per la prosa e sbagliata qui, ed e' la
    ragione per cui `Ogg. Contundente,` / `Leggero` restava spezzato -- `Leggero`
    e' maiuscolo, quindi la regola della prosa apre un paragrafo.

    Quando una riga di sorgente e' una continuazione, e non una riga nuova, si
    decide **geometricamente e senza soglie**: si raggruppano le righe che si
    sovrappongono in y (le righe candidate), e una riga candidata che porta
    contenuto **solo in colonne gia' piene** nella riga corrente e' la
    continuazione di quelle celle. Una riga vera porta contenuto in almeno una
    colonna ancora vuota.

    La giunzione resta `join_lines`, che e' la stessa del produttore di Markdown
    e porta con se' la sdrucciolatura del trattino a fine riga.
    """

    placed: list[tuple[int, _SourceLine]] = []
    residuals: list[_SourceLine] = []
    for line in lines:
        column = _column_of(line, bounds)
        if column is None:
            residuals.append(line)
        else:
            placed.append((column, line))
    if not placed:
        return [], residuals

    def top(line: _SourceLine) -> float:
        return min(p.bbox[1] for p in line.primitives)

    def bottom(line: _SourceLine) -> float:
        return max(p.bbox[3] for p in line.primitives)

    ordered = sorted(placed, key=lambda item: top(item[1]))

    # righe candidate: righe di sorgente che si sovrappongono in y
    # Il confine si misura sulla PRIMA riga del cluster, non sul suo massimo:
    # estendere il fondo a ogni aggiunta concatena per transitivita' (A tocca B,
    # B tocca C, e tre righe di tabella diventano una). Misurato su Fab idx 52,
    # dove `Evitare`, la sua continuazione e `Anticipare` finivano in una cella.
    if align_top:
        # Celle ALLINEATE IN ALTO: una riga di tabella e' l'insieme delle righe di
        # sorgente che COMINCIANO alla stessa altezza, entro un'interlinea.
        # Serve dove la cella lunga e' allineata in alto e l'etichetta di riga e'
        # centrata: su Dag idx 136 la descrizione della riga 53 comincia SOPRA il
        # suo `53`, e con l'aggancio al fondo finiva nella cella della riga 52.
        heights = sorted(bottom(line) - top(line) for _, line in ordered)
        line_height = heights[len(heights) // 2] if heights else 0.0
        clusters = [[ordered[0]]]
        anchor_top = [top(ordered[0][1])]
        for column, line in ordered[1:]:
            if top(line) - anchor_top[-1] < line_height:
                clusters[-1].append((column, line))
            else:
                clusters.append([(column, line)])
                anchor_top.append(top(line))
    else:
        clusters = [[ordered[0]]]
        anchor_bottom = [bottom(ordered[0][1])]
        for column, line in ordered[1:]:
            if top(line) < anchor_bottom[-1] - 1.0:
                clusters[-1].append((column, line))
            else:
                clusters.append([(column, line)])
                anchor_bottom.append(bottom(line))

    rows: list[dict[int, str]] = []
    for cluster in clusters:
        columns_here = {column for column, _ in cluster}
        # Regola ad hoc, deliberatamente STRETTA: solo un cluster che porta
        # contenuto in UNA colonna sola, gia' piena nella riga sopra, e' un «a
        # capo» dentro quella cella. Misurato sulle quattro tabelle di prova: su
        # tre di esse i cluster a una colonna sono ZERO -- le righe che vanno a
        # capo sono gia' assorbite dal raggruppamento in y, perche' le celle
        # accanto sono alte -- quindi li' la regola non puo' fare danno. Su DB
        # idx 75 ce ne sono 7 e sono esattamente le continuazioni.
        # Il caso che la regola sbaglierebbe e' una riga di tabella vera con
        # contenuto in una colonna sola: su queste quattro pagine non compare, e
        # `Fattura Magistrale` (colonne 0, 6, 8) non la attiva.
        # Continuazione se TUTTE le colonne del cluster sono gia' piene e almeno
        # una prosegue il paragrafo della sua cella. Una riga nuova apre una
        # colonna vuota, oppure comincia da capo in tutte -- `Fattura Magistrale`
        # su DB idx 75 porta `Fattura Magistrale`, `x10` e `Riduce il requisito`,
        # e nessuna delle tre prosegue, quindi resta una riga sua.
        # Due vie, ed e' l'UNIONE perche' nessuna delle due copre l'altra:
        #  - UNA colonna sola gia' piena: prende `Pesante` (maiuscolo) e
        #    `3, aumenta l'integrita' di 3` (comincia per cifra), che la regola
        #    del paragrafo scarterebbe entrambi;
        #  - piu' colonne, se almeno una prosegue: prende `Leggero`+`lanciato`,
        #    dove due celle vanno a capo insieme e solo la seconda e' minuscola.
        # `Fattura Magistrale` porta tre colonne e nessuna prosegue: resta riga sua.
        continuation = bool(rows) and columns_here <= set(rows[-1])
        if continuation and len(columns_here) > 1 and not multi_column:
            continuation = False
        if continuation and len(columns_here) > 1:
            continuation = any(
                not breaks_paragraph(rows[-1][column], line.text.strip())
                for column, line in cluster
                if line.text.strip()
            )
        target = rows[-1] if continuation else {}
        for column, line in sorted(cluster, key=lambda item: min(p.bbox[0] for p in item[1].primitives)):
            text = line.text.strip()
            if not text:
                continue
            target[column] = join_lines(target[column], text) if column in target else text
        if not continuation and target:
            rows.append(target)

    grid = [[row.get(index, "") for index in range(len(bounds))] for row in rows]
    return grid, residuals


def _spine_column(
    placed: Sequence[tuple[int, _SourceLine]], column_count: int
) -> int | None:
    """La colonna che scandisce le righe: quella dal passo verticale mediano piu' largo.

    In una tabella la colonna delle etichette ha una riga di sorgente per riga di
    tabella, quindi il salto fra le sue righe e' il passo della tabella; una
    colonna di descrizione va a capo, e il salto fra le sue righe e'
    l'interlinea. Si prende il massimo, senza soglie.

    **Regge sulle cinque pagine di sviluppo e CADE sulla prima non vista**: su Lan
    idx 284 vince la colonna delle CATEGORIE (ARTIGLIERIA, ASSALTO, CONTROLLO,
    ...), che ha cinque voci e il passo piu' ampio, e la tabella esce con 5 righe
    invece di 34. Il passo largo identifica la colonna piu' SPARSA, non quella
    delle etichette.

    Due sostituzioni provate e cadute a loro volta, registrate perche' non
    vengano riprovate:

    - **non va mai a capo (interlinea vs altezza dei glifi), poi piu' ancore**:
      su DB idx 75 la colonna QUALITA' passa il test, perche' li' l'interlinea
      dentro la cella e' piu' larga dell'altezza dei glifi. 40 righe invece di 31;
    - **piu' ancore, non piu' delle bande y della regione**: le bande contate su
      righe scaglionate sono troppe e non vincolano nulla. DB idx 75 resta a 40 e
      Dag idx 136 peggiora a 31+15 da 18+10.

    Tre criteri caduti su questa sola scelta. La conclusione **non e' un quarto
    criterio**: e' che «quale colonna scandisce le righe» non si decide dalla
    geometria della colonna presa da sola.
    """

    best: tuple[float, int] | None = None
    for column in range(column_count):
        centres = sorted(
            (min(p.bbox[1] for p in line.primitives) + max(p.bbox[3] for p in line.primitives))
            / 2.0
            for index, line in placed
            if index == column
        )
        if len(centres) < 2:
            continue
        gaps = sorted(b - a for a, b in zip(centres, centres[1:], strict=False))
        median = gaps[len(gaps) // 2]
        if best is None or median > best[0]:
            best = (median, column)
    return None if best is None else best[1]


def build_rows_from_spine(
    lines: Sequence[_SourceLine], bounds: Sequence[tuple[float, float]]
) -> tuple[list[list[str]], list[_SourceLine]]:
    """Righe scandite dalla colonna delle etichette, senza euristiche di continuazione.

    Ogni riga della colonna scelta e' l'ancora di una riga di tabella; i confini
    fra righe stanno a **meta' strada** fra due ancore consecutive, e ogni altra
    riga di sorgente va nella riga il cui intervallo contiene il suo centro.

    E' un modello diverso, non un aggiustamento: sparisce del tutto la domanda
    «questa riga e' una continuazione?», che nelle versioni precedenti sbagliava
    in due modi opposti -- inghiottiva l'inizio della cella successiva su Dag idx
    136, dove la descrizione comincia SOPRA la sua etichetta, e spezzava
    `Ogg. Contundente,` / `Leggero` su DB idx 75.

    Il caso che questo modello sbaglia, dichiarato: una tabella in cui **nessuna**
    colonna ha una riga sola per riga di tabella. Li' l'ancora va a capo e si
    inventa una riga che non c'e'.
    """

    placed: list[tuple[int, _SourceLine]] = []
    residuals: list[_SourceLine] = []
    for line in lines:
        column = _column_of(line, bounds)
        if column is None:
            residuals.append(line)
        else:
            placed.append((column, line))
    if not placed:
        return [], residuals

    spine = _spine_column(placed, len(bounds))
    if spine is None:
        return [], residuals

    def centre(line: _SourceLine) -> float:
        return (
            min(p.bbox[1] for p in line.primitives) + max(p.bbox[3] for p in line.primitives)
        ) / 2.0

    anchors = sorted(centre(line) for column, line in placed if column == spine)
    edges = [
        (a + b) / 2.0 for a, b in zip(anchors, anchors[1:], strict=False)
    ]

    def row_of(line: _SourceLine) -> int:
        y = centre(line)
        index = 0
        while index < len(edges) and y >= edges[index]:
            index += 1
        return index

    cells: dict[tuple[int, int], list[_SourceLine]] = {}
    for column, line in placed:
        cells.setdefault((row_of(line), column), []).append(line)

    grid: list[list[str]] = []
    for row in range(len(anchors)):
        values: list[str] = []
        for column in range(len(bounds)):
            members = sorted(cells.get((row, column), ()), key=centre)
            text = ""
            for line in members:
                piece = line.text.strip()
                if not piece:
                    continue
                text = join_lines(text, piece) if text else piece
            values.append(text)
        grid.append(values)
    return grid, residuals


def to_markdown(grid: Sequence[Sequence[str]]) -> str:
    if not grid:
        return ""
    width = len(grid[0])
    out = ["| " + " | ".join(c or " " for c in grid[0]) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    for row in grid[1:]:
        out.append("| " + " | ".join(c or " " for c in row) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------- il giro


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--index", type=int, required=True, help="indice 0-based")
    parser.add_argument(
        "--region",
        choices=("lines", "text-lines", "band", "auto", "corridor"),
        default="lines",
        help=(
            "da dove prendere la regione supposta tabella: le due strategie "
            "pdfplumber, oppure le bande di `column_band` ritagliate all'inchiostro"
        ),
    )
    parser.add_argument("--min-persistence", type=float, default=1.0)
    parser.add_argument("--bounds", choices=("middle", "edge"), default="middle")
    parser.add_argument(
        "--rows", choices=("spine", "union", "strict"), default="spine"
    )
    parser.add_argument("--align", choices=("top", "overlap"), default="overlap")
    parser.add_argument("--admit", choices=("in-column", "no-touch"), default="in-column")
    parser.add_argument(
        "--repair",
        choices=("none", "x", "y", "xy"),
        default="xy",
        help="ripara la regione: x = non tagliare righe a meta'; y = corsa di "
             "righe che rispettano le colonne; xy = prima y, poi x",
    )
    args = parser.parse_args()

    document = fitz.open(args.pdf)
    page = document[args.index]
    capture = capture_pymupdf_page(
        page,
        source_id="prototype-table",
        page_id=f"page:{args.index + 1:04d}",
        capture_id=f"prototype:{args.index + 1:04d}",
    )
    primitive_page = normalize_backend_page_capture(capture)

    if args.region == "corridor":
        regions = regions_from_corridors(primitive_page)
    elif args.region == "auto":
        regions = regions_from_gutter_runs(primitive_page)
    elif args.region == "band":
        regions = _regions_from_bands(primitive_page)
    else:
        settings = LINES if args.region == "lines" else TEXT_LINES
        plumber_page = pdfplumber.open(args.pdf).pages[args.index]
        regions = [
            tuple(float(v) for v in t.bbox)
            for t in plumber_page.find_tables(table_settings=settings)
        ]
    regions = [r for r in regions if r[2] > r[0] and r[3] > r[1]]
    if not regions:
        print("nessuna regione con questa strategia")
        return

    for order, seed in enumerate(regions):
        bbox = seed
        if args.repair in ("y", "xy"):
            bbox = repair_region_y(
                primitive_page, bbox, admit_in_column=args.admit == "in-column"
            )  # type: ignore[arg-type]
        if args.repair in ("x", "xy"):
            bbox = repair_region_x(primitive_page, bbox)  # type: ignore[arg-type]
        if args.repair != "none" and bbox != seed:
            print(f"    regione riparata: {tuple(round(v, 1) for v in seed)} "
                  f"-> {tuple(round(v, 1) for v in bbox)}")
        lines = _lines_in_region(primitive_page, bbox)  # type: ignore[arg-type]
        if len(lines) < 2:
            continue
        gutters = table_column_gutters(
            lines, bbox, min_persistence=args.min_persistence  # type: ignore[arg-type]
        )
        bounds = bounds_from_gutters(
            bbox, gutters, at_middle=args.bounds == "middle"
        )  # type: ignore[arg-type]
        print(f"\n=== regione {order}: {bbox} — {len(lines)} righe di sorgente")
        print(f"    gutter (persistenza {args.min_persistence:.0%}): "
              f"{[f'{a:.0f}-{b:.0f}' for a, b in gutters]}")
        print(f"    colonne: {len(bounds)}")
        if len(bounds) < 2:
            print("    < 2 colonne, non una tabella con questa regola")
            continue
        if args.rows == "spine":
            grid, residuals = build_rows_from_spine(lines, bounds)
        else:
            grid, residuals = build_rows_ad_hoc(
                lines,
                bounds,
                multi_column=args.rows == "union",
                align_top=args.align == "top",
            )
        print(f"    righe di tabella: {len(grid)}   residui fuori colonna: {len(residuals)}")
        print()
        print(to_markdown(grid))
        if residuals:
            print("\n    RESIDUI (righe che attraversano un gutter):")
            for line in residuals[:8]:
                print(f"      {line.text.strip()[:90]}")


if __name__ == "__main__":
    main()
