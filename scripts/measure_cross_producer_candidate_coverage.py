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
"""

from __future__ import annotations

import argparse
import json
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
from page_analysis_model import PageAnalysis  # noqa: E402
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

    if verify:
        checked, mismatches = _verify_against_production(bound, analyses, embedded)
        record["verification"] = {"pairs_checked": checked, "mismatches": mismatches}

    record["category"] = "PASS"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdfs = cast(list[tuple[str, Path]], args.pdf)
    sample_path = cast(Path, args.sample_jsonl)
    output_path = cast(Path, args.output)

    if not pdfs:
        print("at least one --pdf LABEL=PATH is required", file=sys.stderr)
        return 1
    if not sample_path.is_file():
        print(f"sample JSONL not found: {sample_path}", file=sys.stderr)
        return 1

    sample_pages = _read_sample_pages(sample_path)
    verify_pending = True
    written = 0

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
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    written += 1
                    print(f"[{label} p.{page_number}] {record.get('category')}", file=sys.stderr)

    print(f"scritte {written} righe in {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
