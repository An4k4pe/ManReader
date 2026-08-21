"""Le tre fonti di regione tabella, sulle stesse pagine, con il render accanto.

Produce OGNI numero citato in `Proposta_RegioneTabella_v1.md` §1: le regioni delle
due strategie pdfplumber, le bande e i gutter di `column_band`, e cosa emette
`_find_table_regions` del legacy. Con `--render` disegna le tre sopra la pagina --
verde `lines/lines`, rosso `text/lines`, blu tratteggiato le bande con i gutter
ombreggiati.

Esiste perche' `AGENTS.MD` §Aggiornamento documenti chiede che lo script che
produce un numero citato stia nel repo: non basta che il risultato sia nel testo.

NON e' la misura di accettazione. Quella e' descritta in
`Proposta_RegioneTabella_v1.md` §4 e va registrata prima di essere eseguita
(`AGENTS.MD` §15). Questo script osserva e basta.

Le pagine sono 0-based: `--pages Wil:244` e' l'indice 244, cioe' `--page 245` per
gli script che usano il numero posizionale. I numeri STAMPATI sono un'altra cosa
ancora e vanno letti sul render.

Read-only, nessuna scrittura fuori da `--outdir`.

Uso:

    ./venv/bin/python scripts/inspect_table_region_sources.py --pdf-dir . \
        --pages Apo:46 Vil:166 Wil:244 Dag:136 DrM:267 FW:62 Fab:256 \
        --render --outdir /tmp/regioni
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor import (  # noqa: E402
    _TABLE_TEXT_LINES_SETTINGS,  # noqa: E402
    _find_table_regions,  # noqa: E402
    _is_valid_text_line_table_region,  # noqa: E402
    _safe_find_tables,
    _table_bbox,
    _table_bboxes,
)
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

LINES = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
TEXT_LINES = {"vertical_strategy": "text", "horizontal_strategy": "lines"}
GREEN = (0.0, 0.55, 0.0)
RED = (0.85, 0.0, 0.0)
BLUE = (0.0, 0.0, 0.9)


def _describe(table: Any) -> tuple[int, int, int, int]:
    rows = table.extract()
    cells = [cell for row in rows for cell in row]
    filled = sum(1 for cell in cells if cell and cell.strip())
    columns = max((len(row) for row in rows), default=0)
    return len(rows), columns, filled, len(cells)


def _report_strategy(plumber_page: Any, label: str, settings: dict[str, str]) -> None:
    tables = plumber_page.find_tables(table_settings=settings)
    print(f"  {label}: {len(tables)} regioni")
    for table in tables:
        x0, y0, x1, y1 = table.bbox
        rows, columns, filled, total = _describe(table)
        print(
            f"      ({x0:7.1f},{y0:7.1f},{x1:7.1f},{y1:7.1f}) "
            f"{x1 - x0:5.0f}x{y1 - y0:5.0f} righe={rows} col={columns} "
            f"piene={filled}/{total}"
        )


def _report_bands(primitive_page: Any) -> Any:
    analysis, measures = build_column_band_page_analysis_with_measurements(
        primitive_page, generation_id="inspect-table-region-sources"
    )
    by_id = {measure.candidate_id: measure for measure in measures}
    print(f"  column_band: {len(analysis.candidates)} bande")
    for candidate in analysis.candidates:
        measure = by_id[candidate.candidate_id]
        gutters = ", ".join(f"{a:.0f}-{b:.0f}" for a, b in measure.gutter_x_intervals)
        x0, y0, x1, y1 = candidate.bbox
        print(
            f"      ({x0:7.1f},{y0:7.1f},{x1:7.1f},{y1:7.1f}) "
            f"col={measure.column_count} depth={measure.depth} gutter=[{gutters}]"
        )
    return analysis, by_id


def _report_legacy(plumber_page: Any) -> None:
    default_regions = _table_bboxes(_safe_find_tables(plumber_page))
    for table in _safe_find_tables(plumber_page, _TABLE_TEXT_LINES_SETTINGS):
        bbox = _table_bbox(table)
        if bbox is None:
            continue
        admitted = _is_valid_text_line_table_region(
            table, bbox, default_regions, plumber_page
        )
        print(
            f"      text/lines ({bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f})"
            f" -> ammessa={admitted}"
        )
    emitted = _find_table_regions(plumber_page)
    print(f"  legacy `_find_table_regions`: {len(emitted)} regioni")
    for x0, y0, x1, y1 in emitted:
        print(f"      ({x0:7.1f},{y0:7.1f},{x1:7.1f},{y1:7.1f}) {x1 - x0:5.0f}x{y1 - y0:5.0f}")


def _render(page: Any, plumber_page: Any, analysis: Any, by_id: dict[str, Any], out: Path) -> None:
    for settings, color in ((LINES, GREEN), (TEXT_LINES, RED)):
        for table in plumber_page.find_tables(table_settings=settings):
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(*table.bbox))
            shape.finish(color=color, width=1.5)
            shape.commit()
    for candidate in analysis.candidates:
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(*candidate.bbox))
        shape.finish(color=BLUE, width=2.5, dashes="[4 3] 0")
        shape.commit()
        for a, b in by_id[candidate.candidate_id].gutter_x_intervals:
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(a, candidate.bbox[1], b, candidate.bbox[3]))
            shape.finish(fill=(0.2, 0.4, 1.0), fill_opacity=0.25, width=0)
            shape.commit()
    page.get_pixmap(dpi=110).save(out)
    print(f"  reso: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--pages", nargs="+", required=True, help="Nome:indice0based")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--outdir", type=Path)
    args = parser.parse_args()

    if args.render and args.outdir is None:
        parser.error("--render richiede --outdir")
    if args.outdir is not None:
        args.outdir.mkdir(parents=True, exist_ok=True)

    for spec in args.pages:
        name, raw_index = spec.split(":")
        index = int(raw_index)
        path = args.pdf_dir / f"{name}.pdf"
        if not path.is_file():
            print(f"MANCANTE: {path}", file=sys.stderr)
            continue

        document = fitz.open(path)
        page = document[index]
        print(f"\n### {name} idx {index}  ({page.rect.width:.0f}x{page.rect.height:.0f})")
        if page.rotation != 0 or tuple(page.mediabox) != tuple(page.cropbox):
            print("  SKIP: guardia pagina (rotation o mediabox/cropbox)")
            continue

        plumber_document = pdfplumber.open(path)
        plumber_page = plumber_document.pages[index]

        _report_strategy(plumber_page, "lines/lines", LINES)
        _report_strategy(plumber_page, "text/lines (producer)", TEXT_LINES)

        capture = capture_pymupdf_page(
            page,
            source_id="inspect-table-region-sources",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"inspect:page:{index + 1:04d}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        analysis, by_id = _report_bands(primitive_page)

        _report_legacy(plumber_page)

        if args.render:
            _render(page, plumber_page, analysis, by_id, args.outdir / f"{name}_{index}.png")


if __name__ == "__main__":
    main()
