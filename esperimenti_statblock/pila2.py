"""`pila.py` con le correzioni 2 e 3. Criterio in CRITERIO_CORREZIONI_2_3.md.

`pila.py` resta CONGELATO (SPEC_PILA.md): questo file e' la copia con le due
correzioni di difetto autorizzate, e nient'altro.

Cosa cambia rispetto a `pila.py`, e nulla di piu':

1. **Estrazione multipla per riga** (`etichette`, era `etichetta`): un formato
   che mette 2-3 campi sulla stessa riga non perde piu' tutti i campi tranne il
   primo (VERDETTO_MANUALE2.md, causa 2).
2. **Confini di colonna dal documento** (`colonne.righe_per_pagina`, era
   `carica` con `COL_GAP = 30.0`): la costante in punti spariva, i confini
   arrivano dal producer `layout.column_band` di produzione
   (VERDETTO_MANUALE2.md, causa 3).

Nessuna costante spostata: maggioranza 0,5, profondita' massima 8, Jaccard 0,4,
MIN_GRUPPO 5, MIN_RICORRENZA = MIN_GRUPPO, LIFT_STRATO 2,0 restano quelle
congelate. La soglia di ricorrenza (causa 1) e la misura di copertura non sono
toccate qui: sono le correzioni 1 e 4, fuori dallo scope di questo giro.

Uso:  python3 pila2.py <file.pdf> [--verita REGEX]
"""
from __future__ import annotations
import re, sys, unicodedata
from collections import Counter

from colonne import righe_per_pagina

MAGGIORANZA = 0.5
PROF_MAX = 8
JACCARD = 0.4
MIN_GRUPPO = 5
# Un'etichetta che ricorre meno volte della dimensione minima di un gruppo non
# puo' caratterizzare nessun gruppo ammissibile: legata per coerenza interna,
# non scelta guardando i risultati di questo manuale.
MIN_RICORRENZA = MIN_GRUPPO
# Uno strato di testa dev'essere almeno 2x piu' frequente in quella posizione
# che su una riga qualunque della REGIONE (non del documento).
LIFT_STRATO = 2.0


def squash(t: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t)).lower()


def clean(t: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip()


def etichette(riga: dict) -> list[str]:
    """Tutte le etichette della riga, non solo la prima. CORREZIONE 2.

    La regola di `pila.py` -- primo span di una riga che porta almeno due stili
    -- ripetuta lungo la riga: uno span e' un'etichetta se quello successivo ha
    stile diverso, il valore e' la corsa di span in quello stile, e la scansione
    riprende dopo. Su una riga con una sola coppia da' esattamente cio' che dava
    `pila.py`; su `Ferocia: 2  Taglia: Normale` non perde piu' `Taglia`.

    Nessuna dimensione e nessuno stile di corpo: `real5.py` estraeva piu' coppie
    per riga ma chiedeva che l'etichetta non fosse piu' grande del corpo locale,
    e la nozione di corpo e' proprio cio' che CRITERIO_SENZA_CORPO ha tolto dal
    metodo. Ripristinare la sua versione avrebbe rimesso dentro una soglia di
    dimensione: non e' quella la correzione autorizzata."""
    stili, span = riga["stili"], riga["span"]
    fuori: list[str] = []
    i = 0
    while i + 1 < len(span):
        if stili[i] == stili[i + 1]:
            i += 1
            continue
        j = i + 1
        while j + 1 < len(span) and stili[j + 1] == stili[i + 1]:
            j += 1
        e = clean(span[i]).rstrip(":").strip()
        if e:
            fuori.append(e)
        i = j + 1
    return fuori


def nuclei_di(pagine) -> tuple[list[tuple[int, int, int]], set[str]]:
    freq = Counter()
    for pg in pagine:
        for r in pg:
            # Un'etichetta ripetuta sulla stessa riga conta una volta: e' una
            # riga sola, e il conteggio serve a dire quanto ricorre nel
            # documento.
            for e in set(etichette(r)):
                freq[e] += 1
    schema = {k for k, c in freq.items() if c >= MIN_RICORRENZA}
    nuclei = []
    for pi, pg in enumerate(pagine):
        corsa, stacco = [], 0
        for i, r in enumerate(pg):
            if set(etichette(r)) & schema:
                corsa.append(i); stacco = 0
            elif corsa:
                stacco += 1
                if stacco > 2:
                    nuclei.append((pi, corsa[0], corsa[-1])); corsa, stacco = [], 0
        if corsa:
            nuclei.append((pi, corsa[0], corsa[-1]))
    return nuclei, schema


def raggruppa(nuclei, pagine, schema):
    firma = {}
    for z in nuclei:
        pi, a, b = z
        firma[z] = {e for r in pagine[pi][a:b + 1] for e in etichette(r) if e in schema}
    jac = lambda x, y: len(x & y) / max(len(x | y), 1)
    gruppi = []
    for z in sorted(nuclei, key=lambda z: -len(firma[z])):
        for g in gruppi:
            if jac(firma[z], g["firma"]) >= JACCARD:
                g["nuclei"].append(z); break
        else:
            gruppi.append({"firma": set(firma[z]), "nuclei": [z]})
    gruppi.sort(key=lambda g: -len(g["nuclei"]))
    return gruppi


def profondita_testa(gruppo, pagine, base) -> tuple[int, list]:
    """Cammina all'indietro finche' esiste uno strato di testa consistente.

    Uno strato e' uno stile che (a) compare a quella distanza prima della
    maggioranza dei nuclei e (b) e' li' molto piu' frequente che su una riga
    qualunque del documento. La condizione (b) e' una CORREZIONE DI DIFETTO
    dichiarata in SPEC_PILA.md: senza di essa lo stile di corpo, che sta prima
    di quasi ogni riga, supera sempre la maggioranza e la camminata non si
    ferma mai."""
    n = len(gruppo["nuclei"])
    strati, prof = [], 0
    for d in range(1, PROF_MAX + 1):
        conta = Counter()
        for pi, a, _ in gruppo["nuclei"]:
            if a - d < 0:
                continue
            for st in set(pagine[pi][a - d]["stili"]):
                conta[st] += 1
        if not conta:
            break
        cand = [(st, c) for st, c in conta.items()
                if c >= MAGGIORANZA * n and (c / n) >= LIFT_STRATO * base.get(st, 1e-9)]
        if not cand:
            break
        stile, c = max(cand, key=lambda x: x[1] / max(base.get(x[0], 1e-9), 1e-9))
        strati.append((d, stile, c, n, round((c / n) / max(base.get(stile, 1e-9), 1e-9), 1)))
        prof = d
    return prof, strati


def record_di(path: str):
    pagine = righe_per_pagina(path)
    nuclei, schema = nuclei_di(pagine)
    gruppi = raggruppa(nuclei, pagine, schema)
    def base_di(gruppo):
        """Frequenza di base LOCALE: sulle pagine dove il gruppo vive, non sul
        documento. Correzione di difetto dichiarata: con la base globale lo
        stile di corpo delle pagine-schede (8pt) risulta raro nel documento
        (dove il corpo e' 9pt) e ottiene un lift alto, quindi la camminata non
        si ferma mai. E' la terza volta che una statistica globale sbaglia dove
        serve quella della regione."""
        pag = {pi for pi, _, _ in gruppo["nuclei"]}
        righe = [r for pi in pag for r in pagine[pi]]
        tot = len(righe) or 1
        c = Counter()
        for r in righe:
            for st in set(r["stili"]):
                c[st] += 1
        return {st: v / tot for st, v in c.items()}
    teste = []                       # (pagina, riga_inizio, gruppo)
    info = []
    for gi, g in enumerate(gruppi):
        if len(g["nuclei"]) < MIN_GRUPPO:
            continue
        prof, strati = profondita_testa(g, pagine, base_di(g))
        info.append((gi, len(g["nuclei"]), prof, strati, sorted(g["firma"])))
        for pi, a, b in g["nuclei"]:
            teste.append((pi, max(0, a - prof), gi))
    # estensione: fino alla testa successiva nella stessa pagina/colonna
    per_pag = {}
    for pi, ini, gi in teste:
        per_pag.setdefault(pi, []).append((ini, gi))
    record = []
    for pi, lista in per_pag.items():
        lista.sort()
        for k, (ini, gi) in enumerate(lista):
            fine = lista[k + 1][0] - 1 if k + 1 < len(lista) else len(pagine[pi]) - 1
            if fine >= ini:
                record.append((pi, ini, fine, gi))
    return pagine, schema, info, record


if __name__ == "__main__":
    path = sys.argv[1]
    ver = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--verita" else None
    pagine, schema, info, record = record_di(path)
    print(f"file: {path}")
    print(f"etichette di schema indotte: {len(schema)}")
    print(f"   {sorted(schema)[:14]}")
    print(f"\ngruppi con >= {MIN_GRUPPO} nuclei: {len(info)}")
    for gi, n, prof, strati, firma in info:
        print(f"\n  gruppo {gi}: {n} nuclei, profondita' di testa dedotta = {prof}")
        for d, st, c, tot, lift in strati:
            print(f"      strato a {d} righe prima: {st}  ({c}/{tot}, lift {lift}x)")
        print(f"      firma: {firma[:10]}")
    print(f"\nrecord emessi: {len(record)}")
    if ver:
        rx = re.compile(ver)
        v = [r for r in record
             if rx.search(squash("".join(x["testo"] for x in pagine[r[0]][r[1]:r[2] + 1])))]
        print(f"record che soddisfano la verita' {ver!r}: {len(v)}")
