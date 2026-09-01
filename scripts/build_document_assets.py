"""Gli asset di un manuale: estratti una volta sola, in due cartelle.

Questo e' il pezzo che la pipeline legacy faceva e che IR 2 non aveva. Il legacy
deduplicava per MD5 (`extractor._seen_image_hashes`, la seconda occorrenza riusa
il file della prima) e saltava la nota per gli sfondi e per i doppioni
(`epub_builder.py:229`). La seconda cartella la descrive `deduplicator.py`, che
pero' **non e' importato da nessun modulo**: `backgrounds/` non e' mai stata
prodotta in un giro normale.

Qui la divisione c'e', e non usa nessuna delle tre soglie cablate del legacy --
80 px di lato minimo, 60% d'area per lo sfondo, 0,15 di pagine per il ripetuto.
Al loro posto due fatti che il documento dichiara, misurati da
`document_asset_recurrence_measurements` e decisi da `document_asset_policy`:

- **su quante pagine il documento colloca lo stesso contenuto** -- una pagina e'
  contenuto, piu' di una e' arredo;
- **quanto e' stretta la collocazione piu' stretta**, contro la lettera piu'
  piccola che il documento stampa.

La regola d'area del legacy manca la barra dorata di Dag, larga il 4% della
pagina e presente su 342 pagine su 379; la ricorrenza la prende.

Uscita::

    <out>/images/           un file per contenuto su una pagina sola
    <out>/assets/           un file per contenuto ripetuto
    <out>/asset_index.csv   ogni contenuto distinto, anche quelli senza file

Uso::

    ./venv/bin/python scripts/build_document_assets.py --pdf Dag.pdf --out /tmp/dag
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from document_asset_catalogue import (  # noqa: E402
    UncataloguedOccurrence,
    build_asset_catalogue,
)
from document_asset_policy import (  # noqa: E402
    BELOW_TEXT_SCALE,
    CONTENT,
    NO_STORED_RESOURCE,
    RECURRING,
    decide_document_assets,
)
from document_asset_recurrence_measurements import (  # noqa: E402
    measure_document_asset_recurrence,
)
from document_heading_measurements import measure_font_sizes  # noqa: E402
from document_heading_policy import prose_sizes  # noqa: E402
from primitive_model import ImageOccurrencePrimitive  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_asset_extraction import extract_occurrence_raster  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

_INDEX_FIELDS = [
    "digest",
    "destinazione",
    "cartella",
    "nome_file",
    "pagine",
    "occorrenze",
    "prima_pagina",
    "estensione_minore_pt",
    "nota_nel_corpo",
    "risorsa_memorizzata",
    "px_per_pt",
    "metodo",
]


def capture_pages(document: fitz.Document, limit: int | None):
    """Cattura e normalizza il documento. L'indice viene dalla pagina."""

    pages = []
    count = len(document) if limit is None else min(limit, len(document))
    for index in range(count):
        capture = capture_pymupdf_page(
            document[index],
            source_id="document-assets",
            page_id=f"page:{index + 1:04d}",
            capture_id=f"assets:pymupdf:page:{index + 1:04d}",
        )
        pages.append(normalize_backend_page_capture(capture))
    return pages


def first_occurrence_of_each_digest(
    pages,
) -> dict[str, tuple[int, ImageOccurrencePrimitive]]:
    """La collocazione da cui estrarre i byte: la prima, come fa il legacy.

    `deduplicator.AssetGroup.representative` sceglie `instances[0]`. Stessa
    scelta e stessa ragione: le occorrenze dello stesso digest hanno lo stesso
    contenuto, e una vale l'altra.
    """

    first: dict[str, tuple[int, ImageOccurrencePrimitive]] = {}
    for primitive_page in pages:
        for primitive in primitive_page.image_primitives:
            digest = primitive.content_digest
            if digest is not None and digest not in first:
                first[digest] = (primitive_page.page_index, primitive)
    return first


def _tri_state(value: bool | None) -> str:
    """`si`/`no`/vuoto. Il vuoto e' «il backend non lo dichiara», non «no»."""

    return "" if value is None else ("si" if value else "no")


def _px_per_pt(primitive: ImageOccurrencePrimitive) -> str:
    """Pixel per punto sulla collocazione, o vuoto se non si puo' calcolare."""

    if primitive.intrinsic_width is None or primitive.intrinsic_height is None:
        return ""
    x0, y0, x1, y1 = primitive.bbox
    width, height = abs(x1 - x0), abs(y1 - y0)
    if width <= 0 or height <= 0:
        return ""
    return f"{max(primitive.intrinsic_width / width, primitive.intrinsic_height / height):.2f}"


def document_text_scale(pages) -> float | None:
    """La lettera piu' piccola che il documento stampa, o None se non si misura.

    `prose_sizes` tace quando ha visto meno di due dimensioni, e qui il silenzio
    si propaga: la policy non scarta niente senza una scala.
    """

    sizes = prose_sizes(measure_font_sizes(pages))
    return min(sizes) if sizes else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="solo le prime N pagine, per una prova rapida",
    )
    arguments = parser.parse_args()

    document = fitz.open(arguments.pdf)
    pages = capture_pages(document, arguments.pages)
    if not pages:
        print("nessuna pagina", file=sys.stderr)
        raise SystemExit(2)

    measurements = measure_document_asset_recurrence(pages)
    text_scale = document_text_scale(pages)
    decisions = decide_document_assets(measurements, text_scale=text_scale)
    first = first_occurrence_of_each_digest(pages)

    arguments.out.mkdir(parents=True, exist_ok=True)
    written: dict[str, int] = {
        CONTENT: 0,
        RECURRING: 0,
        BELOW_TEXT_SCALE: 0,
        NO_STORED_RESOURCE: 0,
    }
    rows: list[dict[str, object]] = []

    # L'estrazione e il catalogo NON stanno qui: stanno in
    # `pymupdf_asset_extraction` e `document_asset_catalogue`, che sono moduli di
    # produzione. Questo script e' un guscio -- legge argomenti, monta le
    # dipendenze, serializza in CSV. Rilievo dell'utente del 31 agosto 2026:
    # giudicare uno script ad hoc non dice come va ManReader.
    info_cache: dict[int, list[dict[str, object]]] = {}

    def raw_info(page_index: int) -> list[dict[str, object]]:
        """Una lettura per pagina, non una per file: era 10 s buttati su Fab."""

        if page_index not in info_cache:
            info_cache[page_index] = document[page_index].get_image_info(
                hashes=True, xrefs=True
            )
        return info_cache[page_index]

    def extract(digest: str):
        page_index, primitive = first[digest]
        return extract_occurrence_raster(
            document,
            document[page_index],
            primitive,
            raw_image_info=raw_info(page_index),
        )

    def store(folder: str, name: str, payload: bytes) -> None:
        target = arguments.out / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(payload)

    catalogue = build_asset_catalogue(
        decisions=decisions,
        first_page_index_of={d: page for d, (page, _) in first.items()},
        extract=extract,
        store=store,
        uncatalogued=tuple(
            UncataloguedOccurrence(
                page_index=occurrence.page_index,
                primitive_id=occurrence.primitive_id,
                reason="nessun content_digest dal backend",
            )
            for occurrence in measurements.digestless
        ),
    )

    for entry in catalogue.entries:
        written[entry.destination] += 1
        page_index, primitive = first[entry.digest]
        rows.append(
            {
                "digest": entry.digest,
                "destinazione": entry.destination,
                "cartella": entry.folder or "",
                "nome_file": entry.file_name or "",
                "pagine": entry.page_count,
                "occorrenze": entry.occurrence_count,
                "prima_pagina": entry.first_page_index,
                "estensione_minore_pt": f"{entry.smallest_placed_extent:.1f}",
                "nota_nel_corpo": "si" if entry.renders_body_note else "no",
                "risorsa_memorizzata": _tri_state(entry.has_stored_resource),
                # Quanti pixel per punto: separa le due famiglie sintetizzate
                # senza inventare un nome per loro. 1,00 = rasterizzato a 72 dpi
                # (i gradienti di Fab); 2,00 = le maschere morbide di DB.
                "px_per_pt": _px_per_pt(primitive),
                "metodo": entry.extraction_method or "",
            }
        )

    for occurrence in catalogue.uncatalogued:
        rows.append(
            {
                "digest": "",
                "destinazione": "senza digest",
                "cartella": "",
                "nome_file": "",
                "pagine": 1,
                "occorrenze": 1,
                "prima_pagina": occurrence.page_index,
                "estensione_minore_pt": "",
                "nota_nel_corpo": "no",
                "risorsa_memorizzata": "",
                "px_per_pt": "",
                "metodo": occurrence.primitive_id,
            }
        )

    index_path = arguments.out / "asset_index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    occurrences = sum(asset.occurrence_count for asset in measurements.assets)
    print(f"pagine                  {measurements.page_count}")
    print(f"scala del testo         {text_scale if text_scale else '(non misurata)'} pt")
    print(f"occorrenze immagine     {occurrences}")
    print(f"contenuti distinti      {len(measurements.assets)}")
    print(f"  images/               {written[CONTENT]}  (con nota nel corpo)")
    print(f"  assets/               {written[RECURRING]}  (ripetuti, senza nota)")
    print(f"  sotto la scala        {written[BELOW_TEXT_SCALE]}  (nessun file, nell'indice)")
    print(
        f"  senza risorsa         {written[NO_STORED_RESOURCE]}"
        "  (nessun file, nell'indice: gradienti e maschere)"
    )
    if measurements.digestless:
        print(f"  senza digest          {len(measurements.digestless)}")
    print(f"indice                  {index_path}")
    document.close()


if __name__ == "__main__":
    main()
