"""Censimento delle visuali interne (layout.embedded_visual candidato futuro, non
ancora un producer) su manuali interi, usando solo lo stage diagnostico Milestone 25
(`page_analysis_interior_visual_diagnostics.dump_interior_visual_diagnostics`).

Nessuna nuova regola geometrica: compone solo la funzione gia' committata in
Milestone 25 (page_analysis_interior_visual_diagnostics.py). Non fa parte del
repository, non modifica nulla, non produce RegionCandidate/PageAnalysis, non passa
dal job. Replica le guardie pagina gia' usate negli altri script di sessione
(rotation != 0, mediabox != cropbox).

Per ogni manuale riporta: pagine scansionate, conteggio totale di visuali "residue"
(ne' page_covering ne' page_edge), quante hanno un content_digest ricorrente su piu'
pagine (sfondo/decorazione ripetuta, stesso meccanismo gia' validato per
page_covering_visual) rispetto a quante sono uniche (candidate a illustrazione
reale), e un elenco separato delle residue con contained_text_primitive_count > 0
(segnale di possibile box/callout, il piu' interessante per un futuro producer).

Uso:
    python3 scripts/scan_interior_visual_diagnostics.py \
        --vil Vil.pdf --dag Dag.pdf --db DB.pdf --kul Kul.pdf --fab Fab.pdf \
        --lan Lan.pdf --apo Apo.pdf
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import fitz

from page_analysis_interior_visual_diagnostics import dump_interior_visual_diagnostics
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page


def _scan_manual(label: str, source_path: Path) -> None:
    document = fitz.open(source_path)
    try:
        page_count = document.page_count
        residual_count = 0
        digest_pages: dict[str, set[int]] = defaultdict(set)
        no_digest_residual_pages: list[int] = []
        contained_text_examples: list[tuple[int, str, int, float]] = []
        guard_skipped = 0
        error_pages: list[tuple[int, str]] = []

        for page_index in range(page_count):
            page_num = page_index + 1
            page = document.load_page(page_index)

            if page.rotation != 0 or page.mediabox != page.cropbox:
                guard_skipped += 1
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
                result = dump_interior_visual_diagnostics(
                    primitive_page,
                    generation_id=f"generation:interior-visual-scan:{label}:{page_num:04d}",
                )
            except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
                error_pages.append((page_num, str(exc)))
                continue

            for visual in result["visuals"]:
                if not visual["is_residual_interior_visual"]:
                    continue
                residual_count += 1
                digest = visual["content_digest"]
                if digest is None:
                    no_digest_residual_pages.append(page_num)
                else:
                    digest_pages[digest].add(page_num)

                contained_count = visual["contained_text_primitive_count"]
                if contained_count > 0:
                    contained_text_examples.append(
                        (
                            page_num,
                            visual["primitive_id"],
                            contained_count,
                            visual["contained_text_area_ratio"],
                        )
                    )

        print(f"=== {label} ({page_count} pagine) ===")
        if guard_skipped:
            print(f"  {guard_skipped} pagine saltate per guardia rotation/cropbox")
        if error_pages:
            print(f"  {len(error_pages)} pagine con errore, es.: {error_pages[:5]}")

        print(f"  {residual_count} visuali residue totali (ne' covering ne' edge)")

        sorted_digests = sorted(digest_pages.items(), key=lambda item: len(item[1]), reverse=True)
        recurring = [d for d in sorted_digests if len(d[1]) > 1]
        unique = [d for d in sorted_digests if len(d[1]) == 1]
        print(
            f"  {len(recurring)} content_digest ricorrenti (>1 pagina, probabile "
            f"decorazione/sfondo), {len(unique)} content_digest su una sola pagina "
            f"(candidate a illustrazione unica), {len(no_digest_residual_pages)} "
            f"residue senza content_digest (drawing, nessuna identita' disponibile)"
        )
        for digest, pages in recurring[:5]:
            sample = sorted(pages)[:8]
            print(f"    ricorrente {digest[:16]}... -> {len(pages)} pagine (es. {sample})")

        if contained_text_examples:
            print(
                f"  {len(contained_text_examples)} visuali residue con testo "
                f"contenuto (possibile box/callout), es.:"
            )
            for page_num, primitive_id, count, ratio in contained_text_examples[:10]:
                print(
                    f"    p.{page_num} {primitive_id}: {count} primitive testo, "
                    f"area_ratio={ratio:.3f}"
                )
        else:
            print("  nessuna visuale residua con testo contenuto")
    finally:
        document.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vil", type=Path, default=Path("Vil.pdf"))
    parser.add_argument("--dag", type=Path, default=Path("Dag.pdf"))
    parser.add_argument("--db", type=Path, default=Path("DB.pdf"))
    parser.add_argument("--kul", type=Path, default=Path("Kul.pdf"))
    parser.add_argument("--fab", type=Path, default=Path("Fab.pdf"))
    parser.add_argument("--lan", type=Path, default=Path("Lan.pdf"))
    parser.add_argument("--apo", type=Path, default=Path("Apo.pdf"))
    args = parser.parse_args()

    for label, source_path in (
        ("vil", args.vil),
        ("dag", args.dag),
        ("db", args.db),
        ("kul", args.kul),
        ("fab", args.fab),
        ("lan", args.lan),
        ("apo", args.apo),
    ):
        if not source_path.is_file():
            print(f"[{label}] file non trovato: {source_path} - saltato")
            continue
        _scan_manual(label, source_path)


if __name__ == "__main__":
    main()
