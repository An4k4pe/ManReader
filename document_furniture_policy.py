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

**Ramo 4 -- il testo che si ripete, e il testo verticale**,
`Criterio_ArredoPerTesto_v1.md`. Generalizza il ramo 1 da «il numero di pagina» a
«qualunque testo che si ripete»: uno slot ricorrente e' arredo **ovunque stia**
se almeno un testo a quello slot compare su due o piu' pagine. Niente fascia.

E' cio' che separa una testatina da un titolo che capita in cima: la testatina
ripete lo **stesso** testo, il titolo no. Misurato sulla fascia alta, dove il ramo
2 non arriva: FWK `Capitolo 5` 3 testi distinti su 11 pagine, FW `Il Mondo` 2 su
20, contro BiD 10 testi distinti su 10 pagine e DrM 9 su 9, che sono titoli veri
e restano.

La seconda clausola e' la **direzione**: una primitiva non orizzontale e' arredo.
Misurato, il testo verticale esiste su 6 manuali su 16 e ogni occorrenza e' un
nome di capitolo o il titolo del manuale -- `Draw Steel`, `Tactician`,
`Arcanista`, `ATTIVITA' DI DOWNTIME`. Sta in una clausola sua perche' una
testatina verticale cambia slot fra recto e verso e col capitolo, quindi la
ricorrenza dello slot non la coglie sempre; la direzione si'.
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


def mirrored(slot: Slot) -> Slot:
    """La chiave che accomuna uno slot e il suo specchio fra recto e verso.

    **Un arredo non centrato si specchia**, e contarne le due posizioni separate
    ne dimezza la ricorrenza. Indicazione dell'utente, e la misura la conferma:
    accoppiando i due lati i numeri di pagina passano da ~25% a **45-50%** delle
    pagine, cioe' da sotto a sopra la soglia del quarto. Su Kul e Lan lo slot del
    folio portava l'etichetta su **4 pagine su 20** e restava sotto; accoppiato
    arriva a otto.

    La `y` non si tocca: e' il lato che si specchia, non l'altezza.

    **Si specchia il CENTRO, non il bordo sinistro**, e la differenza non e'
    teorica: su Kul il numero sta a `x=25` sul verso e `x=72` sul recto, e
    `100-72` fa **28**, non 25. Lo slot porta il bordo sinistro, e lo specchio del
    bordo sinistro di un elemento allineato a destra e' il suo bordo **destro**.
    Il centro invece si riflette esatto. Chi ha solo lo slot -- il ramo 2, che
    legge una misura gia' fatta -- usa il bordo e accetta l'imprecisione; chi ha
    la primitiva usa `mirrored_centre`.
    """

    x, y = slot
    return (min(x, POSITION_GRID - x), y)


def mirrored_centre(primitive: TextPrimitive, page: NormalizedPrimitivePage) -> Slot:
    """La chiave specchiata calcolata sul **centro** della primitiva."""

    width = page.page_geometry.width
    height = page.page_geometry.height
    centre = (primitive.bbox[0] + primitive.bbox[2]) / 2.0 / width * POSITION_GRID
    return (
        round(min(centre, POSITION_GRID - centre)),
        round(primitive.bbox[1] / height * POSITION_GRID),
    )


def mirror_pair(slot: Slot) -> tuple[Slot, Slot]:
    """I due slot che condividono la chiave specchiata."""

    x, y = slot
    return ((x, y), (POSITION_GRID - x, y))


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
    from_repeated_text: frozenset[Slot] = frozenset()
    from_vertical: frozenset[Slot] = frozenset()
    running_heads: frozenset[tuple[str, Slot]] = frozenset()

    @property
    def all_slots(self) -> frozenset[Slot]:
        # `from_repeated_text` **non entra**: la clausola e' stata RITIRATA dopo
        # il giudizio, che l'ha trovata a togliere contenuto su 7 voci su 12.
        # Resta calcolata perche' l'esito la cita e perche' la misura serve a chi
        # riaprira' il fascicolo, ma non tocca cio' che esce dal corpo.
        # `Esito_ArredoPerTesto_v1.md`.
        #
        # `from_vertical` non entra piu' per un'altra ragione: la verticalita' e'
        # una proprieta' della PRIMITIVA e non dello slot, e marcare lo slot
        # toglieva la prosa orizzontale che ci passa su altre pagine. Ora si
        # escludono le primitive, con `vertical_primitive_ids`.
        # `running_heads` **non entra**: e' una coppia (testo, slot) e si applica
        # alle primitive, non allo slot. Toglierne lo slot porterebbe via tutto
        # cio' che ci passa.
        return self.from_label | self.from_recurrence | self.from_sequence


def label_slots(
    pages: Sequence[tuple[NormalizedPrimitivePage, str]],
    *,
    share: float = RECURRENCE_SHARE,
) -> frozenset[Slot]:
    """Ramo 1. `pages` accoppia una pagina alla sua etichetta dichiarata."""

    # Si conta per **chiave specchiata**, cosi' un numero che alterna i lati
    # somma le sue due posizioni invece di dimezzarsi. Si restituiscono poi gli
    # slot **reali** visti, perche' e' su quelli che si decide cosa esce.
    hits: dict[Slot, int] = {}
    real: dict[Slot, set[Slot]] = {}
    with_label = 0
    for page, label in pages:
        label = label.strip()
        if not label:
            continue
        with_label += 1
        seen: set[tuple[Slot, Slot]] = set()
        for primitive in page.text_primitives:
            if _carries_label(primitive.text, label):
                seen.add((mirrored_centre(primitive, page), slot_of(primitive, page)))
        for key in {k for k, _actual in seen}:
            hits[key] = hits.get(key, 0) + 1
        for key, actual in seen:
            real.setdefault(key, set()).add(actual)
    if not with_label:
        return frozenset()
    return frozenset(
        actual
        for key, count in hits.items()
        if count >= with_label * share
        for actual in real.get(key, ())
    )


def recurrent_edge_slots(
    measurements: DocumentTextRecurrenceMeasurements,
    *,
    share: float = RECURRENCE_SHARE,
    band: float = EDGE_BAND,
) -> frozenset[Slot]:
    """Ramo 2, sulla misura gia' committata."""

    lower = POSITION_GRID * (1.0 - band)
    # Anche qui si somma la coppia recto/verso: una filigrana o un piede non
    # centrati si specchiano, e contarli separati li tiene sotto soglia.
    by_key: dict[Slot, int] = {}
    real: dict[Slot, set[Slot]] = {}
    for slot in measurements.slots:
        if slot.y < lower:
            continue
        key = mirrored((slot.x, slot.y))
        by_key[key] = by_key.get(key, 0) + slot.page_count
        real.setdefault(key, set()).add((slot.x, slot.y))
    minimum = measurements.page_count * share
    return frozenset(
        actual
        for key, count in by_key.items()
        if count >= minimum
        for actual in real.get(key, ())
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
    """I quattro rami insieme, tenuti distinti.

    Il ramo 3 scatta **solo** se nessuna pagina porta un'etichetta dichiarata.
    `deduce=False` lo spegne, e serve a misurare che cosa aggiunge.
    """

    declared = [(page, label) for page, label in pages]
    from_sequence: frozenset[Slot] = frozenset()
    if deduce and not any(label.strip() for _, label in declared):
        from_sequence = deduced_number_slots(
            [page for page, _ in declared], share=share
        ).slots

    captured = [page for page, _label in declared]
    return FurnitureSlots(
        from_label=label_slots(pages, share=share),
        from_recurrence=recurrent_edge_slots(measurements, share=share, band=band),
        from_sequence=from_sequence,
        from_repeated_text=repeated_text_slots(captured, share=share),
        from_vertical=vertical_slots(captured),
        running_heads=running_heads(captured, share=share),
    )


def furniture_node_ids(
    page: NormalizedPrimitivePage,
    node_primitive_ids: Sequence[tuple[str, Sequence[str]]],
    slots: frozenset[Slot],
    excluded_primitives: frozenset[str] = frozenset(),
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
        # Una primitiva puo' essere arredo **per se stessa** e non per dove sta:
        # il testo verticale e' il caso, e marcarne lo slot toglieva la prosa
        # orizzontale che ci passa su altre pagine.
        if carrying and all(
            slot_of(p, page) in slots or p.primitive_id in excluded_primitives
            for p in carrying
        ):
            excluded.add(node_id)
    return frozenset(excluded)


def repeated_text_slots(
    pages: Sequence[NormalizedPrimitivePage],
    *,
    share: float = RECURRENCE_SHARE,
) -> frozenset[Slot]:
    """**RITIRATA.** Uno slot ricorrente che ripete lo stesso testo, ovunque stia.

    Il giudizio cieco l'ha trovata a togliere **contenuto** su 7 voci su 12: le
    etichette dei campi di scheda di Draw Steel (`Stamina` sopra il suo valore),
    le parole chiave delle abilita' di DrW, righe di corpo di DB. Ricorrono
    perche' ricorre la **struttura**, non perche' siano arredo, e la condizione
    «almeno un testo si ripete a quello slot» non le distingue.

    Resta calcolata e **non usata**: `all_slots` non la include. La misura serve a
    chi riaprira' il fascicolo. `Esito_ArredoPerTesto_v1.md`.

    `Criterio_ArredoPerTesto_v1.md` §1.A. Generalizza il ramo 1 da «il numero di
    pagina» a «qualunque testo che si ripete», e come quello **non ha vincolo di
    posizione**: riconosce che cosa togliere, non dove.

    La condizione che separa e' che **almeno un testo a quello slot compaia su due
    o piu' pagine**. Misurato sulla fascia alta, dove il ramo 2 non arriva: FWK
    `Capitolo 5` ha 3 testi distinti su 11 pagine e FW `Il Mondo` 2 su 20 -- si
    ripetono; BiD ha 10 testi distinti su 10 pagine e DrM 9 su 9 -- sono titoli
    veri e restano.
    """

    per_slot: dict[Slot, list[str]] = {}
    for page in pages:
        seen: dict[Slot, str] = {}
        for primitive in page.text_primitives:
            text = normalize_text(primitive.text)
            if text:
                seen.setdefault(slot_of(primitive, page), text)
        for slot, text in seen.items():
            per_slot.setdefault(slot, []).append(text)

    minimum = len(pages) * share
    found: set[Slot] = set()
    for slot, texts in per_slot.items():
        if len(texts) < minimum:
            continue
        counts: dict[str, int] = {}
        for text in texts:
            counts[text] = counts.get(text, 0) + 1
        if any(count >= 2 for count in counts.values()):
            found.add(slot)
    return frozenset(found)


def vertical_primitive_ids(page: NormalizedPrimitivePage) -> frozenset[str]:
    """Ramo 4B. Gli **id delle primitive** con testo non orizzontale, di UNA pagina.

    **Id di primitiva e non slot**, ed e' la correzione che il giudizio ha
    imposto: `Criterio_ArredoPerTesto_v1.md` §1.B dice «una primitiva la cui
    direzione non e' orizzontale», e l'avevo implementata marcando il suo SLOT.
    Su Fab lo slot (14,57) porta `CONGEDO` in verticale su una pagina e prosa
    orizzontale su quattro altre -- `perfetti per viaggiare, e combatte con` --
    e quella prosa usciva dal corpo.

    **E di una pagina sola, non del documento.** Gli id di primitiva **non sono
    unici fra pagine**: `primitive:text:text:b0000:l0000:s0000` esiste su ogni
    pagina, e su BiD 70 id su 203 sono ripetuti. Raccoglierli su tutto il
    documento marcava primitive omonime di altre pagine -- il titolo `attivita' di
    downtime` a corpo 30 finiva in review perche' un'altra pagina aveva una
    primitiva verticale con lo stesso id.

    Non serve la scansione del documento: la verticalita' e' un fatto della
    primitiva, e la primitiva sta su una pagina.

    Misurato su 20 pagine per manuale: il testo verticale esiste su 6 manuali su
    16 e **ogni** occorrenza e' un nome di capitolo o il titolo del manuale --
    `Draw Steel`, `Tactician`, `Arcanista`, `ATTIVITA' DI DOWNTIME`.
    """

    found: set[str] = set()
    for primitive in page.text_primitives:
        direction = primitive.direction
        if direction is None or not normalize_text(primitive.text):
            continue
        if abs(direction[0]) <= abs(direction[1]):
            found.add(primitive.primitive_id)
    return frozenset(found)


def vertical_slots(pages: Sequence[NormalizedPrimitivePage]) -> frozenset[Slot]:
    """**Ritirata.** Gli slot occupati da testo non orizzontale.

    Tenuta perche' l'esito la cita, e **non usata**: marcare lo slot toglieva la
    prosa orizzontale che ci passa su altre pagine. La forma giusta e'
    `vertical_primitive_ids`.

    Misurato su 20 pagine per manuale: il testo verticale esiste su 6 manuali su
    16, fra 9 e 36 primitive ciascuno, e **ogni** occorrenza e' un nome di
    capitolo o il titolo del manuale. Su BiD `ATTIVITA' DI DOWNTIME` sta a
    direzione ``(0,-1)`` sul bordo destro e `DOWNTIME` a ``(0,1)`` sul sinistro,
    specchiati fra recto e verso; il titolo vero e' l'orizzontale a corpo 30, che
    compare una volta sola a capo del capitolo.

    Clausola sua e non un caso della A perche' una testatina verticale cambia slot
    fra recto e verso e col capitolo: la ricorrenza dello slot non la coglie
    sempre, la direzione si'.
    """

    found: set[Slot] = set()
    for page in pages:
        for primitive in page.text_primitives:
            direction = primitive.direction
            if direction is None or not normalize_text(primitive.text):
                continue
            if abs(direction[0]) <= abs(direction[1]):
                found.add(slot_of(primitive, page))
    return frozenset(found)


def running_heads(
    pages: Sequence[NormalizedPrimitivePage],
    *,
    share: float = RECURRENCE_SHARE,
    majority: float = 0.5,
) -> frozenset[tuple[str, Slot]]:
    """Ramo 5. Le **testatine correnti**, come coppie (testo, slot).

    `Criterio_TestatinaCorrente_v1.md`. Indicazione dell'utente: «le testatine
    devono funzionare in qualsiasi posizione, alto basso laterale e verso e
    recto».

    **Parte dal testo, non dallo slot**, ed e' li' che la clausola A sbagliava.
    Quella chiedeva «a questo slot si ripete qualche testo?», e un campo di scheda
    ripete il suo: `Stamina` di Draw Steel usciva dal corpo. Questa chiede «questo
    testo sta sempre nello stesso posto?». `Stamina` compare su 16 pagine sparsa
    su **31 slot diversi**, `Psionic` di DrW su **71**, mentre una testatina sta a
    uno solo: una scheda si sposta col contenuto, una testatina no.

    **Torna coppie e non slot**, ed e' la correzione che il giudizio ha imposto.
    Restituire lo slot toglieva **tutto** cio' che ci passa: su Vil lo slot
    (13,11) porta `G I O C A R E` su quattro pagine e **tredici titoli di sezione
    diversi** sulle altre -- `DONI`, `PULSIONI`, `DOVERE` -- e uscivano tutti. E'
    la seconda volta che identifico per testo e tolgo per posizione: la prima e'
    stata la clausola del verticale.

    Lo slot e' **specchiato sul centro** per contare, ma le coppie portano gli
    slot **reali**, perche' e' su quelli che si confronta una primitiva.
    """

    per_text: dict[str, dict[Slot, int]] = {}
    pages_of_text: dict[str, set[int]] = {}
    pages_of_slot: dict[Slot, set[int]] = {}
    real: dict[tuple[str, Slot], set[Slot]] = {}

    for index, page in enumerate(pages):
        for primitive in page.text_primitives:
            text = normalize_text(primitive.text)
            if len(text) < 2:
                continue
            key = mirrored_centre(primitive, page)
            per_text.setdefault(text, {})[key] = per_text.setdefault(text, {}).get(key, 0) + 1
            pages_of_text.setdefault(text, set()).add(index)
            pages_of_slot.setdefault(key, set()).add(index)
            real.setdefault((text, key), set()).add(slot_of(primitive, page))

    minimum = len(pages) * share
    found: set[tuple[str, Slot]] = set()
    for text, slots in per_text.items():
        if len(pages_of_text[text]) < minimum:
            continue
        key, count = max(slots.items(), key=lambda item: item[1])
        # La **maggioranza** delle occorrenze a uno slot solo: e' il punto in cui
        # un testo smette di stare in giro e comincia a stare in un posto.
        if count <= sum(slots.values()) * majority:
            continue
        if len(pages_of_slot[key]) < minimum:
            continue
        for actual in real.get((text, key), ()):
            found.add((text, actual))
    return frozenset(found)


def furniture_primitive_ids(
    page: NormalizedPrimitivePage, slots: frozenset[Slot]
) -> frozenset[str]:
    """Le primitive che stanno in uno slot d'arredo. Non e' un ramo: e' una lettura."""

    return frozenset(
        primitive.primitive_id
        for primitive in page.text_primitives
        if normalize_text(primitive.text) and slot_of(primitive, page) in slots
    )


def running_head_primitive_ids(
    page: NormalizedPrimitivePage,
    heads: frozenset[tuple[str, Slot]],
    already_furniture: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Gli id delle primitive di **questa** pagina che sono una testatina.

    Si confrontano **testo e posizione insieme**: un titolo di sezione che passa
    per lo stesso punto non e' la testatina, e un'occorrenza dello stesso testo
    altrove nella prosa nemmeno.

    Per pagina, come per il verticale: gli id di primitiva **non sono unici fra
    pagine**.

    **E una testatina non sta in mezzo a un testo.** `Criterio_TestatinaCorrente_v2.md`,
    indicazione dell'utente: la ricorrenza nello stesso punto vale «sui bordi o
    comunque non in mezzo ad un testo». Su BiD `punti di riferimento` ricorre su
    sei pagine a coordinate **identiche al decimale** -- x 63,0-206,1, y
    358,0-377,7 -- e non e' arredo: introduce l'elenco dei luoghi del quartiere,
    e sta a meta' pagina con testo sopra e sotto.

    Il vincolo non e' una fascia di bordo tarata, che avrebbe escluso testatine
    vere: `G I O C A R E` di Vil sta a 11 dal bordo e `CAPITOLO` di Fab a 10. E'
    la formulazione letterale dell'utente -- **almeno un lato libero**, cioe'
    almeno una direzione in cui oltre la testatina non c'e' altro testo. Misurato
    sui sedici manuali: **32 testatine su 33 hanno un lato libero**, e
    `punti di riferimento` e' circondata da tutt'e quattro i lati.

    **`already_furniture` recupera il costo che la v2 aveva dichiarato.**
    Indicazione dell'utente: «DB si recupera se quando controlli per la testatina
    hai gia' rimosso sfondi ed estetica». Misurato su DB idx 58: sotto
    `CAPITOLO 5 - MAGIA` c'e' **una cosa sola**, il folio `57`, che e' arredo pure
    lui. Un lato e' libero quando oltre di esso non c'e' **contenuto**, e
    dell'altro arredo non e' contenuto: gli altri rami hanno gia' detto quali
    primitive sono loro, e questa clausola gira dopo.
    """

    return frozenset(
        primitive.primitive_id
        for primitive in page.text_primitives
        if (normalize_text(primitive.text), slot_of(primitive, page)) in heads
        and _has_a_free_side(primitive, page, already_furniture)
    )


def _has_a_free_side(
    primitive, page: NormalizedPrimitivePage, ignore: frozenset[str] = frozenset()
) -> bool:
    """Sopra **o** sotto questa primitiva non c'e' altro **contenuto**.

    **Sopra o sotto, non uno qualunque dei quattro lati**, ed e' una misura a
    imporlo. Con tutti e quattro, su BiD bastava che l'unica cosa a sinistra di
    `punti di riferimento` fosse il folio `280` -- tolto come arredo -- perche' il
    lato sinistro risultasse libero e la protezione cadesse. La direzione che
    conta e' quella della **lettura**: «in mezzo a un testo» vuol dire con del
    testo sopra e sotto.

    **E si guarda la colonna della primitiva**, non la pagina intera:
    `Criterio_TestatinaCorrente_v4.md`. Una linguetta di margine ha il corpo del
    testo **accanto**, non sopra, e guardando tutta la pagina risultava in mezzo
    a un testo che sta in un'altra colonna.

    Misurato sui sedici manuali: tiene **33 testatine su 33**, e
    `punti di riferimento` -- che nella sua colonna ha testo sopra e sotto --
    resta nel corpo.

    `ignore` sono le primitive che gli altri rami hanno gia' dichiarato arredo:
    non contano come testo che circonda, perche' non sono contenuto. Su DB sotto
    `CAPITOLO 5 - MAGIA` c'e' **solo** il folio `57`, e senza questo la testatina
    restava nel corpo -- rilievo dell'utente: «DB si recupera se quando controlli
    per la testatina hai gia' rimosso sfondi ed estetica».

    Le linguette **verticali** non passano di qui: le prende `vertical_primitive_ids`,
    che e' un fatto della primitiva e non della sua posizione.
    """

    x0, y0, x1, y1 = primitive.bbox
    # **Nella sua colonna**, non su tutta la pagina: una linguetta di margine ha
    # il corpo del testo accanto, non sopra. Su Fab `CAPITOLO` ha otto primitive
    # sopra di se' sulla pagina e **zero** nella sua striscia -- e l'utente
    # l'aveva segnalata da togliere.
    column = [
        other
        for other in page.text_primitives
        if other is not primitive
        and other.text.strip()
        and other.primitive_id not in ignore
        and other.bbox[0] < x1
        and other.bbox[2] > x0
    ]
    return not (
        any(other.bbox[3] <= y0 for other in column)
        and any(other.bbox[1] >= y1 for other in column)
    )
