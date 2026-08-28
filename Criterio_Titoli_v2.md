# Criterio — i titoli, v2. Non «sopra il corpo» ma **sopra tutta la prosa**

## 0. Che cosa cade della v1, e sono due cose mie

**La diagnosi del §3 era sbagliata.** Scrivevo che sui manuali densi di schede la
regola sovraproduce «perché dentro una scheda le convenzioni tipografiche della
prosa non valgono», e la storia tornava — era la terza volta che le schede mostro
comparivano. Guardando i candidati uno per uno **non è vero**: su DrW sono
`1st-Level Tradition Features`, `Perfect Clarity (5 Clarity)`, `Accelerate`, cioè
nomi di sezione e di talento; su Wil sono `Guardabosco`, `SENTIERI E COMUNITÀ`.
Sono titoli, o molto vicini. Avevo generalizzato da tre numeri alti a una
spiegazione che si accordava con i giri precedenti.

**Il concetto di «corpo» era sbagliato.** La v1 assumeva **una** dimensione di
corpo per documento. Misurato, non è così:

| manuale | idx | pagina stampata | |
| --- | ---: | --- | --- |
| **Apo** | **76** | **73** | il flusso a 10,6 è il **95% della pagina** |
| Apo | 69 | 66 | 75% a 10,6 |
| Apo | 75 | 72 | 65% a 10,6 |
| Kul | 119, 121, 123 | 119, 121, 123 | 11-14% a 10,0, mescolato al corpo 8,0 |
| Wil | 158 | — | 81% a 9,0 |

Su Apo idx 76 la dimensione che il documento dichiara «corpo» (11,6) quasi non
compare. **Ci sono due o tre flussi di prosa**, non uno — indicazione dell'utente,
e la misura la conferma.

**E una variante che ho provato e che non funziona**, tenuta a verbale perché
nessuno la riproponga: «un titolo è più corto della mediana delle righe di corpo».
Su Wil la mediana è 116 caratteri e non filtra nulla; su **Kul è 1** e filtra
tutto, 88 candidati a zero, titoli veri compresi. Il perché: su Kul l'**82%**
delle righe alla dimensione del corpo è un singolo `.`, i puntini decorativi già
incontrati scrivendo `Criterio_Elenchi_v2.md`.

## 1. La regola

### La misura: quali dimensioni sono **prosa**

> Per ogni dimensione del carattere si misura la **lunghezza mediana** delle sue
> righe, contando solo le righe che portano almeno una lettera o cifra.
>
> Le mediane si ordinano. Il **salto più grande** fra due mediane consecutive
> separa le dimensioni **corte** da quelle **lunghe**: le lunghe sono la
> **prosa**.

**Nessun numero scelto.** Il salto più grande è una proprietà della
distribuzione, non una soglia: le mediane si dispongono in due gruppi da sole.
Misurato su DB:

```
dim 10.0 → 612 righe, mediana 55 car   prosa
dim  9.0 →  86 righe, mediana 45 car   prosa
                    ← il salto
dim 11.5 →  43 righe, mediana 10 car   corta
dim 34.0 →   8 righe, mediana 14 car   corta
```

### La politica: che cos'è un titolo

> Una riga sorgente è un **titolo** se:
>
> 1. la sua dimensione è **maggiore della più grande dimensione di prosa**;
> 2. il suo blocco non contiene righe di **nessuna** dimensione di prosa;
> 3. il suo blocco ha **al più due** righe non vuote;
> 4. il suo testo è più lungo di **un carattere**;
> 5. non è già escluso dal corpo come **arredo**.
>
> Il **livello** è il rango della sua dimensione fra quelle sopra la prosa, dalla
> più grande: `#`, `##`, `###`… fino a `######`.

La **1** e la **2** sono la correzione della v1: dove c'erano «il corpo» ora c'è
**l'insieme delle dimensioni di prosa**. È ciò che chiude Kul, dove 8,0 e 10,0
sono **entrambe** prosa e le 67 righe a 10,0 smettono di essere titoli.

Le altre tre restano della v1, con i loro fatti: la **2** viene da Apo, dove il
blocco del titolo contiene anche la testatina; la **3** è «un titolo è un blocco
suo, al più con un a capo»; la **4** sono i capilettera di Fab (`3`, `n`, `W` a
corpo 30); la **5** i numeri di pagina, che in molti manuali sono più grandi della
prosa.

### Che cosa la correzione cambia, misurato

| manuale | prosa riconosciuta | v1 | **v2** |
| --- | --- | ---: | ---: |
| **Kul** | 8,0 **e** 10,0 | 88 | **21** |
| **DrW** | 7,5 e 12,0 | 58 | **31** |
| **SV** | 9,9-11,9 | 36 | **12** |
| Apo | 10,6 e 11,6 | 3 | 3 |
| DB | 9,0 e 10,0 | 36 | 36 |
| DrM | 7,5 | 53 | 53 |
| Wil | 9,8 e 10,0 | 63 | 63 |
| gli altri nove | | | invariati |

Corregge i tre manuali rotti e **non tocca gli altri tredici**. È la firma di una
regola che ha trovato la causa e non un filtro che taglia a caso.

## 2. Che cosa NON entra nella regola

**Le maiuscole**, ed è il §0 della v1 che resta valido:
`markdown_builder._is_heading_text` «promuove a titolo qualunque testo corto in
maiuscolo **prima ancora di guardare lo stile**», e su DB p.99 ha promosso una
testatina corrente. Qui lo stile si guarda per primo.

**Il grassetto**, che si rende già come grassetto. **Il font**: misurato, su
alcuni manuali il titolo è nello stesso font della prosa.

## 3. Il campione

**16 righe promosse** e **16 righe scartate che stanno sopra la prosa**, seed
**`20260926`** dichiarato qui, da tutti i manuali che ne producono, **dopo**
l'esclusione dell'arredo, con il materiale costruito **dalla resa**.

Le due metà servono a cose diverse, e il giro precedente ha mostrato che serve la
seconda: `Esito_ElencoNumerato_v1.md` ha trovato **tutti e sette** gli errori
nella lista delle scartate, che un campione delle sole promosse non avrebbe
mostrato.

## 4. Pass/fail

### A. Veto — cade a una sola riga, in entrambe le direzioni

> Cade se **una sola** riga promossa non è un titolo, o se **una sola** riga
> scartata lo era.

Etichette: **titolo**, **non titolo**, **incerto**. Seed di controllo
**`20260927`**.

> **Rinforzo del protocollo**: una riserva scritta accanto a un'etichetta netta
> **viene contata come `incerto`**. Tre giri di fila la riserva è finita in prosa
> — arredo, elenchi, numerati — e ogni volta erano proprio le voci che decidevano.

### B. La dispersione per manuale

> Si riporta il numero di titoli **per manuale**, e il verdetto cita i manuali
> con i numeri estremi.

Obbligo di riporto, non barra: una media che desse «regge» mentre un manuale
produce dieci volte i titoli di un altro sarebbe un verbale falso.

### C. La giunzione

> Per ogni titolo prodotto si guarda il paragrafo sopra e sotto.

Bersaglio preciso: un titolo promosso **in mezzo a un paragrafo** lo spezzerebbe
in due, ed è il danno peggiore di questo meccanismo.

### D. Regressione

> `check_list_regression.py` e `check_numbered_lists.py` danno lo stesso
> risultato di prima.

### Se cade

- **A** verso «promossa e non lo era»: la regola è troppo larga, e non si stringe
  a occhio nello stesso giro.
- **A** verso «scartata e lo era»: si riporta quanto manca.
- **B** con numeri estremi: si nomina il manuale e si guarda **cosa** produce,
  invece di attribuirlo a una categoria come ha fatto la v1.

## 5. Che cosa resta fuori

- **La gerarchia**: i livelli vengono dal rango delle dimensioni, non da un
  albero. Un `###` dopo un `#` senza `##` è possibile e non si corregge.
- **I titoli di sezione numerati** di `Esito_ElencoNumerato_v1.md` §3: se questo
  criterio regge, quelle sette righe diventano titoli e la copertura del numerato
  si chiude da sé. **Non è una barra di questo criterio**, perché misurerebbe due
  cose insieme.
- **Le schede mostro come categoria**, che restano il debito più vecchio — ma
  **non** sono la causa di questo difetto, e la v1 sbagliava a dirlo.

## 6. Debiti

`scripts/measure_heading_candidates.py` va aggiornato alla regola di questo
criterio nello stesso commit.
