"""Cross-producer coverage of unresolved embedded_visual candidates.

Diagnostico soltanto: nessun producer nuovo, nessuna regola, nessuna soglia,
nessuna decisione, nessuna scrittura fuori dal JSONL richiesto.

Domanda: delle candidate `layout.embedded_visual` che Resolution lascia
irrisolte, quante stanno gia' sotto una candidate proposta da un altro dei
cinque producer wired nel job? Il prototipo di Milestone 34
(`prototype_resolve_page_candidates_real_pages.py`) ne costruisce due soltanto,
`embedded_visual` e `interior_visual_frame`, quindi la domanda non e' mai stata
misurata. `table_candidate`, `page_covering_visual` e `page_edge_visual` non
sono mai entrati nel confronto.

Per ogni pagina costruisce tutti e cinque i producer sulla stessa
`NormalizedPrimitivePage`, li lega con il sottosistema Milestone 13-19,
applica `resolve_page_candidates` (Milestone 34, regola unica IVF/EV) e, per
ogni candidate `embedded_visual` rimasta `unresolved`, riporta quanta della
propria area e' coperta dalla candidate piu' sovrapposta di ciascun altro
producer.

La copertura riportata e' `overlap_area / area della candidate embedded_visual`,
non `overlap_area / min(area1, area2)` di
`measure_co_referenced_page_candidate_overlap_ratio` (Milestone 34): la domanda
qui e' "quanto di QUESTA candidate e' gia' letto da un altro", che e' asimmetrica.
Il numeratore e' identico, `horizontal_overlap * vertical_overlap`, ed e'
calcolato in linea per costo: sulla prima pagina utile lo script riverifica
tutte le coppie contro la funzione di produzione e riporta eventuali
discordanze, invece di dare per buona l'equivalenza.

Non usa `bind_pymupdf_pdfplumber_document_source` (richiede un riferimento di
file verificato e un contesto di job): apre fitz e pdfplumber dal percorso, come
il prototipo standalone di Milestone 20. Nessuna attestazione, nessun job,
nessuna persistenza.

Uso, dalla radice del repository:

    python3 scripts/measure_cross_producer_candidate_coverage.py \
        --sample-jsonl /percorso/proto_sample40.jsonl \
        --pdf kul=Kul.pdf --pdf fab=Fab.pdf --pdf db=DB.pdf \
        --output /tmp/cross_producer.jsonl

Le pagine non vengono estratte di nuovo: sono lette dal JSONL del campione
casuale gia' registrato, cosi' il confronto avviene sullo stesso campione.

Controllo di permutazione (opt-in, `--permutations N`, default 0 = comportamento
invariato). Domanda: il tasso di copertura osservato per una candidate
`embedded_visual` irrisolta e' sopra il tasso di base atteso per pura
geometria (candidate grandi che coprono per caso una frazione ampia della
pagina), oppure no? Per ogni pagina e ripetizione, le candidate irrisolte
vengono ricollocate a caso (nullo A, posizione libera; nullo B, stessa fascia
`y0`/`y1`, solo `x` libero), preservando larghezza e altezza, e la copertura
e' ricalcolata con la stessa formula contro le candidate NON permutate degli
altri producer. `resolve_page_candidates` non viene mai rieseguito sulla
geometria permutata: l'insieme delle candidate irrisolte resta quello deciso
sui dati reali, la permutazione agisce solo a valle sul calcolo di copertura.
Preregistrato in `Prereg_ContenimentoIVF_EV_v1.md` (non nel repo, stessa
prassi di Milestone 33/34/35). Nessun producer, nessuna regola, nessuna
soglia in codice di produzione: la soglia 0.9 usata per riportare
`covered_ge_09` e' solo di questo script diagnostico.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import cast

import fitz
import pdfplumber
from pdfplumber.page import Page as PlumberPage
from pdfplumber.pdf import PDF as PlumberPDF

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from page_analysis_co_reference import build_co_referenced_page_analyses  # noqa: E402
from page_analysis_co_reference_binding import (  # noqa: E402
    BoundCoReferencedPageAnalyses,
    bind_co_referenced_page_analyses,
)
from page_analysis_co_reference_candidate_overlap_ratio_measurements import (  # noqa: E402
    measure_co_referenced_page_candidate_overlap_ratio,
)
from page_analysis_co_reference_candidate_reference import (  # noqa: E402
    build_co_referenced_page_candidate_reference,
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
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_page_candidates import resolve_page_candidates  # noqa: E402

_EMBEDDED_VISUAL_PRODUCER = "page_analysis.embedded_visual"
_INTERIOR_VISUAL_FRAME_PRODUCER = "page_analysis.interior_visual_frame"
_TABLE_CANDIDATE_PRODUCER = "table_candidate"
_PERMUTATION_COVERAGE_THRESHOLD = 0.9
_BOOTSTRAP_REPETITIONS = 1000


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH, for example kul=/path/Kul.pdf")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "For every unresolved embedded_visual candidate, report how much of its area "
            "is already covered by the most overlapping candidate of each other producer."
        ),
    )
    parser.add_argument(
        "--pdf",
        action="append",
        default=[],
        type=_parse_labelled_path,
        metavar="LABEL=PATH",
        help="A PDF to process. Repeatable.",
    )
    parser.add_argument(
        "--sample-jsonl",
        type=Path,
        required=True,
        help="JSONL produced by sample_resolution_prototype_pages.py.",
    )
    parser.add_argument("--output", type=Path, required=True, help="JSONL to write.")
    parser.add_argument(
        "--permutations",
        type=int,
        default=0,
        help=(
            "Number of permutation-null repetitions per page. 0 (default) runs no "
            "permutation and leaves the JSONL output unchanged."
        ),
    )
    parser.add_argument(
        "--permutation-seed",
        type=str,
        default="20260804",
        help="Deterministic seed for the permutation nulls and the bootstrap CI.",
    )
    return parser


def _read_sample_pages(sample_path: Path) -> dict[str, list[int]]:
    pages: dict[str, list[int]] = defaultdict(list)
    with sample_path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            record = cast(dict[str, object], json.loads(stripped))
            label = cast(str, record.get("sample_label", ""))
            page_input = cast(dict[str, object], record.get("input", {}))
            page_number = page_input.get("page_number")
            if label and isinstance(page_number, int):
                pages[label].append(page_number)
    return {label: sorted(set(values)) for label, values in pages.items()}


def _area(bbox: BBox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _overlap_area(first: BBox, second: BBox) -> float:
    horizontal = min(first[2], second[2]) - max(first[0], second[0])
    vertical = min(first[3], second[3]) - max(first[1], second[1])
    if horizontal <= 0.0 or vertical <= 0.0:
        return 0.0
    return horizontal * vertical


def _relocate_candidate_bbox(
    bbox: BBox,
    *,
    page_width: float,
    page_height: float,
    rng: random.Random,
    randomize_y: bool,
) -> BBox | None:
    """Relocate one bbox to a random position, preserving width/height exactly.

    Returns None (candidate left in place, counted as skipped by the caller)
    when the candidate is wider or taller than the page: no silent exclusion,
    just no relocation to attempt.
    """

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width > page_width or height > page_height:
        return None

    x0 = rng.uniform(0.0, page_width - width)
    y0 = rng.uniform(0.0, page_height - height) if randomize_y else bbox[1]
    relocated: BBox = (x0, y0, x0 + width, y0 + height)

    assert abs((relocated[2] - relocated[0]) - width) < 1e-9, "relocated width mismatch"
    assert abs((relocated[3] - relocated[1]) - height) < 1e-9, "relocated height mismatch"
    assert (
        relocated[0] >= -1e-9
        and relocated[1] >= -1e-9
        and relocated[2] <= page_width + 1e-9
        and relocated[3] <= page_height + 1e-9
    ), "relocated bbox escapes the page rectangle"

    return relocated


def _count_unrelocatable(
    candidates: list[RegionCandidate],
    *,
    page_width: float,
    page_height: float,
) -> int:
    return sum(
        1
        for candidate in candidates
        if (candidate.bbox[2] - candidate.bbox[0]) > page_width
        or (candidate.bbox[3] - candidate.bbox[1]) > page_height
    )


def _permutation_repetition(
    candidates: list[RegionCandidate],
    *,
    others: list[PageAnalysis],
    page_width: float,
    page_height: float,
    rng: random.Random,
    randomize_y: bool,
) -> dict[str, object]:
    covered_ge_09 = {analysis.provenance.producer_name: 0 for analysis in others}
    for candidate in candidates:
        candidate_area = _area(candidate.bbox)
        relocated = _relocate_candidate_bbox(
            candidate.bbox,
            page_width=page_width,
            page_height=page_height,
            rng=rng,
            randomize_y=randomize_y,
        )
        if relocated is None:
            relocated = candidate.bbox
        for analysis in others:
            ratios = [
                _overlap_area(relocated, other.bbox) / candidate_area
                for other in analysis.candidates
            ]
            best = max(ratios) if ratios else 0.0
            if best >= _PERMUTATION_COVERAGE_THRESHOLD:
                covered_ge_09[analysis.provenance.producer_name] += 1
    return {"unresolved": len(candidates), "covered_ge_09": covered_ge_09}


def _union_area_fraction(
    bboxes: list[BBox],
    *,
    page_width: float,
    page_height: float,
) -> float:
    """Fraction of the page rectangle covered by the union of bboxes.

    Computed by coordinate compression (unique sorted x/y boundaries, cells
    marked as covered if their center falls inside any bbox), not by summing
    individual areas -- summation would double-count overlaps.
    """

    page_area = page_width * page_height
    if not bboxes or page_area <= 0.0:
        return 0.0

    xs = sorted({bbox[0] for bbox in bboxes} | {bbox[2] for bbox in bboxes})
    ys = sorted({bbox[1] for bbox in bboxes} | {bbox[3] for bbox in bboxes})

    covered_area = 0.0
    for x_index in range(len(xs) - 1):
        x0, x1 = xs[x_index], xs[x_index + 1]
        cell_width = x1 - x0
        if cell_width <= 0.0:
            continue
        for y_index in range(len(ys) - 1):
            y0, y1 = ys[y_index], ys[y_index + 1]
            cell_height = y1 - y0
            if cell_height <= 0.0:
                continue
            center_x = (x0 + x1) / 2.0
            center_y = (y0 + y1) / 2.0
            if any(
                bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]
                for bbox in bboxes
            ):
                covered_area += cell_width * cell_height

    return covered_area / page_area


def _build_all_analyses(
    primitive_page: NormalizedPrimitivePage,
    *,
    plumber_page: PlumberPage,
    generation_id: str,
) -> tuple[PageAnalysis, ...]:
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


def _verify_against_production(
    bound: BoundCoReferencedPageAnalyses,
    analyses: tuple[PageAnalysis, ...],
    embedded: PageAnalysis,
) -> tuple[int, int]:
    """Recompute every pair with the committed function; return (checked, mismatches)."""

    checked = 0
    mismatches = 0
    for embedded_candidate in embedded.candidates:
        first_reference = build_co_referenced_page_candidate_reference(
            bound,
            analysis=embedded,
            candidate=embedded_candidate,
        )
        for analysis in analyses:
            if analysis is embedded:
                continue
            for candidate in analysis.candidates:
                second_reference = build_co_referenced_page_candidate_reference(
                    bound,
                    analysis=analysis,
                    candidate=candidate,
                )
                try:
                    production = measure_co_referenced_page_candidate_overlap_ratio(
                        bound,
                        first_candidate_reference=first_reference,
                        second_candidate_reference=second_reference,
                    )
                except ValueError:
                    continue
                inline = _overlap_area(embedded_candidate.bbox, candidate.bbox)
                checked += 1
                if abs(inline - production.overlap_area) > 1e-6:
                    mismatches += 1
    return checked, mismatches


def _page_record(
    *,
    label: str,
    page_number: int,
    fitz_document: fitz.Document,
    plumber_pdf: PlumberPDF,
    verify: bool,
    permutations: int = 0,
    permutation_seed: str = "20260804",
) -> dict[str, object]:
    record: dict[str, object] = {"sample_label": label, "page_number": page_number}
    page = fitz_document.load_page(page_number - 1)
    if page.rotation != 0:
        record["category"] = "PRECONDITION_FAIL"
        record["message"] = "rotation must be 0"
        return record
    if page.mediabox != page.cropbox:
        record["category"] = "PRECONDITION_FAIL"
        record["message"] = "cropbox != mediabox"
        return record

    generation_id = f"generation:cross:{label}:{page_number:04d}"
    primitive_page = normalize_backend_page_capture(
        capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{page_number:04d}",
            capture_id=f"diagnostic:cross:page:{page_number:04d}",
        )
    )
    analyses = _build_all_analyses(
        primitive_page,
        plumber_page=plumber_pdf.pages[page_number - 1],
        generation_id=generation_id,
    )
    record["candidate_counts"] = {
        analysis.provenance.producer_name: len(analysis.candidates) for analysis in analyses
    }

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
    record["outcome_counts"] = {
        outcome: sum(1 for value in outcome_by_candidate.values() if value == outcome)
        for outcome in ("accepted", "rejected", "unresolved")
    }

    embedded = next(
        analysis
        for analysis in analyses
        if analysis.provenance.producer_name == _EMBEDDED_VISUAL_PRODUCER
    )
    others = [analysis for analysis in analyses if analysis is not embedded]

    coverage_rows: list[dict[str, object]] = []
    for candidate in embedded.candidates:
        key = (_EMBEDDED_VISUAL_PRODUCER, candidate.candidate_id)
        if outcome_by_candidate.get(key) != "unresolved":
            continue
        candidate_area = _area(candidate.bbox)
        if candidate_area <= 0.0:
            continue
        best: dict[str, float] = {}
        for analysis in others:
            ratios = [
                _overlap_area(candidate.bbox, other.bbox) / candidate_area
                for other in analysis.candidates
            ]
            best[analysis.provenance.producer_name] = max(ratios) if ratios else 0.0
        coverage_rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "area": candidate_area,
                "coverage": best,
            }
        )
    record["unresolved_embedded_visual"] = coverage_rows

    if permutations > 0:
        page_width = primitive_page.page_geometry.width
        page_height = primitive_page.page_geometry.height
        record["page_width"] = page_width
        record["page_height"] = page_height

        frame_analysis = next(
            analysis
            for analysis in analyses
            if analysis.provenance.producer_name == _INTERIOR_VISUAL_FRAME_PRODUCER
        )
        record["interior_visual_frame_page_area_fraction"] = _union_area_fraction(
            [candidate.bbox for candidate in frame_analysis.candidates],
            page_width=page_width,
            page_height=page_height,
        )

        unresolved_ev_candidates: list[RegionCandidate] = []
        for candidate in embedded.candidates:
            key = (_EMBEDDED_VISUAL_PRODUCER, candidate.candidate_id)
            if outcome_by_candidate.get(key) != "unresolved":
                continue
            if _area(candidate.bbox) <= 0.0:
                continue
            unresolved_ev_candidates.append(candidate)

        record["permutation_skipped"] = _count_unrelocatable(
            unresolved_ev_candidates,
            page_width=page_width,
            page_height=page_height,
        )

        null_uniform: list[dict[str, object]] = []
        null_same_row: list[dict[str, object]] = []
        for repetition in range(permutations):
            uniform_rng = random.Random(
                f"{permutation_seed}:{label}:{page_number}:null_uniform:{repetition}"
            )
            null_uniform.append(
                _permutation_repetition(
                    unresolved_ev_candidates,
                    others=others,
                    page_width=page_width,
                    page_height=page_height,
                    rng=uniform_rng,
                    randomize_y=True,
                )
            )
            same_row_rng = random.Random(
                f"{permutation_seed}:{label}:{page_number}:null_same_row:{repetition}"
            )
            null_same_row.append(
                _permutation_repetition(
                    unresolved_ev_candidates,
                    others=others,
                    page_width=page_width,
                    page_height=page_height,
                    rng=same_row_rng,
                    randomize_y=False,
                )
            )

        record["permutation"] = {
            "seed": permutation_seed,
            "repetitions": permutations,
            "null_uniform": null_uniform,
            "null_same_row": null_same_row,
        }

    if verify:
        checked, mismatches = _verify_against_production(bound, analyses, embedded)
        record["verification"] = {"pairs_checked": checked, "mismatches": mismatches}

    record["category"] = "PASS"
    return record


def _bootstrap_ci_95(
    page_pairs: list[tuple[int, int]],
    *,
    seed: str,
    label: str,
    producer_name: str,
) -> tuple[float, float] | None:
    """Per-page bootstrap 95% CI on the observed coverage rate.

    page_pairs is one (unresolved, covered) pair per page. Resamples pages
    with replacement, 1000 repetitions, same seed as the permutation nulls.
    """

    if not page_pairs:
        return None

    rng = random.Random(f"{seed}:bootstrap:{label}:{producer_name}")
    rates: list[float] = []
    for _ in range(_BOOTSTRAP_REPETITIONS):
        sample = rng.choices(page_pairs, k=len(page_pairs))
        total_unresolved = sum(unresolved for unresolved, _ in sample)
        total_covered = sum(covered for _, covered in sample)
        if total_unresolved > 0:
            rates.append(total_covered / total_unresolved)

    if not rates:
        return None
    rates.sort()
    low_index = min(len(rates) - 1, max(0, round(0.025 * (len(rates) - 1))))
    high_index = min(len(rates) - 1, max(0, round(0.975 * (len(rates) - 1))))
    return rates[low_index], rates[high_index]


def _print_summary(
    page_summaries: dict[str, list[dict[str, object]]],
    *,
    permutations: int,
    seed: str,
) -> None:
    for label in sorted(page_summaries):
        pages = page_summaries[label]
        mean_area_fraction = (
            sum(cast(float, page["area_fraction"]) for page in pages) / len(pages)
            if pages
            else 0.0
        )
        print(f"=== {label} ===", file=sys.stderr)
        for null_name in ("null_uniform", "null_same_row"):
            print(f"  {null_name}:", file=sys.stderr)
            for producer_name in (_INTERIOR_VISUAL_FRAME_PRODUCER, _TABLE_CANDIDATE_PRODUCER):
                total_unresolved = sum(cast(int, page["unresolved"]) for page in pages)
                total_observed_covered = sum(
                    cast(dict[str, int], page["observed_covered_ge_09"]).get(producer_name, 0)
                    for page in pages
                )
                observed_rate = (
                    total_observed_covered / total_unresolved if total_unresolved > 0 else None
                )

                repetition_rates: list[float] = []
                for repetition in range(permutations):
                    rep_unresolved = 0
                    rep_covered = 0
                    for page in pages:
                        page_permutation = cast(dict[str, object], page["permutation"])
                        entry = cast(
                            list[dict[str, object]], page_permutation[null_name]
                        )[repetition]
                        rep_unresolved += cast(int, entry["unresolved"])
                        rep_covered += cast(dict[str, int], entry["covered_ge_09"]).get(
                            producer_name, 0
                        )
                    if rep_unresolved > 0:
                        repetition_rates.append(rep_covered / rep_unresolved)
                permuted_mean_rate = (
                    sum(repetition_rates) / len(repetition_rates) if repetition_rates else None
                )

                if observed_rate is None or permuted_mean_rate is None:
                    enrichment: float | str = "n/a"
                elif permuted_mean_rate == 0.0:
                    enrichment = "n/a"
                else:
                    enrichment = observed_rate / permuted_mean_rate

                page_pairs = [
                    (
                        cast(int, page["unresolved"]),
                        cast(dict[str, int], page["observed_covered_ge_09"]).get(
                            producer_name, 0
                        ),
                    )
                    for page in pages
                ]
                ci = _bootstrap_ci_95(page_pairs, seed=seed, label=label, producer_name=producer_name)

                print(
                    f"    {producer_name}: unresolved={total_unresolved} "
                    f"observed_rate={observed_rate} permuted_mean_rate={permuted_mean_rate} "
                    f"enrichment={enrichment} ci95={ci} "
                    f"mean_interior_visual_frame_page_area_fraction={mean_area_fraction}",
                    file=sys.stderr,
                )


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdfs = cast(list[tuple[str, Path]], args.pdf)
    sample_path = cast(Path, args.sample_jsonl)
    output_path = cast(Path, args.output)
    permutations = cast(int, args.permutations)
    permutation_seed = cast(str, args.permutation_seed)

    if not pdfs:
        print("at least one --pdf LABEL=PATH is required", file=sys.stderr)
        return 1
    if not sample_path.is_file():
        print(f"sample JSONL not found: {sample_path}", file=sys.stderr)
        return 1

    sample_pages = _read_sample_pages(sample_path)
    verify_pending = True
    written = 0
    summary_data: dict[str, list[dict[str, object]]] = defaultdict(list)

    with output_path.open("w", encoding="utf-8") as handle:
        for label, pdf_path in pdfs:
            pages = sample_pages.get(label, [])
            if not pages:
                print(f"[{label}] nessuna pagina nel campione - saltato", file=sys.stderr)
                continue
            if not pdf_path.is_file():
                print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
                continue
            print(f"[{label}] {len(pages)} pagine dal campione", file=sys.stderr)
            with (
                fitz.open(pdf_path) as fitz_document,
                pdfplumber.open(str(pdf_path)) as plumber_pdf,
            ):
                for page_number in pages:
                    try:
                        record = _page_record(
                            label=label,
                            page_number=page_number,
                            fitz_document=fitz_document,
                            plumber_pdf=plumber_pdf,
                            verify=verify_pending,
                            permutations=permutations,
                            permutation_seed=permutation_seed,
                        )
                    except Exception as exc:  # noqa: BLE001
                        record = {
                            "sample_label": label,
                            "page_number": page_number,
                            "category": "OPERATIONAL_ERROR",
                            "message": f"{type(exc).__name__}: {exc}",
                        }
                    if record.get("category") == "PASS" and verify_pending:
                        verify_pending = False
                        print(
                            f"   verifica su p.{page_number}: {record.get('verification')}",
                            file=sys.stderr,
                        )
                    if permutations > 0 and record.get("category") == "PASS":
                        coverage_rows = cast(
                            list[dict[str, object]], record["unresolved_embedded_visual"]
                        )
                        observed_covered_ge_09: dict[str, int] = defaultdict(int)
                        for row in coverage_rows:
                            coverage = cast(dict[str, float], row["coverage"])
                            for producer_name, ratio in coverage.items():
                                if ratio >= _PERMUTATION_COVERAGE_THRESHOLD:
                                    observed_covered_ge_09[producer_name] += 1
                        summary_data[label].append(
                            {
                                "unresolved": len(coverage_rows),
                                "observed_covered_ge_09": dict(observed_covered_ge_09),
                                "area_fraction": record[
                                    "interior_visual_frame_page_area_fraction"
                                ],
                                "permutation": record["permutation"],
                            }
                        )
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    written += 1
                    print(f"[{label} p.{page_number}] {record.get('category')}", file=sys.stderr)

    print(f"scritte {written} righe in {output_path}", file=sys.stderr)

    if permutations > 0:
        _print_summary(summary_data, permutations=permutations, seed=permutation_seed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
