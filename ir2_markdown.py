"""Render Markdown from DocumentIR 2. IR2-first, legacy renderers untouched.

Third of the four modules of ``Proposta_IR2Minima_v3.md`` §7.

**Why a new emitter instead of an adapter down to IR 1.** ``markdown_builder``
re-derives from geometry the structure IR 2 already carries decided from the
source, and two of its three conditions cannot be driven by any adapter:
``_should_start_new_paragraph`` joins a paragraph whose predecessor does not end
with strong punctuation whatever the geometry says, and ``_is_heading_text``
promotes any short uppercase text to a heading before it even looks at the style.
``BlockIR`` has no channel to declare a kind, so getting the intended output would
mean fabricating fake geometry and style -- making the adapter lie about the PDF.
Measured, not predicted: the legacy Markdown of DB p.99 shows three identical stat
blocks rendered three different ways and a running header promoted to a heading.

This module renders **only what v0 emits**: paragraphs and asset notes. Headings,
callouts and tables are in the vocabulary and not in emission, each for a reason
recorded in the proposal.

The asset note says **what was replaced**, which is half of ``AGENTS.MD``
§Obiettivo and had never had a milestone: «sostituire immagini, sfondi ed elementi
ripetuti con note brevi e riassuntive di cio' che hanno sostituito». It reports the
governing candidate's ``proposed_structural_kind``, which is a proposal and not a
decision -- so the note describes what was there structurally and how big it was,
never what it depicts. Describing the content would need the optional local AI and
would risk inventing it.
"""

from __future__ import annotations

from document_list_policy import split_number
from ir2_model import (
    KIND_ASSET_NOTE,
    KIND_TABLE,
    KIND_TEXT_HEADING,
    KIND_TEXT_LIST_ITEM,
    KIND_TEXT_LIST_ITEM_ORDERED,
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    DocumentIR2,
    NodeIR2,
    PageIR2,
    TableIR2,
    TextRunIR2,
)

# Politica di resa delle note d'asset, decisione dell'utente del 19 agosto 2026.
#
# Il NODO esiste per ogni occorrenza -- e' la copertura per costruzione, e
# `resolution` ne riporta l'esito. Cio' che si decide qui e' la RESA: nel corpo
# del Markdown vanno solo le note il cui candidato Resolution ha ACCETTATO.
#
# Perche': senza questa porta ogni occorrenza con un file su disco diventava una
# nota nel corpo. Misurato sul campione cieco: 75 note contro le 10 della base,
# 65 delle quali con resolution "unresolved" -- l'87% del rumore veniva da qui e
# non dall'arredo. Le altre non spariscono: vanno nel canale review, che e' il
# posto da cui si guardera' quando l'arredo verra' affrontato, o quando si
# verifichera' se altri producer lo risolvono gia'.
#
# E' una politica, quindi e' un parametro con un default dichiarato, non una
# costante nascosta in un ramo.
RENDER_UNRESOLVED_ASSET_NOTES = False

# Dal kind strutturale proposto alla frase che il lettore vede. Non e' una
# classificazione nuova: e' la traduzione di cio' che il candidato gia' dichiara.
_KIND_PHRASES = {
    "layout.page_covering_visual": "sfondo di pagina",
    "layout.page_edge_visual": "elemento di bordo",
    "layout.embedded_visual": "immagine inserita",
    "layout.interior_visual_frame": "riquadro",
}
_UNCLASSIFIED_PHRASE = "immagine non classificata"


def render_asset_note(asset: AssetRefIR2) -> str:
    """One short line saying what was removed, how big it was, and where it is."""

    phrase = (
        _UNCLASSIFIED_PHRASE
        if asset.proposed_structural_kind is None
        else _KIND_PHRASES.get(asset.proposed_structural_kind, _UNCLASSIFIED_PHRASE)
    )
    width = asset.bbox[2] - asset.bbox[0]
    height = asset.bbox[3] - asset.bbox[1]
    repeated = (
        f", {asset.occurrence_count} occorrenze in pagina" if asset.occurrence_count > 1 else ""
    )
    return f"> **[{phrase}]** {width:.0f}×{height:.0f} pt{repeated} — `{asset.file_name}`"


def render_table(table: TableIR2) -> str:
    """Render a grid as a Markdown table.

    The first row becomes the header, because Markdown has no table without one.
    It is a **rendering** choice and it is declared: IR 2 does not say which row
    is a header, and inventing that claim in the contract would be rendering
    written into the IR.

    A cell's newlines and pipes are escaped rather than dropped: a Markdown table
    cannot hold a line break, and losing the character silently would be the
    content disappearing while every check stays green.
    """

    def cell_text(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " ").strip() or " "

    rows = [[cell_text(cell.text) for cell in row] for row in table.rows]
    width = len(rows[0])
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


# Solo i due tratti che il Markdown sa dire. `serifed`, `monospaced` e
# `superscript` restano registrati sul nodo e **ignorati qui**: il primitivo li
# conserva perche' buttarli sarebbe la stessa perdita che questo lavoro ripara,
# ma inventargli una resa sarebbe far mentire l'adattatore sul PDF. Un tratto
# registrato e non reso non e' un difetto, ed e' scritto perche' nessuno lo conti
# come tale.
_MARKUP = (("bold", "**"), ("italic", "*"))


def _traits_per_character(node: NodeIR2) -> list[tuple[str, frozenset[str]]]:
    """Ogni carattere del nodo con i tratti che lo governano.

    Lo spazio prende un tratto **solo se ce l'hanno entrambi i vicini**. Senza
    questa regola un run marcato che finisce con uno spazio produrrebbe
    ``**parola **``, che Markdown non chiude; con questa regola ``**due parole**``
    resta intero perche' lo spazio interno e' grassetto da entrambi i lati.
    """

    characters: list[tuple[str, frozenset[str]]] = []
    for run in node.runs:
        traits = frozenset(trait for trait, _ in _MARKUP if trait in run.traits)
        characters.extend((character, traits) for character in run.text)

    for position, (character, _traits) in enumerate(characters):
        if not character.isspace():
            continue
        before = next(
            (t for c, t in reversed(characters[:position]) if not c.isspace()), None
        )
        after = next(
            (t for c, t in characters[position + 1 :] if not c.isspace()), None
        )
        shared = frozenset() if before is None or after is None else before & after
        characters[position] = (character, shared)
    return characters


def render_runs(node: NodeIR2) -> str:
    """Il testo del nodo con grassetto e corsivo, dai run.

    Senza run -- o con un solo run senza tratti -- torna esattamente il testo di
    prima: il campo e' additivo e un nodo che non lo porta rende come sempre.

    **I delimitatori si aprono e si chiudono come parentesi**, non a ogni run.
    Chiudere e riaprire era piu' semplice e produceva Markdown rotto quando due
    run marcati sono adiacenti: su FWK un run grassetto seguito da uno
    grassetto-corsivo dava ``**Richiamare Armatura +*****Audace***`` -- cinque
    asterischi, che nessun parser interpreta come inteso. Ora il grassetto resta
    aperto attraverso i due run e il corsivo si annida dentro:
    ``**Richiamare Armatura +*Audace***``.

    Il testo non cambia mai: si inseriscono delimitatori, non si toglie e non si
    aggiunge nemmeno uno spazio.

    **Un caso resta e va dichiarato**: due tratti **disgiunti** e adiacenti senza
    spazio in mezzo -- corsivo attaccato a grassetto -- danno ``*a***b**``, che
    con i delimitatori ad asterisco non si puo' evitare, perche' la chiusura di
    uno e l'apertura dell'altro sono lo stesso carattere. Si eviterebbe usando
    ``_`` per il corsivo, che pero' CommonMark non riconosce dentro parola. Sul
    materiale reso finora l'unica collisione misurata era quella dei tratti
    sovrapposti, che questo codice risolve; questa non e' comparsa.
    """

    text = node.text or ""
    if not node.runs:
        return text

    order = [trait for trait, _ in _MARKUP]
    delimiter_of = dict(_MARKUP)
    pieces: list[str] = []
    open_traits: list[str] = []

    def close_until(wanted: frozenset[str]) -> None:
        # Si svuota finche' TUTTO cio' che resta aperto e' voluto, non finche' lo
        # e' la cima: un tratto da chiudere puo' stare sotto uno da tenere, e
        # guardare solo la cima lo lasciava aperto fino in fondo al paragrafo.
        # Cio' che si e' chiuso di troppo lo riapre il ciclo qui sotto.
        while open_traits and any(trait not in wanted for trait in open_traits):
            pieces.append(delimiter_of[open_traits.pop()])

    per_character = _traits_per_character(node)

    def extent(trait: str, start: int) -> int:
        """Per quanti caratteri il tratto resta acceso senza interruzioni."""

        length = 0
        while start + length < len(per_character) and trait in per_character[start + length][1]:
            length += 1
        return length

    for position, (character, traits) in enumerate(per_character):
        if traits != frozenset(open_traits):
            close_until(traits)
            # Si apre per **durata decrescente**: il tratto che dura di piu' sta
            # fuori. Aprendo in ordine fisso, un grassetto-corsivo seguito da
            # solo corsivo chiudeva entrambi e riapriva il corsivo -- `***a****b*`,
            # cioe' un'altra collisione. Con il corsivo fuori resta `***a**b*`.
            opening = [t for t in order if t in traits and t not in open_traits]
            for trait in sorted(opening, key=lambda t: -extent(t, position)):
                open_traits.append(trait)
                pieces.append(delimiter_of[trait])
        pieces.append(character)
    close_until(frozenset())
    return "".join(pieces)


def render_list_item(node: NodeIR2) -> str:
    """Una voce d'elenco, col marcatore sostituito dalla sintassi Markdown.

    **Il marcatore esce dalla resa, non dall'IR**: `node.text` lo conserva, e chi
    consuma i dati ce l'ha. Quale testa sia il marcatore lo dice `node.marker`,
    deciso dal costruttore dove le primitive ci sono -- questa funzione vede
    caratteri, e coi soli caratteri su Fab toglieva la `O` di `Olivia`. E' la stessa forma dell'arredo -- niente viene
    distrutto, cambia cio' che si vede -- e la ragione e' la stessa: nessuno a
    valle puo' rifiutare questa esclusione, quindi il controllo sta nel criterio.

    Tenerlo darebbe `- *\t Fumante, sudata, calda.`, che oltre a essere
    illeggibile e' **ambiguo per Markdown**: un `-` seguito da `*` e una
    tabulazione si legge come elenco annidato. Un marcatore tenuto non e' neutro.
    """

    # **Il nodo dice quale testa e' il glifo**, e qui non si indovina piu' dai
    # caratteri: `Criterio_MarcatorePerPrimitiva_v1.md`. Su Fab la stessa `O` e'
    # un glifo in un font display e la prima lettera di `Olivia` nel font del
    # corpo, e togliendola per posizione la resa dava `- livia`.
    # Un nodo senza `marker` non ha niente da togliere.
    prefix = node.marker or ""
    body = (node.text or "")[len(prefix) :]
    if not body.strip():
        # Il marcatore e' rimasto orfano del suo testo: succede quando l'ordine
        # di lettura interlaccia due colonne di elenchi e i glifi arrivano prima
        # delle voci (limite gia' a verbale nel builder per DB p.53). Una voce
        # vuota e' peggio di nessuna voce, e il testo esce come paragrafo suo.
        return ""
    if not node.runs:
        return f"- {body}"

    # Il marcatore si toglie **dai run**, non dalla stringa gia' resa: se e' in
    # grassetto -- e su FW lo e' -- `render_runs` lo avvolge in asterischi, e
    # cercarlo in testa alla stringa resa lo mancava, lasciando `- • Afflizione`.
    dropped = len(prefix)
    trimmed: list[TextRunIR2] = []
    for run in node.runs:
        if dropped <= 0:
            trimmed.append(run)
            continue
        if len(run.text) <= dropped:
            dropped -= len(run.text)
            continue
        trimmed.append(TextRunIR2(text=run.text[dropped:], traits=run.traits))
        dropped = 0
    stripped_node = NodeIR2(
        node_id=node.node_id,
        order=node.order,
        kind=node.kind,
        primitive_ids=node.primitive_ids,
        page_ids=node.page_ids,
        text="".join(run.text for run in trimmed),
        runs=tuple(trimmed),
    )
    return f"- {render_runs(stripped_node)}"


def render_ordered_item(node: NodeIR2) -> str:
    """Una voce numerata, col **suo** numero e non uno rinumerato da 1.

    `Criterio_ElencoNumerato_v1.md` §2: un elenco che continua da una pagina
    prima e comincia da `4.`, riscritto `1.`, direbbe una cosa falsa. Markdown
    accetta il numero di partenza.
    """

    rendered = render_runs(node)
    parsed = split_number(rendered)
    if parsed is None:
        return rendered
    number, body = parsed
    return f"{number}. {body}" if body.strip() else ""


def render_node(node: NodeIR2) -> str:
    """Render one node. Unknown kinds are not guessed at.

    **Non prende piu' l'insieme dei marcatori**, e nessuno qui dentro lo prende:
    quale testa sia il marcatore lo dichiara il nodo, `NodeIR2.marker`, deciso
    dal costruttore dove le primitive ci sono. Un renderer che indovina dai
    caratteri e' il difetto che ha prodotto `- livia` su Fab.
    """

    if node.kind == KIND_TEXT_HEADING:
        if node.heading_level is None:
            raise ValueError("a heading node must carry a heading_level")
        return f"{'#' * node.heading_level} {render_runs(node)}"
    if node.kind == KIND_TEXT_LIST_ITEM_ORDERED:
        return render_ordered_item(node)
    if node.kind == KIND_TEXT_LIST_ITEM:
        return render_list_item(node)
    if node.kind == KIND_TEXT_PARAGRAPH:
        return render_runs(node)
    if node.kind == KIND_ASSET_NOTE:
        if node.asset is None:
            raise ValueError("an asset.note node must carry an asset")
        return render_asset_note(node.asset)
    if node.kind == KIND_TABLE:
        if node.structure is None:
            raise ValueError("a table node must carry a structure")
        return render_table(node.structure)
    raise ValueError(f"no renderer for kind {node.kind!r}")


def is_rendered_in_body(
    node: NodeIR2,
    *,
    render_unresolved: bool,
    excluded_node_ids: frozenset[str] = frozenset(),
) -> bool:
    """Whether a node belongs in the body, or in the review channel instead.

    ``excluded_node_ids`` is a **policy the caller computes**, not a mark on the
    node: nothing is written to `NodeIR2`, the serialization is unchanged, and no
    new ``kind`` is born. It is the same shape as ``RENDER_UNRESOLVED_ASSET_NOTES``
    above -- a parameter with a declared default rather than a constant hidden in
    a branch -- and it extends a gate that is already open: `5bbb5f5` decided that
    an asset whose candidate Resolution did not accept stays a node and is
    filtered at rendering.

    **The difference is declared and not hidden.** That gate keys on
    ``resolution``, which is a decision Resolution took about a candidate. Here
    there is no candidate and no Resolution, so **nothing downstream can refuse
    this exclusion** -- which is why `Criterio_ArredoRicorrente_v3.md` puts its
    veto at zero and checks the junction around every removed item. If nobody can
    refuse it later, the check has to be there.

    The declared cost: the decision does not survive serialization, so the
    Markdown and the review channel must be produced in the same run.
    """

    if node.node_id in excluded_node_ids:
        return False
    if node.kind != KIND_ASSET_NOTE:
        return True
    if render_unresolved:
        return True
    return node.resolution == "accepted"


def render_page_markdown(
    page: PageIR2,
    *,
    render_unresolved_assets: bool = RENDER_UNRESOLVED_ASSET_NOTES,
    excluded_node_ids: frozenset[str] = frozenset(),
    render_page_label: bool = False,
) -> str:
    """Render one page. Nodes are emitted in ``order``, which is reading order.

    Asset notes whose candidate Resolution did not accept are **not** rendered by
    default; they stay in IR 2 as nodes and belong to the review channel. See
    ``RENDER_UNRESOLVED_ASSET_NOTES``.

    ``excluded_node_ids`` carries the furniture policy the caller computed; see
    ``is_rendered_in_body``.

    **Il numero di pagina non si rende, ed e' spento di default.** Decisione
    dell'utente del 27 agosto 2026: il riferimento serve **fra i blocchi dati del
    programma**, non nel testo che si legge. Il fatto resta dove serve --
    ``PageIR2.page_label``, serializzato -- e chi lo consuma ce l'ha; il lettore
    non ha bisogno di vederselo scritto in mezzo al testo.

    Una versione precedente lo rendeva come ``> **[pagina 368]**``: era una mia
    lettura estensiva dell'indicazione «referenziare il numero serve a sapere che
    pagina si sta trattando», che riguardava il dato e non la resa. Il parametro
    resta perche' l'EPUB avra' bisogno di un marcatore di confine pagina
    (``epub:type="pagebreak"``), che e' un'altra forma e un'altra decisione.
    """

    if not isinstance(page, PageIR2):
        raise ValueError("page must be a PageIR2")

    blocks: list[str] = []
    if render_page_label and page.page_label:
        blocks.append(f"> **[pagina {page.page_label}]**")
    rendered_nodes = [
        (node, render_node(node))
        for node in sorted(page.nodes, key=lambda n: n.order)
        if is_rendered_in_body(
            node,
            render_unresolved=render_unresolved_assets,
            excluded_node_ids=excluded_node_ids,
        )
    ]

    # Le voci consecutive di un elenco si uniscono con **una** riga a capo, non
    # due: in Markdown una riga vuota fra le voci produce una lista «larga», con
    # un paragrafo dentro ogni voce, e si legge spaziata come se fossero blocchi
    # separati. Fra un elenco e cio' che lo circonda la riga vuota ci vuole,
    # altrimenti il paragrafo precedente si attacca alla prima voce.
    def marker_of(node: NodeIR2) -> str | None:
        """Il marcatore che il **nodo dichiara**, non uno indovinato dal testo.

        Serviva a raggruppare le voci consecutive dello stesso elenco, e lo
        cercava fra i caratteri: su Fab dava `O` per `Olivia`, che marcatore non
        e'. `Criterio_MarcatorePerPrimitiva_v1.md`.
        """

        return (node.marker or "").strip() or None

    parts: list[str] = list(blocks)
    previous_marker: str | None = None
    for node, rendered in rendered_nodes:
        if not rendered:
            continue
        marker = marker_of(node) if node.kind == KIND_TEXT_LIST_ITEM else None
        if node.kind == KIND_TEXT_LIST_ITEM_ORDERED:
            marker = "#numerato"
        # **Un marcatore diverso e' un elenco diverso.** Su FWK `•` apre le voci
        # che ne introducono altre e `*` le voci vere: unirle tutte darebbe un
        # elenco solo di otto voci dove il manuale ne ha tre. L'annidamento resta
        # fuori -- le voci restano allo stesso livello, come il criterio dichiara
        # -- ma almeno gli elenchi restano distinti.
        if marker is not None and marker == previous_marker and parts:
            parts[-1] = f"{parts[-1]}\n{rendered}"
        else:
            parts.append(rendered)
        previous_marker = marker
    return "\n\n".join(parts) + "\n" if parts else ""


def render_document_markdown(
    document: DocumentIR2,
    *,
    render_unresolved_assets: bool = RENDER_UNRESOLVED_ASSET_NOTES,
) -> str:
    """Render a whole document, one page after another."""

    if not isinstance(document, DocumentIR2):
        raise ValueError("document must be a DocumentIR2")

    parts: list[str] = []
    for page in document.pages:
        parts.append(f"<!-- page: {page.page_id} -->")
        rendered = render_page_markdown(
            page, render_unresolved_assets=render_unresolved_assets
        )
        if rendered:
            parts.append(rendered.rstrip("\n"))
    return "\n\n".join(parts) + "\n" if parts else ""
