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
    running_head_primitive_ids,
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
from ir2_markdown import (  # noqa: E402
    KIND_ASSET_NOTE,
    RENDER_UNRESOLVED_ASSET_NOTES,
    is_rendered_in_body,
    render_node,
    render_page_markdown,
)
from ir2_model import DocumentIR2, IR2Provenance, NodeIR2, PageIR2  # noqa: E402
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


def _fail(message: str, code: int) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(code)


def _normalised_sequence(text: str) -> str:
    """Non-space characters, after the dehyphenation amendment, order preserved.

    **Non toglie piu' niente per carattere**, ed e' il ritiro del secondo
    emendamento a E-B (`Criterio_Elenchi_v1.md` §5.E, sostituito da
    `Criterio_ConfrontoEB_v3.md`). Quell'emendamento cancellava i marcatori
    dichiarati **da entrambi i lati**, e faceva due danni opposti:

    - **cancellava troppo.** Il carattere spariva *ovunque comparisse nel
      documento*, non solo in testa alle voci. Ammessa `O` come marcatore su Fab,
      ogni `O` usciva da tutt'e due i lati e la resa `- livia` per `Olivia`
      passava il confronto senza che niente se ne accorgesse. Misurato, i
      caratteri ciechi sono lo 0,1% su Fab, lo 0,6% su DrM, lo 0,5% su DrW coi
      marcatori spediti -- poco, ma la garanzia reggeva per l'alfabeto;
    - **cancellava troppo poco.** Toglieva il marcatore ma non il `- ` che la
      resa mette al suo posto, e il trattino e' un carattere non-spazio che
      sopravvive. Il confronto restava asimmetrico e falliva per costruzione su
      qualunque pagina con elenchi: misurato su FWK idx 119, base
      `Muriecancelli…` contro nuovo `-Muriecancelli…`.

    La sostituzione la fa `_with_source_markers`, che **rimette** il marcatore
    dichiarato al posto del `- `. Cosi' non si cancella niente da nessuna parte, e
    una lettera persa si vede.

    Resta l'emendamento della deidratazione, che e' d'altra natura: un trattino
    e' un carattere non-spazio e riunire una parola lo cambia legittimamente.
    """

    return "".join(_HYPHENATED_WORD_RE.sub("", text).split())


def _emitted_content(page: PageIR2) -> tuple[str, list[tuple[str, str]]]:
    """Il contenuto emesso, **senza la sintassi che l'emettitore aggiunge**.

    Torna la sequenza da confrontare con la base, e l'elenco dei nodi in cui la
    resa ha perso caratteri.

    **Perche' una regola sola invece di un emendamento per sintassi.** E-B e'
    stato rotto da tre meccanismi in fila: gli elenchi (`- ` al posto del
    marcatore), i titoli (`#`) e i run (`*`). Toglierli uno per uno con tre
    normalizzazioni sarebbe stato tre volte lo stesso errore -- la quarta
    sintassi che nasce romperebbe di nuovo il confronto in silenzio.

    Qui la sintassi non si riconosce: si **allinea**. Ogni nodo porta il suo
    testo in chiaro, `node.text`, e la sua resa e' quel testo piu' i delimitatori
    che l'emettitore ci ha messo intorno. Confrontando i due si tiene il testo e
    si perde la sintassi, **qualunque essa sia**, senza sapere quale.

    **E l'allineamento e' anche il controllo che mancava.** Se un carattere del
    nodo non compare nella sua resa, la resa lo ha perso: e' il difetto di Fab --
    `- livia` per `Olivia` -- e finora nessuno lo guardava, perche' E-B
    cancellava i marcatori da entrambi i lati e il confronto passava.

    Il `- ` fa eccezione e va **restituito** prima di allineare: la resa lo mette
    al posto del marcatore, che nel testo del nodo c'e' ancora. Un nodo senza
    marcatore -- dove la testa e' una lettera e non un glifo -- perde solo il
    `- `.

    Un nodo **senza testo** -- tabelle, note d'asset -- non ha con che allinearsi
    e passa com'e': stanno gia' fuori dal giudizio per il §3 del criterio
    d'uscita.

    **E l'arredo rientra**, `Criterio_ConfrontoEB_v4.md`. Toglierlo dal corpo e'
    una decisione di **resa** -- non si scrive nell'IR, e il nodo resta -- quindi
    sta accanto ai `#` e agli `*`, non accanto a un contenuto perso. E-B chiede
    se IR 2 emette le stesse cose nello stesso ordine, e quella domanda si fa
    sull'ordine intero: la base non deduplica e non toglie testatine, e
    confrontarci una resa gia' potata misurerebbe la politica d'arredo invece
    dell'ordine.

    **Il prezzo, dichiarato**: cosi' E-B non puo' piu' vedere un arredo che
    toglie troppo. Non era il suo mestiere -- lo guarda il canale review, e i
    giudizi ciechi che hanno gia' fatto cadere due clausole -- ma va scritto.
    """

    parts: list[str] = []
    losses: list[tuple[str, str]] = []
    for node in sorted(page.nodes, key=lambda n: n.order):
        if not is_rendered_in_body(node, render_unresolved=RENDER_UNRESOLVED_ASSET_NOTES):
            continue
        if node.kind == KIND_ASSET_NOTE:
            # Le note d'asset non stanno nella base: sono la sostituzione che
            # questo progetto introduce, e il §3 del criterio d'uscita le
            # dichiara rumore. Prima le toglieva `_strip_ir2_notes` dalla
            # stringa gia' resa; qui non entrano proprio.
            continue
        fragment = render_node(node)
        if not fragment:
            continue
        if fragment.startswith("- "):
            fragment = (node.marker or "") + fragment[2:]
        if node.text is None:
            parts.append(fragment)
            continue
        lost = _lost_in_rendering(fragment, node.text)
        if lost:
            losses.append((node.node_id, lost))
        parts.append(node.text)
    return ("\n".join(parts), losses)


def _lost_in_rendering(fragment: str, plain: str) -> str:
    """I caratteri del nodo che la sua resa non ha emesso, in ordine.

    Si guardano i soli caratteri non-spazio: la resa unisce le righe e gli spazi
    non sono contenuto. `plain` dev'essere una **sottosequenza** del frammento;
    cio' che non lo e' e' contenuto distrutto dall'emettitore.
    """

    emitted = [character for character in fragment if not character.isspace()]
    position = 0
    lost: list[str] = []
    for character in plain:
        if character.isspace():
            continue
        # Cercare **senza consumare** quando non si trova: una prima versione
        # faceva avanzare il cursore mentre cercava, e al primo carattere
        # mancante lo portava in fondo -- da li' in poi risultava perso tutto.
        # Su `Olivia` reso `livia` diceva che erano perse sei lettere invece di
        # una. Il test e' nato fallito.
        found = next(
            (index for index in range(position, len(emitted)) if emitted[index] == character),
            None,
        )
        if found is None:
            lost.append(character)
        else:
            position = found + 1
    return "".join(lost)


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


def document_scan(
    document: fitz.Document, page_index: int, *, neighbourhood: int
) -> DocumentScan:
    """I sei fatti, ognuno misurato **nel suo ambito**. `Criterio_AmbitoDeiFatti_v1.md`.

    **Il difetto che questa funzione aveva**, e va scritto perche' ha falsato
    quasi tutto: i sei fatti si misuravano su venti pagine centrate **sul
    documento**, e poi governavano la resa di una pagina che quasi mai era fra
    quelle. Del campione dichiarato di dieci pagine ne stava dentro **una**; delle
    pagine che avevo scelto io a mano, sei su sei -- perche' le prendevo vicino al
    centro senza saperlo.

    Costava titoli veri: `IL BANCHETTO` di Wil, **37 punti su un corpo di 10**,
    non prendeva livello, perche' la scala dei ranghi era calcolata dove quel
    titolo non c'era.

    **Ma «scansionare tutto» e' giusto solo per meta' dei fatti**, e lo dice
    `RECURRENCE_SHARE`: una linguetta di capitolo sta sul 100% di venti pagine
    dentro quel capitolo e sul 5% di un libro da quattrocento. Scansionare tutto
    la spegnerebbe.

    Quindi:

    - **ambito documento** -- prosa, livelli, marcatori, firme di scala: sono
      proprieta' della tipografia del libro, e si misurano su **tutte** le pagine;
    - **ambito vicinato** -- arredo, testatine, numeri dedotti: sono proprieta' del
      dintorno, e si misurano su una finestra che **contiene** la pagina resa.

    Un fatto document-level che cambia a seconda di quale pagina si rende non e' un
    fatto document-level: e' la definizione che separa i due ambiti.

    **Una cattura sola**: il vicinato e' una fetta di quella del documento.
    """

    # **La finestra e' UNA e contiene la pagina.** La v1 di questo criterio
    # separava i due ambiti e misurava prosa, livelli e marcatori su TUTTE le
    # pagine. Misurato, non regge: `prose_sizes` taglia al salto piu' grande fra
    # le mediane, e quel taglio **non e' invariante di scala**. Su FWK le
    # dimensioni di prosa passano da 6 a 14 e i livelli da 5 a 2 -- 15,0, 16,0,
    # 20,0 e 30,0 diventano prosa; su Dag da 4 a 23, comprese 2,8 e 3,0. Le firme
    # di scala guadagnano `('*','•')` su FWK e spengono le sue voci d'elenco.
    #
    # Dare a una statistica non invariante di scala una popolazione di taglia
    # diversa e' sbagliato a prescindere da come va a finire. Finche' il taglio
    # non e' invariante, l'ambito documento resta chiuso e si sposta soltanto la
    # finestra: stessa taglia, centrata sulla pagina invece che sul libro.
    # `Criterio_AmbitoDeiFatti_v2.md`.
    first_page = max(0, min(page_index - neighbourhood // 2, len(document) - neighbourhood))
    captured: list = []
    labels: list[str] = []
    indices: list[int] = []
    for index in range(max(0, first_page), min(len(document), max(0, first_page) + neighbourhood)):
        page = document[index]
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            continue
        indices.append(index)
        captured.append(
            normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{index:04d}",
                    capture_id=f"scan:{index:04d}",
                )
            )
        )
        labels.append((page.get_label() or "").strip())

    # --- i fatti, tutti sulla finestra --------------------------------------
    # Il font del corpo apre la seconda via dei marcatori: su Fab il pallino e'
    # la lettera `w` in Wingdings. `Criterio_MarcatoreDaFont_v1.md`.
    body = body_font([p for page in captured for p in page.text_primitives])
    markers = list_markers(measure_document_line_starts(captured, body))
    scales = value_scale_signatures(count_block_signatures(captured, markers))
    sizes = measure_font_sizes(captured)
    prose = prose_sizes(sizes)
    # Due passate: prima si vede quali dimensioni intestano davvero qualcosa, poi
    # si assegnano i ranghi solo a quelle. `Criterio_Titoli_v3.md`.
    carried = sizes_that_carry_headings([sized_lines(page) for page in captured], sizes, prose)

    # --- arredo, testatine, numeri: la stessa finestra ----------------------
    near, near_indices, near_labels = captured, indices, labels

    measured = measure_document_text_recurrence(near)
    slots = furniture_slots(list(zip(near, near_labels, strict=True)), measured)

    # I numeri **dedotti**, dove il documento non dichiara niente. Che il
    # documento dichiari o no e' una domanda d'ambito DOCUMENTO -- si guardano
    # tutte le etichette -- ma la deduzione lavora sul vicinato, perche' e' una
    # sequenza locale.
    deduced: dict[int, str] = {}
    if not any(labels):
        found = deduced_number_slots(near)
        deduced = {
            near_indices[position]: value
            for position, value in found.by_page_position.items()
            if position < len(near_indices)
        }
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
            scan = document_scan(document, page_index, neighbourhood=furniture_sample)
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
                # Le testatine si confrontano per (testo, slot) insieme, cosi' un
                # titolo di sezione che passa per lo stesso punto non esce.
                vertical_primitive_ids(primitive_page)
                | running_head_primitive_ids(primitive_page, slots.running_heads),
            )
            print(
                f"arredo: {len(slots.from_label)} slot da etichetta, "
                f"{len(slots.from_recurrence)} da ricorrenza, "
                f"{len(slots.from_sequence)} da sequenza dedotta, "
                f"{len(slots.running_heads)} testatine, "
                f"{len(vertical_primitive_ids(primitive_page))} primitive verticali, "
                f"{len(excluded_node_ids)} nodi fuori dal corpo"
                + (f" — numero dedotto: {page_label}" if page_label_deduced else ""),
                file=sys.stderr,
            )

        markdown = render_page_markdown(ir2_page, excluded_node_ids=excluded_node_ids)
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
        # Gli id esclusi in forma leggibile da un programma. **Non entrano
        # nell'IR**: l'esclusione e' una decisione di resa e l'IR non la porta.
        # Ma chi costruisce materiale a valle non deve ricavarla leggendo la
        # prosa di `review_ir2.md` con un'espressione regolare -- e' una seconda
        # via, e le seconde vie in questo progetto si sono sempre scollate da
        # quella buona.
        (output_dir / "excluded_ir2.json").write_text(
            json.dumps(sorted(excluded_node_ids), ensure_ascii=False, indent=1),
            encoding="utf-8",
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
            emitted, losses = _emitted_content(ir2_page)
            for node_id, lost in losses:
                print(
                    f"E-B: la resa ha PERSO caratteri di {node_id}: {lost!r}",
                    file=sys.stderr,
                )
            new_sequence = _normalised_sequence(emitted)
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
        help=(
            "ampiezza della finestra di VICINATO per arredo, testatine e numeri "
            "dedotti, centrata sulla pagina resa (default 60). I fatti d'ambito "
            "documento -- prosa, livelli, marcatori -- si misurano su tutte le "
            "pagine e non passano di qui. `Criterio_AmbitoDeiFatti_v1.md`."
        ),
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
