# Proposta — una tabella vera nel Markdown, da IR 2

Chat A, Modalità P. 19 agosto 2026. Fuori dal repo (prassi di Milestone 33/34/35).

**Registra `AGENTS.MD` §614**: «tabelle, callout o liste come nuovo comportamento
attivo» è fra le attività non autorizzate senza decisione architetturale dedicata.
Questo documento è quella decisione. Rilievo E‑5 della revisione.

---

## 1. Il bersaglio, e la regola che ne discende

**Una tabella che si legge come una tabella in `page_ir2.md`.** Non un candidato,
non una misura, non un fatto misurato: una tabella nel file che una persona apre.

Ne discende una regola di metodo, presa su rilievo dell'utente e valida da qui in
avanti: **non si costruisce niente che non finisca nell'uscita.** In questa
sessione tre criteri per distinguere una scheda da una tabella sono stati
registrati al livello dei candidati — due caduti, uno mai eseguito — senza che
nessuno finisse in un `page_ir2.md`. Ora che IR 2 esiste, è il bersaglio di
tutto, e le proposte precedenti vanno riviste con quel metro.

## 2. Cosa esiste già, misurato

- **Le tabelle si risolvono.** `lines/lines`, dove trova qualcosa, **non taglia
  mai una parola** (0 span tagliati su 35) e risolve tutto ciò che trova (8 su 8).
  `text/lines`, la configurazione dell'unico producer, ne taglia il **61%**
  (215 su 353). Verbale in `Esito_StrategiaTabella_v1.md`, seed pre‑registrato.
- **La regola di affiancamento esiste già nel repo**, e non l'avevo trovata:
  `extractor.py:159-175` prende come base le regioni `lines/lines` e ammette una
  regione `text/lines` solo se supera `_is_valid_text_line_table_region`. La
  direzione è quella; le sue **costanti fissate a mano** (3, 3, 8, 0,75, 0,5) sono
  ciò che il progetto vieta, quindi il precedente **non è trapiantabile**.
- **IR 2 produce Markdown verificato**: E‑B 10 su 10 sul campione cieco.
- **`layout.table` esiste già** come `structural_kind` emesso.

## 3. La forma: **un nodo con dentro la griglia**

`NodeIR2` guadagna un terzo campo alternativo. L'invariante passa da «esattamente
uno fra `text` e `asset`» a «esattamente uno fra `text`, `asset`, `structure`».

```
NodeIR2.structure: StructureIR2 | None

TableIR2(rows: tuple[tuple[CellIR2, ...], ...])
CellIR2(row: int, column: int,
        primitive_ids: tuple[str, ...],
        paragraphs: tuple[str, ...])
```

**Il campo si chiama `structure`, non `table`.** Alla seconda volta — callout,
scheda mostro — si allarga un'unione invece di aggiungere un quarto braccio
all'invariante. Rilievo D‑2 della revisione: il costo che il documento
precedente imputava a questa opzione era un costo della **scrittura**, non
dell'opzione.

**La cella porta una tupla di paragrafi, non una stringa.** Su `D6 ATTACCO` le
celle sono paragrafi interi: la IR li conserva, ed è il **renderer** a degradarli
in una tabella Markdown, dichiarando come. Perdita di resa, non di contenuto —
`AGENTS.MD` §Confini obbligatori, `≠ IR ≠ rendering`.

**Il testo delle celle viene dalla sorgente.** Da pdfplumber si prende **solo la
geometria** dei confini; le `TextPrimitive` si assegnano alle celle per
sovrapposizione, come `table_candidate` già fa per le bbox (Milestone 20,
`positive_intersection`). Prendere il testo dalle celle di pdfplumber
introdurrebbe una **seconda sorgente di testo**, lo schema che l'utente ha
corretto tre volte.

### 3.1 Perché non le celle come nodi

L'alternativa — ogni cella un nodo — ha **un vantaggio reale**: si potrebbe
correggere a mano una singola cella, perché `HumanOverride.target_id` punta a un
`node_id`. È scartata per tre costi verificati dalla revisione:

- richiede **due campi nuovi** (riga, colonna) su `NodeIR2`, quindi cambia il
  contratto **quanto** la forma scelta, non meno;
- l'ordine di lettura arriva da `column_band`, che una tabella la legge **per
  colonne** (`State.md`: i gutter annidati di DB p.76 sono «la descrizione
  corretta di una tabella a nove colonne»). O riordina il costruttore — che la sua
  docstring vieta, ed è il bug corretto in Milestone 38 — o riordina il renderer,
  e allora `order` **non è** ordine di lettura proprio dove serve;
- il confine del nodo sarebbe il confine della cella, quindi tarare la strategia
  di estrazione cambierebbe i `node_id` e **orfanerebbe le correzioni umane**.

**La condizione che l'avrebbe ribaltata è stata verificata e non si dà.** La
revisione indipendente aveva indicato un solo argomento decisivo a favore delle
celle-come-nodi: se la correzione umana **per cella** fosse un requisito.

Decisione dell'utente, con una ragione che non è una preferenza di prodotto ma
**l'obiettivo**: *«non credo di dover correggere una cella, è un lavoro di
consultazione il motivo per cui stiamo creando questo programma»*. `AGENTS.MD`
§Obiettivo dice «perché la consultazione resti comoda», e un artefatto di
consultazione non ha bisogno di essere editabile alla cella.

L'unità di correzione resta il **nodo tabella**, che è comunque indirizzabile da
`HumanOverride`/`AIProposal`. Se un giorno servisse la cella, il costo è quello
scritto sopra e andrà pagato allora, non anticipato adesso.

## 4. Da dove viene la griglia

**Una misura satellite**, sul pattern di Milestone 7/33/37, che per ogni
`table_candidate` risponde a due cose: *la griglia si risolve?* e *dove cadono i
confini di riga e colonna?*

Nessun producer toccato — `table_candidate` ha oracoli propri (Milestone 20,
Dag p.137, 114/57 primitive) che il §7 tiene fuori.

**L'affiancamento delle strategie vive qui**, non nel producer: la misura prova
`lines/lines` e, dove tace, `text/lines`, riportando **quale** ha risolto. La
direzione viene da `extractor.py:159`; le sue costanti no. Dove nessuna delle due
risolve, la misura lo dice, e quel «non risolta» è il dato che
`Criterio_TabellaRisolvibile_v1.md` — già registrato — usa come discriminante.

## 5. Igiene del contratto, da fare **prima** di toccare il nodo

Due rilievi della revisione, entrambi verificati eseguendo:

- **`schema_version` non è controllata**: `ir2_model.py` la valida solo come
  stringa non vuota, e una `'9.9-inventata'` passa. Aggiungere il gate sul
  modello di `page_analysis_model.py`. Senza, un IR 2 vecchio non fallirà dicendo
  «sei vecchio» ma «chiave sconosciuta».
- **`text=""` è accettato**: un nodo può dichiarare di avere testo e non averne.
  Va vietato, altrimenti è la scorciatoia che passa i test.

## 6. Criterio di accettazione — da committare prima del codice

**P0 — nessuna regressione.** E‑B resta 10 su 10 sul campione cieco, e il corpo di
`page_ir2.md` privato delle tabelle resta identico sulle pagine senza tabelle.

**A1 — la tabella si legge come una tabella.** Su un set dichiarato prima, il
Markdown contiene una tabella con le righe della pagina, giudicata a vista
dall'utente con il render accanto.

**A2 — nessun contenuto perso.** Ogni `TextPrimitive` della regione tabella sta in
esattamente una cella; l'unione delle celle coincide con le primitive del nodo.
Verificato dal validatore esteso, non asserito.

**A3 — nessuna parola tagliata.** Nessuno span attraversato da un confine di
colonna nelle regioni che diventano tabelle. È la misura che ha selezionato la
strategia, riusata come guardia.

**Regola d'arresto**: se su una pagina del set la tabella esce peggio del testo che
esce oggi, il giro si ferma. «Peggio» lo giudica l'utente a vista.

## 7. Perimetro

**Ammessi**: `ir2_model.py`, `ir2_serialization.py`, `ir2_builder.py`,
`ir2_markdown.py`, `ir2_validate.py`, un modulo nuovo per la misura della griglia,
`scripts/prototype_ir2_page.py`, e i test.

**Vietati**: ogni `page_analysis_*.py` — **incluso** `table_candidate`;
`resolution_*.py`; `primitive_model.py`; `markdown_builder.py`,
`epub_builder.py`, `ir_*.py`, `extractor.py`.

## 8. Fuori scope, dichiarato

La categoria scheda mostro: tre criteri, due caduti e uno non eseguito, e
l'ispezione visiva di tre manuali con tre forme che non si somigliano.
`text.heading` e `text.callout` in emissione. La rimozione dell'arredo. L'EPUB.
La modifica di `table_candidate`. La correzione per cella (§3.1).

## 9. Le due cose che questa proposta **non** risolve, e vanno dette

**Nessuna regola di Resolution accetta un `layout.table`.** Ogni candidato tabella
esce `unresolved`. Se la tabella passasse dalla porta delle note d'asset non
verrebbe resa — è il difetto che ha ucciso l'opzione «tabella come asset». Qui non
si presenta, perché un nodo `structure` non passa da quella porta: ma **va scritto
nel modello**, o qualcuno riproporrà la porta e la tabella sparirà in silenzio.

**Il paragrafo dalla riga è caduto fuori dalla prosa.** `Criterio_ParagrafoDaRiga_v1.md`
§5 è CADUTO su DB p.99, e la conclusione a verbale è «la regola non è sbagliata:
è sbagliata dove il contenuto non è prosa». Il contenuto di una cella non è prosa.
I paragrafi di `CellIR2` non devono passare da `breaks_paragraph` senza che
qualcuno verifichi cosa succede — rilievo B‑12 della revisione, che nessuna delle
opzioni discusse aveva considerato.
