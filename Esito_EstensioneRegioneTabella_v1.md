# Esito di `Criterio_EstensioneRegioneTabella_v1.md` — **il giro si ferma**

L'errore squalificante del §5 è scattato. Il criterio ha fatto ciò per cui era
stato scritto: è il primo verdetto di questo filone che **non** viene da Chat A
che guarda i numeri e decide.

## 1. Che cosa è stato provato

L'ipotesi del §2, nella formulazione corretta dall'utente: una banda entra nella
regione se **nessun** gutter del gruppo interseca testo lì **e almeno uno** ha
testo a lato.

## 2. L'errore squalificante — 5 pagine su 12

| pagina | linea di base §5 | dopo |
| --- | --- | --- |
| Lan pag19 | 7 × 13 | 7 × **6** |
| Lan pag52 | 3×10 **e** 3×10 | 3×**5** e 3×10 |
| DrW pag240 | 12 × 22 | **niente** |
| DrW pag33 | 4 × 53 | **niente** |
| DB pag76 | 5 × 34 | **niente** |
| DrW pag248 | 4 × 44 | 5 × **3** |

**Causa**: la clausola «nessun gutter interseca testo» è troppo stretta perché
basta **una** riga con una cella larga che attraversa **un** gutter per chiudere
la corsa. Nelle tabelle vere questo succede spesso: una descrizione lunga, una
riga di totale, una cella unita.

## 3. La cosa scomoda, che non uso per salvare l'esito

**Su Dag pagina 136 la regola funziona**, e meglio di prima: da `4 × 22` a
`6 × 11`, che è il conteggio giusto per le due tabelle affiancate a tre colonne.
È l'unica pagina in cui la formulazione corretta batte quella vecchia.

Il §5 dice che **una sola regressione ferma il giro**, e ce ne sono cinque. Non
rileggo la regola alla luce del risultato: era pre-registrata proprio per questo.

## 3-bis. Seconda esecuzione: la clausola era implementata al contrario

Rilievo dell'utente dopo il primo esito: **il gutter non va centrato né fissato,
va allineato** perché sia una linea continua che attraversa la tabella senza
toccare nulla — nelle sue immagini nessuna linea tocca una parola, e per riuscirci
stanno da un lato del corridoio.

Aveva ragione sull'implementazione: la prima esecuzione **fissava la x sul seme e
poi verificava** che non intersecasse, quindi bastava una riga con una cella larga
a chiudere la corsa. Il §2 era stato testato al contrario.

Rifatto con la linea che si **riallinea** a ogni banda aggiunta. **Cade di nuovo,
e più forte**: Lan pagina 19 da `7×13` a `5×3`, Lan pagina 52 da due tabelle a una
da 80 righe, BoB pagina 239 da `2×7` a `2×44`, Wil pagina 78 da `4×6` a `1×1`,
DrW pagina 248 da `4×44` a `3×251`. Migliora due pagine (Wil pagina 74 da 17 a 22
righe su 20 attese; DB pagina 62 perde una regione spuria).

## 3-ter. CORREZIONE — la spiegazione del 3-bis era sbagliata

Il §3-bis spiegava le regressioni così: «una linea che può spostarsi di lato trova
quasi sempre un passaggio, quindi la corsa attraversa anche la prosa». **Scritta
senza guardare i render.** Su richiesta dell'utente sono stati disegnati, e la
spiegazione è falsa su tutte e tre le pagine controllate.

Le linee non attraversano la prosa. Sono **margini** e **spazio occupato da
immagini**:

| pagina | la linea che allunga la corsa | che cos'è |
| --- | --- | --- |
| BoB pag239 | una sola, `x395-414` | il **margine destro**, fra il corpo e la linguetta `227` |
| Lan pag52 | una sola, `x48-59` | il **margine sinistro**, fra il bordo e la linguetta `[50]` |
| Lan pag19 | quattro, i gutter **veri** della tabella | proseguono in basso attraverso le **illustrazioni** |

Due cause, entrambe concrete e correggibili, nessuna delle due fondamentale:

1. **L'arredo di bordo sposta il limite «dentro l'inchiostro».** `page_x0`/`page_x1`
   sono il minimo e il massimo su **tutte** le bande: la linguetta di capitolo o
   il numero di pagina li spingono oltre il corpo, e il margine diventa un
   corridoio interno.
2. **La griglia di occupazione conta solo il TESTO.** Sotto la tabella di Lan
   pagina 19 ci sono quattro illustrazioni, che per la griglia sono vuoto: i
   gutter veri della tabella proseguono indisturbati fino in fondo alla pagina.

**Il repo ha già i producer che vedono entrambe**: `page_edge_visual` e
`side_band` per le linguette, `embedded_visual` per le illustrazioni. Non è più
un'ipotesi su un «secondo segnale»: è una mancanza precisa, vista su tre render.

Resta vero che le sei ipotesi sono cadute. Cambia **perché**, e cambia che cosa
serve: non una settima regola sui gutter, ma togliere l'arredo dal calcolo e
mettere il non-testo nella griglia.

## 4. Che cosa questo dice, e che cosa no

**Dice** che «tutti i gutter liberi» non è la formulazione giusta della clausola
di non-intersezione. Non dice che l'osservazione dell'utente sia sbagliata:
l'estensione governata dai gutter resta l'unica descrizione che copre sia le
tabelle tracciate sia quelle a spazio bianco.

**Non dice** nulla sulle colonne, che restano giuste, né sulla copertura.

## 5. Il conto dei tentativi, che è il dato metodologico

**Sei** ipotesi sull'estensione verticale, tutte falsificate. Le prime quattro
decidendo a posteriori sui numeri; la quinta e la sesta contro un criterio scritto
prima. Le
prime quattro sono a verbale nelle docstring di
`scripts/prototype_table_columns_and_rows.py`, questa nel suo `extends`.

La lettura che ne do, e che **non** è un sesto tentativo: ogni regola provata ha
bisogno di sapere già dove finisce la tabella per decidere dove finisce la
tabella. Il §7 del criterio prevedeva questo caso e chiede un criterio proprio per
l'ipotesi successiva — **un secondo segnale indipendente dai gutter**. Su DB
pagina 76 la corsa si allunga sul fregio, che è un **disegno**, e sul piede di
pagina, che è testo in posizione fissa: due cose che il repo ha già producer per
vedere (`page_edge_visual`, `embedded_visual`, e il piede segnalato da
Milestone 37).
