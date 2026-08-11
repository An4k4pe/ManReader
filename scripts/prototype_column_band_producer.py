"""Prototype implementation of Proposta_ColumnBandProducer_v10.md Sec.4.1-4.7,
the "funzione combinata" left unwritten by v8/v9 ("non ancora scritto:
l'implementazione dei tre passi come funzione unica").

Not a producer. Not wired anywhere in the job. Diagnostica pura, stesso
standard delle altre milestone esplorative (Milestone 25/26/29/32). Costruisce
comunque veri oggetti ``RegionCandidate``/``PageAnalysis`` (non dict ad hoc) per
riusare la validazione esistente gratis e per essere direttamente componibile
con il sottosistema Milestone 13-19 negli script che lo importano
(``measure_column_band_table_candidate_overlap.py``).

Sostituisce, senza modificarle, quattro funzioni esistenti e verificate
(riusate per import, non copiate): ``_visible_bbox``, ``_row_gaps``,
``_persistent_gaps_for_rows``, ``_segment_column_bands``
(``scan_column_structure_diagnostics.py``, Milestone 32).

Meccanismo (v10 Sec.4):

  4.1 ``_group_by_pymupdf_line``: raggruppa le TextPrimitive per
      ``(block_index, line_index)`` letto da ``source_observation_id``
      (formato ``text:b####:l####:s####``, verificato in
      ``pymupdf_capture.py:123-125`` -- stesso pattern regex già usato in
      ``dump_pymupdf_line_grouping.py`` e
      ``compare_pymupdf_line_grouping_column_bands.py``, non reinventato).

  4.2 ``_assemble_visual_rows``: fonde gli INVILUPPI dei gruppi per
      sovrapposizione verticale transitiva -- stesso algoritmo di
      ``_cluster_rows`` (Milestone 32), applicato ai gruppi invece che alle
      primitive singole. Ogni riga visiva risultante è l'unione delle bbox di
      tutti i gruppi che vi confluiscono: compatibile senza modifiche con
      ``_row_gaps``/``_segment_column_bands``.

      Verificato SOLO su un caso sintetico in questa sessione (nessun manuale
      reale disponibile nell'ambiente in cui questo script è stato scritto):
      una pagina fittizia a due colonne pure e una con titolo/piè di pagina a
      piena larghezza più corpo a due colonne. Confermato che (a) il
      raggruppamento NAIVE per singolo gruppo (un gruppo = una riga, nessun
      merge -- lo stesso approccio già in
      ``compare_pymupdf_line_grouping_column_bands.py``'s metodo
      ``pymupdf_line``) produce SEMPRE ``column_count=1``, cioè non rileva mai
      la struttura a colonne per costruzione (ogni "riga" contiene solo il
      proprio lato, ``_row_gaps`` non vede mai un gap interno); (b)
      l'assemblaggio di 4.2 riproduce esattamente la sequenza di
      ``column_count`` prodotta da ``_cluster_rows`` sullo stesso caso pulito.
      Non ancora verificato su dati reali, non ancora quantificato quanto
      riduca la sovra-fusione misurata (v10 Sec.11.6) -- richiede
      ``measure_visual_row_merge_reduction.py`` su manuali reali.

  4.3-4.4 confini di colonna e persistenza: ``_row_gaps``/
      ``_persistent_gaps_for_rows``/``_segment_column_bands`` importate
      invariate, applicate alle righe visive di 4.2.

  4.5 Emissione ``RegionCandidate`` per ogni banda con ``column_count >= 2``:
      ``proposed_structural_kind="layout.column_band"`` (nessuna modifica di
      schema, verificato contro ``_validate_structural_kind``,
      ``page_analysis_model.py:35-38``). ``--bbox-mode`` sceglie fra
      ``full-width`` (v10 Sec.11.7, opzione a) e ``observed-extent`` (opzione
      b) -- **non deciso quale sia corretto**, lo script produce entrambi per
      permettere il confronto empirico richiesto da Chat B prima di decidere.

  4.6 Satellite ``ColumnBandMeasurements`` (mai scritta prima, Milestone 33
      punto bloccante 3): qui come dict per riga CSV, non come dataclass
      nuova (nessuna decisione di schema presa da uno script diagnostico).

  4.7 ``unresolved_primitive_ids``: gruppi il cui bbox attraversa ENTRAMBI i
      bordi di un gap persistente della banda (stesso criterio, verificato,
      di ``test_pymupdf_block_gap_straddle.py:22-24`` -- non un nuovo
      predicato). v10 Sec.4.7 lo tratta come DIREZIONE, non chiusura: questo
      script marca i gruppi straddle, non decide se marcarli sia
      editorialmente corretto (vedi ``inspect_column_band_straddle_groups.py``
      per l'ispezione richiesta prima di trattarlo come deciso).

Uso, dalla radice del repository (Python 3.14, non l'ambiente di stesura):

    python3 scripts/prototype_column_band_producer.py MANUALE.pdf \\
        --bbox-mode both --output /tmp/column_bands.csv

    python3 scripts/prototype_column_band_producer.py "*.pdf" \\
        --bbox-mode both --output /tmp/column_bands_all.csv

(la seconda forma richiede la shell del chiamante per l'espansione di *,
non implementata qui: passare più PDF ripetendo l'argomento posizionale non è
supportato da argparse in questa forma -- usare un ciclo di shell, es.
``for f in *.pdf; do python3 scripts/prototype_column_band_producer.py "$f" \\
--bbox-mode both --output "/tmp/bands_$(basename "$f" .pdf).csv"; done``).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import TextIO, cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
for candidate_dir in (SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent):
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scan_column_structure_diagnostics import (  # noqa: E402
    _segment_column_bands,
    _visible_bbox,
)

from geometry_model import BBox  # noqa: E402
from page_analysis_model import (  # noqa: E402
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from page_analysis_validate import validate_page_analysis_against_primitive_page  # noqa: E402
from primitive_model import NormalizedPrimitivePage, TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_PRODUCER_NAME = "prototype.column_band"
_PRODUCER_VERSION = "0.1-prototype"
_CONFIGURATION_ID = "column-band-v10-prototype"
_STRUCTURAL_KIND = "layout.column_band"

_OBSERVATION_ID_PATTERN = re.compile(r"^text:b(\d+):l(\d+):s\d+$")

_DEFAULT_BIN_WIDTH = 1.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "bbox_mode",
    "band_index",
    "band_count",
    "row_start",
    "row_end",
    "row_count",
    "column_count",
    "candidate_bbox",
    "gap_boundaries",
    "primitive_count",
    "unresolved_group_count",
    "unresolved_primitive_count",
)


class _Group:
    __slots__ = ("block_index", "line_index", "bboxes", "primitive_ids", "y0", "y1")

    def __init__(self, block_index: int, line_index: int) -> None:
        self.block_index = block_index
        self.line_index = line_index
        self.bboxes: list[BBox] = []
        self.primitive_ids: list[str] = []
        self.y0 = float("inf")
        self.y1 = float("-inf")

    def add(self, bbox: BBox, primitive_id: str) -> None:
        self.bboxes.append(bbox)
        self.primitive_ids.append(primitive_id)
        self.y0 = min(self.y0, bbox[1])
        self.y1 = max(self.y1, bbox[3])


def _group_by_pymupdf_line(
    text_primitives: list[TextPrimitive],
    *,
    page_width: float,
    page_height: float,
) -> tuple[list[_Group], int]:
    """v10 Sec.4.1. Returns (groups, unparsed_count). Visible-clipped bboxes
    only (same ``_visible_bbox`` gate as Milestone 32); primitives outside the
    page frame are dropped, not counted as unparsed."""

    groups: dict[tuple[int, int], _Group] = {}
    unparsed = 0
    for primitive in text_primitives:
        visible = _visible_bbox(primitive.bbox, page_width=page_width, page_height=page_height)
        if visible is None:
            continue
        match = _OBSERVATION_ID_PATTERN.match(primitive.source_observation_id)
        if match is None:
            unparsed += 1
            continue
        key = (int(match.group(1)), int(match.group(2)))
        group = groups.setdefault(key, _Group(*key))
        group.add(visible, primitive.primitive_id)
    return list(groups.values()), unparsed


def _assemble_visual_rows(groups: list[_Group]) -> list[list[_Group]]:
    """v10 Sec.4.2. Same transitive vertical-overlap merge as ``_cluster_rows``
    (Milestone 32), applied to group envelopes instead of primitive bboxes.
    Returns visual rows as lists of member groups (not flattened), so callers
    can recover group-level provenance after banding."""

    if not groups:
        return []
    ordered = sorted(groups, key=lambda group: group.y0)
    visual_rows: list[list[_Group]] = [[ordered[0]]]
    current_y1 = ordered[0].y1
    for group in ordered[1:]:
        if group.y0 < current_y1:
            visual_rows[-1].append(group)
            current_y1 = max(current_y1, group.y1)
        else:
            visual_rows.append([group])
            current_y1 = group.y1
    return visual_rows


def _flatten_row_bboxes(visual_row: list[_Group]) -> list[BBox]:
    return [bbox for group in visual_row for bbox in group.bboxes]


def _group_straddles_gap(group: _Group, *, gap_start: float, gap_end: float) -> bool:
    """Same predicate, verified, as test_pymupdf_block_gap_straddle.py:22-24:
    a group straddles only if its extent crosses BOTH edges of the gap."""

    group_x0 = min(bbox[0] for bbox in group.bboxes)
    group_x1 = max(bbox[2] for bbox in group.bboxes)
    return group_x0 < gap_start and group_x1 > gap_end


def build_column_band_prototype(
    primitive_page: NormalizedPrimitivePage,
    *,
    generation_id: str,
    bbox_mode: str,
    bin_width: float = _DEFAULT_BIN_WIDTH,
    min_gap_width: float = _DEFAULT_MIN_GAP_WIDTH,
    min_support_ratio: float = _DEFAULT_MIN_SUPPORT_RATIO,
) -> tuple[PageAnalysis, list[dict[str, object]]]:
    """Build a prototype column_band PageAnalysis plus a satellite-measurement
    dict per emitted candidate (v10 Sec.4.6/4.7). ``bbox_mode`` is
    "full-width" or "observed-extent" (v10 Sec.11.7, not decided)."""

    if bbox_mode not in ("full-width", "observed-extent"):
        raise ValueError('bbox_mode must be "full-width" or "observed-extent"')

    page_width = primitive_page.page_geometry.width
    page_height = primitive_page.page_geometry.height

    groups, unparsed = _group_by_pymupdf_line(
        primitive_page.text_primitives, page_width=page_width, page_height=page_height
    )
    visual_rows = _assemble_visual_rows(groups)
    row_bboxes_by_row = [_flatten_row_bboxes(row) for row in visual_rows]

    bands = _segment_column_bands(
        row_bboxes_by_row,
        page_width=page_width,
        bin_width=bin_width,
        min_gap_width=min_gap_width,
        min_support_ratio=min_support_ratio,
    )

    candidates: list[RegionCandidate] = []
    measurements: list[dict[str, object]] = []
    for band_index, band in enumerate(bands):
        if cast(int, band["column_count"]) < 2:
            continue
        band_rows = visual_rows[cast(int, band["row_start"]) : cast(int, band["row_end"]) + 1]
        band_groups = [group for row in band_rows for group in row]
        primitive_ids = tuple(pid for group in band_groups for pid in group.primitive_ids)

        gaps = cast(list[tuple[float, float, float]], band["gaps"])
        if bbox_mode == "full-width":
            candidate_bbox: BBox = (
                0.0,
                float(cast(float, band["y0"])),
                page_width,
                float(cast(float, band["y1"])),
            )
        else:
            observed_x0 = min(min(bbox[0] for bbox in group.bboxes) for group in band_groups)
            observed_x1 = max(max(bbox[2] for bbox in group.bboxes) for group in band_groups)
            candidate_bbox = (
                observed_x0,
                float(cast(float, band["y0"])),
                observed_x1,
                float(cast(float, band["y1"])),
            )

        unresolved_group_ids: list[str] = []
        unresolved_primitive_ids: list[str] = []
        for gap_start, gap_end, _support in gaps:
            for group in band_groups:
                if _group_straddles_gap(group, gap_start=gap_start, gap_end=gap_end):
                    unresolved_group_ids.append(f"b{group.block_index:04d}l{group.line_index:04d}")
                    unresolved_primitive_ids.extend(group.primitive_ids)

        candidate_id = f"candidate:column_band:prototype:{band_index:04d}:{bbox_mode}"
        candidates.append(
            RegionCandidate(
                candidate_id=candidate_id,
                page_id=primitive_page.page_id,
                bbox=candidate_bbox,
                proposed_structural_kind=_STRUCTURAL_KIND,
                primitive_ids=primitive_ids,
            )
        )
        measurements.append(
            {
                "candidate_id": candidate_id,
                "band_index": band_index,
                "band_count": len(bands),
                "row_start": band["row_start"],
                "row_end": band["row_end"],
                "row_count": band["row_count"],
                "column_count": band["column_count"],
                "gap_boundaries": tuple((round(s, 1), round(e, 1)) for s, e, _r in gaps),
                "candidate_bbox": tuple(round(c, 1) for c in candidate_bbox),
                "primitive_count": len(primitive_ids),
                "unresolved_group_count": len(set(unresolved_group_ids)),
                "unresolved_primitive_count": len(set(unresolved_primitive_ids)),
                "unresolved_primitive_ids": tuple(sorted(set(unresolved_primitive_ids))),
            }
        )

    analysis = PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=primitive_page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=primitive_page.source_id,
            source_capture_id=primitive_page.source_capture_id,
            source_page_id=primitive_page.page_id,
            source_primitive_schema_version=primitive_page.schema_version,
            producer_name=_PRODUCER_NAME,
            producer_version=_PRODUCER_VERSION,
            configuration_id=f"{_CONFIGURATION_ID}:{bbox_mode}",
        ),
        regions=(),
        relations=(),
        candidates=tuple(candidates),
    )
    validate_page_analysis_against_primitive_page(analysis, primitive_page)

    if unparsed > 0:
        print(
            f"page {primitive_page.page_id}: {unparsed} primitive(s) with unparseable "
            "source_observation_id, excluded from grouping",
            file=sys.stderr,
        )

    return analysis, measurements


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument(
        "--bbox-mode",
        choices=("full-width", "observed-extent", "both"),
        default="both",
        help="Candidate bbox policy (v10 Sec.11.7, not decided). Default: both, for comparison.",
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument("--bin-width", type=float, default=_DEFAULT_BIN_WIDTH)
    parser.add_argument("--min-gap-width", type=float, default=_DEFAULT_MIN_GAP_WIDTH)
    parser.add_argument("--min-support-ratio", type=float, default=_DEFAULT_MIN_SUPPORT_RATIO)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    modes = ("full-width", "observed-extent") if args.bbox_mode == "both" else (args.bbox_mode,)

    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        page_indices = list(
            [args.page - 1] if args.page is not None else range(document.page_count)
        )
        print(
            f"{pdf_path.name}: {len(page_indices)} pagina/e da processare, "
            f"modalita' {args.bbox_mode}",
            file=sys.stderr,
            flush=True,
        )
        for progress_index, page_index in enumerate(page_indices, start=1):
            if page_index < 0 or page_index >= document.page_count:
                print(f"page out of range, skipped: {page_index + 1}", file=sys.stderr)
                continue
            page_number = page_index + 1
            if (
                progress_index == 1
                or progress_index % 10 == 0
                or progress_index == len(page_indices)
            ):
                print(
                    f"  pagina {page_number} ({progress_index}/{len(page_indices)})...",
                    file=sys.stderr,
                    flush=True,
                )
            page = document.load_page(page_index)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                print(
                    f"page {page_number}: rotation/cropbox precondition failed, skipped",
                    file=sys.stderr,
                )
                continue

            capture = capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"page:{page_number:04d}",
                capture_id=f"diagnostic-column-band-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)

            for mode in modes:
                _analysis, measurements = build_column_band_prototype(
                    primitive_page,
                    generation_id=f"generation:column-band-prototype:{page_number:04d}:{mode}",
                    bbox_mode=mode,
                    bin_width=args.bin_width,
                    min_gap_width=args.min_gap_width,
                    min_support_ratio=args.min_support_ratio,
                )
                for measurement in measurements:
                    rows.append(
                        {
                            "manual": pdf_path.name,
                            "page": page_number,
                            "bbox_mode": mode,
                            **{
                                key: measurement[key]
                                for key in _CSV_FIELDNAMES
                                if key not in ("manual", "page", "bbox_mode")
                            },
                        }
                    )

    if args.output is not None:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            _write_rows(handle, rows)
    else:
        _write_rows(sys.stdout, rows)

    return 0


def _write_rows(handle: TextIO, rows: list[dict[str, object]]) -> None:
    writer = csv.writer(handle)
    writer.writerow(_CSV_FIELDNAMES)
    for row in rows:
        writer.writerow([row.get(name, "") for name in _CSV_FIELDNAMES])


if __name__ == "__main__":
    raise SystemExit(main())
