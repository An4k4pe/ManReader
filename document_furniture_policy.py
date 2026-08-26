"""Quali slot di un documento sono arredo, secondo `Criterio_ArredoRicorrente_v3.md`.

**Politica, non misura.** `document_text_recurrence_measurements` osserva e non
decide; questo modulo decide, e sta separato per quello. Non tocca primitive, non
scrive niente su un nodo, non introduce nessun `kind`: restituisce **posizioni**,
e chi rende decide che farne.

Due rami, e il primo non ha parametri.

**Ramo 1 -- l'etichetta.** Il PDF dichiara il numero stampato di ogni pagina
(``page.get_label()``). Uno slot che porta l'etichetta **della propria pagina** su
almeno una frazione delle pagine e' lo slot del numero di pagina. Non c'e' un
vincolo di posizione: misurato sul corpus, BoB stampa il numero sul lato destro in
alto e Kul in cima, e una fascia bassa li perdeva entrambi. La guardia contro la
coincidenza -- su una pagina numerata ``6`` un ``6`` nel corpo combacia -- e' la
**ricorrenza dello slot**: lo stesso punto che porta l'etichetta della propria
pagina su un quarto delle pagine, ciascuna con la sua, che una collisione di
corpo non produce.

13 manuali su 16 dichiarano le etichette, e su tutti e 13 il ramo trova lo slot
(uno o due, che e' l'alternanza recto/verso). Dove il documento non dichiara
nulla il ramo non ha con che confrontare e **non rimuove niente**.

**Ramo 2 -- la ricorrenza al bordo.** Uno slot nella fascia inferiore, ricorrente
su almeno una frazione delle pagine. Entrambi i numeri vengono da
``extractor.filter_repeated_blocks`` -- ``header_footer_zone=0.08`` e
``repetition_threshold=0.25`` -- nei ruoli che il legacy gli da': la fascia
restringe alla zona, la frazione e' la soglia **di quella zona**. Prende filigrane,
intestazioni correnti, e i numeri dei manuali senza etichetta.

Solo la fascia bassa: quella alta tira dentro corpo su tre manuali su sei. Il
prezzo e' che i titoli correnti in cima restano, ed e' il verso giusto in cui
sbagliare, perche' l'errore opposto e' perdita di contenuto.

**La fascia da sola non basterebbe**, misurato: su Lan, senza la ricorrenza,
prende ``+1``, ``.``, ``La``, ``PNU Classe Student``. E' la ragione per cui il
ramo 2 e' document-level e non page-local.

**Ramo 3 -- la sequenza crescente**, `Criterio_NumeroDedotto_v1.md`. Dove il
documento non dichiara **nessuna** etichetta, il numero stampato si **deduce** da
uno slot che porta un numero crescente pagina dopo pagina. Chiude la caduta
misurata in `Esito_ArredoRicorrente_v1.md`: FW e FWK stampano il numero al centro
dei lati, dove ne' il ramo 1 (non ha con che confrontare) ne' il ramo 2 (guarda
solo la fascia bassa) arrivano, e stavano allo 0%.

Il ramo 3 **tace dove il documento dichiara**: li' il ramo 1 ha un fatto, e una
deduzione che gli si sovrapponesse sarebbe una congettura al posto di un dato.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from document_text_recurrence_measurements import (
    POSITION_GRID,
    DocumentTextRecurrenceMeasurements,
    normalize_text,
)
from primitive_model import NormalizedPrimitivePage, TextPrimitive

EDGE_BAND = 0.08
RECURRENCE_SHARE = 0.25
LABEL_SLACK = 3
# Cio' che il ramo 3 accetta come numero, prima di guardare se cresce. Le
# parentesi ci sono perche' Lan stampa `[99]`, ed e' lo stesso margine che
# `_carries_label` concede al ramo 1.
_NUMBER_STRIP = "[]() .-"

Slot = tuple[int, int]


def slot_of(primitive: TextPrimitive, page: NormalizedPrimitivePage) -> Slot:
    """La posizione quantizzata, come la calcola la misura."""

    width = page.page_geometry.width
    height = page.page_geometry.height
    return (
        round(primitive.bbox[0] / width * POSITION_GRID),
        round(primitive.bbox[1] / height * POSITION_GRID),
    )


def _carries_label(text: str, label: str) -> bool:
    """Il testo e' l'etichetta, con il margine che serve a `[99]` di Lan."""

    stripped = normalize_text(text)
    return bool(label) and label in stripped and len(stripped) <= len(label) + LABEL_SLACK


@dataclass(frozen=True, slots=True)
class FurnitureSlots:
    """Gli slot d'arredo di un documento, per ramo.

    Separati e non fusi perche' l'esito dei due rami si riporta distinto: uno non
    ha parametri e l'altro ne ha due, e un verbale che li sommasse renderebbe
    invisibile quale dei due ha deciso.
    """

    from_label: frozenset[Slot]
    from_recurrence: frozenset[Slot]
    from_sequence: frozenset[Slot] = frozenset()

    @property
    def all_slots(self) -> frozenset[Slot]:
        return self.from_label | self.from_recurrence | self.from_sequence


def label_slots(
    pages: Sequence[tuple[NormalizedPrimitivePage, str]],
    *,
    share: float = RECURRENCE_SHARE,
) -> frozenset[Slot]:
    """Ramo 1. `pages` accoppia una pagina alla sua etichetta dichiarata."""

    hits: dict[Slot, int] = {}
    with_label = 0
    for page, label in pages:
        label = label.strip()
        if not label:
            continue
        with_label += 1
        seen: set[Slot] = set()
        for primitive in page.text_primitives:
            if _carries_label(primitive.text, label):
                seen.add(slot_of(primitive, page))
        for slot in seen:
            hits[slot] = hits.get(slot, 0) + 1
    if not with_label:
        return frozenset()
    return frozenset(slot for slot, count in hits.items() if count >= with_label * share)


def recurrent_edge_slots(
    measurements: DocumentTextRecurrenceMeasurements,
    *,
    share: float = RECURRENCE_SHARE,
    band: float = EDGE_BAND,
) -> frozenset[Slot]:
    """Ramo 2, sulla misura gia' committata."""

    lower = POSITION_GRID * (1.0 - band)
    return frozenset(
        (slot.x, slot.y)
        for slot in measurements.occupied_on_at_least(share)
        if slot.y >= lower
    )


@dataclass(frozen=True, slots=True)
class DeducedNumbers:
    """L'esito del ramo 3: gli slot che portano il numero, e il numero per pagina.

    Vuoto quando la deduzione **rifiuta**, che e' una risposta e non un errore:
    un meccanismo che deduce sempre qualcosa non e' falsificabile.
    """

    slots: frozenset[Slot]
    by_page_position: dict[int, str]

    def __bool__(self) -> bool:
        return bool(self.slots)


def _as_number(text: str) -> int | None:
    stripped = normalize_text(text).strip(_NUMBER_STRIP)
    return int(stripped) if stripped.isdigit() else None


def _rising(values: dict[int, int]) -> bool:
    ordered = [values[k] for k in sorted(values)]
    return all(b > a for a, b in zip(ordered, ordered[1:], strict=False))


def deduced_number_slots(
    pages: Sequence[NormalizedPrimitivePage],
    *,
    share: float = RECURRENCE_SHARE,
) -> DeducedNumbers:
    """Ramo 3. `Criterio_NumeroDedotto_v1.md` §1.

    Il chiamante deve gia' aver stabilito che il documento non dichiara niente:
    questa funzione non vede le etichette, apposta, perche' e' la stessa funzione
    che il §5.A esegue sui 13 manuali che dichiarano per confrontarla con la
    verita' di riferimento. Se guardasse le etichette non ci sarebbe controllo.
    """

    per_slot: dict[Slot, dict[int, int]] = {}
    for position, page in enumerate(pages):
        for primitive in page.text_primitives:
            value = _as_number(primitive.text)
            if value is not None:
                per_slot.setdefault(slot_of(primitive, page), {})[position] = value

    minimum = len(pages) * share
    chosen: set[Slot] = set()
    merged: dict[int, int] = {}
    for slot, values in per_slot.items():
        if len(values) < minimum or not _rising(values):
            continue
        # Gli slot si fondono invece di competere: un numero a lati alterni vive
        # in due slot che sono la stessa cosa, e ogni slot ne porta meta'.
        #
        # Ma due slot che rivendicano la **stessa** pagina con valori diversi non
        # sono un numero alternato: sono due colonne, e qui non c'e' modo di
        # sapere quale sia la pagina. Rifiutare e' l'unica risposta onesta.
        if any(merged.get(k, v) != v for k, v in values.items()):
            return DeducedNumbers(frozenset(), {})
        merged.update(values)
        chosen.add(slot)
    if not chosen or not _rising(merged):
        return DeducedNumbers(frozenset(), {})
    return DeducedNumbers(
        frozenset(chosen), {k: str(v) for k, v in merged.items()}
    )


def furniture_slots(
    pages: Sequence[tuple[NormalizedPrimitivePage, str]],
    measurements: DocumentTextRecurrenceMeasurements,
    *,
    share: float = RECURRENCE_SHARE,
    band: float = EDGE_BAND,
    deduce: bool = True,
) -> FurnitureSlots:
    """I tre rami insieme, tenuti distinti.

    Il ramo 3 scatta **solo** se nessuna pagina porta un'etichetta dichiarata.
    `deduce=False` lo spegne, e serve a misurare che cosa aggiunge.
    """

    declared = [(page, label) for page, label in pages]
    from_sequence: frozenset[Slot] = frozenset()
    if deduce and not any(label.strip() for _, label in declared):
        from_sequence = deduced_number_slots(
            [page for page, _ in declared], share=share
        ).slots

    return FurnitureSlots(
        from_label=label_slots(pages, share=share),
        from_recurrence=recurrent_edge_slots(measurements, share=share, band=band),
        from_sequence=from_sequence,
    )


def furniture_node_ids(
    page: NormalizedPrimitivePage,
    node_primitive_ids: Sequence[tuple[str, Sequence[str]]],
    slots: frozenset[Slot],
) -> frozenset[str]:
    """I nodi da tenere fuori dal corpo: quelli **interamente** in slot d'arredo.

    Interamente e non parzialmente, e la scelta e' conservativa per la stessa
    ragione per cui il criterio ha barra zero: un nodo misto e' un nodo in cui
    dell'arredo si e' fuso con del contenuto, e toglierlo perderebbe il secondo.
    Un nodo misto resta nel corpo, e il difetto si vede.
    """

    by_id = {primitive.primitive_id: primitive for primitive in page.text_primitives}
    excluded: set[str] = set()
    for node_id, primitive_ids in node_primitive_ids:
        carrying = [
            by_id[pid]
            for pid in primitive_ids
            if pid in by_id and normalize_text(by_id[pid].text)
        ]
        if carrying and all(slot_of(p, page) in slots for p in carrying):
            excluded.add(node_id)
    return frozenset(excluded)
