# Proposta — il producer delle regioni tabella

Modalità P. Una proposta sola. Da sottoporre a due giri di revisione indipendente
(metodologico, poi architetturale, in conversazioni separate) prima di qualunque
riga di codice.

**Non committare questo file**: le proposte stanno fuori dal repo (prassi di
Milestone 33, 34, 38, 39). Ciò che si committa è il criterio, e prima della
misura, in un commit senza codice (`AGENTS.MD` §15).

---

## 0. La cosa che devo dire subito, e una volta sola

Il compito è stato aperto dall'utente con questa ragione: avere una struttura in
più prima delle schede mostro, perché **una scheda contiene una tabella** — la
colonna `PARTE × RESISTENZA` di Wil idx 244.

**Ho guardato quella pagina. Nessuna delle tre fonti di regione disponibili nel
repo trova quella tabella**, e questa proposta non la trova. Il valore misurabile
di questa milestone sta su pagine come Apo idx 46 e Vil idx 166 — tabelle vere nel
corpo del manuale — non sulle schede.

Detto una volta. La milestone si costruisce lo stesso: la decisione è dell'utente,
il difetto è reale e osservato, e le pagine su cui paga sono reali anche loro.

---

## 1. Il difetto osservato, con le pagine

Sette pagine, tutte **già spese** in sessioni precedenti (le cinque utili di
`Esito_StrategiaTabella_v1.md`, più Wil idx 244 di `Esito_TabellaInIR2_v1.md`, più
Dag idx 136 che è l'oracolo di Milestone 20). Quattro le ho **aperte con il
render**. Gli indici sono 0-based; i numeri stampati li ho letti sul render, non
dedotti.

### 1.1 `text/lines`, la configurazione del producer: ingoia **e** tronca

| pagina | stampata | regione emessa oggi | cosa contiene davvero |
| --- | --- | --- | --- |
| Apo idx 46 | 43 | 1, `324×393` | **tre** blocchi «COSA PENSA» distinti, più la prosa introduttiva di ciascuno |
| Vil idx 166 | 163 | 1, `366×415` | **due** tabelle distinte, più il titolo display «Spunti per avventure» in mezzo |
| Wil idx 244 | 245 | 1, `474×481` | STILI, ABILITÀ, TRATTI, AGGIUNTIVI, PARTI, COMPORTAMENTO |
| Dag idx 136 | 135 | 2 | vedi sotto |

Su Wil idx 244 la diagnosi di `Esito_TabellaInIR2_v1.md` §1-bis **regge**,
verificata a vista: una sola regione copre cinque strutture non correlate.

**Su Dag idx 136 c'è un difetto nuovo, e sta sulla pagina dell'oracolo di
Milestone 20.** La regione di sinistra è `(72.5, 73.7, 234.6, 744.2)`: comprende
`TIRO` e `BOTTINO` ed **esclude l'intera colonna `DESCRIZIONE`**, che comincia a
`x≈250`. La regione di destra `(319.5, 73.7, 554.7, 418.2)` si ferma dopo la riga
`59` e **lascia fuori la riga `60`**.

Che idx 136 sia la pagina dell'oracolo **l'ho verificato eseguendo**, non dedotto da
`--page N`: `build_table_candidate_page_analysis` su idx 136 dà `(114, 57)` primitive
per candidato, cioè esattamente l'asserzione di
`tests/test_job_page_analysis_runner.py:257`. Le pagine vicine danno `(120, 72)` e
`(35, 33)`.

**I 114 primitivi dell'oracolo sono il conteggio di una regione a cui manca una
colonna.** L'oracolo di Milestone 20 verifica che il producer sia riproducibile, non
che la regione sia giusta — e non ha mai preteso di farlo. Ma è la ragione per cui
il difetto è passato: nessun controllo esistente lo guarda.

Conseguenza metodologica, non solo fattuale: la regione di sinistra ha **51 celle
su 51 piene**, cioè passa per «risolta» al 100% secondo la misura n. 2 di
`Criterio_StrategiaTabella_v1.md`. **La quota di celle piene non vede una regione
troncata**, perché conta le celle che ci sono e non quelle che mancano.

### 1.2 `lines/lines`: il suo punteggio perfetto è fatto di strisce alte una riga

`Esito_StrategiaTabella_v1.md` §2 riporta `lines/lines`: 8 trovate, **8 risolte**,
**0/35 span tagliati**, e §4 dichiara che «il numero che regge meglio è lo 0/35».

Le otto regioni sono queste, guardate:

- **Apo idx 46**: 3 regioni `340×17`, 2 celle ciascuna — sono le **strisce rosa di
  intestazione** `COSA PENSA DEI VILEBORN | COSA PENSA DI GABRIEL`. Il corpo a due
  colonne sotto ciascuna striscia **non è nella regione**.
- **Vil idx 166**: 5 regioni alte 30-42pt — sono le **righe a fondo alternato**
  (zebra) delle due tabelle, non le tabelle.

Su una regione **alta una riga** un confine di colonna non può tagliare uno span
verticalmente, e la quota di celle piene è 100% per costruzione. Lo stesso vale su
Dag idx 136, dove `lines/lines` trova 14 regioni che sono, di nuovo, le righe
zebrate.

Il numero regge esattamente come è scritto e **non regge come suona**: non dice
che `lines/lines` risolve le tabelle, dice che risolve le strisce.

### 1.3 `column_band`, che il repo aveva già e che nessuno aveva messo accanto

Producer wired da Milestone 37. Sulle stesse pagine, la banda e i suoi
`gutter_x_intervals`:

| pagina | bande | esito |
| --- | --- | --- |
| **Apo idx 46** | 3 (`y170-292`, `y334-468`, `y506-652`), gutter `x210-221` | **le tre regioni giuste**, gutter esattamente sul confine fra le due colonne |
| **Vil idx 166** | 2 (`y90-346`, `y358-652`), gutter `x97-99` e `x144-155`,`x247-260` | **le due regioni giuste**, gutter sui confini reali (manca quello della colonna `#`) |
| Wil idx 244 | 2, gutter `x452-458` e `x104-114` | **trova** il gutter che separa la colonna `RESISTENZA`; **sbaglia** l'estensione y (`y0-416` contro `y≈340-590`) |
| Dag idx 136 | 4 annidate, gutter `x163`, `x305`, `x343`, `x411` | **tutti e quattro i confini di colonna sono giusti**; le bande sono alte quanto la pagina |
| DrM idx 267 | 13 annidate | non sono le tabelle |
| FW idx 62 | 0 | muto |
| Fab idx 256 | 0 | muto |

**Conseguenza diretta su un esito già a verbale.** `Esito_TabellaInIR2_v1.md` §4
concludeva che «i gutter dentro le regioni sono pochi» e ne traeva che i confini di
colonna vadano cercati altrove. Sulle pagine qui sopra i gutter **ci sono e sono
giusti**: erano poche le regioni a essere sbagliate. L'affermazione va riformulata,
non ricitata.

### 1.4 Il precedente legacy: eseguito, e su queste pagine è peggio di entrambi

`extractor.py:160` (`_find_table_regions`) affianca le due strategie: base
`lines/lines`, e ammette una regione `text/lines` solo se passa
`_is_valid_text_line_table_region` (`:206-227`). L'ho **eseguito** sulle sette
pagine invece di ragionarci sopra.

| pagina | regioni emesse dal legacy | |
| --- | --- | --- |
| Apo idx 46 | 1 | la regione che ingoia, con 2pt di padding |
| Vil idx 166 | **6** | la regione che ingoia **più** le 5 righe zebrate |
| Wil idx 244 | 1 | `(42.8, −32.8, 549.4, 717.4)` — **esce dal foglio di 32,8pt** |
| Dag idx 136 | **11** | 9 frammenti zebrati a sinistra + 1 regione a destra |
| DrM idx 267 | **0** | |
| FW idx 62 | **0** | |
| Fab idx 256 | **0** | |

Tre cose che questo mostra e che nessuna lettura del codice avrebbe dato:

1. **Su Wil idx 244 il legacy emette una regione che il producer di produzione già
   scarta**: `_bbox_is_contained_in_page` rifiuta `y0 = −32.8`. Il precedente
   produce esattamente ciò che Milestone 20 aveva imparato a buttare.
2. **Su Dag idx 136 il legacy rifiuta la tabella di sinistra perché è alta.**
   `_is_valid_text_line_table_region` esige `altezza ≤ 0,75 × altezza pagina`; la
   tabella occupa `670,5pt` su `792`, cioè l'85%. La soglia fissata a mano scarta
   la tabella vera e lascia i nove frammenti zebrati. È il caso concreto della
   posizione permanente dell'utente sulle soglie hardcoded.
3. **Su DrM, FW e Fab il legacy tace del tutto**, perché `any(...)` su una lista
   vuota è falso: dove `lines/lines` non trova nulla, nessuna regione `text/lines`
   può essere ammessa. Sono le tre pagine che `Esito_StrategiaTabella_v1.md`
   segnava come «producer meglio».

**La direzione del brief — «`lines/lines` riferimento, `text/lines` raffina dentro»
— è la direzione del legacy, e sulle sette pagine il legacy è peggio del producer
attuale su tutte e sette.** Non la trapianto e non la riscrivo con soglie desunte:
il difetto non è nelle soglie, è che nessuna delle due strategie sa dove la tabella
finisce.

---

## 2. Che cosa dice l'insieme delle osservazioni

Le tre fonti sbagliano in modi diversi **sullo stesso asse**:

- `text/lines` **sovraestende in y** (Apo, Vil, Wil) e **tronca in x** (Dag);
- `lines/lines` **frammenta in y**: emette una regione per striscia zebrata o per
  intestazione;
- `column_band` ha **l'estensione y giusta dove la tabella è delimitata da spazio
  bianco** (Apo, Vil) e l'estensione y della pagina dove non lo è (Dag), ed
  eredita sempre **l'estensione x dal padre**, quindi restituisce bande larghe
  quanto la pagina.

Ciò che **nessuno** ha oggi è il confine verticale della tabella. Ciò che
`column_band` **ha già** sono i confini di colonna, che era il pezzo che
`Esito_TabellaInIR2_v1.md` dichiarava mancante.

E c'è un meccanismo, già in produzione e già senza soglie, che calcola confini
verticali dai dati: `_segment_bands` in `page_analysis_column_band.py:871` —
«*ogni y in cui l'insieme dei gutter attivi cambia è un confine. Nessuna griglia di
banda, nessuna soglia di supporto — i confini vengono dai dati*».

---

## 3. La proposta

**Un producer nuovo, `layout.table_region`. Nessun wiring.**

**Meccanismo.** La regione è la **corsa massimale di righe di sorgente consecutive
che condividono lo stesso insieme di gutter**, ritagliata all'**inchiostro delle
proprie primitive**.

- **Estensione y**: i confini di banda di `_segment_bands`. Nessuna soglia nuova.
- **Estensione x**: la bbox visibile delle primitive della corsa. **È la differenza
  rispetto a `column_band`**, che eredita la x dal padre e quindi dà bande larghe
  quanto la pagina anche quando la tabella occupa un terzo del foglio (Vil idx 166:
  banda `x0-454`, tabella `x31-421`).
- **Emissione**: solo corse con **almeno un gutter interno** e **almeno due righe di
  sorgente**. Due conteggi su fatti del documento, non due soglie geometriche.

**pdfplumber non entra.** `table_candidate` **non viene toccato**: stesso
`configuration_id`, stesso `producer_version`, oracolo di Milestone 20 (Dag idx
136, 114/57 primitive) non rieseguito perché non c'è nulla da rieseguire.
`column_band` **non viene toccato**: il suo campione cieco e il giudizio a vista
dell'utente su 10 pagine restano validi.

**Riuso, e la tensione che porta con sé.** Il producer riusa **funzioni pure** di
`page_analysis_column_band.py` sul `NormalizedPrimitivePage` — non i suoi
candidati. È il precedente di Milestone 27 e 30, che riusano invariate le
diagnostiche di Milestone 25/26 come funzioni pure.

Ma la docstring di `build_column_band_page_analysis_with_measurements`
(`:1118-1132`) dice che `column_band_tree` esiste perché **non venga più chiamata
da fuori**: «esporre l'albero interno era il ponte provvisorio». Qui si chiamano le
funzioni **sotto** l'albero (`_group_by_pymupdf_line`, `_build_gap_grid`,
`_chain_gutters`, `_segment_bands`), non l'albero. **Se la revisione giudica che sia
lo stesso ponte, l'alternativa è estrarre il meccanismo in un modulo condiviso — che
è un refactor, e va deciso, non fatto di straforo.** Lo segnalo come decisione da
prendere in revisione, non come dettaglio.

**Perché un producer nuovo e non due candidati concorrenti dallo stesso producer.**
`AGENTS.MD` §Layout e candidati ammette esplicitamente candidati sovrapposti e
concorrenti, quindi la strada esisterebbe. Non la prendo perché non chiude nulla:
consegnare al consumer due regioni incompatibili senza una regola di Resolution
significa che il consumer sceglie male, ed è la condizione che Milestone 37 ha
dovuto tamponare con `first_level_only`.

---

## 4. Il criterio di accettazione, scritto prima — **uno solo**

Va committato in un commit **senza codice** prima di eseguirlo (`AGENTS.MD` §15),
in `Criterio_RegioneTabella_v1.md`.

### 4.1 L'etichetta la dà l'utente, prima di qualunque uscita del codice nuovo

Per ogni pagina del campione, sul **render**: quante tabelle ci sono e dove
(rettangolo a occhio), oppure «nessuna». Se l'etichetta arrivasse dopo, sarebbe una
lettura post-hoc — il difetto che `AGENTS.MD` §15 vieta e che
`Criterio_TabellaRisolvibile_v1.md` §4 aveva già fissato in questo modo.

### 4.2 L'appaiamento, definito adesso

Una regione emessa **appaia** una tabella etichettata se l'area della loro
intersezione è **≥ 80% dell'area di entrambe**. Una soglia sola, simmetrica:
sopra prende chi ingoia, sotto prende chi tronca. L'80% è lo stesso numero già
fissato in `Criterio_TabellaRisolvibile_v1.md` §3, quindi non è scelto adesso.

### 4.3 La regola di pass/fail

> **Regge** se, sul campione cieco, `layout.table_region` appaia **più** tabelle
> etichettate di quante ne appaia `table_candidate` sulle stesse pagine, **e** non
> perde nessuna tabella che `table_candidate` appaiava.
>
> **Cade** sotto una qualunque delle due.

La seconda clausola è l'errore squalificante, stessa forma del §3/§5 di
`Criterio_TabellaInIR2_v1.md`: una sola regressione ferma il giro.

### 4.4 Come può fallire, dichiarato prima

**Il criterio ha una via di caduta che considero probabile.** Su Dag idx 136, FW
idx 62 e Fab idx 256 — cioè su 3 delle 7 pagine già guardate — `column_band` è muto
o dà bande alte quanto la pagina, mentre `text/lines` una regione la produce. Se il
campione cieco contiene pagine di quella famiglia e lì `table_candidate` appaiava,
**la seconda clausola scatta e il giro si ferma**.

In quel caso l'esito **non** è «il meccanismo è sbagliato»: è che il verdetto
«affiancare» di `Esito_StrategiaTabella_v1.md` vale anche qui, con `column_band` al
posto di `lines/lines`, e la scelta fra i due candidati concorrenti è **di
Resolution**, non di un producer. Lo scrivo prima perché non possa essere letto
dopo come una scoperta.

### 4.5 Il campione

Estratto con `scripts/sample_ir2_verification_pages.py`, **seed nuovo dichiarato
nel criterio prima dell'estrazione**, dal pool dei 16 manuali. **Escluse per
costruzione** le sette pagine aperte in questa sessione — Apo 46, Vil 166, Wil 244,
Dag 136, DrM 267, FW 62, Fab 256 — oltre a quelle già nella lista dello script.
Le sette restano come **ancore dichiarate**, citabili come sviluppo e mai come
verifica.

### 4.6 Limite dichiarato prima

Il criterio misura **dove comincia e dove finisce la regione**. Non dice nulla su
righe, celle, intestazioni o resa: quelle sono il meccanismo di Milestone 39, che
resta spento. Una regione perfetta con una griglia sbagliata passa questo criterio,
e deve poterlo passare — altrimenti sto misurando due cose e non ne so falsificare
nessuna.

---

## 5. Perimetro, chiuso

**File ammessi**: un modulo nuovo `page_analysis_table_region.py`; il suo file di
test; uno script diagnostico in `scripts/` che produce i numeri citati
(`AGENTS.MD` §Aggiornamento documenti lo richiede committato); `Criterio_…` ed
`Esito_…`; `State.md` e `AGENTS.MD` a chiusura.

**Non toccare**: `page_analysis_table_candidate.py`, `page_analysis_column_band.py`,
`page_analysis_column_band_measurements.py`, `job_page_analysis_runner.py`,
`extractor.py`, i quattro moduli `ir2_*.py`, i renderer.

---

## 6. Cosa resta esplicitamente fuori

- **Il wiring nel job.** Milestone separata: precedente M27→M28 e M30→M31.
- **La tabella dentro la scheda.** Su Wil idx 244 nessuna delle tre fonti trova
  `PARTE × RESISTENZA`, e questa proposta non la trova. È la ragione dichiarata per
  cui la milestone è stata aperta, e **non la chiude**.
- **Le righe e le celle.** Si produce la regione, non la griglia. `--tables` in IR 2
  resta spento e `Criterio_TabellaInIR2_v1.md` resta caduto.
- **La regola di Resolution** fra `layout.table` e `layout.table_region`: due
  candidati concorrenti, ammessi dall'invariante, non risolti qui. Stessa condizione
  di `table_candidate`, `page_covering_visual`, `page_edge_visual` e `column_band`
  dalle Milestone 21/23/24/37: non un'eccezione introdotta adesso.
- **L'estrazione di `_visible_bbox`**, alla sedicesima copia (fuori scope di
  Milestone 37). Il modulo nuovo ne fa la diciassettesima, e lo dichiaro invece di
  approfittarne per aprire il refactor.
- Dalla lista aperta di Milestone 39, **restano tutti dove sono**: la coppia
  etichetta-valore (69% del difetto misurato su Wil idx 244), la fusione dei
  paragrafi quando si sottrae testo dal flusso, `text.heading`, l'invariante di
  conservazione dei **caratteri** nel percorso IR 2, l'ancora delle note d'asset per
  `y`, la rimozione dell'arredo, la milestone di uscita dallo shadow mode.

---

## 7. Che cosa ho verificato e che cosa no

**Verificato eseguendo**: le regioni delle due strategie pdfplumber sulle 7 pagine;
le bande e i gutter di `column_band` sulle stesse; `_find_table_regions` e
`_is_valid_text_line_table_region` del legacy sulle stesse; i numeri stampati di
Apo 46, Vil 166, Wil 244, Dag 136 letti sul render.

**Verificato guardando**: Apo 46, Vil 166, Wil 244, Dag 136 — quattro render, con le
regioni disegnate sopra.

**Non verificato, e lo lascio alla revisione**:

- DrM 267, FW 62, Fab 256 **non le ho aperte**, quindi non affermo che le regioni
  `text/lines` lì siano giuste o sbagliate — dico solo quante e dove sono.
- Il meccanismo del §3 **non è stato eseguito su nessuna pagina**: è una proposta, e
  il §4.4 dice come può cadere.
- «Nessuna delle tre fonti trova `PARTE × RESISTENZA` su Wil idx 244» vale per **le
  tre che ho eseguito**. La colonna `RESISTENZA` è un **rettangolo nero**, cioè un
  primitivo di disegno: `interior_visual_frame` ed `embedded_visual` potrebbero
  delimitarla, e **non li ho provati**. Se uno dei due la trova, il §0 di questa
  proposta va riscritto e forse anche il §3.
- «Un difetto nuovo, mai scritto» (§1.1) l'ho verificato sui documenti **vivi**.
  **`State_Archive.md` non l'ho cercato**, per la regola che ne vieta la lettura: se
  qualcuno ricorda di averlo già visto lì, l'affermazione va indebolita.
- `_visible_bbox` «alla sedicesima copia» viene da `AGENTS.MD` §Milestone 37, **non
  l'ho ricontato**.

**Base empirica**: 7 pagine, 6 manuali, tutte già spese. Non è un campione, è
l'insieme delle pagine su cui il difetto era già a verbale. Il campione cieco viene
dopo il criterio, non prima.
