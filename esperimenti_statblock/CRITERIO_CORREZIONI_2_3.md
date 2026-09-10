# Correzioni 2 e 3 — criterio scritto PRIMA di eseguire

Riprende `PASSAGGIO_DI_CONSEGNE.md` §5. Autorizzate dall'utente due delle
quattro correzioni pendenti, e solo quelle.

## Cosa si corregge, e perche' sono difetti e non tarature
- **Correzione 2 — estrazione multipla per riga.** `etichetta()` in `pila.py`
  prende il primo span della riga, quindi su `Ferocia: 2  Taglia: Normale`
  perde `Taglia`. E' sbagliato a prescindere dall'esito: i campi stanno nella
  sorgente e il metodo non li guarda. Ripristina cio' che `real5.py` faceva.
- **Correzione 3 — separatore di colonne derivato.** `COL_GAP = 30.0` e' una
  costante in punti tarata su un impaginato a quattro colonne larghe 250pt, e
  su una pagina a colonna singola da 612pt inventa 2-4 colonne. E' sbagliato a
  prescindere dall'esito: nessuna soglia geometrica va fissata, i confini si
  ricavano dal documento.

Nessuna delle due sposta una soglia per migliorare un numero.

## Cosa NON si tocca
- `pila.py` resta **congelato** (`SPEC_PILA.md`): il lavoro va in `pila2.py`.
- Costanti invariate e copiate alla lettera: `MAGGIORANZA` 0,5, `PROF_MAX` 8,
  `JACCARD` 0,4, `MIN_GRUPPO` 5, `MIN_RICORRENZA = MIN_GRUPPO`, `LIFT_STRATO`
  2,0. Sparisce solo `COL_GAP`, ed e' la correzione stessa.
- **Correzione 1** (co-occorrenza al posto del conteggio) e **correzione 4**
  (misura di copertura): fuori scope, altro giro.
- **Terzo manuale sigillato**: Draw Steel: Monsters (385 pagine, sistema mai
  usato) non viene aperto in questo giro. Manuali 1 e 2 sono banco di
  sviluppo, gia' bruciati; nessun numero di qui vale come validazione.

## Come si consuma `column_band`
Dal producer di produzione (Milestone 37), non da una seconda implementazione:
`build_column_band_page_analysis_with_measurements` da' candidati e misure
satellite, e l'ordine di colonna si ricostruisce da quelli — bbox e primitive
dal candidato, gutter, livello e padre dalla misura. E' lo stesso percorso gia'
esercitato dal consumer della fetta verticale. Le costanti del producer restano
ai default di produzione: non sono parametri di questo esperimento.

## Cosa era gia' noto quando ho scritto questo criterio
Dichiarato perche' il criterio non nasca dopo il dato. Dal giro di ripresa:
- manuale 1 (Daggerheart SRD) riproduce identico a `out_pila.txt`: 474 record
  emessi, 148 soddisfano la verita';
- manuale 2 (Dragonbane Quickstart): 34 etichette di schema, 16 gruppi. Le 4
  schede mostro **escono**, ma decapitate: stanno nel gruppo 3 (7 nuclei, unica
  etichetta di schema `Movimento`, profondita' di testa dedotta 1), il record
  parte dalla riga `Ferocia: …` e il nome del mostro resta fuori. Estensioni
  emesse: 6, 20, 32 e 39 righe.

## Predizioni registrate
- **P1 — non-regressione su manuale 1**: restano 148 record su 148 a
  soddisfare `difficulty:`, e i due gruppi noti restano riconoscibili (129
  nuclei con firma avversari, 19 con firma ambienti).
- **P2 — effetto della correzione 2 su manuale 2**: le occorrenze viste
  salgono da 0 a 4 per `Taglia`, da 1 a 4 per `Armatura`, da 3 a 4 per `PF`;
  `Ferocia` resta 4.
- **P3 — effetto della correzione 3 su manuale 2**: sulle 4 pagine di scheda
  (indici 29, 31, 33, 35) nome e riga dei campi cadono nella **stessa** colonna
  4 volte su 4. Oggi sono 2 su 4 (`VERDETTO_MANUALE2.md`, causa 3).
- **P4 — cio' che NON deve cambiare**: il template dei mostri continua a **non**
  formarsi, perche' 4 occorrenze restano sotto `MIN_RICORRENZA = 5`. E' la
  causa 1, che qui non si tocca.

## Misure
- **M1**: `pila2.py <SRD> --verita difficulty:` — record emessi, record che
  soddisfano, gruppi con le loro firme e profondita'.
- **M2**: occorrenze viste delle cinque etichette Dragonbane (`Ferocia`,
  `Taglia`, `Movimento`, `Armatura`, `PF`) con la nuova estrazione.
- **M3**: per ciascuna delle 4 pagine di scheda, la riga dei campi (quella che
  comincia per `Ferocia`) e la riga del nome (la piu' vicina sopra di essa con
  stile diverso) ricevono lo stesso identificativo di colonna nell'ordinamento
  a bande? Conteggio su 4.

## Criterio di accettazione
Le correzioni si accettano se **P1 regge e P2 e P3 sono soddisfatte**.

- Se **P1 cade**, le correzioni hanno un costo sul manuale su cui il metodo e'
  stato progettato: va riportato, e non si sposta nessuna costante per
  recuperarlo.
- Se **P3 cade**, il separatore derivato non risolve la causa 3: va detto, non
  aggiustato con i parametri del producer.
- Se **P4 e' falsificata** e il template si forma lo stesso, va spiegato da
  dove viene prima di accettarlo: non e' un successo, e' un esito inatteso.
