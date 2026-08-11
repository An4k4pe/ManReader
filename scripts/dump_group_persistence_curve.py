"""Scarica la curva GREZZA di supporto per ogni bin x, calcolata con la
STESSA griglia fine di `_measure_group_persistent_gaps`
(`prototype_column_gap_group_persistence.py`) -- non i soli run filtrati
sopra soglia, ma ogni bin, cosi' si vede se un segnale debole esiste anche
dove il risultato finale e' "nessun gap" (`column_count=1`).

Motivo per cui esiste: `dump_raw_group_gaps.py` (campionamento ai centri y
di ogni gruppo, richiede >=2 gruppi attivi in quell'istante) si e' rivelato
inadatto su Fab.pdf p.262 -- le voci della lista numerata a sinistra e a
destra hanno altezze leggermente diverse (lunghezza del testo variabile),
quindi i loro centri y non coincidono quasi mai e il campionamento non
cattura mai il momento in cui i due gruppi sono attivi insieme. Questo
script non campiona ai centri dei gruppi: scandisce l'intera altezza con lo
stesso passo fine (`--bin-height-y`, default 2pt) usato dal meccanismo
vero, quindi non ha quel limite.

Duplica la logica di `_measure_group_persistent_gaps` (stesso file di
provenienza, stessi parametri) ma non filtra: restituisce (eligible,
gap_hit, ratio) per ogni bin x, non solo i run contigui sopra soglia.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/dump_group_persistence_curve.py Fab.pdf --page 262 --output /tmp/curve_fab_p262.csv
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

_CSV_FIELDNAMES = (
    "manual",
    "page",
    "bin_x_start",
    "bin_x_end",
    "eligible_count",
    "gap_count",
    "ratio",
)


def _raw_curve(
    groups: list[_Group],
    *,
    page_width: float,
    y_start: float,
    y_end: float,
    bin_width_x: float,
    bin_height_y: float,
) -> list[tuple[float, float, int, int, float]]:
    """Stessa scansione di `_measure_group_persistent_gaps`, senza soglia ne'
    raccolta in run: ritorna (bin_x_start, bin_x_end, eligible, gap_hit, ratio)
    per ogni bin x della pagina."""
    if not groups or bin_width_x <= 0.0 or bin_height_y <= 0.0:
        return []

    n_x_bins = int(page_width // bin_width_x) + 2
    n_y_bins = max(1, int((y_end - y_start) // bin_height_y) + 1)

    eligible = [0] * n_x_bins
    gap_hit = [0] * n_x_bins
    ordered_groups = sorted(groups, key=lambda g: g.y0)

    for y_bin_index in range(n_y_bins):
        y = y_start + y_bin_index * bin_height_y
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

    curve: list[tuple[float, float, int, int, float]] = []
    for b in range(n_x_bins):
        ratio = (gap_hit[b] / eligible[b]) if eligible[b] > 0 else 0.0
        curve.append((b * bin_width_x, (b + 1) * bin_width_x, eligible[b], gap_hit[b], ratio))
    return curve


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="1-indexed page number.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bin-width-x", type=float, default=1.0)
    parser.add_argument("--bin-height-y", type=float, default=2.0)
    parser.add_argument(
        "--only-eligible",
        action="store_true",
        help="Scarica solo i bin con eligible_count > 0 (esclude i bin mai eleggibili, "
        "es. i margini pagina), per leggere la curva piu' facilmente.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    page_index = args.page - 1
    rows: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        if page_index < 0 or page_index >= document.page_count:
            print(f"page out of range: {args.page}", file=sys.stderr)
            return 1
        page = document.load_page(page_index)
        if page.rotation != 0 or page.mediabox != page.cropbox:
            print("rotation/cropbox precondition failed", file=sys.stderr)
            return 1

        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{args.page:04d}",
            capture_id=f"diagnostic-curve-capture:{page_index}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        page_width = primitive_page.page_geometry.width
        page_height = primitive_page.page_geometry.height

        groups, _unparsed = _group_by_pymupdf_line(
            primitive_page.text_primitives, page_width=page_width, page_height=page_height
        )
        print(
            f"{len(groups)} gruppi (block,line) su {pdf_path.name} p.{args.page}", file=sys.stderr
        )

        curve = _raw_curve(
            groups,
            page_width=page_width,
            y_start=0.0,
            y_end=page_height,
            bin_width_x=args.bin_width_x,
            bin_height_y=args.bin_height_y,
        )
        for bin_x_start, bin_x_end, eligible_count, gap_count, ratio in curve:
            if args.only_eligible and eligible_count == 0:
                continue
            rows.append(
                {
                    "manual": pdf_path.name,
                    "page": args.page,
                    "bin_x_start": round(bin_x_start, 1),
                    "bin_x_end": round(bin_x_end, 1),
                    "eligible_count": eligible_count,
                    "gap_count": gap_count,
                    "ratio": round(ratio, 3),
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
