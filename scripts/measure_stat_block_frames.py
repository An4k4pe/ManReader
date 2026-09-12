"""Per ogni scheda riconosciuta: il riquadro scelto e i riquadri in concorrenza.

Misura, non meccanismo. Serve all'esito del passo 3b
(`Esito_NotaSfondoScheda_v1.md`): quando due riquadri passano il criterio di
scheda sulle stesse righe, quale vince, se contiene il nome, e quante righe di
testo il suo bordo **taglia** -- una riga che il riquadro tocca senza
contenerla. Le due regole di scelta messe a confronto in quell'esito si leggono
da qui: «vince il piu' stretto col nome» e «un bordo che taglia righe non
delimita una scheda».

Le righe e i riquadri sono quelli dell'innesto in `prototype_ir2_page.run`:
stessa cattura, stesso ordine di lettura, ridisegni tolti.

Uso:  python scripts/measure_stat_block_frames.py <pdf> <sigla> <idx da> <idx a>
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _path in (PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from prototype_ir2_page import (  # noqa: E402
    _build_all_analyses,
    _tree_aware_order,
    _tree_rows_from_contract,
    build_column_band_page_analysis_with_measurements,
    capture_pymupdf_page,
    normalize_backend_page_capture,
)

import stat_block_regions as sbr  # noqa: E402
from geometry_model import BBox  # noqa: E402
from ir2_builder import group_source_lines, redrawn_duplicates  # noqa: E402

_FRAME_PRODUCERS = ("page_analysis.embedded_visual", "page_analysis.interior_visual_frame")


def _overlaps(first: BBox, second: BBox) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(
        first[3], second[3]
    ) > max(first[1], second[1])


def main(argv: list[str]) -> int:
    pdf, sigla, start, end = argv[1], argv[2], int(argv[3]), int(argv[4])
    with fitz.open(pdf) as document, pdfplumber.open(pdf) as plumber:
        for index in range(start, min(end, document.page_count - 1) + 1):
            page = document[index]
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page, source_id="s", page_id=f"page:{index + 1:04d}", capture_id="c"
                )
            )
            analyses = _build_all_analyses(
                primitive_page, plumber_page=plumber.pages[index], generation_id="g"
            )
            bands, measures = build_column_band_page_analysis_with_measurements(
                primitive_page, generation_id="g"
            )
            ordered, _inside = _tree_aware_order(
                list(primitive_page.text_primitives),
                _tree_rows_from_contract(bands.candidates, measures),
            )
            deduplicated, _redraws = redrawn_duplicates([primitive for primitive, _g in ordered])
            lines = [line.primitives for line in group_source_lines(deduplicated)]
            frames = [
                sbr.FrameInput(candidate.candidate_id, candidate.bbox, candidate.primitive_ids)
                for analysis in analyses
                if analysis.provenance.producer_name in _FRAME_PRODUCERS
                for candidate in analysis.candidates
            ]
            images = {primitive.primitive_id for primitive in primitive_page.image_primitives}
            boxes = {
                primitive.primitive_id: primitive.bbox
                for primitive in (*primitive_page.drawing_primitives, *primitive_page.image_primitives)
            }
            regions = sbr.stat_block_regions(frames, boxes, lines)
            if not regions:
                continue

            line_boxes = [sbr._line_bbox(line) for line in lines]
            pairs = [sbr.label_pairs(line) for line in lines]
            fields = {i for i, count in enumerate(pairs) if count >= 2}
            proposals: dict[BBox, tuple[tuple[int, ...], int, bool, bool]] = {}
            for frame in frames:
                for piece, members in sbr.split_frame(frame, boxes, line_boxes):
                    inside = tuple(
                        i for i, box in enumerate(line_boxes) if box and sbr._centre_inside(piece, box)
                    )
                    if len(fields.intersection(inside)) < 2:
                        continue
                    cut = sum(
                        1
                        for box in line_boxes
                        if box and _overlaps(piece, box) and not sbr._contains(piece, box)
                    )
                    proposals[piece] = (
                        inside,
                        cut,
                        bool(sbr._name_lines(lines, inside, pairs)),
                        any(member in images for member in members),
                    )

            for region in regions:
                inside, cut, _named, image = proposals[region.bbox]
                name = " ".join(
                    "".join(primitive.text for primitive in lines[i]).strip()
                    for i in region.name_line_indices
                )
                rivals = [
                    value
                    for piece, value in proposals.items()
                    if piece != region.bbox and set(value[0]) & set(inside)
                ]
                print(
                    f"{sigla} idx {index:3d} [{page.get_label()}] nome {name[:28]!r:30s} "
                    f"SCELTA righe {len(inside):3d} tagliate {cut:2d} img {image:d}"
                    + "".join(
                        f" | alt righe {len(v[0])} tagliate {v[1]} nome {v[2]:d} img {v[3]:d}"
                        for v in rivals
                    )
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
