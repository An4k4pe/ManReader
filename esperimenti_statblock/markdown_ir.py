"""La resa Markdown consumando TUTTI i producer wired. Criterio in
CRITERIO_RESA_COMPLETA.md.

Il giro precedente (`markdown_schede.py`) ne consumava uno su sei e si vedeva:
il testo usciva schiacciato perche' l'ordine di lettura non era stabilito, e le
celle di tabella si infilavano nella prosa.

Qui:
  `column_band`             l'ordine di colonna
  `table_candidate`         le tabelle, delimitate
  `embedded_visual`         il riquadro che DELIMITA la scheda
  `interior_visual_frame`   idem, piu' stretto
  `page_covering_visual`    lo sfondo di pagina -> nota
  `page_edge_visual`        le fasce di bordo -> nota

Il rilevatore (`pila2.py`) dice DOVE ci sono campi; il riquadro disegnato dice
DOVE FINISCE la scheda. Misurato prima: su 4 pagine su 4 del Dragonbane esiste
un riquadro che contiene il blocco dei campi col nome.

Il Markdown lo produce `markdown_builder.build_markdown` del repo, invariato,
da un `DocumentIR`. Nessuna modifica a producer, soglie o renderer.

Uso:  python3 markdown_ir.py <file.pdf> --out <dir> [--da N] [--a N]
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from collections import Counter
from pathlib import Path

_QUI = Path(__file__).resolve()
for _cand in _QUI.parents:
    if (_cand / "primitive_model.py").is_file():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break

import colonne  # noqa: E402
import pdfplumber  # noqa: E402
import pila2  # noqa: E402
import pymupdf  # noqa: E402
from copertura import PAGINE_RICORRENZA, corse_residue, raggruppa_rare  # noqa: E402
from markdown_schede import _marcatore_iniziale, _stile, marcatori_di  # noqa: E402

from ir_model import AssetIR, BlockIR, DocumentIR, PageIR  # noqa: E402
from markdown_builder import build_markdown  # noqa: E402
from page_analysis_column_band import (  # noqa: E402
    build_column_band_page_analysis_with_measurements,
)
from page_analysis_embedded_visual import build_embedded_visual_page_analysis  # noqa: E402
from page_analysis_interior_visual_frame import (  # noqa: E402
    build_interior_visual_frame_page_analysis,
)
from page_analysis_page_covering_visual import (  # noqa: E402
    build_page_covering_visual_page_analysis,
)
from page_analysis_page_edge_visual import build_page_edge_visual_page_analysis  # noqa: E402
from page_analysis_table_candidate import build_table_candidate_page_analysis  # noqa: E402
from page_analysis_table_candidate_binding import BoundTableCandidatePage  # noqa: E402
from primitive_normalizer import normalize_backend_page_capture  # noqa: E402
from pymupdf_capture import capture_pymupdf_page  # noqa: E402

NOTA = {"nota": "1"}


def _dentro(bbox, riga) -> bool:
    """La riga appartiene al riquadro se il suo CENTRO ci cade: stessa regola di
    appartenenza dei producer (`page_analysis_column_band.py`)."""
    x0, y0, x1, y1 = bbox
    return (
        x0 <= (riga["x0"] + riga["x1"]) / 2 < x1 and y0 <= (riga["y0"] + riga["y1"]) / 2 < y1
    )


def candidati_di_pagina(documento, plumber, pi: int):
    """I candidati dei sei producer per una pagina, piu' il conto delle
    primitive che restano fuori dalle bande."""
    pagina = documento.load_page(pi)
    cattura = capture_pymupdf_page(
        pagina,
        source_id="esperimenti-statblock",
        page_id=f"page:{pi + 1:04d}",
        capture_id=f"resa:{pi}",
    )
    primitive_page = normalize_backend_page_capture(cattura)
    gid = f"resa:{pi}"

    bande, misure = build_column_band_page_analysis_with_measurements(
        primitive_page, generation_id=gid
    )
    albero = colonne._tree_rows_from_contract(bande.candidates, misure)
    _ordinate, in_banda = colonne._tree_aware_order(list(primitive_page.text_primitives), albero)

    legato = BoundTableCandidatePage(primitive_page=primitive_page, plumber_page=plumber.pages[pi])
    return {
        "primitive_page": primitive_page,
        "in_banda": in_banda,
        "primitive": len(primitive_page.text_primitives),
        "tabelle": build_table_candidate_page_analysis(legato, generation_id=gid).candidates,
        "embedded": build_embedded_visual_page_analysis(
            primitive_page, generation_id=gid
        ).candidates,
        "riquadri": build_interior_visual_frame_page_analysis(
            primitive_page, generation_id=gid
        ).candidates,
        "sfondi": build_page_covering_visual_page_analysis(
            primitive_page, generation_id=gid
        ).candidates,
        "bordi": build_page_edge_visual_page_analysis(
            primitive_page, generation_id=gid
        ).candidates,
    }


def righe_a_campi(righe, min_coppie: int = 2) -> set[int]:
    """Le righe che portano almeno DUE coppie etichetta/valore.

    E' la definizione di `State.md:903` — «campi etichetta:valore da preservare»
    — presa alla lettera e senza soglie: una riga con due campi e' una riga di
    scheda, una con uno solo puo' essere prosa che comincia in grassetto. Non
    passa dalla frequenza: la frequenza serve a dare un NOME al template, non a
    riconoscere che una riga ha dei campi.

    `min_coppie` e' il passo 2 dell'ordine del 10 settembre 2026
    (CRITERIO_UNA_COPPIA.md): gli ambienti di Daggerheart hanno una coppia per
    riga. Il default riproduce i giri precedenti."""
    return {i for i, r in enumerate(righe) if len(pila2.etichette(r)) >= min_coppie}


def regioni_di_pagina(righe, record_righe, firma_di, candidati, min_coppie: int = 2) -> list[dict]:
    """Le regioni della pagina: le schede dal riquadro, poi le tabelle.

    Un riquadro e' una scheda se contiene almeno DUE righe a campi: due, perche'
    una riga sola non e' un record. Il rilevatore non decide il confine — lo
    decide il riquadro disegnato — ma da' il nome del template quando le righe
    dentro appartengono a un suo record. Fra riquadri annidati vince il piu'
    esterno: la scheda e' l'oggetto intero, non il suo blocco dei campi."""
    campi = righe_a_campi(righe, min_coppie)
    proposte: list[dict] = []
    for candidato in list(candidati["embedded"]) + list(candidati["riquadri"]):
        indici = [i for i, r in enumerate(righe) if _dentro(candidato.bbox, r)]
        if len(set(indici) & campi) < 2:
            continue
        gruppi = [record_righe[i] for i in indici if i in record_righe]
        nome = f"scheda — {', '.join(firma_di.get(gruppi[0], [])[:6])}" if gruppi else "scheda"
        proposte.append(
            {
                "ini": indici[0],
                "fine": indici[-1],
                "righe": set(indici),
                "tipo": "scheda",
                "nota": nome,
            }
        )
    for candidato in candidati["tabelle"]:
        indici = [i for i, r in enumerate(righe) if _dentro(candidato.bbox, r)]
        if len(indici) < 2:
            continue
        proposte.append(
            {
                "ini": indici[0],
                "fine": indici[-1],
                "righe": set(indici),
                "tipo": "tabella",
                "nota": f"tabella (candidata, {len(indici)} righe)",
            }
        )
    # Vince la regione piu' ampia, e ogni riga sta in al massimo una.
    proposte.sort(key=lambda r: (-len(r["righe"]), r["ini"]))
    coperte: set[int] = set()
    tenute: list[dict] = []
    for proposta in proposte:
        if proposta["righe"] & coperte:
            continue
        coperte |= proposta["righe"]
        tenute.append(proposta)
    tenute.sort(key=lambda r: r["ini"])
    return tenute


def _aggancio_di(righe):
    """Dove si aggancia una nota: la prima riga, nell'ordine di lettura, che sta
    all'altezza dell'elemento o piu' sotto. Scelta di posizionamento dichiarata,
    non una deduzione di appartenenza."""

    def aggancio(bbox) -> int:
        for indice, riga in enumerate(righe):
            if (riga["y0"] + riga["y1"]) / 2 >= bbox[1]:
                return indice
        return len(righe)

    return aggancio


def _nota_blocco(testo: str, pi: int, ordine: int, tipo: str) -> BlockIR:
    return BlockIR(
        id=f"n-{pi:04d}-{ordine:04d}",
        type="text",
        page_num=pi + 1,
        order=ordine,
        text=testo,
        role="callout",
        metadata={"callout_type": tipo, **NOTA},
    )


def _nota_asset(candidato, pi: int, ordine: int, kind: str, descrizione: str,
                percorso: str | None) -> BlockIR:
    return BlockIR(
        id=f"a-{pi:04d}-{ordine:04d}",
        type="image" if kind == "image" else "vector",
        page_num=pi + 1,
        order=ordine,
        bbox=tuple(candidato.bbox) if candidato is not None else None,
        asset=AssetIR(
            id=f"asset-{pi:04d}-{ordine:04d}",
            sha="",
            kind=kind,
            path=percorso or "#",
            title=descrizione,
            description=(
                "Estratto in cartella e referenziato."
                if percorso
                else "Elemento grafico non estratto: nota al posto dell'asset."
            ),
        ),
        metadata=dict(NOTA),
    )


def _estrai_raster(documento, pi: int, primitive_page, cartella: Path,
                   gia_viste: dict[str, str]) -> list[tuple[object, str, str]]:
    """Le raster della pagina: (primitiva, descrizione, percorso relativo).

    Le occorrenze con lo stesso `content_digest` condividono un file: e' la
    sostituzione degli **elementi ripetuti** dell'obiettivo, non una
    ottimizzazione. Quando l'xref non e' risolvibile il file non si scrive e la
    nota lo dichiara, invece di spacciare una fotografia della pagina per
    l'asset incorporato."""
    pagina = documento.load_page(pi)
    info = pagina.get_image_info(hashes=True, xrefs=True)
    fuori = []
    # Un elemento RIPETUTO prende UNA nota che dice quante volte ricorre, non
    # una nota per occorrenza: e' l'obiettivo alla lettera («elementi ripetuti
    # sostituiti da note brevi»), e senza questo su Dragonbane uscivano 65 note
    # per pagina.
    occorrenze: dict[str, int] = {}
    for primitiva in primitive_page.image_primitives:
        chiave = primitiva.content_digest or primitiva.primitive_id
        occorrenze[chiave] = occorrenze.get(chiave, 0) + 1
    emesse: set[str] = set()
    for primitiva in primitive_page.image_primitives:
        chiave = primitiva.content_digest or primitiva.primitive_id
        if chiave in emesse:
            continue
        emesse.add(chiave)
        larghezza = primitiva.bbox[2] - primitiva.bbox[0]
        altezza = primitiva.bbox[3] - primitiva.bbox[1]
        ripetizioni = occorrenze[chiave]
        descrizione = f"immagine {larghezza:.0f}x{altezza:.0f}pt a pagina {pi + 1}"
        if ripetizioni > 1:
            descrizione += f", ripetuta {ripetizioni} volte in pagina"
        if chiave in gia_viste:
            fuori.append((primitiva, descrizione + ", gia' vista", gia_viste[chiave]))
            continue
        percorso = ""
        try:
            indice = int(primitiva.source_observation_id.split(":i")[1])
            xref = info[indice].get("xref")
            if xref:
                dati = documento.extract_image(xref)
                nome = f"asset/p{pi + 1:04d}_{chiave[:12]}.{dati['ext']}"
                (cartella / nome).parent.mkdir(parents=True, exist_ok=True)
                (cartella / nome).write_bytes(dati["image"])
                percorso = nome
                gia_viste[chiave] = nome
        except (IndexError, ValueError, KeyError, RuntimeError):
            percorso = ""
        fuori.append((primitiva, descrizione, percorso))
    return fuori


def costruisci(path: str, cartella: Path, da: int, a: int):
    pagine, schema, info, record = pila2.record_di(path)
    firma_di = {gi: firma for gi, _n, _prof, _strati, firma in info}
    marcatori = marcatori_di(schema)

    record_righe: list[dict[int, int]] = [dict() for _ in pagine]
    for pi, ini, fine, gi in record:
        for i in range(ini, fine + 1):
            record_righe[pi].setdefault(i, gi)

    # Il residuo ricorrente resta la regola di non-perdita del giro precedente.
    residuo: dict[int, list[tuple[int, int, str]]] = {}
    for gruppo in raggruppa_rare(corse_residue(pagine, schema, pila2.etichette)):
        if len({c[0] for c in gruppo["corse"]}) < PAGINE_RICORRENZA:
            continue
        etichette = ", ".join(sorted(gruppo["firma"])[:6])
        for pi, x, y, _f in gruppo["corse"]:
            residuo.setdefault(pi, []).append((x, y, etichette))

    documento_ir = DocumentIR(schema_version="1.0", source_path=path)
    statistiche = Counter()
    contenuto: Counter[str] = Counter()
    gia_viste: dict[str, str] = {}
    celle_uguali = celle_totali = 0

    with pymupdf.open(path) as doc, pdfplumber.open(path) as plumber:
        for pi in range(da, min(a + 1, len(pagine))):
            righe = pagine[pi]
            candidati = candidati_di_pagina(doc, plumber, pi)
            regioni = regioni_di_pagina(righe, record_righe[pi], firma_di, candidati)
            coperte = {i for r in regioni for i in r["righe"]}
            for x, y, etichette in residuo.get(pi, []):
                if not set(range(x, y + 1)) & coperte:
                    regioni.append(
                        {
                            "ini": x,
                            "fine": y,
                            "righe": set(range(x, y + 1)),
                            "tipo": "ignota",
                            "nota": f"struttura non riconosciuta — {etichette}",
                        }
                    )
            regioni.sort(key=lambda r: r["ini"])
            per_inizio = {r["ini"]: r for r in regioni}

            pagina_ir = PageIR(id=f"page-{pi:04d}", page_num=pi + 1)
            ordine = 0

            fuori_banda = candidati["primitive"] - candidati["in_banda"]
            if fuori_banda > 0:
                pagina_ir.blocks.append(
                    _nota_blocco(
                        f"Ordine di lettura non stabilito per {fuori_banda} span su "
                        f"{candidati['primitive']}: fuori dalle bande di colonna, "
                        f"ordinati per posizione verticale. Il testo puo' risultare "
                        f"interlacciato fra colonne.",
                        pi,
                        ordine,
                        "ordine",
                    )
                )
                ordine += 1
                statistiche["pagine_con_avviso_ordine"] += 1

            # Le note vanno DOVE si legge l'elemento, non tutte in cima:
            # ognuna si aggancia alla prima riga, nell'ordine di lettura, che
            # comincia alla sua altezza o piu' sotto. E' una scelta di
            # posizionamento dichiarata, non una deduzione di appartenenza.
            note_per_riga: dict[int, list[tuple[str, object, str, str | None]]] = {}
            aggancio = _aggancio_di(righe)
            for candidato in list(candidati["sfondi"]) + list(candidati["bordi"]):
                tipo = "sfondo di pagina" if candidato in candidati["sfondi"] else "fascia di bordo"
                x0, y0, x1, y1 = candidato.bbox
                note_per_riga.setdefault(aggancio(candidato.bbox), []).append(
                    ("vector", candidato, f"{tipo}, {x1 - x0:.0f}x{y1 - y0:.0f}pt", None)
                )
                statistiche["note_sfondo"] += 1

            for primitiva, descrizione, percorso in _estrai_raster(
                doc, pi, candidati["primitive_page"], cartella, gia_viste
            ):
                note_per_riga.setdefault(aggancio(primitiva.bbox), []).append(
                    ("image", None, descrizione, percorso or None)
                )
                statistiche["note_immagine"] += 1
                statistiche["immagini_estratte"] += 1 if percorso else 0

            buffer: list[dict] = []
            chiave: tuple[int, int] | None = None
            i = 0
            while i < len(righe):
                for kind, candidato, descrizione, percorso in note_per_riga.pop(i, []):
                    if buffer:
                        pagina_ir.blocks.append(
                            _paragrafo(buffer, pi, ordine, marcatori, contenuto)
                        )
                        ordine += 1
                        buffer, chiave = [], None
                    pagina_ir.blocks.append(
                        _nota_asset(candidato, pi, ordine, kind, descrizione, percorso)
                    )
                    ordine += 1
                regione = per_inizio.get(i)
                if regione is not None:
                    if buffer:
                        pagina_ir.blocks.append(
                            _paragrafo(buffer, pi, ordine, marcatori, contenuto)
                        )
                        ordine += 1
                        buffer, chiave = [], None
                    blocco = righe[regione["ini"] : regione["fine"] + 1]
                    testo = "\n".join(r["testo"] for r in blocco)
                    contenuto.update(_senza_spazi(testo))
                    pagina_ir.blocks.append(
                        BlockIR(
                            id=f"r-{pi:04d}-{ordine:04d}",
                            type="text",
                            page_num=pi + 1,
                            order=ordine,
                            bbox=(
                                min(r["x0"] for r in blocco),
                                min(r["y0"] for r in blocco),
                                max(r["x1"] for r in blocco),
                                max(r["y1"] for r in blocco),
                            ),
                            text=testo,
                            role="callout",
                            metadata={"callout_type": regione["tipo"], "title": regione["nota"]},
                        )
                    )
                    ordine += 1
                    statistiche[f"regioni_{regione['tipo']}"] += 1
                    i = regione["fine"] + 1
                    continue
                riga = righe[i]
                k = (riga["colonna"], riga["blocco"])
                if buffer and (k != chiave or _marcatore_iniziale(riga["testo"], marcatori)):
                    pagina_ir.blocks.append(_paragrafo(buffer, pi, ordine, marcatori, contenuto))
                    ordine += 1
                    buffer = []
                buffer.append(riga)
                chiave = k
                i += 1
            if buffer:
                pagina_ir.blocks.append(_paragrafo(buffer, pi, ordine, marcatori, contenuto))
                ordine += 1
            for indice in sorted(note_per_riga):
                for kind, candidato, descrizione, percorso in note_per_riga[indice]:
                    pagina_ir.blocks.append(
                        _nota_asset(candidato, pi, ordine, kind, descrizione, percorso)
                    )
                    ordine += 1

            documento_ir.pages.append(pagina_ir)
            documento_ir.page_count += 1

            # Misura per il prossimo giro: le celle di pdfplumber conservano i
            # caratteri della pagina, o una tabella Markdown perderebbe testo?
            for tabella in plumber.pages[pi].find_tables():
                estratto = "".join(
                    cella or "" for fila in tabella.extract() for cella in fila
                )
                dentro_bbox = "".join(
                    r["testo"] for r in righe if _dentro(tabella.bbox, r)
                )
                celle_totali += 1
                celle_uguali += 1 if _senza_spazi(estratto) == _senza_spazi(dentro_bbox) else 0

    statistiche["celle_conformi"] = celle_uguali
    statistiche["tabelle_misurate"] = celle_totali
    return pagine, documento_ir, contenuto, statistiche


def _senza_spazi(testo: str) -> Counter[str]:
    return Counter(c for c in unicodedata.normalize("NFKC", testo) if not c.isspace())


def _paragrafo(buffer, pi: int, ordine: int, marcatori, contenuto: Counter[str]) -> BlockIR:
    marcatore = _marcatore_iniziale(buffer[0]["testo"], marcatori)
    testo = " ".join(r["testo"].strip() for r in buffer)
    contenuto.update(_senza_spazi(testo))
    return BlockIR(
        id=f"b-{pi:04d}-{ordine:04d}",
        type="text",
        page_num=pi + 1,
        order=ordine,
        bbox=(
            min(r["x0"] for r in buffer),
            min(r["y0"] for r in buffer),
            max(r["x1"] for r in buffer),
            max(r["y1"] for r in buffer),
        ),
        text=testo,
        style=_stile(buffer[0]),
        role="bullet_list" if marcatore else None,
        metadata={"marker": marcatore} if marcatore else {},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resa Markdown con tutti i producer")
    parser.add_argument("pdf")
    parser.add_argument("--out", required=True)
    parser.add_argument("--da", type=int, default=0)
    parser.add_argument("--a", type=int, default=10**6)
    args = parser.parse_args(argv)

    cartella = Path(args.out)
    cartella.mkdir(parents=True, exist_ok=True)
    pagine, documento, contenuto, statistiche = costruisci(
        args.pdf, cartella, args.da, min(args.a, 10**6)
    )

    da, a = args.da, documento.page_count + args.da - 1
    atteso: Counter[str] = Counter()
    for pi in range(da, min(a + 1, len(pagine))):
        for riga in pagine[pi]:
            atteso += _senza_spazi(riga["testo"])
    if atteso == contenuto:
        print(f"S1 conservazione: OK, {sum(atteso.values())} caratteri non-spazio")
    else:
        print("S1 conservazione: FALLITA", file=sys.stderr)
        print(f"   eccesso: {(contenuto - atteso).most_common(8)}", file=sys.stderr)
        print(f"   mancanti: {(atteso - contenuto).most_common(8)}", file=sys.stderr)

    testo = build_markdown(documento)
    destinazione = cartella / f"{Path(args.pdf).stem}_p{da}-{a}.md"
    destinazione.write_text(testo, encoding="utf-8")
    print(f"pagine {da}-{a}: {documento.page_count} pagine, "
          f"{sum(len(p.blocks) for p in documento.pages)} blocchi")
    for chiave in sorted(statistiche):
        print(f"   {chiave}: {statistiche[chiave]}")
    print(f"markdown: {destinazione}")
    return 0 if atteso == contenuto else 1


if __name__ == "__main__":
    raise SystemExit(main())
