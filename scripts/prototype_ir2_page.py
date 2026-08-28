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
from dataclasses import dataclass
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

from document_furniture_policy import (  # noqa: E402
    deduced_number_slots,
    furniture_node_ids,
    furniture_slots,
    vertical_primitive_ids,
)
from document_heading_measurements import (  # noqa: E402
    measure_font_sizes,
    sized_lines,
)
from document_heading_policy import (  # noqa: E402
    heading_levels,
    prose_sizes,
    sizes_that_carry_headings,
)
from document_line_start_measurements import (  # noqa: E402
    count_block_signatures,
    measure_document_line_starts,
)
from document_list_policy import list_markers, value_scale_signatures  # noqa: E402
from document_text_recurrence_measurements import (  # noqa: E402
    measure_document_text_recurrence,
)
from ir2_builder import (  # noqa: E402
    AssetNoteInput,
    TableRegionInput,
    body_font,
    build_page_ir2,
)
from ir2_markdown import is_rendered_in_body, render_page_markdown  # noqa: E402
from ir2_model import DocumentIR2, IR2Provenance, NodeIR2  # noqa: E402
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


def _normalised_sequence(text: str, list_markers: frozenset[str] = frozenset()) -> str:
    """Non-space characters, after the dehyphenation amendment, order preserved.

    `list_markers` porta il **secondo** emendamento al confronto E-B,
    `Criterio_Elenchi_v1.md` §5.E: i marcatori dichiarati per quel documento
    escono da **entrambi i lati**. Senza, il confronto fallirebbe per
    costruzione, perche' la resa a elenco sostituisce il marcatore con `- `.

    E' la stessa forma dell'emendamento gia' a verbale per la deidratazione:
    un trattino e' un carattere non-spazio e riunire una parola lo cambia
    legittimamente. Togliere da entrambi i lati e' cio' che tiene onesto il
    confronto -- se lo si togliesse da uno solo, il confronto misurerebbe
    l'emendamento invece dell'ordine.
    """

    text = _HYPHENATED_WORD_RE.sub("", text)
    if list_markers:
        text = "".join(character for character in text if character not in list_markers)
    return "".join(text.split())


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


@dataclass(frozen=True, slots=True)
class DocumentScan:
    """Cio' che una scansione del documento produce, tutto insieme.

    Sono quattro fatti document-level -- arredo, numero dedotto, marcatori
    d'elenco, scale di valori -- piu' le dimensioni di prosa e i livelli di
    titolo. Stanno in un tipo e non in una tupla perche' sono sei e crescono: una
    tupla di sei elementi si sbaglia a leggere, e questo modulo si legge molto.

    **Una scansione sola.** Ricatturare le pagine una volta per meccanismo
    moltiplicherebbe il costo del giro per niente: sono tutti fatti sulle stesse
    pagine.
    """

    furniture: object
    deduced_labels: dict[int, str]
    list_markers: frozenset[str]
    scale_signatures: frozenset[tuple[str, ...]]
    prose_sizes: frozenset[float]
    heading_levels: dict[float, int]


def document_furniture_slots(document: fitz.Document, *, sample: int) -> DocumentScan:
    """Gli slot d'arredo del documento e i numeri dedotti, ricatturandone le pagine.

    `sample` limita quante pagine si guardano, centrate sul documento: un
    manuale da 400 pagine ricatturato per intero costa minuti, e la ricorrenza
    non ha bisogno di tutte per essere stabile. E' un parametro di costo e non
    una soglia della regola -- ma va dichiarato, perche' un campione contiguo
    corto sovrastima le intestazioni di capitolo, che su una finestra stretta
    sono su tutte le pagine e su un manuale intero no.
    """

    first = max(0, len(document) // 2 - sample // 2)
    pages: list = []
    indices: list[int] = []
    for index in range(first, min(len(document), first + sample)):
        page = document[index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            continue
        indices.append(index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{index:04d}",
            capture_id=f"furniture:{index:04d}",
        )
        pages.append(
            (normalize_backend_page_capture(capture), (page.get_label() or "").strip())
        )
    captured = [primitive for primitive, _ in pages]
    measured = measure_document_text_recurrence(captured)
    slots = furniture_slots(pages, measured)
    # I marcatori d'elenco escono dalla STESSA scansione: sono un fatto
    # document-level come l'arredo, e ricatturare le pagine due volte
    # raddoppierebbe il costo del giro per niente.
    # Il font del corpo apre la seconda via dei marcatori: su Fab il pallino e'
    # la lettera `w` in Wingdings. `Criterio_MarcatoreDaFont_v1.md`.
    body = body_font([p for page in captured for p in page.text_primitives])
    markers = list_markers(measure_document_line_starts(captured, body))
    # Le firme di blocco escono dalla stessa scansione: dire quali sequenze
    # di glifi siano una scala di valori richiede di aver visto piu' blocchi,
    # ed e' un fatto document-level come l'arredo e i marcatori.
    scales = value_scale_signatures(count_block_signatures(captured, markers))

    # I numeri **dedotti** per indice di pagina, dove il documento non dichiara
    # niente. Servono alla provenienza, non alla rimozione: la rimozione la fa
    # gia' `slots.from_sequence`. Sono due usi separati dello stesso fatto e il
    # criterio li tiene separati perche' possono fallire separati.
    deduced: dict[int, str] = {}
    if not any(label for _, label in pages):
        found = deduced_number_slots([primitive for primitive, _ in pages])
        deduced = {
            indices[position]: value
            for position, value in found.by_page_position.items()
            if position < len(indices)
        }
    # I titoli vengono dalle stesse pagine: quali dimensioni siano prosa lo si
    # puo' dire solo avendone viste tante, `Criterio_Titoli_v2.md` §1.
    sizes = measure_font_sizes(captured)
    prose = prose_sizes(sizes)
    # Due passate: prima si vede quali dimensioni intestano davvero qualcosa, poi
    # si assegnano i ranghi solo a quelle. `Criterio_Titoli_v3.md`.
    carried = sizes_that_carry_headings([sized_lines(page) for page in captured], sizes, prose)
    return DocumentScan(
        furniture=slots,
        deduced_labels=deduced,
        list_markers=markers,
        scale_signatures=scales,
        prose_sizes=prose,
        heading_levels=heading_levels(sizes, prose, carried),
    )


def review_lines_for(
    page_id: str,
    not_rendered: list[NodeIR2],
    by_kind: Counter[str],
    review_rows: list[tuple[str, str]],
) -> list[str]:
    """Il contenuto di `review_ir2.md`, come funzione perche' sia verificabile.

    Era codice in linea dentro `run`. Cio' che scrive e' il materiale su cui
    `Criterio_ArredoRicorrente_v3.md` §4 chiede un giudizio: se non si puo'
    esercitare senza produrre una pagina intera, quel giudizio non e'
    materialmente eseguibile.
    """

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
            if asset is not None:
                size = (
                    f" {asset.bbox[2] - asset.bbox[0]:.0f}"
                    f"×{asset.bbox[3] - asset.bbox[1]:.0f} pt"
                )
                review_lines.append(
                    f"- `{node.node_id}` resolution={node.resolution}"
                    f" kind={asset.proposed_structural_kind}{size}"
                )
                continue
            # Il TESTO va riportato per intero, non descritto: chi giudica
            # deve poter dire se una voce tolta e' arredo o contenuto, e da
            # `node_id` e `kind` non lo puo' dire. Niente troncamento: un
            # paragrafo tolto per errore si riconosce da com'e' fatto, e
            # tagliarlo a N caratteri nasconderebbe proprio il caso lungo.
            review_lines.append(
                f"- `{node.node_id}` kind={node.kind}"
                f" primitive={len(node.primitive_ids)}"
            )
            for line in (node.text or "").splitlines() or [""]:
                review_lines.append(f"  > {line}")
        review_lines.append("")
    for primitive_id, reason in review_rows:
        review_lines.append(f"## occurrence {primitive_id}")
        review_lines.append(f"- {reason}")
        review_lines.append("")
    return review_lines


def run(
    pdf_path: Path,
    page_number: int,
    output_dir: Path,
    base_path: Path | None,
    interrupt_corridor: str = "",
    enable_tables: bool = False,
    remove_furniture: bool = False,
    render_lists: bool = False,
    furniture_sample: int = 60,
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
        #
        # L'arredo si calcola **prima** di costruire la pagina, e non e' un
        # riordino di comodo: dove il documento non dichiara le etichette il
        # numero stampato arriva da li', e il contratto vuole saperlo alla
        # costruzione. La rimozione invece potrebbe restare dopo -- sono due usi
        # separati dello stesso fatto, come dice `Criterio_NumeroDedotto_v1.md`.
        # La scansione e' una sola e serve a due cose: arredo ed elenchi sono
        # entrambi fatti document-level, e ricatturare le pagine due volte
        # raddoppierebbe il costo per niente.
        furniture_slots_found = None
        deduced_labels: dict[int, str] = {}
        markers: frozenset[str] = frozenset()
        scales: frozenset[tuple[str, ...]] = frozenset()
        prose: frozenset[float] = frozenset()
        levels: dict[float, int] = {}
        if remove_furniture or render_lists:
            scan = document_furniture_slots(document, sample=furniture_sample)
            deduced_labels = scan.deduced_labels
            prose = scan.prose_sizes
            levels = scan.heading_levels
            if remove_furniture:
                furniture_slots_found = scan.furniture
            else:
                deduced_labels = {}
            if render_lists:
                markers = scan.list_markers
                scales = scan.scale_signatures
                print(
                    "elenchi: marcatori "
                    + (", ".join(f"{m!r} U+{ord(m):04X}" for m in sorted(markers)) or "nessuno")
                    + " — scale di valori: "
                    + (", ".join(repr("".join(f)) for f in sorted(scales)) or "nessuna"),
                    file=sys.stderr,
                )
                print(
                    f"titoli: prosa a {sorted(prose)}, livelli "
                    + (", ".join(f"{s}→h{n}" for s, n in sorted(levels.items(), reverse=True))
                       or "nessuno"),
                    file=sys.stderr,
                )

        page_label = (page.get_label() or "").strip() or None
        page_label_deduced = False
        if page_label is None and page_index in deduced_labels:
            page_label = deduced_labels[page_index]
            page_label_deduced = True

        ir2_page = build_page_ir2(
            page_id=page_id,
            ordered_text_primitives=ordered_primitives,
            asset_notes=notes,
            table_regions=table_regions if enable_tables else (),
            page_label=page_label,
            page_label_deduced=page_label_deduced,
            list_markers=markers,
            scale_signatures=scales,
            prose_sizes=prose,
            heading_levels=levels,
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

        # La politica dell'arredo e' DOCUMENT-LEVEL: per sapere se uno slot di
        # questa pagina e' arredo bisogna aver visto le altre. Non c'e' modo di
        # evitarlo -- e' la ragione stessa per cui il segnale funziona -- e non
        # c'e' deserializzatore di NormalizedPrimitivePage, quindi le pagine si
        # ricatturano. Costa, ed e' spento di default: acceso solo dal giro che
        # esegue `Criterio_ArredoRicorrente_v3.md`.
        excluded_node_ids: frozenset[str] = frozenset()
        if furniture_slots_found is not None:
            slots = furniture_slots_found
            excluded_node_ids = furniture_node_ids(
                primitive_page,
                [(node.node_id, node.primitive_ids) for node in ir2_page.nodes],
                slots.all_slots,
                # Per pagina, non dal documento: gli id di primitiva non sono
                # unici fra pagine, e la verticalita' e' un fatto della pagina.
                vertical_primitive_ids(primitive_page),
            )
            print(
                f"arredo: {len(slots.from_label)} slot da etichetta, "
                f"{len(slots.from_recurrence)} da ricorrenza, "
                f"{len(slots.from_sequence)} da sequenza dedotta, "
                f"{len(vertical_primitive_ids(primitive_page))} primitive verticali, "
                f"{len(excluded_node_ids)} nodi fuori dal corpo"
                + (f" — numero dedotto: {page_label}" if page_label_deduced else ""),
                file=sys.stderr,
            )

        markdown = render_page_markdown(
            ir2_page, excluded_node_ids=excluded_node_ids, list_markers=markers
        )
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
            if not is_rendered_in_body(
                node, render_unresolved=False, excluded_node_ids=excluded_node_ids
            )
        ]
        # Un nodo di TESTO non ha `asset`, quindi si conta per il proprio `kind`.
        # Senza questo un paragrafo tolto dal corpo non comparirebbe da nessuna
        # parte nel riepilogo, e il file esiste per essere l'elenco da cui si
        # guarda.
        by_kind: Counter[str] = Counter(
            (node.asset.proposed_structural_kind or "(nessun candidato)")
            if node.asset is not None
            else node.kind
            for node in not_rendered
        )

        review_lines = review_lines_for(page_id, not_rendered, by_kind, review_rows)
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
                _strip_asset_markers(base_path.read_text(encoding="utf-8")), markers
            )
            new_sequence = _normalised_sequence(_strip_ir2_notes(markdown), markers)
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
        "--arredo",
        action="store_true",
        help=(
            "toglie dal corpo l'arredo ricorrente e lo manda in review "
            "(Criterio_ArredoRicorrente_v3.md). SPENTO di default: richiede di "
            "ricatturare altre pagine del manuale, perche' il segnale e' "
            "document-level e NormalizedPrimitivePage non ha deserializzatore."
        ),
    )
    parser.add_argument(
        "--elenchi",
        action="store_true",
        help=(
            "riconosce gli elenchi col marcatore desunto dal manuale "
            "(Criterio_Elenchi_v1.md). Spento di default come --arredo e per la "
            "stessa ragione: il segnale e' document-level e le pagine si "
            "ricatturano. La scansione e' condivisa con --arredo."
        ),
    )
    parser.add_argument(
        "--arredo-pagine",
        type=int,
        default=60,
        help="quante pagine ricatturare per la misura di ricorrenza (default 60)",
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
        remove_furniture=args.arredo,
        render_lists=args.elenchi,
        furniture_sample=args.arredo_pagine,
        enable_tables=args.tables,
    )


if __name__ == "__main__":
    main()
