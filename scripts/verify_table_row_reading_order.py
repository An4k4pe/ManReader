"""Milestone 44, Fase 3: la lettura per righe su una pagina reale.

Criterio di accettazione della fase, da `Criterio_Milestone44_V4_v1.md`: «su una
pagina di tabella verificata a vista, l'ordine emesso e' per righe e non per
colonne».

Lo script mette a confronto, sulla regione di una tabella, l'ordine di oggi
(per riga di sorgente, cioe' sostanzialmente per `y`) e quello per righe di
`order_table_lines_by_rows`, usando i confini di colonna che Resolution ammette.
Non modifica niente: stampa e basta.

Uso:  python3 scripts/verify_table_row_reading_order.py <file.pdf> --pagina N
"""

from __future__ import annotations

import argparse
import re
import sys
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
from primitive_model import TextPrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402
from resolution_column_boundaries import resolve_column_boundaries  # noqa: E402
from table_row_reading_order import order_table_lines_by_rows  # noqa: E402

_OBSERVATION_ID = re.compile(r"^text:b(\d+):l(\d+):s(\d+)$")


def _source_lines(primitives: list[TextPrimitive]) -> list[tuple[TextPrimitive, ...]]:
    """Le righe tipografiche dalla sorgente, non dalla geometria.

    Stesso raggruppamento che usano gli altri consumer diagnostici: la riga sta
    gia' nell'id di osservazione (`text:b{block}:l{line}:s{span}`)."""
    grouped: dict[tuple[int, int], list[tuple[int, TextPrimitive]]] = {}
    sciolte: list[tuple[TextPrimitive, ...]] = []
    for primitive in primitives:
        match = _OBSERVATION_ID.match(primitive.source_observation_id or "")
        if match is None:
            sciolte.append((primitive,))
            continue
        chiave = (int(match.group(1)), int(match.group(2)))
        grouped.setdefault(chiave, []).append((int(match.group(3)), primitive))
    righe = sciolte + [
        tuple(p for _s, p in sorted(spans, key=lambda item: item[0]))
        for spans in grouped.values()
    ]
    righe.sort(key=lambda line: (min(p.bbox[1] for p in line), min(p.bbox[0] for p in line)))
    return righe


def _testo(righe) -> list[str]:  # type: ignore[no-untyped-def]
    return [" ".join(p.text for p in riga).strip() for riga in righe]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pagina", type=int, required=True, help="indice posizionale")
    parser.add_argument("--righe", type=int, default=12, help="quante righe stampare")
    args = parser.parse_args(argv)

    with pymupdf.open(args.pdf) as documento, pdfplumber.open(args.pdf) as plumber:
        indice = args.pagina
        primitive_page = normalize_backend_page_capture(
            capture_pymupdf_page(
                documento.load_page(indice),
                source_id="milestone43",
                page_id=f"page:{indice + 1:04d}",
                capture_id=f"m43:{indice}",
            )
        )
        tabelle = build_table_candidate_page_analysis(
            BoundTableCandidatePage(
                primitive_page=primitive_page, plumber_page=plumber.pages[indice]
            ),
            generation_id=f"m43:{indice}",
        ).candidates
        risolti = resolve_column_boundaries(
            page_id=primitive_page.page_id,
            rejected_gutters=measure_rejected_gutters(
                primitive_page.page_id, column_band_gutter_rows(primitive_page)
            ),
            table_candidates=tabelle,
        )

    print(f"file: {args.pdf.name}   pagina indice {indice}")
    print(f"   table_candidate: {len(tabelle)}   confini ammessi: {len(risolti.admitted)}")
    if not risolti.admitted:
        print("   nessun confine ammesso: su questa pagina la Fase 3 non ha niente da fare")
        return 0

    tutte = _source_lines(list(primitive_page.text_primitives))
    for numero, tabella in enumerate(tabelle):
        x0, y0, x1, y1 = tabella.bbox
        dentro = [
            riga
            for riga in tutte
            if x0 <= sum(p.bbox[0] + p.bbox[2] for p in riga) / (2 * len(riga)) < x1
            and y0 <= sum(p.bbox[1] + p.bbox[3] for p in riga) / (2 * len(riga)) < y1
        ]
        confini = [
            (b.x0, b.x1)
            for b in risolti.admitted
            if x0 <= b.x0 and x1 >= b.x1 and y0 <= b.y1 and y1 >= b.y0
        ]
        if not dentro or not confini:
            continue
        print(f"\n== tabella {numero}: {len(dentro)} righe, confini {confini} ==")
        print("   --- ordine di OGGI (per riga di sorgente) ---")
        for testo in _testo(dentro)[: args.righe]:
            print(f"      {testo[:76]}")
        print("   --- ordine PER RIGHE (Fase 3) ---")
        ordinate = order_table_lines_by_rows(dentro, column_boundaries=confini)
        for testo in _testo(ordinate)[: args.righe]:
            print(f"      {testo[:76]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
