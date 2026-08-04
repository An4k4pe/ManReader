"""Contact sheet of image assets selected by shape, rendered in page context.

Diagnostico soltanto: nessun producer, nessuna `PageAnalysis`, nessuna soglia
ratificata, nessuna decisione. Produce un PNG da guardare.

Serve a togliere l'inferenza dall'anello. Finora l'identificazione degli asset
e' avvenuta abbinando misure a elementi plausibili su un render a piena pagina,
che e' il modo in cui si confermano le proprie ipotesi senza accorgersene.
Qui ogni asset selezionato viene ritagliato dalla pagina reale con un margine
di contesto e marcato con un rettangolo rosso, cosi' si vede l'oggetto e dove
sta.

Il contesto e' necessario, non decorativo: un asset di 6x1 punti ritagliato
stretto e' una riga di pixel indistinguibile: con 40 punti di margine intorno
si vede se e' il bordo di una cella, un filetto di separazione o altro.

La selezione avviene per banda sull'asse forma (lato minore in pixel x
rapporto d'aspetto), le stesse coordinate di
`inspect_image_shape_axis.py`. I parametri sono esplorativi, non una regola:
servono a guardare una fetta precisa della distribuzione, inclusa quella che un
eventuale criterio LASCEREBBE STARE, per verificare i falsi negativi e non solo
i falsi positivi.

Uso, dalla radice del repository:

    # cosa prenderebbe un criterio di forma
    python3 scripts/render_image_asset_contact_sheet.py --pdf Vil.pdf \
        --minor-max 16 --aspect-min 4 --limit 24 --output ~/vil_presi.png

    # cosa lascerebbe stare: piccolo ma quadrato
    python3 scripts/render_image_asset_contact_sheet.py --pdf Wil.pdf \
        --minor-max 16 --aspect-max 4 --limit 24 --output ~/wil_risparmiati.png
"""

from __future__ import annotations

import argparse
import io
import random
import sys
from pathlib import Path
from typing import cast

import fitz
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_CELL_WIDTH = 380
_IMAGE_HEIGHT = 210
_CAPTION_HEIGHT = 52
_PADDING = 6


class _Asset:
    __slots__ = ("digest", "occurrences", "pages", "minor", "major", "page_number", "bbox")

    def __init__(
        self,
        digest: str,
        minor: int,
        major: int,
        page_number: int,
        bbox: tuple[float, float, float, float],
    ) -> None:
        self.digest = digest
        self.occurrences = 0
        self.pages: set[int] = set()
        self.minor = minor
        self.major = major
        self.page_number = page_number
        self.bbox = bbox

    @property
    def aspect(self) -> float:
        return self.major / self.minor if self.minor else float("inf")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render selected image assets as a labelled contact sheet.",
    )
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="PNG to write.")
    parser.add_argument("--minor-min", type=int, default=0, help="Minor side in pixels, inclusive.")
    parser.add_argument("--minor-max", type=int, default=10**9)
    parser.add_argument("--aspect-min", type=float, default=0.0)
    parser.add_argument("--aspect-max", type=float, default=float("inf"))
    parser.add_argument("--limit", type=int, default=24, help="Assets rendered. Default 24.")
    parser.add_argument("--sample", choices=("random", "frequency"), default="random")
    parser.add_argument("--seed", type=str, default="20260803")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument(
        "--context-pt",
        type=float,
        default=40.0,
        help="Margin in points around the asset bbox. Default 40.",
    )
    parser.add_argument("--zoom", type=float, default=3.0, help="Render zoom. Default 3.")
    parser.add_argument("--first-page", type=int, default=1)
    parser.add_argument("--last-page", type=int, default=0, help="0 = last page.")
    return parser


def _collect(document: fitz.Document, first_page: int, last_page: int) -> dict[str, _Asset]:
    assets: dict[str, _Asset] = {}
    for page_number in range(first_page, last_page + 1):
        page = document.load_page(page_number - 1)
        if page.rotation != 0 or page.mediabox != page.cropbox:
            continue
        primitive_page = normalize_backend_page_capture(
            capture_pymupdf_page(
                page,
                source_id="diagnostic-source",
                page_id=f"page:{page_number:04d}",
                capture_id=f"diagnostic:sheet:page:{page_number:04d}",
            )
        )
        for image in primitive_page.image_primitives:
            digest = image.content_digest
            if digest is None or image.intrinsic_width is None or image.intrinsic_height is None:
                continue
            asset = assets.get(digest)
            if asset is None:
                asset = _Asset(
                    digest=digest,
                    minor=min(image.intrinsic_width, image.intrinsic_height),
                    major=max(image.intrinsic_width, image.intrinsic_height),
                    page_number=page_number,
                    bbox=image.bbox,
                )
                assets[digest] = asset
            asset.occurrences += 1
            asset.pages.add(page_number)
    return assets


def _render_cell(
    document: fitz.Document, asset: _Asset, context_pt: float, zoom: float
) -> Image.Image:
    page = document.load_page(asset.page_number - 1)
    x0, y0, x1, y1 = asset.bbox
    clip = fitz.Rect(x0 - context_pt, y0 - context_pt, x1 + context_pt, y1 + context_pt)
    clip = clip & page.rect
    if clip.is_empty:
        clip = page.rect
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
    crop = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")

    draw = ImageDraw.Draw(crop)
    rect = (
        (x0 - clip.x0) * zoom,
        (y0 - clip.y0) * zoom,
        (x1 - clip.x0) * zoom,
        (y1 - clip.y0) * zoom,
    )
    left, top, right, bottom = rect
    draw.rectangle(
        (left - 1, top - 1, max(right, left + 1) + 1, max(bottom, top + 1) + 1),
        outline=(220, 30, 30),
        width=2,
    )
    return crop


def _fit(image: Image.Image, box_width: int, box_height: int) -> Image.Image:
    ratio = min(box_width / image.width, box_height / image.height)
    if ratio >= 1.0:
        ratio = min(ratio, 8.0)
    width = max(1, int(image.width * ratio))
    height = max(1, int(image.height * ratio))
    return image.resize((width, height), Image.Resampling.NEAREST)


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    minor_min = cast(int, args.minor_min)
    minor_max = cast(int, args.minor_max)
    aspect_min = cast(float, args.aspect_min)
    aspect_max = cast(float, args.aspect_max)
    limit = cast(int, args.limit)
    columns = max(1, cast(int, args.columns))
    context_pt = cast(float, args.context_pt)
    zoom = cast(float, args.zoom)
    output_path = cast(Path, args.output)

    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        first_page = max(1, cast(int, args.first_page))
        last_arg = cast(int, args.last_page)
        last_page = page_count if last_arg <= 0 else min(last_arg, page_count)

        assets = _collect(document, first_page, last_page)
        selected = [
            asset
            for asset in assets.values()
            if minor_min <= asset.minor <= minor_max and aspect_min <= asset.aspect <= aspect_max
        ]
        if cast(str, args.sample) == "frequency":
            selected.sort(key=lambda asset: -asset.occurrences)
        else:
            selected.sort(key=lambda asset: asset.digest)
            random.Random(cast(str, args.seed)).shuffle(selected)
        selected = selected[:limit]

        if not selected:
            print("nessun asset nella banda richiesta", file=sys.stderr)
            return 1

        print(
            f"{pdf_path.name}: {len(assets)} digest totali, {len(selected)} renderizzati",
            file=sys.stderr,
        )

        rows = (len(selected) + columns - 1) // columns
        cell_height = _IMAGE_HEIGHT + _CAPTION_HEIGHT
        sheet = Image.new(
            "RGB",
            (columns * _CELL_WIDTH, rows * cell_height),
            (250, 250, 250),
        )
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default()

        for index, asset in enumerate(selected):
            column = index % columns
            row = index // columns
            origin_x = column * _CELL_WIDTH
            origin_y = row * cell_height
            try:
                crop = _render_cell(document, asset, context_pt, zoom)
            except Exception as exc:  # noqa: BLE001
                draw.text(
                    (origin_x + _PADDING, origin_y + _PADDING),
                    f"errore: {type(exc).__name__}",
                    fill=(200, 0, 0),
                    font=font,
                )
                continue
            thumb = _fit(crop, _CELL_WIDTH - 2 * _PADDING, _IMAGE_HEIGHT - 2 * _PADDING)
            sheet.paste(
                thumb,
                (
                    origin_x + (_CELL_WIDTH - thumb.width) // 2,
                    origin_y + (_IMAGE_HEIGHT - thumb.height) // 2,
                ),
            )
            draw.rectangle(
                (origin_x, origin_y, origin_x + _CELL_WIDTH - 1, origin_y + cell_height - 1),
                outline=(210, 210, 210),
            )
            caption_y = origin_y + _IMAGE_HEIGHT
            lines = [
                f"{asset.digest[:18]}",
                f"{asset.major}x{asset.minor} px   asp {asset.aspect:.1f}"
                f"   {round(asset.bbox[2] - asset.bbox[0], 1)}x"
                f"{round(asset.bbox[3] - asset.bbox[1], 1)} pt",
                f"occ {asset.occurrences} su {len(asset.pages)} pagine"
                f"   prima: pagina PDF {asset.page_number}",
            ]
            for line_index, line in enumerate(lines):
                draw.text(
                    (origin_x + _PADDING, caption_y + 2 + line_index * 14),
                    line,
                    fill=(40, 40, 40),
                    font=font,
                )

        sheet.save(output_path)
        print(f"provino scritto in {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
