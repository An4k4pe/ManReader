# Milestone 44 — verbale. Fase 1: i corridoi respinti smettono di sparire

Piano e criteri in `Criterio_Milestone44_V4_v1.md`. Strada **A** scelta
dall'utente: misura, non candidato.

## Cosa e' stato fatto, in due passi tenuti distinti
`AGENTS.MD` §Regole operative punto 6 chiede di non mescolare riorganizzazione e
cambio funzionale, quindi:

**Passo 1 — estrazione a comportamento invariato** in `page_analysis_column_band.py`:
- `_judge_gutters(...)`: tutti i corridoi della pagina con profilo e verdetto.
  E' il corpo che stava dentro `column_band_tree`, spostato **senza cambiare una
  riga di comportamento** — stesso ordine per altezza decrescente, stesse
  chiamate, stesse costanti. L'albero prende da qui i soli ammessi, come prima.
- `_FlankingProfile` guadagna `left_chars_total` / `right_chars_total`, i
  caratteri **sommati** per lato. Nessun criterio di ammissione li legge: servono
  perche' la misura non debba ripartire i fianchi una seconda volta, che sarebbe
  una seconda implementazione della stessa cosa.
- `column_band_gutter_rows(...)`: l'uscita osservativa, dati puri e non strutture
  interne. `reject_reason` a `None` significa ammesso.

**Passo 2 — la misura**: `page_analysis_column_band_rejected_gutters.py` con
`RejectedGutter` e `measure_rejected_gutters(page_id, rows)`. Riporta i soli
respinti. Non classifica, non ordina, non mette in relazione con altri candidati:
che un corridoio dentro una tabella vada trattato diversamente da uno dentro un
rientro sospeso e' una decisione, e sta in Resolution o nel consumer.

Il record **rifiuta un respinto senza motivo**: sarebbe uno scarto silenzioso
registrato come tale, cioe' esattamente cio' che il modulo esiste per impedire.

## Criteri di accettazione della Fase 1, verificati
- **Nessuna banda cambia.** Corridoi ammessi su manuali reali, prima e dopo:
  **DB 326, Apo 47** — identici ai numeri della Milestone 43.
- **I corridoi verificati compaiono con il profilo gia' misurato**, confrontati
  uno per uno col verbale della 42:

      TORRE 119, rientro sospeso    somma (0, 2020)     atteso (0, 2020)     OK
      FORESTA 121, colonna D6       somma (3, 1343)     atteso (3, 1343)     OK
      TESORI 1 121, colonna D20     somma (14, 743)     atteso (14, 743)     OK
      TESORI 2 122, colonna D20     somma (34, 2255)    atteso (34, 2255)    OK

- **Suite completa: 1271 test verdi**, 7 skipped (1263 preesistenti + 8 nuovi).
- **Ruff** verde sui tre file, **BasedPyright** 0 errori / 0 warning / 0 note.

## Un fallimento di ambiente, non di codice
`test_runs_table_candidate_for_known_dag_page` chiede `Dag.pdf` nella radice del
repo; in un worktree i PDF di benchmark non ci sono, perche' stanno nel checkout
principale e sono gitignorati. Collegato il file (il symlink cade sotto `*.pdf`
del `.gitignore` e non entra nel diff), il test passa. Nessuna relazione con
questa milestone: e' un test che dipende da un file non versionato.

## Cosa la Fase 1 NON fa
L'uscita non cambia. Le bande emesse sono le stesse di ieri, su ogni manuale.
Le 31 bande in piu' su DB e le 22 su Apo arrivano solo con la Fase 2, che e'
dove V4 viene scritta.

## Prossimo passo, e la sua condizione
Fase 2: la regola V4 — dentro un `table_candidate`, un corridoio si scarta solo
se un lato somma zero. Oracolo gia' fissato: **14 su 14** sui corridoi
verificati, **+31 bande su DB e +22 su Apo, zero fuori dalle tabelle**.
Se l'implementazione da' altri numeri, e' l'implementazione a essere sbagliata.

Resta la condizione scritta nel piano: **la Fase 3 non e' rinviabile oltre la 2.**
Una banda a due colonne su una tabella la fa leggere per colonne — tutti i
numeri, poi tutte le descrizioni. Senza la lettura per righe, la Fase 2 peggiora
le tabelle invece di migliorarle.

---

# Fase 2 — V4 in Resolution

## Un problema di forma, risolto senza forzature
Resolution assegna **un esito a un candidato** (`ResolvedCandidateOutcome`). Ma
un corridoio respinto candidato non e': `column_band` non lo ha mai proposto.
Forzarcelo dentro avrebbe voluto dire promuoverlo prima a candidato, cioe' la
strada B scartata alla Fase 1.

Quindi la regola vive in un artefatto **parallelo**,
`resolution_column_boundaries.py`, che non tocca ne' `resolution_model.py` ne'
`resolution_page_candidates.py`: zero rischio sulla regola di Milestone 34.

## Cosa e' stato aggiunto
- `page_analysis_column_band.py`: estratto `_is_too_short` da `_reject_reason`
  (estrazione pura, stessa espressione in un posto solo) e aggiunto alla riga
  osservativa il campo `rejected_only_by_wordiness`. Serve perche'
  `_reject_reason` **si ferma al primo motivo**: un corridoio senza parole puo'
  essere anche troppo basso, e chi legge l'etichetta da sola non lo saprebbe. Il
  campo risponde con i criteri del producer, senza riscriverli altrove.
- `resolution_column_boundaries.py`: `ResolvedColumnBoundary`,
  `ResolvedPageColumnBoundaries`, `resolve_column_boundaries(...)`.
  Quattro esiti, e **ogni** corridoio respinto ne riceve uno:
      admitted_by_table_context   dentro una tabella, entrambi i lati non vuoti
      outside_table_candidate     nessuna tabella lo copre
      empty_flank                 un lato non porta nessun carattere
      other_reject_reason         lo scarto aveva un altro motivo
  Nessuna soglia nuova: «un lato vuoto» e' la distinzione fra c'e' testo e non
  ce n'e'. La relazione tabella/corridoio e' contenimento in x e sovrapposizione
  in y, la stessa con cui l'oracolo e' stato misurato, scritta nel modulo.

## L'oracolo, centrato su entrambi i manuali
Verificato con `scripts/verify_resolution_column_boundaries.py`, che fa passare
la domanda dai moduli di produzione e non piu' dallo script della 42:

| | corridoi | ammessi dal producer | ammessi da Resolution | totale | atteso |
| --- | --- | --- | --- | --- | --- |
| DB | 639 | 326 | **31** | 357 | 357 |
| Apo | 472 | 47 | **22** | 69 | 69 |

Coincidenza esatta con i numeri misurati nella Milestone 43, e nessun confine
ammesso fuori da una tabella — per costruzione della regola, e verificato.

Su Apo i non ammessi per `outside_table_candidate` sono **33**: sono esattamente
gli elenchi puntati che V3 avrebbe preso per colonne. La regola li rifiuta, e il
motivo resta scritto invece di sparire.

## Verifiche
Suite completa **1282 test verdi** (1263 preesistenti + 19 nuovi), 7 skipped.
Ruff verde sui sei file, BasedPyright 0/0/0. Diff su codice preesistente: solo
`page_analysis_column_band.py`, +168/-42, di cui l'estrazione a comportamento
invariato.

## Cosa NON e' cambiato, ed e' voluto
Nessun consumer usa ancora questi confini. Le bande emesse restano quelle di
prima: la Fase 2 dice **quali corridoi Resolution considera validi**, non li
trasforma in bande e non riordina niente.

## La condizione che resta, e non e' un dettaglio
**Fase 3, non rinviabile.** Un consumer che prendesse questi 53 confini e li
usasse come colonne leggerebbe le tabelle per colonne — tutti i numeri, poi
tutte le descrizioni. Sulla tabella dei tesori sarebbe peggio di oggi. La
lettura **per righe** delle regioni coperte da un `table_candidate` va scritta
prima che qualcuno consumi questo artefatto.

---

# Fase 3 — la lettura per righe delle tabelle

## La regola, e dove vale
`table_row_reading_order.py`, funzione pura, non wired: dentro una regione
coperta da un `table_candidate` le righe si leggono **per righe**. Fuori
l'ordine per colonne resta quello giusto e non viene toccato — due colonne di
prosa lette per righe sarebbero interlacciate, cioe' il difetto da cui e'
partita la Milestone 43.

**Come si formano le righe di tabella, senza costanti**: due righe tipografiche
stanno nella stessa riga se le loro estensioni verticali **si sovrappongono**.
E' una relazione fra rettangoli, non una grandezza da tarare, ed e' la stessa con
cui la Milestone 43 ha misurato il testo affiancato.

La cella che va a capo non rompe niente: le righe successive non si sovrappongono
alla prima, formano gruppi propri che contengono solo la colonna della
descrizione, e finiscono in ordine subito dopo.

Le righe non si ricompongono: arrivano gia' formate dalla sorgente e questa
funzione le **riordina soltanto** — un test verifica che nulla venga aggiunto o
perso.

## Il criterio di accettazione, verificato su pagina reale
`scripts/verify_table_row_reading_order.py` su DB indice 103 (stampata 102),
una delle pagine marcate dall'utente:

    ordine di OGGI                          ordine PER RIGHE
    Nebbia. I personaggi vengono colti...   1
    1                                       Nebbia. I personaggi vengono colti...
    questo periodo e' dimezzata.            questo periodo e' dimezzata.
    Passaggio Bloccato. La via e'...        2
    2                                       Passaggio Bloccato. La via e'...

Il numero di riga passa **davanti** alla propria descrizione invece che dentro.
Stesso esito su DB indice 123 (TESORI 2): `1 / Collana d'Oro / 2D6 monete d'oro`
invece di `Collana d'Oro / 1 / 2D6 monete d'oro`.

E' esattamente il difetto che l'utente aveva segnalato guardando il Markdown il
6 settembre — «numeri un po' a caso» — la cui causa prossima era che la riga del
numero e la prima della descrizione differiscono di frazioni di punto in `y`.
Assegnare prima la riga di tabella e poi la colonna lo toglie alla radice invece
di arrotondare le coordinate.

## Un limite della dimostrazione, dichiarato
Lo script passa alla funzione i soli confini **ammessi da Resolution**. Un
consumer vero userebbe anche i gutter che le bande gia' portano: su DB 123 il
separatore `TESORO | VALORE` e' una banda ammessa da sempre e non compare fra i
confini di Resolution, quindi nella dimostrazione quella colonna non partecipa
all'ordinamento. Non cambia l'esito mostrato, ma il consumer dovra' unire le due
fonti.

## Verifiche
Suite completa **1288 test verdi** (1263 preesistenti + 25 nuovi), 7 skipped.
Ruff verde, BasedPyright 0/0/0 su tutti i file della milestone.

## Stato della Milestone 44
Le tre fasi previste dal piano sono fatte:
1. i corridoi respinti non spariscono piu' (misura);
2. V4 decide quali valgono come confine, in Resolution (oracolo centrato:
   DB 326+31, Apo 47+22);
3. le regioni di tabella si leggono per righe.

**Cosa resta fuori, e non e' un dettaglio**: nessun consumer di questa branch usa
ancora ne' i confini ne' l'ordinamento per righe. Il percorso Markdown di
produzione vive su IR 2, che sta su un altro ramo (Milestone 38-41). Collegare
questi tre pezzi a un consumer reale e' lavoro suo, non di questa milestone.

---

# L'innesto in IR 2: i confini ammessi arrivano al consumer

Criterio pre-registrato in `Criterio_ConfiniInTabellaIR2_v1.md`.

## Cosa e' stato collegato, e cosa NO
Collegati i **confini**: `scripts/prototype_ir2_page.py` — da cui `main_ir2.py`
importa, quindi il punto e' unico e vale per il documento intero — aggiunge ai
`gutter_x_intervals` di `TableRegionInput` gli intervalli che
`resolve_column_boundaries` ammette.

**Non** collegato l'ordinamento per righe, e va detto perche' e' un risultato:
`ir2_builder.build_table` raggruppa gia' le righe di tabella per sovrapposizione
verticale delle righe di sorgente, con lo stesso meccanismo di
`table_row_reading_order.py` e con un'uscita migliore — una griglia di celle
invece di un ordine. Collegare anche quella sarebbe stata una seconda
implementazione della stessa cosa. Il modulo resta come contratto verificato dai
suoi test, non come consumatore.

## Le predizioni
- **Q1 — la tabella guadagna la colonna dei numeri: CONFERMATA.** Su DB 122
  (TESORI 2) `| D20 TESORO | VALORE/OGGETTO/EFFETTO |` diventa
  `| D20 | TESORO | VALORE/OGGETTO/EFFETTO |`, e la riga `| 3 Anello d'Oro | 4D6
  monete d'oro |` diventa `| 3 | Anello d'Oro | 4D6 monete d'oro |`.
- **Q2 — non-regressione: CONFERMATA, ed era la condizione.** `main_ir2.py` su
  DB pagine 95-125 prima e dopo: **11 pagine cambiate, 11 pagine con confini
  ammessi, e sono le stesse**. Nessuna pagina toccata dove Resolution non ha
  ammesso niente.
- **Q3 — il costo: FALSIFICATA.** Prevedevo un aumento misurabile perche'
  `column_band_gutter_rows` ricalcola i corridoi. Misurato: 57,1s prima, 57,0s
  dopo su 31 pagine con 4 processi. Sotto il rumore.

## L'effetto, misurato sulle 11 pagine che cambiano
    tabelle costruite      10 -> 12
    righe di tabella      288 -> 346
    celle non vuote       720 -> 846   (+126)
    celle totali        1.262 -> 1.593

Piu' testo finisce dentro la griglia invece di restare paragrafo residuo. Non e'
uniforme: **due pagine peggiorano** — DB 96 perde una cella piena, DB 102 ne
perde cinque. Su DB 102 la tabella era gia' quasi vuota prima: le righe di
descrizione attraversano un gutter e `_column_of` le lascia fuori per scelta
dichiarata («mettere il testo nella cella sbagliata in silenzio e' peggio che
lasciarlo paragrafo»). Il confine ammesso aggiunge una colonna corretta a una
griglia che non riesce comunque a collocare le descrizioni: e' un difetto
preesistente di quella pagina, non introdotto qui, ma il conto peggiora.

Suite completa verde, ruff verde.
