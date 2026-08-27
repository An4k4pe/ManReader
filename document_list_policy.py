"""Quali caratteri sono marcatori d'elenco in un documento.

`Criterio_Elenchi_v1.md` §1. **Politica, non misura**:
`document_line_start_measurements` osserva, questo modulo decide, e stanno
separati per la stessa ragione per cui lo sono la ricorrenza d'arredo e la sua
politica.

**Non c'e' un elenco di caratteri, e non e' una raffinatezza.** Misurato su 16
manuali e 17714 righe: un `•*-` cablato prenderebbe **3 manuali su 16**. Il
marcatore e' spesso il codepoint di un font di simboli -- `✦` su DB, `\\x8b` su
BoB, `\\x90` su BiD, `!@#` su DrM, `¥£®` su DrW, `↳` su Apo e Vil.

Cio' che separa un marcatore dalla punteggiatura non e' **quale** carattere sia
ma **dove vive**: il marcatore vive a inizio riga, la punteggiatura in mezzo alle
frasi. Da qui le due condizioni, e nessuna delle due e' un numero tarato:

- la **maggioranza** delle occorrenze a inizio riga e' la soglia naturale fra i
  due modi di vivere, e scarta `(` e `"`, che aprono righe ma vivono nelle frasi;
- **due righe nello stesso blocco** e' il minimo che fa di un elenco un elenco, e
  impedisce che un carattere raro qualifichi con una riga sola su una occorrenza
  sola, cioe' al 100%.

**Maggioranza e non totalita'**, ed e' misurato: su DrM `!` apre 45 righe come
marcatore e compare in altre 29 come punto esclamativo vero (`Take Point!`,
`Advance!`). Sta al 60% e deve passare, perche' la regola tocca il carattere
**solo a inizio riga dentro un elenco** e i punti esclamativi in mezzo alle frasi
non li vede. Una soglia al 100% avrebbe perso il manuale con i marcatori piu'
strani.

**Che cosa questo modulo non fa.** Non toglie il marcatore dal testo: restituisce
caratteri, e chi rende decide. E' la stessa forma di `document_furniture_policy`,
che restituisce posizioni e non tocca le primitive.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from document_line_start_measurements import LineStartMeasurements

# La maggioranza. Non e' una taratura: e' il punto in cui un carattere smette di
# vivere nelle frasi e comincia a vivere a inizio riga. Sta qui come costante
# nominata perche' si veda, non perche' si giri.
MAJORITY = 0.5

# Le categorie Unicode della punteggiatura **appaiata**: apre o chiude una
# coppia, quindi per definizione vive dentro una frase. Non e' una lista di
# caratteri scelta a mano -- e' una proprieta' che Unicode dichiara -- ed e' cio'
# che scarta `“` di SV (84 righe) e le parentesi, che aprono righe e non sono
# elenchi.
PAIRED_CATEGORIES = frozenset({"Ps", "Pe", "Pi", "Pf"})

# Un elenco e' un modo di comporre che il manuale usa, non un caso capitato una
# volta. Due pagine e' il minimo per dire «ricorre», ed e' lo stesso ragionamento
# che rende document-level la misura dell'arredo.
MINIMUM_PAGES = 2


def list_markers(
    measurements: LineStartMeasurements,
    *,
    majority: float = MAJORITY,
    minimum_pages: int = MINIMUM_PAGES,
) -> frozenset[str]:
    """I caratteri che in **questo** documento aprono le voci di un elenco.

    Quattro condizioni, e nessuna e' un numero tarato:

    1. non alfanumerico e non spazio;
    2. **non punteggiatura appaiata** -- `PAIRED_CATEGORIES`;
    3. la **maggioranza** delle sue occorrenze apre una riga;
    4. **del testo lo segue** su ogni riga che apre, o quasi: `opens_with_text`
       deve essere la maggioranza di `opens_lines`;
    5. apre righe su almeno `MINIMUM_PAGES` pagine.
    """

    found = set()
    for character, opened in measurements.opens_lines.items():
        if not opened or unicodedata.category(character) in PAIRED_CATEGORIES:
            continue
        if measurements.line_initial_share(character) <= majority:
            continue
        if measurements.opens_with_text.get(character, 0) <= opened * majority:
            continue
        if measurements.pages_opened.get(character, 0) < minimum_pages:
            continue
        found.add(character)
    return frozenset(found)


def opens_a_list_item(text: str, markers: frozenset[str]) -> bool:
    """La riga si apre con un marcatore di questo documento."""

    stripped = text.lstrip()
    return bool(stripped) and stripped[0] in markers


def strip_marker(text: str, markers: frozenset[str]) -> str:
    """Il testo della voce senza il marcatore e senza lo spazio che lo segue.

    Serve a **rendere**, non a costruire: il nodo conserva il testo intero, e il
    marcatore esce solo dalla resa. E' la stessa forma dell'arredo -- niente
    viene distrutto, cambia cio' che si vede -- ed e' la ragione per cui questa
    funzione sta qui e non nel builder.
    """

    stripped = text.lstrip()
    if not stripped or stripped[0] not in markers:
        return text
    # **Tutti** i marcatori in testa, non solo il primo. Una versione precedente
    # ne toglieva uno solo, ragionando che il secondo fosse testo; misurato su FW
    # p.168 e' falso: dove l'ordine di lettura interlaccia due colonne d'elenco
    # arrivano due glifi di fila, e ne restava uno in mezzo alla voce.
    while stripped and stripped[0] in markers:
        stripped = stripped[1:].lstrip()
    return stripped


_BLOCK_NUMBER = re.compile(r"^b(\d+)$")


def value_scale_signatures(
    counted: dict[tuple[str, ...], int],
) -> frozenset[tuple[str, ...]]:
    """Le firme di blocco che sono una **scala di valori**, non un elenco.

    `Criterio_ScalaDiValori_v1.md` §1. Tre condizioni, nessuna tarata:

    - **due o piu' caratteri distinti** -- un elenco usa un carattere solo;
    - **ciascuno una volta sola** -- una scala non ripete i suoi gradini, ed e'
      cio' che salva l'annidamento di FWK, dove i caratteri sono due (`•` e `*`)
      ma `*` si ripete;
    - **la firma ricorre in almeno un altro blocco** -- una scala e' una
      convenzione del documento, non un caso di un blocco.

    Misurato: su DrM `!@#` compare in 43 blocchi, tre glifi distinti senza
    ripetizioni, e sono i tre esiti di un tiro (`≤11`, `12-16`, `17+`).
    """

    return frozenset(
        signature
        for signature, count in counted.items()
        if len(set(signature)) >= 2 and len(signature) == len(set(signature)) and count >= 2
    )


def _block_number(block: str) -> int | None:
    match = _BLOCK_NUMBER.match(block)
    return int(match.group(1)) if match else None


def list_item_flags(
    lines: Sequence[tuple[str, str]],
    markers: frozenset[str],
    scales: frozenset[tuple[str, ...]] = frozenset(),
) -> list[bool]:
    """Quali righe sono voci d'elenco. `lines` e' (blocco, testo) in ordine sorgente.

    **L'unita' e' la corsa**, non il blocco: una sequenza massimale di righe con
    lo **stesso** marcatore che stanno nello stesso blocco o in blocchi
    **consecutivi**. Una corsa di due o piu' e' un elenco; una corsa di una riga
    sola non lo e'.

    Perche' la corsa e non il blocco, misurato su DB e scritto nel criterio: DB
    ha 312 blocchi che portano `✦`, **uno per blocco**, quindi «due righe nello
    stesso blocco» avrebbe dichiarato che DB non ha nessun elenco -- ed e'
    esattamente la condizione che ha fatto cadere `Criterio_Elenchi_v1.md`.

    A idx 60 un elenco vero e' cinque `✦` in blocchi consecutivi (b0015..b0019);
    a idx 13 le righe di costo stanno in b0001 e b0003, con b0002 in mezzo che
    **non porta marcatore**, e la catena si spezza. Non si contano le righe fra
    due marcatori: sarebbe una soglia, e la catena risponde senza sceglierla.

    I blocchi la cui firma e' una **scala** escono prima di tutto: li' il glifo
    porta un valore, e nessuna corsa lo puo' promuovere a voce.
    """

    # **Un carattere che e' gradino di una scala non e' un marcatore in questo
    # documento**, e non solo nei blocchi dove la scala compare per intero.
    # Misurato: su DrM una pagina di minion ha sei blocchi consecutivi con un
    # solo `!` ciascuno -- il tier `≤11` di sei creature diverse. Per la regola
    # delle corse sarebbero una corsa di sei, cioe' un elenco di danni scollegati
    # dove `2 damage` compare due volte senza che si capisca di chi sia.
    # Escludere il carattere a livello di documento e' cio' che lo impedisce.
    graduated = {character for signature in scales for character in signature}
    markers = markers - graduated

    by_block: dict[str, list[str]] = {}
    for block, text in lines:
        stripped = text.strip()
        if stripped and stripped[0] in markers:
            by_block.setdefault(block, []).append(stripped[0])
    scale_blocks = {
        block for block, opening in by_block.items() if tuple(opening) in scales
    }

    candidates: list[tuple[int, int, str]] = []
    for position, (block, text) in enumerate(lines):
        stripped = text.strip()
        if not stripped or stripped[0] not in markers or block in scale_blocks:
            continue
        number = _block_number(block)
        if number is None:
            continue
        candidates.append((number, position, stripped[0]))
    candidates.sort()

    flags = [False] * len(lines)
    run: list[tuple[int, int, str]] = []

    def close() -> None:
        if len(run) >= 2:
            for _number, position, _marker in run:
                flags[position] = True
        run.clear()

    for entry in candidates:
        if run:
            previous = run[-1]
            same_marker = entry[2] == previous[2]
            adjacent = entry[0] in (previous[0], previous[0] + 1)
            if not (same_marker and adjacent):
                close()
        run.append(entry)
    close()
    return flags
