"""Le schede in Markdown: verbatim, con la nota, passando dalla IR del repo.

Criterio in CRITERIO_MARKDOWN_SCHEDE.md. Il bersaglio e' il Markdown.

Il punto del giro e' la LEGATURA: il Markdown non lo stampa questo file, lo
costruisce `markdown_builder.build_markdown` del repo, **invariato**, a partire
da un `DocumentIR` (`ir_model.py`). Le righe e le colonne arrivano dalla catena
di produzione gia' usata in `colonne.py` (cattura -> primitive normalizzate ->
producer `layout.column_band` -> ordine a bande). Se la resa e' brutta, e' un
fatto sulla IR e sul renderer, non un difetto locale.

Nessun tipo di blocco nuovo e nessuna modifica al renderer: una regione usa
`role="callout"`, la sola forma delimitata che IR 1 sa gia' rendere. E' una
scelta di RESA, dichiarata e reversibile: non afferma che una scheda sia un
callout.

Regola di non-perdita (`COMPITO_APERTO_schede_rare.md`): una regione a forma di
record che nessuno schema spiega non si scarta, esce con la nota «struttura non
riconosciuta».

Uso:  python3 markdown_schede.py <file.pdf> --out <dir> [--da N] [--a N]
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

import pila2  # noqa: E402
from colonne import visuali_per_pagina  # noqa: E402
from copertura import PAGINE_RICORRENZA, corse_residue, raggruppa_rare  # noqa: E402

from ir_model import BlockIR, DocumentIR, PageIR  # noqa: E402
from markdown_builder import build_markdown  # noqa: E402

TIPO_CALLOUT = "scheda"


def marcatori_di(schema: set[str]) -> set[str]:
    """I marcatori di elenco del manuale, DEDOTTI e non cablati.

    `ir_builder.py:17` ne tiene una lista fissa di sei; il punto elenco di un
    manuale e' spesso un codepoint di un font di simboli, e una lista cablata
    prende solo i manuali che ci sono dentro. Qui si usa cio' che il metodo ha
    gia' calcolato: un'etichetta ricorrente **senza caratteri alfanumerici** e'
    un marcatore, non un campo. Su Dragonbane deduce `–` e `✦`, e `✦` e'
    effettivamente uno dei sei della lista legacy -- il criterio dedotto la
    contiene, su questo manuale, invece di doverla indovinare."""
    return {e for e in schema if e and not any(c.isalnum() for c in e)}


def _marcatore_iniziale(testo: str, marcatori: set[str]) -> str | None:
    spoglio = testo.lstrip()
    for marcatore in sorted(marcatori, key=len, reverse=True):
        if spoglio.startswith(marcatore):
            return marcatore
    return None


def _senza_spazi(testo: str) -> Counter[str]:
    return Counter(c for c in unicodedata.normalize("NFKC", testo) if not c.isspace())


def _stile(riga: dict) -> dict[str, str]:
    """Lo stile del blocco come lo vuole `markdown_builder`: dimensione media
    pesata sui caratteri, grassetto e corsivo dedotti dal nome del font."""
    peso_totale = 0
    dimensione = 0.0
    grassetto = corsivo = 0
    for (nome, size, _colore), testo in zip(riga["stili"], riga["span"], strict=True):
        n = len(testo.strip())
        if n == 0:
            continue
        peso_totale += n
        dimensione += size * n
        if "bold" in nome.lower() or "black" in nome.lower():
            grassetto += n
        if "italic" in nome.lower() or "oblique" in nome.lower():
            corsivo += n
    if peso_totale == 0:
        return {}
    return {
        "avg_font_size": f"{dimensione / peso_totale:.1f}",
        "bold": "true" if grassetto * 2 > peso_totale else "false",
        "italic": "true" if corsivo * 2 > peso_totale else "false",
    }


def _bbox(riga: dict) -> tuple[float, float, float, float]:
    return (riga["x0"], riga["y0"], riga["x1"], riga["y1"])


def regioni(path: str):
    """Le regioni per pagina: i record del rilevatore piu' il residuo ricorrente.

    Ritorna anche pagine, schema e le firme, perche' servono alla nota."""
    pagine, schema, info, record = pila2.record_di(path)
    firma_di = {gi: firma for gi, _n, _prof, _strati, firma in info}
    marcatori = marcatori_di(schema)
    # Un gruppo la cui firma e' fatta solo di marcatori di elenco non e' un
    # record: e' un elenco puntato. Non diventa callout, e la resa lo tratta
    # come elenco. Regola dedotta, non una soglia.
    solo_elenchi = {
        gi for gi, firma in firma_di.items() if firma and set(firma) <= marcatori
    }

    per_pagina: dict[int, list[dict]] = {}
    for pi, ini, fine, gi in record:
        if gi in solo_elenchi:
            continue
        per_pagina.setdefault(pi, []).append(
            {
                "ini": ini,
                "fine": fine,
                "tipo": "record",
                "nota": f"gruppo {gi} — {', '.join(firma_di.get(gi, [])[:6])}",
            }
        )

    # Il residuo: solo le firme rare che RICORRONO, con il criterio gia' fissato
    # dalla misura di copertura. Non una soglia nuova.
    corse = corse_residue(pagine, schema, pila2.etichette)
    for gruppo in raggruppa_rare(corse):
        if len({c[0] for c in gruppo["corse"]}) < PAGINE_RICORRENZA:
            continue
        etichette_firma = ", ".join(sorted(gruppo["firma"])[:6])
        for pi, a, b, _f in gruppo["corse"]:
            per_pagina.setdefault(pi, []).append(
                {
                    "ini": a,
                    "fine": b,
                    "tipo": "ignota",
                    "nota": f"struttura non riconosciuta — {etichette_firma}",
                }
            )

    # Una riga sta in al massimo una regione: dove un record copre, il residuo
    # non riapre. I record vincono perche' sono la rivendicazione piu' forte.
    for pi, lista in per_pagina.items():
        lista.sort(key=lambda r: (r["ini"], r["tipo"] != "record"))
        coperte: set[int] = set()
        tenute = []
        for regione in lista:
            righe = set(range(regione["ini"], regione["fine"] + 1))
            if righe & coperte:
                continue
            coperte |= righe
            tenute.append(regione)
        per_pagina[pi] = tenute
    return pagine, per_pagina, marcatori


def _blocco_paragrafo(buffer: list[dict], pi: int, ordine: int, marcatori: set[str]) -> BlockIR:
    """Un paragrafo = un blocco di sorgente. Le righe si uniscono con uno
    spazio, che e' l'unico carattere aggiunto; un paragrafo che comincia con un
    marcatore dedotto prende il ruolo `bullet_list`, cioe' quello che il
    renderer del repo gia' sa rendere."""
    marcatore = _marcatore_iniziale(buffer[0]["testo"], marcatori)
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
        text=" ".join(r["testo"].strip() for r in buffer),
        style=_stile(buffer[0]),
        role="bullet_list" if marcatore else None,
        metadata={"marker": marcatore} if marcatore else {},
    )


def _blocco_regione(blocco: list[dict], pi: int, ordine: int, nota: str) -> BlockIR:
    """La regione esce verbatim, riga per riga, dentro un callout con la nota."""
    return BlockIR(
        id=f"b-{pi:04d}-{ordine:04d}",
        type="text",
        page_num=pi + 1,
        order=ordine,
        bbox=(
            min(r["x0"] for r in blocco),
            min(r["y0"] for r in blocco),
            max(r["x1"] for r in blocco),
            max(r["y1"] for r in blocco),
        ),
        text="\n".join(r["testo"] for r in blocco),
        role="callout",
        metadata={"callout_type": TIPO_CALLOUT, "title": nota},
    )


def documento_ir(path: str, pagine, per_pagina, marcatori, da: int, a: int) -> DocumentIR:
    documento = DocumentIR(schema_version="1.0", source_path=path)
    ordine = 0
    for pi in range(da, min(a + 1, len(pagine))):
        righe = pagine[pi]
        pagina_ir = PageIR(id=f"page-{pi:04d}", page_num=pi + 1)
        regioni_pagina = {r["ini"]: r for r in per_pagina.get(pi, [])}
        buffer: list[dict] = []
        chiave: tuple[int, int] | None = None
        i = 0
        while i < len(righe):
            regione = regioni_pagina.get(i)
            if regione is not None:
                if buffer:
                    pagina_ir.blocks.append(_blocco_paragrafo(buffer, pi, ordine, marcatori))
                    ordine += 1
                    buffer, chiave = [], None
                pagina_ir.blocks.append(
                    _blocco_regione(righe[i : regione["fine"] + 1], pi, ordine, regione["nota"])
                )
                ordine += 1
                i = regione["fine"] + 1
                continue
            riga = righe[i]
            k = (riga["colonna"], riga["blocco"])
            if buffer and (k != chiave or _marcatore_iniziale(riga["testo"], marcatori)):
                pagina_ir.blocks.append(_blocco_paragrafo(buffer, pi, ordine, marcatori))
                ordine += 1
                buffer = []
            buffer.append(riga)
            chiave = k
            i += 1
        if buffer:
            pagina_ir.blocks.append(_blocco_paragrafo(buffer, pi, ordine, marcatori))
            ordine += 1
        documento.pages.append(pagina_ir)
        documento.page_count += 1
    return documento


def verifica_conservazione(pagine, documento: DocumentIR, da: int, a: int) -> bool:
    """R1: i caratteri non-spazio dei blocchi IR sono quelli delle righe.

    La verifica sta sulla IR e non sul Markdown perche' il renderer aggiunge
    legittimamente `#`, `**`, `>` e i commenti di pagina."""
    entrata: Counter[str] = Counter()
    for pi in range(da, min(a + 1, len(pagine))):
        for riga in pagine[pi]:
            entrata += _senza_spazi(riga["testo"])
    uscita: Counter[str] = Counter()
    for pagina in documento.pages:
        for blocco in pagina.blocks:
            uscita += _senza_spazi(blocco.text or "")
    if entrata == uscita:
        print(f"R1 conservazione: OK, {sum(entrata.values())} caratteri non-spazio")
        return True
    print("R1 conservazione: FALLITA", file=sys.stderr)
    print(f"   in eccesso: {(uscita - entrata).most_common(10)}", file=sys.stderr)
    print(f"   mancanti:   {(entrata - uscita).most_common(10)}", file=sys.stderr)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--out", required=True)
    parser.add_argument("--da", type=int, default=0, help="indice posizionale, non stampato")
    parser.add_argument("--a", type=int, default=10**6)
    parser.add_argument("--visuali", action="store_true", help="conta le visuali nelle regioni")
    args = parser.parse_args(argv)

    pagine, per_pagina, marcatori = regioni(args.pdf)
    da, a = args.da, min(args.a, len(pagine) - 1)
    documento = documento_ir(args.pdf, pagine, per_pagina, marcatori, da, a)
    print(f"marcatori di elenco dedotti: {sorted(marcatori)}")
    ok = verifica_conservazione(pagine, documento, da, a)

    testo = build_markdown(documento)
    fuori = Path(args.out)
    fuori.mkdir(parents=True, exist_ok=True)
    destinazione = fuori / f"{Path(args.pdf).stem}_p{da}-{a}.md"
    destinazione.write_text(testo, encoding="utf-8")

    record = sum(1 for lista in per_pagina.values() for r in lista if r["tipo"] == "record")
    ignote = sum(1 for lista in per_pagina.values() for r in lista if r["tipo"] == "ignota")
    nel_range = sum(
        1 for pi in range(da, a + 1) for _r in per_pagina.get(pi, [])
    )
    print(
        f"pagine {da}-{a}: {len(documento.pages)} pagine, "
        f"{sum(len(p.blocks) for p in documento.pages)} blocchi, "
        f"{nel_range} regioni nel range"
    )
    print(f"su tutto il documento: {record} regioni record, {ignote} regioni non riconosciute")
    print(f"markdown: {destinazione} ({len(testo)} caratteri)")

    if args.visuali:
        visuali = visuali_per_pagina(args.pdf)
        dentro = 0
        for pi, lista in per_pagina.items():
            if pi >= len(visuali):
                continue
            for regione in lista:
                blocco = pagine[pi][regione["ini"] : regione["fine"] + 1]
                if not blocco:
                    continue
                x0 = min(r["x0"] for r in blocco)
                y0 = min(r["y0"] for r in blocco)
                x1 = max(r["x1"] for r in blocco)
                y1 = max(r["y1"] for r in blocco)
                for bx0, by0, bx1, by1 in visuali[pi]:
                    if bx0 < x1 and bx1 > x0 and by0 < y1 and by1 > y0:
                        dentro += 1
        print(f"visuali che toccano una regione: {dentro} (fuori scope: la nota per lo sfondo)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
