"""Leggere per RIGHE una regione di tabella, non per colonne.

Milestone 44, Fase 3. Senza questa, la Fase 2 peggiora le tabelle invece di
migliorarle: un consumer che prendesse i confini di colonna ammessi da
Resolution e li usasse come colonne leggerebbe una tabella come «tutti i numeri,
poi tutte le descrizioni».

**Dove vale, e dove no.** Solo dentro una regione coperta da un
`table_candidate`. Fuori, l'ordine per colonne e' quello giusto e non va
toccato: due colonne di prosa si leggono una dopo l'altra, e leggerle per righe
le interlaccerebbe -- che e' esattamente il difetto da cui e' partita la
Milestone 43.

**Come si formano le righe, senza costanti.** Due righe tipografiche stanno
nella stessa riga di tabella se le loro estensioni verticali **si sovrappongono**.
E' una relazione fra due rettangoli, non una grandezza da tarare, ed e' la stessa
con cui la Milestone 43 ha misurato il testo affiancato.

La cella che va a capo non rompe niente: le sue righe successive non si
sovrappongono alla prima, quindi formano gruppi propri, che contengono solo la
colonna della descrizione e finiscono in ordine subito dopo. Su una tabella
`numero | descrizione a tre righe` l'uscita e' numero, descrizione 1,
descrizione 2, descrizione 3 -- che e' l'ordine di lettura.

**Il difetto che chiude, misurato.** Ordinando per `y` la riga del numero e la
prima riga della descrizione hanno `y` che differiscono di frazioni di punto, e
il numero finisce **dentro** la frase invece che davanti (misurato: `y` 167,0
contro 166,9). Assegnare prima la riga di tabella e poi la colonna toglie il
problema alla radice invece di arrotondare le coordinate.

Non e' wired: e' una funzione pura, e chi ordina la chiama per le regioni che
Resolution ha marcato come tabella.
"""

from __future__ import annotations

from collections.abc import Sequence

from primitive_model import TextPrimitive

_Line = Sequence[TextPrimitive]


def _extent(line: _Line) -> tuple[float, float, float, float]:
    """`(y0, y1, x0, x1)` della riga tipografica, dai suoi span."""
    return (
        min(p.bbox[1] for p in line),
        max(p.bbox[3] for p in line),
        min(p.bbox[0] for p in line),
        max(p.bbox[2] for p in line),
    )


def _column_index(x_center: float, column_boundaries: Sequence[tuple[float, float]]) -> int:
    """Quante colonne stanno a sinistra del centro della riga.

    Un confine e' un intervallo x: la riga sta a destra di quel confine se il suo
    centro cade oltre la fine dell'intervallo. Una riga che attraversa un confine
    -- una cella unita, un titolo a tutta larghezza -- prende la colonna in cui
    cade il suo centro, e non viene spezzata."""
    return sum(1 for _x0, x1 in column_boundaries if x_center >= x1)


def order_table_lines_by_rows(
    lines: Sequence[_Line],
    *,
    column_boundaries: Sequence[tuple[float, float]],
) -> tuple[tuple[TextPrimitive, ...], ...]:
    """Le righe di una regione di tabella, in ordine di lettura per righe.

    `lines` sono righe tipografiche gia' formate — la riga viene dalla sorgente e
    non si ricompone qui. `column_boundaries` sono gli intervalli x dei confini
    di colonna della regione, come quelli che Resolution ammette.

    Restituisce le stesse righe riordinate: non aggiunge, non toglie e non
    modifica niente.
    """

    non_vuote = [tuple(line) for line in lines if len(tuple(line)) > 0]
    if not non_vuote:
        return ()

    confini = sorted(column_boundaries)
    estensioni = [_extent(line) for line in non_vuote]

    # Righe di tabella: chiusura transitiva della sovrapposizione verticale.
    ordine_y = sorted(range(len(non_vuote)), key=lambda i: (estensioni[i][0], estensioni[i][2]))
    righe_tabella: list[list[int]] = []
    for indice in ordine_y:
        y0, y1, _x0, _x1 = estensioni[indice]
        for gruppo in righe_tabella:
            if any(y0 < estensioni[altro][1] and y1 > estensioni[altro][0] for altro in gruppo):
                gruppo.append(indice)
                break
        else:
            righe_tabella.append([indice])

    fuori: list[tuple[TextPrimitive, ...]] = []
    for gruppo in sorted(righe_tabella, key=lambda g: min(estensioni[i][0] for i in g)):
        gruppo.sort(
            key=lambda i: (
                _column_index((estensioni[i][2] + estensioni[i][3]) / 2.0, confini),
                estensioni[i][0],
                estensioni[i][2],
            )
        )
        fuori.extend(non_vuote[i] for i in gruppo)
    return tuple(fuori)
