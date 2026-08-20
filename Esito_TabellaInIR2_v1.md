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

## 1-bis. CORREZIONE — avevo diagnosticato senza guardare la pagina

Il §1 qui sopra spiegava la fusione senza aver mai aperto Wil p.245. Rilievo
dell'utente. Guardata, **tre cose di quella spiegazione sono sbagliate**.

**Il `30` non è «un numero incolonnato»**: è il valore di **RESISTENZA** della
parte `ARTIGLI`, in una colonna nera a destra che ne porta quattro — 20, 10, 30,
20 — una per ciascuna PARTE. È una struttura a due colonne vera.

**La fusione non peggiora: ripara.** Nel baseline il `30` sta **dentro la frase**
(«…Lo STRUMENTO» / «30 mantiene Portata…»), perché l'ordine di lettura interlaccia
la colonna di destra nel testo di sinistra. Toglierlo ricompone la frase giusta.

**La tabella costruita è sbagliata per un'altra ragione**, che il §1 non vedeva:
inghiotte regioni non correlate — STILI, ABILITÀ, TRATTI, AGGIUNTIVI e PARTI in
un'unica griglia — e lascia la colonna di mezzo vuota, quindi i valori di
resistenza non sono appaiati alle loro parti. La regione viene da
`table_candidate` con `text/lines`, la configurazione che taglia il 61% degli
span: **il problema è la regione, non solo i gutter**.

Il verdetto del §1 — il criterio è caduto — **resta**. Cambia la spiegazione.

## 1-ter. La misura che conta: ordine o forma?

Su Wil p.245, giudicata dall'utente «terribile» in **entrambe** le versioni, con e
senza tabelle. Due proxy dichiarati, non due misure:

| | |
| --- | --- |
| paragrafi emessi | 55 |
| **forma mancante** — paragrafi di ≤2 parole | **38 (69%)** |
| **ordine sbagliato** — risalite di oltre 30pt fra paragrafi consecutivi | **2 (4%)** |

`STILI`, `POSSENTE`, `RAPIDO`, `0`, `PRECISO`, `ANALISI +3`: sulla pagina sono
**coppie etichetta-valore** e titoli di sezione; in uscita sono paragrafi
scollegati.

**L'ordine è quasi giusto. È la forma che manca**, e il 69% mescola almeno due
forme mancanti: i **titoli di sezione** (`text.heading`, criterio inesistente) e
le **coppie etichetta-valore**.

## 1-quater. Ritiro una mia ritrattazione

Avevo dichiarato **caduto** `text.labelled_entry` — il nodo per la coppia
etichetta-valore — sulla base di **un box su una pagina**, DB p.99, dove le voci
uscivano bene senza. **La ritrattazione era prematura**: `POSSENTE 0` e
`ANALISI +3` sono esattamente quella cosa, e senza una forma che le tenga insieme
escono come otto paragrafi.

## 1-quinquies. Il cambio di inquadramento

Tre criteri pre-registrati hanno cercato come **distinguere** una scheda mostro da
una tabella; due sono caduti e uno non è stato eseguito. La misura sopra dice che
la domanda era sbagliata: **il problema non è distinguerla, è che non esiste una
forma per rappresentarla.**

E una scheda **contiene** una tabella — la colonna `PARTE × RESISTENZA` di Wil
p.245 lo è — quindi trattare scheda e tabella come categorie alternative era
l'impostazione sbagliata fin dall'inizio. Posizione dell'utente, che l'aveva detta
prima e che ho trattato come una preferenza invece che come un'osservazione.

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
