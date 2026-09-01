"""Smoke della pipeline NUOVA: cattura → primitive → IR 2 → Markdown + asset.

Lo smoke storico (`main.py DB.pdf --no-ai`) esercita `extractor.py`, cioe' la
pipeline legacy, e **non tocca una riga** di `pymupdf_capture`,
`primitive_normalizer`, `ir2_builder` o `ir2_markdown`. Serviva a dire «nessun
danno collaterale sulla baseline autorevole» e per quello resta valido, ma non
dice niente sul percorso nuovo. Questo lo dice.

Che cosa verifica, e fallisce rumorosamente se non torna:

1. la cattura produce primitive e le immagini dichiarano `has_stored_resource`;
2. l'IR 2 di ogni pagina passa `validate_page_ir2_against_primitive_page`;
3. **ogni** contenuto raster del documento ha una riga nell'indice -- e' la
   copertura di `AGENTS.MD` §Coverage, «nessuna esclusione puo' essere
   silenziosa»;
4. ogni file scritto e' referenziato da una riga dell'indice ed esiste su disco;
5. nessun file e' scritto per una destinazione che non ha cartella;
6. ogni nota resa nel corpo appartiene a un digest che la politica ammette, e
   il file che nomina esiste;
7. ogni file scritto viene da un metodo di estrazione **dichiarato**
   (`stored` o `stored+mask`): una fotografia della regione di pagina non e'
   l'asset, e una ricodifica silenziosa e' perdita di qualita' nascosta.

Uso::

    ./venv/bin/python scripts/smoke_ir2_assets.py --pdf Apo.pdf --pages 34 35
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import csv  # noqa: E402
import json  # noqa: E402

from build_document_assets import (  # noqa: E402
    capture_pages,
    document_text_scale,
)

from document_asset_policy import (  # noqa: E402
    FOLDER_OF_DESTINATION,
    decide_document_assets,
)
from document_asset_recurrence_measurements import (  # noqa: E402
    measure_document_asset_recurrence,
)
from ir2_markdown import render_page_markdown  # noqa: E402
from ir2_serialization import document_ir2_from_dict  # noqa: E402
from ir2_validate import validate_page_ir2_against_primitive_page  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_asset_extraction import (  # noqa: E402
    METHOD_STORED,
    METHOD_STORED_WITH_MASK,
)
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


class SmokeFailure(Exception):
    """Un invariante dello smoke non regge."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def run_assets(pdf: Path, out: Path) -> list[dict[str, str]]:
    """La passata di documento, con lo stesso script che si usa davvero."""

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "build_document_assets.py"),
         "--pdf", str(pdf.resolve()), "--out", str(out)],
        capture_output=True, text=True, cwd=PROJECT_ROOT, check=False,
    )
    _check(result.returncode == 0, f"build_document_assets e' fallito:\n{result.stderr}")
    index = out / "asset_index.csv"
    _check(index.is_file(), "asset_index.csv non e' stato scritto")
    return list(csv.DictReader(index.open(encoding="utf-8")))


def check_index_covers_everything(pdf: Path, rows: list[dict[str, str]]) -> int:
    """Ogni contenuto del documento ha una riga. Nessuna sparizione silenziosa."""

    with fitz.open(pdf) as document:
        pages = capture_pages(document, None)
    measurements = measure_document_asset_recurrence(pages)
    text_scale = document_text_scale(pages)
    decisions = decide_document_assets(measurements, text_scale=text_scale)

    for primitive_page in pages:
        for primitive in primitive_page.image_primitives:
            _check(
                primitive.has_stored_resource is not None,
                f"{primitive.primitive_id} non dichiara has_stored_resource",
            )

    indexed = {row["digest"] for row in rows if row["digest"]}
    for decision in decisions:
        _check(
            decision.digest in indexed,
            f"il contenuto {decision.digest} non ha una riga nell'indice",
        )
    digestless_rows = sum(1 for row in rows if row["destinazione"] == "senza digest")
    _check(
        digestless_rows == len(measurements.digestless),
        "le occorrenze senza digest non sono tutte nell'indice",
    )
    return len(decisions)


def check_files(out: Path, rows: list[dict[str, str]]) -> int:
    """Ogni file e' referenziato ed esiste; niente file dove non ci va."""

    written = 0
    for row in rows:
        destination, name = row["destinazione"], row["nome_file"]
        if destination == "senza digest":
            continue
        folder = FOLDER_OF_DESTINATION.get(destination, "assente")
        _check(folder != "assente", f"destinazione sconosciuta: {destination!r}")
        if folder is None:
            _check(
                not name,
                f"{destination} non deve scrivere file, e ha scritto {name!r}",
            )
            continue
        if not name:
            continue  # occorrenza fuori pagina, gia' dichiarata nell'indice
        _check(
            (out / folder / name).is_file(),
            f"l'indice nomina {folder}/{name} che non esiste",
        )
        # Il metodo dev'essere uno dei due che l'adattatore di produzione sa
        # produrre. Prima qui c'era `!= "rasterized_clip"`, che dopo il passaggio
        # a `pymupdf_asset_extraction` non poteva piu' scattare: un controllo che
        # non puo' fallire non serve. Cosi' invece qualunque via nuova -- una
        # fotografia della pagina, una ricodifica -- si deve dichiarare qui.
        _check(
            row["metodo"] in (METHOD_STORED, METHOD_STORED_WITH_MASK),
            f"{folder}/{name} viene da un metodo non dichiarato: {row['metodo']!r}",
        )
        written += 1

    for folder in ("images", "assets"):
        directory = out / folder
        if not directory.is_dir():
            continue
        named = {row["nome_file"] for row in rows if row["nome_file"]}
        for path in directory.iterdir():
            _check(
                path.name in named,
                f"{folder}/{path.name} e' su disco e non e' nell'indice",
            )
    return written


def check_page(pdf: Path, page_index: int, out: Path, rows: list[dict[str, str]]) -> int:
    """Una pagina: IR 2 valida, e le note rese puntano a file che esistono."""

    page_directory = out / f"page{page_index}"
    page_directory.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "prototype_ir2_page.py"),
         "--pdf", str(pdf.resolve()), "--page-number", str(page_index + 1),
         "--output-dir", str(page_directory),
         "--arredo", "--elenchi", "--arredo-pagine", "20"],
        capture_output=True, text=True, cwd=PROJECT_ROOT, check=False,
    )
    serialized = page_directory / "document_ir2.json"
    _check(
        serialized.is_file(),
        f"IR 2 non prodotta per idx {page_index}:\n{result.stderr[-2000:]}",
    )
    page = document_ir2_from_dict(json.loads(serialized.read_text(encoding="utf-8"))).pages[0]

    with fitz.open(pdf) as document:
        capture = capture_pymupdf_page(
            document[page_index],
            source_id="diagnostic-source",
            page_id=f"page:{page_index + 1:04d}",
            capture_id=f"vslice:pymupdf:page:{page_index + 1:04d}",
        )
    validate_page_ir2_against_primitive_page(
        page, normalize_backend_page_capture(capture)
    )

    by_digest = {row["digest"]: row for row in rows if row["digest"]}
    notes = frozenset(d for d, r in by_digest.items() if r["nota_nel_corpo"] == "si")
    excluded_path = page_directory / "excluded_ir2.json"
    excluded = (
        frozenset(json.loads(excluded_path.read_text(encoding="utf-8")))
        if excluded_path.is_file()
        else frozenset()
    )
    body = render_page_markdown(
        page, excluded_node_ids=excluded, asset_digests_with_note=notes
    )
    rendered = 0
    for node in page.nodes:
        if node.kind != "asset.note" or node.asset is None:
            continue
        _check(
            node.asset.digest in by_digest,
            f"la nota {node.node_id} ha un digest che l'indice non conosce",
        )
        if node.asset.digest in notes and node.node_id not in excluded:
            row = by_digest[node.asset.digest]
            _check(
                row["cartella"] == "images" and bool(row["nome_file"]),
                f"la nota resa {node.node_id} non ha un file in images/",
            )
            _check(
                (out / row["cartella"] / row["nome_file"]).is_file(),
                f"la nota resa {node.node_id} punta a un file assente",
            )
            rendered += 1
    (page_directory / "body_with_assets.md").write_text(body, encoding="utf-8")
    return sum(1 for line in body.splitlines() if line.startswith("> **["))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument(
        "--pages", type=int, nargs="+", required=True,
        help="indici posizionali 0-based delle pagine da rendere",
    )
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()

    temporary = None
    if arguments.out is None:
        temporary = tempfile.TemporaryDirectory()
        out = Path(temporary.name)
    else:
        out = arguments.out
        out.mkdir(parents=True, exist_ok=True)

    try:
        print(f"smoke IR 2 — {arguments.pdf.name}, pagine {arguments.pages}")
        rows = run_assets(arguments.pdf, out)
        contents = check_index_covers_everything(arguments.pdf, rows)
        print(f"  [ok] indice completo             {contents} contenuti, {len(rows)} righe")
        written = check_files(out, rows)
        print(f"  [ok] file coerenti con l'indice  {written} scritti, metodo dichiarato")
        for page_index in arguments.pages:
            notes = check_page(arguments.pdf, page_index, out, rows)
            print(f"  [ok] idx {page_index:<4} IR 2 valida        {notes} note nel corpo")
    except SmokeFailure as failure:
        print(f"\n  FALLITO: {failure}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None and arguments.out is None:
            print(f"  (uscita in {out}, temporanea)")
    print("\nsmoke SUPERATO")
    if temporary is not None:
        temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
