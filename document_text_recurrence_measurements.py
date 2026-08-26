"""Pure recurrence counts of text at the same place, across a document's pages.

**Misura, non classificazione.** Dice che un certo punto della pagina e' occupato
su N pagine e porta M testi distinti; non dice che sia un'intestazione, non
toglie niente, e nessuna primitiva viene toccata -- `AGENTS.MD` §Primitive vuole
le primitive immutabili e senza ruoli semantici, e questo modulo le legge e
basta. Chi decide di escludere e' il consumer, tardi, dove il progetto ha gia'
ratificato che si decide.

**Perche' document-level.** Le otto ipotesi cadute dopo Milestone 35 hanno tutte
la stessa firma -- «separano dentro un manuale, non fra manuali» -- e quella
firma e' l'argomento: un'intestazione corrente non ha nessuna proprieta' locale
che la distingua da un titolo, ha la proprieta' di esserci su duecento pagine
nello stesso punto. `AGENTS.MD` rinvia un «consumer document-level di ricorrenza»
in quattro punti distinti (righe 468, 548, 762, 1037).

**Lo slot e non il testo.** L'unita' e' la posizione, e i testi che vi compaiono
sono un attributo. Serve perche' l'arredo ha tre forme e una sola di queste ha
testo costante: la filigrana e' sempre uguale, l'intestazione di capitolo cambia
poche volte, **il numero di pagina cambia a ogni pagina**. Misurato su DIE 60
pagine: lo slot della filigrana porta 1 testo, quello dei numeri ne porta 30.
Con la chiave sul testo il numero di pagina sarebbe invisibile.

**La posizione fa il lavoro, non la ripetizione.** ``Movimento:`` si ripete su
ogni pagina di bestiario ed e' contenuto; si ripete pero' a `y` qualsiasi.
Misurato su DIE: ``¥`` compare su 20 pagine in **126 posizioni**, ``RISCHIO`` su
10 pagine in 34. L'arredo sta fermo.

**Precedente nel repo, e va citato perche' e' autorevole**: la pipeline legacy
risolve gia' questo con `extractor.filter_repeated_blocks` -- firma
`(zona, testo normalizzato)`, soglie asimmetriche 25% ai bordi e 60% nel corpo,
«perche' nomi di abilita' o titoli di tabella possono legittimamente ripetersi».
Quel modulo **decide**; questo **misura**, e lascia la decisione a valle. Le sue
soglie non sono riprodotte qui di proposito: sono una politica, e una politica in
una misura e' la classificazione che questo modulo rifiuta di fare.

La griglia di quantizzazione e' una **costante di protocollo di misura**: dice
quanto finemente si guarda, non che cosa si accetta. La posizione e' relativa
alla pagina perche' i manuali non hanno tutti lo stesso formato.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from primitive_model import NormalizedPrimitivePage

POSITION_GRID = 100

_WHITESPACE = re.compile(r"\s+")


def _validate_int(value: int, field_name: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def normalize_text(text: str) -> str:
    """Il testo come lo si confronta: bordi tolti, spazi interni collassati.

    Nient'altro. Niente minuscole, niente punteggiatura rimossa: ogni pulizia in
    piu' e' un giudizio su che cosa conti come "lo stesso testo", e un giudizio
    si puo' ricalibrare dopo aver visto l'esito.
    """

    return _WHITESPACE.sub(" ", text).strip()


@dataclass(frozen=True, slots=True)
class TextSlotRecurrence:
    """One quantized position, and what occupies it across the document."""

    x: int
    y: int
    page_count: int
    page_indices: tuple[int, ...]
    texts: tuple[str, ...]

    def __post_init__(self) -> None:
        # x e y sono POSIZIONI, non conteggi, e possono uscire dalla pagina:
        # un testo puo' stare oltre il bordo -- il vivo di stampa, gia' a
        # verbale in Milestone 38 con un'occorrenza a x 699-1284 su una pagina
        # larga 581. Una prima versione li validava non-negativi e falliva su
        # Apo alla prima esecuzione fuori dai manuali di progettazione.
        if isinstance(self.x, bool) or not isinstance(self.x, int):
            raise ValueError("x must be an int")
        if isinstance(self.y, bool) or not isinstance(self.y, int):
            raise ValueError("y must be an int")
        _validate_int(self.page_count, "page_count", positive=True)
        if len(self.page_indices) != self.page_count:
            raise ValueError("page_indices must have page_count entries")
        if len(set(self.page_indices)) != len(self.page_indices):
            raise ValueError("page_indices must not repeat")
        if tuple(sorted(self.page_indices)) != self.page_indices:
            raise ValueError("page_indices must be sorted")
        if not self.texts:
            raise ValueError("texts must not be empty")
        if tuple(sorted(set(self.texts))) != self.texts:
            raise ValueError("texts must be sorted and unique")


@dataclass(frozen=True, slots=True)
class DocumentTextRecurrenceMeasurements:
    """Every occupied slot of a document, with no threshold applied.

    Nessuna soglia: chi consuma sceglie la sua, e cambiarla non richiede di
    rifare la misura. Riportare tutto costa poco -- gli slot occupati su una
    pagina sola sono la maggioranza e sono anche quelli che nessuna soglia
    guardera' mai, ma escluderli qui sarebbe gia' una decisione.
    """

    page_count: int
    slots: tuple[TextSlotRecurrence, ...]

    def __post_init__(self) -> None:
        _validate_int(self.page_count, "page_count", positive=True)
        seen: set[tuple[int, int]] = set()
        for slot in self.slots:
            if not isinstance(slot, TextSlotRecurrence):
                raise ValueError("slots must contain TextSlotRecurrence values")
            if (slot.x, slot.y) in seen:
                raise ValueError("slots must not repeat a position")
            seen.add((slot.x, slot.y))
            if slot.page_count > self.page_count:
                raise ValueError("a slot cannot occupy more pages than the document has")

    def occupied_on_at_least(self, share: float) -> tuple[TextSlotRecurrence, ...]:
        """Gli slot occupati su almeno una frazione delle pagine.

        Una comodita' per chi consuma, **non una soglia del modulo**: la frazione
        la passa il chiamante e la misura non ne conosce nessuna.
        """

        if not 0.0 < share <= 1.0:
            raise ValueError("share must be in (0, 1]")
        minimum = self.page_count * share
        return tuple(slot for slot in self.slots if slot.page_count >= minimum)


def measure_document_text_recurrence(
    pages: Sequence[NormalizedPrimitivePage],
) -> DocumentTextRecurrenceMeasurements:
    """Count which quantized slot carries which text, on how many pages.

    L'indice e la geometria vengono **dalla pagina**, non dal chiamante: un
    documento a formati misti si misura giusto senza che nessuno dichiari nulla,
    e non c'e' un secondo posto dove l'indice possa sbagliarsi.
    """

    if not pages:
        raise ValueError("pages must not be empty")

    page_indices_by_slot: dict[tuple[int, int], set[int]] = defaultdict(set)
    texts_by_slot: dict[tuple[int, int], set[str]] = defaultdict(set)
    seen_indices: set[int] = set()

    for primitive_page in pages:
        if not isinstance(primitive_page, NormalizedPrimitivePage):
            raise ValueError("pages must carry NormalizedPrimitivePage values")
        page_index = primitive_page.page_index
        if page_index in seen_indices:
            raise ValueError("a page index must not repeat")
        seen_indices.add(page_index)

        width = primitive_page.page_geometry.width
        height = primitive_page.page_geometry.height

        for primitive in primitive_page.text_primitives:
            text = normalize_text(primitive.text)
            if not text:
                continue
            slot = (
                round(primitive.bbox[0] / width * POSITION_GRID),
                round(primitive.bbox[1] / height * POSITION_GRID),
            )
            page_indices_by_slot[slot].add(page_index)
            texts_by_slot[slot].add(text)

    slots = tuple(
        TextSlotRecurrence(
            x=x,
            y=y,
            page_count=len(page_indices_by_slot[(x, y)]),
            page_indices=tuple(sorted(page_indices_by_slot[(x, y)])),
            texts=tuple(sorted(texts_by_slot[(x, y)])),
        )
        for x, y in sorted(page_indices_by_slot)
    )
    return DocumentTextRecurrenceMeasurements(page_count=len(pages), slots=slots)
