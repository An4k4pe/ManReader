# Criterio — il tetto dalla massa, e il filtro sulla riga

Dichiarato il 3 settembre 2026, **prima** della misura che decide.

## 0. Che cosa ripara

`Esito_Capolettera_v1.md` ha lasciato adottato il solo meccanismo C. Restano due
difetti, e li ha visti l'utente guardando l'uscita di Fab.

**A. Il tetto della prosa non guarda la massa.** `prose_sizes` taglia al salto più
grande fra le **mediane di lunghezza riga**, e su Fab restituisce tre dimensioni
— 9,7, 9,8, 9,9 — che insieme fanno lo **0,54% della massa** e 41 righe su
tredicimila. La dimensione che porta l'**86,56%** del manuale, 10,0 pt con 10772
righe, **non è nella prosa**.

Il tetto finisce così a 10,3, che è il *pavimento* della prosa e non la sua cima,
salvato solo dalla clausola che prende il massimo col corpo. Sopra passano le
**519 righe a 12,0 pt** — `'Questo è il tuo mondo,'` — che sono citazioni
d'apertura, cioè prosa.

**B. Il filtro «righe corte» non guarda mai la riga.** Gate sulla **mediana della
fascia**; la promozione avviene **riga per riga**. Misurato su Fab:

```
h3  12.3-13.0   mediana_fascia=19  rapporto=0.36 (soglia 0.5)   riga più lunga = 628
h3  11.6-12.0   mediana_fascia=18  rapporto=0.34 (soglia 0.5)   riga più lunga = 139
```

Una fascia con mediana 19 caratteri contiene una riga di **628**. Il meccanismo
dichiara «i titoli hanno righe corte» e produce un titolo di 628 caratteri: si
contraddice. È lo stesso vizio del meccanismo A caduto — la regola è applicata a
un'aggregazione, e la decisione si prende su un individuo.

## 1. Le due regole

> **Il tetto dalla massa.** Una dimensione è **prosa** se porta almeno l'**1,8%**
> della massa in caratteri della fascia di corpo. Il tetto è la più grande fra
> queste, oppure la cima della fascia di corpo se è più alta. Sopra il tetto si
> formano le fasce candidate; **al tetto o sotto, niente può essere un titolo.**
>
> **Il filtro sulla riga.** Una riga più lunga della **mediana di riga del corpo**
> non è un titolo, qualunque sia la sua fascia.

**Perché la massa.** Il corpo è la massa del testo corrente. Una dimensione che ne
porta una frazione confrontabile è ancora testo corrente — una citazione, un
occhiello, un blocco in corpo maggiore. Una che ne porta un millesimo è un
titolo, **per costruzione**: i titoli sono rari, ed è ciò che li rende titoli. È
la stessa moneta con cui si trova già il corpo, e non una statistica nuova.

**Perché al rapporto 1,0 e non 0,5.** La **fascia** si giudica sulla tendenza — i
titoli in media sono molto più corti del testo — e il mezzo va bene lì. La
**riga** si giudica sul limite: un titolo può essere lungo, ma non più di una riga
intera di prosa. Su Fab il corpo ha mediana 53 caratteri: al mezzo morirebbero
titoli veri come `TABELLE PER LA CREAZIONE DELL'IDENTITÀ` (38); a 1,0 muoiono la
riga da 628 e quella da 139, e sopravvivono tutte le righe delle tre fasce vere,
la cui più lunga è 31.

**`prose_sizes` non si tocca.** Resta dov'è e continua a servire la scala
tipografica di `document_asset_policy`, che è un'altra domanda con un'altra
risposta giusta. Cambia soltanto che **i titoli smettono di usarlo**.

## 2. I numeri scelti a mano, e la sensibilità **misurata prima**

**1,8%** — la quota della massa del corpo. Misurato su otto manuali, il tetto per
soglia:

| manuale | 1,0% | 1,5% | 1,8% | 2,0% | 2,2% | 2,5% | 3,0% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fab | 12,0 | 12,0 | **12,0** | 12,0 | 12,0 | 10,3 | 10,3 |
| Dag | 12,0 | 12,0 | **12,0** | 12,0 | 11,0 | 9,2 | 9,2 |
| BiD | 14,0 | 9,6 | **9,6** | 9,6 | 9,6 | 9,6 | 9,6 |
| FWK | 13,0 | 13,0 | **13,0** | 13,0 | 13,0 | 13,0 | 13,0 |
| Wil | 10,2 | 10,2 | **10,2** | 10,2 | 10,2 | 10,2 | 10,2 |
| BoB | 10,2 | 10,2 | **10,2** | 10,2 | 10,2 | 10,2 | 10,2 |
| Apo | 12,0 | 12,0 | **12,0** | 12,0 | 12,0 | 12,0 | 12,0 |
| Vil | 12,0 | 12,0 | **12,0** | 12,0 | 12,0 | 12,0 | 12,0 |

**Da 1,5% a 2,0% gli otto manuali danno lo stesso tetto.** Sopra si rompe prima
Dag (2,2%), sotto si rompe BiD (1,0%). 1,8% sta dentro l'altopiano e lontano da
entrambi i bordi; 2,0% sarebbe sul bordo, ed è la ragione per cui non lo scelgo.

**1,0** — il rapporto del filtro sulla riga. Non è scelto: è il valore che rende
l'enunciato «più lungo di una riga di prosa» letterale.

**Il taglio cumulativo è stato provato e scartato**, e va a verbale perché è la
strada che sembrava ovvia: al 98% Fab dà il tetto giusto (12,0) ma BoB salta a
18,0 e FWK a 20,0. Misura la forma della coda, non dove finisce la prosa.

## 3. Il campione, le esclusioni, e che cosa ho già visto

Seed **`20260902`**, mantenuto. Fuori: **DrM** e **DrW**. Dentro e da guardare:
**Kul**.

**Esplorazione dichiarata** (`AGENTS.MD` §16): le tabelle del §0 e del §2 sono
misure fatte prima di questa dichiarazione, ed è il motivo per cui le regole sono
scritte così. **Non ho misurato l'uscita** con le due regole insieme, che è ciò
che i veti decidono.

## 4. Pass/fail

### A. Veto — il tetto. Il bersaglio

> Su Fab le 519 righe a 12,0 pt non devono più essere titoli, **e** le tre fasce
> vere — `83,0-87,5`, `40,0`, `24,9-25,0` — devono restare tutte e tre promosse
> con le loro 103 righe.

Entrambe le metà, perché una regola che pulisce spegnendo tutto non ha pulito.

### B. Veto — la riga. Verificabile a macchina

> Nessuna riga promossa più lunga della mediana di riga del corpo, su nessun
> manuale.

### C. Veto — FWK senza il meccanismo B

> FWK deve produrre titoli col solo tetto dalla massa. Cade se torna a zero.

È la prova che ritirare B è stato giusto e non una perdita mascherata.

### D. Veto — **il giudizio, che nel giro scorso avevo lasciato cadere**

> Cade se **una sola** riga promossa non è un titolo, su un campione sorteggiato
> di righe promosse.

`Esito_Capolettera_v1.md` §4 registra che averlo omesso mi ha fatto dichiarare
buono prima il meccanismo A e poi il B. Torna, e vale per entrambe le regole.

### E. Globale — il punto fisso

> Nessuna riga promossa ha dimensione minore o uguale al tetto, su nessun
> manuale. Non si indebolisce.

### F. Globale — nessuna dimensione con due livelli

### G. Globale — regressione

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A**, **B** o **C**: cade **quella** regola, si riporta, e l'altra si giudica
  lo stesso.
- **D**: cade la regola che ha promosso la riga, e si riporta quale.
- **E**: cade tutto. Il punto fisso non si negozia.
- **G**: si diagnostica prima di decidere.

## 5. Che cosa resta fuori

- **L'asse del font**, debito della v2, non pagato.
- **Le schede mostro**, dichiarate sei volte.
- **Il meccanismo A**, ritirato, con la sua forma corretta scritta nel tag: arredo
  finestra per finestra, aggregato per pagina.
- **Il difetto di copertura di Vil idx 268**, pre-esistente.
