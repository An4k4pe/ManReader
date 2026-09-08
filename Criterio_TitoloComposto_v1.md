# Criterio — il titolo composto: la sovrastampa e l'unione a corpi diversi

Dichiarato l'8 settembre 2026, **prima** della misura che decide.

## 0. Il difetto, e perché è uno solo

Su Kul l'intera struttura di primo livello è la parola `DELLA`, tre volte. Il
titolo vero della pagina idx 168 è **ORRORI DELLA GNOSI**, e la sorgente lo
compone così:

```
 86.0 pt  x=35.0-192.2  y= 42.8  b0093:l0000  'ORRORI'
 86.0 pt  x=35.0-192.2  y= 42.8  b0093:l0001  'ORRORI'   <- bbox IDENTICA
 95.0 pt  x=35.0-211.3  y=107.0  b0093:l0002  'DELLA'
 95.0 pt  x=35.0-211.3  y=107.0  b0093:l0003  'DELLA'    <- bbox IDENTICA
102.0 pt  x=35.0-192.4  y=178.2  b0093:l0004  'GNOSI'
102.0 pt  x=35.0-192.4  y=178.2  b0093:l0005  'GNOSI'    <- bbox IDENTICA
```

Due cose insieme, **nello stesso blocco**:

1. **ogni parola è disegnata due volte alla stessa identica coordinata** — non
   un'ombra spostata, la stessa riga sopra sé stessa, presumibilmente per
   ispessire il tratto. Da qui `ORRORI ORRORI`, `ANGELI ANGELI CADUTI CADUTI` su
   idx 162, `'Valois Valois'` su Vil, `'◈ villaggio di lala villaggio di lala'`
   su Wil;
2. **le parole hanno corpi crescenti** — 86, 95, 102 — e `merge_wrapped` unisce
   solo a **pari dimensione**, quindi produce tre righe invece di una, a tre
   livelli diversi e in ordine sparso.

**Sono lo stesso oggetto** — un titolo display composto parola per parola, ogni
parola due volte, con corpi diversi per effetto grafico — e per questo stanno in
un criterio solo. Ma i due meccanismi **si dichiarano e si giudicano separati**,
perché sono annidati: fare solo il secondo darebbe
`ORRORI ORRORI DELLA DELLA GNOSI GNOSI`, che è peggio di adesso.

## 1. Meccanismo A — **la sovrastampa**

> Due primitive di testo della **stessa pagina** con **lo stesso testo
> normalizzato, la stessa dimensione e la stessa bbox** sono **la stessa
> impressione**: nel testo della riga il contenuto compare **una volta sola**.

**Non è una soglia: è un'uguaglianza.** Misurato su quattro manuali, le coppie
stesso-testo-stessa-dimensione con bbox **identica** sono **816**, quelle che
differiscono di meno di mezzo punto senza essere identiche sono **5** (3 su Wil,
2 su Kul). Il rapporto è tale che la regola si scrive sull'uguaglianza esatta, e
le 5 restano **fuori e dichiarate**: prenderle richiederebbe una tolleranza
geometrica cablata, che è ciò che il progetto non fa.

**E le primitive non si cancellano.** Questo è il punto su cui il meccanismo può
rompere un invariante senza che nessun test se ne accorga: `AGENTS.MD` §Coverage
vuole che **ogni** `TextPrimitive` sia coperta da un nodo. La deduplicazione
avviene nella **composizione del testo della riga**, non rimuovendo primitive: la
seconda `ORRORI` resta coperta dal nodo, e solo il testo smette di raddoppiarla.

Due cose fisicamente nella stessa scatola con lo stesso testo **sono lo stesso
inchiostro**, quindi la regola non ha bisogno di un giudizio su che cosa siano.

## 2. Meccanismo B — **l'unione a corpi diversi**

> Righe **consecutive dello stesso blocco**, tutte titoli, formano **un solo**
> titolo, **anche se di dimensioni diverse**. Il livello è quello della
> dimensione **maggiore**.

**Che cosa cambia rispetto a `Criterio_Titoli_v3.md` §2**, che questa regola
emenda: quella diceva «righe consecutive dello stesso blocco, tutte titoli
**della stessa dimensione**». Il vincolo di pari dimensione la rendeva sicura e
la rende cieca qui, dove il titolo cambia corpo parola per parola.

**Perché la dimensione maggiore.** Un titolo nel suo insieme è prominente almeno
quanto la sua parola più prominente. Le alternative erano il livello della
**prima** riga — che su Kul darebbe `ORRORI` (86) e sarebbe arbitrario, perché
l'ordine di lettura di un titolo display non è un ordine di importanza — e quello
della dimensione **dominante per caratteri**, che su `ORRORI DELLA GNOSI` (6, 5,
5 caratteri) sceglierebbe per un carattere di scarto. La maggiore è l'unica delle
tre che si giustifichi senza guardare Kul.

**Il vincolo del blocco è ciò che la tiene sicura**: due titoli davvero distinti —
un capitolo e la sua prima sezione — stanno in blocchi diversi. È lo stesso
confine che la v3 usa già, e non ne aggiungo uno nuovo.

## 3. Il campione e le esclusioni

Seed **`20260902`**. **Sedici manuali** per il veto E, perché entrambi i
meccanismi toccano la composizione della riga, che è di tutti.

**Esplorazione dichiarata** (`AGENTS.MD` §16): la composizione di Kul idx 162,
168 e 169 e il conteggio delle bbox su Kul, Vil, Wil e Dag sono misure fatte prima
di questa dichiarazione. **Non ho misurato** l'effetto dei due meccanismi
sull'uscita, che è ciò che i veti decidono.

## 4. Pass/fail — **un veto per meccanismo, più i globali**

### A. Veto — la sovrastampa

> Su Kul idx 168 la riga a 86 pt deve essere `ORRORI` e non `ORRORI ORRORI`; su
> Vil `'Valois Valois'` deve diventare `'Valois'`; su Wil
> `'◈ villaggio di lala villaggio di lala'` deve diventare
> `'◈ villaggio di lala'`. Cade altrimenti.

### B. Veto — l'unione

> Su Kul idx 168 le tre righe devono formare **un solo** titolo,
> `ORRORI DELLA GNOSI`, al livello di 102 pt; su idx 162 un solo titolo,
> `ANGELI CADUTI SEMIDEI E ARCONTI`. Cade altrimenti.

### C. Veto — **la copertura**

> Nessuna primitiva di testo resta scoperta da un nodo, su nessun manuale.
> `AGENTS.MD` §Coverage, verificabile a macchina.

È il veto che protegge dall'unico modo silenzioso in cui il meccanismo A può
sbagliare: cancellare la primitiva duplicata invece di non ripeterne il testo.

### D. Veto — il giudizio, sul delta

> Cade se una riga promossa **che non era promossa prima dei due meccanismi**
> non è un titolo, o se un titolo vero è stato **unito a un altro** che non gli
> apparteneva, su un campione sorteggiato.

La seconda metà è nuova e serve al meccanismo B: unire due titoli distinti è il
suo modo proprio di sbagliare, e non lo vedrebbe nessuno degli altri veti.

### E. Globale — regressione dell'ordine di lettura

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

**Qui non è una formalità.** Entrambi i meccanismi toccano la composizione della
riga, che sta sulla strada dell'ordine di lettura di tutti e sedici i manuali. Se
questo veto cade, cadono entrambi i meccanismi a prescindere da quanto bene
riparino Kul.

### Se cade

- **A**: cade il meccanismo A, e **B non si giudica**, perché senza A darebbe
  `ORRORI ORRORI DELLA DELLA GNOSI GNOSI`. Si riporta e si ferma il giro.
- **B**: cade B e A si giudica lo stesso — A da solo ripara il testo raddoppiato
  di Vil e Wil, che è un guadagno indipendente.
- **C**: difetto di costruzione, si corregge e si rimisura.
- **D**: si riporta quale riga e quale delle due metà.
- **E**: cadono entrambi.

## 5. Che cosa resta fuori

- **Le 5 coppie quasi-identiche** (3 Wil, 2 Kul): richiederebbero una tolleranza
  geometrica cablata.
- **`REALTAÀ`** su Kul, la À doppia: è una corruzione del testo sorgente, non una
  sovrastampa, e non la tratta nessuno dei due meccanismi.
- **Le schede**, nella chat dedicata.
- **Il debito del font**, che resta aperto.
