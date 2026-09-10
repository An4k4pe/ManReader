"""Il riquadro disegnato da' i confini delle schede anche dove e' vettoriale?

Misura, non meccanismo. Riusa **invariato** il riconoscimento del giro
precedente -- `markdown_ir.candidati_di_pagina` (i sei producer) e
`markdown_ir.regioni_di_pagina` (un riquadro `embedded_visual` o
`interior_visual_frame` che contiene almeno due righe con almeno due coppie
etichetta/valore; fra regioni sovrapposte vince la piu' ampia) -- e lo mette
contro una verita' che non passa dai riquadri: un'etichetta che compare **una
volta per scheda** (`--verita`), letta con `pila2.etichette`.

Criterio scritto prima dei dati, 10 settembre 2026, chat dedicata alle schede
su IR 2. Per ogni riga-verita':

    presa        sta in una regione `scheda` che contiene solo lei
    fusa         sta in una regione `scheda` con altre righe-verita'
    in tabella   sta in una regione `tabella` (ha vinto la tabella)
    mancata      non sta in nessuna regione

Regge se fuse + in tabella + mancate = 0 e ogni regione presa comincia dal
nome. Le regioni `scheda` senza riga-verita' si elencano, non si giudicano.

«Comincia dal nome» e' un ausilio di misura dichiarato -- la prima riga della
regione non porta etichette ed e' tutta in maiuscolo -- non una regola da
portare in produzione.

Opzioni per i passi successivi, ciascuno col suo criterio:
  --separa          separa i riquadri fusi (`riquadri.separa_riquadri`),
                    CRITERIO_SEPARA_RIQUADRI.md
  --senza-tabelle   toglie `table_candidate` dalle regioni, perche' scheda
                    contro tabella e' un passo a parte
  --una-coppia      una riga a campi porta almeno UNA coppia invece di due,
                    CRITERIO_UNA_COPPIA.md

Uso:  python confini_dal_riquadro.py <pdf> --verita Thresholds [--verita ...]
                                       [--separa] [--senza-tabelle] [--una-coppia]
                                       [--da N] [--a N]
"""
from __future__ import annotations

import argparse
from collections import Counter

import markdown_ir
import pdfplumber
import pila2
import pymupdf
import riquadri

ESITI = ("presa", "fusa", "in tabella", "mancata")


def _verita_di(righe: list[dict], chiavi: list[str]) -> dict[int, str]:
    fuori: dict[int, str] = {}
    for indice, riga in enumerate(righe):
        for etichetta in pila2.etichette(riga):
            compressa = pila2.squash(etichetta)
            if any(chiave in compressa for chiave in chiavi):
                fuori[indice] = compressa
                break
    return fuori


def _comincia_dal_nome(riga: dict) -> bool:
    testo = pila2.clean(riga["testo"])
    return (
        not pila2.etichette(riga)
        and any(c.isalpha() for c in testo)
        and testo == testo.upper()
    )


def _candidati_che_passano(
    righe: list[dict], candidati: dict, min_coppie: int
) -> tuple[int, int, int]:
    """Quanti candidati visivi ci sono, e quanti passano il criterio PRIMA che
    la regola «vince la piu' ampia» scelga fra loro."""
    campi = markdown_ir.righe_a_campi(righe, min_coppie)
    visivi = list(candidati["embedded"]) + list(candidati["riquadri"])
    passano = 0
    for candidato in visivi:
        dentro = {i for i, r in enumerate(righe) if markdown_ir._dentro(candidato.bbox, r)}
        if len(dentro & campi) >= 2:
            passano += 1
    return len(candidati["embedded"]), len(candidati["riquadri"]), passano


def _breve(testo: str, n: int = 60) -> str:
    testo = pila2.clean(testo)
    return testo if len(testo) <= n else testo[: n - 1] + "…"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("--verita", action="append", required=True)
    parser.add_argument("--separa", action="store_true")
    parser.add_argument("--senza-tabelle", action="store_true")
    parser.add_argument("--una-coppia", action="store_true")
    parser.add_argument("--da", type=int, default=0)
    parser.add_argument("--a", type=int, default=10**6)
    args = parser.parse_args(argv)
    chiavi = [pila2.squash(v) for v in args.verita]
    min_coppie = 1 if args.una_coppia else 2

    pagine, _schema, info, record = pila2.record_di(args.pdf)
    firma_di = {gi: firma for gi, _n, _prof, _strati, firma in info}
    record_righe: list[dict[int, int]] = [dict() for _ in pagine]
    for pi, ini, fine, gi in record:
        for i in range(ini, fine + 1):
            record_righe[pi].setdefault(i, gi)

    totale: Counter[str] = Counter()
    eccezioni: list[str] = []
    senza_verita: list[str] = []
    prese_totali = prese_dal_nome = divisi_totali = 0

    print(
        f"file: {args.pdf}\nverita': {args.verita}\n"
        f"separa: {args.separa}   senza tabelle: {args.senza_tabelle}   "
        f"coppie per riga a campi: {min_coppie}\n"
    )
    print(" idx  ver  presa fusa tab manc  senza   ev ivf passano  div")
    with pymupdf.open(args.pdf) as documento, pdfplumber.open(args.pdf) as plumber:
        for pi in range(args.da, min(args.a + 1, len(pagine))):
            righe = pagine[pi]
            verita = _verita_di(righe, chiavi)
            candidati = markdown_ir.candidati_di_pagina(documento, plumber, pi)
            if args.separa:
                candidati = riquadri.separa_riquadri(candidati, righe)
            if args.senza_tabelle:
                candidati = {**candidati, "tabelle": []}
            regioni = markdown_ir.regioni_di_pagina(
                righe, record_righe[pi], firma_di, candidati, min_coppie=min_coppie
            )
            conto: Counter[str] = Counter()
            for indice in sorted(verita):
                regione = next((r for r in regioni if indice in r["righe"]), None)
                if regione is None:
                    esito = "mancata"
                elif regione["tipo"] == "tabella":
                    esito = "in tabella"
                elif len(set(verita) & regione["righe"]) == 1:
                    esito = "presa"
                else:
                    esito = "fusa"
                conto[esito] += 1
                if esito != "presa":
                    dettaglio = (
                        f", regione di {len(regione['righe'])} righe da "
                        f"{_breve(righe[regione['ini']]['testo'], 40)!r}"
                        if regione is not None
                        else ""
                    )
                    eccezioni.append(
                        f"  idx {pi:3d}  {esito:10s} {_breve(righe[indice]['testo'])!r}{dettaglio}"
                    )
            schede = [r for r in regioni if r["tipo"] == "scheda"]
            for regione in schede:
                dentro = set(verita) & regione["righe"]
                if not dentro:
                    senza_verita.append(
                        f"  idx {pi:3d}  {len(regione['righe']):3d} righe  "
                        f"{_breve(righe[regione['ini']]['testo'])!r}"
                    )
                elif len(dentro) == 1:
                    prese_totali += 1
                    if _comincia_dal_nome(righe[regione["ini"]]):
                        prese_dal_nome += 1
                    else:
                        eccezioni.append(
                            f"  idx {pi:3d}  non dal nome: prima riga "
                            f"{_breve(righe[regione['ini']]['testo'])!r}"
                        )
            n_ev, n_ivf, passano = _candidati_che_passano(righe, candidati, min_coppie)
            n_senza = sum(1 for r in schede if not set(verita) & r["righe"])
            divisi = candidati.get("divisi", 0)
            divisi_totali += divisi
            totale.update(conto)
            if verita or schede or divisi:
                print(
                    f" {pi:3d}  {len(verita):3d}  "
                    + " ".join(f"{conto[e]:4d}" for e in ESITI)
                    + f"  {n_senza:5d}  {n_ev:3d} {n_ivf:3d} {passano:7d}  {divisi:3d}"
                )

    righe_verita = sum(totale.values())
    print(f"\nrighe-verita' {righe_verita}: " + ", ".join(f"{e} {totale[e]}" for e in ESITI))
    print(f"regioni prese che cominciano dal nome: {prese_dal_nome} su {prese_totali}")
    print(f"candidati separati: {divisi_totali}")
    print(f"regioni scheda senza riga-verita': {len(senza_verita)}")
    for voce in senza_verita:
        print(voce)
    print(f"\neccezioni: {len(eccezioni)}")
    for voce in eccezioni:
        print(voce)
    regge = totale["fusa"] + totale["in tabella"] + totale["mancata"] == 0 and (
        prese_dal_nome == prese_totali
    )
    print(f"\nVERDETTO: {'REGGE' if regge else 'NON REGGE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
