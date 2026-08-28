# Criterio — il marcatore d'elenco può essere una **lettera in un font di simboli**

**Scritto prima di implementarlo.**

## 0. Che cosa deve chiudere

Su Fab gli elenchi non vengono riconosciuti affatto, e `list_markers` torna
**vuoto**. Rilievo dell'utente sulle pagine rese: «gli elenchi non sono
riconosciuti, come mai?».

La causa è la condizione 1 di `Criterio_Elenchi_v2.md` §1 — **non alfanumerico** —
e su Fab il punto elenco è la lettera **`w`**:

```
font del corpo di Fab: PTSans-Narrow
   'w'  font=Wingdings-Regular        10 righe   DIVERSO dal corpo
   'W'  font=BodoniOrnamentsITCTT      9 righe   DIVERSO dal corpo
```

`w` in Wingdings **è** un pallino. La regola non può vederlo per costruzione.

**Il font era stato escluso di proposito** dal criterio degli elenchi: «misurato,
su alcuni manuali il marcatore è nello stesso font del corpo» — vero per FWK e
Dag, dove `*` e `•` stanno nel font del testo. Ma come **seconda via** non toglie
niente a quei casi.

## 1. La regola

> Un carattere è **candidato** marcatore se è **non alfanumerico**, **oppure** se
> è alfanumerico e la sua primitiva sta in un **font diverso da quello del
> corpo**.
>
> Tutto il resto di `Criterio_Elenchi_v2.md` §1 resta invariato: non appaiato,
> maggioranza a inizio riga, testo che segue, almeno due pagine.

Il font del corpo è quello di `ir2_builder.body_font`, pesato per **caratteri**.

## 2. Il rischio, misurato prima di correrlo

La via del font apre anche cose che elenchi non sono:

| manuale | apre in più |
| --- | --- |
| **Fab** | `w`×20 — **il pallino** |
| DrM | `M`×190, `I`×70, `R`×59, `P`×31 — le **abbreviazioni di caratteristica** |
| DrW | `x`×65, `á`×41, `í`×41, `é`×40 — **icone** di scheda |

> **Ma ciò che viene dopo le filtra da solo**, ed è il risultato che rende questo
> criterio piccolo invece che rischioso. Misurato, applicando la regola delle
> corse e la firma di scala:
>
> | manuale | voci d'elenco prodotte |
> | --- | ---: |
> | **Fab** | **18** |
> | **DrM** | **0** |
> | **DrW** | **0** |

Su DrM le firme di blocco sono `(M, R)`, `(M, R, I)`, `(M, R, I, P)` — caratteri
**distinti, ciascuno una volta, ricorrenti**: è esattamente la definizione di
**scala di valori** di `Criterio_ScalaDiValori_v1.md`, scritta per i badge di
tier, che qui coglie anche le abbreviazioni di caratteristica senza essere stata
progettata per farlo.

**Questo è il motivo per cui la via del font è sicura**, e va scritto: non perché
sia precisa, ma perché i due meccanismi a valle sono già quelli giusti.

## 3. Il campione

**Tutte** le voci che la via del font aggiunge — sono 18 su un manuale solo, e
guardarle per intero costa meno che difendere un campione. Seed non serve: non c'è
sorteggio.

Più, **d'ufficio**, una verifica su DrM e DrW che le voci aggiunte siano **zero**:
è la barra che tiene onesto il §2.

## 4. Pass/fail

### A. Veto — cade a una sola voce

> Cade se **una sola** delle voci aggiunte non è una voce d'elenco, o se il
> carattere tolto portava significato.

Etichette **elenco** / **non elenco** / **incerto**. Vale il rinforzo: una riserva
accanto a un'etichetta netta conta come `incerto`.

### B. Le zero su DrM e DrW

> Le voci d'elenco prodotte su DrM e DrW dalla via del font devono restare
> **zero**. Se cambiano, la protezione su cui questo criterio si appoggia non è
> quella che credo.

### C. Regressione

> `check_list_regression.py` e `check_numbered_lists.py` invariati, e i marcatori
> trovati sugli altri quattordici manuali invariati.

La via del font è **additiva**: se toglie o cambia un marcatore già trovato, non è
additiva e va ritirata.

### Se cade

- **A**: si riporta quale voce, e non si aggiungono condizioni nello stesso giro.
- **B**: la via del font si ritira, perché il §2 poggia interamente su quella
  misura.

## 5. Che cosa resta fuori

- **`W` in `BodoniOrnamentsITCTT`** su Fab, 9 righe: è un ornamento, e se la
  regola lo prende sarà il veto a dirlo.
- **I capilettera**, già esclusi dalla condizione «più di un carattere».
- **Le schede mostro come categoria**, che qui non serve aprire perché i
  meccanismi esistenti bastano.
