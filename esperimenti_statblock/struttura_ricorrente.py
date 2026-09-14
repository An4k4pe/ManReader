"""La struttura ricorrente e le colonne di tabella come discriminanti delle schede.

Esplorazione (`AGENTS.MD` §16), non decisione. Indicazioni dell'utente, 12
settembre 2026:

- il riquadro «puo' essere un elemento», ma lo stesso sfondo fa anche da box di
  regole, e non va usato come unico discriminante;
- e' una buona indicazione «la ripetizione delle etichette valore varie volte in
  una struttura simile, non posizione, ma struttura», con piu' strutture nello
  stesso manuale (Daggerheart: avversari e ambienti);
- «una tabella come armi ha una serie di righe tutte ordinate con le colonne che
  rispondono a tables o column band. Una scheda ha etichette simili alle
  tabelle», ma non allineate «se non in casi strani»;
- su DB GNOMO, ORCO, GUERRIERO, JALDO e GRUNTA sono schede di PNG e stanno nella
  verita'.

Per un manuale intero, due regole a confronto:

**3a**, com'e' committata: un riquadro (separato se fuso) e' una scheda se
contiene almeno due righe con almeno due coppie etichetta/valore.

**Nuova**: un riquadro e' una scheda se contiene almeno due **righe a campi
libere** -- righe con almeno una coppia che **non** stanno in una colonna di
tabella -- e la sua **struttura ricorre**.

- *Colonna di tabella*: fra il margine sinistro del riquadro (l'inizio piu' a
  sinistra delle sue righe) e l'inizio della riga passa un confine di colonna
  che la tocca in verticale. I confini sono quelli che IR 2 da' gia' alle
  tabelle: i gutter di `column_band` e i confini che Resolution ammette dentro
  i candidati tabella (`prototype_ir2_page.run`). La tolleranza sull'inizio e'
  la larghezza media di un carattere del primo span della riga.
- *Etichette*: quelle di `stat_block_regions.label_spans`, tolte le etichette
  senza lettere ne' cifre, che sono marcatori d'elenco (`✦`).
- *Struttura*: la firma di una regione e' l'insieme delle sue etichette
  normalizzate; due regioni si toccano se condividono almeno due etichette. La
  ricorrenza si riporta in due forme: almeno una regione toccata, e almeno due
  («varie volte»).

Con `--solo-tabelle` contano solo i confini che cadono dentro un candidato
`table_candidate`: variante misurata dopo che la prima ha perso il Wight di
Dragonbane, i cui campi stanno nella colonna di testo destra della scheda.

Fra riquadri sovrapposti che passano la regola vince il piu' ampio, e ogni riga
sta in una regione sola, come in 3a.

Verita': `--verita A` vale se una etichetta contiene A; `--verita A+B` se ci
sono entrambe; piu' `--verita` sono alternative.

Uso:  python struttura_ricorrente.py <pdf> <sigla> --verita ... [--verita ...]
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import fitz  # noqa: E402
import pdfplumber  # noqa: E402
from prototype_ir2_page import (  # noqa: E402
    _build_all_analyses,
    _tree_aware_order,
    _tree_rows_from_contract,
    build_column_band_page_analysis_with_measurements,
    capture_pymupdf_page,
    column_band_gutter_rows,
    measure_rejected_gutters,
    normalize_backend_page_capture,
    resolve_column_boundaries,
)

import stat_block_regions as sbr  # noqa: E402
from ir2_builder import group_source_lines, redrawn_duplicates  # noqa: E402

FRAME_PRODUCERS = ("page_analysis.embedded_visual", "page_analysis.interior_visual_frame")


def normalise(label: str) -> str:
    return "".join(unicodedata.normalize("NFKC", label).casefold().split()).rstrip(":")


def is_label(span) -> bool:
    return any(character.isalnum() for character in span.text)


def select(proposals: list[tuple[tuple[int, ...], dict]]) -> list[dict]:
    """Vince il piu' ampio, ogni riga in una regione sola."""

    proposals.sort(key=lambda proposal: (-len(proposal[0]), proposal[0][0]))
    taken: set[int] = set()
    chosen = []
    for inside, region in proposals:
        if taken.intersection(inside):
            continue
        taken.update(inside)
        chosen.append(region)
    return chosen


def page_regions(document, plumber, index: int, only_tables: bool = False) -> dict[str, list[dict]]:
    page = document[index]
    primitive_page = normalize_backend_page_capture(
        capture_pymupdf_page(page, source_id="s", page_id=f"page:{index + 1:04d}", capture_id="c")
    )
    analyses = _build_all_analyses(primitive_page, plumber_page=plumber.pages[index], generation_id="g")
    bands, measures = build_column_band_page_analysis_with_measurements(primitive_page, generation_id="g")
    ordered, _inside = _tree_aware_order(
        list(primitive_page.text_primitives), _tree_rows_from_contract(bands.candidates, measures)
    )
    deduplicated, _redraws = redrawn_duplicates([primitive for primitive, _g in ordered])
    lines = [line.primitives for line in group_source_lines(deduplicated)]

    # I confini di colonna, come li calcola `prototype_ir2_page.run` per le tabelle.
    band_box = {candidate.candidate_id: candidate.bbox for candidate in bands.candidates}
    gutters = [
        (x0, x1, band_box[measure.candidate_id][1], band_box[measure.candidate_id][3])
        for measure in measures
        for x0, x1 in measure.gutter_x_intervals
    ]
    tables = tuple(
        candidate
        for analysis in analyses
        if analysis.provenance.producer_name == "table_candidate"
        for candidate in analysis.candidates
    )
    admitted = resolve_column_boundaries(
        page_id=primitive_page.page_id,
        rejected_gutters=measure_rejected_gutters(
            primitive_page.page_id, column_band_gutter_rows(primitive_page)
        ),
        table_candidates=tables,
    ).admitted
    gutters += [(b.x0, b.x1, b.y0, b.y1) for b in admitted]
    if only_tables:
        # Variante: solo i confini che cadono dentro un candidato tabella. I
        # gutter fra due colonne di TESTO di una scheda (il Wight) restano fuori.
        gutters = [
            (gx0, gx1, gy0, gy1)
            for gx0, gx1, gy0, gy1 in gutters
            if any(
                t.bbox[0] <= gx0 and gx1 <= t.bbox[2] and gy0 < t.bbox[3] and t.bbox[1] < gy1
                for t in tables
            )
        ]

    frames = [
        sbr.FrameInput(candidate.candidate_id, candidate.bbox, candidate.primitive_ids)
        for analysis in analyses
        if analysis.provenance.producer_name in FRAME_PRODUCERS
        for candidate in analysis.candidates
    ]
    boxes = {
        primitive.primitive_id: primitive.bbox
        for primitive in (*primitive_page.drawing_primitives, *primitive_page.image_primitives)
    }
    line_boxes = [sbr._line_bbox(line) for line in lines]
    labels_of = [[span for span in sbr.label_spans(line) if is_label(span)] for line in lines]
    first_of = [sbr._spans(line)[0] if sbr._spans(line) else None for line in lines]

    old: list[tuple[tuple[int, ...], dict]] = []
    new: list[tuple[tuple[int, ...], dict]] = []
    for frame in frames:
        for piece in sbr.split_frame(frame, boxes, line_boxes):
            inside = tuple(
                i for i, box in enumerate(line_boxes) if box is not None and sbr._centre_inside(piece, box)
            )
            if not inside:
                continue
            margin = min(first_of[i].bbox[0] for i in inside if first_of[i] is not None)
            field = [i for i in inside if labels_of[i]]
            in_column = []
            for i in field:
                first = first_of[i]
                assert first is not None and line_boxes[i] is not None
                width = (first.bbox[2] - first.bbox[0]) / max(len(first.text.strip()), 1)
                start = first.bbox[0]
                _lx0, ly0, _lx1, ly1 = line_boxes[i]
                if any(
                    margin < gx0 and gx1 <= start + width and gy0 < ly1 and ly0 < gy1
                    for gx0, gx1, gy0, gy1 in gutters
                ):
                    in_column.append(i)
            region = {
                "page": index,
                "label": page.get_label() or "",
                "lines": len(inside),
                "first": "".join(p.text for p in lines[inside[0]]).strip()[:40],
                "signature": frozenset(normalise(s.text) for i in inside for s in labels_of[i]),
                "field": len(field),
                "in_column": len(in_column),
            }
            if sum(1 for i in inside if len(labels_of[i]) >= 2) >= 2:
                old.append((inside, dict(region)))
            if len(field) - len(in_column) >= 2:
                new.append((inside, dict(region)))
    return {"3a": select(old), "nuova": select(new)}


def is_true(signature: frozenset[str], truth: list[list[str]]) -> bool:
    return any(all(any(part in label for label in signature) for part in parts) for parts in truth)


def neighbours_of(regions: list[dict]) -> list[int]:
    counts = [0] * len(regions)
    for i, first in enumerate(regions):
        for j in range(i + 1, len(regions)):
            if len(first["signature"] & regions[j]["signature"]) >= 2:
                counts[i] += 1
                counts[j] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("sigla")
    parser.add_argument("--verita", action="append", required=True)
    parser.add_argument("--solo-tabelle", action="store_true")
    args = parser.parse_args(argv)
    truth = [[normalise(part) for part in value.split("+")] for value in args.verita]

    found: dict[str, list[dict]] = {"3a": [], "nuova": []}
    with fitz.open(args.pdf) as document, pdfplumber.open(args.pdf) as plumber:
        for index in range(document.page_count):
            for rule, regions in page_regions(document, plumber, index, args.solo_tabelle).items():
                found[rule].extend(regions)

    for rule, regions in found.items():
        near = neighbours_of(regions)
        for region, count in zip(regions, near, strict=True):
            region["true"] = is_true(region["signature"], truth)
            region["near"] = count
        print(f"\n================ {args.sigla}, regola {rule}: {len(regions)} regioni")
        forms = [("regione", 0)] if rule == "3a" else [("ricorre >= 1", 1), ("ricorre >= 2", 2)]
        for name, minimum in forms:
            kept = [r for r in regions if r["near"] >= minimum]
            counts = Counter(r["true"] for r in kept)
            print(
                f"  {name:14s} tenute {len(kept):4d}: con verita' {counts[True]:4d}, "
                f"senza {counts[False]:4d}   (verita' in tutte le regioni: "
                f"{sum(1 for r in regions if r['true'])})"
            )
        print("  idx [stamp] righe  ver vicini  campi in-colonna  prima riga")
        for r in regions:
            if rule == "3a" and r["true"]:
                continue
            print(
                f"  {r['page']:3d} [{r['label']:>4}] {r['lines']:4d}   {r['true']:d}  {r['near']:5d}  "
                f"{r['field']:5d}  {r['in_column']:8d}   {r['first']!r}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
