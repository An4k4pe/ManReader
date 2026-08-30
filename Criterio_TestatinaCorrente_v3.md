# Criterio — la testatina, v3: **sopra o sotto**, e l'arredo non conta come testo

Emenda `Criterio_TestatinaCorrente_v2.md` su due punti. La regola di fondo — una
testatina non sta in mezzo a un testo — resta.

## 0. L'indicazione

> «DB si recupera se quando controlli per la testatina nello script hai già
> rimosso sfondi ed estetica.»

**Vero, e misurato.** Su DB idx 58, sotto `CAPITOLO 5 – MAGIA` c'è **una cosa
sola**: il folio `57`. Il lato risultava occupato da qualcosa che è arredo pure
lui.

## 1. Le due modifiche

### A. L'altro arredo non conta come testo che circonda

> Un lato è libero quando oltre di esso non c'è **contenuto**. Le primitive che
> gli altri rami hanno già dichiarato arredo non sono contenuto.

Si esegue in **due passate**: prima l'arredo per slot e il verticale, poi le
testatine, che vedono la prima passata. E ciò che conta come «già arredo» sono le
primitive dei **nodi che escono davvero**, non tutte quelle che stanno in uno slot
d'arredo — marcare gli slot è più largo, ed è il primo tentativo che ho fatto.

### B. Il lato libero dev'essere **sopra o sotto**

Con tutti e quattro i lati, la modifica A **rompeva il caso che la v2 doveva
proteggere**: su BiD l'unica cosa a sinistra di `punti di riferimento` è il folio
`280`, e togliendolo come arredo il lato sinistro risultava libero.

> La direzione che conta è quella della **lettura**. «In mezzo a un testo» vuol
> dire con del testo **sopra e sotto**.

`punti di riferimento` ha 11 primitive sopra e 34 sotto: resta nel corpo.

Le linguette **verticali** non passano di qui — le prende `vertical_primitive_ids`,
che è un fatto della primitiva e non della sua posizione.

## 2. Misurato

```
testatine tenute:  32 su 33
persa:              1
punti di riferimento:  11 sopra, 34 sotto  →  RESTA nel corpo
```

Sulle pagine nominate dal giudizio, escono tutte:

```
DB  idx  58   CAPITOLO 5 – MAGIA     ← recuperata da questa v3
Vil idx  64   Personaggi 61
FWK idx  31   Capitolo 2  ·  32
Wil idx  71   72
BiD idx 287   solo 280 — `punti di riferimento` resta
```

## 3. Il costo cambia, e va detto

La v2 dichiarava persa `CAPITOLO 5 – MAGIA` su DB. **Questa v3 la recupera** e ne
perde un'altra:

```
Fab idx 126   CAPITOLO   slot (90, 39)   resta nel corpo
```

È una linguetta laterale **orizzontale** — 26 pt per 11 — a metà altezza nel
margine destro. Non è verticale, quindi il ramo del verticale non la prende; e ha
testo sopra e sotto, quindi la clausola la protegge.

**L'utente l'aveva segnalata da togliere.** Resta dentro, ed è il prezzo di questa
versione.

> **Perché lo pago e non aggiungo una condizione.** La formulazione dell'utente
> era «solo sui bordi **o comunque** non in mezzo ad un testo», e Fab soddisfa la
> prima metà. Ma «sui bordi» si traduce in una fascia, e una fascia larga
> abbastanza per Fab lascia passare `punti di riferimento` — misurato nella v2,
> 10 contro 30 su cento. L'unico modo per prenderle entrambe sarebbe trattare la
> libertà verticale e quella orizzontale con due regole diverse, tarate sui due
> casi: sarebbe il giro di rifinitura che il `CLAUDE.md` dice di fermare.
>
> E fra le due, **la protezione del contenuto vale più di un arredo mancato**: è
> la barra che questo progetto non negozia.

## 4. Che cosa resta aperto

- **`CAPITOLO` su Fab**, dichiarata qui e non nascosta.
- **Le otto voci false su Fab idx 126**, cifre sole, aperte da
  `Criterio_AmbitoDeiFatti_v2.md` §4.D e non ancora diagnosticate.
