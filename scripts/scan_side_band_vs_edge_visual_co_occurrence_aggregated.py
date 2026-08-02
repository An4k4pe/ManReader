"""Aggregated version of scan_side_band_vs_edge_visual_co_occurrence.py.

Stessa composizione di API ratificate (Milestone 6, 13-16), ma non stampa una riga
per ogni coppia: classifica ogni coppia side_band x visual in una delle tre
categorie -- "contained" (bbox side_band interamente dentro la bbox visiva, entro
una tolleranza), "overlapping" (intersezione parziale) o "disjoint" (nessuna
intersezione, gap positivo su almeno un asse) -- e conta le occorrenze per
(manuale, produttore side_band, kind visivo, categoria), con un piccolo campione
di pagine per gruppo invece di ogni singola occorrenza.

"contained"/"overlapping"/"disjoint" sono categorie di QUESTO script diagnostico,
derivate localmente dalle bbox gia' esposte da CoReferencedPageCandidatePairMeasurements
(Milestone 16). Non sono contratti pubblici e non modificano ne' estendono
measure_co_referenced_page_candidate_pair, che resta invariata e priva di
containment/ratio per decisione esplicita di quella milestone.

Uso:
    python3 scan_side_band_vs_edge_visual_co_occurrence_aggregated.py \
        --vil Vil.pdf --dag Dag.pdf --db DB.pdf --kul Kul.pdf
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import fitz

from geometry_model import BBox
from page_analysis_co_reference import build_co_referenced_page_analyses
from page_analysis_co_reference_binding import bind_co_referenced_page_analyses
from page_analysis_co_reference_candidate_pair_measurements import (
    measure_co_referenced_page_candidate_pair,
)
from page_analysis_co_reference_candidate_reference import (
    build_co_referenced_page_candidate_reference,
)
from page_analysis_model import PageAnalysis, RegionCandidate
from page_analysis_page_covering_visual import build_page_covering_visual_page_analysis
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis
from page_analysis_side_band import (
    build_local_fragment_side_band_page_analysis,
    build_singleton_side_band_page_analysis,
)
from primitive_normalizer import normalize_backend_page_capture
from pymupdf_capture import capture_pymupdf_page

_CONTAINMENT_TOLERANCE = 0.5


def _classify(
    *,
    side_bbox: BBox,
    visual_bbox: BBox,
    horizontal_overlap: float,
    vertical_overlap: float,
) -> str:
    if horizontal_overlap <= 0.0 or vertical_overlap <= 0.0:
        return "disjoint"

    contained = (
        side_bbox[0] >= visual_bbox[0] - _CONTAINMENT_TOLERANCE
        and side_bbox[1] >= visual_bbox[1] - _CONTAINMENT_TOLERANCE
        and side_bbox[2] <= visual_bbox[2] + _CONTAINMENT_TOLERANCE
        and side_bbox[3] <= visual_bbox[3] + _CONTAINMENT_TOLERANCE
    )
    return "contained" if contained else "overlapping"


def _scan_manual(
    label: str,
    source_path: Path,
    counts: dict[tuple[str, str, str, str], int],
    examples: dict[tuple[str, str, str, str], list[int]],
) -> None:
    document = fitz.open(source_path)
    try:
        page_count = document.page_count
        co_occurrence_pages = 0
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

            side_band_family: list[tuple[str, PageAnalysis, RegionCandidate]] = [
                ("singleton", singleton_analysis, candidate)
                for candidate in singleton_analysis.candidates
            ] + [
                ("local-fragment", local_fragment_analysis, candidate)
                for candidate in local_fragment_analysis.candidates
            ]
            visual_family: list[tuple[PageAnalysis, RegionCandidate]] = [
                (page_edge_analysis, candidate) for candidate in page_edge_analysis.candidates
            ] + [
                (page_covering_analysis, candidate)
                for candidate in page_covering_analysis.candidates
            ]

            if not side_band_family or not visual_family:
                continue

            co_occurrence_pages += 1
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

            for side_producer, side_analysis, side_candidate in side_band_family:
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
                    category = _classify(
                        side_bbox=measurement.first_candidate_bbox,
                        visual_bbox=measurement.second_candidate_bbox,
                        horizontal_overlap=measurement.horizontal_overlap,
                        vertical_overlap=measurement.vertical_overlap,
                    )
                    key = (
                        side_producer,
                        visual_candidate.proposed_structural_kind,
                        category,
                        label,
                    )
                    counts[key] += 1
                    page_list = examples[key]
                    if page_num not in page_list and len(page_list) < 5:
                        page_list.append(page_num)

        print(f"[{label}] {page_count} pagine, {co_occurrence_pages} con co-occorrenza")
    finally:
        document.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vil", type=Path, default=Path("Vil.pdf"))
    parser.add_argument("--dag", type=Path, default=Path("Dag.pdf"))
    parser.add_argument("--db", type=Path, default=Path("DB.pdf"))
    parser.add_argument("--kul", type=Path, default=Path("Kul.pdf"))
    parser.add_argument("--fab", type=Path, default=Path("Fab.pdf"))
    args = parser.parse_args()

    counts: dict[tuple[str, str, str, str], int] = defaultdict(int)
    examples: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)

    for label, source_path in (
        ("vil", args.vil),
        ("dag", args.dag),
        ("db", args.db),
        ("kul", args.kul),
        ("fab", args.fab),
    ):
        if not source_path.is_file():
            print(f"[{label}] file non trovato: {source_path} - saltato")
            continue
        _scan_manual(label, source_path, counts, examples)

    print()
    print("=== riepilogo coppie side_band x visual, per categoria ===")
    for key in sorted(counts, key=lambda item: (-counts[item], item)):
        side_producer, visual_kind, category, label = key
        count = counts[key]
        page_sample = examples[key]
        print(
            f"[{label}] {side_producer} vs {visual_kind}: {category} -> {count} coppie "
            f"(es. pagine {page_sample})"
        )


if __name__ == "__main__":
    main()
