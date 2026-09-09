"""La misura di copertura. Criterio in CRITERIO_COPERTURA.md.

**Correzione 4** di `PASSAGGIO_DI_CONSEGNE.md` §5: quanto testo del documento
non e' spiegato da nessuno schema, e dove si concentra. Esiste per un guasto
preciso -- sul secondo manuale il metodo ha mancato un template di 4 schede
**senza segnalare niente** -- e il suo unico banco di prova serio e' proprio
quel giro fallito, che si rifa' qui importando il rilevatore CONGELATO.

Riporta, non decide: nessuna soglia si abbassa, nessun template raro viene
promosso. Il residuo si definisce sulle **etichette** e non sull'appartenenza a
un record emesso, perche' e' cosi' che il fallimento e' stato silenzioso -- le
righe delle schede erano finite dentro i record di un altro gruppo.

Uso:  python3 copertura.py <file.pdf> [--congelato]
      --congelato usa `pila.py` invece di `pila2.py`, per il retro-test.
"""
from __future__ import annotations

import sys
from collections import defaultdict

JACCARD = 0.4          # lo stesso del metodo
STACCO = 2             # la stessa tolleranza di `nuclei_di`
PAGINE_RICORRENZA = 3  # una firma rara "ricorre" se sta su >= 3 pagine distinte


def _motore(path: str, congelato: bool):
    """Il rilevatore e la sua estrazione di etichette, senza modificarlo."""
    if congelato:
        import pila

        pagine, schema, info, record = pila.record_di(path)

        def etich(riga: dict) -> list[str]:
            e = pila.etichetta(riga)
            return [e] if e else []

        return pila.squash, pagine, schema, info, record, etich

    import pila2

    pagine, schema, info, record = pila2.record_di(path)
    return pila2.squash, pagine, schema, info, record, pila2.etichette


def copertura_testo(squash, pagine, record):
    """C1: caratteri non-spazio dentro un record emesso, totale e per pagina."""
    dentro: dict[int, set[int]] = defaultdict(set)
    for pi, ini, fine, _gi in record:
        dentro[pi].update(range(ini, fine + 1))

    per_pagina = []
    totale = coperti = 0
    for pi, pg in enumerate(pagine):
        c = sum(len(squash(r["testo"])) for r in pg)
        d = sum(len(squash(pg[i]["testo"])) for i in dentro.get(pi, set()) if i < len(pg))
        totale += c
        coperti += d
        per_pagina.append((pi, c, d))
    return totale, coperti, per_pagina


def corse_residue(pagine, schema, etich):
    """Le corse di righe che portano etichette **tutte** fuori dallo schema.

    Stesso meccanismo dei nuclei (stessa tolleranza di stacco), popolazione
    complementare: nessuna costante nuova."""
    corse = []
    for pi, pg in enumerate(pagine):
        corsa: list[int] = []
        firma: set[str] = set()
        stacco = 0
        for i, r in enumerate(pg):
            es = set(etich(r))
            if es and not (es & schema):
                corsa.append(i)
                firma |= es
                stacco = 0
            elif corsa:
                stacco += 1
                if stacco > STACCO:
                    corse.append((pi, corsa[0], corsa[-1], frozenset(firma)))
                    corsa, firma, stacco = [], set(), 0
        if corsa:
            corse.append((pi, corsa[0], corsa[-1], frozenset(firma)))
    return corse


def raggruppa_rare(corse):
    """Le corse residue per somiglianza di firma. Stesso Jaccard del metodo."""
    def jac(a, b):
        return len(a & b) / max(len(a | b), 1)

    gruppi: list[dict] = []
    for c in sorted(corse, key=lambda c: -len(c[3])):
        for g in gruppi:
            if jac(c[3], g["firma"]) >= JACCARD:
                g["corse"].append(c)
                break
        else:
            gruppi.append({"firma": set(c[3]), "corse": [c]})
    gruppi.sort(key=lambda g: (-len({c[0] for c in g["corse"]}), -len(g["corse"])))
    return gruppi


def main(argv: list[str]) -> int:
    path = argv[1]
    congelato = "--congelato" in argv
    squash, pagine, schema, info, record, etich = _motore(path, congelato)

    print(f"file: {path}")
    print(f"rilevatore: {'pila.py (CONGELATO)' if congelato else 'pila2.py'}")
    print(f"etichette di schema: {len(schema)}   record emessi: {len(record)}")

    totale, coperti, per_pagina = copertura_testo(squash, pagine, record)
    quota = coperti / totale if totale else 0.0
    print(f"\n== C1 == caratteri non-spazio dentro un record: {coperti}/{totale} ({quota:.1%})")
    scoperte = sorted(per_pagina, key=lambda t: -(t[1] - t[2]))[:10]
    print("   pagine con piu' testo fuori dai record (indice, non coperti/totali):")
    for pi, c, d in scoperte:
        print(f"      pagina {pi:3d}   {c - d:5d}/{c:5d}")

    corse = corse_residue(pagine, schema, etich)
    gruppi = raggruppa_rare(corse)
    ricorrenti = [g for g in gruppi if len({c[0] for c in g["corse"]}) >= PAGINE_RICORRENZA]
    print(
        f"\n== C2 == corse residue: {len(corse)} in {len(gruppi)} firme; "
        f"firme su >= {PAGINE_RICORRENZA} pagine: {len(ricorrenti)}"
    )
    for g in ricorrenti[:40]:
        pag = sorted({c[0] for c in g["corse"]})
        etichette_firma = sorted(g["firma"])
        print(
            f"   {len(pag):3d} pagine, {len(g['corse']):3d} corse   "
            f"pagine {pag[:8]}{'...' if len(pag) > 8 else ''}"
        )
        print(f"        firma: {etichette_firma[:8]}{'...' if len(etichette_firma) > 8 else ''}")

    print("\n== C3 == pagine con piu' corse residue")
    per_pag: dict[int, int] = defaultdict(int)
    for pi, _a, _b, _f in corse:
        per_pag[pi] += 1
    piu_residue = sorted(per_pag.items(), key=lambda t: -t[1])[:10]
    for pi, n in piu_residue:
        print(f"      pagina {pi:3d}   {n:3d} corse")

    if info:
        gi, n = info[0][0], info[0][1]
        # Le pagine del gruppo si prendono dai record gia' emessi, che portano
        # l'indice di gruppo: nessun ricalcolo, e vale per entrambi i motori.
        pagine_gruppo = {pi for pi, _a, _b, g in record if g == gi}
        sovrapposte = [pi for pi, _n in piu_residue if pi in pagine_gruppo]
        print(
            f"\n   A2: il gruppo piu' numeroso ({n} nuclei) vive su "
            f"{len(pagine_gruppo)} pagine; delle 10 pagine con piu' residuo, "
            f"{len(sovrapposte)} sono sue: {sovrapposte}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
