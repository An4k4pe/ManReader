"""Le misure M2 e M3 del criterio CRITERIO_CORREZIONI_2_3.md.

Committato perche' produce numeri citati: `AGENTS.MD` §Aggiornamento documenti
chiede che lo script che produce un numero riportato stia nel repo. Le etichette
Dragonbane e gli indici di pagina qui dentro sono il verbale di cosa e' stato
verificato, non una soluzione cablata: stesso status degli script sanati di
Milestone 35.

Uso:  python3 misure_correzioni_2_3.py <manuale2.pdf>
"""
from __future__ import annotations

import sys
from collections import Counter

from colonne import righe_per_pagina
from pila2 import clean, etichette, squash

# M2: le cinque etichette della scheda mostro Dragonbane (VERDETTO_MANUALE2.md).
ETICHETTE = ["Ferocia", "Taglia", "Movimento", "Armatura", "PF"]
# M3: le quattro schede mostro, per indice posizionale di pagina e nome stampato.
# I nomi sono il VERBALE di cio' che e' stato letto nel documento, non una
# soluzione cablata: la prima versione di questa misura identificava il nome come
# "la riga piu' vicina sopra i campi con stile diverso", e su 2 pagine su 4
# quella riga e' prosa della descrizione (verificato: pagina 33 riga [7] "mostro
# secondo le regole di pagina 21.", pagina 35 riga [14] "(2D8 danni)."). Una
# misura che identifica l'oggetto sbagliato non misura il criterio: corretta
# come difetto, e dichiarata qui.
SCHEDE = [
    (29, "RAGNO GIGANTE"),
    (31, "PIPISTRELLI VAMPIRO"),
    (33, "LA SIGNORA"),
    (35, "IL WIGHT"),
]

def main(path: str) -> int:
    pagine = righe_per_pagina(path)

    print("== M2: occorrenze viste per etichetta (correzione 2) ==")
    freq: Counter[str] = Counter()
    for pg in pagine:
        for riga in pg:
            for e in set(etichette(riga)):
                freq[e] += 1
    for nome in ETICHETTE:
        print(f"   {nome:12s} {freq[nome]:3d}")

    print("\n== M3: nome e campi nella stessa colonna? (correzione 3) ==")
    insieme = 0
    for indice, atteso in SCHEDE:
        righe = pagine[indice] if indice < len(pagine) else []
        campi = next(
            (r for r in righe if squash(r["testo"]).startswith("ferocia:")), None
        )
        nome = next(
            (r for r in righe if squash(r["testo"]) == squash(atteso)), None
        )
        if campi is None or nome is None:
            print(f"   pagina {indice}: campi={campi is not None} nome={nome is not None}")
            continue
        stessa = nome["colonna"] == campi["colonna"]
        insieme += 1 if stessa else 0
        print(
            f"   pagina {indice}: nome {clean(nome['testo'])[:24]!r} col={nome['colonna']} "
            f"x0={nome['x0']:.1f} | campi col={campi['colonna']} x0={campi['x0']:.1f} "
            f"-> {'STESSA' if stessa else 'DIVERSE'}"
        )
    print(f"   stessa colonna: {insieme} su {len(SCHEDE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
