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
KIND_ASSET_NOTE = "asset.note"
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
class NodeIR2:
    """One ordered content node.

    Carries either ``text`` or ``asset``, never both and never neither: a node
    that carries nothing is a hole in the coverage, and a node that carries both
    would make the emitter guess.

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

        if (self.text is None) == (self.asset is None):
            raise ValueError("a node must carry exactly one of text or asset")
        if self.text is not None and not isinstance(self.text, str):
            raise ValueError("text must be a string")
        if self.asset is not None and not isinstance(self.asset, AssetRefIR2):
            raise ValueError("asset must be an AssetRefIR2")

        if self.resolution is not None and self.resolution not in _VALID_RESOLUTIONS:
            raise ValueError("resolution must be accepted, rejected, unresolved, or None")


@dataclass(frozen=True, slots=True)
class PageIR2:
    """One page. The order of ``nodes`` is reading order."""

    page_id: str
    nodes: tuple[NodeIR2, ...] = ()

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
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
