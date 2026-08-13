"""Prototipo: bande di colonna con confini RICAVATI dal documento, senza
soglia di larghezza del gap e senza soglia di supporto.

Non un producer. Non wired. Nessun RegionCandidate emesso. Diagnostica pura,
stesso standard degli altri prototipi di questa diagnostica.

## Il problema che prova a risolvere

Il meccanismo di Fase 2 (`prototype_column_gap_group_persistence.py`) ha due
costanti che decidono l'esito e che nessuno ha derivato:

  --min-gap-width      15pt, ereditato invariato da Milestone 32
  --min-support-ratio  0,6, applicato sull'intera altezza pagina

Misurato in sessione (v. `State.md`, "Fallimento misurato su Dag" e "Misura sul
corpus"): la prima e' SOPRA il gutter reale di Dag (9,8pt), quindi blocca a
prescindere; la seconda e' irraggiungibile sul 73-77% delle pagine con
contenuto multicolonna, perche' la regione multicolonna copre in mediana il
41-43% dell'estensione di testo della pagina. L'assunzione "una struttura di
colonna per pagina" vale sul 2,7-3,5% dei casi.

## L'idea

Le due soglie sono un sintomo dello stesso errore: si chiede "questo gap e'
abbastanza largo, e persiste abbastanza a lungo *rispetto alla pagina*?".
Entrambe le domande hanno bisogno di un metro esterno.

Qui la domanda e' rovesciata: **ogni gap definisce da se' la banda in cui
vale**. Un gap non deve persistere per una frazione della pagina -- persiste
esattamente sulla sua estensione y, e quella estensione *e'* il confine della
banda. Il taglio verticale lo decide il documento, non una costante.

Cade con essa anche la soglia di larghezza: uno spazio fra parole e un gutter
di colonna non si distinguono per larghezza (si sovrappongono: 9,8pt su Dag e'
piu' stretto di molti spazi di giustificazione) ma per **estensione verticale**.
Lo spazio fra parole si sposta a ogni riga e non persiste; il gutter resta alla
stessa x per decine di righe. Non serve una soglia in pt: serve ordinare i gap
per quanto durano.

## Il metodo

1. Gruppi `(block_index, line_index)` da `_group_by_pymupdf_line` (riusata per
   import da `prototype_column_band_producer.py`, non copiata).
2. Griglia fine x/y. Per ogni fetta y, i gruppi attivi sono quelli il cui
   inviluppo `[y0,y1]` la copre -- stessa definizione di Fase 2, deliberatamente
   invariata: cambiare due cose insieme renderebbe il confronto inutile.
   (Differenza nota da `_cluster_rows`, che usa overlap esatto di bbox: v.
   `State.md`, rischio architetturale aperto e mai stressato da un caso reale.)
3. Una cella (x_bin, y_bin) e' "gap" se non e' coperta da alcun gruppo attivo
   ED e' interna all'inviluppo x dei gruppi attivi di quella fetta -- i margini
   di pagina non sono gap.
4. Per ogni fetta y: gli intervalli x massimali di celle "gap".
5. Gli intervalli si incatenano **lungo y**, non lungo x (`_chain_gutters`):
   un gutter e' alto e stretto, e inseguirlo lungo x obbliga a intersecare le
   estensioni y di colonne adiacenti -- su prosa giustificata, dove le righe
   finiscono a x diverse, quell'intersezione collassa e spezza un gutter di
   176pt in frammenti da 10. Misurato su Dag p.84 durante la scrittura di
   questo script, non ipotizzato: due iterazioni precedenti dell'algoritmo
   fallivano cosi'.
6. La x di un gutter e' l'**intersezione** degli intervalli che lo compongono:
   il nucleo che resta scoperto per tutta la sua estensione, cioe' la larghezza
   garantita, non quella massima (che su prosa giustificata e' un artefatto
   delle righe corte a fine paragrafo). Un gutter si chiude quando del testo lo
   attraversa; una zona senza testo non lo chiude ma non ne allunga
   l'estensione.
7. Un gutter conta come separatore di colonna solo se ha almeno
   `--min-flanking-groups` righe distinte **per lato** entro la sua estensione
   y (default 2). Non e' una soglia geometrica tarabile ma un minimo
   strutturale: una colonna di una riga sola non e' una colonna, e un gap con
   zero righe da un lato non separa niente. Il criterio si conta in righe del
   documento, non in punti ne' in frazioni di pagina -- nessun metro esterno.
   Si applica solo a `--emit bands`; `--emit gutters` resta grezzo, con
   `left_groups`/`right_groups` in chiaro, cosi' il filtro si puo' sempre
   rifare a valle su output gia' raccolti.
8. Le bande si ricavano dai confini y dei gutter superstiti: ogni y in cui
   l'insieme dei gutter attivi cambia e' un confine. `column_count` di una
   banda = numero di gutter che la attraversano per intero, piu' uno.

## Stato empirico, aggiornato all'11 agosto 2026

- **Dag p.84 posizionale** (pagina stampata 82; prosa 2 colonne verificata a
  render E a ispezione visiva diretta del PDF; e' il caso su cui il meccanismo
  di Fase 2 falliva a ogni combinazione di parametri con `--min-gap-width`
  15pt): **una sola banda**, y 126-312, estensione 186pt, `column_count=2`,
  gutter a x 298-306 largo 8pt -- **sotto** la vecchia soglia -- fiancheggiato
  da 15 righe a sinistra e 16 a destra. Nessuna soglia di larghezza, nessun
  support ratio.
  L'introduzione monocolonna sopra la banda (titolo, sottotitolo, intestazione
  di sezione) non produce alcuna banda perche' non contiene gutter;
  l'illustrazione a piena larghezza sotto neppure. E' il comportamento voluto
  su una pagina a struttura mista, che e' il caso tipico e non particolare
  (v. `State.md`, "Struttura di colonna variabile dentro la stessa pagina").
- **Residuo risolto** (era: gutter spezzato in due bande, 126-172 e 192-312).
  Causa misurata, non ipotizzata: a y 180-190 e' attiva la sola colonna destra,
  la cui riga comincia a x=306,8 -- dentro il nucleo del gutter, fissato a
  298-312 perche' le righe precedenti di destra erano rientrate (312,5 e
  321,0). La regola di chiusura chiedeva che il nucleo fosse INTERAMENTE senza
  testo, e chiudeva. Ora lo restringe alla parte ancora libera (`_largest_free_run`),
  stesso principio del nucleo garantito gia' usato quando un intervallo
  combacia; chiude solo se non resta niente.
  Nota di metodo: il difetto era visibile nel render gia' disponibile e non e'
  stato riconosciuto per un giro. L'ispezione visiva va fatta, non rimandata.
- **Fab p.262 posizionale = pagina stampata 260** (scostamento +2). Ispezionata
  visivamente: **e' a COLONNA SINGOLA** -- sei riquadri numerati impilati in
  verticale, ciascuno con un numero cerchiato a sinistra. Non e' una lista a due
  colonne. Quindi `persistence`, che vi restituisce `column_count=1`, e'
  corretto, e questo prototipo con `--min-flanking-groups` >= 3 non emette
  nulla, corretto anche lui.
  A `--min-flanking-groups 2` (default) il prototipo emette pero' **un falso
  positivo**: banda y 536-566, gutter x 42-60, cioe' lo spazio fra il numero
  cerchiato e il riquadro che lo segue, con esattamente 2 righe per lato. E' il
  caso che mostra il limite del minimo strutturale a 2 -- un elemento decorativo
  affiancato a due righe di testo lo soddisfa. Una pagina non basta per
  cambiare il default: v. lo sweep sul corpus.
  **Due correzioni di versioni precedenti di questa docstring**, lasciate a
  verbale invece che cancellate, perche' sono lo stesso errore ripetuto:
  (a) in 56954f9 si affermava che `persistence` desse `column_count=2` su p.262
  e che il prototipo non lo riproducesse -- falso, dava 1;
  (b) subito dopo si affermava che su p.262 "falliscono entrambi" -- falso
  anche questo, la pagina e' a colonna singola e nessuno dei due sbaglia.
  Entrambe le affermazioni derivavano dalla narrazione di `State.md` invece che
  da una misura o da un'ispezione. `State.md` cita un caso Fab a lista numerata
  con `column_count=2` corretto ma **non dice quale pagina sia**: non e' la 262,
  e resta non identificato. E' lo stesso errore di attribuzione via `--page N`
  che `State.md` registra come rischio procedurale, commesso due volte di
  seguito nello stesso file che lo descrive.

## Cosa NON risolve, dichiarato

- L'overlap banda/`table_candidate` (Milestone 33 punto bloccante 2) e il
  confound `side_band`: intatti, come per tutti i meccanismi di questa
  diagnostica.
- `--bin-width-x` e `--bin-height-y` restano costanti di discretizzazione. Non
  sono soglie decisionali (non stabiliscono se un gap conta) ma la risoluzione
  con cui si guarda; vanno comunque verificate per sensibilita', non assunte
  innocue. Il default y (2pt) e' lo stesso di Fase 2 di proposito.
  **SMENTITO, correzione a verbale**: la revisione architetturale ha misurato
  che, avendo rimosso `--min-gap-width` senza sostituirlo, nessun criterio
  guarda piu' la larghezza -- quindi il gutter minimo rappresentabile e' un bin
  e `--bin-width-x` E' la soglia di larghezza, implicita e mai dichiarata
  (3,4% dei gutter accettati e' largo 1pt). Per `--bin-height-y` la difesa
  regge meglio: entra solo in `too_short` attraverso `line_height` misurata.
- La distinzione fra spazio fra parole e gutter e' AFFIDATA all'ordinamento per
  estensione y, non dimostrata. Se su qualche pagina uno spazio fra parole
  persistesse verticalmente il metodo lo chiamerebbe gutter.
  **NON PIU' IPOTETICO, correzione a verbale**: una versione precedente di
  questa riga diceva "caso non ancora cercato". E' stato cercato e trovato --
  3,6% dei gutter accettati e' attraversato da almeno una riga di testo che li
  scavalca, con casi verificati su DB p.120 e Wil p.160 (allineamenti
  accidentali di spazi di giustificazione dentro elenchi puntati). Il 3,6% e'
  un limite inferiore: conta solo le righe che scavalcano INTERAMENTE il gutter.

- ATTENZIONE, la sezione "Il metodo" qui sopra descrive un solo criterio di
  ammissione (`--min-flanking-groups`) mentre il codice ne ha TRE
  (`too_few_lines`, `too_few_chars`, `too_short`, v. `_reject_reason`). La
  descrizione e' rimasta indietro rispetto al meccanismo. Rilievo della
  revisione del diff, non ancora sanato riscrivendo la sezione.

Uso:

    python3 scripts/prototype_derived_column_bands.py Dag.pdf --page 84
    python3 scripts/prototype_derived_column_bands.py Dag.pdf --page 84 --emit gutters
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO, cast

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

from prototype_column_band_producer import _Group, _group_by_pymupdf_line  # noqa: E402

from primitive_model import TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH_X = 1.0
_DEFAULT_BIN_HEIGHT_Y = 2.0

_DEFAULT_MIN_FLANKING_GROUPS = 2
_DEFAULT_MIN_FLANKING_CHARS = 5
_DEFAULT_MIN_GUTTER_LINES = 3.0
_DEFAULT_MIN_COLUMN_CHARS = 15.0
_AVERAGE_CHAR_WIDTH_RATIO = 0.5

_COVERED = 0
_GAP = 1
_NO_TEXT = 2

_GUTTER_FIELDNAMES = (
    "manual",
    "page",
    "gutter_index",
    "x0",
    "x1",
    "width",
    "y0",
    "y1",
    "y_extent",
    "left_groups",
    "right_groups",
    "flanking_min",
    "left_rotated",
    "right_rotated",
    "left_width_median",
    "right_width_median",
    "shared_blocks",
    "page_line_height",
    "left_chars_median",
    "right_chars_median",
    "left_wordy",
    "right_wordy",
    "page_font_size",
    "reject_reason",
    "tree_status",
)

_TREE_FIELDNAMES = (
    "manual",
    "page",
    "band_id",
    "parent_id",
    "depth",
    "x0",
    "x1",
    "y0",
    "y1",
    "column_count",
    "gutter_x_intervals",
)

_BAND_FIELDNAMES = (
    "manual",
    "page",
    "band_index",
    "y0",
    "y1",
    "y_extent",
    "column_count",
    "gutter_x_intervals",
)


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
        "shared_blocks",
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
        shared_blocks: int,
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
        self.shared_blocks = shared_blocks

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

    @property
    def chars_minimum(self) -> float:
        """Caratteri per riga sul lato PIU' POVERO. Un separatore di colonna ha
        parole da entrambe le parti; un punto decorativo, un numero di elenco o
        l'etichetta di una linguetta no. Il vincolo non e' arbitrario ma
        tipografico: non si va a capo dopo una lettera o un articolo, quindi una
        colonna larga uno o due caratteri o non e' una colonna, o e' cosi'
        stretta che sbagliarla e' un errore trascurabile e correggibile dopo."""

        return min(self.left_chars_median, self.right_chars_median)


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
    min_flanking_chars: float,
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
      - ``too_few_chars``   meno di N caratteri per riga sul lato piu' povero:
                            non si va a capo dopo un articolo.
      - ``too_short``       gutter piu' basso di N righe DELLA PAGINA: l'unita'
                            e' l'interlinea misurata, non una costante in pt.
    """

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
    min_chars: float = 5.0,
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
    left_blocks: set[int] = set()
    right_blocks: set[int] = set()
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
                left_blocks.add(group.block_index)
                left_chars.append(
                    sum(text_length_by_id.get(i, 0) for i in group.primitive_ids)
                )
        elif group_x0 >= gutter_x1:
            if is_rotated:
                right_rotated += 1
            else:
                right_widths.append(group_x1 - group_x0)
                right_blocks.add(group.block_index)
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
        shared_blocks=len(left_blocks & right_blocks),
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
    return inner.span_y0 < outer.span_y1 and outer.span_y0 < inner.span_y1


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
    # Fab p.139 a 8. Il default 15 sta nel vuoto, dalla parte conservativa.
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


def _process_page(
    document: fitz.Document,
    page_index: int,
    *,
    manual: str,
    bin_width_x: float,
    bin_height_y: float,
    min_flanking_groups: int,
    min_flanking_chars: float,
    min_gutter_lines: float,
    min_column_chars: float = _DEFAULT_MIN_COLUMN_CHARS,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    page = document.load_page(page_index)
    if page.rotation != 0 or page.mediabox != page.cropbox:
        # Stessa precondizione degli altri script diagnostici: una pagina
        # ruotata o ritagliata renderebbe le coordinate non confrontabili.
        print(
            f"rotation/cropbox precondition failed su p.{page_index + 1}, saltata",
            file=sys.stderr,
        )
        return [], [], []

    capture = capture_pymupdf_page(
        page,
        source_id="diagnostic-source",
        page_id=f"page:{page_index + 1:04d}",
        capture_id=f"diagnostic-derived-bands-capture:{page_index}",
    )
    primitive_page = normalize_backend_page_capture(capture)
    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    groups, _unparsed = _group_by_pymupdf_line(
        primitive_page.text_primitives, page_width=page_width, page_height=page_height
    )
    if not groups:
        return [], [], []

    grid, _n_x_bins, _n_y_bins = _build_gap_grid(
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

    rotated_groups = _rotated_group_ids(groups, primitive_page.text_primitives)
    text_length_by_id = {
        p.primitive_id: len((p.text or "").strip()) for p in primitive_page.text_primitives
    }
    page_label = page_index + 1
    line_height = _median_line_height(groups)
    font_size = _median_font_size(primitive_page.text_primitives)
    _pre_tree = [
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
            min_flanking_chars=min_flanking_chars,
            min_gutter_lines=min_gutter_lines,
        )
        is None
    ]
    _segment_tree(
        _pre_tree,
        bin_width_x=bin_width_x,
        page_width=page_width,
        font_size=font_size,
        min_column_chars=min_column_chars,
    )

    gutter_rows: list[dict[str, object]] = []
    for gutter_index, rect in enumerate(rects):
        x0 = rect.x_bin_start * bin_width_x
        x1 = (rect.x_bin_end + 1) * bin_width_x
        profile = _flanking_profile(
            groups,
            rect,
            bin_width_x=bin_width_x,
            rotated_groups=rotated_groups,
            text_length_by_id=text_length_by_id,
            min_chars=min_flanking_chars,
        )
        reject_reason = _reject_reason(
            profile,
            rect,
            line_height=line_height,
            min_flanking_groups=min_flanking_groups,
            min_flanking_chars=min_flanking_chars,
            min_gutter_lines=min_gutter_lines,
        )
        gutter_rows.append(
            {
                "manual": manual,
                "page": page_label,
                "gutter_index": gutter_index,
                "x0": round(x0, 2),
                "x1": round(x1, 2),
                "width": round(x1 - x0, 2),
                "y0": round(rect.y0, 2),
                "y1": round(rect.y1, 2),
                "y_extent": round(rect.y1 - rect.y0, 2),
                "left_groups": profile.left,
                "right_groups": profile.right,
                "flanking_min": profile.minimum,
                "left_rotated": profile.left_rotated,
                "right_rotated": profile.right_rotated,
                "left_width_median": round(profile.left_width_median, 2),
                "right_width_median": round(profile.right_width_median, 2),
                "shared_blocks": profile.shared_blocks,
                "left_chars_median": round(profile.left_chars_median, 1),
                "right_chars_median": round(profile.right_chars_median, 1),
                "left_wordy": profile.left_wordy,
                "right_wordy": profile.right_wordy,
                "page_line_height": round(line_height, 2),
                "page_font_size": round(font_size, 2),
                "reject_reason": reject_reason or "",
                "tree_status": rect.tree_status,
            }
        )

    # Solo i gutter che separano davvero qualcosa entrano nella segmentazione.
    separating = [
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
            min_flanking_chars=min_flanking_chars,
            min_gutter_lines=min_gutter_lines,
        )
        is None
    ]

    tree_rows = _segment_tree(
        separating,
        bin_width_x=bin_width_x,
        page_width=page_width,
        font_size=font_size,
        min_column_chars=min_column_chars,
    )
    for row in tree_rows:
        row["manual"] = manual
        row["page"] = page_label

    band_rows: list[dict[str, object]] = []
    for band_index, (band_y0, band_y1, crossing) in enumerate(
        _segment_bands(separating, bin_width_x=bin_width_x)
    ):
        band_rows.append(
            {
                "manual": manual,
                "page": page_label,
                "band_index": band_index,
                "y0": round(band_y0, 2),
                "y1": round(band_y1, 2),
                "y_extent": round(band_y1 - band_y0, 2),
                "column_count": len(crossing) + 1,
                "gutter_x_intervals": " ".join(f"{a:.1f}-{b:.1f}" for a, b in crossing),
            }
        )

    return gutter_rows, band_rows, tree_rows


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=None, help="1-indexed. Default: tutto il PDF.")
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--emit",
        choices=("bands", "gutters", "tree"),
        default="bands",
        help="bands: la segmentazione a fasce y globali (difettosa, v. docstring). "
        "gutters: i candidati grezzi senza filtro. tree: la segmentazione GERARCHICA, "
        "con estensione x esplicita e sotto-bande. Default: bands.",
    )
    parser.add_argument(
        "--min-flanking-chars",
        type=float,
        default=_DEFAULT_MIN_FLANKING_CHARS,
        help="Caratteri per riga richiesti sul lato piu' povero. Vincolo tipografico, non "
        "geometrico: non si va a capo dopo una lettera o un articolo. Scarta i punti "
        "decorativi, le colonne di numeri di tabella e le etichette di linguetta. Default: 5.",
    )
    parser.add_argument(
        "--min-gutter-lines",
        type=float,
        default=_DEFAULT_MIN_GUTTER_LINES,
        help="Altezza minima del gutter in RIGHE DELLA PAGINA (interlinea mediana misurata, "
        "non una costante in pt). Default: 3.",
    )
    parser.add_argument(
        "--min-column-chars",
        type=float,
        default=_DEFAULT_MIN_COLUMN_CHARS,
        help="Larghezza minima di una colonna, in CARATTERI del documento (corpo del "
        "carattere x 0,5). Criterio di banda, non di gutter. Default: 15.",
    )
    parser.add_argument("--bin-width-x", type=float, default=_DEFAULT_BIN_WIDTH_X)
    parser.add_argument("--bin-height-y", type=float, default=_DEFAULT_BIN_HEIGHT_Y)
    parser.add_argument(
        "--min-flanking-groups",
        type=int,
        default=_DEFAULT_MIN_FLANKING_GROUPS,
        help="Righe distinte richieste su CIASCUN lato di un gutter perche' conti come "
        "separatore di colonna. Non e' una soglia geometrica tarabile ma un minimo "
        "strutturale: una colonna di una riga sola non e' una colonna, e un gap con zero "
        "righe da un lato non separa nulla. Si applica solo a --emit bands; --emit gutters "
        "resta grezzo, cosi' il filtro si puo' sempre rifare a valle. Default: 2.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    all_gutters: list[dict[str, object]] = []
    all_bands: list[dict[str, object]] = []
    all_tree: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        page_indices = (
            [args.page - 1] if args.page is not None else list(range(document.page_count))
        )
        print(f"{pdf_path.name}: {len(page_indices)} pagina/e da processare", file=sys.stderr)
        for page_index in page_indices:
            if page_index < 0 or page_index >= document.page_count:
                print(f"pagina fuori range: {page_index + 1}", file=sys.stderr)
                return 1
            gutter_rows, band_rows, tree_rows = _process_page(
                document,
                page_index,
                manual=pdf_path.name,
                bin_width_x=args.bin_width_x,
                bin_height_y=args.bin_height_y,
                min_flanking_groups=args.min_flanking_groups,
                min_flanking_chars=args.min_flanking_chars,
                min_gutter_lines=args.min_gutter_lines,
                min_column_chars=args.min_column_chars,
            )
            all_gutters.extend(gutter_rows)
            all_bands.extend(band_rows)
            all_tree.extend(tree_rows)

    rows = {"gutters": all_gutters, "tree": all_tree}.get(args.emit, all_bands)
    fieldnames = {"gutters": _GUTTER_FIELDNAMES, "tree": _TREE_FIELDNAMES}.get(
        args.emit, _BAND_FIELDNAMES
    )

    handle: TextIO
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        handle = args.output.open("w", newline="", encoding="utf-8")
    else:
        handle = sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if handle is not sys.stdout:
            handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
