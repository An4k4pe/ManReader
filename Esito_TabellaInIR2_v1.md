# Esito di `Criterio_TabellaInIR2_v1.md` — **il giro si ferma**

L'errore squalificante è scattato, sull'unica pagina in cui il meccanismo ha
prodotto qualcosa. Il criterio ha fatto esattamente ciò per cui era stato scritto.

---

## 1. L'errore squalificante — **1 pagina su 12**

Il §3 chiedeva che l'elenco dei paragrafi, esclusi i nodi tabella, fosse una
**sottosequenza esatta** del baseline salvato prima.

Undici pagine su dodici passano. **Wil p.245 no**, e il paragrafo che non esiste
nel baseline è la **fusione di due che ci sono**:

```
baseline:  «… FURTO per rubare il suo STRUMENTO … Lo STRUMENTO»
baseline:  «30 mantiene Portata e Resistenza migliorate grazie alle Tecniche …»
nuovo:     «… Lo STRUMENTO mantiene Portata e Resistenza migliorate …»
```

Fra i due c'era un `30` — un numero incolonnato — che è finito in una cella.
Toglierlo ha reso **adiacenti due righe che prima non lo erano**, e
`breaks_paragraph` le ha unite.

**È il difetto per cui il criterio esisteva**, previsto nel §4.1 della proposta e
invisibile a tutto il resto: il validatore vede gli id coperti, il round-trip
passa, la suite è verde.

**Il §5 del criterio: una sola regressione fuori dalla tabella ferma il giro.**
Si ferma.

## 2. Una cosa scomoda, che non uso per salvare l'esito

Su questa istanza la fusione produce testo **migliore**: `Lo STRUMENTO mantiene
Portata` è la frase giusta, e il `30` era un intruso.

**Non rileggo il criterio alla luce del risultato.** Era pre-registrato proprio
per questa classe di difetto, e decidere adesso che «questo caso però va bene» è
la lettura post-hoc che `AGENTS.MD` §15 vieta. Se il criterio va emendato, va
emendato da chi decide e **prima** del prossimo giro, non dopo aver visto quale
verdetto conviene.

## 3. I due conteggi, riportati come il §4 chiede

**1 tabella costruita su 7 regioni candidate**, sulle 12 pagine del campione:

| pagina | tabelle / regioni |
| --- | --- |
| Wil p.245 | **1 / 1** |
| Lan p.245 | 0 / 2 |
| DrW p.4, Fab p.176, DIE p.3, SV p.351 | 0 / 1 ciascuna |
| DIE p.51, Kul p.35, DIE p.290, Wil p.200, FW p.223, FW p.45 | 0 / 0 |

Le etichette dell'utente non sono state date, quindi il conteggio «quante
etichettate tabella escono come tabella» **non è calcolabile** e non lo si
inventa.

## 4. Perché quasi nessuna tabella: l'ipotesi del §3.1 non regge come sperato

`column_bounds` chiede almeno due colonne, cioè almeno un gutter **dentro** la
regione. Su DB p.90 `column_band` emette un gutter solo, `x300-331`, che è la
divisione principale della pagina: le due regioni tabella stanno a `x346-531` e
`x62-249`, **entrambe fuori**. Nessuna colonna, nessuna tabella.

Dove i gutter cadono dentro, funziona: **DB p.76** — la pagina che `State.md:122`
cita per i sette gutter annidati, «la descrizione corretta di una tabella a nove
colonne» — produce la sua tabella.

Quindi l'ipotesi **non è falsificata, è parziale**: i gutter descrivono le colonne
di una tabella *quando `column_band` li trova dentro la regione*, e su queste
pagine succede raramente. Era dichiarata non misurata nel §3.1 della proposta, con
il controesempio già a verbale (`State.md:128`, «accetta una colonna di tabella e
ne rifiuta le sorelle»).

## 5. Stato del codice

**Implementato, testato, e a default spento.** `--tables` lo accende; senza, il
comportamento è identico a prima — verificato: 11 pagine su 12 hanno lo stesso
elenco di paragrafi, e la dodicesima differisce solo con il flag acceso.

Contratto: `NodeIR2.structure`, `TableIR2`, `CellIR2`, con `text=""` ora vietato e
l'invariante a tre braccia. Serializzazione con `kind` discriminante dell'unione.
Validatore esteso: l'unione delle celle deve coincidere con le primitive del nodo.
Emettitore: tabella Markdown con la prima riga come intestazione, **scelta di resa
dichiarata** perché IR 2 non dice quale riga sia un'intestazione.

Suite 1369 (+21), ruff verde, basedpyright 0/0/0. Resta il fallimento
pre-esistente e ambientale.

## 6. Cosa serve prima di riaprire

1. **Una decisione sul criterio**: se la fusione di due paragrafi debba far
   fallire sempre, o solo quando peggiora il testo. La seconda richiede un
   giudizio umano dentro un controllo automatico, e va progettata.
2. **Il difetto della fusione va chiuso comunque**, indipendentemente dalle
   tabelle: estrarre primitive dal flusso rende adiacenti righe che non lo erano,
   e succederà a ogni meccanismo che sottragga testo — l'arredo per primo.
3. **I gutter dentro le regioni** sono pochi. Se le tabelle contano, i confini di
   colonna vanno cercati anche altrove — e quella è la domanda che i due criteri
   caduti sulla discriminazione avevano lasciato aperta.
