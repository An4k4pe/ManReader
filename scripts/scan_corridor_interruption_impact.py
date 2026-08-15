"""Quante bande cambierebbero se il corridoio si interrompesse, e di quanto.

Raggio d'azione di `Criterio_InterruzioneCorridoio_v1.md`, cioe' del flag
`--interrupt-corridor` di `prototype_vertical_slice_page.py`. NON e' una misura
di accuratezza: dice quante bande la regola tocca, non quante ne migliora. Per
sapere se il taglio e' giusto bisogna guardare le pagine.

Riusa `_corridor_blockers` e `_split_bands_at_crossings` dal consumer invece di
reimplementarle: una seconda implementazione divergerebbe, ed e' gia' successo
su questo progetto con le due definizioni di orientamento del testo.

Costruisce il solo `embedded_visual` invece dei cinque producer perche'
`_corridor_blockers` filtra per `proposed_structural_kind` e gli altri quattro
non contribuiscono blocker: i blocker prodotti sono identici a quelli della
fetta completa, senza il costo di pdfplumber.

`--page` e i numeri di pagina in uscita sono indici POSIZIONALI
(`page_index = N - 1`), non i numeri stampati: vedi `CLAUDE.md`.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
for candidate_dir in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate_dir) not in sys.path:
        sys.path.insert(0, str(candidate_dir))

from prototype_vertical_slice_page import (  # noqa: E402
    _corridor_blockers,
    _split_bands_at_crossings,
)

from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from prototype_derived_column_bands import (  # noqa: E402
    _DEFAULT_MIN_FLANKING_CHARS,
    _process_page,
)
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def _unused_bands_by_id(tree: list[dict[str, object]]) -> dict[int, list[dict[str, object]]]:
    out: dict[int, list[dict[str, object]]] = {}
    for row in tree:
        out.setdefault(int(cast(int, row["band_id"])), []).append(row)
    return out


def scan_page(
    document: fitz.Document, page_index: int, manual: str, blockers_from: str = "both"
) -> list[dict[str, object]]:
    try:
        _gutters, _bands, tree = _process_page(
            document,
            page_index,
            manual=manual,
            bin_width_x=1.0,
            bin_height_y=2.0,
            min_flanking_groups=2,
            min_flanking_chars=_DEFAULT_MIN_FLANKING_CHARS,
            min_gutter_lines=3.0,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostica: una pagina rotta non ferma lo scan
        print(f"  {manual} p.{page_index + 1}: _process_page fallita ({exc})", file=sys.stderr)
        return []
    if not tree:
        return []

    page = document.load_page(page_index)
    capture = capture_pymupdf_page(
        page,
        source_id="diagnostic-source",
        page_id=f"page:{page_index + 1:04d}",
        capture_id=f"corridor-impact:{page_index}",
    )
    primitive_page = normalize_backend_page_capture(capture)
    analyses = (build_embedded_visual_page_analysis(primitive_page, generation_id="scan"),)
    if blockers_from == "visuals":
        # Solo i candidati: si azzera il contributo dei filetti passando una
        # pagina senza DrawingPrimitive al raccoglitore.
        blockers = [
            candidate.bbox
            for analysis in analyses
            for candidate in analysis.candidates
            if candidate.proposed_structural_kind == "layout.embedded_visual"
        ]
    elif blockers_from == "drawings":
        blockers = [
            bbox
            for bbox in _corridor_blockers(primitive_page=primitive_page, analyses=())
        ]
    else:
        blockers = _corridor_blockers(primitive_page=primitive_page, analyses=analyses)
    cut_tree = _split_bands_at_crossings(tree, blockers)

    original = {int(cast(int, r["band_id"])): r for r in tree}
    # I pezzi si raggruppano per `origin_band_id`, non per contenimento
    # geometrico: dentro l'intervallo di una banda cadono anche i pezzi delle
    # sue figlie, e contarli produceva perfino tagli negativi (DB p.3, -128pt).
    by_origin: dict[int, list[dict[str, object]]] = {}
    for piece in cut_tree:
        by_origin.setdefault(int(cast(int, piece["origin_band_id"])), []).append(piece)

    rows: list[dict[str, object]] = []
    for band_id, row in original.items():
        y0, y1 = float(cast(float, row["y0"])), float(cast(float, row["y1"]))
        all_pieces = by_origin.get(band_id, [])
        covered = sum(
            float(cast(float, p["y1"])) - float(cast(float, p["y0"])) for p in all_pieces
        )
        removed = (y1 - y0) - covered
        if removed <= 0.01 and len(all_pieces) <= 1:
            continue
        rows.append(
            {
                "manual": manual,
                "page_positional": page_index + 1,
                "band_id": band_id,
                "band_y0": round(y0, 1),
                "band_y1": round(y1, 1),
                "band_height": round(y1 - y0, 1),
                "pieces": len(all_pieces),
                "removed_pt": round(removed, 1),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuals", nargs="+", required=True)
    parser.add_argument("--max-pages", type=int, default=60)
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument(
        "--blockers", choices=("both", "drawings", "visuals"), default="both",
        help="quale sorgente di blocker considerare, per attribuire il raggio d'azione",
    )
    args = parser.parse_args(argv)

    all_rows: list[dict[str, object]] = []
    total_bands = 0
    for manual in args.manuals:
        pdf_path = cast(Path, args.pdf_dir) / f"{manual}.pdf"
        if not pdf_path.is_file():
            print(f"manca: {pdf_path}", file=sys.stderr)
            continue
        with fitz.open(pdf_path) as document:
            for page_index in range(min(args.max_pages, document.page_count)):
                try:
                    _g, _b, tree = _process_page(
                        document,
                        page_index,
                        manual=manual,
                        bin_width_x=1.0,
                        bin_height_y=2.0,
                        min_flanking_groups=2,
                        min_flanking_chars=_DEFAULT_MIN_FLANKING_CHARS,
                        min_gutter_lines=3.0,
                    )
                    total_bands += len(tree)
                except Exception:  # noqa: BLE001
                    pass
                all_rows.extend(scan_page(document, page_index, manual, args.blockers))

    all_rows.sort(key=lambda r: cast(float, r["removed_pt"]), reverse=True)
    print(f"blocker considerati: {args.blockers}")
    print(f"bande esaminate: {total_bands}")
    print(f"bande toccate dalla regola: {len(all_rows)}")
    if total_bands:
        print(f"quota: {100 * len(all_rows) / total_bands:.1f}%")
    print("\nle dieci con il taglio piu' grande:")
    for row in all_rows[:10]:
        print(
            f"  {row['manual']} p.{row['page_positional']:>4} "
            f"banda y {row['band_y0']:>6}-{row['band_y1']:<6} "
            f"alta {row['band_height']:>6}pt -> {row['pieces']} pezzi, "
            f"tolti {row['removed_pt']}pt"
        )

    if args.csv_output is not None:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()) if all_rows else [])
            if all_rows:
                writer.writeheader()
                writer.writerows(all_rows)
        print(f"\nscritto {args.csv_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
