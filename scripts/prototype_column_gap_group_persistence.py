"""Rilevazione dei confini di colonna SENZA passare da un clustering di righe
-- proposta dell'utente in sessione, non di v10. Sostituisce concettualmente
`_cluster_rows`/`_assemble_visual_rows` (v10 Sec.4.1-4.2, gia' ritrattato:
misurato su tre manuali reali, riduzione della sovra-fusione = 0) come base
per la rilevazione dei gap.

Motivazione: il compito di `column_band` e' "dove sono i bordi delle
colonne", non "quali primitive appartengono alla stessa riga tipografica" --
i due problemi sono stati indebitamente accoppiati fin da Milestone 32.
La sovra-fusione e il flicker per-riga (v10 Sec.11.6, DB/Fab/Kul, verificato
identico fra vecchio e nuovo meccanismo) sono difetti del CLUSTERING DI
RIGHE, non della domanda "dove sono i gap orizzontali persistenti in questa
zona" -- che si puo' rispondere aggregando direttamente sui gruppi
`(block_index, line_index)`, senza mai decidere quali gruppi condividano una
riga visiva.

Metodo, generalizzazione di `_persistent_gaps_for_rows` (Milestone 32) da
"per riga" a "per fetta y fine":

Invece di iterare su righe pre-clusterizzate, si itera su una griglia y fine
(`--bin-height`, default 2pt -- una frazione di un'interlinea tipica).
Per ogni fetta y:
  - i gruppi "attivi" sono quelli il cui inviluppo [y0,y1] copre quella
    fetta (nessuna decisione su "stessa riga", solo sovrapposizione diretta
    con l'altezza corrente);
  - l'estensione eleggibile in quella fetta e' l'unione delle estensioni x
    dei gruppi attivi (corrisponde a `[row_x0, row_x1]` di
    `_row_gaps`, ma ricalcolata fetta per fetta, non per riga);
  - un bin x e' "gap" in quella fetta se e' dentro l'estensione eleggibile
    ma nessun gruppo attivo lo copre.
Persistenza per bin x = frazione di fette y eleggibili in cui il bin e' gap,
sull'intera regione data (default: tutta la pagina) -- stesso criterio di
soglia (`--min-support-ratio`) e stessa raccolta in run contigue
(`--min-gap-width`) di `_persistent_gaps_for_rows`, Milestone 32, non
reinventati.

Perche' questo evita il problema delle celle di tabella che vanno a capo
(v9/v10 Sec. su Fab.pdf "Armi da Mischia" e "Luogo d'Avventura",
render confermati dall'utente): una fetta y dove e' attivo un solo gruppo
stretto (la continuazione di una cella che va a capo) ha un'estensione
eleggibile STRETTA, quindi le altre posizioni x (dove normalmente ci sono
le altre colonne) non diventano "gap" in quella fetta -- semplicemente non
sono eleggibili li'. Con il vecchio meccanismo per-riga, quella riga di
continuazione veniva letta come `column_count=1`, rompendo la banda.

Avvertenza esplicita, dalla storia gia' registrata in questo file
(`scan_column_structure_diagnostics.py`, Milestone 32, v1 "whole-page"):
un singolo elemento a piena larghezza che attraversa il gutter (titolo,
bordo tabella) puo' azzerare un gap se l'aggregazione e' un OR semplice non
pesato. Qui la soglia di persistenza (`--min-support-ratio`, stesso default
0.6) e' la stessa salvaguardia gia' verificata da v2/v3 di quella milestone
contro esattamente questo fallimento -- non e' un ritorno a v1, ne eredita
la protezione applicandola a una griglia fine invece che a righe.

Non un producer. Non wired. Nessun `RegionCandidate`. Diagnostica pura,
prima di qualunque decisione: qui si misura solo se i gap trovati sono piu'
stabili di quelli del vecchio meccanismo, non si propone ancora un contratto.

Uso:

    python3 scripts/prototype_column_gap_group_persistence.py DB.pdf --page 76 --output /tmp/gaps_db_p76.csv
    python3 scripts/prototype_column_gap_group_persistence.py DB.pdf --page 113 --output /tmp/gaps_db_p113.csv
    python3 scripts/prototype_column_gap_group_persistence.py Fab.pdf --page 84 --output /tmp/gaps_fab_p84.csv
"""

from __future__ import annotations

import argparse
import csv
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

from prototype_column_band_producer import _Group, _group_by_pymupdf_line  # noqa: E402

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_DEFAULT_BIN_WIDTH_X = 1.0
_DEFAULT_BIN_HEIGHT_Y = 2.0
_DEFAULT_MIN_GAP_WIDTH = 15.0
_DEFAULT_MIN_SUPPORT_RATIO = 0.6

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "y_start",
    "y_end",
    "column_count",
    "gap_start",
    "gap_end",
    "support_ratio",
)


def _measure_group_persistent_gaps(
    groups: list[_Group],
    *,
    page_width: float,
    y_start: float,
    y_end: float,
    bin_width_x: float,
    bin_height_y: float,
    min_gap_width: float,
    min_support_ratio: float,
) -> list[tuple[float, float, float]]:
    """Persistenza dei gap calcolata su una griglia y fine, non su righe.
    Ogni gruppo contribuisce alla sua estensione y reale, non a una riga
    pre-clusterizzata. Ritorna i gap persistenti come (start, end, support)."""

    if not groups or bin_width_x <= 0.0 or bin_height_y <= 0.0:
        return []

    n_x_bins = int(page_width // bin_width_x) + 2
    n_y_bins = max(1, int((y_end - y_start) // bin_height_y) + 1)

    eligible = [0] * n_x_bins
    gap_hit = [0] * n_x_bins

    # Ordina i gruppi per y0 solo per rendere deterministico l'ordine di
    # `active` (i risultati non dipendono dall'ordine, ma un dump stabile fra
    # esecuzioni e' piu' facile da confrontare).
    ordered_groups = sorted(groups, key=lambda g: g.y0)

    for y_bin_index in range(n_y_bins):
        y = y_start + y_bin_index * bin_height_y
        # Scansione completa dei gruppi per ogni fetta: costo
        # O(n_y_bins * n_groups). Accettabile per uso diagnostico su una
        # pagina alla volta; se un giorno servisse su interi manuali, qui va
        # una finestra scorrevole (i gruppi sono ordinati per y0, non per y1,
        # quindi servirebbe anche una coda ordinata per y1).
        active = [g for g in ordered_groups if g.y0 <= y < g.y1]
        if not active:
            continue

        eligible_x0 = min(min(bbox[0] for bbox in g.bboxes) for g in active)
        eligible_x1 = max(max(bbox[2] for bbox in g.bboxes) for g in active)
        start_eligible_bin = max(0, int(eligible_x0 // bin_width_x))
        end_eligible_bin = min(n_x_bins - 1, int(eligible_x1 // bin_width_x))
        if start_eligible_bin > end_eligible_bin:
            continue

        covered = bytearray(end_eligible_bin - start_eligible_bin + 1)
        for g in active:
            for bbox in g.bboxes:
                x0, _y0, x1, _y1 = bbox
                sb = max(start_eligible_bin, int(x0 // bin_width_x))
                eb = min(end_eligible_bin, int(x1 // bin_width_x))
                for b in range(sb, eb + 1):
                    covered[b - start_eligible_bin] = 1

        for b in range(start_eligible_bin, end_eligible_bin + 1):
            eligible[b] += 1
            if not covered[b - start_eligible_bin]:
                gap_hit[b] += 1

    persistent: list[tuple[float, float, float]] = []
    run_start: float | None = None
    run_ratios: list[float] = []
    for b in range(n_x_bins):
        ratio = (gap_hit[b] / eligible[b]) if eligible[b] > 0 else 0.0
        if ratio >= min_support_ratio:
            if run_start is None:
                run_start = b * bin_width_x
            run_ratios.append(ratio)
        else:
            if run_start is not None:
                run_end = b * bin_width_x
                if run_end - run_start >= min_gap_width:
                    persistent.append((run_start, run_end, sum(run_ratios) / len(run_ratios)))
                run_start = None
                run_ratios = []
    if run_start is not None:
        run_end = n_x_bins * bin_width_x
        if run_end - run_start >= min_gap_width:
            persistent.append((run_start, run_end, sum(run_ratios) / len(run_ratios)))

    return persistent


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to scan.")
    parser.add_argument(
        "--page", type=int, default=None, help="1-indexed page number. Default: whole document."
    )
    parser.add_argument(
        "--y-window",
        type=str,
        default=None,
        help="Y0,Y1 opzionale per limitare l'analisi a una sotto-regione della pagina "
        "(es. per isolare una tabella). Default: tutta la pagina.",
    )
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    parser.add_argument("--bin-width-x", type=float, default=_DEFAULT_BIN_WIDTH_X)
    parser.add_argument("--bin-height-y", type=float, default=_DEFAULT_BIN_HEIGHT_Y)
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

    y_window: tuple[float, float] | None = None
    if args.y_window is not None:
        parts = args.y_window.split(",")
        if len(parts) != 2:
            print("--y-window deve essere Y0,Y1", file=sys.stderr)
            return 1
        y_window = (float(parts[0]), float(parts[1]))

    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        page_indices = list(
            [args.page - 1] if args.page is not None else range(document.page_count)
        )
        print(
            f"{pdf_path.name}: {len(page_indices)} pagina/e da processare",
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
                capture_id=f"diagnostic-group-persistence-capture:{page_index}",
            )
            primitive_page = normalize_backend_page_capture(capture)
            page_width = primitive_page.page_geometry.width
            page_height = primitive_page.page_geometry.height

            groups, _unparsed = _group_by_pymupdf_line(
                primitive_page.text_primitives, page_width=page_width, page_height=page_height
            )
            if not groups:
                continue

            y_start, y_end = y_window if y_window is not None else (0.0, page_height)

            gaps = _measure_group_persistent_gaps(
                groups,
                page_width=page_width,
                y_start=y_start,
                y_end=y_end,
                bin_width_x=args.bin_width_x,
                bin_height_y=args.bin_height_y,
                min_gap_width=args.min_gap_width,
                min_support_ratio=args.min_support_ratio,
            )
            column_count = len(gaps) + 1
            if not gaps:
                rows.append(
                    {
                        "manual": pdf_path.name,
                        "page": page_number,
                        "y_start": round(y_start, 1),
                        "y_end": round(y_end, 1),
                        "column_count": 1,
                        "gap_start": "",
                        "gap_end": "",
                        "support_ratio": "",
                    }
                )
            for gap_start, gap_end, support in gaps:
                rows.append(
                    {
                        "manual": pdf_path.name,
                        "page": page_number,
                        "y_start": round(y_start, 1),
                        "y_end": round(y_end, 1),
                        "column_count": column_count,
                        "gap_start": round(gap_start, 1),
                        "gap_end": round(gap_end, 1),
                        "support_ratio": round(support, 3),
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
        writer.writerow([row[name] for name in _CSV_FIELDNAMES])


if __name__ == "__main__":
    raise SystemExit(main())
