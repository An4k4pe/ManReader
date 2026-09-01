"""ManReader IR 2 — converte un PDF percorrendo la pipeline nuova, per intero.

    ./venv/bin/python main_ir2.py Dag.pdf --out output/Dag

**Perche' esiste.** `main.py` e' la pipeline legacy da capo a fondo: non contiene
una riga su `ir2_*`, `pymupdf_capture` o `primitive_normalizer`. Fuori dai test,
gli unici a importare `ir2_builder` e `ir2_markdown` erano **script**. La pipeline
nuova aveva un prototipo per pagina e nessun punto d'ingresso di documento, ed e'
per questo che ogni misura di questa sessione ha dovuto cucire insieme due script:
la cosa da chiamare non c'era. `AGENTS.MD` §Migrazione lo registra come un buco
aperto — «la milestone di uscita non esiste».

**Non cambia niente di autorevole.** Il legacy resta la baseline e non viene
toccato: questo e' un secondo percorso che produce la sua uscita, che e' la
definizione di shadow mode. Nessun default si sposta.

**Il PDF si legge una volta.** La fetta verticale, nata per pagina, riapre il
documento e **ricattura venti pagine** per ognuna che rende, perche' i fatti
d'arredo e tipografia si misurano su una finestra. Qui la cattura si fa una volta
e la finestra e' una fetta di quella: e' cio' che la docstring di `document_scan`
dichiarava da sempre senza avere un chiamante che lo sfruttasse.

**Ma i fatti restano a finestra, non a documento.** E' la parte che sembra
un'ottimizzazione mancata e non lo e': `Criterio_AmbitoDeiFatti_v2.md` ha misurato
che `prose_sizes` **non e' invariante di scala** -- allargando al documento
intero le dimensioni di prosa di FWK passano da 6 a 14 e quelle di Dag da 4 a 23.
La finestra si **sposta**, non si allarga. Calcolare i sei fatti una volta sola
per tutto il libro sarebbe piu' veloce e riaprirebbe il difetto che quel criterio
ha chiuso.

**Gli asset.** La ricorrenza del contenuto e' invece un fatto **di documento** --
lo sfondo sta su duecento pagine, l'illustrazione su una -- e si misura su tutte
le pagine. Da li' `document_asset_policy` decide la destinazione,
`pymupdf_asset_extraction` tira fuori i byte componendo la maschera di
trasparenza, e `document_asset_catalogue` registra **tutto**, anche cio' che non
diventa un file: `AGENTS.MD` §Coverage, nessuna esclusione silenziosa.

Uscita::

    <out>/document.md          il corpo, pagina dopo pagina
    <out>/document_ir2.json    l'IR 2 serializzata
    <out>/images/              un file per illustrazione, con la sua trasparenza
    <out>/assets/              un file per elemento ripetuto
    <out>/asset_index.csv      ogni contenuto raster, anche senza file
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path

import fitz
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Il cuore per pagina vive ancora nella fetta verticale, e questa e' l'unica
# implementazione: duplicarlo qui creerebbe i «due rami che non si toccavano»
# che questo progetto ha gia' pagato una volta, divergenti su 9 pagine su 20.
# Promuoverlo a modulo di produzione e' il passo dopo, ed e' un riordino puro:
# va fatto da solo, non dentro un cambio funzionale (`AGENTS.MD` §Regole, 6).
from prototype_ir2_page import (  # noqa: E402
    BuiltPage,
    CapturedDocument,
    OpenedSource,
    capture_document,
    run,
)

from document_asset_catalogue import (  # noqa: E402
    UncataloguedOccurrence,
    build_asset_catalogue,
)
from document_asset_policy import decide_document_assets  # noqa: E402
from document_asset_recurrence_measurements import (  # noqa: E402
    measure_document_asset_recurrence,
)
from document_heading_measurements import measure_font_sizes  # noqa: E402
from document_heading_policy import prose_sizes  # noqa: E402
from ir2_markdown import render_page_markdown  # noqa: E402
from ir2_model import DocumentIR2, IR2Provenance  # noqa: E402
from ir2_serialization import document_ir2_from_dict, document_ir2_to_dict  # noqa: E402
from job_source_snapshot import inspect_source_file  # noqa: E402
from pymupdf_asset_extraction import extract_occurrence_raster  # noqa: E402


# **Lo stato dei processi figli, ereditato per `fork` e mai serializzato.**
#
# Le pagine sono indipendenti -- la finestra dei fatti e' in sola lettura -- ma
# `fitz.Document` non e' serializzabile e la cattura del documento e' grossa.
# Su Linux `fork` fa ereditare la memoria del padre in copy-on-write: la cattura
# si fa **una volta sola nel padre** e i figli la vedono senza che nessuno la
# impacchetti. Ogni figlio apre soltanto i propri handle di backend, che sono
# l'unica cosa che non si puo' condividere.
@dataclass
class _Lavoro:
    """Cio' che ogni processo deve sapere per rendere una pagina."""

    pdf: Path
    scratch: Path
    captured: CapturedDocument
    tabelle: bool
    finestra: int
    opened: OpenedSource | None = None


_LAVORO: _Lavoro | None = None


def _prepara_figlio() -> None:
    """Ogni processo apre i suoi handle. Il resto lo ha ereditato."""

    assert _LAVORO is not None
    _LAVORO.opened = OpenedSource(
        document=fitz.open(_LAVORO.pdf),
        plumber=pdfplumber.open(_LAVORO.pdf),
    )


def _rendi_pagina(page_index: int) -> tuple[int, object, str | None]:
    """Una pagina, dentro un processo figlio. Torna il `BuiltPage` o l'errore."""

    assert _LAVORO is not None
    try:
        return page_index, run(
            _LAVORO.pdf,
            page_index + 1,
            _LAVORO.scratch / f"{page_index:05d}",
            None,
            remove_furniture=True,
            render_lists=True,
            enable_tables=_LAVORO.tabelle,
            furniture_sample=_LAVORO.finestra,
            opened=_LAVORO.opened,
            captured_document=_LAVORO.captured,
        ), None
    except Exception as errore:  # noqa: BLE001
        # Una pagina che cade non deve fermare il documento: si registra e si
        # prosegue. Tre crash di questo giro venivano da pagine singole, e
        # perdere l'intero manuale per una di esse costa piu' di quanto protegga.
        return page_index, None, f"{type(errore).__name__}: {errore}"


_STATO = "stato.json"


def _impronta_del_codice() -> str:
    """Un'impronta dei moduli del progetto **davvero caricati**.

    **Perche' serve.** Lo stato registrava sorgente e opzioni, non il codice:
    correggendo un producer e rilanciando sulla stessa cartella, la ripresa
    riusava le pagine calcolate dal codice vecchio e la correzione non si vedeva.
    E' la stessa trappola che rende pericolosa la cache di `PageAnalysis`, dove
    `producer_version` e' una stringa scritta a mano che nessuno ricorda di
    cambiare.

    **Perche' dai moduli caricati e non da un elenco.** Un elenco dichiarato si
    dimentica di aggiornarlo quando nasce un modulo nuovo, e allora l'impronta
    mente proprio nel caso in cui servirebbe. `sys.modules` dice cosa e' stato
    caricato davvero, e non puo' andare fuori sincrono.

    **Sbaglia per eccesso, di proposito.** Un commento cambiato in un modulo
    qualunque invalida la ripresa e costa un ricalcolo. L'errore opposto --
    riprendere su codice diverso -- costa un'uscita mista che nessuno vede.
    """

    percorsi: list[Path] = []
    for modulo in list(sys.modules.values()):
        percorso = getattr(modulo, "__file__", None)
        if not percorso:
            continue
        risolto = Path(percorso).resolve()
        # `venv` e' un symlink fuori dalla radice: `resolve()` lo porta fuori da
        # solo, e il controllo esplicito regge anche dove non lo e'.
        if not risolto.is_relative_to(PROJECT_ROOT) or "venv" in risolto.parts:
            continue
        percorsi.append(risolto)

    digest = hashlib.sha256()
    for risolto in sorted(set(percorsi)):
        digest.update(risolto.name.encode("utf-8"))
        try:
            digest.update(risolto.read_bytes())
        except OSError:
            digest.update(b"<illeggibile>")
    return digest.hexdigest()


def _stato_atteso(
    pdf: Path, finestra: int, tabelle: bool
) -> dict[str, dict[str, object]]:
    """La sorgente **verificata** e le opzioni che cambiano l'uscita.

    `inspect_source_file` costruisce la referenza (sha256 e dimensione) **senza
    copiare il PDF**: `AGENTS.MD` §Sorgente vuole la sorgente «immutabile o
    verificata prima del resume», e verificarla basta -- duplicare duecento
    megabyte per manuale sarebbe il prezzo di una garanzia che gia' abbiamo.

    Le opzioni entrano nello stato perche' cambiano cio' che si e' prodotto:
    riprendere con una finestra diversa unirebbe pagine misurate su ambiti
    diversi, e sarebbe una fusione silenziosa.
    """

    riferimento = inspect_source_file(pdf)
    return {
        "sorgente": {
            "sha256": riferimento.sha256,
            "size_bytes": riferimento.size_bytes,
            "original_name": riferimento.original_name,
        },
        "opzioni": {"finestra": finestra, "tabelle": tabelle},
        "codice": {"sha256": _impronta_del_codice()},
    }


def _pagina_su_disco(scratch: Path, page_index: int) -> BuiltPage | None:
    """La pagina gia' resa in una corsa precedente, o None se non c'e'.

    **La ripresa non ha bisogno del deserializzatore della cattura**: cio' che
    serve e' gia' su disco e gia' rileggibile -- l'IR 2 della pagina e gli id
    esclusi dall'arredo. Quello che si evita e' il lavoro dei producer, che e'
    la parte cara.
    """

    directory = scratch / f"{page_index:05d}"
    serializzata = directory / "document_ir2.json"
    if not serializzata.is_file():
        return None
    try:
        pagina = document_ir2_from_dict(
            json.loads(serializzata.read_text(encoding="utf-8"))
        ).pages[0]
        esclusi = directory / "excluded_ir2.json"
        excluded = (
            frozenset(json.loads(esclusi.read_text(encoding="utf-8")))
            if esclusi.is_file()
            else frozenset()
        )
    except (OSError, ValueError, KeyError, IndexError):
        # Un artefatto illeggibile si rifa': meglio ricalcolare che fidarsi.
        return None
    return BuiltPage(
        page_id=pagina.page_id,
        page_index=page_index,
        ir2_page=pagina,
        excluded_node_ids=excluded,
        asset_digests=tuple(
            n.asset.digest for n in pagina.nodes if n.asset is not None
        ),
        markdown="",
        producer_names=(),
    )


def _asset_da_disco(
    indice: Path, out: Path
) -> tuple[list[dict[str, object]], frozenset[str]] | tuple[None, None]:
    """L'indice asset di una corsa precedente, se e' completo e i file ci sono.

    **Un indice che nomina un file assente non si riusa.** Riprendere con
    mezza cartella di immagini darebbe note che puntano nel vuoto, ed e' peggio
    che rifare l'estrazione -- che e' la parte lenta, ma non la parte fragile.
    """

    if not indice.is_file():
        return None, None
    try:
        with indice.open(encoding="utf-8") as handle:
            righe = list(csv.DictReader(handle))
    except (OSError, ValueError):
        return None, None
    if not righe:
        return None, None
    for riga in righe:
        nome, cartella = riga.get("nome_file"), riga.get("cartella")
        if nome and cartella and not (out / cartella / nome).is_file():
            return None, None
    note = frozenset(
        r["digest"] for r in righe if r.get("digest") and r.get("nota_nel_corpo") == "si"
    )
    return [dict(r) for r in righe], note


_INDEX_FIELDS = [
    "digest", "destinazione", "cartella", "nome_file", "pagine", "occorrenze",
    "prima_pagina", "estensione_minore_pt", "nota_nel_corpo",
    "risorsa_memorizzata", "metodo",
]


def _tri_state(value: bool | None) -> str:
    """`si`/`no`/vuoto. Il vuoto e' «il backend non lo dichiara», non «no»."""

    return "" if value is None else ("si" if value else "no")


def document_text_scale(captured: CapturedDocument) -> float | None:
    """La lettera piu' piccola che il documento stampa, o None se non si misura.

    **Limite dichiarato**: qui la popolazione e' il documento intero, e
    `prose_sizes` non e' invariante di scala -- su Dag il minimo scende a 2,8 pt
    e il ramo della scala tipografica diventa quasi inerte, mentre su Fab a 9,8
    pt funziona. Non lo correggo di nascosto: cambiare la popolazione di questa
    statistica e' una decisione di misura e vuole il suo criterio. Nel frattempo
    il ramo che conta per i filetti e' un altro -- «nessuna risorsa memorizzata»,
    che li prende prima e non dipende dalla scala.
    """

    pages = [captured.pages[i] for i in sorted(captured.pages)]
    sizes = prose_sizes(measure_font_sizes(pages)) if pages else frozenset()
    return min(sizes) if sizes else None


def build_assets(
    document: fitz.Document,
    captured: CapturedDocument,
    out: Path,
) -> tuple[list[dict[str, object]], frozenset[str]]:
    """Estrae e cataloga gli asset del documento; ritorna righe e digest con nota."""

    pages = [captured.pages[i] for i in sorted(captured.pages)]
    measurements = measure_document_asset_recurrence(pages)
    decisions = decide_document_assets(
        measurements, text_scale=document_text_scale(captured)
    )

    first: dict[str, tuple[int, object]] = {}
    for index in sorted(captured.pages):
        for primitive in captured.pages[index].image_primitives:
            digest = primitive.content_digest
            if digest is not None and digest not in first:
                first[digest] = (index, primitive)

    info_cache: dict[int, list[dict[str, object]]] = {}

    def raw_info(page_index: int) -> list[dict[str, object]]:
        """Una lettura per pagina, non una per file."""

        if page_index not in info_cache:
            info_cache[page_index] = document[page_index].get_image_info(
                hashes=True, xrefs=True
            )
        return info_cache[page_index]

    def extract(digest: str):
        page_index, primitive = first[digest]
        return extract_occurrence_raster(
            document, document[page_index], primitive,  # type: ignore[arg-type]
            raw_image_info=raw_info(page_index),
        )

    def store(folder: str, name: str, payload: bytes) -> None:
        target = out / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(payload)

    catalogue = build_asset_catalogue(
        decisions=decisions,
        first_page_index_of={d: page for d, (page, _) in first.items()},
        extract=extract,
        store=store,
        uncatalogued=tuple(
            UncataloguedOccurrence(
                page_index=o.page_index,
                primitive_id=o.primitive_id,
                reason="nessun content_digest dal backend",
            )
            for o in measurements.digestless
        ),
    )

    rows: list[dict[str, object]] = [
        {
            "digest": e.digest,
            "destinazione": e.destination,
            "cartella": e.folder or "",
            "nome_file": e.file_name or "",
            "pagine": e.page_count,
            "occorrenze": e.occurrence_count,
            "prima_pagina": e.first_page_index,
            "estensione_minore_pt": f"{e.smallest_placed_extent:.1f}",
            "nota_nel_corpo": "si" if e.renders_body_note else "no",
            "risorsa_memorizzata": _tri_state(e.has_stored_resource),
            "metodo": e.extraction_method or "",
        }
        for e in catalogue.entries
    ]
    rows.extend(
        {
            "digest": "", "destinazione": "senza digest", "cartella": "",
            "nome_file": "", "pagine": 1, "occorrenze": 1,
            "prima_pagina": o.page_index, "estensione_minore_pt": "",
            "nota_nel_corpo": "no", "risorsa_memorizzata": "",
            "metodo": o.primitive_id,
        }
        for o in catalogue.uncatalogued
    )
    return rows, catalogue.digests_with_body_note()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--pages", type=str, default=None,
        help="intervallo di indici 0-based, es. 100-120. Default: tutto.",
    )
    parser.add_argument(
        "--finestra", type=int, default=20,
        help="pagine su cui misurare i fatti d'arredo e tipografia (default 20).",
    )
    parser.add_argument("--tabelle", action="store_true")
    parser.add_argument(
        "--rifai", action="store_true",
        help="ignora quanto gia' prodotto e ricomincia da capo.",
    )
    parser.add_argument(
        "--processi", type=int, default=0,
        help="quanti processi (0 = uno per core). Le pagine sono indipendenti.",
    )
    arguments = parser.parse_args()

    arguments.out.mkdir(parents=True, exist_ok=True)
    scratch = arguments.out / ".pagine"
    percorso_stato = arguments.out / _STATO

    # --- Lo stato: si riprende solo da una corsa sulla STESSA sorgente ---
    atteso = _stato_atteso(arguments.pdf, arguments.finestra, arguments.tabelle)
    riprendi = False
    produttori_salvati: tuple[str, ...] = ()
    if percorso_stato.is_file() and not arguments.rifai:
        try:
            trovato = json.loads(percorso_stato.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            trovato = None
        if isinstance(trovato, dict) and all(
            trovato.get(chiave) == atteso[chiave]
            for chiave in ("sorgente", "opzioni", "codice")
        ):
            riprendi = True
            # **I produttori vengono dallo stato, non dalle pagine riprese.** Una
            # pagina riletta da disco non li porta -- l'IR 2 serializzata non li
            # registra per pagina -- e senza questo una ripresa TOTALE scriveva
            # `producer_names: []` nella provenienza del documento. Difetto
            # trovato confrontando una ripresa parziale con una totale.
            produttori_salvati = tuple(trovato.get("produttori") or ())
        elif trovato is not None:
            # **Non si riprende in silenzio su una sorgente diversa.** Mescolare
            # pagine di due documenti, o di due ampiezze di finestra, produrrebbe
            # un'uscita che non corrisponde a nessuno dei due.
            if trovato.get("sorgente") != atteso["sorgente"]:
                quale = "la sorgente e' cambiata"
            elif trovato.get("opzioni") != atteso["opzioni"]:
                quale = "le opzioni sono cambiate"
            else:
                quale = "il codice e' cambiato"
            print(
                f"stato incompatibile: {quale}. Usa --rifai per ricominciare.",
                file=sys.stderr,
            )
            return 2

    with fitz.open(arguments.pdf) as document, pdfplumber.open(arguments.pdf) as plumber:
        print(f"cattura di {len(document)} pagine...", flush=True)
        captured = capture_document(document)
        skipped = len(document) - len(captured.pages)
        print(f"  {len(captured.pages)} catturate, {skipped} fuori dalla guardia")

        indice = arguments.out / "asset_index.csv"
        rows, notes = _asset_da_disco(indice, arguments.out) if riprendi else (None, None)
        if rows is None:
            print("asset del documento...", flush=True)
            rows, notes = build_assets(document, captured, arguments.out)
            with indice.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=_INDEX_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        else:
            print(f"asset ripresi dall'indice: {len(rows)} contenuti", flush=True)

        wanted = sorted(captured.pages)
        if arguments.pages:
            first_text, _, last_text = arguments.pages.partition("-")
            low = int(first_text)
            high = int(last_text) if last_text else low
            wanted = [i for i in wanted if low <= i <= high]

        global _LAVORO
        _LAVORO = _Lavoro(
            pdf=arguments.pdf,
            scratch=scratch,
            captured=captured,
            tabelle=arguments.tabelle,
            finestra=arguments.finestra,
        )
        # --- Cio' che una corsa precedente ha gia' prodotto ---
        gia_fatte: dict[int, BuiltPage] = {}
        if riprendi:
            for page_index in wanted:
                pagina = _pagina_su_disco(scratch, page_index)
                if pagina is not None:
                    gia_fatte[page_index] = pagina
            if gia_fatte:
                print(f"riprendo: {len(gia_fatte)} pagine gia' su disco", flush=True)
        da_fare = [i for i in wanted if i not in gia_fatte]

        processi = arguments.processi or (os.cpu_count() or 1)
        processi = max(1, min(processi, max(1, len(da_fare))))
        print(
            f"rendo {len(da_fare)} pagine su {processi} "
            f"process{'o' if processi == 1 else 'i'}...",
            flush=True,
        )

        risultati: list[tuple[int, object, str | None]] = []
        if processi == 1:
            # Un processo solo resta la via **identica** a prima, e serve a due
            # cose: eseguire dove `fork` non c'e', e avere una traccia pulita
            # quando una pagina cade.
            _LAVORO.opened = OpenedSource(document=document, plumber=plumber)
            for page_index in da_fare:
                risultati.append(_rendi_pagina(page_index))
        else:
            # `fork` e non `spawn`: i figli ereditano `captured` senza che venga
            # impacchettata. Con `spawn` andrebbe serializzata a ogni processo,
            # ed e' la cosa piu' grossa che abbiamo in mano.
            with ProcessPoolExecutor(
                max_workers=processi,
                mp_context=get_context("fork"),
                initializer=_prepara_figlio,
            ) as pool:
                for esito in pool.map(_rendi_pagina, da_fare, chunksize=1):
                    risultati.append(esito)

        rese: dict[int, BuiltPage] = dict(gia_fatte)
        caduti: list[tuple[int, str]] = []
        for page_index, page, errore in risultati:
            if errore is not None:
                caduti.append((page_index, errore))
            elif page is not None:
                rese[page_index] = page  # type: ignore[assignment]
        # **L'ordine e' quello delle pagine, non quello in cui sono finite.**
        built = [rese[i] for i in wanted if i in rese]
        if caduti:
            print(f"\n  {len(caduti)} pagine non rese:", file=sys.stderr)
            for page_index, errore in caduti[:10]:
                print(f"    idx {page_index}: {errore}", file=sys.stderr)

    if not built:
        print("nessuna pagina prodotta", file=sys.stderr)
        return 2

    ir2 = DocumentIR2(
        provenance=IR2Provenance(
            source_id=arguments.pdf.stem,
            generation_id=f"generation:ir2:{arguments.pdf.stem}",
            producer_names=tuple(
                sorted({name for p in built for name in p.producer_names})
                or produttori_salvati
            ),
        ),
        pages=tuple(p.ir2_page for p in built),
    )
    (arguments.out / "document_ir2.json").write_text(
        json.dumps(document_ir2_to_dict(ir2), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # La resa si rifa' **qui**, con la politica d'asset in mano: la fetta la
    # produce senza, perche' per pagina la ricorrenza di documento non si sa.
    parts: list[str] = []
    for page in built:
        body = render_page_markdown(
            page.ir2_page,
            excluded_node_ids=page.excluded_node_ids,
            asset_digests_with_note=notes,
        )
        if body.strip():
            parts.append(f"<!-- {page.page_id} -->\n\n{body.rstrip()}")
    (arguments.out / "document.md").write_text(
        "\n\n".join(parts) + "\n", encoding="utf-8"
    )

    # **Lo stato si scrive alla fine, e solo se nessuna pagina e' caduta.**
    # Segnare come ripartibile una corsa incompleta farebbe saltare al giro dopo
    # proprio le pagine che mancano.
    if not caduti:
        percorso_stato.write_text(
            json.dumps(
                {**atteso, "produttori": list(ir2.provenance.producer_names)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    rendered_notes = sum(
        1 for part in parts for line in part.splitlines() if line.startswith("> **[")
    )
    print(f"\npagine rese           {len(built)} su {len(wanted)}")
    print(f"note d'asset nel corpo {rendered_notes}")
    print(f"contenuti catalogati   {len(rows)}")
    print(f"uscita                 {arguments.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
