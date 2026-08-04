"""Image assets mapped on typographic thickness x shape, normalised PAGE-LOCALLY.

Diagnostico soltanto: nessun producer, nessuna soglia ratificata, nessuna
decisione, nessuna classificazione. Le etichette usate qui nominano REGIONI
della mappa, non categorie ratificate.

Perche' questi due assi. La dimensione in pixel intrinseci e' una proprieta' di
come l'editore ha esportato il file: gli stessi filetti misurano 1 px su un
manuale e 12 px su un altro, e su quell'asse nessun confine e' risultato
stabile. La dimensione in punti assoluti e' meglio ma ignora la scala
tipografica: una banda alta 12 pt e' una zebratura in un manuale con corpo 11 e
un filetto grosso in uno con corpo 18. L'asse usato qui e' il lato minore in
punti diviso il corpo del testo, che e' il riferimento rispetto a cui quelle
forme sono state disegnate.

La sola spessore non basta: a parita' di spessore un bollino di elenco puntato
e' quasi quadrato e un filetto e' allungato. Quindi la mappa e' a due
dimensioni, spessore relativo x rapporto d'aspetto, e le regioni si leggono
insieme.

VERSIONE PAGE-LOCAL. La prima versione di questo script accumulava le
`font_size` su tutto il documento e produceva una sola moda per manuale: i
numeri prodotti normalizzavano quindi sul corpo del MANUALE mentre il criterio
che intendevano sostenere e' pagina-locale. Difetto trovato in revisione
indipendente. Qui il corpo e' stimato per ogni pagina (moda delle `font_size`
di quella pagina, arrotondate a 0,5 pt) e ogni occorrenza e' normalizzata sul
corpo della propria pagina; a un asset presente su piu' pagine si attribuisce
la MEDIANA dei rapporti osservati.

Lo script riporta anche quanto il corpo varia fra le pagine dello stesso
manuale: se e' praticamente costante, normalizzare per pagina o per documento
e' indifferente e il difetto non ha effetto pratico; se varia, la differenza
conta e i due risultati non sono confrontabili.

Le pagine dove il corpo non e' stimabile (meno di `--min-text-primitives`
primitive testuali) non vengono normalizzate: le loro immagini sono contate a
parte, non attribuite a una regione.

Uso, dalla radice del repository:

    python3 scripts/inspect_image_typographic_shape.py --pdf-dir ./ --json-output ~/typo_shape.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_RATIO_EDGES = (0.05, 0.1, 0.2, 0.35, 0.6, 1.0, 1.5, 2.5, 5.0)
_RATIO_LABELS = (
    "<=.05",
    ".05-.1",
    ".1-.2",
    ".2-.35",
    ".35-.6",
    ".6-1",
    "1-1.5",
    "1.5-2.5",
    "2.5-5",
    ">5",
)
_ASPECT_EDGES = (1.2, 2.0, 4.0, 8.0, 20.0, 50.0)
_ASPECT_LABELS = ("<=1.2", "1.2-2", "2-4", "4-8", "8-20", "20-50", ">50")


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Map image assets on page-local relative typographic thickness against aspect "
            "ratio, per manual, and report how much the page body size varies."
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
    parser.add_argument("--pdf-dir", type=Path, help="Every *.pdf inside is inspected.")
    parser.add_argument(
        "--min-digests",
        type=int,
        default=20,
        help="Manuals below this asset count are listed but not mapped.",
    )
    parser.add_argument(
        "--min-text-primitives",
        type=int,
        default=20,
        help="Below this the page body size is treated as not estimable.",
    )
    parser.add_argument("--json-output", type=Path)
    return parser


class _Asset:
    __slots__ = ("occurrences", "pages", "ratios", "aspects", "first_page", "first_bbox")

    def __init__(self, first_page: int, first_bbox: tuple[float, float]) -> None:
        self.occurrences = 0
        self.pages: set[int] = set()
        self.ratios: list[float] = []
        self.aspects: list[float] = []
        self.first_page = first_page
        self.first_bbox = first_bbox

    @property
    def ratio(self) -> float:
        return statistics.median(self.ratios)

    @property
    def aspect(self) -> float:
        return statistics.median(self.aspects)


def _bucket(value: float, edges: tuple[float, ...]) -> int:
    for index, edge in enumerate(edges):
        if value <= edge:
            return index
    return len(edges)


def _page_body_size(primitive_page: NormalizedPrimitivePage) -> tuple[float, int]:
    counter: Counter[float] = Counter()
    for text in primitive_page.text_primitives:
        size = text.font_size
        if size is not None and size > 0:
            counter[round(size * 2) / 2] += 1
    if not counter:
        return 0.0, 0
    return counter.most_common(1)[0][0], sum(counter.values())


def _collect(pdf_path: Path, min_text: int) -> dict[str, object]:
    assets: dict[str, _Asset] = {}
    page_bodies: list[float] = []
    skipped = 0
    unestimable_pages = 0
    unnormalised_images = 0
    total_images = 0

    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        for page_number in range(1, page_count + 1):
            page = document.load_page(page_number - 1)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                skipped += 1
                continue
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"diagnostic:typo:page:{page_number:04d}",
                )
            )
            body, text_count = _page_body_size(primitive_page)
            estimable = body > 0 and text_count >= min_text
            if estimable:
                page_bodies.append(body)
            else:
                unestimable_pages += 1

            for image in primitive_page.image_primitives:
                total_images += 1
                digest = image.content_digest
                if digest is None:
                    continue
                x0, y0, x1, y1 = image.bbox
                width = x1 - x0
                height = y1 - y0
                if width <= 0 or height <= 0:
                    continue
                if not estimable:
                    unnormalised_images += 1
                    continue
                minor = min(width, height)
                major = max(width, height)
                asset = assets.get(digest)
                if asset is None:
                    asset = _Asset(page_number, (round(width, 1), round(height, 1)))
                    assets[digest] = asset
                asset.occurrences += 1
                asset.pages.add(page_number)
                asset.ratios.append(minor / body)
                asset.aspects.append(major / minor)

    return {
        "assets": assets,
        "page_bodies": page_bodies,
        "skipped": skipped,
        "unestimable_pages": unestimable_pages,
        "unnormalised_images": unnormalised_images,
        "total_images": total_images,
        "page_count": page_count,
    }


def _report(label: str, collected: dict[str, object], min_digests: int) -> dict[str, object]:
    assets = cast(dict[str, _Asset], collected["assets"])
    bodies = cast(list[float], collected["page_bodies"])
    page_count = cast(int, collected["page_count"])
    values = list(assets.values())

    print(
        f"\n=== {label}   {page_count} pagine "
        f"({collected['skipped']} escluse, {collected['unestimable_pages']} senza corpo "
        f"stimabile)"
    )
    print(
        f"    asset normalizzati {len(values)}   occorrenze immagine "
        f"{collected['total_images']}   non normalizzate "
        f"{collected['unnormalised_images']}"
    )

    if bodies:
        ordered = sorted(bodies)
        low = ordered[int(0.1 * (len(ordered) - 1))]
        high = ordered[int(0.9 * (len(ordered) - 1))]
        spread = high / low if low > 0 else float("inf")
        distinct = len(set(ordered))
        print(
            f"    corpo per pagina: mediana {statistics.median(ordered):g} pt, "
            f"p10 {low:g}, p90 {high:g}, dispersione p90/p10 {spread:.2f}x, "
            f"valori distinti {distinct}"
        )
    if len(values) < min_digests:
        print("    non mappato (troppo pochi asset)")
        return {"label": label, "assets": len(values), "mapped": False}

    grid: Counter[tuple[int, int]] = Counter()
    for asset in values:
        grid[(_bucket(asset.ratio, _RATIO_EDGES), _bucket(asset.aspect, _ASPECT_EDGES))] += 1

    print("\n    asset per spessore relativo (righe) x aspetto (colonne)")
    print("       " + f"{'sp/corpo':>9}" + "".join(f"{name:>8}" for name in _ASPECT_LABELS))
    for row, row_name in enumerate(_RATIO_LABELS):
        if not any(grid.get((row, col), 0) for col in range(len(_ASPECT_LABELS))):
            continue
        cells = "".join(f"{grid.get((row, col), 0) or '':>8}" for col in range(len(_ASPECT_LABELS)))
        print(f"       {row_name:>9}{cells}")

    regions = {
        "filetto": lambda a: a.ratio <= 0.2 and a.aspect >= 8,
        "banda": lambda a: 0.2 < a.ratio <= 1.5 and a.aspect >= 8,
        "bollino": lambda a: a.ratio <= 1.5 and a.aspect < 2,
        "sottile": lambda a: a.ratio <= 1.5 and 2 <= a.aspect < 8,
        "grande": lambda a: a.ratio > 1.5,
    }
    print("\n    regioni nominate (descrittive, non una classificazione):")
    summary: dict[str, list[int]] = {}
    for name, predicate in regions.items():
        chosen = [a for a in values if predicate(a)]
        occurrences = sum(a.occurrences for a in chosen)
        single = sum(1 for a in chosen if len(a.pages) == 1)
        summary[name] = [len(chosen), occurrences, single]
        print(
            f"       {name:<10} {len(chosen):>5} asset {occurrences:>7} occ  "
            f"su 1 pagina {single:>5}"
        )

    return {
        "label": label,
        "assets": len(values),
        "mapped": True,
        "page_body_median": statistics.median(bodies) if bodies else 0.0,
        "page_body_distinct": len(set(bodies)),
        "unestimable_pages": collected["unestimable_pages"],
        "unnormalised_images": collected["unnormalised_images"],
        "regions": summary,
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

    min_digests = cast(int, args.min_digests)
    min_text = cast(int, args.min_text_primitives)

    results: list[dict[str, object]] = []
    for label, pdf_path in targets:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
            continue
        try:
            collected = _collect(pdf_path, min_text)
        except Exception as exc:  # noqa: BLE001
            print(f"[{label}] errore: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        results.append(_report(label, collected, min_digests))

    mapped = [r for r in results if r.get("mapped")]
    if mapped:
        print("\n\n=== confronto fra manuali (asset distinti per regione)")
        print(
            f"{'manuale':>10}{'corpo':>7}{'valori':>8}{'filetto':>9}{'banda':>8}"
            f"{'bollino':>9}{'sottile':>9}{'grande':>8}"
        )
        for result in mapped:
            regions = cast(dict[str, list[int]], result["regions"])
            print(
                f"{cast(str, result['label']):>10}"
                f"{cast(float, result['page_body_median']):>7g}"
                f"{cast(int, result['page_body_distinct']):>8}"
                f"{regions['filetto'][0]:>9}{regions['banda'][0]:>8}"
                f"{regions['bollino'][0]:>9}{regions['sottile'][0]:>9}"
                f"{regions['grande'][0]:>8}"
            )

    json_output = cast(Path | None, args.json_output)
    if json_output is not None:
        json_output.write_text(
            json.dumps({"manuals": results}, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON scritto in {json_output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
