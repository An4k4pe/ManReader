# Esito di `Criterio_Titoli_v3.md` — **due falsi positivi veri, e metà giudizio invalido**

**Stato in una riga**: il veto §4.A **cade** su due righe promosse che titoli non
sono — verificate sulla resa vera. L'altra metà del giudizio, le 16 righe
scartate, **non è valida**: il mio campione le ha classificate con una regola
diversa da quella della pipeline.

---

## 1. Il verdetto e la sua metà buona

32 righe, seed `20261003`, DrM e DrW esclusi dalla popolazione come il §3
dichiarava prima del sorteggio. 412 righe candidate su 14 manuali.

L'etichettatore: **25 titolo, 7 non titolo, 0 incerto**.

### I due falsi positivi, confermati sulla resa

| riga | manuale | esce come | che cos'è |
| --- | --- | --- | --- |
| 13 | BoB | `### **penalità missione:**` | **etichetta di colonna** dentro un riquadro dati, ripetuta quattro volte in pagina |
| 19 | Kul | `### 121` | **numero di pagina** |

Entrambi verificati facendo girare la pipeline, non dedotti dal campione.

> **Il veto è a zero e cade.** Due righe promosse su sedici non sono titoli.

**Il secondo è istruttivo**: `121` è arredo che nessun ramo ha tolto, e il
criterio dei titoli aveva la condizione 4 — «non è già escluso come arredo» —
proprio per questo. La condizione c'è; è l'arredo che non l'ha preso, e
`Esito_ArredoPerTesto_v1.md` ha appena ritirato la clausola che avrebbe dovuto
farlo.

## 2. L'altra metà **non vale**, ed è un difetto mio

Sulle 16 righe scartate l'etichettatore ne ha giudicate 11 «titolo». Ma verificando
sulla pipeline, **la pipeline le promuove**:

```
Wil 154   ### Guardabosco
Apo  73   # In cerca del cuore
Lan 218   # HORUS **PEGASUS**
Dag 193   ### PIANIFICARE UN ARCO NARRATIVO
```

**Perché il campione diceva il contrario**: `scripts/sample_heading_lines.py`
chiama `heading_lines` sulle righe **grezze**, mentre il builder chiama prima
`merge_wrapped`. Un titolo che va a capo ha due righe alla sua dimensione nel
blocco, quindi per il campione non era «solo alla sua dimensione» — per la
pipeline sì, perché le due righe sono già state unite.

Su Wil il caso è ancora più chiaro: la riga unita è `Guardabosco Guardabosco`,
cioè la testatina e il titolo. Il sampler le contava due.

> **Delle 11 «mancate», almeno 9 sono artefatti del campione.** Restano candidate
> a mancate vere `Fab 178` e `BiD 164` (`ALLENARSI`), che la pipeline non promuove.

## 3. La quarta volta

È il **quarto giro di fila** in cui il materiale del giudizio è più debole del
giudizio:

1. arredo — le voci mostrate senza il contesto della pagina;
2. elenchi — le voci troncate a fine riga fisica;
3. titoli v2 — il contorno che puntava alla prima occorrenza invece che alla riga;
4. **qui** — il campione classificato con una regola diversa dalla pipeline.

I primi tre erano difetti di **presentazione**: mostravano male una
classificazione giusta. **Questo è peggio**: la classificazione stessa era
diversa, quindi metà del giudizio ha risposto a una domanda che la pipeline non
pone.

**La regola che ne esce, e che va scritta una volta per tutte**: il campione non
deve **ricalcolare** la classificazione. Deve leggerla da dove la pipeline la
scrive — `document_ir2.json`, dove il `kind` del nodo dice già se è un titolo.
Ogni volta che l'ho ricalcolata ho introdotto una differenza.

## 4. Che cosa resta stabilito

- **Due falsi positivi reali** su 16 promosse: un'etichetta di colonna e un numero
  di pagina. Il veto cade.
- **Le 7 «non titolo»** dell'etichettatore si raggruppano in tre famiglie sole:
  etichette di colonna di tabella (3), arredo di pagina (2), un'epigrafe in corpo
  grande (1), un'etichetta dentro una scheda (1). Nessuna sorpresa: sono le classi
  che il criterio §5 già nominava o che l'arredo dovrebbe togliere.
- **La copertura non è misurata** da questo giro, e non va citata.

## 5. Conseguenza

Il criterio **non è scaricato**. Il veto cade, e prima di rifarlo va rifatto il
campione:

1. la classificazione si **legge** da `document_ir2.json`, non si ricalcola;
2. le due famiglie dei falsi positivi — etichette di colonna e arredo non tolto —
   vanno affrontate, e la seconda dipende dal fascicolo dell'arredo.

Non si ritocca la regola dei titoli in questo giro: il §4 lo vieta, e il difetto
di `121` non è nei titoli.

## 6. Verifiche

Suite **1474** test, un solo fallimento, quello ambientale già a verbale.
