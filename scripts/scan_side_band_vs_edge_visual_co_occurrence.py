"""Standalone diagnostic: side_band vs page_edge_visual/page_covering_visual.

Non fa parte del repository, non modifica nulla, non fa commit, non passa dal job
system. Riusa esclusivamente contratti puri gia' ratificati (Milestone 6, 13-16):
per ogni pagina costruisce le quattro correnti singleton-side-band,
local-fragment-side-band, page-edge-visual, page-covering-visual sulla stessa
NormalizedPrimitivePage, le compone con build_co_referenced_page_analyses +
bind_co_referenced_page_analyses, e per le pagine dove compaiono candidate sia
dalla famiglia testuale (side_band) sia da quella visiva (edge/covering) misura
ogni coppia con measure_co_referenced_page_candidate_pair (gap/overlap/delta,
stessa API della Milestone 16). Nessun nuovo contratto, nessuna nuova regola
geometrica: solo composizione di API pubbliche esistenti su dati reali.

Replica le guardie pagina di job_page_analysis_runner.py (rotation != 0,
mediabox != cropbox): le pagine che le violerebbero vengono saltate.

Uso:
    python3 scan_side_band_vs_edge_visual_co_occurrence.py \
        --vil Vil.pdf --dag Dag.pdf --db DB.pdf --kul Kul.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz

from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_co_reference_candidate_pair_measurements import (
    measure_co_referenced_page_candidate_pair,
)
from page_analysis_co_reference_candidate_reference import (
    build_co_referenced_page_candidate_reference,
)
from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from page_analysis_side_band import (
    build_local_fragment_side_band_page_analysis,
    build_singleton_side_band_page_analysis,
)
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page


def _scan_manual(label: str, source_path: Path) -> None:
    document = fitz.open(source_path)
    try:
        page_count = document.page_count
        for page_index in range(page_count):
            page_num = page_index + 1
            page = document.load_page(page_index)

            if page.rotation != 0 or page.mediabox != page.cropbox:
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
                singleton_analysis = build_singleton_side_band_page_analysis(
                    primitive_page,
                    generation_id=f"generation:singleton:{label}:{page_num:04d}",
                )
                local_fragment_analysis = build_local_fragment_side_band_page_analysis(
                    primitive_page,
                    generation_id=f"generation:local-fragment:{label}:{page_num:04d}",
                )
                page_edge_analysis = build_page_edge_visual_page_analysis(
                    primitive_page,
                    generation_id=f"generation:page-edge:{label}:{page_num:04d}",
                )
                page_covering_analysis = build_page_covering_visual_page_analysis(
                    primitive_page,
                    generation_id=f"generation:page-covering:{label}:{page_num:04d}",
                )
            except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
                print(f"[{label} p.{page_num}] ERRORE: {exc}")
                continue

            singleton_count = len(singleton_analysis.candidates)
            local_fragment_count = len(local_fragment_analysis.candidates)
            page_edge_count = len(page_edge_analysis.candidates)
            page_covering_count = len(page_covering_analysis.candidates)

            if not (
                singleton_count or local_fragment_count or page_edge_count or page_covering_count
            ):
                continue

            print(
                f"[{label} p.{page_num}] singleton={singleton_count} "
                f"local_fragment={local_fragment_count} page_edge={page_edge_count} "
                f"page_covering={page_covering_count}"
            )

            side_band_family = [
                (singleton_analysis, candidate) for candidate in singleton_analysis.candidates
            ] + [
                (local_fragment_analysis, candidate)
                for candidate in local_fragment_analysis.candidates
            ]
            visual_family = [
                (page_edge_analysis, candidate) for candidate in page_edge_analysis.candidates
            ] + [
                (page_covering_analysis, candidate)
                for candidate in page_covering_analysis.candidates
            ]

            if not side_band_family or not visual_family:
                continue

            co_referenced = build_co_referenced_page_analyses(
                (
                    singleton_analysis,
                    local_fragment_analysis,
                    page_edge_analysis,
                    page_covering_analysis,
                )
            )
            bound = bind_co_referenced_page_analyses(
                primitive_page,
                co_referenced_page_analyses=co_referenced,
            )

            print(f"  >>> CO-OCCORRENZA [{label} p.{page_num}]")
            for side_analysis, side_candidate in side_band_family:
                side_reference = build_co_referenced_page_candidate_reference(
                    bound,
                    analysis=side_analysis,
                    candidate=side_candidate,
                )
                for visual_analysis, visual_candidate in visual_family:
                    visual_reference = build_co_referenced_page_candidate_reference(
                        bound,
                        analysis=visual_analysis,
                        candidate=visual_candidate,
                    )
                    measurement = measure_co_referenced_page_candidate_pair(
                        bound,
                        first_candidate_reference=side_reference,
                        second_candidate_reference=visual_reference,
                    )
                    print(
                        f"    {side_candidate.candidate_id} "
                        f"({side_candidate.proposed_structural_kind}) bbox="
                        f"{tuple(round(v, 1) for v in measurement.first_candidate_bbox)}  vs  "
                        f"{visual_candidate.candidate_id} "
                        f"({visual_candidate.proposed_structural_kind}) bbox="
                        f"{tuple(round(v, 1) for v in measurement.second_candidate_bbox)}"
                    )
                    print(
                        f"      gap=(h={measurement.horizontal_gap:.1f}, "
                        f"v={measurement.vertical_gap:.1f}) "
                        f"overlap=(h={measurement.horizontal_overlap:.1f}, "
                        f"v={measurement.vertical_overlap:.1f})"
                    )
    finally:
        document.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vil", type=Path, default=Path("Vil.pdf"))
    parser.add_argument("--dag", type=Path, default=Path("Dag.pdf"))
    parser.add_argument("--db", type=Path, default=Path("DB.pdf"))
    parser.add_argument("--kul", type=Path, default=Path("Kul.pdf"))
    args = parser.parse_args()

    for label, source_path in (
        ("vil", args.vil),
        ("dag", args.dag),
        ("db", args.db),
        ("kul", args.kul),
    ):
        if not source_path.is_file():
            print(f"[{label}] file non trovato: {source_path} - saltato")
            continue
        print(f"=== {label} ===")
        _scan_manual(label, source_path)


if __name__ == "__main__":
    main()
