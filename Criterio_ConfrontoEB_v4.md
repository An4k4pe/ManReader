# Criterio — E-B: anche **l'arredo** è resa, e rientra nel confronto

Chiude la terza differenza che `Criterio_ConfrontoEB_v3.md` §4 aveva lasciato
aperta chiamandola «una terza decisione». È la stessa regola del §1 di quel
criterio, applicata dove non era stata applicata.

## 0. Che cosa restava aperto

> **L'arredo è la seconda differenza legittima.** Con l'arredo acceso la base
> porta le testatine e la resa no — su FWK idx 119, `Capitolo 6`. Neutralizzarla
> vorrebbe dire togliere dalla base i nodi esclusi, ed è una terza decisione che
> non prendo qui. — `Criterio_ConfrontoEB_v3.md` §4

La formulazione conteneva già l'errore: dicevo «togliere dalla base», cioè
cancellare. Ed è la mossa che questo confronto ha sbagliato tre volte di fila.

## 1. La regola

> Togliere l'arredo dal corpo è una decisione di **resa**: non si scrive nell'IR,
> il nodo resta, e l'esclusione vive in `excluded_node_ids`. Quindi l'arredo sta
> accanto ai `#` e agli `*`, non accanto a un contenuto perso — e si neutralizza
> come loro, **restituendolo**, non cancellandolo dall'altra parte.

In concreto: E-B confronta il contenuto emesso **per intero e in ordine**,
ignorando l'esclusione. Non si tocca la base, non si toglie niente da nessun lato.

**Perché è la mossa giusta e non una comodità.** La base è l'uscita della fetta
verticale, che non ha politica d'arredo. Confrontarci una resa già potata
misurerebbe **la politica d'arredo** invece dell'ordine — e E-B esiste per una
domanda sola: *IR 2 emette le stesse cose nello stesso ordine?*

## 2. Il prezzo, dichiarato

Così E-B **non può più vedere un arredo che toglie troppo**.

Non era il suo mestiere: quello lo guardano il canale `review_ir2.md`, che elenca
ogni nodo escluso col suo testo, e i giudizi ciechi — che su questo hanno già
fatto cadere due clausole, quella del testo ripetuto e quella del verticale. Ma
va scritto, perché è la cosa che qualcuno potrebbe credere coperta e non lo è.

## 3. Il risultato, con **tutti** i meccanismi accesi

Le dieci pagine di `Campione_UscitaIR2Minima_v1.md`, `--arredo --elenchi`, ognuna
contro la sua base rigenerata:

```
FWK idx 122  IDENTICO 1280     Dag idx 199  IDENTICO 1862
BiD idx 287  IDENTICO 1431     Fab idx 126  DIVERSO   797/789
Apo idx  34  IDENTICO 1538     BoB idx 297  IDENTICO 1621
Vil idx  64  IDENTICO 1200     BiD idx 314  IDENTICO 3256
FWK idx  31  IDENTICO 1697     Wil idx  71  IDENTICO 1553
```

**9 su 10 identiche, zero caratteri persi**, e FWK idx 119 — la pagina che con
l'arredo acceso falliva ancora dopo la v3 — passa.

La decima resta quella del §4 della v3, ed è spiegata: su Fab la base scrive
`CAPITOLO` due volte e IR 2 una, perché `redrawn_duplicates` fonde i due
ridisegni gemelli e la fetta verticale no.

### Dove eravamo tre versioni fa

```
prima della v2   falliva su 10 pagine su 10, al carattere 0 dove c'erano elenchi
v2               marcatori allineati, ma `#` e `*` la rompevano ancora
v3               9 su 10 — ma solo con l'arredo SPENTO
v4               9 su 10 con tutto acceso
```

## 4. Pass/fail

### A. La resa non cambia

> Nessun byte del Markdown prodotto cambia: E-B è un confronto, non un
> emettitore.

**Verificato**: 1503 test, il solo fallimento è quello ambientale già a verbale.

### B. Il campione passa con i meccanismi accesi

> Almeno nove pagine su dieci identiche con `--arredo --elenchi`, e ogni
> differenza spiegata.

**Misurato**: 9 su 10.

### C. Il test dice la cosa nuova

Il test che asseriva «un nodo escluso non arriva al confronto» **è stato
capovolto**, non cancellato: ora asserisce che l'arredo ci resta, e porta scritto
perché. Un test che cambia verso è una decisione, e si legge come tale.
