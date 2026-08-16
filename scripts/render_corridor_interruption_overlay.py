"""Le bande prima e dopo l'interruzione del corridoio, sulla stessa pagina.

Stesso scopo di `render_gutter_tree_overlay.py` e stessa ragione: su questa
diagnostica ogni risultato pulito letto nei soli numeri si e' rivelato almeno
una volta un artefatto. "11 bande diventano 50" non dice se il taglio cade dove
serve; l'overlay si'.

Cosa disegna:

  verde        i gutter accettati, ciascuno sulla PROPRIA fascia probatoria
  blu          bande PRIMA (`prototype_derived_column_bands`), tratto spesso
  arancione    bande DOPO l'interruzione, tratto sottile e rientrato di 2pt
               cosi' resta visibile anche dove coincide con quella blu
  rosso        i blocker che ATTRAVERSANO davvero un gutter, cioe' quelli che
               hanno prodotto un taglio
  grigio       i blocker raccolti che non attraversano nulla, per rendere
               visibile quanto della raccolta sia inerte

Riusa `_corridor_blockers` e `_split_bands_at_crossings` dal consumer: una
seconda implementazione divergerebbe da quella misurata.

`--page` e' un indice POSIZIONALE (`page_index = N - 1`), vedi `CLAUDE.md`.

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/render_corridor_interruption_overlay.py Dag.pdf --page 164 --output output/cut_dag164.png
"""

from __future__ import annotations

import argparse
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

_BLUE = (0.10, 0.35, 0.85)
_ORANGE = (0.95, 0.45, 0.05)
_RED = (0.85, 0.10, 0.10)
_GREY = (0.65, 0.65, 0.65)
_GREEN = (0.05, 0.60, 0.20)


def _gutters_of(row: dict[str, object]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for chunk in str(row.get("gutter_x_intervals") or "").split():
        start, _, end = chunk.partition("-")
        try:
            out.append((float(start), float(end)))
        except ValueError:
            continue
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="indice POSIZIONALE")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument(
        "--blockers", choices=("both", "drawings", "visuals"), default="drawings"
    )
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF non trovato: {pdf_path}", file=sys.stderr)
        return 1
    page_index = args.page - 1

    with fitz.open(pdf_path) as document:
        if not 0 <= page_index < document.page_count:
            print(f"pagina fuori range: {args.page}", file=sys.stderr)
            return 1
        gutters, _bands, tree = _process_page(
            document,
            page_index,
            manual=pdf_path.name,
            bin_width_x=1.0,
            bin_height_y=2.0,
            min_flanking_groups=2,
            min_flanking_chars=_DEFAULT_MIN_FLANKING_CHARS,
            min_gutter_lines=3.0,
        )
        accepted_gutters = [g for g in gutters if not g.get("reject_reason")]
        page = document.load_page(page_index)
        capture = capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"page:{args.page:04d}",
            capture_id=f"corridor-overlay:{page_index}",
        )
        primitive_page = normalize_backend_page_capture(capture)
        analyses = (
            build_embedded_visual_page_analysis(primitive_page, generation_id="overlay"),
        )
        blockers = _corridor_blockers(
            primitive_page=primitive_page, analyses=analyses, sources=args.blockers
        )
        cut_tree = _split_bands_at_crossings(tree, blockers)

        # Quali blocker hanno davvero tagliato qualcosa: stesso test di
        # `_split_bands_at_crossings`, cosi' il rosso non promette piu' del vero.
        crossing: list[tuple[float, float, float, float]] = []
        for bbox in blockers:
            bx0, by0, bx1, by1 = bbox
            for row in tree:
                y0, y1 = float(cast(float, row["y0"])), float(cast(float, row["y1"]))
                if by1 <= y0 or by0 >= y1:
                    continue
                if any(bx0 <= gx0 and bx1 >= gx1 for gx0, gx1 in _gutters_of(row)):
                    crossing.append(bbox)
                    break

        for bbox in blockers:
            colour = _RED if bbox in crossing else _GREY
            rect = fitz.Rect(bbox[0], bbox[1] - 0.6, bbox[2], bbox[3] + 0.6)
            page.draw_rect(rect, color=colour, fill=colour, fill_opacity=0.55, width=0.3)

        # I gutter accettati, ciascuno sulla PROPRIA fascia y e non su quella
        # della banda. Due versioni precedenti di questo overlay hanno sviato la
        # lettura: la prima non li disegnava affatto, la seconda li tirava per
        # tutta l'altezza della banda, facendo sembrare che il meccanismo
        # vedesse un corridoio dove non lo vede.
        #
        # Verde pieno: la fascia PROBATORIA (`y0`/`y1`), dove entrambi i lati
        # sono attivi e il gutter e' dimostrato.
        # Verde a contorno: lo SPAN, cioe' fin dove l'estensione lo porta. La
        # distinzione e' quella che decide la nidificazione, quindi va vista.
        for gutter in accepted_gutters:
            gx0 = float(cast(float, gutter["x0"]))
            gx1 = float(cast(float, gutter["x1"]))
            gy0 = float(cast(float, gutter["y0"]))
            gy1 = float(cast(float, gutter["y1"]))
            page.draw_rect(
                fitz.Rect(gx0, gy0, gx1, gy1),
                color=_GREEN,
                fill=_GREEN,
                fill_opacity=0.45,
                width=1.2,
            )

        for row in tree:
            rect = fitz.Rect(
                float(cast(float, row["x0"])),
                float(cast(float, row["y0"])),
                float(cast(float, row["x1"])),
                float(cast(float, row["y1"])),
            )
            page.draw_rect(rect, color=_BLUE, width=2.4)

        for row in cut_tree:
            rect = fitz.Rect(
                float(cast(float, row["x0"])) + 2.0,
                float(cast(float, row["y0"])) + 2.0,
                float(cast(float, row["x1"])) - 2.0,
                float(cast(float, row["y1"])) - 2.0,
            )
            page.draw_rect(rect, color=_ORANGE, width=1.0)

        page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom)).save(str(args.output))

    print(
        f"{pdf_path.name} p.{args.page}: bande {len(tree)} -> {len(cut_tree)}, "
        f"blocker {len(blockers)} di cui attraversanti {len(crossing)} -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
