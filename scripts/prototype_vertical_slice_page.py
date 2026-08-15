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
The paragraph order used below (``y0`` ascending, then ``x0`` ascending, with
a paragraph break whenever the next TextPrimitive's ``y0`` does not overlap
the previous one's ``y1``) is a diagnostic display choice for this prototype,
not a claim about reading order, and carries no weight beyond this script.

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
from prototype_derived_column_bands import (  # noqa: E402
    _DEFAULT_MIN_FLANKING_CHARS,
    _process_page,
)

from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses  # noqa: E402
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
    previous_text_y1: float | None = None

    def flush_paragraph() -> None:
        if paragraph_words:
            lines.append(" ".join(paragraph_words))
            paragraph_words.clear()

    for _, _, kind, payload in items:
        if kind == "text":
            primitive = cast(TextPrimitive, payload)
            if previous_text_y1 is not None and primitive.bbox[1] < previous_text_y1:
                pass  # still the same paragraph: vertical overlap with previous line
            elif previous_text_y1 is not None:
                flush_paragraph()
            paragraph_words.append(primitive.text)
            previous_text_y1 = primitive.bbox[3]
        else:
            flush_paragraph()
            entry = cast(dict[str, object], payload)
            lines.append(
                f"{_ASSET_MARKER_PREFIX} primitive_id={entry['primitive_id']} "
                f"digest={entry['digest']} candidate_id={entry['candidate_id']} "
                f"asset_file={entry['asset_file']}"
            )
            previous_text_y1 = None

    flush_paragraph()
    return "\n\n".join(lines) + "\n"


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
    previous: TextPrimitive | None = None
    previous_group: int | None = None

    def flush() -> None:
        if words:
            paragraphs.append(" ".join(words))
            words.clear()

    for _rank, _kind_order, kind, payload in items:
        if kind == "text":
            primitive, group = cast("tuple[TextPrimitive, int]", payload)
            starts_new = previous is None or previous_group != group
            if previous is not None and not starts_new:
                overlaps = (
                    primitive.bbox[1] < previous.bbox[3]
                    and previous.bbox[1] < primitive.bbox[3]
                )
                starts_new = not overlaps
            if starts_new:
                flush()
            text = (primitive.text or "").strip()
            if text:
                words.append(text)
            previous = primitive
            previous_group = group
        else:
            flush()
            paragraphs.append(_asset_marker_line(cast(dict, payload)))
            previous = None
            previous_group = None

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

            _gutters, _bands, tree = _process_page(
                fitz_document,
                page_index,
                manual=pdf_path.name,
                bin_width_x=1.0,
                bin_height_y=2.0,
                min_flanking_groups=2,
                min_flanking_chars=_DEFAULT_MIN_FLANKING_CHARS,
                min_gutter_lines=3.0,
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
        "--emit-order-variants",
        action="store_true",
        help=(
            "scrive anche page_lines.md (riga dalla sorgente, nessuna banda) e "
            "page_bands.md (ordinamento ad albero di column_band). page.md resta "
            "invariato: e' la precondizione P0 del criterio."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        args.pdf,
        args.page_number,
        args.output_dir,
        emit_order_variants=args.emit_order_variants,
    )


if __name__ == "__main__":
    main()
