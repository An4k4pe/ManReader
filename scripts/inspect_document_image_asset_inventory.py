"""Document-wide inventory of image occurrences grouped by content_digest.

Diagnostico soltanto: nessun producer, nessun `RegionCandidate`, nessuna
`PageAnalysis`, nessuno stato mutabile che attraversi le pagine dentro un
contratto, nessuna scrittura fuori da stdout e dal JSON richiesto.

Domanda: la pipeline nuova conta collocazioni
(`ImageOccurrencePrimitive` e' per occorrenza), la pipeline legacy conta
immagini (`get_images` per xref, `rects[0]`, piu' deduplica MD5 fra pagine).
Quanto vale la differenza su un manuale intero?

Riporta:
  N  occorrenze immagine totali
  D  content_digest distinti
  N/D  fattore di collasso
  quota di digest con una sola occorrenza (coda: probabili illustrazioni uniche)
  distribuzione delle occorrenze per digest
  distribuzione delle dimensioni intrinseche in pixel, perche' l'unico filtro
  di scarto raster del legacy e' su quelle (`config.min_image_width/height`)
  e nessun producer della pipeline nuova le guarda

Il raggruppamento e' una funzione pura della collezione di pagine, non un
registro che vive dentro un producer: l'identita' resta page-local, la
ricorrenza e' derivata a livello documento. Il PDF viene aperto una sola volta
e le pagine scorse dentro lo stesso contesto.

Uso, dalla radice del repository:

    python3 scripts/inspect_document_image_asset_inventory.py --pdf Kul.pdf
    python3 scripts/inspect_document_image_asset_inventory.py --pdf DB.pdf --first-page 1 --last-page 60
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Group every image occurrence of a document by content_digest and report "
            "the occurrence-to-asset collapse factor."
        ),
    )
    parser.add_argument("--pdf", type=Path, required=True, help="PDF file to inspect.")
    parser.add_argument("--first-page", type=int, default=1, help="One-based, inclusive.")
    parser.add_argument("--last-page", type=int, default=0, help="One-based, inclusive. 0 = last.")
    parser.add_argument("--json-output", type=Path, help="Optional JSON dump.")
    parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="How many top digests to list. Default: 12.",
    )
    return parser


def _histogram(counts: list[int], edges: tuple[int, ...]) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    previous = 0
    for edge in edges:
        label = f"{previous + 1}-{edge}" if edge - previous > 1 else f"{edge}"
        rows.append((label, sum(1 for value in counts if previous < value <= edge)))
        previous = edge
    rows.append((f">{previous}", sum(1 for value in counts if value > previous)))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    first_page = max(1, cast(int, args.first_page))
    last_page_arg = cast(int, args.last_page)
    top = cast(int, args.top)

    occurrences_by_digest: Counter[str] = Counter()
    pages_by_digest: dict[str, set[int]] = defaultdict(set)
    size_by_digest: dict[str, tuple[float, float]] = {}
    intrinsic_by_digest: dict[str, tuple[int, int] | None] = {}
    total_occurrences = 0
    missing_digest = 0
    skipped_pages = 0

    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        last_page = page_count if last_page_arg <= 0 else min(last_page_arg, page_count)
        for page_number in range(first_page, last_page + 1):
            page = document.load_page(page_number - 1)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                skipped_pages += 1
                continue
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"diagnostic:inventory:page:{page_number:04d}",
                )
            )
            for image in primitive_page.image_primitives:
                total_occurrences += 1
                digest = image.content_digest
                if digest is None:
                    missing_digest += 1
                    continue
                occurrences_by_digest[digest] += 1
                pages_by_digest[digest].add(page_number)
                if digest not in size_by_digest:
                    x0, y0, x1, y1 = image.bbox
                    size_by_digest[digest] = (round(x1 - x0, 1), round(y1 - y0, 1))
                    intrinsic_by_digest[digest] = (
                        (image.intrinsic_width, image.intrinsic_height)
                        if image.intrinsic_width is not None and image.intrinsic_height is not None
                        else None
                    )

    distinct = len(occurrences_by_digest)
    counted = sum(occurrences_by_digest.values())
    singletons = sum(1 for value in occurrences_by_digest.values() if value == 1)
    single_page = sum(1 for pages in pages_by_digest.values() if len(pages) == 1)

    print(f"documento: {pdf_path.name}  pagine {first_page}-{last_page} di {page_count}")
    if skipped_pages:
        print(f"  pagine saltate per precondizioni (rotation/cropbox): {skipped_pages}")
    print()
    print(f"  N  occorrenze immagine        {total_occurrences}")
    print(f"     senza content_digest       {missing_digest}")
    print(f"  D  digest distinti            {distinct}")
    if distinct:
        print(f"     fattore di collasso N/D    {counted / distinct:.1f}")
        print(f"     digest con 1 occorrenza    {singletons}  ({100 * singletons / distinct:.1f}%)")
        print(
            f"     digest su 1 sola pagina    {single_page}  ({100 * single_page / distinct:.1f}%)"
        )

    print()
    print("  distribuzione occorrenze per digest:")
    for label, value in _histogram(
        list(occurrences_by_digest.values()), (1, 2, 5, 10, 25, 50, 100)
    ):
        print(f"     {label:>8}  {value:>5}")

    print()
    print(f"  primi {top} digest per occorrenze:")
    print(f"     {'digest':>14}  {'occorr':>7}  {'pagine':>7}  {'bbox pt':>16}  {'pixel':>14}")
    for digest, count in occurrences_by_digest.most_common(top):
        width, height = size_by_digest[digest]
        intrinsic = intrinsic_by_digest.get(digest)
        pixels = f"{intrinsic[0]}x{intrinsic[1]}" if intrinsic else "-"
        print(
            f"     {digest[:14]:>14}  {count:>7}  {len(pages_by_digest[digest]):>7}  "
            f"{f'{width} x {height}':>16}  {pixels:>14}"
        )

    known_intrinsic = [value for value in intrinsic_by_digest.values() if value is not None]
    print()
    print(f"  dimensione intrinseca nota per {len(known_intrinsic)}/{distinct} digest")
    if known_intrinsic:
        print("  distribuzione del lato minore in pixel (filtro raster del legacy):")
        smaller = [min(width, height) for width, height in known_intrinsic]
        for label, value in _histogram(smaller, (4, 8, 16, 32, 64, 128, 256)):
            print(f"     {label:>8}  {value:>5}")

    json_output = cast(Path | None, args.json_output)
    if json_output is not None:
        payload = {
            "pdf": str(pdf_path),
            "first_page": first_page,
            "last_page": last_page,
            "total_occurrences": total_occurrences,
            "missing_digest": missing_digest,
            "distinct_digests": distinct,
            "digests": [
                {
                    "digest": digest,
                    "occurrences": count,
                    "pages": sorted(pages_by_digest[digest]),
                    "bbox_size": list(size_by_digest[digest]),
                    "intrinsic": list(intrinsic_by_digest[digest] or ()),
                }
                for digest, count in occurrences_by_digest.most_common()
            ],
        }
        json_output.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON scritto in {json_output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
