"""Le righe di campi di una scheda: combinazioni di etichette che si ripetono.

**Indicazione dell'utente, 19 settembre 2026**, guardando due pagine del bestiario
di Dragonbane: la scheda e' il riquadro piccolo — `Ferocia: 3  Taglia: Enorme`,
`Movimento: 24  Armatura: 6  PF: 84`, poi i tratti descrittivi — e tutto il resto
della pagina, `ATTACCHI MOSTRUOSI` e `ANIMALI COMUNI`, e' tabella. «Puo' anche
essere di etichette ordinate, ma se la tabella lo risolve non preoccupiamocene
troppo: deve essere leggibile.»

**Perche' le combinazioni e non le etichette sparse.** `repeated_structures`
impara un *insieme* di etichette, e su Dragonbane quell'insieme contiene
`movimento` — che e' anche una colonna di `ANIMALI COMUNI` — e `artigli!`, che e'
una **riga** della tabella degli attacchi. Basta una di quelle a far scattare la
scheda dentro una tabella. Misurato sui tre manuali, il 19 settembre:

| combinazione su una riga sola | volte | dove |
| --- | ---: | --- |
| `ferocia + taglia` | 13 | le 13 creature di Dragonbane |
| `movimento + armatura + pf` | 12 | le stesse |
| `movimento + pf` | 4 | le creature evocate, pagine 67-69 |
| `difficolta + soglie + pf + stress` | 149 | le schede avversario di Daggerheart |
| nessuna | 0 | **Apocalisse**, che infatti non ha schede |

Le tabelle non producono queste righe: l'intestazione di `ANIMALI COMUNI` ha le
celle tutte dello stesso stile, quindi non forma coppie etichetta/valore, e le
righe di `COMPLICAZIONI` su Apocalisse portano un valore per cella.

**Il minimo di tre ripetizioni non e' nuovo**: e' quello che `repeated_structures`
chiede gia' a una struttura per esistere, e qui si applica alla combinazione
invece che all'insieme.

**Emendamento del 20 settembre 2026**, `Criterio_PosizioneRelativaDeiCampi_v1.md`.
Il contenimento da solo non bastava, e l'indicazione dell'utente lo diceva gia':
«non basta che ci siano, devono essere nella stessa posizione relativa». Su DB
la combinazione `{tiraund6.1, 2, 3, 4, 5}` — i numeri delle opzioni di un D6
dentro le celle della tabella dei tesori — si ripeteva cinque volte e faceva
uscire sette righe dalla tabella. Ora una combinazione entra solo se un solo
**profilo di posizioni** copre la maggioranza delle sue occorrenze:

| combinazione | occorrenze | profilo dominante |
| --- | ---: | ---: |
| `movimento + pf` | 16 | 10 |
| `ferocia + taglia` | 13 | 10 |
| `movimento + armatura + pf` | 12 | 10 |
| `tiraund6.1 + 2 + 3 + 4 + 5` | 5 | **1** |
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from stat_block_regions import LineFacts

MINIMO_RIPETIZIONI = 3


def recurring_field_combinations(
    pages: Mapping[int, Sequence[LineFacts]], *, minimo: int = MINIMO_RIPETIZIONI
) -> frozenset[frozenset[str]]:
    """Le combinazioni di etichette che stanno **sulla stessa riga** e si ripetono.

    Una riga con una sola etichetta non fa combinazione: una parola in grassetto
    non e' una scheda. Si contano le combinazioni intere, non i loro pezzi, e si
    tengono quelle che il documento ripete almeno ``minimo`` volte.
    """

    quante: Counter[frozenset[str]] = Counter()
    profili: dict[frozenset[str], Counter[tuple[tuple[str, int], ...]]] = {}
    for facts in pages.values():
        for line in facts:
            etichette = frozenset(line.labels)
            if len(etichette) < 2:
                continue
            quante[etichette] += 1
            profili.setdefault(etichette, Counter())[_profilo(line, etichette)] += 1
    return frozenset(
        combinazione
        for combinazione, n in quante.items()
        if n >= minimo and _sta_sempre_nello_stesso_posto(profili[combinazione], n)
    )


def _profilo(line: LineFacts, combinazione: frozenset[str]) -> tuple[tuple[str, int], ...]:
    """Dove stanno le etichette sulla riga, in larghezze di carattere.

    Lo scostamento dal bordo sinistro della riga diviso per la larghezza media di
    un carattere dell'etichetta: un numero adimensionale, che non cambia se il
    manuale e' composto a un corpo diverso."""

    if line.bbox is None:
        return ()
    x0 = line.bbox[0]
    return tuple(
        (etichetta, round((inizio - x0) / larghezza))
        for etichetta, (inizio, larghezza) in zip(line.labels, line.label_starts, strict=True)
        if etichetta in combinazione and larghezza > 0
    )


def _sta_sempre_nello_stesso_posto(
    profili: Counter[tuple[tuple[str, int], ...]], occorrenze: int
) -> bool:
    """Un solo profilo copre la maggioranza delle occorrenze.

    `Criterio_PosizioneRelativaDeiCampi_v1.md`: «non basta che ci siano, devono
    essere nella stessa posizione relativa». Su DB i tre insiemi di campi veri
    hanno un profilo dominante che copre 10 occorrenze su 16, 13 e 12; i numeri
    delle opzioni di un D6 dentro le celle dei tesori hanno cinque profili
    distinti su cinque occorrenze, e il piu' frequente ne copre una.

    «La maggioranza» non e' una soglia nuova: e' la forma che
    `_bound_label_groups` usa gia' per legare due etichette."""

    if not profili:
        return False
    return max(profili.values()) * 2 > occorrenze


def field_line_indices(
    facts: Sequence[LineFacts], combinations: frozenset[frozenset[str]]
) -> tuple[int, ...]:
    """Le righe della pagina che portano una delle combinazioni.

    Contenimento e non uguaglianza: una riga che porta la combinazione **piu**'
    un'altra etichetta resta una riga di campi. Il contrario -- accettare un pezzo
    della combinazione -- e' esattamente cio' che fa entrare `movimento` da solo.
    """

    if not combinations:
        return ()
    trovate = []
    for index, line in enumerate(facts):
        etichette = frozenset(line.labels)
        if len(etichette) >= 2 and any(c <= etichette for c in combinations):
            trovate.append(index)
    return tuple(trovate)


def field_line_groups(
    facts: Sequence[LineFacts], indices: Sequence[int]
) -> list[tuple[int, ...]]:
    """Le righe di campi raggruppate per scheda: righe consecutive nell'ordine di
    lettura stanno nella stessa scheda, un salto le separa.

    «Consecutive» e' nell'ordine di lettura del chiamante, non nella geometria:
    due righe di campi separate da una riga di prosa sono la stessa scheda --
    `Ferocia` e `Movimento` hanno in mezzo il nome del tratto -- mentre due schede
    diverse hanno fra loro molte righe.
    """

    gruppi: list[list[int]] = []
    for index in indices:
        if gruppi and index - gruppi[-1][-1] <= 2:
            gruppi[-1].append(index)
        else:
            gruppi.append([index])
    return [tuple(gruppo) for gruppo in gruppi]


def opens_a_record(line: LineFacts) -> bool:
    """La riga comincia con un'etichetta, quindi apre un record della scheda.

    `Criterio_RigheDellaSchedaACapo_v1.md` §2. «Comincia con» e' scostamento zero
    dal bordo sinistro della riga, nella stessa unita' dei profili: larghezze di
    carattere dell'etichetta. Dentro una scheda le righe stanno tutte nello
    stesso blocco della sorgente, e senza questo segnale `breaks_paragraph` le
    salda: la riga `ATT: ...` finisce in coda a `Difficolta': ...`, e
    l'intestazione della seconda caratteristica in coda al testo della prima.

    Le righe che continuano un valore andato a capo non aprono nulla: non hanno
    etichetta in testa, e restano attaccate alla riga di sopra."""

    if not line.labels or not line.label_starts or line.bbox is None:
        return False
    # Sulla riga ci dev'essere un'etichetta che si DICHIARA tale, cioe' che
    # finisce con i due punti: `field_labels` rileva alternanze di stile, e
    # senza questo una riga di continuazione con dentro una parola in grassetto
    # — `l'ha evocata, usando i **PV** del suo creatore.` — apriva un record e
    # tagliava la frase in due. `Criterio_RigheDellaSchedaACapo_v1.md` §5.
    #
    # Non basta guardare la PRIMA etichetta: un intoppo di font spezza
    # `Canto Incantatore - Azione:` in `Canto ` + `Incantato` + `re - Azione:`,
    # e i due punti finiscono nel terzo pezzo. Guardare solo il primo span
    # sarebbe guardare la segmentazione, non il campo.
    if not any(line.label_declares):
        return False
    inizio, larghezza = line.label_starts[0]
    if larghezza <= 0:
        return False
    return round((inizio - line.bbox[0]) / larghezza) == 0
