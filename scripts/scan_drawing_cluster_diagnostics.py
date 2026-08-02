"""Verifica su manuali reali del clustering geometrico di Milestone 26.

Nessuna nuova logica: compone solo dump_drawing_cluster_diagnostics (Milestone 26).
Non fa parte del repository, non modifica nulla, non produce RegionCandidate/
PageAnalysis, non passa dal job. Replica le guardie pagina gia' usate negli altri
script di sessione (rotation != 0, mediabox != cropbox).

Riporta, per manuale: conteggio drawing grezzi vs. conteggio cluster (collasso),
distribuzione di dispersion_ratio, ed esempi dei cluster multi-membro con
dispersion_ratio piu' basso (i piu' sospetti di unione artificiosa/bridging) per
ispezione manuale -- non ci si ferma al solo conteggio aggregato, come richiesto
dalla revisione Chat B di Milestone 26.

I cluster multi-membro gia' classificati is_page_covering_visual o
is_page_edge_visual (dal modulo stesso) sono contati a parte e ESCLUSI dalla
lista dei sospetti: uno sfondo o una cornice fatti di molti tratti sottili ha
dispersion_ratio basso per natura (bbox-unione quasi a pagina intera, inchiostro
reale modesto) senza essere un caso di bridging -- includerli genererebbe rumore
sulla lista da ispezionare. Restano comunque visibili nei conteggi aggregati,
nessuna esclusione silenziosa.

Uso:
    python3 scripts/scan_drawing_cluster_diagnostics.py \
        --vil Vil.pdf --dag Dag.pdf --db DB.pdf --kul Kul.pdf --fab Fab.pdf \
        --lan Lan.pdf --apo Apo.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz

from page_analysis_drawing_cluster_diagnostics import dump_drawing_cluster_diagnostics
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page

_LOW_DISPERSION_THRESHOLD = 0.3


def _scan_manual(label: str, source_path: Path) -> None:
    document = fitz.open(source_path)
    try:
        page_count = document.page_count
        raw_drawing_count = 0
        cluster_count = 0
        multi_member_cluster_count = 0
        covering_or_edge_count = 0
        excluded_count = 0
        dispersion_values: list[float] = []
        low_dispersion_examples: list[tuple[int, list[str], float, int]] = []
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
                raw_drawing_count += len(primitive_page.drawing_primitives)
                result = dump_drawing_cluster_diagnostics(
                    primitive_page,
                    generation_id=f"generation:drawing-cluster-scan:{label}:{page_num:04d}",
                )
            except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
                error_pages.append((page_num, str(exc)))
                continue

            for cluster in result["clusters"]:
                cluster_count += 1
                if cluster["excluded_reason"] is not None:
                    excluded_count += 1
                    continue
                if cluster["primitive_count"] <= 1:
                    continue
                multi_member_cluster_count += 1
                if cluster["is_page_covering_visual"] or cluster["is_page_edge_visual"]:
                    covering_or_edge_count += 1
                    continue
                ratio = cluster["dispersion_ratio"]
                if ratio is None:
                    continue
                dispersion_values.append(ratio)
                if ratio < _LOW_DISPERSION_THRESHOLD:
                    low_dispersion_examples.append(
                        (
                            page_num,
                            cluster["drawing_primitive_ids"],
                            ratio,
                            cluster["primitive_count"],
                        )
                    )

        print(f"=== {label} ({page_count} pagine) ===")
        if guard_skipped:
            print(f"  {guard_skipped} pagine saltate per guardia rotation/cropbox")
        if error_pages:
            print(f"  {len(error_pages)} pagine con errore, es.: {error_pages[:5]}")

        print(f"  {raw_drawing_count} drawing grezzi -> {cluster_count} cluster totali")
        print(
            f"  {excluded_count} cluster esclusi dal pre-filtro (tiny/border_like), "
            f"{multi_member_cluster_count} cluster multi-membro"
        )
        print(
            f"  di cui {covering_or_edge_count} gia' is_page_covering_visual/"
            f"is_page_edge_visual (esclusi dai sospetti, dispersion bassa attesa per natura)"
        )
        if dispersion_values:
            average = sum(dispersion_values) / len(dispersion_values)
            below_threshold = sum(1 for v in dispersion_values if v < _LOW_DISPERSION_THRESHOLD)
            print(
                f"  dispersion_ratio medio sui cluster residual interior visual: {average:.3f}; "
                f"{below_threshold}/{len(dispersion_values)} sotto {_LOW_DISPERSION_THRESHOLD} "
                f"(sospetti di unione dispersa/bridging, da ispezionare)"
            )
        if low_dispersion_examples:
            low_dispersion_examples.sort(key=lambda item: item[2])
            print(f"  {len(low_dispersion_examples)} cluster con dispersion_ratio piu' basso, es.:")
            for page_num, primitive_ids, ratio, count in low_dispersion_examples[:10]:
                print(
                    f"    p.{page_num} dispersion_ratio={ratio:.3f} "
                    f"({count} membri): {primitive_ids}"
                )
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
