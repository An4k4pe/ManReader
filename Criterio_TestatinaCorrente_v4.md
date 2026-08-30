# Criterio — la testatina, v4: «sopra e sotto» si legge **nella sua colonna**

Emenda `Criterio_TestatinaCorrente_v3.md` in un punto, e **annulla il costo che
la v3 dichiarava**.

## 0. L'indicazione

> «CAPITOLO di Fab ha testo sopra e sotto, sono tutte cose da togliere.»

Misurato su Fab idx 126, `CAPITOLO` a `x 378,9→405,0  y 151,8→162,6`:

```
sopra, su tutta la pagina      8 primitive,  8 non-arredo
sopra, nella sua colonna       0 primitive              →  LIBERO
```

Le otto primitive sopra di lei stanno **in un'altra colonna**. `CAPITOLO` è una
linguetta di margine: il corpo del testo le sta **accanto**, non sopra.

## 1. La modifica

> «In mezzo a un testo» si legge **nella colonna della primitiva**: contano solo
> le primitive la cui estensione orizzontale si sovrappone alla sua.

Nient'altro cambia. Restano dalla v3: il lato libero è **sopra o sotto**, e le
primitive che gli altri rami hanno già dichiarato arredo **non contano come
testo**.

Non c'è nessun numero: «stessa colonna» è la sovrapposizione di due intervalli.

## 2. Misurato

```
testatine tenute:      33 su 33          (la v3 ne perdeva una)
punti di riferimento:  testo sopra e sotto nella sua colonna  →  RESTA nel corpo
```

Sulle pagine nominate dal giudizio dell'utente, **escono tutte**:

```
DB  idx  58   CAPITOLO 5 – MAGIA
Fab idx 126   CAPITOLO                    ← recuperata da questa v4
Vil idx  64   Personaggi 61
FWK idx  31   Capitolo 2  ·  32
Wil idx  71   72
Apo idx  34   Primo atto 31
BiD idx 287   solo 280 — `punti di riferimento` resta
```

## 3. Il costo

**Nessuno.** È la prima versione di questa clausola che non ne dichiara uno: la v2
perdeva `CAPITOLO 5 – MAGIA` su DB, la v3 la recuperava perdendo `CAPITOLO` su
Fab, la v4 le tiene entrambe.

Le tre versioni non sono tre ripensamenti sullo stesso dato: ognuna è caduta su un
caso che la precedente non aveva, e ognuna l'ha nominato prima di correggerlo.

## 4. Che cosa resta aperto

- **`W` su Fab**, l'ornamento di un glifo solo: il ramo lo rifiuta per la riga
  `len(text) < 2` di `running_heads`, ed è a verbale da
  `Esito_DieciPagineOggi_v1.md`. Non lo tocco qui.
- **Le otto voci false su Fab idx 126**, cifre sole, aperte da
  `Criterio_AmbitoDeiFatti_v2.md` §4.D.
