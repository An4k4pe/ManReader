# Domanda di contratto — come entra una tabella in IR 2

Documento di decisione, non una proposta di implementazione. Fuori dal repo
(prassi di Milestone 33/34/35). Chat A **non** ha una preferenza fra le opzioni e
lo dichiara: è la ragione per cui la domanda va a revisione prima che si scriva.

---

## 1. Come ci siamo arrivati

Tre tentativi pre-registrati di distinguere una tabella da una scheda mostro:
due caduti (`Esito_RegolaritaTableCandidate_v1.md`,
`Esito_SeparatoriVariabili_v1.md`), il terzo registrato e non eseguito
(`Criterio_TabellaRisolvibile_v1.md`).

Poi una misura sulle strategie di estrazione
(`Esito_StrategiaTabella_v1.md`, seed pre-registrato), che ha dato:

- `lines/lines` — dove trova qualcosa, **non taglia mai una parola** (0 span
  tagliati su 35) e risolve tutto ciò che trova (8 su 8);
- `text/lines`, quella del producer da Milestone 20 — taglia il **61%** degli span
  nelle proprie regioni (215 su 353);
- verdetto della regola scritta prima: **affiancare**, 2 pagine su 5.

Decisione dell'utente: **risolvere le tabelle e portarle a IR 2**.

## 2. Il vincolo di disegno, già concordato

Da pdfplumber si prende **la geometria della griglia**; il **testo viene dalla
sorgente**, assegnando le `TextPrimitive` alle celle per sovrapposizione — come
`table_candidate` già fa oggi per le bbox con `positive_intersection` (Milestone
20).

Il motivo non è estetico: prendere il testo dalle celle di pdfplumber
introdurrebbe **una seconda sorgente di testo** nella pipeline, ed è lo schema che
l'utente ha corretto tre volte (riga, paragrafo, spazi fra span).

## 3. Il problema di contratto

`ir2_model.NodeIR2` impone: **esattamente uno fra `text` e `asset`**, mai
entrambi e mai nessuno. Una griglia non è nessuno dei due.

Ed è precisamente il limite che il modulo dichiara di sé: il pattern aperto di
`kind` vale per i kind **senza struttura interna**; un kind che deve portare
righe e celle non è «un kind in più a costo zero», è **una modifica al contratto**.

## 4. Le opzioni, con i precedenti del repo

**A — campo nuovo su `NodeIR2`.** `table: TableIR2 | None`, e l'invariante diventa
«esattamente uno fra text, asset, table».
*Precedente*: `ir_model.BlockIR` ha già `asset: AssetIR | None`.
*Costo*: ogni kind strutturato futuro chiede un campo, e la proprietà «aggiungere
un kind non tocca il modello» smette di valere per la classe che conta.

**B — nodi figli.** Il nodo tabella ha figli riga, ogni riga ha figli cella.
*Costo*: `PageIR2.nodes` è una tupla piatta con l'invariante «gli `order` sono una
permutazione di 0..n-1». L'annidamento lo rompe, o richiede una relazione
padre-figlio nuova.
*Precedente contrario*: Milestone 33 ha **scartato** di mettere la gerarchia dentro
il candidato e l'ha messa in una misura satellite.

**C — misura satellite.** Il nodo resta piatto e una `TableMeasurements` porta la
griglia.
*Precedente forte*: Milestone 7, 33 e 37; e Milestone 37 ha dimostrato che un
consumer sa ricostruire da candidato più misura.
*Problemi*: il nodo deve comunque portare `text` o `asset`, e oggi non potrebbe
portare nessuno dei due; e una misura «osserva, non decide», mentre una griglia
che determina la resa è vicina a una decisione.

**D — le celle SONO i nodi.** Niente nodo tabella: ogni cella è un nodo piatto con
un kind proprio, e porta riga e colonna.
*Pro*: il modello resta piatto, la copertura funziona senza modifiche, l'ordine
resta una permutazione.
*Costo*: il renderer deve **riassemblare** la tabella dai nodi, e riassemblare è
la parola che su questo progetto ha già fatto danni tre volte.

**E — la tabella è un asset.** *Aggiunta dopo aver guardato il legacy su
richiesta dell'utente; non era nella prima stesura, ed è il precedente più forte
dei cinque.*

Il legacy ha **già risposto a questa domanda**, e nessuna delle quattro opzioni
sopra è la sua risposta:

- `extractor.py:4131` scrive la tabella come **file CSV** in `tables/`;
- `ir_builder.py:126,845` la trasforma in un `BlockIR` con `type="table"` e un
  **`AssetIR`** — in IR 1 **una tabella è un asset**, come un'immagine;
- `ir_builder.py:205-216` (`_text_block_covered_by_table`) **toglie dal flusso di
  lettura** i blocchi di testo coperti dalla tabella (contenimento con tolleranza
  1,5, oppure sovrapposizione ≥ 90%);
- `markdown_builder.py:77` la rende come `[Tabella: …](path)`, **un riferimento
  senza griglia**;
- `epub_builder.py:377-401` costruisce invece una **`<table>` HTML vera** più il
  riferimento al CSV.

Cioè: **la griglia vive in un artefatto referenziato, non nel nodo**, e ogni
renderer decide quanto inlinearla.

Mappato su IR 2, costa **zero modifiche al contratto**: un nodo con
`asset=AssetRefIR2(file_name=".csv")`, e le primitive delle celle come
`primitive_ids` del nodo — copertura soddisfatta, nessuna duplicazione,
`NodeIR2` intatto.

*Vincolo da rispettare*: `AGENTS.MD` §Layout e candidati dice che «un candidato
tabella non rimuove testo e non produce CSV definitivo **prima della
resolution**». IR 2 sta dopo Resolution, quindi è lecito — ma va scritto invece
che sottinteso.

*Costo dichiarato*: il Markdown perderebbe la griglia, come la perde oggi nel
legacy. Se si vuole una tabella Markdown vera, l'emettitore deve rileggere il
file, e allora il file diventa parte del contratto di resa e non solo un asset.

## 5. Le domande aperte che dipendono dalla scelta

1. **L'invariante dell'ordine** (`order` permutazione di 0..n-1) sopravvive?
2. **La copertura**: `ir2_validate` esige ogni `TextPrimitive` in **esattamente
   un** nodo. Con le celle come nodi funziona; con la tabella come nodo unico, le
   primitive delle celle appartengono al nodo tabella e la struttura interna non è
   verificata da nulla.
3. **La resa**: una tabella Markdown vera perde il contenuto multi-paragrafo di una
   cella. Su `D6 ATTACCO` le celle sono paragrafi interi.
4. **La regola di selezione fra le due strategie** — ipotesi suggerita dai dati e
   **non provata**: preferire `lines/lines` dove trova qualcosa, ricadere su
   `text/lines` dove tace. Adiacente, non parte di questa domanda.

## 6. Cosa Chat A NON chiede

Non chiede di scegliere il meccanismo di estrazione, già misurato. Non chiede di
modificare `table_candidate`, che ha oracoli propri da rieseguire a parte
(Milestone 20, Dag p.137, 114/57 primitive).

Chiede **una sola cosa**: quale forma dare alla tabella nel contratto IR 2, e a
quale costo.
