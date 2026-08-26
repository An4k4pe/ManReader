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

from ir2_model import (
    KIND_ASSET_NOTE,
    KIND_TABLE,
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    DocumentIR2,
    NodeIR2,
    PageIR2,
    TableIR2,
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


def render_runs(node: NodeIR2) -> str:
    """Il testo del nodo con grassetto e corsivo, dai run.

    Senza run -- o con un solo run senza tratti -- torna esattamente il testo di
    prima: il campo e' additivo e un nodo che non lo porta rende come sempre.

    Il markup si chiude e riapre a ogni run invece di cercare l'estensione
    massima: la seconda cosa richiederebbe di riordinare i delimitatori attorno
    agli spazi, ed e' il genere di furbizia che rompe su un caso che nessuno ha
    guardato. Gli spazi di giunzione stanno **dentro** il run che li precede
    (vedi `ir2_builder.join_runs`), quindi un `**parola **` non si forma perche'
    lo spazio non e' mai in testa a un run marcato.
    """

    text = node.text or ""
    if not node.runs:
        return text

    pieces: list[str] = []
    for run in node.runs:
        piece = run.text
        stripped = piece.strip()
        if stripped:
            leading = piece[: len(piece) - len(piece.lstrip())]
            trailing = piece[len(piece.rstrip()) :]
            for trait, delimiter in _MARKUP:
                if trait in run.traits:
                    stripped = f"{delimiter}{stripped}{delimiter}"
            piece = f"{leading}{stripped}{trailing}"
        pieces.append(piece)
    return "".join(pieces)


def render_node(node: NodeIR2) -> str:
    """Render one node. Unknown kinds are not guessed at."""

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
    render_page_label: bool = True,
) -> str:
    """Render one page. Nodes are emitted in ``order``, which is reading order.

    Asset notes whose candidate Resolution did not accept are **not** rendered by
    default; they stay in IR 2 as nodes and belong to the review channel. See
    ``RENDER_UNRESOLVED_ASSET_NOTES``.

    ``excluded_node_ids`` carries the furniture policy the caller computed; see
    ``is_rendered_in_body``.
    """

    if not isinstance(page, PageIR2):
        raise ValueError("page must be a PageIR2")

    blocks: list[str] = []
    if render_page_label and page.page_label:
        # Il numero stampato che il PDF dichiara, non uno dedotto. Sta nella
        # stessa forma delle note d'asset -- una riga breve che dice che cosa
        # c'era -- perche' e' la stessa cosa: un elemento della pagina reso come
        # riferimento invece che lasciato in mezzo al testo.
        blocks.append(f"> **[pagina {page.page_label}]**")
    blocks += [
        rendered
        for rendered in (
            render_node(node)
            for node in sorted(page.nodes, key=lambda n: n.order)
            if is_rendered_in_body(
                node,
                render_unresolved=render_unresolved_assets,
                excluded_node_ids=excluded_node_ids,
            )
        )
        if rendered
    ]
    return "\n\n".join(blocks) + "\n" if blocks else ""


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
