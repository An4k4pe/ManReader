"""DocumentIR 2 contracts: the content side of the new pipeline.

Data-only contracts. This module does not read PDFs, run producers, resolve
candidates, persist JSON, or render anything.

Approved by ``Proposta_IR2Minima_v3.md`` (Modalita' P, due giri di revisione
indipendente). Uno stadio solo: ``ResolvedSemanticDocument`` non viene costruito,
e la ragione e' che non esiste in nessun file di codice del repo mentre
``DocumentIR`` esiste come contratto, store, validatore e renderer -- si costruisce
lo stadio con un precedente strutturale e si salta quello senza.

WHAT IS NEW HERE, and is not new anywhere else in the project:

- **The order of ``PageIR2.nodes`` is reading order**, and ``NodeIR2.order``
  carries it explicitly. ``page_analysis_model`` denies reading order to
  candidates and relations on purpose; here it becomes contract. The explicit
  field follows the ``BlockIR.order`` precedent of IR 1 (``ir_model.py``) instead
  of leaving the order implicit in a tuple position, so that it stays diffable.
- **Ownership.** Assigning a primitive to a node is ownership, and
  ``AGENTS.MD`` lists ``ownership finale`` among the activities needing a
  dedicated architectural decision. The ownership produced here is **of stage and
  regenerable**: a node is rebuilt from scratch on every run from primitives and
  candidates, and no decision becomes irreversible.

``NodeIR2.node_id`` must stay stable across regenerations, because human
corrections and AI proposals target a node by id (the ``AIProposal.target_id`` /
``HumanOverride.target_id`` precedent in ``ir_model.py``, kept separate from the
extracted data). Stability is bounded, and the bounds are declared in
``Proposta_IR2Minima_v3.md`` §5.1: the composition of the node, the future cure
for capture degeneracy, the absent versioning of the capture logic, and the known
degenerate-capture case.

``kind`` is an open pattern, not a closed list -- same discipline as
``_STRUCTURAL_KIND_PATTERN``. Growing the vocabulary does not touch this module.
The limit is declared: it holds for kinds without internal structure. A kind that
must distinguish, say, a label from a value has nowhere to put it here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from geometry_model import (
    BBox,
    _validate_bbox,
    _validate_non_empty_string,
    _validate_non_negative_int,
)

IR2_SCHEMA_VERSION = "2.0"

_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")

# Vocabolario dichiarato. NON e' una lista chiusa e non viene usata per
# validare: sta qui perche' un lettore sappia cosa il progetto intende emettere,
# e quali kind sono gia' stati decisi ma non hanno ancora chi li riempie.
KIND_TEXT_PARAGRAPH = "text.paragraph"
# Una voce d'elenco. E' un kind suo e non un paragrafo con un flag perche' la
# resa e' diversa e il vocabolario di IR 2 dichiara i generi, non li deduce.
# `Criterio_Elenchi_v1.md`.
KIND_TEXT_LIST_ITEM = "text.list_item"
# Una voce di elenco **numerato**. Kind suo perche' la resa e' diversa e il
# numero va conservato: `Criterio_ElencoNumerato_v1.md` §2 vieta di rinumerare
# da 1, perche' un elenco che continua da una pagina prima e comincia da `4.`
# riscritto `1.` direbbe una cosa falsa.
KIND_TEXT_LIST_ITEM_ORDERED = "text.list_item_ordered"
KIND_ASSET_NOTE = "asset.note"
KIND_TABLE = "layout.table"
# Nel vocabolario, NON in emissione in v0:
#   text.heading  -- il criterio non esiste; su DB p.99 il solo corpo di pagina
#                    ne prende uno su quattro. Milestone sua.
#   text.callout  -- interior_visual_frame li trova gia', ma scegliere fra
#                    candidati annidati e' una decisione di Resolution.

_VALID_RESOLUTIONS = frozenset({"accepted", "rejected", "unresolved"})


def _validate_kind(value: str) -> None:
    if not isinstance(value, str) or _KIND_PATTERN.fullmatch(value) is None:
        raise ValueError("kind must be a namespaced lowercase kind")


def _validate_unique_non_empty_ids(value: tuple[str, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for index, item in enumerate(value):
        _validate_non_empty_string(item, f"{field_name}[{index}]")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)


@dataclass(frozen=True, slots=True)
class AssetRefIR2:
    """One asset an ``asset.note`` node stands in for.

    ``proposed_structural_kind`` is reported from the governing candidate and is
    a proposal, never a decision -- ``RegionCandidate`` is by contract an
    unapproved structural proposal.
    """

    digest: str
    file_name: str
    bbox: BBox
    occurrence_count: int
    proposed_structural_kind: str | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.digest, "digest")
        _validate_non_empty_string(self.file_name, "file_name")
        _validate_bbox(self.bbox)
        _validate_non_negative_int(self.occurrence_count, "occurrence_count")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be at least 1")
        if self.proposed_structural_kind is not None:
            _validate_kind(self.proposed_structural_kind)


@dataclass(frozen=True, slots=True)
class CellIR2:
    """One cell of a table.

    ``primitive_ids`` may be empty: an empty cell is a legitimate cell, and it
    owns no text. When it is empty, ``text`` must be empty too -- text without
    primitives would be text this pipeline did not read from the source.
    """

    row: int
    column: int
    text: str
    primitive_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_non_negative_int(self.row, "row")
        _validate_non_negative_int(self.column, "column")
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        _validate_unique_non_empty_ids(self.primitive_ids, "primitive_ids")
        if self.text and not self.primitive_ids:
            raise ValueError("a cell with text must own the primitives it came from")


@dataclass(frozen=True, slots=True)
class TableIR2:
    """A rectangular grid of cells.

    Rectangular on purpose: the grid comes from column boundaries that hold for
    the whole region, so a row with a different cell count would mean the
    boundaries were not the region's. Each cell's ``row``/``column`` must match
    its position, which makes «coordinates complete and non overlapping» true by
    construction instead of by a separate check.
    """

    rows: tuple[tuple[CellIR2, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not self.rows:
            raise ValueError("rows must be a non-empty tuple")

        width = len(self.rows[0])
        if width == 0:
            raise ValueError("a row must have at least one cell")

        for row_index, row in enumerate(self.rows):
            if not isinstance(row, tuple):
                raise ValueError("each row must be a tuple")
            if len(row) != width:
                raise ValueError("all rows must have the same number of cells")
            for column_index, cell in enumerate(row):
                if not isinstance(cell, CellIR2):
                    raise ValueError("rows must contain CellIR2 values")
                if cell.row != row_index or cell.column != column_index:
                    raise ValueError("cell coordinates must match their position")


# La categoria, non il kind: alla seconda volta -- callout, scheda mostro -- si
# allarga questa unione invece di aggiungere un braccio all'invariante di NodeIR2.
type StructureIR2 = TableIR2


@dataclass(frozen=True, slots=True)
class TextRunIR2:
    """A stretch of a node's text with one set of typographic traits.

    Additive by design: ``NodeIR2.text`` stays the plain string, and ``runs``
    describes how it is set. Nothing that reads ``text`` needs to change, the
    conservation check keeps comparing plain characters, and an emitter that
    ignores ``runs`` produces exactly what it produced before.

    Traits are typographic facts and not semantic roles -- ``bold`` does not mean
    "heading". They arrive from ``TextPrimitive.font_traits``, which
    ``primitive_normalizer`` fills from the span flags.

    A run per style and not a style per node, because on real pages a paragraph
    is not uniform: measured on six pages, **46% of paragraphs carry more than
    one style** (50 carry two, 13 carry three, out of 138).
    """

    text: str
    traits: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise ValueError("run text must be a non-empty string")
        _validate_unique_non_empty_ids(self.traits, "traits")


@dataclass(frozen=True, slots=True)
class NodeIR2:
    """One ordered content node.

    Carries exactly one of ``text``, ``asset`` or ``structure``: a node that
    carries nothing is a hole in the coverage, and a node that carries more than
    one would make the emitter guess.

    ``text`` may not be the empty string. A node that declares text and has none
    is indistinguishable from a full one to every check, and it is the shortcut
    that would pass the tests -- so it is refused here.

    ``page_ids`` is a tuple from day one even though v0 always fills it with one
    element: ``AGENTS.MD`` §Semantica e IR requires multi-page provenance, and
    adding it later would change the type.

    ``resolution`` reports what Resolution decided about the governing candidate;
    ``None`` means no candidate referenced the primitives. It never decides
    anything -- Resolution is the only level that may accept, reject or leave a
    candidate unresolved.
    """

    node_id: str
    order: int
    kind: str
    primitive_ids: tuple[str, ...]
    page_ids: tuple[str, ...]
    text: str | None = None
    asset: AssetRefIR2 | None = None
    structure: StructureIR2 | None = None
    runs: tuple[TextRunIR2, ...] = ()
    candidate_ids: tuple[str, ...] = ()
    resolution: str | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.node_id, "node_id")
        _validate_non_negative_int(self.order, "order")
        _validate_kind(self.kind)
        _validate_unique_non_empty_ids(self.primitive_ids, "primitive_ids")
        if not self.primitive_ids:
            raise ValueError("primitive_ids must not be empty")
        _validate_unique_non_empty_ids(self.page_ids, "page_ids")
        if not self.page_ids:
            raise ValueError("page_ids must not be empty")
        _validate_unique_non_empty_ids(self.candidate_ids, "candidate_ids")

        carried = [self.text, self.asset, self.structure]
        if sum(1 for value in carried if value is not None) != 1:
            raise ValueError("a node must carry exactly one of text, asset or structure")
        if self.text is not None:
            if not isinstance(self.text, str):
                raise ValueError("text must be a string")
            if not self.text:
                raise ValueError("text must not be empty")
        if self.asset is not None and not isinstance(self.asset, AssetRefIR2):
            raise ValueError("asset must be an AssetRefIR2")
        if self.structure is not None and not isinstance(self.structure, TableIR2):
            raise ValueError("structure must be a StructureIR2")

        if self.runs:
            if self.text is None:
                raise ValueError("runs may only describe a node that carries text")
            for run in self.runs:
                if not isinstance(run, TextRunIR2):
                    raise ValueError("runs must contain TextRunIR2 values")
            # I run DESCRIVONO il testo, non lo sostituiscono: se le due cose
            # divergessero l'emettitore avrebbe due verita' e ne sceglierebbe una
            # in silenzio. Questo e' l'unico invariante che il campo aggiunge.
            if "".join(run.text for run in self.runs) != self.text:
                raise ValueError("runs must concatenate to text")

        if self.resolution is not None and self.resolution not in _VALID_RESOLUTIONS:
            raise ValueError("resolution must be accepted, rejected, unresolved, or None")


@dataclass(frozen=True, slots=True)
class PageIR2:
    """One page. The order of ``nodes`` is reading order.

    ``page_label`` e' il numero **stampato** di questa pagina. Di norma e' un
    fatto che il PDF dichiara (``/PageLabels``, letto da ``page.get_label()``);
    dove il PDF non dichiara nulla puo' essere **dedotto leggendolo dalla
    pagina**, e allora ``page_label_deduced`` e' ``True``.

    **I due non sono lo stesso fatto**, ed e' la ragione per cui il flag esiste
    invece di lasciare il campo indistinto: uno e' cio' che l'editore ha scritto,
    l'altro cio' che abbiamo letto. Un consumatore dell'IR deve poter rifiutare
    una deduzione; chi legge il Markdown no, e infatti la resa e' la stessa.
    Dedurre e' governato da `Criterio_NumeroDedotto_v1.md`, il cui veto §5.A --
    zero disaccordi contro le etichette dichiarate di 13 manuali -- e' cio' che
    rende difendibile una resa indistinguibile.

    Dove non si dichiara ne' si deduce resta ``None``: PyMuPDF non sintetizza il
    numero fisico, e ``idx + 1`` sarebbe un'invenzione (su DIE l'etichetta a
    ``idx`` 50 e' ``39``).

    Serve a due cose. Dice **di quale pagina stampata si tratta** -- indicazione
    dell'utente: referenziare il numero serve a sapere che pagina si sta
    trattando. E chiude la terza delle tre numerazioni che questo progetto tiene
    separate e che gli sono gia' costate un giro di etichette: ``idx`` 0-based
    degli script, pagina del file 1-based, numero stampato -- l'ultimo finora
    dichiarato «non verificato e da non citare».

    Il campo esiste **indipendentemente** dal fatto che il numero venga poi
    riconosciuto e tolto dal corpo: il fatto non dipende dal riconoscimento.
    """

    page_id: str
    nodes: tuple[NodeIR2, ...] = ()
    page_label: str | None = None
    page_label_deduced: bool = False

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
        if self.page_label is not None:
            _validate_non_empty_string(self.page_label, "page_label")
        if not isinstance(self.page_label_deduced, bool):
            raise ValueError("page_label_deduced must be a bool")
        # Un flag che dichiara la provenienza di un valore assente non dichiara
        # niente, e lasciarlo passare renderebbe rappresentabile uno stato che
        # non significa nulla.
        if self.page_label_deduced and self.page_label is None:
            raise ValueError("page_label_deduced requires a page_label")
        if not isinstance(self.nodes, tuple):
            raise ValueError("nodes must be a tuple")

        seen_ids: set[str] = set()
        for node in self.nodes:
            if not isinstance(node, NodeIR2):
                raise ValueError("nodes must contain NodeIR2 values")
            if node.node_id in seen_ids:
                raise ValueError("node_id must be unique within a page")
            seen_ids.add(node.node_id)
            if self.page_id not in node.page_ids:
                raise ValueError("a node must declare the page it belongs to in page_ids")

        # L'ordine e' una permutazione di 0..n-1: senza questo un `order`
        # duplicato o con buchi renderebbe l'ordine di lettura ambiguo, che e'
        # esattamente cio' che questo contratto promette di non essere.
        orders = sorted(node.order for node in self.nodes)
        if orders != list(range(len(self.nodes))):
            raise ValueError("node order values must be a permutation of 0..n-1")


@dataclass(frozen=True, slots=True)
class IR2Provenance:
    """Where a DocumentIR 2 came from."""

    source_id: str
    generation_id: str
    producer_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.source_id, "source_id")
        _validate_non_empty_string(self.generation_id, "generation_id")
        _validate_unique_non_empty_ids(self.producer_names, "producer_names")


@dataclass(frozen=True, slots=True)
class DocumentIR2:
    """One document."""

    provenance: IR2Provenance
    schema_version: str = IR2_SCHEMA_VERSION
    pages: tuple[PageIR2, ...] = field(default=())

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.schema_version, "schema_version")
        if not isinstance(self.provenance, IR2Provenance):
            raise ValueError("provenance must be an IR2Provenance")
        if not isinstance(self.pages, tuple):
            raise ValueError("pages must be a tuple")

        seen_pages: set[str] = set()
        for page in self.pages:
            if not isinstance(page, PageIR2):
                raise ValueError("pages must contain PageIR2 values")
            if page.page_id in seen_pages:
                raise ValueError("page_id must be unique within a document")
            seen_pages.add(page.page_id)
