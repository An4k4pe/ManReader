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

# Quanti livelli si usano. **Tre, non sei**, e non e' una limitazione tecnica:
# Markdown ne ha sei, ma distinguere sei ranghi di dimensione non aggiunge
# informazione utile a chi legge, e su un manuale con otto dimensioni che
# intestano il rango diventa un dettaglio senza significato.
#
# Indicazione dell'utente: il font piu' grande e' `#`, il successivo `##`, e il
# minore che non sia paragrafo `###`. Cio' che sta sotto il secondo rango
# collassa sul terzo, che e' esattamente «un titolo, e non uno dei due sopra».
MAX_LEVEL = 3

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
    measurements: FontSizeMeasurements,
    prose: frozenset[float],
    carried: frozenset[float] | None = None,
) -> dict[float, int]:
    """Il livello di ogni dimensione sopra la prosa: rango, non soglia.

    La piu' grande e' `1`, poi `2`, e cosi' via. Oltre `MAX_LEVEL` si collassa,
    perche' e' quanto Markdown ha.

    **`carried` sono le dimensioni che producono davvero titoli**, e passarle
    cambia il risultato dove conta. Misurato: su Lan `80.0` si prende `h1` senza
    produrre un solo titolo; su Fab cinque dimensioni su dodici occupano un rango
    a vuoto, e le cinque che i titoli li producono finiscono tutte schiacciate su
    `h6`. Una dimensione che non intesta niente non consuma un livello.
    """

    if not prose:
        return {}
    limit = max(prose)
    above = sorted(
        (
            size
            for size in measurements.line_count
            if size > limit + SIZE_EPSILON and (carried is None or size in carried)
        ),
        reverse=True,
    )
    return {size: min(rank, MAX_LEVEL) for rank, size in enumerate(above, start=1)}


def sizes_that_carry_headings(
    pages: Sequence[Sequence[SizedLine]],
    measurements: FontSizeMeasurements,
    prose: frozenset[float],
) -> frozenset[float]:
    """Le dimensioni che, su questo documento, intestano davvero qualcosa.

    Si decide **prima** quali righe sono titoli, con i livelli provvisori, e
    **poi** si assegnano i ranghi solo alle dimensioni sopravvissute. Il giro
    inverso -- ranghi a tutte le dimensioni sopra la prosa -- lasciava i primi
    livelli a dimensioni che non intestano niente.
    """

    provisional = heading_levels(measurements, prose)
    found: set[float] = set()
    for lines in pages:
        merged, _groups = merge_wrapped(lines)
        for position in heading_lines(merged, prose, provisional):
            found.add(merged[position].size)
    return frozenset(found)


def heading_lines(
    lines: Sequence[SizedLine],
    prose: frozenset[float],
    levels: dict[float, int],
    excluded: frozenset[str] = frozenset(),
) -> dict[int, int]:
    """Da posizione della riga al suo livello di titolo. `lines` e' una pagina.

    `Criterio_Titoli_v3.md` §1. **L'unita' e' la riga, non il blocco.** Una riga
    e' un titolo se sta sopra tutta la prosa ed e' **l'unica alla sua dimensione
    dentro il suo blocco**.

    **Che cosa e' caduto della v2**, e va detto perche' non si rimetta: chiedevo
    che il blocco non contenesse prosa e avesse al piu' due righe. Misurato, quel
    vincolo costava cinque titoli -- su BiD `ridurre il sospetto` e `recuperare`,
    su Dag `QUANDO IL DISASTRO E' IMMINENTE` -- perche' il backend mette il titolo
    nello stesso blocco della prosa che introduce. E **non comprava** la
    protezione per cui l'avevo messo: su DrM le righe sopra la prosa in blocchi
    con prosa sono **zero**, perche' le celle di scheda stanno a dimensioni che
    sono esse stesse prosa.

    «Solo alla sua dimensione» separa dove il blocco non separava: un titolo e'
    solo, una cella di scheda o una riga di tabella ha sorelle alla stessa
    dimensione. Su BiD, delle righe sopra la prosa in blocchi con prosa, dieci
    sono sole e quattordici no.

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
    for positions in by_block.values():
        at_size: dict[float, int] = {}
        for position in positions:
            size = lines[position].size
            at_size[size] = at_size.get(size, 0) + 1
        for position in positions:
            line = lines[position]
            if len(line.text) <= 1 or line.text in excluded:
                continue
            level = levels.get(line.size)
            # **Sola alla sua dimensione nel blocco.** Le righe consecutive di
            # pari dimensione sono gia' state unite dal chiamante, quindi un
            # titolo che va a capo qui conta come una riga sola.
            if level is not None and at_size.get(line.size) == 1:
                found[position] = level
    return found


def merge_wrapped(
    lines: Sequence[SizedLine], breaks: frozenset[int] = frozenset()
) -> tuple[list[SizedLine], list[int]]:
    """Unisce le righe consecutive dello **stesso blocco** e **pari dimensione**.

    `Criterio_Titoli_v3.md` §2. Un titolo che va a capo e' **un** titolo: su Dag
    `FAR SALIRE DI LIVELLO IL` e `GRUPPO` stanno nello stesso blocco a dimensione
    12,0 e uscivano come due.

    **L'unione va fatta prima di contare.** La condizione del §1 chiede che la
    riga sia sola alla sua dimensione nel blocco: un titolo spezzato in due ne
    avrebbe due, e non sarebbe piu' un titolo affatto.

    **Solo lo stesso blocco**, ed e' il vincolo che impedisce di fondere titoli
    fratelli: su DB `ANIMISMO`, `ELEMENTALISMO` e `MENTALISMO` sono adiacenti e
    della stessa dimensione, ma ognuno nel suo blocco, e restano tre.

    `breaks` sono posizioni che **devono** cominciare un gruppo nuovo: le impone
    il `Criterio_TitoloSopraIlParagrafo_v1.md`, i cui titoli stanno alla stessa
    dimensione della prosa che intestano. Su Vil `DONI` e le quattro righe che lo
    seguono sono **tutte** a 11,6 nello stesso blocco, e senza questo l'unione se
    lo mangiava: e' la ragione per cui usciva `**DONI I doni sono aspetti…**` in
    un grassetto solo.

    Torna la lista unita e, per ogni riga originale, l'indice del gruppo a cui
    appartiene -- serve al chiamante per sapere dove NON rompere il paragrafo.
    """

    merged: list[SizedLine] = []
    group_of: list[int] = []
    for position, line in enumerate(lines):
        if (
            position not in breaks
            and merged
            and merged[-1].block == line.block
            and abs(merged[-1].size - line.size) < 0.05
        ):
            merged[-1] = SizedLine(
                block=line.block,
                text=f"{merged[-1].text} {line.text}".strip(),
                size=line.size,
                x0=min(merged[-1].x0, line.x0),
                x1=max(merged[-1].x1, line.x1),
                font=merged[-1].font,
            )
        else:
            merged.append(line)
        group_of.append(len(merged) - 1)
    return merged, group_of


def headings_above_a_paragraph(
    lines: Sequence[SizedLine],
    levels: dict[float, int],
    excluded: frozenset[str] = frozenset(),
) -> dict[int, int]:
    """I titoli che la dimensione non puo' vedere. `Criterio_TitoloSopraIlParagrafo_v1.md`.

    **Perche' la dimensione non basta.** Su Apo `LA DONNA DI CENDRES` sta a 10,6
    in `Calluna-Semibold` e il corpo accanto a 11,6 in `ArnoPro-Regular`: il
    titolo e' *nominalmente piu' piccolo* del testo che intesta, ed e' composto
    tutto in maiuscolo. Il punto tipografico misura il corpo del carattere, non
    l'inchiostro, e la scala dei ranghi qui misura la cosa sbagliata.

    Quattro condizioni, e nessuna e' un numero tarato -- margine, raggedness e
    font sono fatti **del blocco che si sta guardando**:

    1. il font che governa la riga e' diverso da quello che governa il blocco;
    2. nel blocco **la segue** almeno una riga governata dal font del blocco;
    3. finisce prima del margine destro del blocco, e di piu' di quanto le righe
       **interne** del blocco si concedano da sole;
    4. non e' gia' un titolo per dimensione, non e' arredo, non e' un carattere.

    **La 1 da sola non basta, ed e' misurato.** Su Vil idx 131 la seconda riga di
    `b0001` e' interamente in `ArnoPro-Bold` mentre il blocco e' governato da
    `ArnoPro-Regular`: la condizione sul font la promuoverebbe. Ma finisce a
    391,2 su un margine di 391,2 -- **riempie la misura** -- ed e' prosa che va a
    capo con un'enfasi dentro. `DONI`, sopra di lei, si ferma a 88,5.

    Il livello e' quello **subito sotto** il piu' profondo assegnato per
    dimensione, col tetto di `MAX_LEVEL`. E' una collocazione dichiarata e non
    misurata: un titolo che il documento compone piu' piccolo del corpo non e' un
    capitolo.
    """

    by_block: dict[str, list[int]] = {}
    for position, line in enumerate(lines):
        by_block.setdefault(line.block, []).append(position)

    level = min(max(levels.values(), default=0) + 1, MAX_LEVEL)
    found: dict[int, int] = {}
    for positions in by_block.values():
        if len(positions) < 2:
            continue
        block_font = _governing_font_of([lines[p] for p in positions])
        if block_font is None:
            continue
        margin = max(lines[p].x1 for p in positions)
        # Le righe **interne**: la prima puo' essere il titolo, l'ultima e' corta
        # per costruzione perche' e' dove il paragrafo finisce. Cio' che resta
        # dice quanto questo blocco lascia ragged il suo margine.
        inner = positions[1:-1]
        raggedness = max((margin - lines[p].x1 for p in inner), default=0.0)
        for order, position in enumerate(positions):
            line = lines[position]
            if len(line.text) <= 1 or line.text in excluded:
                continue
            if levels.get(line.size) is not None:
                continue
            if line.font is None or line.font == block_font:
                continue
            follows = any(
                lines[other].font == block_font for other in positions[order + 1 :]
            )
            if not follows:
                continue
            if margin - line.x1 <= raggedness:
                continue
            found[position] = level
    return found


def _governing_font_of(lines: Sequence[SizedLine]) -> str | None:
    """Il font della maggioranza dei caratteri di queste righe."""

    weight: dict[str, int] = {}
    for line in lines:
        if line.font:
            weight[line.font] = weight.get(line.font, 0) + len(line.text)
    if not weight:
        return None
    return max(weight.items(), key=lambda item: (item[1], item[0]))[0]
