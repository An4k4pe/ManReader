"""Che cosa apre le righe di un documento. Misura, non decide.

`Criterio_Elenchi_v1.md` §1. Osserva e riporta; la politica che decide quali
caratteri siano marcatori d'elenco sta in `document_list_policy`, separata per la
stessa ragione per cui lo sono la ricorrenza d'arredo e la sua politica: una
misura che decidesse non si potrebbe rileggere senza rileggere la decisione.

**Tre numeri per carattere, e ognuno serve a una condizione diversa.**

``opens_lines``
    Quante righe sorgente il carattere apre.

``occurrences``
    Quante volte compare **in tutto il testo**, a inizio riga e non.

``pages_opened``
    Su quante pagine distinte apre almeno una riga.

``opens_with_text``
    Quante di quelle righe hanno **del testo** dopo il marcatore -- sulla stessa
    riga, oppure sulla riga successiva quando il marcatore sta da solo.

I primi due danno il rapporto che separa un marcatore dalla punteggiatura, e non
e' una questione di quale carattere sia: misurato su 16 manuali, il marcatore
cambia da manuale a manuale ed e' spesso il codepoint di un font di simboli --
``✦`` su DB, ``\\x8b`` su BoB, ``!@#`` su DrM. Cio' che li accomuna e' **dove
vivono**: a inizio riga. La punteggiatura vive in mezzo alle frasi.

Il terzo distingue un elenco da un carattere capitato una volta: un elenco e' un
modo di comporre che il manuale usa, non un caso.

Il quarto e' quello che separa un marcatore da un ornamento, ed e' misurato: su
FW il `•` sta **da solo sulla sua riga** 41 volte su 41, e il testo della voce e'
la riga dopo; su Kul il `.` sta da solo 1096 volte su 1098 e la riga dopo e' **un
altro punto** -- una fila di puntini decorativi. Guardare solo la riga del
marcatore li confondeva.

**Una condizione provata e caduta, tenuta a verbale**: la prima versione chiedeva
due righe nello **stesso blocco sorgente**, come «il minimo che fa di un elenco
un elenco». Misurata, era falsa: su DB `✦` apre 312 righe e ha **zero** blocchi
con due, perche' ogni voce e' un blocco a se'. La condizione uccideva i marcatori
veri di DB, BoB, DrM e Apo e lasciava passare `.` di Kul.

**Un carattere puo' essere marcatore e punteggiatura nello stesso manuale.** Su
DrM ``!`` apre 45 righe come marcatore e compare in altre 29 come punto
esclamativo. La misura riporta entrambi i numeri senza sceglierne uno.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from primitive_model import NormalizedPrimitivePage

_OBSERVATION = re.compile(r"^text:(b\d+):(l\d+):s\d+$")


@dataclass(frozen=True, slots=True)
class LineStartMeasurements:
    """I tre conteggi per carattere, piu' quante righe sono state guardate."""

    opens_lines: dict[str, int]
    occurrences: dict[str, int]
    pages_opened: dict[str, int]
    opens_with_text: dict[str, int]
    line_count: int

    def __post_init__(self) -> None:
        if self.line_count < 0:
            raise ValueError("line_count cannot be negative")
        for name, counts in (
            ("opens_lines", self.opens_lines),
            ("occurrences", self.occurrences),
            ("pages_opened", self.pages_opened),
            ("opens_with_text", self.opens_with_text),
        ):
            for character, count in counts.items():
                if len(character) != 1:
                    raise ValueError(f"{name} keys must be single characters")
                if count < 0:
                    raise ValueError(f"{name} counts cannot be negative")

    def line_initial_share(self, character: str) -> float:
        """Quanta parte delle occorrenze sta a inizio riga. Zero se assente."""

        whole = self.occurrences.get(character, 0)
        return self.opens_lines.get(character, 0) / whole if whole else 0.0


def source_lines(page: NormalizedPrimitivePage) -> list[tuple[str, str]]:
    """(blocco, testo) per ogni riga sorgente, i pezzi in ordine di x.

    Una primitiva la cui osservazione non si legge come riga diventa una riga di
    se stessa in un blocco proprio: ignorarla la toglierebbe dai conteggi, e la
    misura direbbe di aver guardato piu' di quanto ha guardato.
    """

    grouped: dict[tuple[str, str], list] = defaultdict(list)
    loose: list[tuple[str, str]] = []
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match is None:
            loose.append((f"?{primitive.primitive_id}", primitive.text))
        else:
            grouped[(match.group(1), match.group(2))].append(primitive)

    lines = [
        (block, "".join(p.text for p in sorted(primitives, key=lambda z: z.bbox[0])))
        for (block, _line), primitives in grouped.items()
    ]
    return lines + loose


def _is_a_glyph_marker(primitive, character: str, body_font_name: str | None) -> bool:
    """La primitiva che apre la riga e' **il solo carattere**, in un font diverso.

    `Criterio_MarcatoreDaFont_v1.md`: su Fab il pallino e' la lettera `w` in
    `Wingdings-Regular`, e la condizione «non alfanumerico» non puo' vederlo.

    **Due condizioni, e la seconda l'ha imposta una misura.** Una prima versione
    cercava *una qualunque* primitiva con quel carattere sulla pagina: bastava un
    `M` isolato da qualche parte perche' ogni riga che comincia per `M` diventasse
    una voce, e FW passava da 57 voci a 92. Un pallino e' **una primitiva a se'**;
    una maiuscola in un font da titolo e' il primo carattere di una parola.
    """

    if body_font_name is None or primitive is None:
        return False
    if primitive.text.strip() != character:
        return False
    return primitive.font_name is not None and primitive.font_name != body_font_name


def _grouped_lines(page: NormalizedPrimitivePage) -> list[tuple[str, str, object]]:
    """(blocco, testo, prima primitiva) per ogni riga sorgente, in ordine di x."""

    grouped: dict[tuple[str, str], list] = defaultdict(list)
    loose: list[tuple[str, str, object]] = []
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match is None:
            loose.append((f"?{primitive.primitive_id}", primitive.text, primitive))
        else:
            grouped[(match.group(1), match.group(2))].append(primitive)

    lines: list[tuple[str, str, object]] = []
    for (block, _line), primitives in grouped.items():
        ordered = sorted(primitives, key=lambda z: z.bbox[0])
        lines.append((block, "".join(p.text for p in ordered), ordered[0]))
    return lines + loose


def measure_document_line_starts(
    pages: Sequence[NormalizedPrimitivePage],
    body_font_name: str | None = None,
) -> LineStartMeasurements:
    """I quattro conteggi su tutte le pagine date.

    `body_font_name` apre la **seconda via** del `Criterio_MarcatoreDaFont_v1.md`:
    un carattere alfanumerico conta come candidato se sta in un font diverso da
    quello del corpo. Senza, la misura si comporta come prima.
    """

    opens: Counter[str] = Counter()
    with_text: Counter[str] = Counter()
    occurrences: Counter[str] = Counter()
    on_pages: dict[str, set[int]] = defaultdict(set)
    # Per la via del font, numeratore e denominatore vanno tenuti **per font**:
    # e' l'unico modo perche' contino la stessa cosa. §1b del criterio.
    by_font: Counter[tuple[str, str | None]] = Counter()
    opens_by_font: Counter[tuple[str, str | None]] = Counter()
    seen = 0

    for index, page in enumerate(pages):
        grouped = _grouped_lines(page)
        lines = [text for _block, text, _first in grouped]
        openers = [first for _block, _text, first in grouped]
        # Il denominatore deve contare la **stessa cosa** del numeratore. Per un
        # candidato alfanumerico la cosa e' «questo carattere **in quel font**»:
        # contare tutte le `w` della prosa renderebbe la maggioranza
        # irraggiungibile per costruzione, e contarne zero la renderebbe
        # indefinita. `Criterio_MarcatoreDaFont_v1.md`.
        for primitive in page.text_primitives:
            other_font = (
                body_font_name is not None
                and primitive.font_name is not None
                and primitive.font_name != body_font_name
            )
            # **Il font sta nella chiave, non fuori.** `Criterio_MarcatoreDaFont_v2.md`
            # §1b. Il commento della v1 diceva gia' che il denominatore deve
            # contare «questo carattere IN QUEL FONT», ma l'implementazione
            # contava il carattere in un font qualunque diverso dal corpo.
            # Misurato su Vil: il pallino `h` in `NelsonOrnaments` apre 37 righe
            # su 82 occorrenze -- 45%, sotto la maggioranza -- e le altre 45 sono
            # `h` dentro parole in `ArnoPro-Bold`, che col pallino non c'entrano.
            for character in primitive.text:
                if character.isspace():
                    continue
                if character.isalnum():
                    if other_font:
                        by_font[(character, primitive.font_name)] += 1
                else:
                    occurrences[character] += 1

        for position, text in enumerate(lines):
            stripped = text.strip()
            if not stripped:
                continue
            seen += 1
            head = stripped[0]
            if head.isspace():
                continue
            # Per un candidato **alfanumerico** serve anche che il glifo sia
            # separato da cio' che segue. Misurato su FWK: `Bruinloa` ha la `B`
            # in un font decorativo, primitiva a se', ed e' una MAIUSCOLETTA
            # attaccata alla parola -- il manuale passava da 136 voci a 140.
            # Il vincolo vale solo per questa via: `✦Effetto Pieno:` di DB non ha
            # spazio ed entra dall'altra.
            #
            # **Separato vuol dire due cose, non una** -- `Criterio_MarcatoreDaFont_v2.md`.
            # O uno spazio lo separa, **oppure il glifo e' tutta la riga**: su Vil
            # il pallino e' `h` in `NelsonOrnaments` su una riga sua, e il testo
            # della voce e' la riga accanto. Una riga di un carattere e' separata
            # da cio' che segue piu' di quanto lo sia un glifo con lo spazio, e il
            # meccanismo sa gia' trattarla: e' da li' che entra `•` di FW.
            # Su FWK le 30 maiuscolette sono tutte ATTACCATE, zero da sole.
            if head.isalnum() and not (
                _is_a_glyph_marker(openers[position], head, body_font_name)
                and (len(stripped) == 1 or stripped[1].isspace())
            ):
                continue
            opens[head] += 1
            on_pages[head].add(index)
            if head.isalnum():
                opener = openers[position]
                opens_by_font[(head, getattr(opener, "font_name", None))] += 1

            if len(stripped) > 1:
                with_text[head] += 1
                continue
            # Il marcatore sta da solo sulla riga: il testo della voce, se c'e',
            # e' la riga dopo. Guardarla e' cio' che distingue il `•` di FW --
            # solo, e seguito dal testo della voce -- dal `.` di Kul, solo e
            # seguito da un altro punto.
            following = next(
                (line.strip() for line in lines[position + 1 :] if line.strip()), ""
            )
            if following and following[0] != head:
                with_text[head] += 1

    # Il denominatore di un candidato alfanumerico e' quante volte quel carattere
    # compare **nel font con cui apre le righe**: se apre in piu' font si prende
    # quello che apre di piu', perche' e' quello di cui si sta dicendo che e' un
    # marcatore.
    for (character, font), _count in opens_by_font.most_common():
        if character not in occurrences:
            occurrences[character] = by_font.get((character, font), 0)

    return LineStartMeasurements(
        opens_lines=dict(opens),
        occurrences=dict(occurrences),
        pages_opened={character: len(seen_on) for character, seen_on in on_pages.items()},
        opens_with_text=dict(with_text),
        line_count=seen,
    )


def block_marker_signature(
    page: NormalizedPrimitivePage, markers: frozenset[str]
) -> list[tuple[str, tuple[str, ...]]]:
    """(blocco, firma) per ogni blocco che apre almeno una riga con un candidato.

    La firma tiene l'**ordine** e le **ripetizioni**: ``('!', '@', '#')`` non e' la
    stessa cosa di ``('*', '*', '*')``, ed e' esattamente la differenza fra una
    scala di valori e un elenco (`Criterio_ScalaDiValori_v1.md` §1).
    """

    per_block: dict[str, dict[str, str]] = defaultdict(dict)
    for primitive in page.text_primitives:
        match = _OBSERVATION.match(primitive.source_observation_id or "")
        if match is None:
            continue
        block, line = match.group(1), match.group(2)
        per_block[block][line] = per_block[block].get(line, "") + primitive.text

    signatures: list[tuple[str, tuple[str, ...]]] = []
    for block, by_line in per_block.items():
        opening = [
            by_line[line].strip()[0]
            for line in sorted(by_line)
            if by_line[line].strip() and by_line[line].strip()[0] in markers
        ]
        if opening:
            signatures.append((block, tuple(opening)))
    return signatures


def count_block_signatures(
    pages: Sequence[NormalizedPrimitivePage], markers: frozenset[str]
) -> dict[tuple[str, ...], int]:
    """Quante volte ogni firma ricorre nel documento."""

    counted: Counter[tuple[str, ...]] = Counter()
    for page in pages:
        for _block, signature in block_marker_signature(page, markers):
            counted[signature] += 1
    return dict(counted)
