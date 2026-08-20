"""Pure validation between a DocumentIR 2 page and a normalized primitive page.

The repo puts a validator next to each of the neighbouring contracts
(``page_analysis_validate``, ``ir_validate``); this is the one for IR 2, and it
is the module that makes the coverage claim **checkable instead of asserted**.

``Proposta_IR2Minima_v3.md`` §7 states the coverage is satisfied by construction.
By construction is not by verification: the two invariants below are what turn
that sentence into something a run can fail.

Both come straight from ``AGENTS.MD`` §Coverage e ownership:

- «La coverage è obbligatoria per le primitive che possono trasportare
  contenuto» -> every ``TextPrimitive`` of the page must appear in some node,
  including the ones whose text is empty. An empty span carries no characters but
  it is still a primitive, and leaving it out would be a silent exclusion.
- «Una primitiva testuale non può appartenere a più nodi finali salvo
  duplicazione esplicita» -> no primitive id twice. Today the non-duplication is
  measured on four pages (``State.md``) and not guaranteed by anything; here it
  becomes a check.

Image primitives are deliberately **not** required to be covered: an occurrence
wholly outside the page produces no raster and therefore no node (see the
off-page fix), and page furniture is meant to leave the reading flow entirely.
Requiring their coverage would forbid both by accident.
"""

from __future__ import annotations

from ir2_model import PageIR2
from primitive_model import NormalizedPrimitivePage


def validate_page_ir2_against_primitive_page(
    page: PageIR2,
    primitive_page: NormalizedPrimitivePage,
) -> None:
    """Validate one IR 2 page against the primitive page it was built from."""

    if not isinstance(page, PageIR2):
        raise ValueError("page must be a PageIR2")
    if not isinstance(primitive_page, NormalizedPrimitivePage):
        raise ValueError("primitive_page must be a NormalizedPrimitivePage")

    if page.page_id != primitive_page.page_id:
        raise ValueError("page_id must match primitive_page page_id")

    known_ids = {
        primitive.primitive_id
        for primitive in (
            *primitive_page.text_primitives,
            *primitive_page.image_primitives,
            *primitive_page.drawing_primitives,
        )
    }

    seen: set[str] = set()
    for node in page.nodes:
        # Un nodo strutturato possiede le primitive delle sue celle, e l'unione
        # delle celle deve coincidere con cio' che il nodo dichiara: senza questo
        # la griglia sarebbe dentro il contratto e non verificata da niente, che
        # e' il difetto che questo modulo esiste per non avere.
        if node.structure is not None:
            from_cells = [
                primitive_id
                for row in node.structure.rows
                for cell in row
                for primitive_id in cell.primitive_ids
            ]
            if len(from_cells) != len(set(from_cells)):
                raise ValueError("a primitive belongs to more than one cell of the same table")
            if set(from_cells) != set(node.primitive_ids):
                raise ValueError("the union of the cells must equal the node primitives")

        for primitive_id in node.primitive_ids:
            if primitive_id not in known_ids:
                raise ValueError("node references a primitive absent from the primitive page")
            if primitive_id in seen:
                raise ValueError(
                    "a primitive belongs to more than one node without explicit duplication"
                )
            seen.add(primitive_id)

    text_ids = {primitive.primitive_id for primitive in primitive_page.text_primitives}
    uncovered = text_ids - seen
    if uncovered:
        raise ValueError(f"{len(uncovered)} text primitives are covered by no node")
