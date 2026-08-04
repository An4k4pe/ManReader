"""Density of image assets along the aspect axis, and search for a stable valley.

Diagnostico soltanto: nessun producer, nessuna soglia ratificata, nessuna
decisione.

Domanda, registrata prima dell'esecuzione: fra le immagini con lato minore
piccolo, la distribuzione del rapporto d'aspetto ha una VALLE di densita' fra
il modo "quadrato" e il modo "allungato", e quella valle cade nello stesso
posto su editori diversi?

Perche' conta. Il tetto d'area (`_DEFAULT_MAX_AREA_RATIO = 0.28`) e' stato
falsificato mostrando che la distribuzione e' continua: 407 righe fra 0,283 e
0,589 senza salti. Dell'asse forma finora e' stata misurata solo la PREVALENZA
(quota di occorrenze in una fascia scelta a mano, da 0% a 96% a seconda del
manuale), che e' una quantita' diversa e non dice nulla sulla separabilita'.
Questo script misura la separazione. Se la distribuzione e' continua come
quella dell'area, il criterio di forma muore per la stessa ragione e la linea
si chiude; se esiste una valle e cade allo stesso posto su molti editori,
quella e' la differenza sostanziale rispetto a una soglia scelta sul massimo
campionario.

Criteri dichiarati prima di guardare i risultati:

  - VALLE presente se la densita' minima fra i due modi piu' alti scende a
    `--valley-max-ratio` (default 0,50) o meno del piu' basso dei due modi;
  - STABILE se le posizioni delle valli dei manuali che ne hanno una stanno
    entro un fattore 2 fra la minima e la massima;
  - CADUTA se la maggioranza dei manuali con campione sufficiente risulta
    unimodale, oppure se le posizioni delle valli si distribuiscono su piu' di
    un fattore 4.

Il peso primario e' per DIGEST, non per occorrenze: un solo filetto ripetuto
mille volte non deve creare un modo. La versione pesata per occorrenze e'
riportata a fianco come controllo, non come misura principale.

Le pagine escluse dalle precondizioni (`rotation != 0`, `mediabox != cropbox`)
sono contate e riportate, non saltate in silenzio: le due diagnostiche
precedenti sull'asse forma le scartavano senza contatore e l'entita'
dell'esclusione non era nota.

Uso, dalla radice del repository:

    python3 scripts/inspect_aspect_density_valley.py --pdf-dir ./ --json-output ~/valley.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure the density of image assets along log2(aspect) for thin images "
            "and look for a density valley, per manual."
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
        "--minor-max",
        type=int,
        default=16,
        help="Only assets with minor side at or below this. Default 16.",
    )
    parser.add_argument(
        "--bins-per-octave",
        type=int,
        default=4,
        help="Histogram resolution on log2(aspect). Default 4.",
    )
    parser.add_argument(
        "--max-octaves",
        type=int,
        default=10,
        help="Aspect range covered: 1 to 2**N. Default 10 (up to 1024).",
    )
    parser.add_argument(
        "--min-digests",
        type=int,
        default=40,
        help="Manuals below this count in band are reported as insufficient.",
    )
    parser.add_argument(
        "--valley-max-ratio",
        type=float,
        default=0.50,
        help="Valley if min between modes <= this fraction of the lower mode.",
    )
    parser.add_argument("--json-output", type=Path)
    return parser


def _collect(pdf_path: Path, minor_max: int) -> tuple[list[tuple[float, int]], int, int, int]:
    """Return (aspect, occurrences) per digest in band, plus counters."""

    seen: dict[str, tuple[float, int]] = {}
    skipped = 0
    total_pages = 0
    total_images = 0
    with fitz.open(pdf_path) as document:
        page_count = int(document.page_count)
        for page_number in range(1, page_count + 1):
            total_pages += 1
            page = document.load_page(page_number - 1)
            if page.rotation != 0 or page.mediabox != page.cropbox:
                skipped += 1
                continue
            primitive_page = normalize_backend_page_capture(
                capture_pymupdf_page(
                    page,
                    source_id="diagnostic-source",
                    page_id=f"page:{page_number:04d}",
                    capture_id=f"diagnostic:valley:page:{page_number:04d}",
                )
            )
            for image in primitive_page.image_primitives:
                total_images += 1
                digest = image.content_digest
                width = image.intrinsic_width
                height = image.intrinsic_height
                if digest is None or width is None or height is None:
                    continue
                minor = min(width, height)
                major = max(width, height)
                if minor <= 0 or minor > minor_max:
                    continue
                aspect = major / minor
                previous = seen.get(digest)
                seen[digest] = (aspect, (previous[1] if previous else 0) + 1)
    return list(seen.values()), skipped, total_pages, total_images


def _histogram(
    values: list[float], weights: list[int], bins_per_octave: int, max_octaves: int
) -> list[float]:
    bin_count = bins_per_octave * max_octaves
    out = [0.0] * bin_count
    for value, weight in zip(values, weights, strict=True):
        index = 0 if value < 1.0 else int(math.log2(value) * bins_per_octave)
        out[min(max(index, 0), bin_count - 1)] += weight
    return out


def _smooth(counts: list[float]) -> list[float]:
    out: list[float] = []
    for index in range(len(counts)):
        window = counts[max(0, index - 1) : index + 2]
        out.append(sum(window) / len(window))
    return out


def _bin_aspect(index: int, bins_per_octave: int) -> float:
    return float(2 ** ((index + 0.5) / bins_per_octave))


def _find_valley(counts: list[float], bins_per_octave: int, max_ratio: float) -> dict[str, object]:
    smoothed = _smooth(counts)
    peaks = [
        index
        for index in range(len(smoothed))
        if smoothed[index] > 0
        and smoothed[index] >= smoothed[max(0, index - 1)]
        and smoothed[index] >= smoothed[min(len(smoothed) - 1, index + 1)]
    ]
    if len(peaks) < 2:
        return {"valley": None, "reason": "unimodale o senza secondo modo"}
    peaks.sort(key=lambda index: -smoothed[index])
    first, second = sorted(peaks[:2])
    if second - first < 2:
        return {"valley": None, "reason": "modi adiacenti, nessuno spazio per una valle"}
    interior = range(first + 1, second)
    valley_index = min(interior, key=lambda index: smoothed[index])
    lower_mode = min(smoothed[first], smoothed[second])
    depth = smoothed[valley_index] / lower_mode if lower_mode else 1.0
    return {
        "valley": depth <= max_ratio,
        "valley_aspect": round(_bin_aspect(valley_index, bins_per_octave), 2),
        "depth_ratio": round(depth, 3),
        "mode_low_aspect": round(_bin_aspect(first, bins_per_octave), 2),
        "mode_high_aspect": round(_bin_aspect(second, bins_per_octave), 2),
        "reason": "",
    }


def _bar(value: float, peak: float, width: int = 34) -> str:
    if peak <= 0:
        return ""
    return "#" * max(0, int(round(width * value / peak)))


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

    minor_max = cast(int, args.minor_max)
    bins_per_octave = cast(int, args.bins_per_octave)
    max_octaves = cast(int, args.max_octaves)
    min_digests = cast(int, args.min_digests)
    valley_max_ratio = cast(float, args.valley_max_ratio)

    results: list[dict[str, object]] = []
    for label, pdf_path in targets:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato", file=sys.stderr)
            continue
        try:
            rows, skipped, total_pages, total_images = _collect(pdf_path, minor_max)
        except Exception as exc:  # noqa: BLE001
            print(f"[{label}] errore: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        aspects = [aspect for aspect, _ in rows]
        occurrences = [count for _, count in rows]
        digest_hist = _histogram(aspects, [1] * len(aspects), bins_per_octave, max_octaves)
        occ_hist = _histogram(aspects, occurrences, bins_per_octave, max_octaves)

        print(
            f"\n=== {label}   {total_pages} pagine ({skipped} escluse da precondizioni)"
            f"   {total_images} occorrenze immagine"
        )
        print(f"    digest con lato minore <= {minor_max} px: {len(rows)}")
        if len(rows) < min_digests:
            print(f"    CAMPIONE INSUFFICIENTE (< {min_digests}), non analizzato")
            results.append(
                {
                    "label": label,
                    "digests_in_band": len(rows),
                    "sufficient": False,
                    "skipped_pages": skipped,
                }
            )
            continue

        detection = _find_valley(digest_hist, bins_per_octave, valley_max_ratio)
        peak = max(digest_hist)
        print("    densita' per digest lungo l'aspetto (barra = digest, [occ] = occorrenze):")
        for index, value in enumerate(digest_hist):
            if value == 0 and occ_hist[index] == 0:
                continue
            low = _bin_aspect(index, bins_per_octave) / (2 ** (0.5 / bins_per_octave))
            high = low * (2 ** (1 / bins_per_octave))
            marker = ""
            if detection.get("valley") is not None and detection.get("valley_aspect") is not None:
                valley_aspect = cast(float, detection["valley_aspect"])
                if low <= valley_aspect < high:
                    marker = "  <== valle" if detection["valley"] else "  <== minimo (non valle)"
            print(
                f"       {low:>7.2f}-{high:<7.2f} {int(value):>5} {_bar(value, peak):<35}"
                f"[{int(occ_hist[index]):>6}]{marker}"
            )
        if detection["valley"] is None:
            print(f"    NESSUNA VALLE: {detection['reason']}")
        else:
            verdict = "VALLE" if detection["valley"] else "minimo troppo poco profondo"
            print(
                f"    {verdict}: aspetto {detection['valley_aspect']}, "
                f"profondita' {detection['depth_ratio']} del modo piu' basso "
                f"(soglia {valley_max_ratio}); modi a {detection['mode_low_aspect']} "
                f"e {detection['mode_high_aspect']}"
            )

        results.append(
            {
                "label": label,
                "digests_in_band": len(rows),
                "sufficient": True,
                "skipped_pages": skipped,
                "total_pages": total_pages,
                "digest_histogram": digest_hist,
                "occurrence_histogram": occ_hist,
                **detection,
            }
        )

    usable = [r for r in results if r.get("sufficient") and r.get("valley") is True]
    analysed = [r for r in results if r.get("sufficient")]
    print("\n\n=== esito contro i criteri dichiarati")
    print(f"    manuali con campione sufficiente: {len(analysed)}")
    print(f"    manuali con una valle:            {len(usable)}")
    if usable:
        positions = [cast(float, r["valley_aspect"]) for r in usable]
        spread = max(positions) / min(positions) if min(positions) > 0 else float("inf")
        print(
            "    posizioni delle valli: "
            + ", ".join(f"{cast(str, r['label'])}={r['valley_aspect']}" for r in usable)
        )
        print(f"    dispersione (max/min): {spread:.2f}x")
        if spread <= 2.0:
            print("    STABILE secondo il criterio dichiarato (entro un fattore 2)")
        elif spread > 4.0:
            print("    CADUTA: dispersione oltre il fattore 4")
        else:
            print("    intermedio: fra 2x e 4x, non stabile e non caduto")
    if analysed and len(usable) * 2 < len(analysed):
        print("    CADUTA: la maggioranza dei manuali analizzati non ha una valle")

    json_output = cast(Path | None, args.json_output)
    if json_output is not None:
        json_output.write_text(
            json.dumps(
                {
                    "minor_max": minor_max,
                    "bins_per_octave": bins_per_octave,
                    "valley_max_ratio": valley_max_ratio,
                    "manuals": results,
                },
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
