"""La seconda lettura della compilazione: i campi di una scheda, etichetta e valore.

`Criterio_CompilazioneScheda_v1.md`. Riceve le righe di sorgente della **parte a
campi** di una scheda, nell'ordine di lettura, e il modello della sua struttura
(`stat_block_regions.structure_templates`: quali testi ricorrono nella
maggioranza delle istanze). Restituisce i campi, ognuno con le sue primitive.

Nessuna soglia: coppie e vicinanze sono relazioni di stile o geometriche.

- **Corsa**: span consecutivi della riga nello stesso stile.
- **Coppia in linea**: una corsa con lettere o cifre seguita da una corsa di altro
  stile e' etichetta, e la seconda e' il valore -- la regola di
  `stat_block_regions.label_spans`. **L'etichetta continua** se il valore e' fatto
  di soli `:` (il Quickstart compone `PF` e `:` in due corpi), o se ha lettere o
  cifre ed e' seguito da un **terzo stile**: su Draw Steel `M` nel font dei glifi,
  ` ight` in grassetto e ` 0` in un altro peso sono `Might: 0`. La sovrapposizione
  degli span non lo distingue: `M` su ` ight` e' 0,24 pt, ma `Movimento:` su ` 24`
  in DB e' 0,36.
- **Coppia impilata**, sulle righe senza coppie in linea: uno span che ricorre
  nella maggioranza delle istanze prende come valore lo span sovrapposto in
  orizzontale piu' vicino sopra o sotto di lui, se ricorre meno. Le coppie si
  assegnano dalla piu' vicina, una volta sola: `Size` sotto `1S`.
- **Riga che continua**: una riga senza coppie, subito dopo una riga che finisce
  con un valore, nello stile di quel valore, sotto la coppia e sovrapposta a lei in
  orizzontale, lo prolunga (`surround, trail` su Daggerheart). Senza la
  sovrapposizione, su Draw Steel la colonna di destra continuava la sinistra. Le
  righe dopo la parte a campi (``tail``) entrano solo cosi', finche' continuano:
  su DB la seconda arma dei goblin va a capo sotto l'ultima etichetta.
- **Iniziale**: un'etichetta che comincia con un carattere solo, seguito da una
  corsa in minuscolo, si scrive senza spazio in mezzo (`M` + ` ight` = `Might`).
- **Righe in testa**: le righe prima della prima con un campo non entrano -- la
  descrizione in prosa di un mostro di Dragonbane resta un paragrafo.
- Le altre righe sono **valori senza etichetta**; un segno senza lettere ne' cifre
  va al campo prima.

L'ordine dei campi e' quello della pagina: righe di ancore dall'alto, poi da
sinistra. Il testo resta quello della sorgente, spaziature ridotte a uno spazio:
i `:` delle etichette e il separatore finale di un valore li toglie la resa.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from primitive_model import TextPrimitive
from stat_block_regions import Style, _style, normalised_label


@dataclass(frozen=True, slots=True)
class CompiledField:
    """Un campo: etichetta come stampata (vuota se il valore non ne ha), valore,
    e le primitive da cui vengono."""

    label: str
    value: str
    primitive_ids: tuple[str, ...]


@dataclass(slots=True)
class _Run:
    spans: list[TextPrimitive]

    @property
    def style(self) -> Style:
        return _style(self.spans[0])

    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)


@dataclass(slots=True)
class _Field:
    label: str
    value: str
    anchor: TextPrimitive
    spans: list[TextPrimitive]
    value_style: Style | None = None
    ids: list[str] = field(default_factory=list)


def _clean(text: str) -> str:
    return " ".join(text.split())


def _has_alnum(text: str) -> bool:
    return any(character.isalnum() for character in text)


def _space_join(left: str, right: str) -> str:
    return f"{left.rstrip()} {right.lstrip()}".strip()


def _runs(line: Sequence[TextPrimitive]) -> list[_Run]:
    runs: list[_Run] = []
    for span in line:
        if not span.text.strip():
            continue
        if runs and _style(span) == runs[-1].style:
            runs[-1].spans.append(span)
        else:
            runs.append(_Run([span]))
    return runs


def _inline(runs: list[_Run]) -> list[tuple[list[_Run], _Run | None]]:
    """Le coppie in linea di una riga, come (corse dell'etichetta, valore); una
    corsa rimasta sola ha valore ``None``."""

    items: list[tuple[list[_Run], _Run | None]] = []
    index = 0
    while index < len(runs):
        run = runs[index]
        if index + 1 >= len(runs) or not _has_alnum(run.text):
            items.append(([run], None))
            index += 1
            continue
        label = [run]
        value = index + 1
        while value + 1 < len(runs):
            text = runs[value].text.strip()
            if text == ":" or (_has_alnum(text) and runs[value + 1].style != run.style):
                label.append(runs[value])
                value += 1
                continue
            break
        items.append((label, runs[value]))
        index = value + 1
    return items


def _centre(span: TextPrimitive) -> float:
    return (span.bbox[1] + span.bbox[3]) / 2


def _overlaps(first: TextPrimitive, second: TextPrimitive) -> bool:
    return min(first.bbox[2], second.bbox[2]) > max(first.bbox[0], second.bbox[0])


def _join_label(runs: Sequence[_Run]) -> str:
    text = ""
    for run in runs:
        piece = _clean(run.text)
        if not piece:
            continue
        initial = len(text) == 1 and text.isalnum() and piece[0].islower()
        text = f"{text}{piece}" if not text or initial or piece.startswith(":") else f"{text} {piece}"
    return text


def _stacked_pairs(
    lines: Sequence[Sequence[TextPrimitive]],
    plain: Sequence[bool],
    recurrence: Mapping[str, int],
    instance_count: int,
) -> list[tuple[tuple[int, TextPrimitive], tuple[int, TextPrimitive]]]:
    """Le coppie impilate: ((riga, etichetta), (riga, valore)), dalla piu' vicina."""

    def recurs(span: TextPrimitive) -> int:
        return recurrence.get(normalised_label(span.text), 0)

    spans = [span for line in lines for span in line if span.text.strip()]
    candidates = {
        id(span): (position, span)
        for position, line in enumerate(lines)
        if plain[position]
        for span in line
        if _has_alnum(span.text)
    }
    proposals: list[tuple[float, int, int]] = []
    for _label_position, label in candidates.values():
        if recurs(label) * 2 <= instance_count:
            continue
        crossing = [other for other in spans if other is not label and _overlaps(label, other)]
        above = max((o for o in crossing if _centre(o) < _centre(label)), key=_centre, default=None)
        below = min((o for o in crossing if _centre(o) > _centre(label)), key=_centre, default=None)
        for neighbour in (above, below):
            if neighbour is None or id(neighbour) not in candidates:
                continue
            if recurs(neighbour) < recurs(label):
                proposals.append((abs(_centre(label) - _centre(neighbour)), id(label), id(neighbour)))
    used: set[int] = set()
    pairs = []
    for _distance, label_id, value_id in sorted(proposals):
        if label_id in used or value_id in used:
            continue
        used.update((label_id, value_id))
        pairs.append((candidates[label_id], candidates[value_id]))
    return pairs


def _continues(line: Sequence[TextPrimitive], last_value: _Field) -> bool:
    return (
        bool(line)
        and _style(line[0]) == last_value.value_style
        and _centre(line[0]) > _centre(last_value.anchor)
        and any(_overlaps(line[0], span) for span in last_value.spans)
    )


def compile_fields(
    lines: Sequence[Sequence[TextPrimitive]],
    recurrence: Mapping[str, int],
    instance_count: int,
    join: Callable[[str, str], str] = _space_join,
    tail: Sequence[Sequence[TextPrimitive]] = (),
) -> tuple[CompiledField, ...]:
    """I campi della parte a campi di una scheda. ``join`` unisce una riga che
    continua al valore prima: il costruttore passa la sua, che toglie la
    sillabazione."""

    per_line = [_inline(_runs(line)) for line in lines]
    plain = [all(value is None for _label, value in items) for items in per_line]
    stacked = _stacked_pairs(lines, plain, recurrence, instance_count)
    paired = {id(span) for pair in stacked for _position, span in pair}
    role_lines = {position for pair in stacked for position, _span in pair} | {
        position for position, is_plain in enumerate(plain) if not is_plain
    }
    if not role_lines:
        return ()
    first_line = min(role_lines)

    fields = [
        _Field(
            label=_clean(label.text),
            value=_clean(value.text),
            anchor=min(label, value, key=_centre),
            spans=[label, value],
        )
        for (_lp, label), (_vp, value) in stacked
    ]

    def loose(text: str, spans: list[TextPrimitive]) -> None:
        if not _has_alnum(text) and fields:
            fields[-1].value = f"{fields[-1].value} {text}".strip()
            fields[-1].spans.extend(spans)
        else:
            fields.append(_Field(label="", value=text, anchor=spans[0], spans=spans))

    last_value: _Field | None = None
    for position in range(first_line, len(lines)):
        if plain[position]:
            rest = [s for s in lines[position] if s.text.strip() and id(s) not in paired]
            if last_value is not None and _continues(rest, last_value):
                last_value.value = join(last_value.value, _clean("".join(s.text for s in rest)))
                last_value.spans.extend(rest)
                continue
            if rest:
                loose(_clean("".join(s.text for s in rest)), rest)
            last_value = None
            continue
        last_value = None
        for label_runs, value in per_line[position]:
            if value is None:
                loose(_clean(label_runs[0].text), list(label_runs[0].spans))
                last_value = None
                continue
            last_value = _Field(
                label=_join_label(label_runs),
                value=_clean(value.text),
                anchor=label_runs[0].spans[0],
                spans=[span for run in [*label_runs, value] for span in run.spans],
                value_style=value.style,
            )
            fields.append(last_value)
    taken = list(lines[first_line:])
    for line in tail:
        rest = [span for span in line if span.text.strip()]
        items = _inline(_runs(line))
        if any(value is not None for _label, value in items):
            break
        if not rest:
            taken.append(line)
            continue
        if last_value is None or not _continues(rest, last_value):
            break
        last_value.value = join(last_value.value, _clean("".join(s.text for s in rest)))
        last_value.spans.extend(rest)
        taken.append(line)

    # L'ordine della pagina: righe di ancore dall'alto, poi da sinistra.
    rows: list[list[_Field]] = []
    for item in sorted(fields, key=lambda item: (_centre(item.anchor), item.anchor.bbox[0])):
        top = rows[-1][0].anchor.bbox if rows else None
        if top is not None and top[1] <= _centre(item.anchor) <= top[3]:
            rows[-1].append(item)
        else:
            rows.append([item])
    fields = [item for row in rows for item in sorted(row, key=lambda item: item.anchor.bbox[0])]

    # Ogni primitiva delle righe prese sta in un campo: le spaziature col campo
    # dello span prima, o dopo se vengono in testa.
    owner = {id(span): position for position, item in enumerate(fields) for span in item.spans}
    previous: int | None = None
    pending: list[str] = []
    for line in taken:
        for primitive in line:
            position = owner.get(id(primitive))
            if position is None:
                if previous is None:
                    pending.append(primitive.primitive_id)
                else:
                    fields[previous].ids.append(primitive.primitive_id)
                continue
            fields[position].ids.extend(pending)
            pending = []
            fields[position].ids.append(primitive.primitive_id)
            previous = position
    return tuple(
        CompiledField(label=item.label, value=item.value, primitive_ids=tuple(item.ids))
        for item in fields
        if item.ids
    )
