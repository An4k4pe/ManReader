"""Image assets mapped on typographic thickness x shape, per manual.

Diagnostico soltanto: nessun producer, nessuna soglia ratificata, nessuna
decisione, nessuna classificazione. Le etichette usate qui nominano REGIONI
della mappa, non categorie ratificate.

Perche' questi due assi. La dimensione in pixel intrinseci e' una proprieta' di
come l'editore ha esportato il file: gli stessi filetti misurano 1 px su un
manuale e 12 px su un altro, e su quell'asse nessun confine e' risultato
stabile. La dimensione in punti assoluti e' meglio ma ignora la scala
tipografica: una banda alta 12 pt e' una zebratura in un manuale con corpo 11 e
un filetto grosso in uno con corpo 18. L'asse usato qui e' il lato minore in
punti diviso il CORPO DEL TESTO di quel manuale, che e' il riferimento rispetto
a cui quelle forme sono state disegnate.

La sola spessore non basta: a parita' di spessore un bollino di elenco puntato
e' quasi quadrato e un filetto e' allungato. Quindi la mappa e' a due
dimensioni, spessore relativo x rapporto d'aspetto, e le regioni si leggono
insieme.

Il corpo del testo e' stimato come MODA delle `font_size` delle primitive
testuali del manuale (arrotondate a 0,5 pt), con la mediana stampata a fianco
come controllo: la moda coglie il corpo, la mediana viene tirata giu' da note e
didascalie.

Ogni asset e' un `content_digest`. Il lato minore in punti e' quello della
prima occorrenza; lo script conta a parte quanti asset sono collocati a
dimensioni molto diverse fra un'occorrenza e l'altra, perche' in quel caso una
misura sola non li descrive.

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
            "Map image assets on relative typographic thickness (minor side in points "
            "over the manual's body font size) against aspect ratio, per manual."
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
    parser.add_argument("--json-output", type=Path)
    return parser


class _Asset:
    __slots__ = (
        "occurrences",
        "pages",
        "minor_pt",
        "major_pt",
        "min_minor",
        "max_minor",
        "first_page",
    )

    def __init__(self, minor_pt: float, major_pt: float, first_page: int) -> None:
        self.occurrences = 0
        self.pages: set[int] = set()
        self.minor_pt = minor_pt
        self.major_pt = major_pt
        self.min_minor = minor_pt
        self.max_minor = minor_pt
        self.first_page = first_page

    @property
    def aspect(self) -> float:
        return self.major_pt / self.minor_pt if self.minor_pt > 0 else float("inf")


def _bucket(value: float, edges: tuple[float, ...]) -> int:
    for index, edge in enumerate(edges):
        if value <= edge:
            return index
    return len(edges)


def _collect(pdf_path: Path) -> tuple[dict[str, _Asset], float, float, int, int]:
    assets: dict[str, _Asset] = {}
    font_counter: Counter[float] = Counter()
    font_values: list[float] = []
    skipped = 0
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
            for text in primitive_page.text_primitives:
                size = text.font_size
                if size is not None and size > 0:
                    rounded = round(size * 2) / 2
                    font_counter[rounded] += 1
                    font_values.append(size)
            for image in primitive_page.image_primitives:
                digest = image.content_digest
                if digest is None:
                    continue
                x0, y0, x1, y1 = image.bbox
                width = x1 - x0
                height = y1 - y0
                if width <= 0 or height <= 0:
                    continue
                minor = min(width, height)
                major = max(width, height)
                asset = assets.get(digest)
                if asset is None:
                    asset = _Asset(minor, major, page_number)
                    assets[digest] = asset
                asset.occurrences += 1
                asset.pages.add(page_number)
                asset.min_minor = min(asset.min_minor, minor)
                asset.max_minor = max(asset.max_minor, minor)
    mode = font_counter.most_common(1)[0][0] if font_counter else 0.0
    median = statistics.median(font_values) if font_values else 0.0
    return assets, mode, median, skipped, page_count


def _report(
    label: str,
    assets: dict[str, _Asset],
    mode: float,
    median: float,
    skipped: int,
    page_count: int,
    min_digests: int,
) -> dict[str, object]:
    values = list(assets.values())
    print(
        f"\n=== {label}   {page_count} pagine ({skipped} escluse)"
        f"   corpo: moda {mode:g} pt, mediana {median:.1f} pt"
    )
    print(f"    asset distinti {len(values)}   occorrenze {sum(a.occurrences for a in values)}")
    if len(values) < min_digests or mode <= 0:
        print("    non mappato (troppo pochi asset o corpo non stimabile)")
        return {"label": label, "assets": len(values), "mapped": False}

    scaled = sum(1 for a in values if a.min_minor > 0 and a.max_minor / a.min_minor > 1.5)
    if scaled:
        print(
            f"    attenzione: {scaled} asset collocati a dimensioni molto diverse "
            f"(max/min lato minore > 1.5)"
        )

    grid: Counter[tuple[int, int]] = Counter()
    occ: Counter[tuple[int, int]] = Counter()
    for asset in values:
        ratio = asset.minor_pt / mode
        key = (_bucket(ratio, _RATIO_EDGES), _bucket(asset.aspect, _ASPECT_EDGES))
        grid[key] += 1
        occ[key] += asset.occurrences

    print("\n    asset per spessore relativo (righe) x aspetto (colonne)")
    print("       " + f"{'sp/corpo':>9}" + "".join(f"{name:>8}" for name in _ASPECT_LABELS))
    for row, row_name in enumerate(_RATIO_LABELS):
        cells = "".join(f"{grid.get((row, col), 0) or '':>8}" for col in range(len(_ASPECT_LABELS)))
        if any(grid.get((row, col), 0) for col in range(len(_ASPECT_LABELS))):
            print(f"       {row_name:>9}{cells}")

    regions = {
        "filetto      (<=.2 corpo, aspetto>=8)": lambda a: (
            a.minor_pt / mode <= 0.2 and a.aspect >= 8
        ),
        "banda        (.2-1.5 corpo, aspetto>=8)": lambda a: (
            0.2 < a.minor_pt / mode <= 1.5 and a.aspect >= 8
        ),
        "bollino      (<=1.5 corpo, aspetto<2)": lambda a: (
            a.minor_pt / mode <= 1.5 and a.aspect < 2
        ),
        "sottile alt. (<=1.5 corpo, aspetto 2-8)": lambda a: (
            a.minor_pt / mode <= 1.5 and 2 <= a.aspect < 8
        ),
        "grande       (>1.5 corpo)": lambda a: a.minor_pt / mode > 1.5,
    }
    print("\n    regioni nominate (descrittive, non una classificazione):")
    summary: dict[str, list[int]] = {}
    for name, predicate in regions.items():
        chosen = [a for a in values if predicate(a)]
        count = len(chosen)
        occurrences = sum(a.occurrences for a in chosen)
        single = sum(1 for a in chosen if len(a.pages) == 1)
        summary[name.split()[0]] = [count, occurrences, single]
        print(f"       {name:<42} {count:>5} asset {occurrences:>7} occ  su 1 pagina {single:>5}")

    return {
        "label": label,
        "assets": len(values),
        "mapped": True,
        "font_mode": mode,
        "font_median": round(median, 2),
        "scaled_assets": scaled,
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
    results: list[dict[str, object]] = []
    for label, pdf_path in targets:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
            continue
        try:
            assets, mode, median, skipped, page_count = _collect(pdf_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[{label}] errore: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        results.append(_report(label, assets, mode, median, skipped, page_count, min_digests))

    mapped = [r for r in results if r.get("mapped")]
    if mapped:
        print("\n\n=== confronto fra manuali (asset distinti per regione)")
        print(
            f"{'manuale':>10}{'corpo':>7}{'filetto':>9}{'banda':>8}{'bollino':>9}"
            f"{'sottile':>9}{'grande':>8}"
        )
        for result in mapped:
            regions = cast(dict[str, list[int]], result["regions"])
            print(
                f"{cast(str, result['label']):>10}{cast(float, result['font_mode']):>7g}"
                + "".join(
                    f"{regions[key][0]:>9}"
                    if key == "filetto"
                    else f"{regions[key][0]:>8}"
                    if key in ("banda", "grande")
                    else f"{regions[key][0]:>9}"
                    for key in ("filetto", "banda", "bollino", "sottile", "grande")
                )
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
