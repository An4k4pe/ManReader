"""Quali righe sono titoli, e di che livello. `Criterio_Titoli_v2.md` §1.

**Politica, non misura**: `document_heading_measurements` osserva, questo modulo
decide, e stanno separati come per l'arredo e gli elenchi.

**Non «sopra il corpo» ma «sopra tutta la prosa».** E' la correzione della v1 del
criterio, che assumeva una sola dimensione di corpo per documento. Su Kul 8,0 e
10,0 sono **entrambe** prosa: guardando solo la piu' frequente, le 67 righe a 10,0
risultavano titoli. Con la prosa presa per intero i candidati passano da 88 a 21,
e sugli altri tredici manuali non cambia niente.

**L'errore che non va rifatto** e' scritto nel repo:
`markdown_builder._is_heading_text` «promuove a titolo qualunque testo corto in
maiuscolo **prima ancora di guardare lo stile**», e su DB p.99 ha promosso una
testatina corrente. Qui le maiuscole non compaiono nella regola.
"""

from __future__ import annotations

from collections.abc import Sequence

from document_heading_measurements import FontSizeMeasurements, SizedLine

# Quanto una dimensione deve superare la prosa per contare come diversa. Non e'
# una soglia della regola: e' la tolleranza con cui si leggono due float che il
# backend riporta con l'arrotondamento del PDF.
SIZE_EPSILON = 0.4

# Un titolo e' un blocco suo, al piu' con un a capo.
MAX_LINES_IN_A_HEADING_BLOCK = 2

# Quanti livelli Markdown ha.
MAX_LEVEL = 6

# Una dimensione con pochissime righe non dice niente sulla lunghezza mediana
# delle sue righe. Non e' una soglia della regola -- non decide se qualcosa e'
# titolo -- ma la numerosita' minima perche' una mediana significhi qualcosa.
MIN_LINES_FOR_A_MEDIAN = 4


def prose_sizes(measurements: FontSizeMeasurements) -> frozenset[float]:
    """Le dimensioni le cui righe sono **lunghe**, cioe' la prosa del documento.

    Le mediane si ordinano e si taglia al **salto piu' grande** fra due
    consecutive: e' una proprieta' della distribuzione, non una soglia scelta.
    Misurato su DB, le mediane sono 10, 14, 21, 45, 55 e il salto sta fra 21 e 45,
    che separa esattamente `11.5` e `34.0` da `9.0` e `10.0`.

    Con meno di due dimensioni non c'e' salto da trovare: tutto cio' che si e'
    visto e' prosa, e non si promuove niente. Preferire il silenzio all'invenzione
    e' la stessa scelta del ramo dedotto del numero di pagina.
    """

    usable = sorted(
        (
            (size, measurements.median_length[size])
            for size, count in measurements.line_count.items()
            if count >= MIN_LINES_FOR_A_MEDIAN
        ),
        key=lambda entry: entry[1],
    )
    if len(usable) < 2:
        return frozenset(size for size, _median in usable)

    gaps = [
        (usable[index + 1][1] - usable[index][1], index) for index in range(len(usable) - 1)
    ]
    _largest, cut = max(gaps)
    return frozenset(size for size, _median in usable[cut + 1 :])


def heading_levels(
    measurements: FontSizeMeasurements, prose: frozenset[float]
) -> dict[float, int]:
    """Il livello di ogni dimensione sopra la prosa: rango, non soglia.

    La piu' grande e' `1`, poi `2`, e cosi' via. Oltre `MAX_LEVEL` si collassa,
    perche' e' quanto Markdown ha.
    """

    if not prose:
        return {}
    limit = max(prose)
    above = sorted(
        (size for size in measurements.line_count if size > limit + SIZE_EPSILON),
        reverse=True,
    )
    return {size: min(rank, MAX_LEVEL) for rank, size in enumerate(above, start=1)}


def heading_lines(
    lines: Sequence[SizedLine],
    prose: frozenset[float],
    levels: dict[float, int],
    excluded: frozenset[str] = frozenset(),
) -> dict[int, int]:
    """Da posizione della riga al suo livello di titolo. `lines` e' una pagina.

    `excluded` sono i testi gia' tolti dal corpo come **arredo**: in molti manuali
    il numero di pagina e' piu' grande della prosa -- `152` su BiD, `[209]` su Lan
    -- e senza questo diventerebbe un titolo di primo livello.
    """

    if not prose or not levels:
        return {}

    by_block: dict[str, list[int]] = {}
    for position, line in enumerate(lines):
        by_block.setdefault(line.block, []).append(position)

    found: dict[int, int] = {}
    for _block, positions in by_block.items():
        if len(positions) > MAX_LINES_IN_A_HEADING_BLOCK:
            continue
        # Un blocco che contiene prosa non e' un blocco di titolo, qualunque cosa
        # ci sia dentro d'altro. Su Apo il blocco del titolo contiene anche la
        # testatina, che sta SOTTO la prosa: chiedere che tutte le righe stiano
        # sopra perdeva quel manuale, chiedere che nessuna sia prosa lo recupera.
        if any(lines[position].size in prose for position in positions):
            continue
        for position in positions:
            line = lines[position]
            if len(line.text) <= 1 or line.text in excluded:
                continue
            level = levels.get(line.size)
            if level is not None:
                found[position] = level
    return found
