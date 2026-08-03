"""Read-only inspection of ImageOccurrencePrimitive.content_digest by bbox size.

Diagnostico soltanto: nessun producer, nessun `RegionCandidate`, nessuna
`PageAnalysis`, nessun wiring, nessuna scrittura fuori da stdout o dal JSON
richiesto. Non classifica e non decide.

Domanda a cui risponde: quando piu' immagini di una pagina hanno la stessa
dimensione di bbox, sono la stessa immagine ripetuta o immagini diverse che
condividono la misura? La geometria non lo distingue,
`ImageOccurrencePrimitive.content_digest` (gia' presente in primitive_model.py,
popolato da pymupdf_capture.py via get_image_info(hashes=True)) in linea di
principio si'.

Per ogni pagina richiesta raggruppa le immagini per dimensione di bbox
arrotondata e riporta quante occorrenze e quanti digest distinti ci sono in
ciascun gruppo. Su piu' pagine riporta anche, per ogni digest, su quante pagine
compare: un digest su molte pagine e' arredamento ricorrente, un digest su una
sola pagina e' contenuto locale.

`content_digest` e' opzionale nel contratto: le immagini che ne sono prive
vengono contate a parte e non silenziosamente ignorate.

Uso, dalla radice del repository:

    python3 scripts/inspect_image_content_digest_recurrence.py \
        --pdf /percorso/reale/Kul.pdf --pages 111,153,185,200
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


def _parse_pages(value: str) -> tuple[int, ...]:
    pages: list[int] = []
    for chunk in value.split(","):
        stripped = chunk.strip()
        if not stripped:
            continue
        try:
            page_number = int(stripped)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"not an integer: {stripped!r}") from exc
        if page_number < 1:
            raise argparse.ArgumentTypeError("page numbers are one-based")
        pages.append(page_number)
    if not pages:
        raise argparse.ArgumentTypeError("at least one page number is required")
    return tuple(pages)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Group a page's image primitives by rounded bbox size and report how many "
            "distinct content_digest values each group contains."
        ),
    )
    parser.add_argument("--pdf", type=Path, required=True, help="PDF file to inspect.")
    parser.add_argument(
        "--pages",
        type=_parse_pages,
        required=True,
        metavar="N,N,N",
        help="Comma-separated one-based page numbers.",
    )
    parser.add_argument(
        "--min-group-size",
        type=int,
        default=3,
        help="Only report size groups with at least this many images. Default: 3.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Also write the full result as JSON to this path.",
    )
    return parser


def _inspect_page(
    document: fitz.Document,
    *,
    page_number: int,
) -> list[dict[str, object]]:
    page = document.load_page(page_number - 1)
    primitive_page = normalize_backend_page_capture(
        capture_pymupdf_page(
            page,
            source_id="diagnostic-source",
            page_id=f"diagnostic-page:{page_number:04d}",
            capture_id=f"diagnostic-capture:{page_number:04d}",
        )
    )

    by_size: dict[tuple[float, float], list[str | None]] = defaultdict(list)
    for image in primitive_page.image_primitives:
        x0, y0, x1, y1 = image.bbox
        by_size[(round(x1 - x0, 1), round(y1 - y0, 1))].append(image.content_digest)

    groups: list[dict[str, object]] = []
    for (width, height), digests in by_size.items():
        present = [digest for digest in digests if digest is not None]
        groups.append(
            {
                "page_number": page_number,
                "width": width,
                "height": height,
                "occurrences": len(digests),
                "digest_missing": len(digests) - len(present),
                "distinct_digests": len(set(present)),
                "digests": sorted(set(present)),
            }
        )
    groups.sort(key=lambda group: -cast(int, group["occurrences"]))
    return groups


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdf_path = cast(Path, args.pdf)
    pages = cast(tuple[int, ...], args.pages)
    min_group_size = cast(int, args.min_group_size)

    if not pdf_path.is_file():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    all_groups: list[dict[str, object]] = []
    digest_pages: dict[str, set[int]] = defaultdict(set)
    digest_occurrences: Counter[str] = Counter()

    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        for page_number in pages:
            if not 1 <= page_number <= page_count:
                print(
                    f"p.{page_number} fuori range (il PDF ha {page_count} pagine) - saltata",
                    file=sys.stderr,
                )
                continue
            groups = _inspect_page(document, page_number=page_number)
            all_groups.extend(groups)
            for group in groups:
                for digest in cast(list[str], group["digests"]):
                    digest_pages[digest].add(page_number)
            for group in groups:
                digests = cast(list[str], group["digests"])
                if len(digests) == 1:
                    digest_occurrences[digests[0]] += cast(int, group["occurrences"])

    print(f"{'pag':>5}  {'larghezza x altezza':>22}  {'occorr':>7}  {'digest':>7}  {'senza':>6}")
    for group in all_groups:
        if cast(int, group["occurrences"]) < min_group_size:
            continue
        size = f"{group['width']} x {group['height']}"
        print(
            f"{group['page_number']:>5}  {size:>22}  {group['occurrences']:>7}  "
            f"{group['distinct_digests']:>7}  {group['digest_missing']:>6}"
        )

    multi = {
        digest: sorted(page_set) for digest, page_set in digest_pages.items() if len(page_set) > 1
    }
    print()
    print(f"digest presenti su piu' di una pagina del campione: {len(multi)}")
    for digest, page_list in sorted(multi.items(), key=lambda item: -len(item[1]))[:10]:
        total = digest_occurrences.get(digest, 0)
        print(
            f"   {digest[:16]}...  su {len(page_list)} pagine {page_list}  occorrenze note: {total}"
        )

    json_output = cast(Path | None, args.json_output)
    if json_output is not None:
        payload = {
            "pdf_path": str(pdf_path),
            "pages": list(pages),
            "groups": all_groups,
            "digest_page_counts": {digest: sorted(pgs) for digest, pgs in digest_pages.items()},
        }
        json_output.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON scritto in {json_output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
