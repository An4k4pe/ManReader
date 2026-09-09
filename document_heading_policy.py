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


# Quanti caratteri identici consecutivi fanno un **filetto di guida**. Quattro e
# non tre, perche' tre punti sono i puntini di sospensione, che stanno dentro una
# frase legittima. `Criterio_Capolettera_v1.md` §3.
LEADER_RUN = 4

# I confini del **titolo impilato**, `Criterio_TitoloImpilato_v1.md` §1. Stanno
# tutti dentro vuoti misurati su 114 coppie candidate dei sedici manuali: dentro
# nessuno dei tre cade un solo caso.
#
#   sovrapposizione >= 0,22   vuoto 0,167 -> 0,264   interlinea normale / negativa
#   sovrapposizione <  1,00   vuoto 0,871 -> 1,025   impilato / affiancato
#   avanzamento     <= 1,50   vuoto 1,182 -> 3,898   titolo che continua / paragrafo
STACK_OVERLAP_MIN = 0.22
STACK_OVERLAP_MAX = 1.0
STACK_ADVANCE_MAX = 1.5


def is_stacked(previous: SizedLine, line: SizedLine) -> bool:
    """Se le due righe sono composte **una sull'altra**, cioe' un titolo solo.

    `Criterio_TitoloImpilato_v1.md` §1. Un titolo display impilato e' composto con
    l'**interlinea negativa** -- le parole si incastrano -- mentre un'intestazione
    e cio' che introduce hanno interlinea normale, e due colonne affiancate hanno
    scatole che si contengono. Tre figure diverse, e la composizione le distingue.

    **L'avanzamento positivo non e' una soglia, e' un verso**: dice che la seconda
    riga sta *sotto* e non *accanto*. E' cio' che toglie le 22 coppie di BoB --
    `'sgattaiolare' + 'ESEMPI'`, `'orologio da 8' + 'MIGLIORARE LE MISSIONI'` --
    che hanno avanzamento **negativo** perche' stanno in colonne diverse che il
    blocco ha messo insieme, e che avevano fatto ritirare il meccanismo
    precedente (`Esito_TitoloComposto_v1.md` §2).

    Tutto e' rapportato all'altezza della **scatola piu' piccola**: e' la sola
    delle due che sia confrontabile fra corpi molto diversi.
    """

    smaller = min(previous.y1 - previous.y0, line.y1 - line.y0)
    if smaller <= 0:
        return False
    overlap = (previous.y1 - line.y0) / smaller
    advance = (line.y0 - previous.y0) / smaller
    return (
        0.0 < advance <= STACK_ADVANCE_MAX
        and STACK_OVERLAP_MIN <= overlap < STACK_OVERLAP_MAX
    )


def has_leader(text: str) -> bool:
    """Se il testo contiene un filetto di guida, cioe' una voce di sommario.

    Il segnale e' la **ripetizione tipografica** -- `'.............'` -- non una
    lunghezza tarata: il filetto si riconosce dal carattere ripetuto.

    Misurato su BoB: delle 19 righe promosse piu' lunghe di 60 caratteri, **18
    sono a 12,0 pt sulle pagine idx 6-8**, cioe' il sommario di apertura. Ognuna
    e' sola alla sua dimensione nel proprio blocco, quindi passava la regola di
    riga, e la sua fascia passava il filtro sulla lunghezza con 0,45 contro 0,50.
    """

    run = 0
    previous = ""
    for character in text:
        if character.isalnum() or character.isspace():
            run = 0
            previous = ""
            continue
        if character == previous:
            run += 1
            if run >= LEADER_RUN:
                return True
        else:
            previous = character
            run = 1
    return False


def heading_lines(
    lines: Sequence[SizedLine],
    prose: frozenset[float],
    levels: dict[float, int],
    excluded: frozenset[str] = frozenset(),
    *,
    max_length: float | None = None,
) -> dict[int, int]:
    """Da posizione della riga al suo livello di titolo. `lines` e' una pagina.

    `Criterio_Titoli_v3.md` §1. **L'unita' e' la riga, non il blocco.** Una riga
    e' un titolo se sta sopra tutta la prosa ed e' **l'unica alla sua dimensione
    dentro il suo blocco**.

    ``max_length`` e' la mediana di riga del corpo: **una riga piu' lunga di una
    riga di prosa non e' un titolo**, qualunque sia la sua fascia.
    `Criterio_TettoDallaMassa_v1.md` §1. Il filtro sulla lunghezza esisteva gia',
    ma guardava la **mediana della fascia** mentre la promozione si decide **riga
    per riga**: su Fab una fascia con mediana 19 caratteri conteneva una riga di
    **628**, e il meccanismo dichiarava «i titoli hanno righe corte» producendo un
    titolo di 628 caratteri.

    Il rapporto qui e' **1,0** e non il mezzo del filtro di fascia, e la
    differenza ha una ragione: la fascia si giudica sulla **tendenza** -- i titoli
    in media sono molto piu' corti del testo -- e la riga sul **limite**: un
    titolo puo' essere lungo, ma non piu' di una riga intera di prosa. Su Fab il
    corpo ha mediana 53 caratteri: al mezzo morirebbe
    `TABELLE PER LA CREAZIONE DELL'IDENTITA'` (38), che e' un titolo vero.

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
            # Una voce di sommario non e' un titolo, per quanto sia sola
            # alla sua dimensione nel blocco. `Criterio_Capolettera_v1.md` §3.
            if has_leader(line.text):
                continue
            # Una riga piu' lunga di una riga di prosa non e' un titolo.
            # `Criterio_TettoDallaMassa_v1.md` §1.
            if max_length is not None and len(line.text) > max_length:
                continue
            level = levels.get(line.size)
            # **Sola alla sua dimensione nel blocco.** Le righe consecutive di
            # pari dimensione sono gia' state unite dal chiamante, quindi un
            # titolo che va a capo qui conta come una riga sola.
            if level is not None and at_size.get(line.size) == 1:
                found[position] = level
    return found


def merge_wrapped(
    lines: Sequence[SizedLine],
    breaks: frozenset[int] = frozenset(),
    levels: dict[float, int] | None = None,
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

    **A dimensioni diverse serve la geometria**, ed e' il
    `Criterio_TitoloImpilato_v1.md`. Il primo tentativo -- unire due titoli
    adiacenti dello stesso blocco e basta -- e' caduto con 83 unioni in
    maggioranza sbagliate (`'sgattaiolare ESEMPI'` su BoB): «solo lo stesso
    blocco» impedisce di fondere i titoli **fratelli**, che stanno a pari
    dimensione in blocchi diversi, ma un'intestazione e cio' che introduce hanno
    dimensioni **diverse** e stanno nello **stesso** blocco.

    Con ``levels`` dato, due righe di dimensioni diverse si uniscono solo se sono
    **composte una sull'altra** -- `is_stacked` -- e il livello risultante e'
    quello della dimensione **maggiore**: un titolo e' prominente almeno quanto la
    sua parola piu' prominente. Su Kul i corpi crescono parola per parola, 86, 95,
    102, e quella crescita e' un effetto grafico, non una gerarchia.

    Il confronto geometrico e' fra la riga e **quella originale che la precede**,
    non fra la riga e l'unione accumulata: le scatole di un'unione si allargano, e
    misurare su quelle cambierebbe i rapporti a ogni passo.

    Torna la lista unita e, per ogni riga originale, l'indice del gruppo a cui
    appartiene -- serve al chiamante per sapere dove NON rompere il paragrafo.
    """

    merged: list[SizedLine] = []
    group_of: list[int] = []
    previous: SizedLine | None = None
    for position, line in enumerate(lines):
        same_size = bool(merged) and abs(merged[-1].size - line.size) < 0.05
        stacked = (
            levels is not None
            and bool(merged)
            and previous is not None
            and levels.get(merged[-1].size) is not None
            and levels.get(line.size) is not None
            and is_stacked(previous, line)
        )
        if (
            position not in breaks
            and merged
            and merged[-1].block == line.block
            and (same_size or stacked)
        ):
            merged[-1] = SizedLine(
                block=line.block,
                text=f"{merged[-1].text} {line.text}".strip(),
                # A pari dimensione resta quella; impilate vince la maggiore.
                size=line.size if same_size else max(merged[-1].size, line.size),
                x0=min(merged[-1].x0, line.x0),
                x1=max(merged[-1].x1, line.x1),
                font=merged[-1].font,
                y0=min(merged[-1].y0, line.y0),
                y1=max(merged[-1].y1, line.y1),
            )
        else:
            merged.append(line)
        group_of.append(len(merged) - 1)
        previous = line
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
            # Una voce di sommario non e' un titolo, per quanto sia sola
            # alla sua dimensione nel blocco. `Criterio_Capolettera_v1.md` §3.
            if has_leader(line.text):
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
