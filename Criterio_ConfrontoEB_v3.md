# Criterio — E-B: **allineare**, non riconoscere la sintassi

Sostituisce `Criterio_ConfrontoEB_v2.md`, che aveva chiuso una delle tre rotture
di E-B e dichiarate aperte le altre due. Le chiude tutte, con **una** regola
invece di due.

## 0. Perché non due emendamenti

La v2 lasciava scritto:

> I `#` dei titoli e gli `*` dell'enfasi sono sintassi che l'emettitore aggiunge e
> che la base non ha. Vanno neutralizzati come il `- `, e **non lo faccio in
> questo giro**.

Scriverli come due normalizzazioni separate sarebbe stato **tre volte lo stesso
errore**. E-B è stato rotto da tre meccanismi in fila — gli elenchi, i titoli, i
run — e ognuno lo ha rotto in silenzio, perché nessuno dei tre sapeva di doverlo
aggiornare. La quarta sintassi che nasce lo romperebbe di nuovo allo stesso modo.

Il difetto non è che mancassero due regole: è che il confronto **riconosceva** la
sintassi invece di **derivarla**.

## 1. La regola

> La sintassi non si riconosce: si **allinea**. Ogni nodo porta il suo testo in
> chiaro, `node.text`, e la sua resa è quel testo più i delimitatori che
> l'emettitore ci ha messo intorno. Il confronto usa il testo del nodo, e la
> sintassi cade **qualunque essa sia**, senza sapere quale.

Due eccezioni, entrambe dichiarate:

- **il `- ` si restituisce prima**, sostituito dal marcatore che il nodo dichiara
  (`NodeIR2.marker`, `Criterio_MarcatorePerPrimitiva_v1.md`): la resa lo mette al
  posto del marcatore, che nel testo del nodo c'è ancora. Un nodo senza marcatore
  — dove la testa è una lettera e non un glifo — perde solo il `- `;
- **le note d'asset non entrano**. Sono la sostituzione che questo progetto
  introduce, la base non le ha, e il §3 del criterio d'uscita le dichiara rumore.

Un nodo **senza testo** — tabelle — non ha con che allinearsi e passa com'è.
Stanno già fuori dal giudizio per lo stesso §3.

## 2. E l'allineamento è anche il controllo che mancava

Se un carattere del nodo **non compare nella sua resa**, la resa lo ha perso. È il
difetto di Fab — `- livia` per `Olivia` — e fino a ieri nessuno lo guardava,
perché E-B cancellava i marcatori da entrambi i lati e il confronto passava.

Ora si riporta per nodo:

```
E-B: la resa ha PERSO caratteri di page:0172:text:b0062:l0000:s0000: 'O'
```

Non fa parte del confronto con la base: è un fatto sull'emettitore, e vale anche
dove una base non c'è.

## 3. Il risultato, sul campione dichiarato del criterio d'uscita

Le dieci pagine di `Campione_UscitaIR2Minima_v1.md`, ognuna contro la sua base
rigenerata dalla fetta verticale:

| | |
| --- | ---: |
| **ordine identico alla base** | **9 su 10** |
| differenza | 1, spiegata |
| caratteri persi dalla resa | **0** |

```
FWK idx 122   IDENTICO  1280      Dag idx 199   IDENTICO  1862
BiD idx 287   IDENTICO  1431      Fab idx 126   DIVERSO    797/789
Apo idx  34   IDENTICO  1538      BoB idx 297   IDENTICO  1621
Vil idx  64   IDENTICO  1200      BiD idx 314   IDENTICO  3256
FWK idx  31   IDENTICO  1697      Wil idx  71   IDENTICO  1553
```

**Prima di questa modifica E-B falliva su tutte e dieci**, e falliva al carattere
0 su qualunque pagina con elenchi.

## 4. L'unica differenza, e perché non è un difetto

Fab idx 126: la base scrive `CAPITOLO` **due volte**, IR 2 una.

Sono i due **ridisegni gemelli** — due primitive identiche alle stesse
coordinate — che `redrawn_duplicates` fonde in un nodo solo tenendo gli id del
gemello come copertura. La fetta verticale non deduplica e li emette entrambi.

Il §2 del criterio d'uscita chiede che ogni differenza sia **spiegata**, non che
non ce ne siano. Questa è spiegata, ed è nel verso giusto: il lettore vede
`CAPITOLO` una volta.

**L'arredo è la seconda differenza legittima**, e non compare in questa tabella
perché il campione è stato eseguito senza. Con l'arredo acceso la base porta le
testatine e la resa no — su FWK idx 119, `Capitolo 6`. Neutralizzarla vorrebbe
dire togliere dalla base i nodi esclusi, ed è una terza decisione che non prendo
qui.

## 5. Pass/fail

Non c'è verdetto: è una correzione a un controllo.

### A. La resa non cambia

> Nessun byte del Markdown prodotto cambia.

**Verificato**: 1503 test, invariati salvo gli otto nuovi; il solo fallimento è
quello ambientale già a verbale.

### B. Il campione del criterio d'uscita torna a passare

> Almeno nove pagine su dieci identiche, e ogni differenza spiegata.

**Misurato**: 9 su 10, la decima spiegata al §4.

### C. Nessun carattere cancellato da nessuno dei due lati

Verificabile leggendo `_normalised_sequence`: non toglie più niente, e non ha più
il parametro dei marcatori.

### D. I test nascono falliti

Il test di `_lost_in_rendering` su `Olivia`/`livia` **è nato fallito**, e ha
trovato un difetto vero nella prima stesura: il cursore avanzava mentre cercava, e
al primo carattere mancante finiva in fondo — da lì in poi risultava perso tutto.
Diceva sei lettere perse invece di una.
