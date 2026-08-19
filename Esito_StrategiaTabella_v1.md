# Esito di `Criterio_StrategiaTabella_v1.md` — **AFFIANCARE**

Prodotto da `scripts/measure_table_strategies.py`, seed `20260821` fissato nel
criterio prima della misura.

## 1. Il verdetto, applicando la regola come è scritta

Il §4 chiedeva, per «cambiare», che una strategia tagliasse meno span **e**
risolvesse almeno quante regioni di `text/lines` **su ≥ 80% delle pagine**.

| pagina | `lines/lines` tagliati/risolte | `text/lines` tagliati/risolte | verdetto |
| --- | --- | --- | --- |
| Apo idx 46 | 0 / 3 | 33 / 0 | lines domina |
| Vil idx 166 | 0 / 5 | 42 / 1 | lines domina |
| DrM idx 267 | 0 / 0 | 94 / 2 | producer meglio |
| FW idx 62 | 0 / 0 | 21 / 1 | producer meglio |
| Fab idx 256 | 0 / 0 | 25 / 1 | producer meglio |

**2 su 5, cioè 40%.** Sotto l'80% per «cambiare», sopra lo zero per «lasciare
sola». Il criterio prevedeva esplicitamente questo esito: **affiancare**.

## 2. Aggregato

| strategia | trovate | risolte | span tagliati |
| --- | --- | --- | --- |
| `lines/lines` | 8 | **8** | **0 / 35 (0%)** |
| `text/lines` (producer) | 7 | 5 | 215 / 353 (**61%**) |
| `lines_strict` | 0 | 0 | — |
| `text/text` | 11 | 1 | 558 / 841 (66%) |

`lines_strict` non trova nulla su nessuna pagina del campione. `text/text` è la
peggiore: trova di più e risolve una regione su undici.

## 3. Il dettaglio che orienta la regola di scelta

Sulle tre pagine dove «il producer è meglio», `lines/lines` **non trova niente**.
Non risolve peggio: **tace**. E dove parla, taglia **zero** span e risolve tutto
ciò che trova.

Suggerisce una regola di selezione — *preferire `lines/lines` dove trova qualcosa,
ricadere su `text/lines` dove non trova nulla* — che però **non è stata provata**
ed è un'ipotesi suggerita dai dati, non un esito. Il §4 dice che la regola di
scelta «va decisa a parte», e vale.

## 4. Limiti, e sono seri

**Il campione utile è 5 pagine, non 12.** Su 12 estratte, 11 hanno almeno una
griglia da *qualche* strategia, ma solo 5 ne hanno una da `lines/lines` o da
`text/lines` — le altre sono viste solo da `text/text`, che è la peggiore. I
denominatori del §5 erano stati fissati per togliere le pagine senza griglia, e
tolgono più di quanto previsto.

Con cinque pagine, «40%» è due su cinque. Il verdetto «affiancare» regge perché è
l'esito centrale fra tre, ma non ha la base per essere citato come misura.

**Il numero che regge meglio** è lo `0/35` contro `215/353`: è una proprietà
osservata su tutte le regioni trovate, non una quota su cinque pagine.

## 5. Cosa questo NON dice

Non dice che `table_candidate` vada modificato. Il §6 del criterio lo dichiarava
prima: modificare un producer wired ha oracoli propri — Milestone 20, Dag p.137,
114/57 primitive — che vanno rieseguiti a parte.

E non dice nulla sulla bontà dell'estrazione di **testo** di pdfplumber, che nel
disegno concordato non viene usata: il testo viene dalla sorgente, da pdfplumber
si prende solo la geometria.
