"""Random-sample driver for prototype_resolve_page_candidates_real_pages.py.

Diagnostico soltanto, nessun producer, nessun wiring, nessuna persistenza fuori
dal file JSONL richiesto. Non decide nulla: estrae un campione casuale
riproducibile di pagine da uno o piu' PDF ed esegue su ciascuna il prototipo di
Resolution gia' committato (ba94a34, Milestone 34), concatenando l'output.

Ragione d'essere: le osservazioni precedenti sulla massa di candidate
`embedded_visual` irrisolte venivano da pagine scelte a mano (DB p.125/48/14/
28/110/99/73), cioe' selezionate perche' interessanti. Un campione scelto a mano
non dice nulla sulla distribuzione. Qui la selezione e' uniforme, senza
reimmissione, con seed fisso: nessuna pagina e' scelta da un umano, e la stessa
riga di comando produce sempre lo stesso campione.

Le pagine rifiutate dalle precondizioni del prototipo (rotation != 0,
cropbox != mediabox) non vengono sostituite: restano nel campione con la loro
categoria PRECONDITION_FAIL. Sostituirle introdurrebbe una selezione.

Uso, dalla radice del repository:

    python3 scripts/sample_resolution_prototype_pages.py \
        --pdf apo=/percorso/Apo.pdf \
        --pdf dag=/percorso/Dag.pdf \
        --output /tmp/proto_sample.jsonl

L'etichetta a sinistra dell'uguale e' arbitraria e serve solo a marcare le righe
di output: nessun nome di manuale e' cablato nel codice.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import cast

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_PROTOTYPE = PROJECT_ROOT / "scripts" / "prototype_resolve_page_candidates_real_pages.py"
_DEFAULT_SEED = "20260802"
_DEFAULT_PAGES_PER_PDF = 6


def _parse_labelled_path(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH, for example dag=/path/Dag.pdf")
    return label, Path(raw_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Draw a reproducible uniform random page sample from one or more PDFs and run "
            "the committed Resolution prototype on each drawn page."
        ),
    )
    parser.add_argument(
        "--pdf",
        action="append",
        default=[],
        type=_parse_labelled_path,
        metavar="LABEL=PATH",
        help="A PDF to sample from. Repeatable.",
    )
    parser.add_argument(
        "--pages-per-pdf",
        type=int,
        default=_DEFAULT_PAGES_PER_PDF,
        help=f"Pages drawn per PDF. Default: {_DEFAULT_PAGES_PER_PDF}.",
    )
    parser.add_argument(
        "--seed",
        type=str,
        default=_DEFAULT_SEED,
        help=f"Sampling seed. Default: {_DEFAULT_SEED}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSONL file to write. Overwritten if it exists.",
    )
    return parser


def _page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as document:
        return int(document.page_count)


def _draw_pages(*, label: str, seed: str, page_count: int, sample_size: int) -> list[int]:
    generator = random.Random(f"{seed}:{label}")
    population = range(1, page_count + 1)
    if sample_size >= page_count:
        return list(population)
    return sorted(generator.sample(population, sample_size))


def _run_one_page(*, label: str, pdf_path: Path, page_number: int) -> dict[str, object]:
    generation_id = f"generation:sample:{label}:{page_number:04d}"
    completed = subprocess.run(
        [
            sys.executable,
            str(_PROTOTYPE),
            str(pdf_path),
            str(page_number),
            "--generation-id",
            generation_id,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    if stdout:
        for line in reversed(stdout.splitlines()):
            try:
                record = cast(dict[str, object], json.loads(line))
            except json.JSONDecodeError:
                continue
            record["sample_label"] = label
            record["prototype_exit_code"] = completed.returncode
            return record
    return {
        "sample_label": label,
        "prototype_exit_code": completed.returncode,
        "category": "DRIVER_NO_JSON",
        "input": {"pdf_path": str(pdf_path), "page_number": page_number},
        "stderr_tail": completed.stderr.strip()[-2000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pdfs = cast(list[tuple[str, Path]], args.pdf)
    if not pdfs:
        print("at least one --pdf LABEL=PATH is required", file=sys.stderr)
        return 1
    if not _PROTOTYPE.is_file():
        print(f"prototype script not found: {_PROTOTYPE}", file=sys.stderr)
        return 1

    sample_size = cast(int, args.pages_per_pdf)
    seed = cast(str, args.seed)
    output_path = cast(Path, args.output)

    plan: list[tuple[str, Path, list[int]]] = []
    for label, pdf_path in pdfs:
        if not pdf_path.is_file():
            print(f"[{label}] file non trovato: {pdf_path} - saltato interamente", file=sys.stderr)
            continue
        page_count = _page_count(pdf_path)
        pages = _draw_pages(
            label=label,
            seed=seed,
            page_count=page_count,
            sample_size=sample_size,
        )
        plan.append((label, pdf_path, pages))
        print(f"[{label}] {page_count} pagine, campione {pages}", file=sys.stderr)

    if not plan:
        print("nessun PDF utilizzabile", file=sys.stderr)
        return 1

    written = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for label, pdf_path, pages in plan:
            for page_number in pages:
                record = _run_one_page(label=label, pdf_path=pdf_path, page_number=page_number)
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                written += 1
                category = record.get("category", "?")
                print(f"[{label} p.{page_number}] {category}", file=sys.stderr)

    print(f"scritte {written} righe in {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
