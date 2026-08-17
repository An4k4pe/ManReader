"""Standalone diagnostic: one page through the new pipeline, end to end.

Milestone 36, Fase A. Diagnostic prototype, not production code: composes
existing, unmodified building blocks (capture, normalization, the five wired
producers, the Milestone 13-19 co-reference subsystem, Resolution's single
rule) to answer one question -- what does one page actually look like once
routed through the new contracts, instead of the legacy pipeline? No new
producer, no new contract, no job wiring.

Duplicates locally the producer-composition helper already written in
scripts/measure_cross_producer_candidate_coverage.py instead of importing it:
scripts in this repository do not import from other scripts (``_contains``
already exists independently in five separate modules; same precedent).

Text ordering is NOT a contract. ``page_analysis_model.py`` explicitly denies
reading order for candidates and relations (lines 189-190, 192-193, 195-196):
"The order of ... is only representation order. It is not reading order,
geometric order, structural order, or any other structural constraint."
The order used below (``y0`` ascending, then ``x0`` ascending, unless one of
the ``--emit-order-variants`` branches is asked for) is a diagnostic display
choice for this prototype, not a claim about reading order, and carries no
weight beyond this script.

Paragraph segmentation is NOT a display choice and is not derived from
geometry: it comes from ``block_index`` in ``source_observation_id``
(``text:b{block}:l{line}:s{span}``), because PyMuPDF's block IS the paragraph
-- verified on DB p.53, where ``b3`` is one three-line prose paragraph and
``b4``-``b7`` are four list items, one block each. The previous rule broke a
paragraph wherever two consecutive primitives' ``y`` ranges failed to overlap,
and failed in a way no patch fixes: on DB p.53 each list item ends with an
EMPTY span whose bbox is taller than the line, which overlapped the next item
and bridged it, emitting three items on one line. Geometry stays legitimate
for positioning and for checking, never for rebuilding the structure of the
text. Same rule in all three emitters here and in
``compare_reading_order_with_column_bands.py``, kept identical on purpose.

Vector primitives are excluded from asset extraction by explicit choice
(proposal §9.2), not by omission: only ``ImageOccurrencePrimitive`` (raster)
occurrences are extracted to disk. ``DrawingPrimitive`` occurrences are never
written as asset files in this slice.

Asset note markers are single, self-contained lines in ``page.md``, each
starting with the fixed prefix ``%%VSLICE-ASSET%%`` (chosen because that
sequence is not expected to occur in manual body text). A marker line can be
removed mechanically and unambiguously with the regex ``^%%VSLICE-ASSET%%.*$``
applied per line -- the self-verification in §8 below relies on exactly this
separability to reconstruct the body text without markers.

Asset extraction prefers the embedded image resource by ``xref``
(``extraction_method = xref`` in ``assets_index.csv``). When no resolvable
xref exists (e.g. inline images), the occurrence's placed area is rasterized
directly from the page instead (``extraction_method = rasterized_clip``).
That fallback is a substitution, not the embedded asset: the bytes on disk in
that case do NOT match the ``digest`` they are filed under, which remains the
hash PyMuPDF computed for the true embedded resource. The substitution is
recorded, never silent -- but it must not be mistaken for the original.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

import fitz
import pdfplumber
from pdfplumber.page import Page as PlumberPage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Diagnostica su diagnostica: le due varianti d'ordine di `--emit-order-variants`
# vengono dagli stessi artefatti gia' committati, non da una seconda
# implementazione. Nessuno dei due e' un producer e nessuno e' wired.
from compare_reading_order_with_column_bands import (  # noqa: E402
    _by_source_line,
    _tree_aware_order,
)
# Le bande vengono dal MODULO DI PRODUZIONE, non piu' dallo script diagnostico.
# Prima questa fetta chiamava `prototype_derived_column_bands._process_page`,
# quindi il markdown che si giudicava a vista NON era prodotto dal percorso che
# il job monta: due rami che non si toccavano, divergenti su 9 pagine su 20.
# Rilievo della revisione architetturale.
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)

from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
from page_analysis_drawing_cluster_diagnostics import (  # noqa: E402
    dump_drawing_cluster_diagnostics,
)
from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from page_analysis_model import PageAnalysis, RegionCandidate  # noqa: E402
from page_analysis_page_covering_visual import (  # noqa: E402
    build_page_covering_visual_page_analysis,
)
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis  # noqa: E402
from page_analysis_table_candidate import build_table_candidate_page_analysis  # noqa: E402
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_model import (  # noqa: E402
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_page_candidates import resolve_page_candidates  # noqa: E402

_ASSET_MARKER_PREFIX = "%%VSLICE-ASSET%%"
_ASSET_MARKER_LINE_PATTERN = re.compile(rf"^{re.escape(_ASSET_MARKER_PREFIX)}.*$", re.MULTILINE)
_ASSET_FILE_FIELD_PATTERN = re.compile(r"asset_file=(\S+)")
_IMAGE_OBSERVATION_INDEX_PATTERN = re.compile(r"^image:i(\d+)$")
_TEXT_BLOCK_PATTERN = re.compile(r"^text:b(\d+):l\d+:s\d+$")
_UNSAFE_FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9_-]")


def _precondition_fail(message: str) -> None:
    print(f"PRECONDITION_FAIL: {message}", file=sys.stderr)
    sys.exit(3)


def _invariant_fail(message: str) -> None:
    print(f"INVARIANT_FAIL: {message}", file=sys.stderr)
    sys.exit(4)


def _safe_filename_stem(identity: str) -> str:
    return _UNSAFE_FILENAME_CHARACTERS.sub("_", identity)


def _build_all_analyses(
    primitive_page: NormalizedPrimitivePage,
    *,
    plumber_page: PlumberPage,
    generation_id: str,
) -> tuple[PageAnalysis, ...]:
    """Duplicated locally from measure_cross_producer_candidate_coverage.py."""

    return (
        build_table_candidate_page_analysis(
            BoundTableCandidatePage(
                primitive_page=primitive_page,
                plumber_page=plumber_page,
            ),
            generation_id=generation_id,
        ),
        build_page_covering_visual_page_analysis(primitive_page, generation_id=generation_id),
        build_page_edge_visual_page_analysis(primitive_page, generation_id=generation_id),
        build_embedded_visual_page_analysis(primitive_page, generation_id=generation_id),
        build_interior_visual_frame_page_analysis(primitive_page, generation_id=generation_id),
    )


def _image_index_from_observation_id(source_observation_id: str) -> int:
    match = _IMAGE_OBSERVATION_INDEX_PATTERN.match(source_observation_id)
    if match is None:
        raise ValueError(
            f"unexpected image source_observation_id format: {source_observation_id!r}"
        )
    return int(match.group(1))


def _extract_image_bytes(
    *,
    fitz_document: fitz.Document,
    page: fitz.Page,
    primitive: ImageOccurrencePrimitive,
    raw_image_info: list[dict[str, Any]],
) -> tuple[bytes, str, str]:
    """Extract the raster bytes for one occurrence; return (bytes, ext, method).

    ``method`` is ``"xref"`` when the embedded resource itself was extracted,
    or ``"rasterized_clip"`` when the fallback below was used -- callers must
    not treat the two as interchangeable (see module docstring).
    """

    image_index = _image_index_from_observation_id(primitive.source_observation_id)
    xref = cast(int | None, raw_image_info[image_index].get("xref"))
    if xref is not None and xref > 0:
        info = fitz_document.extract_image(xref)
        return cast(bytes, info["image"]), cast(str, info["ext"]), "xref"

    # Defensive fallback for occurrences with no resolvable xref (e.g. inline
    # images): rasterize the placed occurrence directly from the page. This
    # is a substitution, not the embedded asset -- see module docstring.
    clip = fitz.Rect(*primitive.bbox)
    pixmap = page.get_pixmap(clip=clip)
    return pixmap.tobytes("png"), "png", "rasterized_clip"


def _asset_identity(primitive: ImageOccurrencePrimitive) -> tuple[str, bool]:
    """Return (identity_key, digest_missing) for one image occurrence."""

    if primitive.content_digest is not None:
        return primitive.content_digest, False
    return f"missing:{primitive.primitive_id}", True


def _governing_outcome(
    primitive_id: str,
    *,
    analyses: tuple[PageAnalysis, ...],
    outcome_by_candidate: dict[tuple[str, str], str],
) -> tuple[RegionCandidate | None, str, str | None]:
    """Pick the (candidate, outcome, producer_name) that governs one occurrence.

    Preference order: an accepted candidate wins; otherwise the first
    unresolved candidate (sorted by producer_name, candidate_id) is reported;
    otherwise the occurrence has no_candidate. ``rejected`` candidates are
    never governing: Resolution's single rule only rejects an embedded_visual
    candidate when an accepted interior_visual_frame candidate references the
    exact same primitive set, so a rejected-only occurrence cannot occur.
    """

    referencing: list[tuple[str, RegionCandidate]] = []
    for analysis in analyses:
        for candidate in analysis.candidates:
            if primitive_id in candidate.primitive_ids:
                referencing.append((analysis.provenance.producer_name, candidate))
    referencing.sort(key=lambda item: (item[0], item[1].candidate_id))

    accepted = [
        (producer_name, candidate)
        for producer_name, candidate in referencing
        if outcome_by_candidate.get((producer_name, candidate.candidate_id)) == "accepted"
    ]
    if accepted:
        producer_name, candidate = accepted[0]
        return candidate, "accepted", producer_name

    unresolved = [
        (producer_name, candidate)
        for producer_name, candidate in referencing
        if outcome_by_candidate.get((producer_name, candidate.candidate_id)) == "unresolved"
    ]
    if unresolved:
        producer_name, candidate = unresolved[0]
        return candidate, "unresolved", producer_name

    return None, "no_candidate", None


def _sorted_text_primitives(text_primitives: tuple[TextPrimitive, ...]) -> list[TextPrimitive]:
    return sorted(text_primitives, key=lambda primitive: (primitive.bbox[1], primitive.bbox[0]))


def _build_markdown_body(
    *,
    text_primitives: list[TextPrimitive],
    note_entries: list[dict[str, object]],
) -> str:
    """Interleave text paragraphs and note markers in geometric order.

    Paragraph breaks are decided strictly from consecutive TextPrimitive
    ``y0``/``y1`` (no overlap => new paragraph); note markers do not
    participate in that decision and are always emitted as their own line,
    so a note can never silently merge two paragraphs into one. A note CAN
    split one paragraph into two: ``flush_paragraph()`` runs before the
    marker is emitted, so any text on either side of the note lands in a
    separate paragraph even when the underlying TextPrimitive geometry would
    not otherwise have triggered a break.
    """

    items: list[tuple[float, float, str, object]] = []
    items.extend(
        (primitive.bbox[1], primitive.bbox[0], "text", primitive) for primitive in text_primitives
    )
    items.extend(
        (cast(float, entry["y0"]), cast(float, entry["x0"]), "note", entry)
        for entry in note_entries
    )
    items.sort(key=lambda item: (item[0], item[1]))

    lines: list[str] = []
    paragraph_words: list[str] = []
    previous_block: int | None = None
    seen_text = False

    def flush_paragraph() -> None:
        if paragraph_words:
            lines.append(" ".join(paragraph_words))
            paragraph_words.clear()

    for _, _, kind, payload in items:
        if kind == "text":
            primitive = cast(TextPrimitive, payload)
            block = _source_block(primitive)
            # Id non interpretabile: paragrafo a se'. Non si indovina
            # l'appartenenza, perche' sbagliarla fonde paragrafi distinti.
            if seen_text and (block is None or block != previous_block):
                flush_paragraph()
            paragraph_words.append(primitive.text)
            previous_block = block
            seen_text = True
        else:
            flush_paragraph()
            entry = cast(dict[str, object], payload)
            lines.append(
                f"{_ASSET_MARKER_PREFIX} primitive_id={entry['primitive_id']} "
                f"digest={entry['digest']} candidate_id={entry['candidate_id']} "
                f"asset_file={entry['asset_file']}"
            )
            previous_block = None
            seen_text = False

    flush_paragraph()
    return "\n\n".join(lines) + "\n"


def _corridor_blockers(
    *,
    primitive_page: NormalizedPrimitivePage,
    analyses: tuple[PageAnalysis, ...],
    sources: str = "both",
) -> list[tuple[float, float, float, float]]:
    """Cio' che puo' interrompere un corridoio, come bbox (x0, y0, x1, y1).

    Criterio_InterruzioneCorridoio_v1.md §2. Qui si RACCOGLIE soltanto; se una
    di queste cose attraversi davvero un dato gutter lo decide
    ``_split_bands_at_crossings``, perche' dipende dall'intervallo x di quel
    gutter.

    Tre sorgenti e una esclusione:

    - i candidati ``layout.embedded_visual``, cioe' il producer che dice dove
      sono le figure, con le soglie ratificate in Milestone 27/28;
    - MAI i candidati ``layout.page_covering_visual``: sono il fondo pagina, e
      contarli bloccherebbe qualunque corridoio -- la trappola gia' vista da
      ``--widen-bands``;
    - le ``DrawingPrimitive`` piu' basse della riga di testo piu' bassa della
      pagina: non possono contenere testo, quindi sono separatori e non
      regioni. La soglia e' desunta dalla pagina, non fissata.

    Le ``DrawingPrimitive`` piu' alte di cosi' NON contano: sono regioni, e le
    regioni devono arrivare da ``embedded_visual``. Se una non arriva e'
    un buco di quel producer, e va chiuso li' invece di costruire qui un
    secondo rilevatore di visuali.

    Il testo non compare perche' e' gia' coperto: un corridoio esiste solo dove
    il testo non copre il suo intervallo x.
    """

    blockers: list[tuple[float, float, float, float]] = []

    if sources in ("both", "visuals"):
        for analysis in analyses:
            for candidate in analysis.candidates:
                if candidate.proposed_structural_kind == "layout.embedded_visual":
                    blockers.append(candidate.bbox)

    if sources == "visuals":
        return blockers

    text_heights = [
        primitive.bbox[3] - primitive.bbox[1]
        for primitive in primitive_page.text_primitives
        if primitive.bbox[3] > primitive.bbox[1]
    ]
    if text_heights:
        shortest_line = min(text_heights)
        # Si LEGGE la classificazione di Milestone 26 invece di ridedurla dalle
        # primitive grezze. `page_analysis_drawing_cluster_diagnostics` gia'
        # raggruppa i disegni e segnala quelli senza area; da quando registra
        # anche `degenerate_bbox`, un filetto orizzontale conserva la propria
        # posizione invece di ridursi alla sola etichetta `tiny`. Il costo e'
        # andare a leggere che in quel punto un altro modulo ha segnalato
        # qualcosa -- che e' esattamente cio' che `AGENTS.MD` §Layout e
        # candidati chiede a un consumer, invece di ricavarlo dai pixel.
        clusters = cast(
            list[dict[str, object]],
            dump_drawing_cluster_diagnostics(
                primitive_page, generation_id="corridor-blockers"
            )["clusters"],
        )
        for cluster in clusters:
            box = cluster["bbox"] or cluster["degenerate_bbox"]
            if box is None:
                continue
            bbox = cast(list[float], box)
            if bbox[3] - bbox[1] < shortest_line:
                blockers.append((bbox[0], bbox[1], bbox[2], bbox[3]))

    return blockers


def _split_bands_at_crossings(
    tree: list[dict[str, object]],
    blockers: list[tuple[float, float, float, float]],
) -> list[dict[str, object]]:
    """Spezza ogni banda dove un blocker ATTRAVERSA uno dei suoi gutter.

    Attraversare = coprire per intero l'intervallo x del gutter. Costeggiare
    non basta: su DrW p.97 l'immagine finisce a x 299 e il gutter comincia a
    299, e quella pagina deve restare intatta.

    Spezza, non tronca (§3 del criterio). Troncare manderebbe fuori banda tutto
    cio' che sta sotto l'interruzione, e dove le colonne proseguono quelle
    primitive tornerebbero a ``(y0, x0)`` mescolandosi riga per riga: un falso
    negativo su regione multicolonna, la classe non recuperabile.

    ``column_band`` non viene toccato: da qui non esce nessun gutter nuovo e
    nessuna banda che il producer non avesse gia' emesso -- solo pezzi di
    quelle.
    """

    out: list[dict[str, object]] = []
    next_band_id = max((int(cast(int, r["band_id"])) for r in tree), default=0) + 1
    renamed: dict[int, list[dict[str, object]]] = {}

    for row in tree:
        band_id = int(cast(int, row["band_id"]))
        y0, y1 = float(cast(float, row["y0"])), float(cast(float, row["y1"]))
        gutters: list[tuple[float, float]] = []
        for chunk in str(row.get("gutter_x_intervals") or "").split():
            start, _, end = chunk.partition("-")
            try:
                gutters.append((float(start), float(end)))
            except ValueError:
                continue

        blocked: list[tuple[float, float]] = []
        for bx0, by0, bx1, by1 in blockers:
            crosses = any(bx0 <= gx0 and bx1 >= gx1 for gx0, gx1 in gutters)
            if crosses and by1 > y0 and by0 < y1:
                blocked.append((max(by0, y0), min(by1, y1)))

        if not blocked:
            kept_row = dict(row)
            kept_row["origin_band_id"] = band_id
            out.append(kept_row)
            renamed[band_id] = [kept_row]
            continue

        # Le fette che sopravvivono: [y0, y1] meno gli intervalli bloccati.
        blocked.sort()
        pieces: list[tuple[float, float]] = []
        cursor = y0
        for block_y0, block_y1 in blocked:
            if block_y0 > cursor:
                pieces.append((cursor, block_y0))
            cursor = max(cursor, block_y1)
        if cursor < y1:
            pieces.append((cursor, y1))

        produced: list[dict[str, object]] = []
        for index, (piece_y0, piece_y1) in enumerate(pieces):
            piece = dict(row)
            piece["y0"], piece["y1"] = piece_y0, piece_y1
            # Da quale banda originale viene questo pezzo. Serve a chi misura:
            # risalire per contenimento sbaglia, perche' dentro l'intervallo di
            # una banda cadono anche i pezzi delle sue figlie.
            piece["origin_band_id"] = band_id
            if index > 0:
                piece["band_id"] = next_band_id
                next_band_id += 1
            produced.append(piece)
            out.append(piece)
        renamed[band_id] = produced

    # Un figlio si riaggancia al pezzo di padre che lo copre di piu' in y.
    #
    # DUE COSE CHE QUESTA FUNZIONE NON DEVE FARE, entrambe scoperte perche' su
    # Dag p.24 l'uscita cambiava con ZERO blocker attraversanti:
    #
    # 1. non toccare la genealogia quando il padre non e' stato spezzato. Un
    #    padre intero ha un pezzo solo e conserva il proprio band_id, quindi non
    #    c'e' niente da riagganciare;
    # 2. non orfanare mai. Una versione precedente cercava il pezzo che
    #    contenesse il PUNTO MEDIO del figlio e, non trovandolo, azzerava
    #    parent_id e depth. La premessa era falsa: la subordinazione e' una
    #    disgiunzione x piu' un confronto di estensione (`_segment_tree`), non un
    #    contenimento in y, quindi una figlia puo' estendersi oltre il padre.
    #    Su Dag p.24 appiattiva tre bande annidate e con esse la regola "vince la
    #    banda piu' profonda", senza che nessuna interruzione fosse avvenuta.
    for row in out:
        parent = row.get("parent_id")
        if parent in ("", None):
            continue
        pieces_of_parent = renamed.get(int(cast(int, parent)), [])
        if len(pieces_of_parent) <= 1:
            continue

        row_y0 = float(cast(float, row["y0"]))
        row_y1 = float(cast(float, row["y1"]))

        def overlap(piece: dict[str, object]) -> float:
            return max(
                0.0,
                min(row_y1, float(cast(float, piece["y1"])))
                - max(row_y0, float(cast(float, piece["y0"]))),
            )

        row["parent_id"] = max(pieces_of_parent, key=overlap)["band_id"]

    return out


def _source_block(primitive: TextPrimitive) -> int | None:
    """Il paragrafo secondo la sorgente: `block_index` dall'id di osservazione.

    Il paragrafo NON si deduce dalla geometria. `pymupdf_capture.py:123-125`
    scrive gia' blocco, riga e span nell'id (`text:b{block}:l{line}:s{span}`), e
    il blocco e' il paragrafo -- verificato su DB p.53, dove `b3` e' un
    paragrafo di prosa su tre righe e `b4`-`b7` sono quattro voci di elenco, una
    per blocco.

    La regola precedente confrontava le `y` di due primitive consecutive e
    andava a capo dove non si sovrapponevano. Falliva in modo non riparabile:
    su DB p.53 ogni voce dell'elenco finisce con uno span SENZA testo di bbox
    piu' alto della riga, che si sovrapponeva alla voce successiva e faceva da
    ponte, emettendo tre voci su una riga sola. La geometria resta legittima per
    posizionare e per verificare, mai per ricostruire la struttura del testo.
    """

    match = _TEXT_BLOCK_PATTERN.match(primitive.source_observation_id or "")
    return int(match.group(1)) if match else None


def _tree_rows_from_contract(
    candidates: tuple[RegionCandidate, ...],
    measurements: tuple[Any, ...],
) -> list[dict[str, object]]:
    """Le righe che l'ordinatore vuole, ricostruite da candidati e misure.

    Serve a dimostrare una cosa e a dimostrarla ogni volta che gira: il
    contratto di Milestone 33 -- candidato minimale piu' misura satellite --
    **basta** a un consumer che debba ordinare per colonne. Dal candidato
    vengono bbox e primitive, dalla misura i gutter, il livello e il padre.
    Nessuna struttura interna del producer attraversa questo confine.

    Se un giorno questa funzione avesse bisogno di qualcosa che ne' il candidato
    ne' la misura portano, quella sarebbe la prova che il contratto non basta --
    ed e' esattamente la domanda che Milestone 33 aveva lasciato aperta.
    """

    band_id_by_candidate = {c.candidate_id: index + 1 for index, c in enumerate(candidates)}
    measure_by_candidate = {m.candidate_id: m for m in measurements}

    rows: list[dict[str, object]] = []
    for candidate in candidates:
        measure = measure_by_candidate.get(candidate.candidate_id)
        if measure is None:
            continue
        parent = ""
        if measure.parent_candidate_id is not None:
            parent = band_id_by_candidate.get(measure.parent_candidate_id, "")
        rows.append(
            {
                "band_id": band_id_by_candidate[candidate.candidate_id],
                "parent_id": parent,
                "depth": measure.depth,
                "x0": candidate.bbox[0],
                "y0": candidate.bbox[1],
                "x1": candidate.bbox[2],
                "y1": candidate.bbox[3],
                "column_count": measure.column_count,
                "gutter_x_intervals": " ".join(
                    f"{a:.1f}-{b:.1f}" for a, b in measure.gutter_x_intervals
                ),
            }
        )
    return rows


def _asset_marker_line(entry: dict[str, object]) -> str:
    return (
        f"{_ASSET_MARKER_PREFIX} primitive_id={entry['primitive_id']} "
        f"digest={entry['digest']} candidate_id={entry['candidate_id']} "
        f"asset_file={entry['asset_file']}"
    )


def _ordered_markdown_body(
    *,
    ordered: list[tuple[TextPrimitive, int]],
    note_entries: list[dict[str, object]],
) -> str:
    """Come ``_build_markdown_body`` ma su un ordine GIA' stabilito.

    ``_build_markdown_body`` riordina per ``(y0, x0)`` dopo aver mescolato testo
    e note: passargli una sequenza gia' ordinata a bande la disferebbe. Qui
    l'ordine del testo e' quello ricevuto e non viene toccato.

    Un solo adattamento, lo stesso gia' dichiarato in
    ``compare_reading_order_with_column_bands.py``: il cambio di colonna forza
    un paragrafo. Senza, l'ultima riga di una colonna si fonde con la prima
    della successiva e il confronto sarebbe truccato a sfavore del ramo a bande.

    Le note si inseriscono prima della prima primitiva testuale che le segue in
    ``y``; se nessuna le segue, in fondo. Il testo non si sposta: le note si
    accomodano attorno a lui, mai il contrario.
    """

    items: list[tuple[int, int, str, object]] = []
    items.extend(
        (rank, 1, "text", payload) for rank, payload in enumerate(ordered)
    )
    for entry in note_entries:
        note_y0 = cast(float, entry["y0"])
        rank = next(
            (r for r, (primitive, _g) in enumerate(ordered) if primitive.bbox[1] > note_y0),
            len(ordered),
        )
        items.append((rank, 0, "note", entry))
    items.sort(key=lambda item: (item[0], item[1]))

    paragraphs: list[str] = []
    words: list[str] = []
    previous_block: int | None = None
    previous_group: int | None = None
    seen_text = False

    def flush() -> None:
        if words:
            paragraphs.append(" ".join(words))
            words.clear()

    for _rank, _kind_order, kind, payload in items:
        if kind == "text":
            primitive, group = cast("tuple[TextPrimitive, int]", payload)
            block = _source_block(primitive)
            # Paragrafo dal BLOCCO della sorgente, piu' il solo adattamento gia'
            # dichiarato: il cambio di colonna forza comunque un paragrafo,
            # altrimenti l'ultima riga di una colonna si fonde con la prima
            # della successiva. Il resto e' letto, non dedotto: la regola
            # geometrica precedente e' caduta su DB p.53, dove uno span vuoto
            # faceva da ponte fra tre voci d'elenco che sono tre blocchi.
            if seen_text and (
                previous_group != group or block is None or block != previous_block
            ):
                flush()
            text = (primitive.text or "").strip()
            if text:
                words.append(text)
            previous_block = block
            previous_group = group
            seen_text = True
        else:
            flush()
            paragraphs.append(_asset_marker_line(cast(dict, payload)))
            previous_block = None
            previous_group = None
            seen_text = False

    flush()
    return "\n\n".join(paragraphs) + "\n"


def _strip_asset_markers(body: str) -> str:
    return _ASSET_MARKER_LINE_PATTERN.sub("", body)


def _non_space_multiset(text: str) -> Counter[str]:
    return Counter(character for character in text if not character.isspace())


def run(
    pdf_path: Path,
    page_number: int,
    output_dir: Path,
    emit_order_variants: bool = False,
    interrupt_corridor: str = "",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (
        fitz.open(pdf_path) as fitz_document,
        pdfplumber.open(str(pdf_path)) as plumber_pdf,
    ):
        page_count = fitz_document.page_count
        if not 1 <= page_number <= page_count:
            _precondition_fail(f"page_number out of range (page_count={page_count})")

        page_index = page_number - 1
        page = fitz_document.load_page(page_index)
        if page.rotation != 0:
            _precondition_fail("rotation must be 0")
        if page.mediabox != page.cropbox:
            _precondition_fail("cropbox != mediabox")

        generation_id = f"vslice:page:{page_number:04d}"
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{page_number:04d}",
            capture_id=f"vslice:pymupdf:page:{page_number:04d}",
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
            (
                outcome.candidate_reference.producer_name,
                outcome.candidate_reference.candidate_id,
            ): outcome.outcome
            for outcome in resolved.outcomes
        }

        raw_image_info = cast(
            list[dict[str, Any]], page.get_image_info(hashes=True, xrefs=True)
        )

        # --- Asset extraction: one file per distinct identity, raster only ---
        assets: dict[str, dict[str, object]] = {}
        occurrence_rows: list[dict[str, object]] = []
        note_entries: list[dict[str, object]] = []
        written_asset_paths: set[Path] = set()

        for primitive in sorted(
            primitive_page.image_primitives, key=lambda item: item.primitive_id
        ):
            identity, digest_missing = _asset_identity(primitive)
            if identity not in assets:
                image_bytes, extension, extraction_method = _extract_image_bytes(
                    fitz_document=fitz_document,
                    page=page,
                    primitive=primitive,
                    raw_image_info=raw_image_info,
                )
                file_name = f"{_safe_filename_stem(identity)}.{extension}"
                file_path = output_dir / file_name
                file_path.write_bytes(image_bytes)
                written_asset_paths.add(file_path)
                assets[identity] = {
                    "digest": identity,
                    "file_path": file_name,
                    "intrinsic_width": primitive.intrinsic_width,
                    "intrinsic_height": primitive.intrinsic_height,
                    "occurrence_count": 0,
                    "digest_missing": digest_missing,
                    "extraction_method": extraction_method,
                }
            asset = assets[identity]
            asset["occurrence_count"] = cast(int, asset["occurrence_count"]) + 1

            candidate, outcome, _producer_name = _governing_outcome(
                primitive.primitive_id,
                analyses=analyses,
                outcome_by_candidate=outcome_by_candidate,
            )
            destination = "body" if outcome == "accepted" else "review"
            occurrence_rows.append(
                {
                    "digest": identity,
                    "bbox": ",".join(f"{coordinate:.6f}" for coordinate in primitive.bbox),
                    "primitive_id": primitive.primitive_id,
                    "destination": destination,
                    "candidate_id": candidate.candidate_id if candidate is not None else "",
                    "outcome": outcome,
                }
            )
            if outcome == "accepted":
                note_entries.append(
                    {
                        "y0": primitive.bbox[1],
                        "x0": primitive.bbox[0],
                        "primitive_id": primitive.primitive_id,
                        "digest": identity,
                        "candidate_id": candidate.candidate_id if candidate is not None else "",
                        "asset_file": assets[identity]["file_path"],
                    }
                )

        # --- Markdown body ---
        text_primitives = _sorted_text_primitives(primitive_page.text_primitives)
        body = _build_markdown_body(text_primitives=text_primitives, note_entries=note_entries)
        page_md_path = output_dir / "page.md"
        page_md_path.write_text(body, encoding="utf-8")

        # --- Review file ---
        review_rows = [row for row in occurrence_rows if row["destination"] == "review"]
        review_lines = [f"# Review — page {page_number}", ""]
        for row in review_rows:
            review_lines.append(f"## occurrence {row['primitive_id']}")
            review_lines.append(f"- bbox: {row['bbox']}")
            review_lines.append(f"- outcome: {row['outcome']}")
            review_lines.append(f"- candidate_id: {row['candidate_id'] or '(none)'}")
            review_lines.append(f"- asset_file={assets[cast(str, row['digest'])]['file_path']}")
            review_lines.append("")
        review_md_path = output_dir / "review.md"
        review_md_path.write_text("\n".join(review_lines) + "\n", encoding="utf-8")

        # --- Assets index ---
        assets_index_path = output_dir / "assets_index.csv"
        fieldnames = [
            "record_type",
            "digest",
            "file_path",
            "intrinsic_width",
            "intrinsic_height",
            "occurrence_count",
            "digest_missing",
            "bbox",
            "primitive_id",
            "destination",
            "candidate_id",
            "outcome",
            "extraction_method",
        ]
        with assets_index_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for identity in sorted(assets):
                asset = assets[identity]
                writer.writerow(
                    {
                        "record_type": "asset",
                        "digest": asset["digest"],
                        "file_path": asset["file_path"],
                        "intrinsic_width": asset["intrinsic_width"],
                        "intrinsic_height": asset["intrinsic_height"],
                        "occurrence_count": asset["occurrence_count"],
                        "digest_missing": asset["digest_missing"],
                        "bbox": "",
                        "primitive_id": "",
                        "destination": "",
                        "candidate_id": "",
                        "outcome": "",
                        "extraction_method": asset["extraction_method"],
                    }
                )
            for row in occurrence_rows:
                writer.writerow(
                    {
                        "record_type": "occurrence",
                        "digest": row["digest"],
                        "file_path": "",
                        "intrinsic_width": "",
                        "intrinsic_height": "",
                        "occurrence_count": "",
                        "digest_missing": "",
                        "bbox": row["bbox"],
                        "primitive_id": row["primitive_id"],
                        "destination": row["destination"],
                        "candidate_id": row["candidate_id"],
                        "outcome": row["outcome"],
                        "extraction_method": "",
                    }
                )

        # === §8: self-verification, both invariants ===
        # Anchored to primitive_page.text_primitives (the pipeline's actual
        # source), not to the sorted intermediate list that also feeds
        # _build_markdown_body: the two must stay independently checkable
        # even if a future filter is added to the sorting/ordering step.
        _verify_content_conservation(primitive_page.text_primitives, body)
        _verify_reference_integrity(
            output_dir=output_dir,
            written_asset_paths=written_asset_paths,
            page_md_body=body,
            review_md_text="\n".join(review_lines) + "\n",
            occurrence_row_count=len(occurrence_rows),
            image_primitive_count=len(primitive_page.image_primitives),
            asset_count=len(assets),
        )

        # === Varianti d'ordine (Criterio_GiunzioneFettaVerticale_v1.md §5) ===
        # `page.md` sopra NON viene toccato: e' la precondizione P0, cioe' che
        # questo flag non possa cambiare Milestone 36 in silenzio.
        #
        # Il termine di paragone del ramo a bande e' `page_lines.md`, MAI
        # `page.md`: confrontare le bande (che hanno la riga di sorgente) con
        # l'ordinamento grezzo (che non ce l'ha) misura due cose insieme e le
        # attribuisce entrambe alle bande. E' il trucco gia' trovato al quinto
        # giro di revisione.
        if emit_order_variants:
            variant_paths: list[Path] = []

            lines_ordered = [(p, 0) for p in _by_source_line(list(primitive_page.text_primitives))]
            lines_body = _ordered_markdown_body(
                ordered=lines_ordered, note_entries=note_entries
            )
            lines_path = output_dir / "page_lines.md"
            lines_path.write_text(lines_body, encoding="utf-8")
            variant_paths.append(lines_path)
            _verify_content_conservation(primitive_page.text_primitives, lines_body)

            # Il consumer legge **candidati e misure satellite**, non le
            # strutture interne del producer. Prima chiamava `column_band_tree`,
            # cioe' l'albero: era il ponte provvisorio finche' la misura
            # satellite prevista da Milestone 33 non esisteva. Ora esiste, e
            # questo passaggio e' la prova che il contratto basta a consumare --
            # dal candidato bbox e primitive, dalla misura i gutter e il livello.
            column_band_analysis, column_band_measures = (
                build_column_band_page_analysis_with_measurements(
                    primitive_page, generation_id=generation_id
                )
            )
            tree = _tree_rows_from_contract(
                column_band_analysis.candidates, column_band_measures
            )
            bands_ordered, inside = _tree_aware_order(
                list(primitive_page.text_primitives), tree
            )
            bands_body = _ordered_markdown_body(
                ordered=bands_ordered, note_entries=note_entries
            )
            bands_path = output_dir / "page_bands.md"
            bands_path.write_text(bands_body, encoding="utf-8")
            variant_paths.append(bands_path)
            _verify_content_conservation(primitive_page.text_primitives, bands_body)

            print(
                f"order_variants: bands={len(tree)} "
                f"primitives_in_band={inside}/{len(primitive_page.text_primitives)}",
                file=sys.stderr,
            )

            # Criterio_InterruzioneCorridoio_v1.md. Emette SEMPRE anche la
            # variante non tagliata, sopra: il confronto va fatto fra le due, e
            # su DrW p.97 il criterio predice che siano identiche.
            if interrupt_corridor:
                blockers = _corridor_blockers(
                    primitive_page=primitive_page,
                    analyses=analyses,
                    sources=interrupt_corridor,
                )
                cut_tree = _split_bands_at_crossings(tree, blockers)
                cut_ordered, cut_inside = _tree_aware_order(
                    list(primitive_page.text_primitives), cut_tree
                )
                cut_body = _ordered_markdown_body(
                    ordered=cut_ordered, note_entries=note_entries
                )
                cut_path = output_dir / "page_bands_cut.md"
                cut_path.write_text(cut_body, encoding="utf-8")
                variant_paths.append(cut_path)
                _verify_content_conservation(primitive_page.text_primitives, cut_body)
                print(
                    f"corridor_interrupt: blockers={len(blockers)} "
                    f"bands={len(tree)}->{len(cut_tree)} "
                    f"primitives_in_band={inside}->{cut_inside} "
                    f"identical={'yes' if cut_body == bands_body else 'NO'}",
                    file=sys.stderr,
                )
            print(
                "OK: wrote " + ", ".join(str(path) for path in variant_paths),
                file=sys.stderr,
            )

        # Non-blocking measures.
        stripped_body = _strip_asset_markers(body)
        note_count = len(note_entries)
        review_count = len(review_rows)
        word_count = len(stripped_body.split())
        ratio = note_count / word_count if word_count > 0 else float("nan")
        print(
            f"notes={note_count} review_entries={review_count} "
            f"body_words={word_count} notes_per_word={ratio}",
            file=sys.stderr,
        )
        print(f"OK: wrote {page_md_path}, {review_md_path}, {assets_index_path}", file=sys.stderr)


def _verify_content_conservation(
    text_primitives: tuple[TextPrimitive, ...], body: str
) -> None:
    input_multiset = _non_space_multiset("".join(primitive.text for primitive in text_primitives))
    stripped_body = _strip_asset_markers(body)
    output_multiset = _non_space_multiset(stripped_body)

    input_total = sum(input_multiset.values())
    output_total = sum(output_multiset.values())
    print(
        f"content_conservation: input_non_space_chars={input_total} "
        f"output_non_space_chars={output_total}",
        file=sys.stderr,
    )

    if input_multiset == output_multiset:
        return

    excess = output_multiset - input_multiset
    deficit = input_multiset - output_multiset
    print(f"  excess in output (not in input): {excess.most_common(20)}", file=sys.stderr)
    print(f"  deficit (missing from output): {deficit.most_common(20)}", file=sys.stderr)
    _invariant_fail("content conservation: non-space character multisets differ")


def _verify_reference_integrity(
    *,
    output_dir: Path,
    written_asset_paths: set[Path],
    page_md_body: str,
    review_md_text: str,
    occurrence_row_count: int,
    image_primitive_count: int,
    asset_count: int,
) -> None:
    referenced_files = set(_ASSET_FILE_FIELD_PATTERN.findall(page_md_body)) | set(
        _ASSET_FILE_FIELD_PATTERN.findall(review_md_text)
    )
    missing_files = [name for name in sorted(referenced_files) if not (output_dir / name).is_file()]

    print(
        f"reference_integrity: referenced_files={len(referenced_files)} "
        f"missing_files={len(missing_files)} occurrence_rows={occurrence_row_count} "
        f"image_primitives={image_primitive_count} asset_rows={asset_count} "
        f"files_written={len(written_asset_paths)}",
        file=sys.stderr,
    )

    problems: list[str] = []
    if missing_files:
        problems.append(f"referenced asset files missing on disk: {missing_files}")
    if occurrence_row_count != image_primitive_count:
        problems.append(
            "occurrence row count "
            f"({occurrence_row_count}) != ImageOccurrencePrimitive count ({image_primitive_count})"
        )
    if len(written_asset_paths) != asset_count:
        problems.append(
            f"files written ({len(written_asset_paths)}) != asset row count ({asset_count})"
        )

    if problems:
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        _invariant_fail("reference integrity check failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Vertical slice: run one PDF page through capture, normalization, the five "
            "wired producers, co-reference, and Resolution; write page.md, "
            "assets_index.csv, review.md, and raster asset files."
        ),
    )
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--page-number", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--interrupt-corridor",
        choices=("both", "drawings", "visuals"),
        default="",
        help=(
            "spezza le bande dove un embedded_visual o un filetto attraversa il "
            "corridoio (Criterio_InterruzioneCorridoio_v1.md). Emette "
            "page_bands_cut.md accanto a page_bands.md, mai al posto suo. "
            "Richiede --emit-order-variants."
        ),
    )
    parser.add_argument(
        "--emit-order-variants",
        action="store_true",
        help=(
            "scrive anche page_lines.md (riga dalla sorgente, nessuna banda) e "
            "page_bands.md (ordinamento ad albero di column_band). page.md resta "
            "invariato: e' la precondizione P0 del criterio."
        ),
    )
    args = parser.parse_args()
    # Senza --emit-order-variants il blocco dell'interruzione non viene mai
    # eseguito, e il flag veniva accettato in silenzio. Su un progetto che ha
    # gia' registrato quattro errori di misura consecutivi, uno strumento che
    # tace quando non ha fatto la cosa richiesta e' un rischio sproporzionato al
    # costo di questa riga. Rilievo della revisione indipendente.
    if args.interrupt_corridor and not args.emit_order_variants:
        parser.error("--interrupt-corridor richiede --emit-order-variants")
    return args


def main() -> None:
    args = parse_args()
    run(
        args.pdf,
        args.page_number,
        args.output_dir,
        emit_order_variants=args.emit_order_variants,
        interrupt_corridor=args.interrupt_corridor,
    )


if __name__ == "__main__":
    main()
