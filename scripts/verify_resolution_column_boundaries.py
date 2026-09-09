"""Verifica l'oracolo della Milestone 43, Fase 2, sulla catena vera.

La regola V4 e' gia' stata misurata nella Milestone 42 con uno script che
ricomponeva la decisione sopra il profilo del producer. Qui la stessa domanda
passa invece dai moduli di produzione -- `column_band_gutter_rows`,
`measure_rejected_gutters`, `build_table_candidate_page_analysis`,
`resolve_column_boundaries` -- e i numeri devono coincidere.

Oracolo, dal verbale della Milestone 42:
    DB.pdf   126 pagine   +31 corridoi ammessi da V4, 0 fuori da una tabella
    Apo.pdf  148 pagine   +22 corridoi ammessi da V4, 0 fuori da una tabella

Se questo script ne da' altri, e' l'implementazione a essere sbagliata: la
misura e' stata fatta prima, ed e' quella a vincolare il codice.

Uso:  python3 scripts/verify_resolution_column_boundaries.py <file.pdf>
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
for candidate_dir in [PROJECT_ROOT, *PROJECT_ROOT.parents]:
    if (candidate_dir / "primitive_model.py").is_file():
        PROJECT_ROOT = candidate_dir
        break
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pdfplumber  # noqa: E402
import pymupdf  # noqa: E402

from page_analysis_column_band import column_band_gutter_rows  # noqa: E402
from page_analysis_column_band_rejected_gutters import (  # noqa: E402
    measure_rejected_gutters,
)
from page_analysis_table_candidate import (  # noqa: E402
    build_table_candidate_page_analysis,
)
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_column_boundaries import resolve_column_boundaries  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--da", type=int, default=0)
    parser.add_argument("--a", type=int, default=10**6)
    args = parser.parse_args(argv)

    conta: Counter[str] = Counter()
    pagine_con_ammessi: list[int] = []
    with pymupdf.open(args.pdf) as documento, pdfplumber.open(args.pdf) as plumber:
        for indice in range(args.da, min(args.a + 1, documento.page_count)):
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    documento.load_page(indice),
                    source_id="milestone43",
                    page_id=f"page:{indice + 1:04d}",
                    capture_id=f"m43:{indice}",
                )
            )
            righe = column_band_gutter_rows(primitive_page)
            conta["corridoi"] += len(righe)
            conta["ammessi_dal_producer"] += sum(1 for r in righe if r["reject_reason"] is None)

            respinti = measure_rejected_gutters(primitive_page.page_id, righe)
            tabelle = build_table_candidate_page_analysis(
                BoundTableCandidatePage(
                    primitive_page=primitive_page, plumber_page=plumber.pages[indice]
                ),
                generation_id=f"m43:{indice}",
            ).candidates
            risolti = resolve_column_boundaries(
                page_id=primitive_page.page_id,
                rejected_gutters=respinti,
                table_candidates=tabelle,
            )
            for boundary in risolti.boundaries:
                conta[boundary.reason_token] += 1
            if risolti.admitted:
                pagine_con_ammessi.append(indice)
                conta["ammessi_da_resolution"] += len(risolti.admitted)

    print(f"file: {args.pdf.name}")
    print(f"   corridoi totali: {conta['corridoi']}")
    print(f"   ammessi dal producer (V0): {conta['ammessi_dal_producer']}")
    print(f"   ammessi da Resolution (V4): {conta['ammessi_da_resolution']}")
    print(f"   totale con V4 applicata: "
          f"{conta['ammessi_dal_producer'] + conta['ammessi_da_resolution']}")
    print("   motivi dei non ammessi:")
    for motivo in ("outside_table_candidate", "empty_flank", "other_reject_reason"):
        print(f"      {motivo:26s} {conta[motivo]}")
    print(f"   pagine con almeno un confine ammesso: {len(pagine_con_ammessi)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
