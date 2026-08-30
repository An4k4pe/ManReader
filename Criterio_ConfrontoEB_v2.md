# Criterio — E-B: si **rimette** il marcatore, non si cancella il carattere

Sostituisce il §5.E di `Criterio_Elenchi_v1.md`. Non cambia niente della resa:
cambia come E-B la confronta con la base.

## 0. Che cos'è E-B, in una riga

`Criterio_UscitaIR2Minima_v2.md` §2: **l'ordine emesso da IR 2 deve essere
identico alla base** — l'uscita della fetta verticale al commit `3a2238d`, su
nove pagine che l'utente aveva giudicato corrette *prima che IR 2 esistesse*.

Il confronto è fra le **sequenze di caratteri non-spazio** del Markdown reso e
della base. Essendo sensibile all'ordine, becca anche i caratteri persi — ed è
**l'unico controllo che guarda l'uscita resa**. La conservazione a livello di IR è
un'altra cosa e su questi casi funzionava: `node.text` conserva tutto, e la
perdita stava solo nel Markdown.

## 1. L'emendamento che sostituisco faceva **due** danni opposti

Il §5.E toglieva i marcatori dichiarati **da entrambi i lati**.

**Cancellava troppo.** Il carattere spariva *ovunque comparisse nel documento*,
non solo in testa alle voci. Ammessa `O` come marcatore su Fab, ogni `O` usciva da
tutt'e due i lati, e la resa `- livia` per `Olivia` passava il confronto senza che
niente se ne accorgesse.

```
marcatori spediti   Fab 0,1%   DrM 0,6%   DrW 0,5%   dei caratteri ciechi a E-B
```

Poco, oggi, e per una ragione che non è una garanzia: i marcatori alfanumerici
ammessi finora stanno in font di simboli e sono rari nell'alfabeto — `w` in venti
pagine di italiano compare 25 volte.

**E cancellava troppo poco.** Toglieva il marcatore ma **non il `- `** che la resa
mette al suo posto, e il trattino è un carattere non-spazio che sopravvive alla
normalizzazione. Il confronto restava asimmetrico e falliva **per costruzione** su
qualunque pagina con elenchi. Misurato su FWK idx 119:

```
base   'Capitolo6Muriecancellicorazzati.Unmausoleo…'
nuovo  '-Muriecancellicorazzati.-Unmausoleo…'          divergenza al carattere 0
```

Un emendamento scritto per far passare il confronto, che il confronto non lo
faceva passare, e intanto lo accecava altrove.

## 2. La regola

> E-B **non cancella niente per carattere.** Ogni riga che la resa ha aperto con
> `- ` torna ad aprirsi col **marcatore che il suo nodo dichiara** — `NodeIR2.marker`,
> `Criterio_MarcatorePerPrimitiva_v1.md`. Poi i due lati si confrontano interi.

Un nodo **senza** marcatore — `Olivia` su Fab, dove la testa è una lettera e non
un glifo — perde solo il `- `, e il testo resta intero da tutt'e due le parti.

L'appaiamento è **per ordine di emissione**, e si guardano solo i nodi la cui resa
comincia davvero per `- `: un glifo orfano del suo testo si rende vuoto e non
consuma un posto.

**Resta** l'emendamento della deidratazione, che è d'altra natura: un trattino è
un carattere non-spazio e riunire una parola lo cambia legittimamente.

## 3. Che cosa questo ripara, misurato

FWK idx 119, stessa base, stessa pagina:

```
prima   divergenza al carattere    0     base 'Capitolo6Muriecancelli…'  nuovo '-Muriecancelli…'
dopo    divergenza al carattere  354     i marcatori `*` coincidono uno per uno
```

E il confronto torna a **vedere**: non si cancella più niente da nessuna parte,
quindi una lettera persa nella resa fa divergere le sequenze.

## 4. Che cosa **non** ripara, e va dichiarato

E-B è stato rotto da tre meccanismi in fila, non da uno. Questo ne chiude uno.

**Le due asimmetrie di sintassi Markdown**, che nessun emendamento copre:

```
base   '…NegromanteIndipendenteSostituisceOccultista120…'
nuovo  '…###**NegromanteIndipendente***Sostituisce**Occultista*****12…'
```

I `#` dei titoli e gli `*` dell'enfasi sono sintassi che l'emettitore aggiunge e
che la base non ha. Vanno neutralizzati come il `- `, e **non lo faccio in questo
giro**: sono due emendamenti a due meccanismi diversi — i titoli e i run — e vanno
dichiarati prima, ognuno col suo.

**E l'arredo, che è un'altra cosa ancora.** Su FWK la testatina `Capitolo 6` esce
dal corpo giustamente, quindi la base ce l'ha e la resa no. Non è un'asimmetria di
sintassi: è una **differenza di contenuto voluta**. Il §2 del criterio di uscita
dice che ogni differenza va *spiegata*, non che non ce ne debbano essere — e
questa è spiegata. Se qualcuno la volesse neutralizzare dovrebbe togliere
dalla base i nodi esclusi, ed è una terza decisione.

> **E-B oggi non passa su nessuna pagina che abbia titoli, enfasi o arredo.** Era
> già così prima di questa modifica; quello che cambia è che ora si sa **perché**,
> voce per voce, con la misura accanto.

## 5. Pass/fail

Non c'è verdetto: è una correzione a un controllo, e le barre sono di regressione.

### A. La resa non cambia

> Nessun byte del Markdown prodotto cambia: E-B è un confronto, non un
> emettitore.

**Verificato**: la suite passa invariata, 1495 test, e il solo fallimento è quello
ambientale già a verbale.

### B. I marcatori coincidono

> Sulla pagina che l'ha imposta, i marcatori dei due lati devono allinearsi uno
> per uno.

**Misurato**: FWK idx 119, divergenza da 0 a 354, e i `*` restituiti coincidono.

### C. Il confronto torna a vedere

> Nessun carattere viene più cancellato da nessuno dei due lati.

Verificabile leggendo `_normalised_sequence`: non ha più il parametro.
