"""Page-local line detection and its coincidence with existing table candidates.

Diagnostico soltanto: nessun producer nuovo, nessuna `PageAnalysis` prodotta
oltre a quella di `table_candidate` gia' committato, nessuna soglia ratificata,
nessuna decisione.

Due domande in una sola lettura dei PDF.

1. STIMABILITA' PAGE-LOCAL. Il criterio di forma normalizza il lato minore di
   un'immagine sul corpo del testo, e il corpo si stima dalla pagina stessa
   (moda delle `font_size` delle primitive testuali di quella pagina). Non
   serve nessun passaggio documentale, quindi il criterio resta una funzione
   pura di una `NormalizedPrimitivePage` e non tocca cache, ordine di
   esecuzione o persistenza. Il rischio non e' divergere da una moda
   documentale -- il riferimento e' la pagina -- ma che su certe pagine il
   corpo non sia stimabile affatto: poche primitive testuali, o nessuna.
   Lo script conta quelle pagine e riporta cosa contengono.

2. LE LINEE SERVONO A VALLE? Le righe raster non sono viste da pdfplumber, che
   lavora su tratti vettoriali e testo: le zebrature e le griglie composte come
   immagini sono invisibili al producer `table_candidate`. Lo script misura,
   per ogni occorrenza classificata come linea o banda dalla forma, quanta
   della sua area cade dentro un `table_candidate` della stessa pagina. Le
   linee dentro una tabella gia' trovata la CONFERMANO; quelle su pagine dove
   `table_candidate` non trova nulla sono candidate a tabelle mancate. Nessuna
   delle due cose e' una regola: sono due conteggi.

Le regioni nominate qui (linea, banda, bollino, grande) etichettano zone della
mappa spessore-relativo x aspetto, non sono una classificazione ratificata.

Le pagine sono campionate per manuale con seed fisso, perche' `find_tables` di
pdfplumber e' lento e leggere tutto significherebbe ore.

Uso, dalla radice del repository:

    python3 scripts/inspect_page_local_lines_vs_tables.py --pdf-dir ./ \
        --pages-per-pdf 40 --json-output ~/lines_tables.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import cast

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geometry_model import BBox  # noqa: E402
from page_analysis_table_candidate import build_table_candidate_page_analysis  # noqa: E402
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_model import NormalizedPrimitivePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_MIN_TEXT_PRIMITIVES = 20
_LINE_MAX_RATIO = 0.2
_BAND_MAX_RATIO = 1.5
_MIN_ASPECT = 8.0


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the body font size page-locally, classify image occurrences by "
            "relative thickness and aspect, and measure how much of the line-like mass "
            "falls inside existing table candidates."
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
    parser.add_argument("--pages-per-pdf", type=int, default=40)
    parser.add_argument("--seed", type=str, default="20260803")
    parser.add_argument("--permutations", type=int, default=20)
    parser.add_argument(
        "--min-text-primitives",
        type=int,
        default=_MIN_TEXT_PRIMITIVES,
        help="Below this the page body size is treated as not estimable.",
    )
    parser.add_argument("--json-output", type=Path)
    return parser


def _page_body_size(primitive_page: NormalizedPrimitivePage) -> tuple[float, int]:
    counter: Counter[float] = Counter()
    for text in primitive_page.text_primitives:
        size = text.font_size
        if size is not None and size > 0:
            counter[round(size * 2) / 2] += 1
    if not counter:
        return 0.0, 0
    return counter.most_common(1)[0][0], sum(counter.values())


def _area(bbox: BBox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _overlap(first: BBox, second: BBox) -> float:
    horizontal = min(first[2], second[2]) - max(first[0], second[0])
    vertical = min(first[3], second[3]) - max(first[1], second[1])
    if horizontal <= 0.0 or vertical <= 0.0:
        return 0.0
    return horizontal * vertical


def _region(ratio: float, aspect: float) -> str:
    if aspect >= _MIN_ASPECT and ratio <= _LINE_MAX_RATIO:
        return "linea"
    if aspect >= _MIN_ASPECT and ratio <= _BAND_MAX_RATIO:
        return "banda"
    if ratio <= _BAND_MAX_RATIO and aspect < 2.0:
        return "bollino"
    if ratio <= _BAND_MAX_RATIO:
        return "sottile"
    return "grande"


def _permutation_control(
    lines: list[BBox],
    tables: list[BBox],
    width: float,
    height: float,
    rounds: int,
    generator: random.Random,
) -> tuple[int, float]:
    """Osservato e atteso sotto ricollocazione casuale sulla stessa pagina."""
    observed = 0
    for box in lines:
        area = _area(box)
        if area > 0 and sum(_overlap(box, t) for t in tables) / area >= 0.5:
            observed += 1
    hits = 0
    for _ in range(rounds):
        for box in lines:
            box_width = box[2] - box[0]
            box_height = box[3] - box[1]
            x = generator.uniform(0.0, max(0.0, width - box_width))
            y = generator.uniform(0.0, max(0.0, height - box_height))
            moved = (x, y, x + box_width, y + box_height)
            area = box_width * box_height
            if area > 0 and sum(_overlap(moved, t) for t in tables) / area >= 0.5:
                hits += 1
    expected = hits / (rounds * len(lines)) if lines else 0.0
    return observed, expected


def _process(
    label: str, pdf_path: Path, pages_per_pdf: int, seed: str, min_text: int, permutations: int
) -> dict[str, object]:
    stats: Counter[str] = Counter()
    coverage_buckets: Counter[str] = Counter()
    lines_on_tableless_pages = 0
    pages_with_lines_no_table = 0

    with fitz.open(pdf_path) as document, pdfplumber.open(str(pdf_path)) as plumber:
        page_count = int(document.page_count)
        generator = random.Random(f"{seed}:{label}")
        population = range(1, page_count + 1)
        chosen = (
            sorted(population)
            if pages_per_pdf >= page_count
            else sorted(generator.sample(population, pages_per_pdf))
        )
        for page_number in chosen:
            page = document.load_page(page_number - 1)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                stats["pagine_scartate"] += 1
                continue
            stats["pagine"] += 1
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"diagnostic:lines:page:{page_number:04d}",
                )
            )
            body, text_count = _page_body_size(primitive_page)
            if body <= 0 or text_count < min_text:
                stats["pagine_corpo_non_stimabile"] += 1
                stats["immagini_su_pagine_non_stimabili"] += len(primitive_page.image_primitives)
                continue

            try:
                table_analysis = build_table_candidate_page_analysis(
                    BoundTableCandidatePage(
                        primitive_page=primitive_page,
                        plumber_page=plumber.pages[page_number - 1],
                    ),
                    generation_id=f"generation:lines:{label}:{page_number:04d}",
                )
                table_boxes = [candidate.bbox for candidate in table_analysis.candidates]
            except Exception:  # noqa: BLE001
                stats["pagine_table_candidate_fallito"] += 1
                table_boxes = []
            stats["table_candidate"] += len(table_boxes)

            page_lines = 0
            page_line_boxes: list[BBox] = []
            page_lines_covered = 0
            for image in primitive_page.image_primitives:
                x0, y0, x1, y1 = image.bbox
                width = x1 - x0
                height = y1 - y0
                if width <= 0 or height <= 0:
                    continue
                minor = min(width, height)
                major = max(width, height)
                region = _region(minor / body, major / minor if minor > 0 else float("inf"))
                stats[f"reg_{region}"] += 1
                if region not in ("linea", "banda"):
                    continue
                page_lines += 1
                page_line_boxes.append(image.bbox)
                area = _area(image.bbox)
                covered = sum(_overlap(image.bbox, box) for box in table_boxes)
                share = covered / area if area > 0 else 0.0
                if share >= 0.5:
                    coverage_buckets[">=0.5"] += 1
                    page_lines_covered += 1
                elif share > 0.0:
                    coverage_buckets["0-0.5"] += 1
                else:
                    coverage_buckets["0"] += 1
            if page_line_boxes and table_boxes:
                observed, expected = _permutation_control(
                    page_line_boxes,
                    table_boxes,
                    float(page.rect.width),
                    float(page.rect.height),
                    permutations,
                    generator,
                )
                stats["perm_linee"] += len(page_line_boxes)
                stats["perm_osservate"] += observed
                stats["perm_attese_x1000"] += int(round(expected * len(page_line_boxes) * 1000))
            if page_lines and not table_boxes:
                pages_with_lines_no_table += 1
                lines_on_tableless_pages += page_lines

    return {
        "label": label,
        "page_count": page_count,
        "stats": dict(stats),
        "coverage": dict(coverage_buckets),
        "pagine_con_linee_senza_tabella": pages_with_lines_no_table,
        "linee_su_pagine_senza_tabella": lines_on_tableless_pages,
    }


def _print(result: dict[str, object]) -> None:
    stats = cast(dict[str, int], result["stats"])
    coverage = cast(dict[str, int], result["coverage"])
    pages = stats.get("pagine", 0)
    print(f"\n=== {result['label']}   {result['page_count']} pagine totali, {pages} campionate")
    unusable = stats.get("pagine_corpo_non_stimabile", 0)
    print(
        f"    corpo non stimabile su {unusable} pagine "
        f"({100 * unusable / pages if pages else 0:.0f}%), "
        f"che contengono {stats.get('immagini_su_pagine_non_stimabili', 0)} immagini"
    )
    regions = ("linea", "banda", "bollino", "sottile", "grande")
    print(
        "    occorrenze per regione: "
        + "  ".join(f"{name} {stats.get(f'reg_{name}', 0)}" for name in regions)
    )
    total_lines = coverage.get(">=0.5", 0) + coverage.get("0-0.5", 0) + coverage.get("0", 0)
    if total_lines:
        print(
            f"    linee+bande: {total_lines}, dentro un table_candidate "
            f">=50% : {coverage.get('>=0.5', 0)} "
            f"({100 * coverage.get('>=0.5', 0) / total_lines:.0f}%), "
            f"parziale {coverage.get('0-0.5', 0)}, "
            f"fuori {coverage.get('0', 0)}"
        )
    perm = stats.get("perm_linee", 0)
    if perm:
        observed = stats.get("perm_osservate", 0) / perm
        expected = stats.get("perm_attese_x1000", 0) / 1000 / perm
        lift = observed / expected if expected > 0 else float("inf")
        print(
            f"    controllo di permutazione: osservato {100 * observed:.0f}%, "
            f"atteso a caso {100 * expected:.0f}%, arricchimento {lift:.1f}x"
        )
    print(
        f"    table_candidate trovati: {stats.get('table_candidate', 0)}"
        f"   pagine con linee ma nessuna tabella: "
        f"{result['pagine_con_linee_senza_tabella']}"
        f" ({result['linee_su_pagine_senza_tabella']} linee)"
    )


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

    pages_per_pdf = cast(int, args.pages_per_pdf)
    seed = cast(str, args.seed)
    min_text = cast(int, args.min_text_primitives)
    permutations = cast(int, args.permutations)

    results: list[dict[str, object]] = []
    for label, pdf_path in targets:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
            continue
        print(f"[{label}] in corso...", file=sys.stderr)
        try:
            result = _process(label, pdf_path, pages_per_pdf, seed, min_text, permutations)
        except Exception as exc:  # noqa: BLE001
            print(f"[{label}] errore: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        _print(result)
        results.append(result)

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
