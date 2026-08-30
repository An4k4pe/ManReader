# Criterio — ogni fatto document-level si misura **nel suo ambito**

**Scritto prima di implementarlo.** Chiude un difetto di tubatura che falsa
quasi tutte le misure di questa sessione.

## 0. Il difetto

`document_furniture_slots` misura **sei fatti** — dimensioni di prosa, livelli di
titolo, marcatori d'elenco, firme di scala, slot d'arredo, numeri dedotti — su una
finestra di venti pagine, e la finestra è centrata **sul documento**:

```python
first = max(0, len(document) // 2 - sample // 2)
```

Poi quei fatti governano la resa di una pagina che, quasi sempre, **non è fra
quelle**. Misurato:

```
campione dichiarato di dieci pagine     dentro la finestra:  1 su 10
le pagine che ho scelto io a mano        dentro la finestra:  6 su 6
```

Le pagine che sceglievo io stavano tutte dentro perché le prendevo vicino al
centro, senza saperlo. **È una distorsione di campionamento in quasi tutto ciò che
ho misurato in questa sessione**, e l'ha trovata il giudizio dell'utente su un
campione sorteggiato che non avevo scelto io.

### Che cosa costa, misurato

```
BiD  whitecrown     dim 28,0 su prosa 9,6     finestra sul documento: livello None   sulla pagina: livello 2
Wil  IL BANCHETTO   dim 37,0 su prosa 10,0    finestra sul documento: livello None   sulla pagina: livello 3
```

Un titolo a **37 punti su un corpo di 10**, solo alla sua dimensione nel suo
blocco, non prende livello. Non è un limite di copertura del meccanismo dei
titoli: è che la scala dei ranghi è stata calcolata dove quel titolo non c'era.

Lo stesso difetto lascia `?` al posto del numero di pagina su FWK idx 31 e Wil idx
71 — il numero dedotto esiste solo per le pagine dentro la finestra — e
plausibilmente lascia in corpo parte dell'arredo residuo che il giudizio ha
segnalato su quattro pagine.

## 1. La regola, e perché non è «tutto il documento»

La risposta ovvia — scansionare il documento intero — è **giusta per metà dei
fatti e sbagliata per l'altra metà**, e il codice stesso lo dice:

> `RECURRENCE_SHARE = 0.25` — un testo è arredo se ricorre su **almeno un quarto**
> delle pagine guardate.

Una linguetta di capitolo sta sul 100% di una finestra di venti pagine dentro quel
capitolo, e sul 5% di un libro da quattrocento. Scansionare tutto **spegnerebbe**
l'arredo di capitolo. La finestra non è solo un risparmio: per i fatti che
ricorrono localmente è **l'ambito giusto**, ed era centrata nel posto sbagliato.

> **Ogni fatto si misura nell'ambito di cui è un fatto.**
>
> - **Ambito documento** — dimensioni di prosa, livelli di titolo, marcatori
>   d'elenco, firme di scala. Sono proprietà della tipografia del libro: un corpo
>   è un corpo in tutto il volume, e un rango di dimensione non cambia a pagina
>   180. Si misurano su **tutte le pagine**.
> - **Ambito vicinato** — slot d'arredo, testatine correnti, numeri dedotti. Sono
>   proprietà del *dintorno*: una testatina corrente cambia col capitolo, ed è
>   esattamente ciò che la ricorrenza deve poter vedere. Si misurano su una
>   finestra che **contiene la pagina che si sta rendendo**.
>
> Un fatto document-level che cambia a seconda di quale pagina si rende **non è un
> fatto document-level**: è la definizione che separa i due ambiti, e la si
> applica di conseguenza.

**Una cattura sola.** Le pagine si catturano una volta per il documento intero, e
la finestra del vicinato è una fetta di quella cattura. Costo misurato per
manuale intero: **da 4 a 31 secondi**, contro i 3-30 che una pagina già costa.

## 2. Che cosa questo cambia, e va rimisurato

Cambia gli slot d'arredo di ogni pagina, i livelli dei titoli e i marcatori. **Ogni
numero misurato in questa sessione su una pagina fuori dalla finestra è sospetto**
e va rifatto. Va rifatto in particolare:

- la barra E-B sulle dieci pagine;
- la copertura d'arredo;
- le voci d'elenco per manuale.

## 3. Pass/fail

### A. Le due barre dure delle dieci pagine

> Nessuna pagina può perdere contenuto, e l'arredo non può portare via contenuto.
> Sono le due barre che `Esito_DieciPagineOggi_v1.md` ha visto passare 10 su 10, e
> devono restare passate.

Si verificano con la barra E-B — che vede le perdite — più il canale review, che
elenca ciò che esce dal corpo.

### B. E-B non peggiora

> `scripts/check_eb.py`: almeno **nove pagine identiche su dieci**, zero caratteri
> persi, e ogni differenza nuova spiegata.

### C. La barra di copertura — i due titoli

> `whitecrown` su BiD idx 287 e `IL BANCHETTO` su Wil idx 71 devono prendere un
> livello di titolo.

Sono i due casi per cui la modifica è scritta. Se non li prende non ha fatto il
suo lavoro.

### D. L'arredo non si spegne

> Le voci d'arredo prodotte per manuale non devono **calare**, e in particolare le
> testatine di capitolo devono restare.

È il rischio dichiarato al §1: se l'ambito vicinato fosse tracciato male, la
ricorrenza smetterebbe di vedere l'arredo di capitolo. Si riporta il numero per
manuale, prima e dopo.

### E. Gli elenchi

> `check_list_regression.py` e `check_numbered_lists.py` invariati, e le voci per
> manuale non devono calare.

### Se cade

- **A**: si ritira, immediatamente. Una perdita di contenuto non si negozia.
- **C**: la finestra non era la causa, e la diagnosi del §0 è sbagliata.
- **D**: l'ambito vicinato va ridefinito, non allargato a caso.

## 4. Che cosa resta fuori

**La dimensione della finestra del vicinato.** Resta venti pagine, come oggi: è un
parametro di costo già dichiarato, e cambiarlo nello stesso giro renderebbe
impossibile dire quale delle due cose ha mosso i numeri.

**Il costo nel job vero.** Qui si paga una cattura intera per rendere una pagina,
perché il prototipo rende una pagina alla volta. In una pipeline che le rende
tutte, la cattura si fa una volta e si ammortizza — ed è la ragione per cui
questo è il verso giusto e non un lusso del diagnostico.
