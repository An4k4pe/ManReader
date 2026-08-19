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
    KIND_TEXT_PARAGRAPH,
    AssetRefIR2,
    DocumentIR2,
    NodeIR2,
    PageIR2,
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


def render_node(node: NodeIR2) -> str:
    """Render one node. Unknown kinds are not guessed at."""

    if node.kind == KIND_TEXT_PARAGRAPH:
        return node.text or ""
    if node.kind == KIND_ASSET_NOTE:
        if node.asset is None:
            raise ValueError("an asset.note node must carry an asset")
        return render_asset_note(node.asset)
    raise ValueError(f"no renderer for kind {node.kind!r}")


def is_rendered_in_body(node: NodeIR2, *, render_unresolved: bool) -> bool:
    """Whether a node belongs in the body, or in the review channel instead."""

    if node.kind != KIND_ASSET_NOTE:
        return True
    if render_unresolved:
        return True
    return node.resolution == "accepted"


def render_page_markdown(
    page: PageIR2,
    *,
    render_unresolved_assets: bool = RENDER_UNRESOLVED_ASSET_NOTES,
) -> str:
    """Render one page. Nodes are emitted in ``order``, which is reading order.

    Asset notes whose candidate Resolution did not accept are **not** rendered by
    default; they stay in IR 2 as nodes and belong to the review channel. See
    ``RENDER_UNRESOLVED_ASSET_NOTES``.
    """

    if not isinstance(page, PageIR2):
        raise ValueError("page must be a PageIR2")

    blocks = [
        rendered
        for rendered in (
            render_node(node)
            for node in sorted(page.nodes, key=lambda n: n.order)
            if is_rendered_in_body(node, render_unresolved=render_unresolved_assets)
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
