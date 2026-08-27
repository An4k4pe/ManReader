"""Build one IR 2 page from ordered primitives, candidates and Resolution outcomes.

Second of the four modules of ``Proposta_IR2Minima_v3.md`` §7.

**The reading order is received, never recomputed.** The caller passes the text
primitives already in reading order. Recomputing it here would be a second
implementation of the ordering, and it would turn the exit criterion into a
comparison between two mechanisms instead of a check on this one -- on a project
that has already had two definitions of the same thing diverge.

**The atom is the source line**, from ``Criterio_ParagrafoDaRiga_v1.md``:

1. inside a line the spans are concatenated with no separator, ordered by
   ``span_index`` -- the spans already carry their own spacing, and joining them
   with a space adds a second one at every style boundary (measured on DB p.99:
   ``'a '`` + ``'PERSUADERE'`` + ``'.'`` gives ``a PERSUADERE .`` when joined);
2. hyphenation is rejoined with ``ir_builder``'s regex, at its own conditions.

**Where a paragraph breaks** is ``Criterio_RotturaParagrafo_v2.md``, and it
replaces the purely lexical rule this module was born with. That rule broke a
paragraph whenever the next line did not start lowercase, which cut a period at
every acronym, parenthesis and proper noun: a blind sample of 20 pages judged by
a person named "spaziature" on 17 of them, which in Markdown is a blank line
inside a sentence. It also split every stat block by field, the fall already
recorded in ``Esito_ParagrafoDaRiga_Par5_v1.md`` §5.

The rule is now the block boundary with a lexical veto -- see ``breaks_paragraph``
-- and both signals were already in the pipeline and unused.

Every text primitive of a paragraph goes into the node, including the ones whose
text is empty. They carry no characters but they are primitives, and leaving them
out would be a silent exclusion -- ``ir2_validate`` checks exactly this.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from document_list_policy import opens_a_list_item  # noqa: I001
from geometry_model import BBox
from ir2_model import (
    KIND_ASSET_NOTE,
    KIND_TABLE,
    KIND_TEXT_LIST_ITEM,
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    CellIR2,
    NodeIR2,
    PageIR2,
    TableIR2,
    TextRunIR2,
)
from ir_builder import _HYPHENATED_WORD_RE
from primitive_model import TextPrimitive

_SOURCE_LINE_PATTERN = re.compile(r"^text:(b\d+):(l\d+):s\d+$")
_STARTS_LOWERCASE = re.compile(r"^[a-zà-öø-ÿ]")
# Il marcatore di elenco e i terminatori di frase erano due clausole della regola
# lessicale. Cadono con essa: la rottura la decide il blocco, e un periodo che
# finisce a meta' blocco NON chiude un paragrafo -- un paragrafo contiene piu'
# frasi. Tenerle sarebbe stato portarsi dietro due eccezioni non piu' esercitate.
_HYPHEN_AT_END = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]-$")


@dataclass(frozen=True, slots=True)
class AssetNoteInput:
    """One asset note the caller wants placed in the reading flow.

    The caller owns asset extraction and Resolution lookup; this module only
    turns the result into nodes. ``sort_key`` is where the note belongs in the
    reading order, and it is an **index into the ordered text primitives the
    caller passed**, not a coordinate: the note goes before the paragraph that
    contains that primitive. Deciding it belongs to whoever owns the ordering,
    which is not this module -- a previous version compared ``y`` here, which is
    geometry overriding reading order and lands a right-column note inside the
    left column on a two-column page.
    """

    primitive_id: str
    digest: str
    file_name: str
    bbox: BBox
    occurrence_count: int
    anchor_index: int
    proposed_structural_kind: str | None = None
    candidate_ids: tuple[str, ...] = ()
    resolution: str | None = None


@dataclass(frozen=True, slots=True)
class TableRegionInput:
    """One region the caller believes is a table, with its column boundaries.

    Nothing here is computed by this module. ``bbox`` comes from a
    ``table_candidate``; ``gutter_x_intervals`` come from
    ``ColumnBandMeasurements`` -- both are producers already wired, and
    ``State.md`` assigns those gutters to the table consumer in as many words:
    «column_band non deve leggere le tabelle, deve dire dove sono i confini di
    colonna, e se una regione e' una tabella la gestisce il consumer di tabelle
    aiutato da questi gutter».
    """

    bbox: BBox
    gutter_x_intervals: tuple[tuple[float, float], ...] = ()
    candidate_ids: tuple[str, ...] = ()
    resolution: str | None = None


@dataclass(frozen=True, slots=True)
class _SourceLine:
    block: str
    line: str
    text: str
    primitives: tuple[TextPrimitive, ...]


def _source_line_key(primitive: TextPrimitive) -> tuple[str, str] | None:
    match = _SOURCE_LINE_PATTERN.match(primitive.source_observation_id)
    if match is None:
        return None
    return match.group(1), match.group(2)


def _span_index(primitive: TextPrimitive) -> int:
    tail = primitive.source_observation_id.rsplit(":s", 1)
    if len(tail) != 2 or not tail[1].isdigit():
        return 0
    return int(tail[1])


def group_source_lines(ordered: Sequence[TextPrimitive]) -> list[_SourceLine]:
    """Group ordered primitives into source lines, keeping the received order.

    A primitive whose observation id cannot be read as a line becomes a line of
    its own: guessing which line it belongs to would risk merging distinct ones,
    and that is the failure this project has already corrected three times.
    """

    lines: list[_SourceLine] = []
    current_key: tuple[str, str] | None = None
    current: list[TextPrimitive] = []

    def flush() -> None:
        if not current:
            return
        ordered_spans = sorted(current, key=_span_index)
        text = "".join(primitive.text for primitive in ordered_spans)
        block, line = current_key if current_key is not None else ("", "")
        lines.append(
            _SourceLine(block=block, line=line, text=text, primitives=tuple(ordered_spans))
        )
        current.clear()

    for primitive in ordered:
        key = _source_line_key(primitive)
        if key is None or key != current_key:
            flush()
            current_key = key
        current.append(primitive)
    flush()
    return lines


def bind_marker_glyphs(
    lines: list[_SourceLine], markers: frozenset[str]
) -> list[_SourceLine]:
    """Riattacca un glifo d'elenco al testo della sua voce.

    **Il legame e' un fatto della sorgente, non della geometria.** Misurato su FW
    p.168: il glifo `•` sta a x=57,7 e il suo testo `Afflizione` a x=72,7, alla
    **stessa y** e nello **stesso blocco** ``b0011`` -- il backend li spezza in due
    *righe*, ``l0000`` e ``l0001``. Il glifo della colonna accanto sta a x=213,6,
    stessa y, blocco ``b0012``.

    L'ordinamento a bande, che decide per posizione, puo' quindi mettere il glifo
    di una colonna prima del testo dell'altra: succedeva, e il testo della seconda
    colonna restava orfano mentre il glifo si prendeva quello della prima.

    Il blocco lo dice senza ambiguita', e per la stessa ragione per cui lo dice
    per i paragrafi (`Criterio_ParagrafoDaBlocco_v1.md`): e' gia' nella sorgente e
    nessuno lo stava usando. La riparazione si applica **qui**, sulle righe
    sorgente, dove nessun ordinamento la puo' disfare -- non sull'ordine, che la
    rifarebbe a ogni giro.

    Cerca **in avanti**, non solo la riga adiacente: fra il glifo e il suo testo
    l'ordine di lettura puo' aver infilato righe di un altro blocco.

    Un glifo che non trova il suo testo resta com'e': inventargli un compagno
    sarebbe la fusione di righe distinte che questo builder ha gia' corretto tre
    volte.
    """

    if not markers:
        return lines

    remaining = list(lines)
    result: list[_SourceLine] = []
    while remaining:
        line = remaining.pop(0)
        if line.text.strip() not in markers:
            result.append(line)
            continue
        partner = next(
            (
                other
                for other in remaining
                if other.block == line.block and other.text.strip()
            ),
            None,
        )
        if partner is None:
            result.append(line)
            continue
        remaining.remove(partner)
        result.append(
            _SourceLine(
                block=line.block,
                line=line.line,
                text=line.text + partner.text,
                primitives=line.primitives + partner.primitives,
            )
        )
    return result


def _with_redraws(ids: tuple[str, ...], redraw_ids: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Gli id del nodo piu' quelli dei ridisegni dei suoi gemelli."""

    if not redraw_ids:
        return ids
    out: list[str] = []
    for primitive_id in ids:
        out.append(primitive_id)
        out.extend(redraw_ids.get(primitive_id, ()))
    return tuple(out)


def redrawn_duplicates(
    ordered: Sequence[TextPrimitive],
) -> tuple[list[TextPrimitive], dict[str, tuple[str, ...]]]:
    """Separa i ridisegni: stesso testo, **stessa bbox**, sulla stessa pagina.

    Un PDF puo' disegnare lo stesso glifo due volte nello stesso punto -- effetto
    di ombra o di contorno, comune nei manuali illustrati. Due primitive con
    testo identico e bbox identica sono lo stesso segno sulla pagina, non due,
    e senza questa separazione il testo esce **due volte**.

    Misurato su due manuali e due elementi diversi: su Wil idx 103 il titolo
    `I Wilder` esce due volte da 13 paragrafi (`Esito_FormaMancante_v1.md` §5,
    segnalato dall'utente); su Fab il numero di pagina e' doppio su **6 pagine su
    40**, con bbox identica al quarto decimale.

    **Va fatto a livello di pagina, non di riga**: su Wil le due copie stanno in
    righe di sorgente diverse dello stesso blocco (`b0002:l0000` e `b0002:l0001`),
    su Fab in blocchi diversi (`b0000` e `b0004`). E' per questo che il ridisegno
    produce un paragrafo in piu' e non un carattere in piu'.

    **Nessuna soglia**: l'uguaglianza e' esatta su testo e bbox. Due glifi
    identici nello stesso identico punto sono sovrapposti per definizione.

    Il duplicato **non sparisce**: torna nella mappa, e il chiamante lo aggiunge
    ai `primitive_ids` del nodo che porta il suo gemello. `ir2_validate` esige
    che ogni primitiva sia coperta, e una rimozione silenziosa sarebbe
    l'esclusione che `AGENTS.MD` §Coverage vieta.
    """

    kept: list[TextPrimitive] = []
    twin_of: dict[tuple[str, BBox], str] = {}
    duplicates: dict[str, list[str]] = {}
    for primitive in ordered:
        if not primitive.text:
            kept.append(primitive)
            continue
        key = (primitive.text, primitive.bbox)
        twin = twin_of.get(key)
        if twin is None:
            twin_of[key] = primitive.primitive_id
            kept.append(primitive)
        else:
            duplicates.setdefault(twin, []).append(primitive.primitive_id)
    return kept, {twin: tuple(ids) for twin, ids in duplicates.items()}


def body_font(primitives: Sequence[TextPrimitive]) -> str | None:
    """The page's body font: the one carrying the most **characters**.

    Derived from the page, never a list of font names. It is what lets the rule
    tell a bullet from a lowercase letter: on Fab p.248 the nine list markers are
    the letter ``w`` in ``Wingdings-Regular`` while the body is ``PTSans-Narrow``,
    and `Esito_ParagrafoDaRiga_Par5_v1.md` records the same trap on DrW p.97,
    where the target symbol is the letter ``o``.

    **Characters and not primitives**, and the difference is not cosmetic.
    `Criterio_RotturaParagrafo_v2.md` §1 says "la moda dei ``font_name`` delle
    primitive testuali"; counting primitives gives ``Hideout-Bold`` on DB p.99,
    because a page of stat blocks has many short bold lines and few long prose
    ones. The prose carries the characters. Measured against the user's labels on
    that page: 37 junctions right out of 43 counting primitives, **40 counting
    characters**. The deviation from the letter of the criterion is declared
    here; its binding constraint -- derived from the page, never a list -- holds
    either way.
    """

    counts: Counter[str] = Counter()
    for primitive in primitives:
        if primitive.font_name:
            counts[primitive.font_name] += len(primitive.text)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def breaks_paragraph(
    previous: _SourceLine,
    following: _SourceLine,
    page_body_font: str | None,
    list_markers: frozenset[str] = frozenset(),
) -> bool:
    """Decide whether a paragraph breaks between two consecutive source lines.

    The rule of `Criterio_RotturaParagrafo_v2.md` §1, and it has **no
    parameters**: a paragraph breaks where the source block changes, unless the
    next line opens with a lowercase character *of the body font*.

    Both signals were already in the pipeline and neither was used here. The
    block lives in every ``source_observation_id`` and was ratified once
    (`Criterio_ParagrafoDaBlocco_v1.md`) before Milestone 38 switched it off on
    the evidence of a single page; the font comes from ``TextPrimitive``.

    The lexical test survives with its **role reversed**, and that is the whole
    design. It used to *force* a break whenever the next line was not lowercase,
    which split a paragraph at every acronym, parenthesis and proper noun -- the
    "spaziature" that 17 pages out of 20 of a blind sample complained about. Here
    it can only *veto* a break the block boundary already proposed, so its way of
    failing flips from breaking too much to breaking too little. That is a
    declared preference, not a measurement: better two paragraphs joined than one
    cut in three.

    The block alone does not do: on a two-column page a paragraph running from
    the foot of one column to the head of the next is two blocks, and breaking
    there cuts a sentence in half (measured on SV p.181, 27 paragraphs against
    23).
    """

    # Una voce d'elenco rompe SEMPRE, anche dentro lo stesso blocco: e' li' che
    # le voci vivono, ed e' la ragione per cui uscivano schiacciate in un
    # paragrafo solo. `Criterio_Elenchi_v1.md` §1.
    #
    # Rompe solo cio' che **apre** una voce, non cio' che la segue: una voce che
    # va a capo continua sulla riga dopo senza marcatore, e romperla la
    # taglierebbe in due. Il prezzo e' che l'ultima voce puo' assorbire la prosa
    # che segue nello stesso blocco, ed e' il verso in cui questo builder ha gia'
    # dichiarato di preferire di sbagliare.
    # Una riga fatta del **solo** marcatore non e' una voce: e' il glifo, e il
    # testo della voce e' la riga dopo. Misurato su FW, dove `•` sta da solo 41
    # volte su 41. Senza questa riga usciva `- ` vuoto e il testo finiva in un
    # paragrafo a parte, cioe' l'elenco peggiorava la pagina invece di
    # migliorarla.
    if (
        previous.text.strip()
        and previous.text.strip() in list_markers
        and not opens_a_list_item(following.text, list_markers)
    ):
        return False
    if opens_a_list_item(following.text, list_markers):
        return True
    if previous.block == following.block:
        return False
    text = following.text.lstrip()
    if not text:
        return False
    if not _STARTS_LOWERCASE.match(text):
        return True
    opening_font = following.primitives[0].font_name if following.primitives else None
    return opening_font != page_body_font


def join_lines(previous_text: str, next_text: str) -> str:
    """Join two source lines that belong to the same paragraph.

    The dehyphenation is applied **only at the junction**, never to the
    accumulated paragraph. ``previous_text`` is everything gathered so far, and
    running the regex over all of it made a hyphen a hundred characters back
    disappear because the *current* junction happened to have one -- the same
    text came out two different ways depending on whether a later line ended in
    a hyphen. E-B is blind to it by construction, since it applies the same
    regex to both sides of the comparison.

    The character classes stay ``ir_builder``'s: the regex decides whether this
    junction is a hyphenation, and it is applied to a two-character window so
    that there is still only one definition of what a hyphenation is.
    """

    left = previous_text.rstrip()
    right = next_text.lstrip()
    joined = f"{left} {right}"
    if not _HYPHEN_AT_END.search(left):
        return joined

    window = f"{left[-2:]} {right[:1]}"
    if _HYPHENATED_WORD_RE.sub("", window) == window:
        return joined
    return f"{left[:-1]}{right}"


def runs_for_line(line: _SourceLine) -> list[TextRunIR2]:
    """The line's spans, merged into runs of equal traits.

    Empty spans contribute no character and therefore no run; they stay in the
    node's ``primitive_ids`` all the same, which is what ``ir2_validate`` checks.
    """

    runs: list[TextRunIR2] = []
    for primitive in line.primitives:
        if not primitive.text:
            continue
        traits = tuple(primitive.font_traits)
        if runs and runs[-1].traits == traits:
            runs[-1] = TextRunIR2(runs[-1].text + primitive.text, traits)
        else:
            runs.append(TextRunIR2(primitive.text, traits))
    return runs


def _strip_runs(runs: list[TextRunIR2]) -> tuple[TextRunIR2, ...]:
    """I run del paragrafo finito, spogliati come lo e' il suo `text`."""

    return tuple(_lstrip_runs(_rstrip_runs(runs)))


def _rstrip_runs(runs: list[TextRunIR2]) -> list[TextRunIR2]:
    out = list(runs)
    while out:
        stripped = out[-1].text.rstrip()
        if stripped:
            out[-1] = TextRunIR2(stripped, out[-1].traits)
            break
        out.pop()
    return out


def _lstrip_runs(runs: list[TextRunIR2]) -> list[TextRunIR2]:
    out = list(runs)
    while out:
        stripped = out[0].text.lstrip()
        if stripped:
            out[0] = TextRunIR2(stripped, out[0].traits)
            break
        out.pop(0)
    return out


def join_runs(left_runs: list[TextRunIR2], right_runs: list[TextRunIR2]) -> list[TextRunIR2]:
    """The run-level mirror of ``join_lines``, character for character.

    It must reproduce the same three cases -- plain join with a space, join with
    a space despite a trailing hyphen, dehyphenation -- because ``NodeIR2``
    refuses runs that do not concatenate to ``text``. Mirroring is deliberate:
    the alternative was to rebuild the runs by aligning them to an already
    joined string, and the space this inserts and the hyphen it removes belong
    to no primitive, so no alignment can be exact.

    The inserted space is attached to the **left** run: it is the junction of two
    lines and it has no traits of its own, and giving it the traits of what comes
    before keeps a bold word from growing a bold space in front of the next one.
    """

    left = _rstrip_runs(left_runs)
    right = _lstrip_runs(right_runs)
    if not left:
        return right
    if not right:
        return left

    left_text = "".join(run.text for run in left)
    right_text = "".join(run.text for run in right)
    dehyphenate = False
    if _HYPHEN_AT_END.search(left_text):
        window = f"{left_text[-2:]} {right_text[:1]}"
        dehyphenate = _HYPHENATED_WORD_RE.sub("", window) != window

    if dehyphenate:
        tail = left[-1]
        left = left[:-1] + ([TextRunIR2(tail.text[:-1], tail.traits)] if len(tail.text) > 1 else [])
    else:
        tail = left[-1]
        left = left[:-1] + [TextRunIR2(tail.text + " ", tail.traits)]

    if left and right and left[-1].traits == right[0].traits:
        merged = TextRunIR2(left[-1].text + right[0].text, right[0].traits)
        return left[:-1] + [merged] + right[1:]
    return left + right


def column_bounds(region: TableRegionInput) -> list[tuple[float, float]]:
    """Column intervals of a region: what the gutters leave between them."""

    x0, _y0, x1, _y1 = region.bbox
    inside = sorted(
        (max(a, x0), min(b, x1))
        for a, b in region.gutter_x_intervals
        if a > x0 and b < x1
    )
    bounds: list[tuple[float, float]] = []
    edge = x0
    for gutter_start, gutter_end in inside:
        if gutter_start > edge:
            bounds.append((edge, gutter_start))
        edge = max(edge, gutter_end)
    if x1 > edge:
        bounds.append((edge, x1))
    return bounds


def _column_of(line: _SourceLine, bounds: list[tuple[float, float]]) -> int | None:
    """Which column a source line sits in, or None when it does not fit one.

    A line that straddles a gutter belongs to no column, and becomes a residual
    rather than being pushed into the nearer cell: putting text in the wrong cell
    silently is worse than leaving it as a paragraph.
    """

    x0 = min(p.bbox[0] for p in line.primitives)
    x1 = max(p.bbox[2] for p in line.primitives)
    for index, (left, right) in enumerate(bounds):
        if x0 >= left - 0.5 and x1 <= right + 0.5:
            return index
    return None


def build_table(
    region: TableRegionInput, lines: Sequence[_SourceLine]
) -> tuple[TableIR2 | None, list[_SourceLine]]:
    """Build a grid from the region's lines. Returns (table, residual lines)."""

    bounds = column_bounds(region)
    if len(bounds) < 2:
        return None, list(lines)

    placed: list[tuple[int, _SourceLine]] = []
    residuals: list[_SourceLine] = []
    for line in lines:
        column = _column_of(line, bounds)
        if column is None:
            residuals.append(line)
        else:
            placed.append((column, line))
    if not placed:
        return None, residuals

    # Le righe della tabella vengono dalle RIGHE DI SORGENTE raggruppate per
    # sovrapposizione in y: la geometria dice quali stanno affiancate, non
    # ricostruisce il testo, che resta quello della sorgente.
    ordered = sorted(placed, key=lambda item: min(p.bbox[1] for p in item[1].primitives))
    rows: list[list[tuple[int, _SourceLine]]] = [[ordered[0]]]
    for column, line in ordered[1:]:
        top = min(p.bbox[1] for p in line.primitives)
        bottom = max(max(p.bbox[3] for p in item[1].primitives) for item in rows[-1])
        if top < bottom - 1.0:
            rows[-1].append((column, line))
        else:
            rows.append([(column, line)])

    grid: list[tuple[CellIR2, ...]] = []
    for row_index, row in enumerate(rows):
        by_column: dict[int, list[_SourceLine]] = {}
        for column, line in row:
            by_column.setdefault(column, []).append(line)
        cells: list[CellIR2] = []
        for column_index in range(len(bounds)):
            members = sorted(
                by_column.get(column_index, ()),
                key=lambda item: min(p.bbox[0] for p in item.primitives),
            )
            text = " ".join(line.text.strip() for line in members if line.text.strip())
            cells.append(
                CellIR2(
                    row=row_index,
                    column=column_index,
                    text=text,
                    primitive_ids=tuple(
                        p.primitive_id for line in members for p in line.primitives
                    ),
                )
            )
        grid.append(tuple(cells))

    return TableIR2(rows=tuple(grid)), residuals


def build_page_ir2(
    *,
    page_id: str,
    ordered_text_primitives: Sequence[TextPrimitive],
    asset_notes: Sequence[AssetNoteInput] = (),
    table_regions: Sequence[TableRegionInput] = (),
    page_label: str | None = None,
    page_label_deduced: bool = False,
    list_markers: frozenset[str] = frozenset(),
) -> PageIR2:
    """Build one IR 2 page. Reading order is the caller's; this only groups."""

    # I ridisegni escono dal flusso PRIMA di qualunque raggruppamento: stanno in
    # righe e blocchi diversi dal gemello, quindi a valle sarebbero gia' diventati
    # una riga in piu' e poi un paragrafo in piu'. Tornano dentro come copertura
    # sul nodo del gemello, mai come testo.
    ordered_text_primitives, redraw_ids = redrawn_duplicates(ordered_text_primitives)
    source_lines = group_source_lines(ordered_text_primitives)
    tables: list[tuple[int, TableIR2, TableRegionInput, tuple[str, ...]]] = []
    consumed_ids: set[str] = set()
    for region in table_regions:
        x0, y0, x1, y1 = region.bbox
        inside = [
            line
            for line in source_lines
            if all(
                p.primitive_id not in consumed_ids
                and p.bbox[0] >= x0 - 0.5
                and p.bbox[2] <= x1 + 0.5
                and p.bbox[1] >= y0 - 0.5
                and p.bbox[3] <= y1 + 0.5
                for p in line.primitives
            )
        ]
        if not inside:
            continue
        table, _residuals = build_table(region, inside)
        if table is None:
            continue
        owned = tuple(
            primitive_id
            for row in table.rows
            for cell in row
            for primitive_id in cell.primitive_ids
        )
        if not owned:
            continue
        anchor = min(
            index
            for index, primitive in enumerate(ordered_text_primitives)
            if primitive.primitive_id in set(owned)
        )
        tables.append((anchor, table, region, owned))
        consumed_ids.update(owned)

    remaining = [p for p in ordered_text_primitives if p.primitive_id not in consumed_ids]
    paragraphs: list[
        tuple[str, tuple[TextPrimitive, ...], tuple[TextRunIR2, ...], bool]
    ] = []
    pending_text = ""
    pending_primitives: list[TextPrimitive] = []
    pending_runs: list[TextRunIR2] = []
    previous_line: _SourceLine | None = None
    # Il font del corpo si desume dalla pagina INTERA, non dal residuo: togliere
    # le celle di una tabella non deve poter cambiare quale font e' il corpo.
    page_body_font = body_font(ordered_text_primitives)

    for source_line in bind_marker_glyphs(group_source_lines(remaining), list_markers):
        if previous_line is None:
            pending_text = source_line.text
            pending_primitives = list(source_line.primitives)
            pending_runs = runs_for_line(source_line)
            previous_line = source_line
            continue
        if breaks_paragraph(previous_line, source_line, page_body_font, list_markers):
            paragraphs.append(
                (
                    pending_text.strip(),
                    tuple(pending_primitives),
                    _strip_runs(pending_runs),
                    opens_a_list_item(pending_text, list_markers),
                )
            )
            pending_text = source_line.text
            pending_primitives = list(source_line.primitives)
            pending_runs = runs_for_line(source_line)
        else:
            pending_text = join_lines(pending_text, source_line.text)
            pending_primitives.extend(source_line.primitives)
            pending_runs = join_runs(pending_runs, runs_for_line(source_line))
        previous_line = source_line
    if pending_primitives:
        paragraphs.append(
            (
                pending_text.strip(),
                tuple(pending_primitives),
                _strip_runs(pending_runs),
                opens_a_list_item(pending_text, list_markers),
            )
        )

    # I paragrafi NON si riordinano: l'ordine ricevuto e' l'ordine di lettura, e
    # riordinarli per geometria lo scavalcherebbe. Le note si inseriscono
    # DAVANTI al primo paragrafo che sta sotto di loro, senza spostare il testo
    # -- stesso schema del consumer che ha prodotto la base.
    #
    # Una versione precedente ordinava tutto per (y0, x0). Passava sulle pagine a
    # colonna singola, dove geometria e lettura coincidono, e falliva su 4 pagine
    # su 10 del campione. Trovato da E-B alla prima esecuzione.
    # L'ancora delle note indicizza la lista ORIGINALE, non quella residua:
    # estrarre le celle accorcia la sequenza, e usare la lista residua
    # sposterebbe le note di tante posizioni quante sono le primitive assorbite.
    index_of_primitive = {
        primitive.primitive_id: index
        for index, primitive in enumerate(ordered_text_primitives)
    }
    paragraph_of_original_index: dict[int, int] = {}
    for paragraph_index, (_text, primitives, _runs, _item) in enumerate(paragraphs):
        for primitive in primitives:
            original = index_of_primitive.get(primitive.primitive_id)
            if original is not None:
                paragraph_of_original_index[original] = paragraph_index

    def _rank_for(anchor: int) -> int:
        """Il paragrafo davanti a cui va un elemento ancorato a `anchor`."""

        candidates = [i for i in paragraph_of_original_index if i >= anchor]
        if not candidates:
            return len(paragraphs)
        return paragraph_of_original_index[min(candidates)]

    notes_by_rank: dict[int, list[AssetNoteInput]] = {}
    for note in asset_notes:
        notes_by_rank.setdefault(_rank_for(note.anchor_index), []).append(note)

    tables_by_rank: dict[int, list[tuple[TableIR2, TableRegionInput, tuple[str, ...]]]] = {}
    for anchor, table, region, owned in tables:
        tables_by_rank.setdefault(_rank_for(anchor), []).append((table, region, owned))

    items: list[tuple[str, object]] = []
    for index in range(len(paragraphs) + 1):
        for entry in tables_by_rank.get(index, ()):
            items.append(("table", entry))
        for note in sorted(notes_by_rank.get(index, ()), key=lambda item: item.anchor_index):
            items.append(("asset", note))
        if index < len(paragraphs):
            items.append(("text", paragraphs[index]))

    nodes: list[NodeIR2] = []
    for order, (kind, payload) in enumerate(items):
        if kind == "text":
            text, primitives, runs, is_list_item = payload  # type: ignore[misc]
            first = primitives[0]
            # L'identita' viene dal PRIMO PRIMITIVO, non dalla riga. Una riga di
            # sorgente puo' comparire piu' volte nell'ordine di lettura quando
            # l'ordinamento a bande la spezza fra due colonne -- misurato su DB
            # p.53, dove il glifo di elenco finisce in una banda e il suo testo
            # in un'altra, e `b0007:l0001` compare due volte. Con la riga come
            # identita' due nodi collidevano e il contratto rifiutava la pagina.
            # Lo span e' l'ultimo livello dell'id di sorgente, quindi resta
            # derivato dalla sorgente e stabile.
            suffix = first.source_observation_id or first.primitive_id
            nodes.append(
                NodeIR2(
                    node_id=f"{page_id}:{suffix}",
                    order=order,
                    kind=(
                        KIND_TEXT_LIST_ITEM if is_list_item else KIND_TEXT_PARAGRAPH
                    ),
                    primitive_ids=_with_redraws(
                        tuple(item.primitive_id for item in primitives), redraw_ids
                    ),
                    page_ids=(page_id,),
                    text=text,
                    runs=runs,
                )
            )
            continue

        if kind == "table":
            table, region, owned = payload  # type: ignore[misc]
            nodes.append(
                NodeIR2(
                    node_id=f"{page_id}:table:{owned[0]}",
                    order=order,
                    kind=KIND_TABLE,
                    primitive_ids=owned,
                    page_ids=(page_id,),
                    structure=table,
                    candidate_ids=region.candidate_ids,
                    resolution=region.resolution,
                )
            )
            continue

        note = payload  # type: ignore[assignment]
        assert isinstance(note, AssetNoteInput)
        nodes.append(
            NodeIR2(
                node_id=f"{page_id}:{note.primitive_id}",
                order=order,
                kind=KIND_ASSET_NOTE,
                primitive_ids=(note.primitive_id,),
                page_ids=(page_id,),
                asset=AssetRefIR2(
                    digest=note.digest,
                    file_name=note.file_name,
                    bbox=note.bbox,
                    occurrence_count=note.occurrence_count,
                    proposed_structural_kind=note.proposed_structural_kind,
                ),
                candidate_ids=note.candidate_ids,
                resolution=note.resolution,
            )
        )

    return PageIR2(
        page_id=page_id,
        nodes=tuple(nodes),
        page_label=page_label,
        page_label_deduced=page_label_deduced,
    )
