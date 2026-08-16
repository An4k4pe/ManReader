"""Le due garanzie dell'albero di bande: conservazione, e nessuna banda che
taglia parole.

G1 -- CONSERVAZIONE. `_segment_tree` promette che ogni gutter accettato compaia
esattamente una volta nell'albero. E' la guardia che distingue una correzione da
un trucco: le scorciatoie ovvie riparano una pagina SCARTANDO un gutter
subordinato, e su una pagina a 3 colonne sopra e 2 sotto perderebbero struttura
vera in silenzio. Qui si rimisura invece di fidarsi del numero storico.

G2 -- NESSUNA BANDA TAGLIA PAROLE. Formulazione dell'utente. Un confine x di
banda che cade dentro il bbox di una primitiva testuale contenuta in quella
banda e' una hard rule violata: la primitiva viene attribuita a una struttura di
colonne a cui non appartiene. Misurato su DB p.53, dove la banda del box eredita
`x0 = 178` dalla colonna del padre e 5 primitive del box scavalcano quel
confine.

Non un producer. Non wired. Sola lettura.

`--page` e i numeri in uscita sono indici POSIZIONALI, vedi `CLAUDE.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
for candidate_dir in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate_dir) not in sys.path:
        sys.path.insert(0, str(candidate_dir))

from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from prototype_derived_column_bands import (  # noqa: E402
    _DEFAULT_MIN_FLANKING_CHARS,
    _process_page,
)
from pymupdf_capture import capture_pymupdf_page  # noqa: E402


def _band_x_edges(row: dict[str, object]) -> list[float]:
    """I confini x che la banda impone: i suoi estremi e i bordi dei gutter."""

    edges = [float(cast(float, row["x0"])), float(cast(float, row["x1"]))]
    for chunk in str(row.get("gutter_x_intervals") or "").split():
        start, _, end = chunk.partition("-")
        try:
            edges.extend((float(start), float(end)))
        except ValueError:
            continue
    return edges


def scan_page(document: fitz.Document, page_index: int, manual: str) -> dict[str, int]:
    try:
        gutters, _bands, tree = _process_page(
            document,
            page_index,
            manual=manual,
            bin_width_x=1.0,
            bin_height_y=2.0,
            min_flanking_groups=2,
            min_flanking_chars=_DEFAULT_MIN_FLANKING_CHARS,
            min_gutter_lines=3.0,
        )
    except Exception:  # noqa: BLE001 - una pagina rotta non ferma lo scan
        return {}
    if not tree:
        return {}

    accepted = [g for g in gutters if not g.get("reject_reason")]

    # G1 si legge da `tree_status`, che il meccanismo assegna gia' da cio' che
    # l'albero CONTIENE davvero. Una versione precedente di questo script
    # contava invece quante volte la stringa x di un gutter comparisse fra le
    # righe, e dava 4 mancanti e 8 duplicati su cinque manuali: falso allarme,
    # perche' `_segment_bands` ripete lo stesso gutter in OGNI fascia y che
    # attraversa, e due gutter distinti alla stessa x sono indistinguibili in
    # quella stringa. La misura sbagliata avrebbe fatto fallire la porta prima
    # ancora di cambiare qualcosa.
    # `edge_strip` NON e' una perdita: e' lo scarto dichiarato del minimo di
    # larghezza ai bordi, con etichetta, e vale per le linguette di capitolo
    # (misurati 4 casi su Fab, tutti quella). Una seconda versione di questo
    # script li contava come conservazione caduta -- secondo falso allarme di
    # fila. Conta solo cio' che sparisce SENZA etichetta.
    missing = sum(
        1 for g in accepted if g.get("tree_status") not in ("band", "edge_strip")
    )
    dropped_labelled = sum(1 for g in accepted if g.get("tree_status") == "edge_strip")

    capture = capture_pymupdf_page(
        document.load_page(page_index),
        source_id="diagnostic-source",
        page_id=f"page:{page_index + 1:04d}",
        capture_id=f"band-invariants:{page_index}",
    )
    primitives = normalize_backend_page_capture(capture).text_primitives

    # G2: un confine x della banda cade dentro il bbox di una primitiva che la
    # banda contiene in y. Il confine e' un taglio: se ci passa dentro del
    # testo, quel testo e' attribuito a una colonna che non e' la sua.
    cut = 0
    for row in tree:
        by0, by1 = float(cast(float, row["y0"])), float(cast(float, row["y1"]))
        edges = _band_x_edges(row)
        for primitive in primitives:
            centre_y = (primitive.bbox[1] + primitive.bbox[3]) / 2.0
            if not (by0 <= centre_y < by1):
                continue
            if any(primitive.bbox[0] < edge < primitive.bbox[2] for edge in edges):
                cut += 1

    return {
        "bands": len(tree),
        "accepted": len(accepted),
        "missing": missing,
        "dropped_labelled": dropped_labelled,
        "cut": cut,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--manuals", nargs="+", required=True)
    parser.add_argument("--max-pages", type=int, default=60)
    args = parser.parse_args(argv)

    totals = {"bands": 0, "accepted": 0, "missing": 0, "dropped_labelled": 0, "cut": 0}
    pages_with_cut = 0
    pages = 0
    for manual in args.manuals:
        pdf_path = cast(Path, args.pdf_dir) / f"{manual}.pdf"
        if not pdf_path.is_file():
            print(f"manca: {pdf_path}", file=sys.stderr)
            continue
        with fitz.open(pdf_path) as document:
            for page_index in range(min(args.max_pages, document.page_count)):
                result = scan_page(document, page_index, manual)
                if not result:
                    continue
                pages += 1
                for key in totals:
                    totals[key] += result[key]
                if result["cut"]:
                    pages_with_cut += 1

    print(f"pagine con almeno una banda: {pages}")
    print(f"bande: {totals['bands']}   gutter accettati: {totals['accepted']}")
    print(
        f"G1 conservazione: spariti senza etichetta {totals['missing']}"
        f"   (scartati con etichetta edge_strip: {totals['dropped_labelled']})"
        f"   -> {'OK' if totals['missing'] == 0 else 'CADUTA'}"
    )
    print(
        f"G2 confini che tagliano una primitiva: {totals['cut']} "
        f"su {pages_with_cut} pagine"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
