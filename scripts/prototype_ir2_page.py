"""Standalone diagnostic: one page through IR 2, end to end.

Wires the four modules of ``Proposta_IR2Minima_v3.md`` §7 -- model, builder,
validator, Markdown emitter -- on a real page, and checks the exit criterion of
``Criterio_UscitaIR2Minima_v2.md`` against the base.

Diagnostic prototype, not production code, and **not** a promotion of the
vertical slice: ``State.md`` states that the diagnostic emitter is not the
starting point of the IR-first renderer and that promoting it is an explicit
decision. The IR 2 modules were written new; what is reused from the slice is the
part that is not IR 2 -- capture composition, asset extraction, and above all the
**reading order**, which must be the same one the base was judged on, or the
comparison would measure two orderings instead of one node builder.

Importing from another script is the precedent the slice itself set and
documented; a third copy of the producer composition would be worse.

E-B, from the criterion: the order emitted by IR 2 must be identical to the base.
The comparison is on the sequence of non-space characters, which is order
sensitive, after removing from **both sides** what the dehyphenation regex would
remove -- the amendment declared in ``Criterio_ParagrafoDaRiga_v1.md`` §3, because
a hyphen is a non-space character and rejoining a word legitimately changes it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from compare_reading_order_with_column_bands import _tree_aware_order  # noqa: E402
from prototype_vertical_slice_page import (  # noqa: E402
    _asset_identity,
    _build_all_analyses,
    _corridor_blockers,
    _extract_image_bytes,
    _governing_outcome,
    _safe_filename_stem,
    _split_bands_at_crossings,
    _strip_asset_markers,
    _tree_rows_from_contract,
)

from ir2_builder import AssetNoteInput, TableRegionInput, build_page_ir2  # noqa: E402
from ir2_markdown import is_rendered_in_body, render_page_markdown  # noqa: E402
from ir2_model import DocumentIR2, IR2Provenance  # noqa: E402
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict  # noqa: E402
from ir2_validate import validate_page_ir2_against_primitive_page  # noqa: E402
from ir_builder import _HYPHENATED_WORD_RE  # noqa: E402
from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_page_candidates import resolve_page_candidates  # noqa: E402

_ASSET_NOTE_LINE_PREFIX = "> **["


def _fail(message: str, code: int) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(code)


def _normalised_sequence(text: str) -> str:
    """Non-space characters, after the dehyphenation amendment, order preserved."""

    return "".join(_HYPHENATED_WORD_RE.sub("", text).split())


def _anchor_index(primitive: object, ordered: list) -> int:
    """Posizione nell'ordine di lettura davanti a cui va la nota.

    Regola ereditata dal consumer che ha prodotto la base: la prima primitiva
    testuale che sta piu' in basso dell'occorrenza. **Limite dichiarato**: e'
    un confronto su y, quindi su una pagina a due colonne una nota della colonna
    destra puo' ancorarsi a testo della sinistra. Il difetto sta qui, nel
    chiamante che possiede l'ordinamento, e non piu' nel costruttore, che ora
    riceve un indice e non fa geometria. Correggerlo richiede sapere in quale
    colonna cade l'immagine, cioe' combinare `column_band` con i producer
    visuali: e' lavoro di ordinamento, non di IR 2, e non e' in questo perimetro.
    """

    y0 = primitive.bbox[1]  # type: ignore[attr-defined]
    for index, candidate in enumerate(ordered):
        if candidate.bbox[1] > y0:
            return index
    return len(ordered)


def _strip_ir2_notes(markdown: str) -> str:
    return "\n".join(
        line for line in markdown.splitlines() if not line.startswith(_ASSET_NOTE_LINE_PREFIX)
    )


def run(
    pdf_path: Path,
    page_number: int,
    output_dir: Path,
    base_path: Path | None,
    interrupt_corridor: str = "",
    enable_tables: bool = False,
) -> None:
    page_index = page_number - 1
    generation_id = f"generation:ir2:{page_number:04d}"
    page_id = f"page:{page_number:04d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as document, pdfplumber.open(pdf_path) as plumber_pdf:
        page = document[page_index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            _fail("page guard: rotation or mediabox != cropbox", 3)

        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=page_id,
            capture_id=f"ir2:pymupdf:{page_id}",
        )
        primitive_page = normalize_backend_page_capture(capture)

        analyses = _build_all_analyses(
            primitive_page,
            plumber_page=plumber_pdf.pages[page_index],
            generation_id=generation_id,
        )
        bound = bind_co_referenced_page_analyses(
            primitive_page,
            co_referenced_page_analyses=build_co_referenced_page_analyses(analyses),
        )
        resolved = resolve_page_candidates(bound)
        outcome_by_candidate = {
            (o.candidate_reference.producer_name, o.candidate_reference.candidate_id): o.outcome
            for o in resolved.outcomes
        }

        # --- L'ORDINE DI LETTURA, preso dal percorso che ha prodotto la base ---
        band_analysis, band_measures = build_column_band_page_analysis_with_measurements(
            primitive_page, generation_id=generation_id
        )
        tree = _tree_rows_from_contract(band_analysis.candidates, band_measures)
        if interrupt_corridor:
            # Diagnostico, spento di default. Milestone 37 misuro' che la meta'
            # filetti regge e la meta' embedded_visual annienta (DB p.50 da 83
            # primitive in banda a 0), e lascio' il flag spento.
            blockers = _corridor_blockers(
                primitive_page=primitive_page,
                analyses=analyses,
                sources=interrupt_corridor,
            )
            cut = _split_bands_at_crossings(tree, blockers)
            print(
                f"corridor_interrupt: blockers={len(blockers)} bands={len(tree)}->{len(cut)}",
                file=sys.stderr,
            )
            tree = cut
        ordered, _inside = _tree_aware_order(list(primitive_page.text_primitives), tree)
        ordered_primitives = [primitive for primitive, _group in ordered]

        # --- Le regioni tabella ---
        #
        # Niente e' calcolato qui: la regione viene da `table_candidate` (producer
        # gia' wired) e i confini di colonna da `ColumnBandMeasurements`. State.md
        # assegna quei gutter al consumer di tabelle in queste parole: «column_band
        # non deve leggere le tabelle, deve dire dove sono i confini di colonna, e
        # se una regione e' una tabella la gestisce il consumer di tabelle aiutato
        # da questi gutter». Milestone 37 ha tolto la restrizione al primo livello
        # proprio per renderli disponibili.
        gutters = tuple(
            interval for measure in band_measures for interval in measure.gutter_x_intervals
        )
        table_regions: list[TableRegionInput] = []
        for analysis in analyses:
            if analysis.provenance.producer_name != "table_candidate":
                continue
            for candidate in analysis.candidates:
                outcome = outcome_by_candidate.get(
                    (analysis.provenance.producer_name, candidate.candidate_id)
                )
                table_regions.append(
                    TableRegionInput(
                        bbox=candidate.bbox,
                        gutter_x_intervals=gutters,
                        candidate_ids=(candidate.candidate_id,),
                        resolution=outcome,
                    )
                )

        # --- Le note d'asset ---
        raw_image_info = document[page_index].get_image_info(hashes=True, xrefs=True)
        assets: dict[str, dict[str, object]] = {}
        counts: Counter[str] = Counter(
            _asset_identity(primitive)[0] for primitive in primitive_page.image_primitives
        )
        notes: list[AssetNoteInput] = []
        review_rows: list[tuple[str, str]] = []
        for primitive in sorted(primitive_page.image_primitives, key=lambda p: p.primitive_id):
            identity, _missing = _asset_identity(primitive)
            if identity not in assets:
                extracted = _extract_image_bytes(
                    fitz_document=document,
                    page=page,
                    primitive=primitive,
                    raw_image_info=raw_image_info,
                )
                if extracted is None:
                    assets[identity] = {"file_name": ""}
                else:
                    image_bytes, extension, _method = extracted
                    file_name = f"{_safe_filename_stem(identity)}.{extension}"
                    (output_dir / file_name).write_bytes(image_bytes)
                    assets[identity] = {"file_name": file_name}

            file_name = str(assets[identity]["file_name"])
            if not file_name:
                # Nessun raster: l'occorrenza sta interamente fuori pagina. Non
                # puo' diventare un nodo -- AssetRefIR2 esige un file_name non
                # vuoto -- ma non puo' nemmeno sparire: AGENTS.MD, Coverage e
                # ownership, «Nessuna esclusione puo' essere silenziosa». Va nel
                # canale review, come fa gia' la fetta verticale.
                review_rows.append(
                    (primitive.primitive_id, "nessun raster: occorrenza interamente fuori pagina")
                )
                continue

            candidate, outcome, _producer = _governing_outcome(
                primitive.primitive_id,
                analyses=analyses,
                outcome_by_candidate=outcome_by_candidate,
            )
            notes.append(
                AssetNoteInput(
                    primitive_id=primitive.primitive_id,
                    digest=identity,
                    file_name=file_name,
                    bbox=primitive.bbox,
                    occurrence_count=counts[identity],
                    anchor_index=_anchor_index(primitive, ordered_primitives),
                    proposed_structural_kind=(
                        None if candidate is None else candidate.proposed_structural_kind
                    ),
                    candidate_ids=() if candidate is None else (candidate.candidate_id,),
                    resolution=None if outcome == "no_candidate" else outcome,
                )
            )

        # --- I quattro moduli ---
        ir2_page = build_page_ir2(
            page_id=page_id,
            ordered_text_primitives=ordered_primitives,
            asset_notes=notes,
            table_regions=table_regions if enable_tables else (),
        )
        validate_page_ir2_against_primitive_page(ir2_page, primitive_page)

        ir2_document = DocumentIR2(
            provenance=IR2Provenance(
                source_id="diagnostic-source",
                generation_id=generation_id,
                producer_names=tuple(
                    sorted({a.provenance.producer_name for a in analyses})
                ),
            ),
            pages=(ir2_page,),
        )

        payload = document_ir2_to_dict(ir2_document)
        if document_ir2_from_dict(json.loads(json.dumps(payload))) != ir2_document:
            _fail("serialization round trip is not lossless", 4)
        (output_dir / "document_ir2.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        markdown = render_page_markdown(ir2_page)
        (output_dir / "page_ir2.md").write_text(markdown, encoding="utf-8")

        # --- Canale review: cio' che NON entra nel corpo, e perche' ---
        #
        # E' il controllo che l'utente ha chiesto di tenere: l'arredo andra'
        # affrontato, oppure andra' verificato che altri producer lo risolvano
        # gia'. Questo file e' l'elenco da cui si guardera', raggruppato per
        # genere strutturale proposto, perche' quella domanda sia misurabile
        # invece che ricordata.
        not_rendered = [
            node
            for node in ir2_page.nodes
            if not is_rendered_in_body(node, render_unresolved=False)
        ]
        by_kind: Counter[str] = Counter(
            (node.asset.proposed_structural_kind or "(nessun candidato)")
            for node in not_rendered
            if node.asset is not None
        )

        review_lines = [f"# Review IR 2 — {page_id}", ""]
        review_lines.append(
            f"Nodi non resi nel corpo: **{len(not_rendered)}**. "
            f"Occorrenze senza raster: **{len(review_rows)}**."
        )
        review_lines.append("")
        if by_kind:
            review_lines.append("## Per genere strutturale proposto")
            review_lines.append("")
            for kind, count in sorted(by_kind.items(), key=lambda item: (-item[1], item[0])):
                review_lines.append(f"- {kind}: {count}")
            review_lines.append("")
        if not_rendered:
            review_lines.append("## Nodi non resi")
            review_lines.append("")
            for node in not_rendered:
                asset = node.asset
                size = "" if asset is None else (
                    f" {asset.bbox[2] - asset.bbox[0]:.0f}×{asset.bbox[3] - asset.bbox[1]:.0f} pt"
                )
                review_lines.append(
                    f"- `{node.node_id}` resolution={node.resolution}"
                    f" kind={asset.proposed_structural_kind if asset else None}{size}"
                )
            review_lines.append("")
        for primitive_id, reason in review_rows:
            review_lines.append(f"## occurrence {primitive_id}")
            review_lines.append(f"- {reason}")
            review_lines.append("")
        (output_dir / "review_ir2.md").write_text(
            "\n".join(review_lines) + "\n", encoding="utf-8"
        )

        covered = {
            primitive_id for node in ir2_page.nodes for primitive_id in node.primitive_ids
        }
        recorded = covered | {primitive_id for primitive_id, _reason in review_rows}
        missing = [
            primitive.primitive_id
            for primitive in primitive_page.image_primitives
            if primitive.primitive_id not in recorded
        ]
        if missing:
            _fail(f"esclusione silenziosa: {len(missing)} occorrenze immagine non registrate", 6)

        print(
            f"ir2: nodes={len(ir2_page.nodes)} "
            f"paragraphs={sum(1 for n in ir2_page.nodes if n.kind == 'text.paragraph')} "
            f"asset_notes={sum(1 for n in ir2_page.nodes if n.kind == 'asset.note')} "
            f"note_in_body={sum(1 for n in ir2_page.nodes if n.kind == 'asset.note' and n.resolution == 'accepted')} "
            f"tables={sum(1 for n in ir2_page.nodes if n.structure is not None)}/{len(table_regions)} "
            f"text_primitives={len(primitive_page.text_primitives)}",
            file=sys.stderr,
        )

        # --- E-B, contro la base ---
        if base_path is not None:
            if not base_path.is_file():
                _fail(f"base non trovata: {base_path}", 3)
            base_sequence = _normalised_sequence(
                _strip_asset_markers(base_path.read_text(encoding="utf-8"))
            )
            new_sequence = _normalised_sequence(_strip_ir2_notes(markdown))
            if base_sequence == new_sequence:
                print(f"E-B: ordine IDENTICO alla base ({len(base_sequence)} caratteri)",
                      file=sys.stderr)
            else:
                print(
                    f"E-B: ordine DIVERSO -- base={len(base_sequence)} nuovo={len(new_sequence)}",
                    file=sys.stderr,
                )
                for index, (left, right) in enumerate(zip(base_sequence, new_sequence, strict=False)):
                    if left != right:
                        print(
                            f"  prima divergenza a {index}: "
                            f"base {base_sequence[index:index + 60]!r} "
                            f"nuovo {new_sequence[index:index + 60]!r}",
                            file=sys.stderr,
                        )
                        break
                _fail("E-B: l'ordine emesso non coincide con la base", 5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--page-number", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--tables",
        action="store_true",
        help=(
            "costruisce i nodi tabella. SPENTO di default: il criterio di "
            "accettazione e' caduto (Esito_TabellaInIR2_v1.md)."
        ),
    )
    parser.add_argument(
        "--interrupt-corridor",
        choices=("both", "drawings", "visuals"),
        default="",
        help="diagnostico: spezza le bande dove un filetto o un embedded_visual "
             "attraversa il corridoio. Spento di default (Milestone 37).",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="page_bands.md della base; se dato, verifica E-B.",
    )
    args = parser.parse_args()
    run(
        args.pdf,
        args.page_number,
        args.output_dir,
        args.base,
        interrupt_corridor=args.interrupt_corridor,
        enable_tables=args.tables,
    )


if __name__ == "__main__":
    main()
