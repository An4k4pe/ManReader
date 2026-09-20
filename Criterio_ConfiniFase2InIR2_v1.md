# Criterio — i confini ammessi dalla Fase 2 nelle tabelle di IR 2

Dichiarato l'11 settembre 2026, **prima** della misura che decide.

## 0. Che cosa collega, e perché non si collega com'è

La Fase 2 della Milestone 43 (`resolution_column_boundaries.py`, portata qui con
`a4e5090`) dice quali corridoi respinti da `column_band` valgono comunque come
confine di colonna: quelli respinti **solo** per mancanza di parole ai fianchi,
**coperti** da un `table_candidate`, con testo su **entrambi** i fianchi. Oggi
nessun consumer la legge.

Il consumer naturale è la tabella di IR 2 (`--tabelle`), che legge già **per
righe**: è la condizione che il docstring della Fase 2 pone perché consumarla non
peggiori le tabelle.

**Ma collegata così com'è fa danno.** `column_bounds` applica un corridoio a tutta
la regione, in x soltanto, e un confine ammesso non è alto quanto la sua tabella.
Misurati sui tre manuali interi, i confini ammessi che cadono dentro una regione:

| manuale | ammessi | alti almeno metà tabella | più bassi |
| --- | ---: | ---: | ---: |
| DB  | 31 | 15 | 16 |
| Apo | 22 |  1 | 21 |
| Dag | 17 |  8 |  9 |

Un confine basso vale su una **striscia** della regione. Dag p115 (idx 116) ne ha
uno alto 56 pt su una regione di 518: sopra c'è una tabella d'esempio di due
righe, sotto la prosa che la spiega. Applicato a tutta la regione **farebbe
uscire dalla tabella 28 righe di prosa** — i residui passano da 2 a 30 — perché
`_column_of` fa di una riga che scavalca un confine un residuo, e il paragrafo
esce spezzato fra righe rimaste in cella e righe uscite.

## 1. La regola

> Il chiamante passa a ogni regione tabella i confini ammessi che la coprono, con
> la stessa relazione di `_covered_by_a_table`: contenuti in x, sovrapposti in y.
>
> `build_table` ne aggiunge uno ai confini della regione **solo se nessuna riga
> che la tabella teneva ne esce**: se, con il confine, le righe collocate in una
> colonna restano quante erano. I confini si provano in ordine di x, ciascuno
> contro quelli già accettati.

**Perché questa e non una quota d'altezza.** «Almeno metà tabella» è la lente con
cui ho guardato, non una regola: sarebbe una soglia, e non dice che cosa il
confine fa alle righe. La regola sopra non ne ha: una riga scavalca il confine o
no, ed è la regola che il consumer applica **già** a una riga che scavalca un
corridoio. Un confine che vale su una striscia passa lo stesso **se** fuori dalla
striscia nessuna riga lo attraversa — e allora non toglie niente a nessuno.

**Che cosa può fare, per costruzione**: dividere una colonna in due, oppure far
diventare tabella a due colonne una regione che oggi ne ha una sola e quindi
tabella non è. **Non può** far uscire una riga dalla tabella, né farcene entrare
una.

**Senza `--tabelle` non cambia niente**: i corridoi respinti si calcolano solo
quando le tabelle sono accese.

## 2. Il campione e l'esplorazione

**Esplorazione dichiarata.** Ho scelto la regola dopo aver guardato Dag p115,
p131 e p132 (idx 116, 132, 133), e ho provato il cancello su nove pagine: Dag
p22/p115/p310, Apo p47/p107/p111, DB p24/p29/p120. Respinge i confini che
toglierebbero righe su sette e ne ammette su due, più Dag p131/p132. **Non ho
guardato l'uscita** né il markdown di nessuna: è ciò che il §3 decide.

**Popolazione**: DB, Apo e Dag **interi**, con `--tabelle`, prima (`a4e5090`) e
dopo. Sono i tre manuali su cui la Fase 2 ha confini ammessi misurati. Si giudica
**ogni** tabella il cui markdown cambia, senza campionare: i confini in gioco
sono al più 70, su 53 pagine.

## 3. Pass/fail

### A. Barra

- Test verdi, ruff pulito.
- `scripts/check_eb.py --pdf-dir .`: 9 su 10, e l'unica diversa è Fab idx 126,
  già a verbale. Senza `--tabelle` è identica per costruzione, e va misurata lo
  stesso.

### B. Per costruzione: nessuna riga esce

Ogni tabella che esisteva prima possiede **le stesse primitive** dopo — divise
fra più celle, ma le stesse. Una sola tabella in cui l'insieme cambia è un
difetto d'implementazione, e ferma tutto prima del giudizio.

### C. Il giudizio, pagina per pagina

Ogni tabella cambiata si guarda sull'immagine della pagina:

- **meglio** — la colonna nuova è una colonna che la pagina stampa (Dag p132:
  `TIRO` staccato da `BOTTINO`);
- **peggio** — taglia in due ciò che la pagina stampa come **una** colonna,
  oppure fa tabella di una regione che la pagina **non** stampa come tabella;
- **neutro** — il resto: una colonna vera su una tabella che era rotta e resta
  rotta allo stesso modo, per esempio.

**Passa se meglio > peggio, e se nessuna tabella nuova — una regione che prima
tabella non era — cade su qualcosa che la pagina non stampa come tabella.** La
seconda condizione è il veto: fare tabella della prosa è l'errore per cui la
Milestone 39 è caduta, e non si compensa con colonne divise bene altrove.

Giudico io, sulle immagini, e consegno l'elenco delle pagine con l'indice **e** il
numero stampato perché l'utente possa controllare: finché nessun altro guarda le
pagine, una misura che conferma chi l'ha progettata non è verificata.

## 4. Che cosa NON dice

- Non dice che le tabelle di IR 2 siano buone: il criterio della Milestone 39
  resta caduto, e `--tabelle` resta spento di default.
- **Non ripara il difetto più grosso che l'esplorazione ha mostrato**: nella
  regione entrano i corridoi **ammessi** di **altre** bande, perché
  `gutter_x_intervals` è la somma dei corridoi di tutta la pagina. Su Dag p131 il
  corridoio 310-324 viene dalla prosa a due colonne **sopra** la tabella, taglia
  la colonna `DESCRIZIONE` e ne fa uscire 30 righe. È lo stesso difetto — un
  confine applicato fuori dalla sua altezza — ma su un meccanismo già collegato,
  e non si mescola con questo.
- Non ripara la scelta della regione (Milestone 39, punto aperto 4) né i
  corridoi `too_short` delle tabelle piccole.
