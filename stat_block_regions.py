"""Le schede statistiche: quali riquadri disegnati lo sono, e quale riga le intesta.

**Consumer, non producer.** Legge i candidati di due producer gia' wired --
`embedded_visual` e `interior_visual_frame`, cioe' i riquadri disegnati sulla
pagina -- e le righe di sorgente nell'ordine di lettura del chiamante. Che
relazione ci sia fra un riquadro e le righe che contiene si decide qui, non
dentro un producer: `AGENTS.MD` §Layout e candidati.

**I confini di una scheda non si deducono, si leggono**: il riquadro e'
disegnato sulla pagina. Tre regole, ognuna misurata prima su due manuali in
`esperimenti_statblock/`, e nessuna soglia: contenimento, stile e conteggio di
coppie sono relazioni o fatti della pagina.

1. **Il riquadro fuso si separa** (`CRITERIO_SEPARA_RIQUADRI.md`, accettato).
   Il raggruppamento vettoriale fonde riquadri vicini -- su Daggerheart schede
   distanti 8,6-9,9 pt uscivano come una colonna sola -- ma il candidato fuso
   porta i singoli riquadri nei suoi `primitive_ids`. I membri massimali che
   contengono righe sono pezzi distinti; quelli che condividono una riga sono
   lo stesso pezzo. Su Daggerheart le schede prese passano da 85 a 130 su 149,
   Dragonbane resta invariato.
2. **Un riquadro e' una scheda se contiene almeno due righe con almeno due
   coppie etichetta/valore.** E' l'appunto di `State.md` sulle schede di
   bestiario, «campi etichetta:valore da preservare», preso alla lettera. Una
   coppia e' uno span seguito da uno span di stile diverso, la regola di
   `esperimenti_statblock/pila2.py`. Con una coppia sola per riga passano
   prosa e tabelle: `RISULTATI_UNA_COPPIA.txt`, non accettato al giudizio a
   vista dell'utente.
3. **Fra riquadri sovrapposti vince il piu' stretto che contiene un nome, e
   senza nome il piu' ampio; ogni riga sta in al piu' una scheda.** La scheda
   e' l'oggetto intero, non il suo blocco dei campi, che il nome non lo contiene.
   La prima forma -- «vince quello con piu' righe» -- e' caduta al passo 3b
   (`Esito_NotaSfondoScheda_v1.md`): su Dragonbane idx 31 l'illustrazione del
   pipistrello copre la pergamena della scheda e anche il testo della stanza
   accanto, 56 righe contro 28, e vinceva lei. Sulle 141 schede dei tre
   intervalli di sviluppo e' l'unica che cambia.

Il **nome** e' la prima riga della scheda, se non porta coppie, piu' le righe
che la seguono **subito**, nell'ordine di lettura, nello stesso stile -- un
nome che va a capo e' un nome solo -- e solo se quello stile **non ricompare**
nella scheda fuori dal nome. E' la condizione dei titoli di
`Criterio_Titoli_v3.md`, «l'unica alla sua dimensione dentro il suo blocco».

Contiguita' e unicita' sono un emendamento dichiarato
(`Esito_SchedaInIR2_v1.md`), trovato dal controllo su DB: a p.98
un'illustrazione con sopra anche prosa passava da scheda, e la sua prima riga di
prosa diventava titolo insieme a una riga di un'altra colonna; a p.121 diventava
titolo l'etichetta della prima riga di una tabella. Misurato sui tre intervalli
di sviluppo: lo stile del nome non ricompare nella scheda in 136 schede su 136 di
Daggerheart e Dragonbane. Dove sbagliano, sbagliano verso nessun titolo invece
che verso un titolo falso.

Ogni scheda porta anche i **membri del suo riquadro** (`frame_primitive_ids`):
sono le primitive che la nota dello sfondo sostituisce
(`Criterio_NotaSfondoScheda_v1.md`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from geometry_model import BBox
from primitive_model import TextPrimitive

type Style = tuple[str, float, object]


@dataclass(frozen=True, slots=True)
class FrameInput:
    """Un riquadro candidato, cosi' come lo dichiara il suo producer."""

    candidate_id: str
    bbox: BBox
    primitive_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StatBlockRegion:
    """Una scheda: il pezzo di riquadro che la delimita e le righe che contiene.

    ``line_indices`` e ``name_line_indices`` indicizzano le righe ricevute, in
    ordine di lettura. ``candidate_id`` e' il riquadro da cui la scheda viene:
    separare un candidato fuso non ne inventa uno nuovo, quindi piu' schede
    possono portare lo stesso. ``frame_primitive_ids`` sono i membri del pezzo:
    tutti quelli del candidato se non si e' separato, i massimali del pezzo se
    si e' separato.
    """

    bbox: BBox
    candidate_id: str
    frame_primitive_ids: tuple[str, ...]
    line_indices: tuple[int, ...]
    name_line_indices: tuple[int, ...]


def _style(primitive: TextPrimitive) -> Style:
    """Lo stile come identita': font senza prefisso di sottoinsieme, dimensione
    a un decimale, colore. Conta solo l'uguaglianza fra stili."""

    name = (primitive.font_name or "").split("+")[-1]
    return (name, round(primitive.font_size or 0.0, 1), primitive.color)


def _spans(line: Sequence[TextPrimitive]) -> list[TextPrimitive]:
    """Gli span che portano caratteri: le sole spaziature non hanno stile che
    conti, e `pila2` le scartava gia' costruendo le righe."""

    return [primitive for primitive in line if primitive.text.strip()]


def label_pairs(line: Sequence[TextPrimitive]) -> int:
    """Quante coppie etichetta/valore porta una riga.

    Uno span e' un'etichetta se quello successivo ha stile diverso; il valore
    e' la corsa di span in quello stile, e la scansione riprende dopo. Non
    dipende dai due punti -- un formato che scrive `PF 5` li farebbe mancare
    tutti -- ne' da una dimensione. Un'etichetta fatta dei soli due punti non
    conta."""

    spans = _spans(line)
    styles = [_style(span) for span in spans]
    pairs = 0
    index = 0
    while index + 1 < len(spans):
        if styles[index] == styles[index + 1]:
            index += 1
            continue
        end = index + 1
        while end + 1 < len(spans) and styles[end + 1] == styles[index + 1]:
            end += 1
        if spans[index].text.strip().rstrip(":").strip():
            pairs += 1
        index = end + 1
    return pairs


def _line_bbox(line: Sequence[TextPrimitive]) -> BBox | None:
    spans = _spans(line)
    if not spans:
        return None
    return (
        min(span.bbox[0] for span in spans),
        min(span.bbox[1] for span in spans),
        max(span.bbox[2] for span in spans),
        max(span.bbox[3] for span in spans),
    )


def _centre_inside(outer: BBox, inner: BBox) -> bool:
    """La riga sta nel riquadro se il suo CENTRO ci cade: la stessa regola di
    appartenenza di `page_analysis_column_band.py` e dell'esperimento."""

    x = (inner[0] + inner[2]) / 2
    y = (inner[1] + inner[3]) / 2
    return outer[0] <= x < outer[2] and outer[1] <= y < outer[3]


def _contains(outer: BBox, inner: BBox) -> bool:
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


def _union(first: BBox, second: BBox) -> BBox:
    return (
        min(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        max(first[3], second[3]),
    )


def split_frame(
    frame: FrameInput,
    visual_boxes: Mapping[str, BBox],
    line_boxes: Sequence[BBox | None],
) -> list[tuple[BBox, tuple[str, ...]]]:
    """I riquadri dentro un candidato, ciascuno coi suoi membri, o il candidato
    stesso se ce n'e' uno.

    I **massimali** sono i membri il cui bbox non sta dentro quello di un altro
    membro con bbox diverso: due membri con lo stesso bbox -- il fondo e il suo
    contorno -- restano entrambi, e condividendo le righe si uniscono. Contano
    solo i massimali che contengono almeno una riga. Se ne restano almeno due il
    candidato si separa; altrimenti resta **com'e'**, col suo bbox e tutti i suoi
    membri.
    """

    members = [
        (pid, visual_boxes[pid]) for pid in frame.primitive_ids if pid in visual_boxes
    ]
    maximal = [
        (pid, box)
        for pid, box in members
        if not any(other != box and _contains(other, box) for _other_pid, other in members)
    ]
    groups: list[tuple[BBox, set[int], list[str]]] = []
    for pid, box in maximal:
        inside = {
            index
            for index, line_box in enumerate(line_boxes)
            if line_box is not None and _centre_inside(box, line_box)
        }
        if not inside:
            continue
        merged = box
        ids = [pid]
        for group in [group for group in groups if group[1] & inside]:
            groups.remove(group)
            merged = _union(merged, group[0])
            inside |= group[1]
            ids = group[2] + ids
        groups.append((merged, inside, ids))
    if len(groups) < 2:
        return [(frame.bbox, frame.primitive_ids)]
    groups.sort(key=lambda group: (group[0][1], group[0][0]))
    return [(box, tuple(sorted(ids))) for box, _inside, ids in groups]


def _name_lines(
    lines: Sequence[Sequence[TextPrimitive]],
    inside: tuple[int, ...],
    pairs: Sequence[int],
) -> tuple[int, ...]:
    first = inside[0]
    if pairs[first]:
        return ()
    style = _style(_spans(lines[first])[0])
    names = [first]
    for index in inside[1:]:
        if index != names[-1] + 1:
            break
        if pairs[index] or _style(_spans(lines[index])[0]) != style:
            break
        names.append(index)
    named = set(names)
    if any(
        _style(span) == style
        for index in inside
        if index not in named
        for span in _spans(lines[index])
    ):
        return ()
    return tuple(names)


def stat_block_regions(
    frames: Sequence[FrameInput],
    visual_boxes: Mapping[str, BBox],
    lines: Sequence[Sequence[TextPrimitive]],
) -> tuple[StatBlockRegion, ...]:
    """Le schede della pagina, in ordine di lettura.

    ``frames`` sono i candidati dei producer visivi, ``visual_boxes`` il bbox di
    ogni primitiva visiva della pagina, ``lines`` le righe di sorgente
    nell'ordine di lettura del chiamante. Una riga senza caratteri non ha bbox e
    non appartiene a nessun riquadro."""

    line_boxes = [_line_bbox(line) for line in lines]
    pairs = [label_pairs(line) for line in lines]
    field_lines = {index for index, count in enumerate(pairs) if count >= 2}

    proposals: list[tuple[BBox, str, tuple[str, ...], tuple[int, ...], tuple[int, ...]]] = []
    for frame in frames:
        for piece, members in split_frame(frame, visual_boxes, line_boxes):
            inside = tuple(
                index
                for index, line_box in enumerate(line_boxes)
                if line_box is not None and _centre_inside(piece, line_box)
            )
            if len(field_lines.intersection(inside)) >= 2:
                proposals.append(
                    (piece, frame.candidate_id, members, inside, _name_lines(lines, inside, pairs))
                )

    # Prima le proposte con un nome, dalla piu' stretta; poi quelle senza, dalla
    # piu' ampia. A parita', l'ordine di lettura.
    proposals.sort(
        key=lambda proposal: (
            (0, len(proposal[3])) if proposal[4] else (1, -len(proposal[3])),
            proposal[3][0],
        )
    )
    taken: set[int] = set()
    regions: list[StatBlockRegion] = []
    for piece, candidate_id, members, inside, name in proposals:
        if taken.intersection(inside):
            continue
        taken.update(inside)
        regions.append(
            StatBlockRegion(
                bbox=piece,
                candidate_id=candidate_id,
                frame_primitive_ids=members,
                line_indices=inside,
                name_line_indices=name,
            )
        )
    regions.sort(key=lambda region: region.line_indices[0])
    return tuple(regions)


def crosses_a_stat_block(bbox: BBox, regions: Sequence[StatBlockRegion]) -> bool:
    """Una tabella che attraversa il confine di una scheda: si sovrappone al suo
    riquadro senza starci dentro.

    Su Daggerheart `table_candidate` copre colonne intere di tre schede, e una
    tabella cosi' e' sbagliata per costruzione. Una tabella **dentro** la scheda
    -- quella degli attacchi -- e' contenuto della scheda, e resta."""

    for region in regions:
        overlaps = min(bbox[2], region.bbox[2]) > max(bbox[0], region.bbox[0]) and min(
            bbox[3], region.bbox[3]
        ) > max(bbox[1], region.bbox[1])
        if overlaps and not _contains(region.bbox, bbox):
            return True
    return False
