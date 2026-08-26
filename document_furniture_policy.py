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

    @property
    def all_slots(self) -> frozenset[Slot]:
        return self.from_label | self.from_recurrence


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


def furniture_slots(
    pages: Sequence[tuple[NormalizedPrimitivePage, str]],
    measurements: DocumentTextRecurrenceMeasurements,
    *,
    share: float = RECURRENCE_SHARE,
    band: float = EDGE_BAND,
) -> FurnitureSlots:
    """I due rami insieme, tenuti distinti."""

    return FurnitureSlots(
        from_label=label_slots(pages, share=share),
        from_recurrence=recurrent_edge_slots(measurements, share=share, band=band),
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
