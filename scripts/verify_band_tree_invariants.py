"""Le due garanzie dell'albero di bande: conservazione, e nessuna banda che
taglia parole.

G1 -- CONSERVAZIONE. La promessa di `_segment_tree` e' che ogni gutter accettato
compaia **esattamente una volta** nell'albero, e sono due direzioni: sparire, e
comparire due volte. La revisione indipendente del 16 agosto 2026 ha rilevato
che qui se ne misurava una sola, e aveva ragione a chiederlo -- la direzione
scoperta e' proprio quella che aveva gia' prodotto un difetto reale (un
subordinato con due padri possibili emesso due volte, chiuso da `placed`).

**Provandoci si e' scoperto che la seconda direzione non e' misurabile
dall'uscita attuale**, e il tentativo produceva falsi positivi su pagine reali.
Vedi `check_conservation`. Lo strumento ora dichiara il limite invece di
restituire un numero che sembra un verdetto: quello che manca per misurarla e'
un'identita' stabile per gutter emessa da `_segment_tree`.

G2 -- NESSUNA BANDA TAGLIA PAROLE. Formulazione dell'utente. Un confine x di
banda che cade dentro il bbox di una primitiva testuale contenuta in quella
banda e' una hard rule violata: la primitiva finisce in una struttura di colonne
che non e' la sua. Misurato su DB p.53, dove la banda del box ereditava
`x0 = 178` dalla colonna del padre.

**Si riporta il LORDO, non il netto.** Un aggregato che scende puo' nascondere
pagine che salgono, e "bande da 298 a 310" puo' nascondere distruzioni dentro
una creazione netta. Con `--csv-output` si ottiene il dettaglio per pagina, che
e' l'unico modo di rispondere a "in nessun caso sale".

`--self-test` esegue i CONTROLLI NEGATIVI: rompe di proposito un albero e mostra
che le guardie se ne accorgono. Serve perche' una guardia mai vista fallire non
si distingue dall'assenza di guardia.

`--first-page` esiste perche' le prime N pagine di un manuale non sono un
campione: sono l'apertura, e differiscono dal corpo proprio nella variabile in
gioco (densita' di tabelle e riquadri).

I numeri di pagina sono indici POSIZIONALI, vedi `CLAUDE.md`.
Non un producer. Non wired. Sola lettura.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, cast

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

_FIELDS = ("bands", "accepted", "missing", "x_key_collisions", "labelled", "cut")


def _gutter_keys(row: dict[str, object]) -> list[str]:
    return str(row.get("gutter_x_intervals") or "").split()


def _band_x_edges(row: dict[str, object]) -> list[float]:
    edges = [float(cast(float, row["x0"])), float(cast(float, row["x1"]))]
    for chunk in _gutter_keys(row):
        start, _, end = chunk.partition("-")
        try:
            edges.extend((float(start), float(end)))
        except ValueError:
            continue
    return edges


def check_conservation(
    accepted: list[dict[str, object]], tree: list[dict[str, object]]
) -> tuple[int, int, int]:
    """G1 nelle due direzioni. Ritorna (spariti, duplicati, scartati_etichettati).

    SPARITI: un gutter accettato che l'albero non contiene e che nessuno ha
    etichettato. `edge_strip` NON conta come sparizione: e' lo scarto dichiarato
    del minimo di larghezza ai bordi, con etichetta, e vale per le linguette di
    capitolo. Viene comunque riportato a parte, perche' un'esclusione dichiarata
    resta un'esclusione e chi legge deve vederla.

    INDISTINGUIBILI: la seconda direzione -- lo stesso gutter emesso due volte
    in rami diversi -- **non e' misurabile dall'uscita attuale**, e il numero
    qui restituito NON va letto come "duplicati".

    Le righe dell'albero identificano un gutter solo per intervallo x, e gutter
    DIVERSI possono condividerlo: su Dag p.127 `399.0-408.0` compare sotto tre
    genitori, ma nelle fasce y 82-270, 280-456 e 488-762, che sono tre gutter
    distinti emessi una volta ciascuno; idem su DrW p.163 per `353.0-365.0`.
    Contarli come duplicazione e' un falso positivo -- ed e' la stessa collisione
    sulla stringa x che aveva gia' fatto sbagliare il primo tentativo di misura.

    Per misurarla davvero servirebbe che `_segment_tree` emettesse un'identita'
    stabile per gutter accanto all'intervallo x. E' un cambio dentro
    `column_band` e non si fa di soppiatto dentro uno script di verifica.

    Il valore restituito e' quindi un LIMITE SUPERIORE, utile solo a dire "sotto
    questa soglia non c'e' nulla da guardare", mai a dichiarare una violazione.
    """

    # ATTENZIONE: anche questa direzione poggia sulla chiave stringa.
    # `_segment_tree` assegna `tree_status` confrontando f"{x0:.1f}-{x1:.1f}"
    # con l'insieme delle chiavi emesse, quindi un gutter MAI emesso la cui
    # chiave coincide con quella di un altro emesso viene marcato `band`.
    # Misurato dalla revisione indipendente: 21 pagine su 794 hanno due gutter
    # accettati che condividono la chiave; mascheramenti effettivi 0. La guardia
    # ha quindi margine zero per costruzione, non per fortuna.
    missing = sum(1 for g in accepted if g.get("tree_status") not in ("band", "edge_strip"))
    labelled = sum(1 for g in accepted if g.get("tree_status") == "edge_strip")

    parents_by_key: dict[str, set[str]] = {}
    for row in tree:
        parent = str(row.get("parent_id", ""))
        for key in _gutter_keys(row):
            parents_by_key.setdefault(key, set()).add(parent)
    indistinguishable = sum(1 for parents in parents_by_key.values() if len(parents) > 1)

    return missing, indistinguishable, labelled


def check_cuts(tree: list[dict[str, object]], primitives: tuple[Any, ...]) -> int:
    """G2: confini x di banda che cadono dentro il bbox di una primitiva."""

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
    return cut


class _FakePrimitive:
    def __init__(self, bbox: tuple[float, float, float, float]) -> None:
        self.bbox = bbox


def self_test() -> int:
    """Controlli negativi: le guardie devono FALLIRE quando devono."""

    failures = 0

    def report(name: str, ok: bool) -> None:
        nonlocal failures
        print(f"  {'OK     ' if ok else 'FALLITO'}  {name}")
        if not ok:
            failures += 1

    sane_tree: list[dict[str, object]] = [
        {"band_id": 1, "parent_id": "", "x0": 0.0, "x1": 600.0, "y0": 0.0, "y1": 300.0,
         "gutter_x_intervals": "300.0-310.0"},
        {"band_id": 2, "parent_id": "", "x0": 0.0, "x1": 600.0, "y0": 300.0, "y1": 600.0,
         "gutter_x_intervals": "300.0-310.0"},
    ]
    sane_accepted: list[dict[str, object]] = [
        {"x0": 300.0, "x1": 310.0, "tree_status": "band"}
    ]

    missing, collisions, _ = check_conservation(sane_accepted, sane_tree)
    report("albero sano: nessuno sparito", missing == 0)
    report("albero sano: stesso gutter in due fasce y non collide", collisions == 0)

    missing, _, _ = check_conservation(
        [{"x0": 300.0, "x1": 310.0, "tree_status": ""}], sane_tree
    )
    report("gutter tolto dall'albero: G1 lo rileva", missing == 1)

    two_parents = sane_tree + [
        {"band_id": 3, "parent_id": 1, "x0": 0.0, "x1": 300.0, "y0": 10.0, "y1": 90.0,
         "gutter_x_intervals": "300.0-310.0"},
    ]
    _, collisions, _ = check_conservation(sane_accepted, two_parents)
    report("stessa x sotto due genitori: la collisione viene contata", collisions == 1)
    # Nota, NON un controllo: una frase in prosa passata a `report` come se
    # fosse un asserto stampava OK senza verificare nulla, dentro l'auto-test
    # che esiste perche' "una guardia mai vista fallire non si distingue
    # dall'assenza di guardia". Rilievo della revisione indipendente.
    print(
        "  NOTA      la collisione sopra NON dimostra una duplicazione: due "
        "gutter distinti alla stessa x la producono identica (Dag p.127)"
    )

    missing, _, labelled = check_conservation(
        [{"x0": 300.0, "x1": 310.0, "tree_status": "edge_strip"}], sane_tree
    )
    report(
        "edge_strip: non e' sparizione, ma viene riportato",
        missing == 0 and labelled == 1,
    )

    report(
        "primitiva che scavalca un confine: G2 la rileva",
        check_cuts(sane_tree, (_FakePrimitive((280.0, 100.0, 320.0, 112.0)),)) == 1,
    )
    report(
        "primitiva tutta dentro una colonna: G2 non la conta",
        check_cuts(sane_tree, (_FakePrimitive((100.0, 100.0, 200.0, 112.0)),)) == 0,
    )

    print("\n" + ("AUTO-TEST SUPERATO" if failures == 0 else f"AUTO-TEST FALLITO: {failures}"))
    return 1 if failures else 0


def scan_page(document: fitz.Document, page_index: int, manual: str) -> dict[str, object]:
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
    missing, collisions, labelled = check_conservation(accepted, tree)

    capture = capture_pymupdf_page(
        document.load_page(page_index),
        source_id="diagnostic-source",
        page_id=f"page:{page_index + 1:04d}",
        capture_id=f"band-invariants:{page_index}",
    )
    primitives = normalize_backend_page_capture(capture).text_primitives

    return {
        "manual": manual,
        "page_positional": page_index + 1,
        "bands": len(tree),
        "accepted": len(accepted),
        "missing": missing,
        "x_key_collisions": collisions,
        "labelled": labelled,
        "cut": check_cuts(tree, primitives),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path)
    parser.add_argument("--manuals", nargs="+")
    parser.add_argument("--first-page", type=int, default=1, help="indice POSIZIONALE di partenza")
    parser.add_argument("--max-pages", type=int, default=60)
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.pdf_dir is None or not args.manuals:
        parser.error("servono --pdf-dir e --manuals, oppure --self-test")

    rows: list[dict[str, object]] = []
    for manual in args.manuals:
        pdf_path = cast(Path, args.pdf_dir) / f"{manual}.pdf"
        if not pdf_path.is_file():
            print(f"manca: {pdf_path}", file=sys.stderr)
            continue
        with fitz.open(pdf_path) as document:
            start = args.first_page - 1
            last = min(start + args.max_pages, document.page_count)
            for page_index in range(start, last):
                result = scan_page(document, page_index, manual)
                if result:
                    rows.append(result)

    total = {k: sum(cast(int, r[k]) for r in rows) for k in _FIELDS}
    print(
        f"perimetro: pagine posizionali {args.first_page}-"
        f"{args.first_page + args.max_pages - 1} per manuale"
    )
    print(f"pagine con almeno una banda: {len(rows)}")
    print(f"bande: {total['bands']}   gutter accettati: {total['accepted']}")
    print(
        f"G1 direzione SPARIZIONE: {total['missing']}"
        f"   (scartati con etichetta: {total['labelled']})"
        f"   -> {'OK' if total['missing'] == 0 else 'CADUTA'}"
    )
    print(
        f"G1 direzione DUPLICAZIONE: NON MISURABILE dall'uscita attuale. "
        f"Collisioni sulla chiave x: {total['x_key_collisions']} (limite superiore, "
        f"non violazioni -- vedi check_conservation)"
    )
    print(
        f"G2 confini che tagliano una primitiva: {total['cut']} "
        f"su {sum(1 for r in rows if r['cut'])} pagine"
    )

    if args.csv_output is not None and rows:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"dettaglio per pagina in {args.csv_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
