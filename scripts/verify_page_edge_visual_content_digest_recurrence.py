"""Standalone diagnostic: content_digest recurrence for page_edge_visual candidates.

Stesso identico approccio di verify_page_covering_visual_content_digest_recurrence.py,
applicato a page_edge_visual invece che page_covering_visual: nessun nuovo meccanismo,
solo lo stesso content_digest (gia' su ImageOccurrencePrimitive, popolato end-to-end da
pymupdf_capture.py/primitive_normalizer.py) raggruppato per candidate page_edge_visual
attraverso l'intero documento.

Non fa parte del repository, non modifica nulla, non fa commit, non passa dal job
system. Replica le guardie pagina di job_page_analysis_runner.py (rotation != 0,
mediabox != cropbox). Le candidate 'drawing' restano solo contate, mai raggruppate per
identita' (nessun campo di identita' di contenuto per DrawingPrimitive in
primitive_model.py, limite gia' noto).

Uso:
    python3 verify_page_edge_visual_content_digest_recurrence.py \
        --dag Dag.pdf --vil Vil.pdf --db DB.pdf --kul Kul.pdf
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import fitz

from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page


def _scan_manual(label: str, source_path: Path) -> None:
    document = fitz.open(source_path)
    try:
        page_count = document.page_count
        digest_pages: dict[str, set[int]] = defaultdict(set)
        no_digest_image_pages: list[int] = []
        drawing_candidate_pages: list[int] = []
        guard_skipped_pages: list[tuple[int, str]] = []
        error_pages: list[tuple[int, str]] = []

        for page_index in range(page_count):
            page_num = page_index + 1
            page = document.load_page(page_index)

            if page.rotation != 0:
                guard_skipped_pages.append((page_num, f"rotation={page.rotation}"))
                continue
            if page.mediabox != page.cropbox:
                guard_skipped_pages.append(
                    (page_num, f"mediabox={page.mediabox} cropbox={page.cropbox}")
                )
                continue

            try:
                primitive_page = normalize_backend_page_capture(
                    capture_pymupdf_page(
                        page,
                        source_id=f"diagnostic:{label}",
                        page_id=f"page:{page_num:04d}",
                        capture_id=f"diagnostic:{label}:capture:page:{page_num:04d}",
                    )
                )
                analysis = build_page_edge_visual_page_analysis(
                    primitive_page,
                    generation_id=f"generation:edge-digest-scan:{label}:{page_num:04d}",
                )
            except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
                error_pages.append((page_num, str(exc)))
                continue

            image_primitives_by_id = {
                primitive.primitive_id: primitive for primitive in primitive_page.image_primitives
            }

            for candidate in analysis.candidates:
                if len(candidate.primitive_ids) != 1:
                    continue
                primitive_id = candidate.primitive_ids[0]
                image_primitive = image_primitives_by_id.get(primitive_id)
                if image_primitive is None:
                    drawing_candidate_pages.append(page_num)
                    continue
                if image_primitive.content_digest is None:
                    no_digest_image_pages.append(page_num)
                    continue
                digest_pages[image_primitive.content_digest].add(page_num)

        print(f"=== {label} ({page_count} pagine) ===")

        if guard_skipped_pages:
            print(f"  {len(guard_skipped_pages)} pagine saltate per guardia rotation/cropbox, es.:")
            for page_num, reason in guard_skipped_pages[:5]:
                print(f"    p.{page_num}: {reason}")

        if error_pages:
            print(f"  {len(error_pages)} pagine con errore di cattura/analisi, es.:")
            for page_num, message in error_pages[:5]:
                print(f"    p.{page_num}: {message}")

        sorted_digests = sorted(digest_pages.items(), key=lambda item: len(item[1]), reverse=True)
        if sorted_digests:
            print(
                f"  {len(sorted_digests)} content_digest distinti fra le candidate "
                f"page_edge_visual immagine:"
            )
        for digest, pages in sorted_digests:
            sample_pages = sorted(pages)
            shown = sample_pages[:8]
            suffix = "..." if len(sample_pages) > 8 else ""
            print(f"    digest {digest[:16]}... -> {len(pages)} pagine (es. {shown}{suffix})")

        if no_digest_image_pages:
            print(
                f"  {len(no_digest_image_pages)} candidate immagine senza content_digest "
                f"(pagine: {sorted(set(no_digest_image_pages))[:10]})"
            )
        if drawing_candidate_pages:
            print(
                f"  {len(drawing_candidate_pages)} candidate 'drawing' "
                f"(nessuna identita' di contenuto disponibile nello schema attuale; "
                f"pagine: {sorted(set(drawing_candidate_pages))[:10]})"
            )
        if not sorted_digests and not drawing_candidate_pages:
            print("  nessuna candidate page_edge_visual nell'intero documento")
    finally:
        document.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, default=Path("Dag.pdf"))
    parser.add_argument("--vil", type=Path, default=Path("Vil.pdf"))
    parser.add_argument("--db", type=Path, default=Path("DB.pdf"))
    parser.add_argument("--kul", type=Path, default=Path("Kul.pdf"))
    args = parser.parse_args()

    for label, source_path in (
        ("dag", args.dag),
        ("vil", args.vil),
        ("db", args.db),
        ("kul", args.kul),
    ):
        if not source_path.is_file():
            print(f"[{label}] file non trovato: {source_path} - saltato")
            continue
        _scan_manual(label, source_path)


if __name__ == "__main__":
    main()
