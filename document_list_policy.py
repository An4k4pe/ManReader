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

import unicodedata

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
