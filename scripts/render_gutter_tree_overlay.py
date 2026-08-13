"""Renderizza sopra la pagina i gutter accettati e l'albero di bande, per
guardare con gli occhi quello che i CSV descrivono per coordinate.

Serve perche' su questa diagnostica ogni risultato pulito letto solo nei numeri
si e' rivelato almeno una volta un artefatto della selezione delle pagine. Un
overlay non dimostra niente da solo, ma rende immediato il tipo di errore che i
conteggi non mostrano: un gutter che cade in mezzo a una colonna, una banda che
taglia un flusso di testo, una sotto-banda che esce dal padre.

Cosa disegna:

  verde        gutter ACCETTATI (rettangolo pieno, semitrasparente)
  rosso        gutter scartati, con il motivo (`reject_reason`) accanto
  blu          bande di primo livello (cornice, tratto spesso)
  arancione    sotto-bande (cornice, tratto sottile), con l'indentazione
               dell'albero resa dallo spessore

Non un producer. Non wired. Diagnostica pura.

Uso:

    python3 scripts/render_gutter_tree_overlay.py DB.pdf --page 83 --output output/tree_db83.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

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

from prototype_derived_column_bands import _process_page  # noqa: E402

_ACCEPTED = (0.0, 0.65, 0.0)
_REJECTED = (0.85, 0.1, 0.1)
_BAND = (0.0, 0.25, 0.9)
_SUBBAND = (0.95, 0.5, 0.0)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="Indice POSIZIONALE nel PDF (page_index = N-1), non il numero stampato.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument(
        "--hide-rejected",
        action="store_true",
        help="Non disegnare i gutter scartati. Utile sulle pagine dove sono tanti.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
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
            min_flanking_chars=5.0,
            min_gutter_lines=3.0,
        )
        page = document.load_page(page_index)

        for row in gutters:
            rejected = bool(row["reject_reason"])
            if rejected and args.hide_rejected:
                continue
            rect = fitz.Rect(
                float(cast(float, row["x0"])),
                float(cast(float, row["y0"])),
                float(cast(float, row["x1"])),
                float(cast(float, row["y1"])),
            )
            colour = _REJECTED if rejected else _ACCEPTED
            annotation = page.draw_rect(rect, color=colour, fill=colour, fill_opacity=0.30, width=0.4)
            del annotation
            if rejected:
                page.insert_text(
                    fitz.Point(rect.x1 + 1.5, rect.y0 + 7),
                    str(row["reject_reason"]),
                    fontsize=4.5,
                    color=_REJECTED,
                )

        for row in tree:
            depth = int(cast(int, row["depth"]))
            rect = fitz.Rect(
                float(cast(float, row["x0"])),
                float(cast(float, row["y0"])),
                float(cast(float, row["x1"])),
                float(cast(float, row["y1"])),
            )
            # Le cornici annidate vengono rientrate di 2pt per livello, cosi'
            # padre e figlio restano distinguibili anche quando condividono un bordo.
            rect = rect + (depth * 2.0, depth * 2.0, -depth * 2.0, -depth * 2.0)
            colour = _BAND if depth == 0 else _SUBBAND
            page.draw_rect(rect, color=colour, width=2.2 if depth == 0 else 1.1)
            page.insert_text(
                fitz.Point(rect.x0 + 2, rect.y0 + 9),
                f"#{row['band_id']} {row['column_count']}col",
                fontsize=6.5,
                color=colour,
            )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom)).save(str(args.output))

    accepted = sum(1 for row in gutters if not row["reject_reason"])
    print(
        f"{pdf_path.name} p.{args.page}: {accepted} gutter accettati, "
        f"{len(gutters) - accepted} scartati, {len(tree)} bande nell'albero",
        file=sys.stderr,
    )
    print(f"scritto {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
