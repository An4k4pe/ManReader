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
7. Nessun filtro: lo script emette ogni gutter ordinato per estensione y, cosi'
   la separazione fra spazi fra parole e gutter si vede nel dato invece di
   essere postulata.
8. Le bande si ricavano dai confini y dei gutter: ogni y in cui l'insieme dei
   gutter attivi cambia e' un confine. `column_count` di una banda = numero di
   gutter che la attraversano per intero, piu' uno.

## Stato empirico, aggiornato all'11 agosto 2026

- **Dag p.84 posizionale** (prosa 2 colonne verificata a render, il caso su cui
  il meccanismo di Fase 2 falliva a ogni combinazione di parametri con
  `--min-gap-width` 15pt): trovato. Gutter a x 298-306, larghezza 8pt --
  **sotto** la vecchia soglia -- con estensione 120pt, piu' un secondo tratto di
  46pt sopra. Nessuna soglia di larghezza, nessun support ratio.
- **Residuo non risolto**: su quella stessa pagina il gutter esce spezzato in
  due bande (126-172 e 192-312) invece che in una. Il taglio cade dove cambia
  la struttura del contenuto a destra; non e' stato indagato.
- **Fab p.262 posizionale**: entrambi i meccanismi falliscono, non e' un
  disaccordo. Misurato sull'intero corpus, non dedotto: `persistence` su quella
  pagina restituisce `column_count=1`, non 2. Questo prototipo trova solo bande
  minuscole (12pt e 30pt di estensione), cioe' rumore.
  **Correzione di una versione precedente di questa docstring** (commit
  56954f9), lasciata a verbale invece che cancellata: vi si affermava che
  `persistence` desse `column_count=2` su p.262 e che il prototipo non lo
  riproducesse. L'affermazione era presa dalla narrazione di `State.md` invece
  che da una misura, ed e' falsa. `State.md` cita un caso Fab a lista numerata
  con `column_count=2` corretto ma **non indica quale pagina sia**: non e' la
  262, e non e' stato identificato. E' lo stesso errore di attribuzione via
  `--page N` gia' registrato in `State.md` come rischio procedurale.
  Compatibile col dato di `dump_raw_group_gaps.py` su p.262 (meta' delle fette
  y ha gap NEGATIVI: i gruppi delle due colonne si sovrappongono in x, quindi un
  corridoio verticale libero non esiste), ma la spiegazione resta non
  verificata.

## Cosa NON risolve, dichiarato

- L'overlap banda/`table_candidate` (Milestone 33 punto bloccante 2) e il
  confound `side_band`: intatti, come per tutti i meccanismi di questa
  diagnostica.
- `--bin-width-x` e `--bin-height-y` restano costanti di discretizzazione. Non
  sono soglie decisionali (non stabiliscono se un gap conta) ma la risoluzione
  con cui si guarda; vanno comunque verificate per sensibilita', non assunte
  innocue. Il default y (2pt) e' lo stesso di Fase 2 di proposito.
- La distinzione fra spazio fra parole e gutter e' AFFIDATA all'ordinamento per
  estensione y, non dimostrata. Se su qualche pagina uno spazio fra parole
  persistesse verticalmente (colonne di testo molto strette, o testo
  incolonnato a mano) il metodo lo chiamerebbe gutter. Caso non ancora cercato.

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

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH_X = 1.0
_DEFAULT_BIN_HEIGHT_Y = 2.0

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

    __slots__ = ("x_bin_start", "x_bin_end", "y0", "y1")

    def __init__(self, x_bin_start: int, x_bin_end: int, y0: float, y1: float) -> None:
        self.x_bin_start = x_bin_start
        self.x_bin_end = x_bin_end
        self.y0 = y0
        self.y1 = y1


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
            core = row[gutter.x_bin_start : gutter.x_bin_end + 1]
            if all(state == _NO_TEXT for state in core):
                # Zona senza testo: non conferma il gutter ma non lo smentisce.
                # y1 non avanza, cosi' l'estensione resta quella sostenuta.
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


def _segment_bands(
    rects: list[_GapRect], *, bin_width_x: float
) -> list[tuple[float, float, list[tuple[float, float]]]]:
    """Bande dai confini y dei gutter: ogni y in cui l'insieme dei gutter
    attivi cambia e' un confine. Nessuna griglia di banda, nessuna soglia di
    supporto -- i confini vengono dai dati."""

    if not rects:
        return []

    boundaries = sorted({rect.y0 for rect in rects} | {rect.y1 for rect in rects})
    bands: list[tuple[float, float, list[tuple[float, float]]]] = []
    for band_y0, band_y1 in zip(boundaries, boundaries[1:], strict=False):
        if band_y1 <= band_y0:
            continue
        crossing = [
            (rect.x_bin_start * bin_width_x, (rect.x_bin_end + 1) * bin_width_x)
            for rect in rects
            if rect.y0 <= band_y0 and rect.y1 >= band_y1
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
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    page = document.load_page(page_index)
    if page.rotation != 0 or page.mediabox != page.cropbox:
        # Stessa precondizione degli altri script diagnostici: una pagina
        # ruotata o ritagliata renderebbe le coordinate non confrontabili.
        print(
            f"rotation/cropbox precondition failed su p.{page_index + 1}, saltata",
            file=sys.stderr,
        )
        return [], []

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
        return [], []

    grid, _n_x_bins, _n_y_bins = _build_gap_grid(
        groups,
        page_width=page_width,
        page_height=page_height,
        bin_width_x=bin_width_x,
        bin_height_y=bin_height_y,
    )
    rects = _chain_gutters(grid, bin_height_y=bin_height_y)
    rects.sort(key=lambda r: (r.y1 - r.y0), reverse=True)

    page_label = page_index + 1
    gutter_rows: list[dict[str, object]] = []
    for gutter_index, rect in enumerate(rects):
        x0 = rect.x_bin_start * bin_width_x
        x1 = (rect.x_bin_end + 1) * bin_width_x
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
            }
        )

    band_rows: list[dict[str, object]] = []
    for band_index, (band_y0, band_y1, crossing) in enumerate(
        _segment_bands(rects, bin_width_x=bin_width_x)
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

    return gutter_rows, band_rows


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=None, help="1-indexed. Default: tutto il PDF.")
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument(
        "--emit",
        choices=("bands", "gutters"),
        default="bands",
        help="bands: la segmentazione ricavata. gutters: i candidati gutter grezzi, "
        "ordinati per estensione y, senza alcun filtro. Default: bands.",
    )
    parser.add_argument("--bin-width-x", type=float, default=_DEFAULT_BIN_WIDTH_X)
    parser.add_argument("--bin-height-y", type=float, default=_DEFAULT_BIN_HEIGHT_Y)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    all_gutters: list[dict[str, object]] = []
    all_bands: list[dict[str, object]] = []

    with fitz.open(pdf_path) as document:
        page_indices = (
            [args.page - 1] if args.page is not None else list(range(document.page_count))
        )
        print(f"{pdf_path.name}: {len(page_indices)} pagina/e da processare", file=sys.stderr)
        for page_index in page_indices:
            if page_index < 0 or page_index >= document.page_count:
                print(f"pagina fuori range: {page_index + 1}", file=sys.stderr)
                return 1
            gutter_rows, band_rows = _process_page(
                document,
                page_index,
                manual=pdf_path.name,
                bin_width_x=args.bin_width_x,
                bin_height_y=args.bin_height_y,
            )
            all_gutters.extend(gutter_rows)
            all_bands.extend(band_rows)

    rows = all_gutters if args.emit == "gutters" else all_bands
    fieldnames = _GUTTER_FIELDNAMES if args.emit == "gutters" else _BAND_FIELDNAMES

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
