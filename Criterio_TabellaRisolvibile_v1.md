# Criterio — «ciò che una strategia a filetti risolve è una tabella»

Registrato **prima** dell'esecuzione, e **non eseguito qui**. Serve a fissare la
formulazione e il campione adesso, perché nessuno possa sceglierli dopo aver
visto un risultato. È il terzo tentativo sul discriminante tabella/scheda: i primi
due sono caduti e sono a verbale.

**Chi ha riaperto**: l'utente. I due criteri precedenti vietavano a Chat A di
cercare una terza formulazione dall'interno del giro, ed è un divieto che vale per
chi rischia di avvitarsi, non per chi decide.

## 1. Da dove viene

Esplorazione dichiarata senza verdetto, su quattro regioni di tre manuali.

Con le impostazioni **del producer** (`vertical_strategy: "text"`,
`horizontal_strategy: "lines"`, Milestone 20) le griglie sono inutilizzabili su
tutte e quattro: le celle tagliano le parole (`['rocia: 2 Taglia:', 'ormale']`,
`['1M Size Immunity', '6 Speed e 5']`) e su Vil affettano perfino la prosa in
sette colonne. Quote di celle piene 53%-83%: **nessuna separazione**.

Con la strategia **di default, basata sui filetti**, la separazione si vede:

| regione | esito |
| --- | --- |
| DB idx 89, righe di `D6 ATTACCO` | 3 tabelle, **100%** celle piene |
| Vil idx 222, striscia `DIFFICOLTÀ` e righe soglia | 4 tabelle, **100%** piene |
| DB idx 89, pannello FANTASMA | 1 tabella, **0%** piene |
| DB idx 98, pannello statistiche | 2 tabelle, **0%** piene |
| DrM idx 86, Devil Legate | **nessuna tabella trovata** |

100% contro 0%, non 75% contro 50% come nei due criteri caduti.

## 2. L'ipotesi da provare

> Una regione che una strategia a filetti risolve **con celle piene** è una
> tabella, e va al consumer di tabelle. Una regione che quella strategia **non
> risolve** — non trovata, o trovata vuota — **dentro una banda**, è una scheda.

## 3. Che cosa si misura

Per ogni regione candidata: `find_tables` con strategia a filetti, e la **quota di
celle non vuote** della griglia estratta.

- **risolta** = griglia trovata **e** ≥ 80% di celle non vuote;
- **non risolta** = nessuna griglia, oppure < 80%.

La soglia all'80% è fissata qui e non dopo: l'esplorazione ha visto 100% e 0%, e
una soglia in mezzo a quel divario non è tarata sul risultato.

## 4. Il campione, e come si assegnano le etichette

**Le pagine non le sceglie Chat A.** 12 pagine estratte uniformemente con
`scripts/sample_ir2_verification_pages.py`, **seed `20260820`**, dal pool dei 16
manuali, escluse per costruzione le pagine già usate qui (DB idx 89, DB idx 98,
DrM idx 86, Vil idx 222) oltre a quelle già nella lista dello script.

**L'etichetta la dà l'utente a vista, sul render, PRIMA di vedere la misura**: per
ogni regione, «tabella» o «scheda» o «nessuna delle due». Invertire l'ordine
renderebbe l'etichetta una lettura post-hoc, che è il difetto che
`AGENTS.MD` §15 vieta.

## 5. Regola di pass/fail

**Regge** se, sulle regioni etichettate, ≥ 90% delle «tabella» risulta risolta
**e** ≥ 90% delle «scheda» risulta non risolta.

**Cade** sotto una qualunque delle due.

Le regioni «nessuna delle due» si riportano e non concorrono.

## 6. Limite dichiarato prima

Se regge, **non** autorizza a scrivere un producer «scheda»: autorizza a dire che
il discriminante esiste. La categoria scheda ha ancora contro l'ispezione visiva
di tre manuali con tre forme che non si somigliano, e quella non è stata
smentita da nulla.

## 7. Nota che vale comunque

`table_candidate` con `text/lines` produce griglie che affettano le parole, anche
sulla prosa. **Non arriva a valle** — il producer emette bbox e `primitive_ids`,
mai le celle — ma è la ragione per cui non può servire da discriminante, ed è un
fatto sulla configurazione scelta in Milestone 20 che prima non era scritto.
