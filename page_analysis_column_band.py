"""Producer `layout.column_band`: le bande di colonne come `RegionCandidate`.

Contratto di Milestone 33: un `RegionCandidate` minimale per banda
(`proposed_structural_kind="layout.column_band"`), cardinalita' multipla gia'
ammessa da `page_analysis_model.py`. Nessuna modifica a `RegionCandidate` o
`PageAnalysis`.

Il meccanismo e' quello della Fase 4 della diagnostica pre-milestone, chiusa il
16 agosto 2026: i confini delle bande sono **ricavati dal documento**, non da
soglie fissate. L'idea e' rovesciare la domanda -- invece di "questo gap e' largo
almeno N punti e persiste sull'M% della pagina", si chiede quale intervallo x
resti scoperto scendendo lungo y, e **l'estensione verticale del gutter e' essa
stessa il confine della banda**. Cadono il support ratio (non c'e' piu' un
denominatore di pagina) e la soglia di larghezza (spazio fra parole e gutter non
si distinguono per larghezza -- 8pt su Dag -- ma per persistenza verticale).

I criteri di ammissione non sono soglie geometriche in punti:

  `too_few_lines`        meno di due righe distinte per lato; i fianchi di solo
                         testo ruotato non contano;
  `too_few_wordy_lines`  meno di due righe per lato che portino almeno
                         `min_flanking_chars` caratteri -- vincolo tipografico:
                         non si va a capo dopo una lettera o un articolo;
  `too_short`            gutter piu' basso di `min_gutter_lines` righe DELLA
                         PAGINA, con l'interlinea mediana come unita'.

La segmentazione e' gerarchica (`_segment_tree`): i gutter massimali definiscono
le bande di primo livello e ogni colonna riceve ricorsivamente i gutter
contenuti in essa, con estensione x esplicita. L'invariante dichiarato e' che
ogni gutter accettato compaia una volta nell'albero **oppure porti un'etichetta
di scarto** -- non-silenziosita', non conservazione incondizionata.

DIFETTI NOTI EREDITATI dalla diagnostica, scritti qui perche' non si perdano:
la collocazione del subordinato dentro una colonna del padre decide ancora sullo
`span` e non sugli estremi probatori (`_segment_tree`, filtro dei subordinati),
mentre `_is_subordinate` e' passata ai probatori -- due meta' della stessa
decisione con due grandezze diverse, misurate su 10 casi in 7 pagine di cui sei
si leggono comunque bene; e l'identita' di un gutter nell'uscita e' il suo
intervallo x, che gutter distinti possono condividere.
"""

from __future__ import annotations

from typing import cast

from geometry_model import BBox
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive

_PRODUCER_NAME = "page_analysis.column_band"
_STRUCTURAL_KIND = "layout.column_band"
_PRODUCER_VERSION = "0.1"
# I confini sono ricavati dal documento, non fissati: la configurazione e' la
# forma dei criteri, non un insieme di soglie in punti.
_CONFIGURATION_ID = "column_band:derived_gutters:v1"

import re  # noqa: E402  (accanto alla costante che lo usa)

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s\d+$")


def _visible_bbox(
    bbox: BBox,
    *,
    page_width: float,
    page_height: float,
) -> BBox | None:
    """Il bbox ritagliato alla pagina, `None` se non ne resta area.

    Identica alla versione gia' presente in `page_analysis_page_covering_visual`,
    `page_analysis_primitive_extent` e `page_analysis_primitive_pair_measurements`
    -- quattro copie nel repo, che e' il precedente esistente e non una scelta
    presa qui. La diagnostica la importava da uno script; un modulo di produzione
    non puo' dipendere da `scripts/`.
    """

    x0 = max(0.0, bbox[0])
    y0 = max(0.0, bbox[1])
    x1 = min(page_width, bbox[2])
    y1 = min(page_height, bbox[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1, y1)


class _Group:
    __slots__ = ("block_index", "line_index", "bboxes", "primitive_ids", "y0", "y1")

    def __init__(self, block_index: int, line_index: int) -> None:
        self.block_index = block_index
        self.line_index = line_index
        self.bboxes: list[BBox] = []
        self.primitive_ids: list[str] = []
        self.y0 = float("inf")
        self.y1 = float("-inf")

    def add(self, bbox: BBox, primitive_id: str) -> None:
        self.bboxes.append(bbox)
        self.primitive_ids.append(primitive_id)
        self.y0 = min(self.y0, bbox[1])
        self.y1 = max(self.y1, bbox[3])


def _group_by_pymupdf_line(
    text_primitives: list[TextPrimitive],
    *,
    page_width: float,
    page_height: float,
) -> tuple[list[_Group], int]:
    """Le righe della sorgente: un gruppo per `(block_index, line_index)`.

    La riga tipografica **non si ricostruisce geometricamente**: sta gia'
    nell'id di osservazione che `pymupdf_capture` scrive per ogni span
    (`text:b{block}:l{line}:s{span}`). Qui si legge, e basta.

    Questa funzione arriva dal prototipo della Fase 1/2, il cui meccanismo di
    banding e' stato scartato -- ma questo strato non ne faceva parte: gia'
    allora leggeva la riga dall'id, che e' l'assunto su cui il rework si e' poi
    assestato. E' l'unica parte di quel prototipo sopravvissuta, e sopravvive
    perche' era gia' giusta.

    Le bbox sono ritagliate alla pagina; una primitiva interamente fuori dal
    foglio viene scartata e non contata fra le non interpretabili, che sono
    un'altra cosa (id in un formato che non riconosciamo).
    """

    groups: dict[tuple[int, int], _Group] = {}
    unparsed = 0
    for primitive in text_primitives:
        visible = _visible_bbox(primitive.bbox, page_width=page_width, page_height=page_height)
        if visible is None:
            continue
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed += 1
            continue
        key = (int(match.group(1)), int(match.group(2)))
        group = groups.setdefault(key, _Group(*key))
        group.add(visible, primitive.primitive_id)
    return list(groups.values()), unparsed


_DEFAULT_BIN_WIDTH_X = 1.0
_DEFAULT_BIN_HEIGHT_Y = 2.0

_DEFAULT_MIN_FLANKING_GROUPS = 2
_DEFAULT_MIN_FLANKING_CHARS = 5
_DEFAULT_MIN_GUTTER_LINES = 3.0
_DEFAULT_MIN_COLUMN_CHARS = 10.0
_AVERAGE_CHAR_WIDTH_RATIO = 0.5

_COVERED = 0
_GAP = 1
_NO_TEXT = 2


class _GapRect:
    """Un candidato gutter: intervallo x contiguo, esteso su un intervallo y."""

    __slots__ = ("x_bin_start", "x_bin_end", "y0", "y1", "span_y0", "span_y1", "tree_status")

    def __init__(self, x_bin_start: int, x_bin_end: int, y0: float, y1: float) -> None:
        self.x_bin_start = x_bin_start
        self.x_bin_end = x_bin_end
        # y0/y1: fascia in cui il gutter e' EVIDENZIATO, cioe' dove entrambi i
        # lati sono attivi insieme. E' la grandezza usata dai criteri di
        # ammissione, e non va toccata: allungarla gonfierebbe i conteggi di
        # fianco e falserebbe `too_short`.
        self.y0 = y0
        self.y1 = y1
        # span_y0/span_y1: fin dove la SEPARAZIONE vale, cioe' finche' il
        # corridoio non viene attraversato. E' la grandezza usata dalle bande.
        self.span_y0 = y0
        self.span_y1 = y1
        self.tree_status = ""


def _build_gap_grid(
    groups: list[_Group],
    *,
    page_width: float,
    page_height: float,
    bin_width_x: float,
    bin_height_y: float,
) -> tuple[list[bytearray], int, int]:
    """Griglia a tre stati: `grid[y_bin][x_bin]` vale
    ``_COVERED`` (testo qui), ``_GAP`` (testo su questa fetta y, ma non in
    questa x) o ``_NO_TEXT`` (nessun testo su questa fetta y).

    Il terzo stato non e' un dettaglio implementativo. Con due soli stati
    l'interlinea fra due righe consecutive -- dove nessun gruppo e' attivo --
    verrebbe marcata "non gap" e spezzerebbe ogni gutter a ogni riga: un gutter
    di 20 righe risulterebbe come venti frammenti da un'interlinea l'uno.
    ``_NO_TEXT`` e' trasparente per la continuita' verticale (la run prosegue)
    ma non contribuisce all'estensione, che viene ritagliata sulle sole fette
    con testo. Cosi' l'interlinea non spezza il gutter e una zona senza testo
    (un'illustrazione a piena larghezza) non lo allunga artificialmente."""

    n_x_bins = max(1, int(page_width / bin_width_x) + 1)
    n_y_bins = max(1, int(page_height / bin_height_y) + 1)
    grid: list[bytearray] = []

    for y_bin_index in range(n_y_bins):
        y = y_bin_index * bin_height_y
        # Default ``_NO_TEXT``: tutto cio' che sta FUORI dall'inviluppo x dei
        # gruppi attivi non e' "coperto", e' semplicemente senza testo. La
        # distinzione conta: su una fetta y dove e' attiva solo la riga della
        # colonna sinistra (le righe delle due colonne quasi mai coincidono in
        # y, v. dump_group_persistence_curve.py), la x del gutter cade fuori
        # dall'inviluppo. Marcarla ``_COVERED`` spezzerebbe il gutter proprio
        # sulle fette che lo attraversano.
        row = bytearray([_NO_TEXT]) * n_x_bins
        active = [g for g in groups if g.y0 <= y < g.y1]
        if not active:
            grid.append(row)
            continue

        eligible_x0 = min(min(bbox[0] for bbox in g.bboxes) for g in active)
        eligible_x1 = max(max(bbox[2] for bbox in g.bboxes) for g in active)
        start_bin = max(0, int(eligible_x0 // bin_width_x))
        end_bin = min(n_x_bins - 1, int(eligible_x1 // bin_width_x))
        if start_bin > end_bin:
            grid.append(row)
            continue

        covered = bytearray(end_bin - start_bin + 1)
        for group in active:
            for bbox in group.bboxes:
                b_start = max(start_bin, int(bbox[0] // bin_width_x))
                b_end = min(end_bin, int(bbox[2] // bin_width_x))
                for x_bin in range(b_start, b_end + 1):
                    covered[x_bin - start_bin] = 1

        for offset, is_covered in enumerate(covered):
            row[start_bin + offset] = _COVERED if is_covered else _GAP
        grid.append(row)

    return grid, n_x_bins, n_y_bins


class _FlankingProfile:
    """Cosa sta ai due lati di un gutter, entro la sua estensione y."""

    __slots__ = (
        "left",
        "right",
        "left_rotated",
        "right_rotated",
        "left_width_median",
        "right_width_median",
        "left_chars_median",
        "right_chars_median",
        "left_wordy",
        "right_wordy",
    )

    def __init__(
        self,
        left: int,
        right: int,
        left_rotated: int,
        right_rotated: int,
        left_width_median: float,
        right_width_median: float,
        left_chars_median: float,
        right_chars_median: float,
        left_wordy: int,
        right_wordy: int,
    ) -> None:
        self.left = left
        self.right = right
        self.left_rotated = left_rotated
        self.right_rotated = right_rotated
        self.left_width_median = left_width_median
        self.right_width_median = right_width_median
        self.left_chars_median = left_chars_median
        self.right_chars_median = right_chars_median
        self.left_wordy = left_wordy
        self.right_wordy = right_wordy

    @property
    def minimum(self) -> int:
        return min(self.left, self.right)

    @property
    def wordy_minimum(self) -> int:
        """Quante righe, sul lato piu' povero, portano almeno il minimo di
        caratteri richiesto. Sostituisce la MEDIANA dei caratteri, che era il
        difetto: su una pagina a elenco puntato PyMuPDF indicizza ogni
        marcatore come una riga di un carattere, e su DIE p.127 i marcatori
        bastavano a trascinare la mediana a 1 e a far scartare un gutter alto
        668pt con 102 righe a sinistra e 70 a destra. Abbassare la soglia non
        serviva -- a 2 la pagina cadeva lo stesso. Contare le righe che portano
        parole risponde alla domanda giusta: c'e' testo vero da entrambe le
        parti?"""

        return min(self.left_wordy, self.right_wordy)



def _rotated_group_ids(
    groups: list[_Group], text_primitives: list[TextPrimitive]
) -> set[tuple[int, int]]:
    """I gruppi il cui testo e' scritto in verticale, da
    ``TextPrimitive.direction`` (il vettore `dir` di PyMuPDF, catturato in
    `pymupdf_capture.py`). Un gruppo e' ruotato se TUTTE le sue primitive lo
    sono.

    ATTENZIONE, correzione a verbale: una versione precedente di questa
    docstring affermava che ``direction`` non fosse mai stato usato. E' FALSO --
    ``_has_compatible_orientation`` (page_analysis_text_hypotheses.py:74-95, usata
    a :55, importata da page_analysis_side_band.py:18) lo consuma in produzione
    da Milestone 6, con un predicato PIU' STRETTO di questo: ammette solo
    dx circa +-1 e dy circa 0, mentre qui basta abs(dy) > abs(dx). Le due
    definizioni divergono sul testo obliquo. Vanno unificate sulla prima.

    Serve a escludere le linguette di capitolo, che sono la causa verificata
    dei falsi positivi: su DrW p.216 e Fab p.139 -- entrambe pagine a colonna
    singola che il prototipo segnalava come a due colonne -- l'unico testo
    verticale della pagina e' l'etichetta della linguetta ("Talent",
    "REGOLE"), e il gutter rilevato e' lo spazio fra quella e il corpo del
    testo. Sulle pagine dove il rilevamento e' corretto (tabella Vil p.75,
    etichette LIVELLO di DIE p.105) le primitive verticali sono ZERO: il
    criterio non le tocca.

    Non e' una soglia: l'orientamento del testo e' un fatto del documento."""

    direction_by_id = {p.primitive_id: p.direction for p in text_primitives}
    rotated: set[tuple[int, int]] = set()
    for group in groups:
        directions = [
            direction_by_id.get(primitive_id) for primitive_id in group.primitive_ids
        ]
        known = [d for d in directions if d is not None]
        if known and all(abs(d[1]) > abs(d[0]) for d in known):
            rotated.add((group.block_index, group.line_index))
    return rotated


def _reject_reason(
    profile: _FlankingProfile,
    rect: _GapRect,
    *,
    line_height: float,
    min_flanking_groups: int,
    min_gutter_lines: float,
) -> str | None:
    """Perche' questo gutter NON e' un separatore di colonna, o ``None`` se lo e'.

    Il motivo viene emesso nel dump grezzo invece di essere buttato: uno
    scarto etichettato e' materiale per i producer successivi. Un gutter con un
    solo carattere numerico per lato, per esempio, e' un forte indizio di
    TABELLA -- e' proprio la colonna dei numeri di riga -- e va passato a chi
    rileva tabelle, non perso. Lo stesso vale per le linguette di capitolo
    (fianco ruotato) e per i callout.

    Nessuno dei tre criteri e' una soglia geometrica in punti:
      - ``too_few_lines``   meno di N righe per lato: una colonna di una riga
                            non e' una colonna.
      - ``too_few_wordy_lines`` meno di N righe per lato che portino almeno M
                            caratteri: non si va a capo dopo un articolo.
      - ``too_short``       gutter piu' basso di N righe DELLA PAGINA: l'unita'
                            e' l'interlinea misurata, non una costante in pt.
    """

    # NOTA, misurata da Chat B e verificata: questo criterio non scarta MAI in
    # esclusiva. Le righe "wordy" sono un sottoinsieme di quelle contate qui e
    # usano lo stesso N, quindi `too_few_lines` implica sempre
    # `too_few_wordy_lines`: 0 scarti esclusivi su 19.939 gutter. Resta come
    # ETICHETTA, perche' distingue "zero righe da un lato" da "righe senza
    # parole" ed e' materiale per i producer a valle, ma non decide nulla.
    # Chi crede che sia questo a imporre "una colonna ha piu' di una riga" si
    # sbaglia: e' `too_short`, che misura la stessa cosa in righe di pagina.
    if profile.minimum < min_flanking_groups:
        return "too_few_lines"
    if profile.wordy_minimum < min_flanking_groups:
        return "too_few_wordy_lines"
    if line_height > 0 and (rect.y1 - rect.y0) < min_gutter_lines * line_height:
        return "too_short"
    return None


def _flanking_profile(
    groups: list[_Group],
    rect: _GapRect,
    *,
    bin_width_x: float,
    rotated_groups: set[tuple[int, int]],
    text_length_by_id: dict[str, int],
    min_chars: float = float(_DEFAULT_MIN_FLANKING_CHARS),
) -> _FlankingProfile:
    """Quante righe distinte `(block_index, line_index)` fiancheggiano il gutter
    a sinistra e a destra entro la sua estensione y, quanto sono larghe, e
    quanti blocchi PyMuPDF compaiono su entrambi i lati.

    Il conteggio delle righe e' la domanda strutturale che sostituisce la soglia
    in punti: un separatore di colonna ha molte righe per lato, uno spazio fra
    parole ne ha una, il vuoto accanto a un'immagine zero. Non ha metro esterno
    -- sono righe del documento, non frazioni di pagina.

    Gli altri due campi non servono a decidere se un gutter esiste ma a
    caratterizzare COSA separa, che il conteggio da solo non dice. Ipotesi da
    verificare, non risultati: in una tabella la colonna di sinistra e' stretta
    (numeri) e quella di destra larga; in un callout l'etichetta laterale e'
    strettissima e molto asimmetrica; in prosa a due colonne le due larghezze
    sono simili. E due colonne di prosa dovrebbero stare in blocchi PyMuPDF
    distinti, mentre le due meta' di una riga di tabella possono condividerlo."""

    gutter_x0 = rect.x_bin_start * bin_width_x
    gutter_x1 = (rect.x_bin_end + 1) * bin_width_x
    left_widths: list[float] = []
    right_widths: list[float] = []
    left_rotated = 0
    right_rotated = 0
    left_chars: list[float] = []
    right_chars: list[float] = []

    for group in groups:
        if group.y1 <= rect.y0 or group.y0 >= rect.y1:
            continue
        group_x0 = min(bbox[0] for bbox in group.bboxes)
        group_x1 = max(bbox[2] for bbox in group.bboxes)
        is_rotated = (group.block_index, group.line_index) in rotated_groups
        if group_x1 <= gutter_x0:
            if is_rotated:
                left_rotated += 1
            else:
                left_widths.append(group_x1 - group_x0)
                left_chars.append(
                    sum(text_length_by_id.get(i, 0) for i in group.primitive_ids)
                )
        elif group_x0 >= gutter_x1:
            if is_rotated:
                right_rotated += 1
            else:
                right_widths.append(group_x1 - group_x0)
                right_chars.append(
                    sum(text_length_by_id.get(i, 0) for i in group.primitive_ids)
                )

    def median(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        return ordered[len(ordered) // 2]

    return _FlankingProfile(
        left=len(left_widths),
        right=len(right_widths),
        left_rotated=left_rotated,
        right_rotated=right_rotated,
        left_width_median=median(left_widths),
        right_width_median=median(right_widths),
        left_chars_median=median(left_chars),
        right_chars_median=median(right_chars),
        left_wordy=sum(1 for n in left_chars if n >= min_chars),
        right_wordy=sum(1 for n in right_chars if n >= min_chars),
    )


def _median_font_size(text_primitives: list[TextPrimitive]) -> float:
    """Corpo del carattere mediano della pagina. Unita' del documento, da usare
    per giudicare se un gruppo fiancheggiante sia testo leggibile: un gruppo
    largo meno di un carattere non e' una colonna. Misurato, non usato ancora
    come regola."""

    sizes = sorted(p.font_size for p in text_primitives if p.font_size)
    if not sizes:
        return 0.0
    return sizes[len(sizes) // 2]


def _median_line_height(groups: list[_Group]) -> float:
    """Altezza di riga mediana della pagina, dai gruppi stessi. Serve solo come
    unita' di lettura nell'output -- non e' usata come soglia da nessuna parte."""

    heights = sorted(g.y1 - g.y0 for g in groups if g.y1 > g.y0)
    if not heights:
        return 0.0
    return heights[len(heights) // 2]


def _largest_free_run(row: bytearray, x_bin_start: int, x_bin_end: int) -> tuple[int, int] | None:
    """La run contigua piu' lunga di celle NON ``_COVERED`` dentro
    ``[x_bin_start, x_bin_end]``, o ``None`` se il tratto e' tutto coperto.

    Serve a restringere un gutter invece di chiuderlo quando del testo ne
    invade solo una parte."""

    best: tuple[int, int] | None = None
    best_length = 0
    run_start: int | None = None
    for x_bin in range(x_bin_start, x_bin_end + 1):
        if row[x_bin] != _COVERED:
            if run_start is None:
                run_start = x_bin
        elif run_start is not None:
            length = x_bin - run_start
            if length > best_length:
                best_length = length
                best = (run_start, x_bin - 1)
            run_start = None
    if run_start is not None:
        length = x_bin_end + 1 - run_start
        if length > best_length:
            best = (run_start, x_bin_end)
    return best


def _gap_intervals(row: bytearray) -> list[tuple[int, int]]:
    """Intervalli x massimali di celle ``_GAP`` su una fetta y."""

    intervals: list[tuple[int, int]] = []
    start: int | None = None
    for x_bin, state in enumerate(row):
        if state == _GAP:
            if start is None:
                start = x_bin
        elif start is not None:
            intervals.append((start, x_bin - 1))
            start = None
    if start is not None:
        intervals.append((start, len(row) - 1))
    return intervals


def _chain_gutters(grid: list[bytearray], *, bin_height_y: float) -> list[_GapRect]:
    """Incatena gli intervalli di gap lungo y, non lungo x.

    L'orientamento non e' indifferente. Un gutter e' alto e stretto: chi lo
    insegue lungo x deve intersecare le estensioni y di colonne adiacenti, e su
    prosa giustificata -- dove le righe finiscono a x leggermente diverse --
    l'intersezione collassa dopo pochi bin, spezzando un gutter di 176pt in
    frammenti da 10. Inseguendolo lungo y invece si chiede la cosa giusta: quale
    intervallo x resta gap mentre si scende.

    La x di un gutter viene ristretta all'**intersezione** degli intervalli che
    lo compongono: e' il nucleo che resta scoperto per tutta la sua estensione,
    cioe' la larghezza garantita del gutter, non la sua larghezza massima. Su
    prosa giustificata la larghezza massima e' un artefatto delle righe che
    finiscono corte a fine paragrafo.

    Un gutter resta aperto finche' la sua x e' gap oppure senza testo; si chiude
    quando del testo la attraversa. Nessuna soglia."""

    open_gutters: list[_GapRect] = []
    closed: list[_GapRect] = []

    for y_bin_index, row in enumerate(grid):
        intervals = _gap_intervals(row)
        still_open: list[_GapRect] = []
        used: set[int] = set()

        for gutter in open_gutters:
            match: tuple[int, int] | None = None
            for position, (x0_bin, x1_bin) in enumerate(intervals):
                if position in used:
                    continue
                if x0_bin <= gutter.x_bin_end and gutter.x_bin_start <= x1_bin:
                    match = (x0_bin, x1_bin)
                    used.add(position)
                    break
            if match is not None:
                gutter.x_bin_start = max(gutter.x_bin_start, match[0])
                gutter.x_bin_end = min(gutter.x_bin_end, match[1])
                gutter.y1 = (y_bin_index + 1) * bin_height_y
                still_open.append(gutter)
                continue
            # Nessun intervallo di gap combacia. Non basta chiedere se il
            # nucleo sia INTERAMENTE senza testo: quando su questa fetta e'
            # attiva una sola delle due colonne, parte del nucleo cade fuori
            # dal suo inviluppo (``_NO_TEXT``) e parte puo' essere coperta --
            # succede quando una riga della colonna destra comincia piu' a
            # sinistra di quelle che l'hanno preceduta, perche' le prime erano
            # rientrate. Misurato su Dag p.84 y 180-190, dove la regola
            # "una parte coperta, chiudi" spezzava in due un gutter che
            # visivamente e' uno solo (verificato a render).
            #
            # Il gutter va invece RISTRETTO alla sua parte ancora libera, come
            # gia' avviene quando un intervallo combacia: stesso principio del
            # nucleo garantito. Si chiude solo se non resta niente.
            survivor = _largest_free_run(
                row, gutter.x_bin_start, gutter.x_bin_end
            )
            if survivor is not None:
                gutter.x_bin_start, gutter.x_bin_end = survivor
                still_open.append(gutter)
            else:
                closed.append(gutter)

        for position, (x0_bin, x1_bin) in enumerate(intervals):
            if position not in used:
                still_open.append(
                    _GapRect(
                        x0_bin,
                        x1_bin,
                        y_bin_index * bin_height_y,
                        (y_bin_index + 1) * bin_height_y,
                    )
                )
        open_gutters = still_open

    closed.extend(open_gutters)
    return [g for g in closed if g.x_bin_end >= g.x_bin_start]


def _extend_gutter_span(
    grid: list[bytearray], rect: _GapRect, *, bin_height_y: float
) -> None:
    """Estende `span_y0`/`span_y1` finche' il corridoio non viene ATTRAVERSATO.

    La condizione di arresto e' l'interruzione, non l'assenza di testo. Una
    versione precedente si fermava dove finiva il testo che fiancheggia il
    corridoio: sbagliato, perche' usa l'assenza di prova come prova di assenza
    -- se nessuno attraversa il corridoio, la separazione fra le due colonne
    continua a esistere anche dove i due lati tacciono. Il caso che lo mostra e'
    Dag p.164, dove le ultime righe delle due colonne non si sovrappongono in y
    e la banda si fermava lasciando fuori il testo che le appartiene.

    Estendere era pericoloso finche' le bande erano piatte, perche' il consumer
    assegnava ogni primitiva alla PRIMA banda che la conteneva e una banda
    estesa svuotava le altre. Con l'albero il pericolo non c'e': l'assegnazione
    va alla banda piu' profonda."""

    start, end = rect.x_bin_start, rect.x_bin_end

    def free_row(row: bytearray, lo: int, hi: int) -> tuple[int, int] | None:
        """Il nucleo sopravvive se resta un tratto contiguo non coperto. Stesso
        principio di `_largest_free_run` durante l'incatenamento: si restringe,
        non si chiude. Su DrW p.97 il nucleo fissato sull'estensione probatoria
        e' 299-323, ma sei righe della colonna destra cominciano a 313; senza
        restringimento l'estensione si ferma a y 378 e lascia fuori 64
        primitive su 171, mentre il corridoio 299-313 e' libero su tutta la
        pagina."""

        best: tuple[int, int] | None = None
        run: int | None = None
        for x in range(lo, hi + 2):
            covered = x > hi or row[x] == _COVERED
            if not covered and run is None:
                run = x
            elif covered and run is not None:
                if best is None or (x - run) > (best[1] - best[0] + 1):
                    best = (run, x - 1)
                run = None
        return best

    top = max(0, int(rect.y0 / bin_height_y))
    while top > 0:
        survivor = free_row(grid[top - 1], start, end)
        if survivor is None:
            break
        start, end = survivor
        top -= 1
    bottom = min(len(grid), int(rect.y1 / bin_height_y))
    while bottom < len(grid):
        survivor = free_row(grid[bottom], start, end)
        if survivor is None:
            break
        start, end = survivor
        bottom += 1

    rect.x_bin_start, rect.x_bin_end = start, end
    rect.span_y0 = top * bin_height_y
    rect.span_y1 = bottom * bin_height_y


def _is_subordinate(inner: _GapRect, outer: _GapRect) -> bool:
    """`inner` vive DENTRO una colonna di `outer`: le due x sono disgiunte, le y
    si sovrappongono, e `outer` e' piu' esteso in y.

    E' un test di disgiunzione, senza soglie. Su DB p.18 il gutter di pagina
    (x 301-320, y 488-668) ha due gutter di tabella interamente alla sua destra
    (x 338-343 e x 398-446): sono subordinati, e non devono contribuire confini
    al livello superiore -- e' il taglio che spezzava il flusso della colonna
    sinistra a y 610."""

    if not (inner.x_bin_end < outer.x_bin_start or inner.x_bin_start > outer.x_bin_end):
        return False
    if (outer.y1 - outer.y0) <= (inner.y1 - inner.y0):
        return False
    # Sovrapposizione sui PROBATORI, non sullo span. `span_y0`/`span_y1` dicono
    # fin dove si PRESUME che la separazione continui; `y0`/`y1` dove e'
    # DIMOSTRATA, cioe' dove entrambi i lati sono attivi. "Questa struttura sta
    # dentro quella" e' una claim strutturale e deve poggiare sulla
    # dimostrazione -- ed e' la stessa separazione che la condizione qui sopra
    # gia' rispetta, per cui prima questa funzione misurava la stessa cosa in
    # due modi diversi al proprio interno.
    #
    # Misurato su DB p.53: il box LESIONI GRAVI (probatorio 60-120, span 46-176)
    # diventava figlio della tabella (probatorio 160-504, span 120-582) perche'
    # le estensioni colmano i quaranta punti di vuoto che separano le due
    # strutture. Da figlio ereditava come estensione x la colonna del padre,
    # cioe' un confine a 178 che nel box non esiste: cinque primitive lo
    # scavalcavano e quattro su diciassette finivano nella banda della tabella.
    return inner.y0 < outer.y1 and outer.y0 < inner.y1


def _segment_tree(
    rects: list[_GapRect],
    *,
    bin_width_x: float,
    page_width: float,
    font_size: float = 0.0,
    min_column_chars: float = _DEFAULT_MIN_COLUMN_CHARS,
) -> list[dict[str, object]]:
    """Segmentazione GERARCHICA. Le bande di primo livello nascono dai soli
    gutter massimali; ogni colonna di una banda riceve ricorsivamente i gutter
    che le stanno dentro.

    Sostituisce l'assunzione implicita che rendeva possibile il difetto: oggi
    una banda ha estensione x pari alla pagina, quindi un gutter a destra puo'
    tagliare la colonna di sinistra. Qui l'estensione x e' esplicita.

    Invariante di conservazione, il criterio di successo fissato prima di
    scrivere questa funzione: **ogni gutter accettato compare esattamente una
    volta** nell'albero. Le correzioni ovvie (fondere le bande annidate, tenere
    i soli gutter massimali) riparano DB p.18 ma SCARTANO il gutter subordinato,
    e su una pagina a 3 colonne sopra e 2 sotto perderebbero struttura vera in
    silenzio. La conservazione e' cio' che distingue la correzione dal trucco."""

    # Larghezza minima di una colonna, espressa in CARATTERI del documento e non
    # in punti: una colonna larga otto caratteri non puo' contenere prosa. Stesso
    # ragionamento tipografico di `too_few_wordy_lines` applicato alla larghezza.
    # E' un criterio di BANDA, non di gutter: ha senso solo dentro un contesto x,
    # e infatti prima della gerarchia non era calcolabile. Misurato sulle ancore:
    # le colonne vere stanno fra 40 e 78 caratteri, la linguetta di capitolo di
    # Fab p.139 a 8. Il default era 15 e una versione precedente di questo
    # commento lo diceva "dalla parte conservativa": rovesciato. Misurato sul
    # corpus da Chat B: 18 colonne VERE stanno fra 15,0 e 16,0 caratteri, quindi
    # 15 ha margine zero verso l'alto, e l'errore che produce e' un falso
    # negativo -- quello che nessun livello a valle recupera. Inoltre il modo
    # basso viene quasi tutto da un solo manuale (159 casi su 162 da Fab, la sua
    # linguetta). Portato a 10: le ancore restano identiche e il corpus perde 3
    # casi su 11.846.
    min_column_width = (
        min_column_chars * font_size * _AVERAGE_CHAR_WIDTH_RATIO if font_size > 0 else 0.0
    )

    rows: list[dict[str, object]] = []
    counter = [0]
    # Chi non entra nell'albero non sparisce: viene marcato. E' lo stesso
    # principio dello scarto etichettato dei gutter -- un bordino riconosciuto
    # come tale e' materiale per chi rileva bande di capitolo, non spazzatura.
    dropped: dict[int, str] = {}

    def wide_enough(rect: _GapRect, x0: float, x1: float) -> bool:
        """Il minimo di larghezza si applica SOLO alle colonne che toccano il
        bordo della pagina.

        Distinzione proposta dall'utente e non ovvia: una linguetta di capitolo
        produce una colonna strettissima **al bordo**, una tabella la produce
        **all'interno**. Applicare il minimo ovunque scartava anche le colonne
        di tabella (su DB p.18 la colonna "D6" e' larga 3 caratteri, su DB p.83
        le colonne di costo circa 8) e con esse la struttura che volevamo
        descrivere. Limitandolo ai bordi si tolgono i bordini senza toccare le
        tabelle."""

        if min_column_width <= 0:
            return True
        left_edge = rect.x_bin_start * bin_width_x - x0
        right_edge = x1 - (rect.x_bin_end + 1) * bin_width_x
        if x0 <= 0.5 and left_edge < min_column_width:
            return False
        return not (x1 >= page_width - 0.5 and right_edge < min_column_width)

    def emit(
        members: list[_GapRect],
        x0: float,
        x1: float,
        parent: int | None,
        depth: int,
    ) -> None:
        if not members:
            return
        usable = []
        for candidate in members:
            if wide_enough(candidate, x0, x1):
                usable.append(candidate)
            else:
                dropped[id(candidate)] = "edge_strip"
        if not usable:
            return
        maximal = [
            r for r in usable if not any(_is_subordinate(r, other) for other in usable)
        ]
        subordinate = [r for r in usable if r not in maximal]
        placed: set[int] = set()

        for band_y0, band_y1, crossing in _segment_bands(maximal, bin_width_x=bin_width_x):
            counter[0] += 1
            band_id = counter[0]
            rows.append(
                {
                    "band_id": band_id,
                    "parent_id": parent if parent is not None else "",
                    "depth": depth,
                    "x0": round(x0, 2),
                    "x1": round(x1, 2),
                    "y0": round(band_y0, 2),
                    "y1": round(band_y1, 2),
                    "column_count": len(crossing) + 1,
                    "gutter_x_intervals": " ".join(f"{a:.1f}-{b:.1f}" for a, b in crossing),
                }
            )
            bounds = [x0] + [edge for pair in crossing for edge in pair] + [x1]
            for index in range(0, len(bounds) - 1, 2):
                col_x0, col_x1 = bounds[index], bounds[index + 1]
                inside = [
                    r
                    for r in subordinate
                    if id(r) not in placed
                    and r.x_bin_start * bin_width_x >= col_x0
                    and (r.x_bin_end + 1) * bin_width_x <= col_x1
                    and r.span_y0 < band_y1
                    and band_y0 < r.span_y1
                ]
                # Un gutter appartiene a UNA colonna sola: marcarlo qui evita che
                # un subordinato con due padri possibili venga emesso due volte.
                placed.update(id(r) for r in inside)
                emit(inside, col_x0, col_x1, band_id, depth + 1)

        # I subordinati che nessuna banda ha potuto ospitare NON vanno persi.
        # La subordinazione e' una relazione globale sulla pagina, ma vale solo
        # dentro la fascia y in cui il padre esiste davvero: sotto quella fascia
        # un gutter "subordinato" e' a tutti gli effetti massimale nella propria
        # regione. Misurato su DB p.83, tre tabelle impilate con colonne a x
        # diverse: il gutter piu' alto veniva eletto padre di tutte e le altre
        # due tabelle restavano orfane. Si ricorre sullo stesso livello, con la
        # guardia che il sottoinsieme si riduca davvero per non ciclare.
        leftover = [r for r in subordinate if id(r) not in placed]
        if leftover and len(leftover) < len(usable):
            emit(leftover, x0, x1, parent, depth)

    emit(rects, 0.0, page_width, None, 0)

    # Lo stato si assegna da cio' che l'albero CONTIENE davvero, non per
    # esclusione: marcare "band" tutto cio' che non e' stato scartato
    # esplicitamente lasciava passare i gutter che nessun ramo aveva emesso
    # (53 pagine su cinque manuali). Un invariante verificato per assenza non
    # e' un invariante.
    emitted: set[str] = set()
    for row in rows:
        emitted.update(str(row["gutter_x_intervals"]).split())
    for rect in rects:
        key = f"{rect.x_bin_start * bin_width_x:.1f}-{(rect.x_bin_end + 1) * bin_width_x:.1f}"
        if key in emitted:
            rect.tree_status = "band"
        else:
            rect.tree_status = dropped.get(id(rect), "not_placed")
    return rows


def _segment_bands(
    rects: list[_GapRect], *, bin_width_x: float
) -> list[tuple[float, float, list[tuple[float, float]]]]:
    """Bande dai confini y dei gutter: ogni y in cui l'insieme dei gutter
    attivi cambia e' un confine. Nessuna griglia di banda, nessuna soglia di
    supporto -- i confini vengono dai dati."""

    if not rects:
        return []

    boundaries = sorted({rect.span_y0 for rect in rects} | {rect.span_y1 for rect in rects})
    bands: list[tuple[float, float, list[tuple[float, float]]]] = []
    for band_y0, band_y1 in zip(boundaries, boundaries[1:], strict=False):
        if band_y1 <= band_y0:
            continue
        crossing = [
            (rect.x_bin_start * bin_width_x, (rect.x_bin_end + 1) * bin_width_x)
            for rect in rects
            if rect.span_y0 <= band_y0 and rect.span_y1 >= band_y1
        ]
        if not crossing:
            continue
        bands.append((band_y0, band_y1, sorted(crossing)))
    return bands


def build_column_band_page_analysis(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    bin_width_x: float = _DEFAULT_BIN_WIDTH_X,
    bin_height_y: float = _DEFAULT_BIN_HEIGHT_Y,
    min_flanking_groups: int = _DEFAULT_MIN_FLANKING_GROUPS,
    min_flanking_chars: float = _DEFAULT_MIN_FLANKING_CHARS,
    min_gutter_lines: float = _DEFAULT_MIN_GUTTER_LINES,
    min_column_chars: float = _DEFAULT_MIN_COLUMN_CHARS,
) -> PageAnalysis:
    """Un `RegionCandidate` per banda di colonne, contratto di Milestone 33.

    Le primitive di una banda sono quelle il cui CENTRO cade nel suo rettangolo:
    stessa regola di appartenenza usata dalla diagnostica, e la condivisione di
    una primitiva fra candidati e' esplicitamente ammessa da `AGENTS.MD` §Layout
    e candidati ("le primitive possono essere condivise fra candidati; la
    condivisione non implica ownership").

    Nessuna decisione: le bande annidate sono emesse come candidati alla pari,
    perche' un `RegionCandidate` e' una proposta non approvata e la relazione fra
    candidati si decide in Resolution o nel consumer, mai qui.
    """

    if not generation_id:
        raise ValueError("generation_id must not be empty")

    tree = _column_band_tree(
        primitive_page,
        bin_width_x=bin_width_x,
        bin_height_y=bin_height_y,
        min_flanking_groups=min_flanking_groups,
        min_flanking_chars=min_flanking_chars,
        min_gutter_lines=min_gutter_lines,
        min_column_chars=min_column_chars,
    )

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    candidates: list[RegionCandidate] = []
    for row in tree:
        # Ritagliato alla pagina: l'estensione dei gutter puo' portare una banda
        # oltre il bordo (DrW p.97 arriva a y 784, Dag p.164 a 794) e un
        # candidato fuori pagina non passa `validate_page_analysis_against_primitive_page`.
        # Il ritaglio non e' una correzione del meccanismo: la banda resta quella,
        # e' la sua rappresentazione come candidato a dover stare nel foglio.
        raw = _visible_bbox(
            (
                float(cast(float, row["x0"])),
                float(cast(float, row["y0"])),
                float(cast(float, row["x1"])),
                float(cast(float, row["y1"])),
            ),
            page_width=page_width,
            page_height=page_height,
        )
        if raw is None:
            continue
        bbox: BBox = raw
        primitive_ids = tuple(
            primitive.primitive_id
            for primitive in primitive_page.text_primitives
            if bbox[0] <= (primitive.bbox[0] + primitive.bbox[2]) / 2.0 < bbox[2]
            and bbox[1] <= (primitive.bbox[1] + primitive.bbox[3]) / 2.0 < bbox[3]
        )
        if not primitive_ids:
            continue
        candidates.append(
            RegionCandidate(
                candidate_id=f"candidate:column-band:{primitive_page.page_id}:{row['band_id']}",
                page_id=primitive_page.page_id,
                bbox=bbox,
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=primitive_ids,
            )
        )

    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=_PRODUCER_NAME,
            producer_version=_PRODUCER_VERSION,
            configuration_id=_CONFIGURATION_ID,
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )


def _column_band_tree(
    primitive_page: NormalizedPrimitivePage,
    *,
    bin_width_x: float,
    bin_height_y: float,
    min_flanking_groups: int,
    min_flanking_chars: float,
    min_gutter_lines: float,
    min_column_chars: float,
) -> list[dict[str, object]]:
    """L'albero di bande, senza le etichette diagnostiche di manuale e pagina.

    E' il corpo di `_process_page` della diagnostica **al netto della cattura**:
    quella prendeva un `fitz.Document` solo per chiamare `capture_pymupdf_page`,
    e da li' in poi lavorava gia' su `NormalizedPrimitivePage`. Un producer la
    riceve, quindi il passo cade.
    """

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height
    groups, _unparsed = _group_by_pymupdf_line(
        list(primitive_page.text_primitives), page_width=page_width, page_height=page_height
    )
    if not groups:
        return []

    grid, _n_x, _n_y = _build_gap_grid(
        groups,
        page_width=page_width,
        page_height=page_height,
        bin_width_x=bin_width_x,
        bin_height_y=bin_height_y,
    )
    rects = _chain_gutters(grid, bin_height_y=bin_height_y)
    for rect in rects:
        _extend_gutter_span(grid, rect, bin_height_y=bin_height_y)
    rects.sort(key=lambda r: (r.y1 - r.y0), reverse=True)

    rotated_groups = _rotated_group_ids(groups, list(primitive_page.text_primitives))
    text_length_by_id = {
        p.primitive_id: len((p.text or "").strip()) for p in primitive_page.text_primitives
    }
    line_height = _median_line_height(groups)
    accepted = [
        rect
        for rect in rects
        if _reject_reason(
            _flanking_profile(
                groups,
                rect,
                bin_width_x=bin_width_x,
                rotated_groups=rotated_groups,
                text_length_by_id=text_length_by_id,
                min_chars=min_flanking_chars,
            ),
            rect,
            line_height=line_height,
            min_flanking_groups=min_flanking_groups,
            min_gutter_lines=min_gutter_lines,
        )
        is None
    ]
    return _segment_tree(
        accepted,
        bin_width_x=bin_width_x,
        page_width=page_width,
        font_size=_median_font_size(list(primitive_page.text_primitives)),
        min_column_chars=min_column_chars,
    )
