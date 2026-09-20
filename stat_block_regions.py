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
   senza nome il piu' ampio; ogni riga sta in al piu' una scheda.** La scheda e'
   l'oggetto intero, non il suo blocco dei campi, che il nome non lo contiene.
   La prima forma -- «vince quello con piu' righe» -- sceglieva un riquadro che
   copre la scheda **e** il suo intorno: su Dragonbane idx 31 l'illustrazione del
   pipistrello (56 righe contro le 28 della pergamena), su DB idx 116 un riquadro
   che copre il box dei goblin e la tabella degli eventi accanto (58 righe).
   Regola misurata al passo 3b (`Esito_NotaSfondoScheda_v1.md`, ramo in
   sospeso) e ripresa senza la nota degli sfondi.

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
"""

from __future__ import annotations

import unicodedata
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
    possono portare lo stesso.
    """

    bbox: BBox
    candidate_id: str
    line_indices: tuple[int, ...]
    name_line_indices: tuple[int, ...]
    signature: frozenset[str] = frozenset()


def _style(primitive: TextPrimitive) -> Style:
    """Lo stile come identita': font senza prefisso di sottoinsieme, dimensione
    a un decimale, colore. Conta solo l'uguaglianza fra stili."""

    name = (primitive.font_name or "").split("+")[-1]
    return (name, round(primitive.font_size or 0.0, 1), primitive.color)


def _spans(line: Sequence[TextPrimitive]) -> list[TextPrimitive]:
    """Gli span che portano caratteri: le sole spaziature non hanno stile che
    conti, e `pila2` le scartava gia' costruendo le righe."""

    return [primitive for primitive in line if primitive.text.strip()]


def label_spans(line: Sequence[TextPrimitive]) -> list[TextPrimitive]:
    """Gli span-etichetta delle coppie etichetta/valore di una riga, in ordine.

    Uno span e' un'etichetta se quello successivo ha stile diverso; il valore
    e' la corsa di span in quello stile, e la scansione riprende dopo. Non
    dipende dai due punti -- un formato che scrive `PF 5` li farebbe mancare
    tutti -- ne' da una dimensione. Un'etichetta fatta dei soli due punti non
    conta."""

    spans = _spans(line)
    styles = [_style(span) for span in spans]
    labels: list[TextPrimitive] = []
    index = 0
    while index + 1 < len(spans):
        if styles[index] == styles[index + 1]:
            index += 1
            continue
        end = index + 1
        while end + 1 < len(spans) and styles[end + 1] == styles[index + 1]:
            end += 1
        if spans[index].text.strip().rstrip(":").strip():
            labels.append(spans[index])
        index = end + 1
    return labels


def line_labels(line: Sequence[TextPrimitive]) -> list[str]:
    """Il testo delle etichette di `label_spans`, senza spazi ai lati e senza i
    due punti finali."""

    return [span.text.strip().rstrip(":").strip() for span in label_spans(line)]


def normalised_label(text: str) -> str:
    """L'etichetta come identita' di struttura: NFKC, senza spazi, minuscole,
    senza i due punti finali. `Diﬃ  culty` e `Difficulty` sono la stessa."""

    return "".join(unicodedata.normalize("NFKC", text).casefold().split()).rstrip(":")


def field_labels(line: Sequence[TextPrimitive]) -> list[TextPrimitive]:
    """Le etichette di `label_spans` che portano almeno una lettera o una cifra.

    Un'etichetta senza nessuna delle due e' un marcatore d'elenco -- il `✦` di
    Dragonbane -- ed e' la regola con cui il giro sperimentale li desumeva dal
    documento. Contata come etichetta, faceva ricorrere fra loro box che hanno
    in comune solo il punto elenco."""

    return [span for span in label_spans(line) if any(c.isalnum() for c in span.text)]


def label_pairs(line: Sequence[TextPrimitive]) -> int:
    """Quante coppie etichetta/valore porta una riga: `line_labels`, contate."""

    return len(line_labels(line))


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
) -> list[BBox]:
    """I riquadri dentro un candidato, o il candidato stesso se ce n'e' uno.

    I **massimali** sono i membri il cui bbox non sta dentro quello di un altro
    membro con bbox diverso: due membri con lo stesso bbox -- il fondo e il suo
    contorno -- restano entrambi, e condividendo le righe si uniscono. Contano
    solo i massimali che contengono almeno una riga. Se ne restano almeno due il
    candidato si separa; altrimenti resta **com'e'**, e il suo bbox non cambia.
    """

    members = [visual_boxes[pid] for pid in frame.primitive_ids if pid in visual_boxes]
    maximal = [
        box
        for box in members
        if not any(other != box and _contains(other, box) for other in members)
    ]
    groups: list[tuple[BBox, set[int]]] = []
    for box in maximal:
        inside = {
            index
            for index, line_box in enumerate(line_boxes)
            if line_box is not None and _centre_inside(box, line_box)
        }
        if not inside:
            continue
        merged = box
        for group in [group for group in groups if group[1] & inside]:
            groups.remove(group)
            merged = _union(merged, group[0])
            inside |= group[1]
        groups.append((merged, inside))
    if len(groups) < 2:
        return [frame.bbox]
    return [box for box, _inside in sorted(groups, key=lambda group: (group[0][1], group[0][0]))]


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
    """Le schede della pagina dai riquadri disegnati (la regola di 3a), in ordine
    di lettura.

    ``frames`` sono i candidati dei producer visivi, ``visual_boxes`` il bbox di
    ogni primitiva visiva della pagina, ``lines`` le righe di sorgente
    nell'ordine di lettura del chiamante. Una riga senza caratteri non ha bbox e
    non appartiene a nessun riquadro. La regola dalla struttura ripetuta, che non
    ha bisogno di riquadri, e' `stat_blocks_from_structures`."""

    line_boxes = [_line_bbox(line) for line in lines]
    pairs = [label_pairs(line) for line in lines]
    labels = [field_labels(line) for line in lines]
    two_pair_lines = {index for index, count in enumerate(pairs) if count >= 2}

    proposals: list[tuple[BBox, str, tuple[int, ...], tuple[int, ...]]] = []
    for frame in frames:
        for piece in split_frame(frame, visual_boxes, line_boxes):
            inside = tuple(
                index
                for index, line_box in enumerate(line_boxes)
                if line_box is not None and _centre_inside(piece, line_box)
            )
            if not inside:
                continue
            if len(two_pair_lines.intersection(inside)) >= 2:
                proposals.append(
                    (piece, frame.candidate_id, inside, _name_lines(lines, inside, pairs))
                )

    # Prima le proposte con un nome, dalla piu' stretta; poi quelle senza, dalla
    # piu' ampia. A parita', l'ordine di lettura.
    proposals.sort(
        key=lambda proposal: (
            (0, len(proposal[2])) if proposal[3] else (1, -len(proposal[2])),
            proposal[2][0],
        )
    )
    taken: set[int] = set()
    regions: list[StatBlockRegion] = []
    for piece, candidate_id, inside, name in proposals:
        if taken.intersection(inside):
            continue
        taken.update(inside)
        regions.append(
            StatBlockRegion(
                bbox=piece,
                candidate_id=candidate_id,
                line_indices=inside,
                name_line_indices=name,
                signature=frozenset(
                    normalised_label(span.text) for index in inside for span in labels[index]
                ),
            )
        )
    regions.sort(key=lambda region: region.line_indices[0])
    return tuple(regions)


@dataclass(frozen=True, slots=True)
class LineFacts:
    """Cio' che la regola dalla struttura ripetuta legge di una riga.

    Si calcola per ogni riga di ogni pagina nella prima passata di `main_ir2` e
    passa fra processi, quindi porta solo valori semplici. Una riga di sole
    spaziature ha ``style`` e ``bbox`` a ``None``."""

    style: Style | None
    text: str
    labels: tuple[str, ...]
    label_starts: tuple[tuple[float, float], ...]
    bbox: BBox | None
    # Per ogni etichetta: se il suo testo **si dichiara** etichetta, cioe' se
    # finisce con i due punti. `field_labels` rileva alternanze di stile, non
    # campi, e su una riga andata a capo che contiene una parola in grassetto
    # chiama «etichetta» tutto il testo che la precede. Chi si appoggia a una
    # SINGOLA etichetta — e non alla ripetizione di una combinazione — ha
    # bisogno di distinguerle: `Criterio_RigheDellaSchedaACapo_v1.md` §5.
    label_declares: tuple[bool, ...] = ()


def line_facts(line: Sequence[TextPrimitive]) -> LineFacts:
    """Stile d'apertura, testo, etichette normalizzate con il loro x0 e la
    larghezza media di un loro carattere."""

    spans = _spans(line)
    if not spans:
        return LineFacts(None, "", (), (), None)
    found = [
        (label, span)
        for label, span in ((normalised_label(s.text), s) for s in field_labels(line))
        if label
    ]
    return LineFacts(
        style=_style(spans[0]),
        text="".join(primitive.text for primitive in line).strip(),
        labels=tuple(label for label, _span in found),
        label_starts=tuple(
            (span.bbox[0], (span.bbox[2] - span.bbox[0]) / max(len(span.text.strip()), 1))
            for _label, span in found
        ),
        label_declares=tuple(
            span.text.strip().endswith(":") for _label, span in found
        ),
        bbox=_line_bbox(line),
    )


@dataclass(frozen=True, slots=True)
class RepeatedStructure:
    """Una struttura che si ripete nel documento: le sue etichette e lo stile del
    nome che la intesta (``None`` se nessuno stile la precede regolarmente)."""

    labels: frozenset[str]
    head_style: Style | None


def _bound_label_groups(pages: Mapping[int, Sequence[LineFacts]]) -> list[frozenset[str]]:
    """Le etichette che si contano insieme.

    Due etichette sono legate se compaiono insieme su almeno tre pagine («varie
    volte», indicazione dell'utente) e, sulle pagine dove compare la piu' rara
    delle due, hanno lo stesso conteggio nella maggioranza dei casi. E' il segnale
    senza soglie misurato in `esperimenti_statblock/strutture_contate.py`: una
    pagina di Draw Steel con 4 mostri ha 4 Immunity, 4 Movement e 4 Weakness ma 11
    Effect; una di Daggerheart con 12 avversari ha 12 Difficulty e 12 Thresholds."""

    counts: dict[str, dict[int, int]] = {}
    for index, lines in pages.items():
        for facts in lines:
            for label in facts.labels:
                per_page = counts.setdefault(label, {})
                per_page[index] = per_page.get(index, 0) + 1
    labels = [label for label, per_page in counts.items() if len(per_page) >= 3]
    near: dict[str, set[str]] = {label: set() for label in labels}
    for position, first in enumerate(labels):
        pages_first = counts[first]
        for second in labels[position + 1 :]:
            pages_second = counts[second]
            if len(pages_first.keys() & pages_second.keys()) < 3:
                continue
            rarer = pages_first if len(pages_first) <= len(pages_second) else pages_second
            equal = sum(
                1 for page in rarer if pages_first.get(page, 0) == pages_second.get(page, 0)
            )
            if equal * 2 > len(rarer):
                near[first].add(second)
                near[second].add(first)
    seen: set[str] = set()
    groups: list[frozenset[str]] = []
    for start in labels:
        if start in seen or not near[start]:
            continue
        stack, group = [start], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            group.add(node)
            stack.extend(near[node] - seen)
        groups.append(frozenset(group))
    return groups


def _instances(lines: Sequence[LineFacts], labels: frozenset[str]) -> list[tuple[int, int]]:
    """(prima, ultima riga con etichette) delle istanze di una struttura su una pagina.

    Un'istanza nuova comincia quando un'etichetta gia' vista nell'istanza corrente
    ricompare, e un'istanza deve portare almeno due etichette diverse: una sola e'
    una parola in grassetto, non la struttura."""

    found: list[tuple[int, int]] = []
    start = last = -1
    seen: set[str] = set()
    for position, facts in enumerate(lines):
        here = labels.intersection(facts.labels)
        if not here:
            continue
        if start >= 0 and here & seen:
            if len(seen) >= 2:
                found.append((start, last))
            start, seen = -1, set()
        if start < 0:
            start = position
        seen |= here
        last = position
    if start >= 0 and len(seen) >= 2:
        found.append((start, last))
    return found


def _table_like(lines: Sequence[LineFacts], first: int, last: int, labels: frozenset[str]) -> bool:
    """«Righe tutte ordinate», dall'indicazione dell'utente sulle tabelle: ogni riga
    con etichette della struttura ne porta una sola, e ogni etichetta ha almeno
    un'altra etichetta dell'istanza alla stessa x entro un carattere -- stanno in
    colonna, come le proprieta' delle armi di Daggerheart. In una scheda almeno una
    riga porta piu' etichette, o un'etichetta sta da sola nella sua x."""

    starts: list[tuple[float, float]] = []
    for facts in lines[first : last + 1]:
        mine = [
            start
            for label, start in zip(facts.labels, facts.label_starts, strict=True)
            if label in labels
        ]
        if not mine:
            continue
        if len(mine) > 1:
            return False
        starts.append(mine[0])
    if len(starts) < 2:
        return False
    return all(
        any(
            other != mine and abs(start - other_start) < min(width, other_width)
            for other, (other_start, other_width) in enumerate(starts)
        )
        for mine, (start, width) in enumerate(starts)
    )


def repeated_structures(
    pages: Mapping[int, Sequence[LineFacts]],
) -> tuple[RepeatedStructure, ...]:
    """Le strutture che si ripetono nel documento, in ordine di precedenza.

    Una struttura e' un gruppo di etichette legate (`_bound_label_groups`) con
    almeno tre istanze nel documento. Le strutture con piu' istanze si prendono le
    righe per prime -- con la loro coda, fino all'istanza successiva -- e cosi' i
    frammenti di glifi dentro le capacita' di Draw Steel non fanno strutture a
    parte. Una struttura le cui istanze sono in maggioranza «a righe ordinate» e'
    una tabella e non entra. Il nome: fra gli stili presenti nella maggioranza
    degli spazi che precedono le istanze, il piu' grande."""

    ordered = sorted(pages)
    candidates = []
    for labels in _bound_label_groups(pages):
        found = [
            (index, first, last)
            for index in ordered
            for first, last in _instances(pages[index], labels)
        ]
        if len(found) >= 3:
            candidates.append((labels, found))
    candidates.sort(key=lambda candidate: len(candidate[1]), reverse=True)

    taken: dict[int, set[int]] = {}
    result: list[RepeatedStructure] = []
    for labels, found in candidates:
        kept = [
            (index, first, last)
            for index, first, last in found
            if not taken.get(index, set()).intersection(range(first, last + 1))
        ]
        if len(kept) < 3:
            continue
        tables = sum(1 for index, first, last in kept if _table_like(pages[index], first, last, labels))
        if tables * 2 > len(kept):
            continue
        presence: dict[Style, int] = {}
        previous: dict[int, int] = {}
        for index, first, last in sorted(kept):
            start = previous.get(index, -1) + 1
            styles = {
                facts.style
                for facts in pages[index][start:first]
                if facts.style is not None and not facts.labels
            }
            for style in styles:
                presence[style] = presence.get(style, 0) + 1
            previous[index] = last
        majority = [style for style, count in presence.items() if count * 2 > len(kept)]
        head = max(majority, key=lambda style: style[1]) if majority else None
        result.append(RepeatedStructure(labels=labels, head_style=head))
        by_page: dict[int, list[tuple[int, int]]] = {}
        for index, first, last in kept:
            by_page.setdefault(index, []).append((first, last))
        for index, spans in by_page.items():
            spans.sort()
            for position, (first, last) in enumerate(spans):
                end = spans[position + 1][0] - 1 if position + 1 < len(spans) else last
                taken.setdefault(index, set()).update(range(first, end + 1))
    return tuple(result)


def _block_tail(
    lines: Sequence[LineFacts],
    last: int,
    limit: int,
    breaks: frozenset[int],
    block: BBox,
    frames: Sequence[BBox],
) -> list[int]:
    """Le righe della parte libera: dopo l'ultima riga con etichette la scheda
    continua fino alla prima **interruzione**, e comunque non oltre ``limit``:

    - una riga in ``breaks``: un nome o una riga a dimensione di titolo;
    - se la scheda sta in un riquadro, la prima riga fuori dal riquadro;
    Le righe dentro un **riquadro estraneo** si saltano, senza chiudere la scheda:
    su DrM idx 43 il box laterale «Angulotl Tactics» sta, nell'ordine di lettura,
    in mezzo alla scheda di Angulotl Wave. Estraneo vuol dire che porta almeno due
    righe -- come le due righe del criterio: la fascia dietro il nome di una
    capacita' di Draw Steel e' di una riga sola -- e non tocca ne' la scheda ne' un
    riquadro che la tocca: la pergamena degli attacchi dei Pipistrelli esce di 8 pt
    da quella della scheda, ma la tocca."""

    def overlaps(first: BBox, second: BBox) -> bool:
        return min(first[2], second[2]) > max(first[0], second[0]) and min(
            first[3], second[3]
        ) > max(first[1], second[1])

    own = min(
        (piece for piece in frames if _contains(piece, block)),
        key=lambda piece: (piece[2] - piece[0]) * (piece[3] - piece[1]),
        default=None,
    )
    touching = [piece for piece in frames if overlaps(piece, block)]
    others = [
        piece
        for piece in frames
        if not overlaps(piece, block)
        and not any(overlaps(outer, piece) for outer in touching)
        and sum(1 for facts in lines if facts.bbox is not None and _centre_inside(piece, facts.bbox)) >= 2
    ]
    tail: list[int] = []
    for position in range(last + 1, limit + 1):
        box = lines[position].bbox
        if position in breaks:
            break
        if box is not None:
            if own is not None and not _centre_inside(own, box):
                break
            if any(_centre_inside(piece, box) for piece in others):
                continue
        tail.append(position)
    return tail


def stat_blocks_from_structures(
    lines: Sequence[LineFacts],
    structures: Sequence[RepeatedStructure],
    heading_sizes: frozenset[float] = frozenset(),
    frames: Sequence[BBox] = (),
) -> tuple[StatBlockRegion, ...]:
    """Le schede di una pagina dalle strutture ripetute del documento, senza riquadri.

    Per ogni struttura, in ordine di precedenza, le istanze della pagina che non
    toccano righe gia' prese. Il **nome** e' la riga piu' vicina prima
    dell'istanza nello stile del nome della struttura, con le righe consecutive
    dello stesso stile sopra di lei: un nome che va a capo e' un nome solo. La
    scheda va dal nome fino alla riga prima della scheda successiva della stessa
    struttura; il ``bbox`` copre il nome e le righe con etichette, non la coda,
    perche' la tabella degli attacchi che segue la scheda resti una tabella.

    **La fine della scheda** (`_block_end`, indicazione dell'utente del 14
    settembre: struttura che si ripete, poi una parte libera, poi la prosa). Gli
    stili non la separano -- misurato in `esperimenti_statblock/fine_scheda.py`,
    la parte libera usa gli stili della prosa -- quindi la scheda finisce a cio'
    che la interrompe: il nome di un'altra scheda, una riga alla dimensione di una
    fascia di titolo del documento (``heading_sizes``, le fasce dello script dei
    titoli), il bordo del riquadro che la contiene quando c'e' (``frames``), la
    scheda successiva, la fine della pagina."""

    taken: set[int] = set()
    regions: list[StatBlockRegion] = []
    for number, structure in enumerate(structures):
        found = [
            (first, last)
            for first, last in _instances(lines, structure.labels)
            if not taken.intersection(range(first, last + 1))
        ]
        starts: list[int] = []
        names: list[tuple[int, ...]] = []
        previous = -1
        for first, last in found:
            name: list[int] = []
            if structure.head_style is not None:
                nearest = next(
                    (
                        position
                        for position in range(first - 1, previous, -1)
                        if lines[position].style == structure.head_style
                        and position not in taken
                    ),
                    None,
                )
                if nearest is not None:
                    name = [nearest]
                    while (
                        name[0] - 1 > previous
                        and lines[name[0] - 1].style == structure.head_style
                        and name[0] - 1 not in taken
                    ):
                        name.insert(0, name[0] - 1)
            starts.append(name[0] if name else first)
            names.append(tuple(name))
            previous = last
        head_positions = frozenset(
            index
            for other in structures
            if other.head_style is not None
            for index, facts in enumerate(lines)
            if facts.style == other.head_style
        )
        breaks = head_positions | frozenset(
            index
            for index, facts in enumerate(lines)
            if facts.style is not None and facts.style[1] in heading_sizes
        )
        for position, (_first, last) in enumerate(found):
            start = starts[position]
            limit = starts[position + 1] - 1 if position + 1 < len(found) else len(lines) - 1
            boxes = [
                box
                for index in range(start, last + 1)
                if (box := lines[index].bbox) is not None
                and (index in names[position] or lines[index].labels)
            ]
            if not boxes:
                continue
            bbox = boxes[0]
            for box in boxes[1:]:
                bbox = _union(bbox, box)
            tail = _block_tail(lines, last, limit, breaks, bbox, frames)
            span = tuple(
                index for index in [*range(start, last + 1), *tail] if index not in taken
            )
            regions.append(
                StatBlockRegion(
                    bbox=bbox,
                    candidate_id=f"structure:{number}",
                    line_indices=span,
                    name_line_indices=names[position],
                    signature=structure.labels,
                )
            )
            taken.update(span)
    regions.sort(key=lambda region: region.line_indices[0])
    return tuple(regions)


def crossed_stat_blocks(
    bbox: BBox, regions: Sequence[StatBlockRegion]
) -> list[StatBlockRegion]:
    """Le schede il cui riquadro la regione tocca senza contenerle tutte dentro
    di se': cioe' quelle che una tabella attraversa. Una tabella **dentro** la
    scheda non la attraversa."""

    return [
        region
        for region in regions
        if min(bbox[2], region.bbox[2]) > max(bbox[0], region.bbox[0])
        and min(bbox[3], region.bbox[3]) > max(bbox[1], region.bbox[1])
        and not _contains(region.bbox, bbox)
    ]


def crosses_a_stat_block(bbox: BBox, regions: Sequence[StatBlockRegion]) -> bool:
    """Una tabella che attraversa il confine di almeno una scheda."""

    return bool(crossed_stat_blocks(bbox, regions))
