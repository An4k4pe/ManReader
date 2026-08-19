"""Build one IR 2 page from ordered primitives, candidates and Resolution outcomes.

Second of the four modules of ``Proposta_IR2Minima_v3.md`` §7.

**The reading order is received, never recomputed.** The caller passes the text
primitives already in reading order. Recomputing it here would be a second
implementation of the ordering, and it would turn the exit criterion into a
comparison between two mechanisms instead of a check on this one -- on a project
that has already had two definitions of the same thing diverge.

The paragraph rules come from ``Criterio_ParagrafoDaRiga_v1.md``, pre-registered
and committed before this module existed. **The atom is the source line**, and the
block decides nothing:

1. inside a line the spans are concatenated with no separator, ordered by
   ``span_index`` -- the spans already carry their own spacing, and joining them
   with a space adds a second one at every style boundary (measured on DB p.99:
   ``'a '`` + ``'PERSUADERE'`` + ``'.'`` gives ``a PERSUADERE .`` when joined);
2. between two consecutive lines a paragraph breaks when the next line does not
   start lowercase, or the previous ends with ``.;!?``, or the previous ends with
   ``:`` and the next starts with a dash or a digit (the list guard);
3. hyphenation is rejoined with ``ir_builder``'s regex, at its own conditions.

The colon does **not** end a paragraph, unlike ``_ends_with_strong_punctuation``
in ``markdown_builder``: it is what keeps ``Non-Mostri:`` attached to its text.

Every text primitive of a paragraph goes into the node, including the ones whose
text is empty. They carry no characters but they are primitives, and leaving them
out would be a silent exclusion -- ``ir2_validate`` checks exactly this.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from geometry_model import BBox
from ir2_model import (
    KIND_ASSET_NOTE,
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    NodeIR2,
    PageIR2,
)
from ir_builder import _HYPHENATED_WORD_RE
from primitive_model import TextPrimitive

_SOURCE_LINE_PATTERN = re.compile(r"^text:(b\d+):(l\d+):s\d+$")
_STARTS_LOWERCASE = re.compile(r"^[a-zà-öø-ÿ]")
_STARTS_LIST_MARKER = re.compile(r"^[-•●◆\d]")
_PARAGRAPH_TERMINATORS = (".", ";", "!", "?")
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


def breaks_paragraph(previous_text: str, next_text: str) -> bool:
    """Decide whether a paragraph breaks between two consecutive source lines."""

    previous = previous_text.rstrip()
    following = next_text.lstrip()
    if not following:
        return False
    if previous.endswith(":") and _STARTS_LIST_MARKER.match(following):
        return True
    if not _STARTS_LOWERCASE.match(following):
        return True
    return previous.endswith(_PARAGRAPH_TERMINATORS)


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


def build_page_ir2(
    *,
    page_id: str,
    ordered_text_primitives: Sequence[TextPrimitive],
    asset_notes: Sequence[AssetNoteInput] = (),
) -> PageIR2:
    """Build one IR 2 page. Reading order is the caller's; this only groups."""

    paragraphs: list[tuple[str, tuple[TextPrimitive, ...]]] = []
    pending_text = ""
    pending_primitives: list[TextPrimitive] = []

    for source_line in group_source_lines(ordered_text_primitives):
        if not pending_primitives:
            pending_text = source_line.text
            pending_primitives = list(source_line.primitives)
            continue
        if breaks_paragraph(pending_text, source_line.text):
            paragraphs.append((pending_text.strip(), tuple(pending_primitives)))
            pending_text = source_line.text
            pending_primitives = list(source_line.primitives)
        else:
            pending_text = join_lines(pending_text, source_line.text)
            pending_primitives.extend(source_line.primitives)
    if pending_primitives:
        paragraphs.append((pending_text.strip(), tuple(pending_primitives)))

    # I paragrafi NON si riordinano: l'ordine ricevuto e' l'ordine di lettura, e
    # riordinarli per geometria lo scavalcherebbe. Le note si inseriscono
    # DAVANTI al primo paragrafo che sta sotto di loro, senza spostare il testo
    # -- stesso schema del consumer che ha prodotto la base.
    #
    # Una versione precedente ordinava tutto per (y0, x0). Passava sulle pagine a
    # colonna singola, dove geometria e lettura coincidono, e falliva su 4 pagine
    # su 10 del campione. Trovato da E-B alla prima esecuzione.
    paragraph_of_primitive: dict[int, int] = {}
    consumed = 0
    for paragraph_index, (_text, primitives) in enumerate(paragraphs):
        for _primitive in primitives:
            paragraph_of_primitive[consumed] = paragraph_index
            consumed += 1

    notes_by_rank: dict[int, list[AssetNoteInput]] = {}
    for note in asset_notes:
        rank = paragraph_of_primitive.get(note.anchor_index, len(paragraphs))
        notes_by_rank.setdefault(rank, []).append(note)

    items: list[tuple[str, object]] = []
    for index, paragraph in enumerate(paragraphs):
        for note in sorted(notes_by_rank.get(index, ()), key=lambda item: item.anchor_index):
            items.append(("asset", note))
        items.append(("text", paragraph))
    for note in sorted(
        notes_by_rank.get(len(paragraphs), ()), key=lambda item: item.anchor_index
    ):
        items.append(("asset", note))

    nodes: list[NodeIR2] = []
    for order, (kind, payload) in enumerate(items):
        if kind == "text":
            text, primitives = payload  # type: ignore[misc]
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
                    kind=KIND_TEXT_PARAGRAPH,
                    primitive_ids=tuple(item.primitive_id for item in primitives),
                    page_ids=(page_id,),
                    text=text,
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

    return PageIR2(page_id=page_id, nodes=tuple(nodes))
