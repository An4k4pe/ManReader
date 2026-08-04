"""Cross-manual distribution of image assets on the shape axis (minor side x aspect).

Diagnostico soltanto: nessun producer, nessuna `PageAnalysis`, nessuna soglia
ratificata, nessuna decisione. Descrive una distribuzione e mostra esempi da
guardare; non classifica.

Contesto: il filtro raster del legacy (`config.min_image_width/height = 80`)
scarta per taglia assoluta ed e' risultato inutilizzabile sotto l'obiettivo
"ogni immagine diventa una nota": su Fab elimina 237 icone di contenuto da
16x16 px. L'ipotesi da verificare e' che filetti e immagini non differiscano
per taglia ma per FORMA -- un'immagine con lato minore di pochi pixel e
rapporto d'aspetto estremo e' una riga, non un'illustrazione -- e soprattutto
che questa separazione sia STABILE fra manuali diversi, che e' il punto su cui
il tetto d'area ha fallito.

Misura per ogni manuale, raggruppando le occorrenze per `content_digest`:

  - distribuzione congiunta lato-minore-in-pixel x rapporto d'aspetto
  - quota di occorrenze e di digest nella regione candidata a "riga"
  - fra quelli in regione, quanti compaiono su una sola pagina (che NON prova
    che siano contenuto, ma segnala i casi da guardare per primi)
  - esempi con pagina e bbox, per l'ispezione visiva richiesta da
    `AGENTS.MD` §Regole operative punto 14

`--max-minor-px` e `--min-aspect` sono parametri esplorativi, non una regola:
servono a leggere la stessa fetta di distribuzione su manuali diversi e a
vedere se resta la stessa. Il rapporto d'aspetto e' calcolato sulle dimensioni
intrinseche dell'immagine (proprieta' dell'asset), non sul bbox di
collocazione, che puo' essere deformato.

Uso, dalla radice del repository:

    python3 scripts/inspect_image_shape_axis.py \
        --pdf kul=Kul.pdf --pdf fab=Fab.pdf --pdf db=DB.pdf \
        --json-output /tmp/shape_axis.json

    python3 scripts/inspect_image_shape_axis.py --pdf-dir ~/manuali --samples 8
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_MINOR_EDGES = (2, 4, 8, 16, 32, 64, 128)
_ASPECT_EDGES = (1.5, 2.0, 4.0, 8.0, 16.0, 32.0)


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH, for example kul=/path/Kul.pdf")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Describe the joint distribution of image assets over minor side (pixels) "
            "and aspect ratio, per manual, and print boundary examples to inspect."
        ),
    )
    parser.add_argument(
        "--pdf",
        action="append",
        default=[],
        type=_parse_labelled_path,
        metavar="LABEL=PATH",
        help="A PDF to inspect. Repeatable.",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        help="Directory: every *.pdf inside is inspected, label = file stem.",
    )
    parser.add_argument(
        "--max-minor-px",
        type=int,
        default=4,
        help="Exploratory: minor side at or below this is 'thin'. Default 4.",
    )
    parser.add_argument(
        "--min-aspect",
        type=float,
        default=4.0,
        help="Exploratory: aspect ratio at or above this is 'long'. Default 4.0.",
    )
    parser.add_argument(
        "--samples", type=int, default=5, help="Boundary examples printed per manual. Default 5."
    )
    parser.add_argument(
        "--json-output", type=Path, help="Optional JSON dump of the per-asset rows."
    )
    return parser


class _Asset:
    __slots__ = ("digest", "occurrences", "pages", "minor", "major", "bbox", "first_page")

    def __init__(
        self, digest: str, minor: int, major: int, bbox: tuple[float, float], first_page: int
    ) -> None:
        self.digest = digest
        self.occurrences = 0
        self.pages: set[int] = set()
        self.minor = minor
        self.major = major
        self.bbox = bbox
        self.first_page = first_page

    @property
    def aspect(self) -> float:
        return self.major / self.minor if self.minor else float("inf")


def _collect(pdf_path: Path) -> tuple[dict[str, _Asset], int, int, int]:
    assets: dict[str, _Asset] = {}
    total = 0
    missing = 0
    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        for page_number in range(1, page_count + 1):
            page = document.load_page(page_number - 1)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                continue
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"diagnostic:shape:page:{page_number:04d}",
                )
            )
            for image in primitive_page.image_primitives:
                total += 1
                digest = image.content_digest
                if (
                    digest is None
                    or image.intrinsic_width is None
                    or image.intrinsic_height is None
                ):
                    missing += 1
                    continue
                asset = assets.get(digest)
                if asset is None:
                    x0, y0, x1, y1 = image.bbox
                    asset = _Asset(
                        digest=digest,
                        minor=min(image.intrinsic_width, image.intrinsic_height),
                        major=max(image.intrinsic_width, image.intrinsic_height),
                        bbox=(round(x1 - x0, 1), round(y1 - y0, 1)),
                        first_page=page_number,
                    )
                    assets[digest] = asset
                asset.occurrences += 1
                asset.pages.add(page_number)
    return assets, total, missing, page_count


def _bucket(value: float, edges: tuple[float, ...] | tuple[int, ...]) -> int:
    for index, edge in enumerate(edges):
        if value <= edge:
            return index
    return len(edges)


def _labels(edges: tuple[float, ...] | tuple[int, ...], integer: bool) -> list[str]:
    out: list[str] = []
    previous: float | int = 0
    for edge in edges:
        out.append(f"<={edge:g}" if previous == 0 else f"{previous:g}-{edge:g}")
        previous = edge
    out.append(f">{previous:g}")
    return out


def _report(
    label: str,
    assets: dict[str, _Asset],
    total: int,
    missing: int,
    page_count: int,
    max_minor: int,
    min_aspect: float,
    samples: int,
) -> dict[str, object]:
    values = list(assets.values())
    distinct = len(values)
    grid: Counter[tuple[int, int]] = Counter()
    occ_grid: Counter[tuple[int, int]] = Counter()
    for asset in values:
        key = (_bucket(asset.minor, _MINOR_EDGES), _bucket(asset.aspect, _ASPECT_EDGES))
        grid[key] += 1
        occ_grid[key] += asset.occurrences

    in_region = [a for a in values if a.minor <= max_minor and a.aspect >= min_aspect]
    region_occ = sum(a.occurrences for a in in_region)
    region_single = [a for a in in_region if len(a.pages) == 1]
    outside_thin = [a for a in values if a.minor <= max_minor and a.aspect < min_aspect]

    print(f"\n=== {label}  ({page_count} pagine)")
    print(f"    occorrenze {total}   digest {distinct}   senza dati {missing}")
    print(f"    regione lato<={max_minor}px e aspetto>={min_aspect:g}:")
    print(
        f"       digest {len(in_region)} ({100 * len(in_region) / distinct if distinct else 0:.0f}%)"
        f"   occorrenze {region_occ} ({100 * region_occ / total if total else 0:.0f}%)"
        f"   di cui su 1 pagina: {len(region_single)}"
    )
    print(
        f"    sottili ma NON allungate (lato<={max_minor}px, aspetto<{min_aspect:g}): "
        f"{len(outside_thin)} digest"
    )

    minor_labels = _labels(_MINOR_EDGES, True)
    aspect_labels = _labels(_ASPECT_EDGES, False)
    print("\n    digest per lato minore (righe) x aspetto (colonne):")
    print("       " + "".join(f"{name:>9}" for name in ["lato\\asp", *aspect_labels]))
    for row_index, row_name in enumerate(minor_labels):
        cells = "".join(
            f"{grid.get((row_index, col_index), 0):>9}" for col_index in range(len(aspect_labels))
        )
        print(f"       {row_name:>9}{cells}")

    boundary = sorted(
        (a for a in values if a.minor <= max_minor * 4 and a.aspect >= min_aspect / 2),
        key=lambda a: -a.occurrences,
    )
    if boundary:
        print("\n    esempi al confine, da guardare (pagina, bbox pt, pixel, aspetto):")
        for asset in boundary[:samples]:
            print(
                f"       p.{asset.first_page:<5} {asset.bbox[0]}x{asset.bbox[1]} pt"
                f"   {asset.major}x{asset.minor} px   asp {asset.aspect:.1f}"
                f"   occ {asset.occurrences} su {len(asset.pages)} pagine"
            )

    return {
        "label": label,
        "page_count": page_count,
        "occurrences": total,
        "distinct": distinct,
        "region_digests": len(in_region),
        "region_occurrences": region_occ,
        "region_single_page": len(region_single),
        "thin_not_long": len(outside_thin),
        "assets": [
            {
                "digest": a.digest,
                "occurrences": a.occurrences,
                "pages": len(a.pages),
                "first_page": a.first_page,
                "bbox": list(a.bbox),
                "minor_px": a.minor,
                "major_px": a.major,
                "aspect": round(a.aspect, 2),
            }
            for a in sorted(values, key=lambda a: -a.occurrences)
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    targets: list[tuple[str, Path]] = list(cast(list[tuple[str, Path]], args.pdf))
    pdf_dir = cast(Path | None, args.pdf_dir)
    if pdf_dir is not None:
        if not pdf_dir.is_dir():
            print(f"not a directory: {pdf_dir}", file=sys.stderr)
            return 1
        targets.extend((path.stem, path) for path in sorted(pdf_dir.glob("*.pdf")))
    if not targets:
        print("at least one --pdf LABEL=PATH or --pdf-dir is required", file=sys.stderr)
        return 1

    max_minor = cast(int, args.max_minor_px)
    min_aspect = cast(float, args.min_aspect)
    samples = cast(int, args.samples)

    summaries: list[dict[str, object]] = []
    for label, pdf_path in targets:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
            continue
        try:
            assets, total, missing, page_count = _collect(pdf_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[{label}] errore: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        summaries.append(
            _report(label, assets, total, missing, page_count, max_minor, min_aspect, samples)
        )

    if summaries:
        print(
            f"\n\n=== confronto fra manuali (regione lato<={max_minor}px e aspetto>={min_aspect:g})"
        )
        print(
            f"{'manuale':>14}{'pagine':>8}{'occorr':>9}{'digest':>8}"
            f"{'occ in reg':>12}{'%':>6}{'dig in reg':>12}{'1 pagina':>10}"
        )
        for summary in summaries:
            occurrences = cast(int, summary["occurrences"])
            region = cast(int, summary["region_occurrences"])
            print(
                f"{summary['label']:>14}{summary['page_count']:>8}{occurrences:>9}"
                f"{summary['distinct']:>8}{region:>12}"
                f"{100 * region / occurrences if occurrences else 0:>5.0f}%"
                f"{summary['region_digests']:>12}{summary['region_single_page']:>10}"
            )

    json_output = cast(Path | None, args.json_output)
    if json_output is not None:
        json_output.write_text(
            json.dumps(
                {"max_minor_px": max_minor, "min_aspect": min_aspect, "manuals": summaries},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nJSON scritto in {json_output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
