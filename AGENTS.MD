# ManReader — Regole per agenti e sviluppo

## Stato corrente

Il progetto è in **Modalità I — implementazione incrementale**, versione di fase v0.22.

L'architettura target e il piano generale di migrazione sono approvati.

La pipeline corrente resta la baseline legacy funzionante e non deve essere rimossa o riscritta finché il nuovo percorso non è stato verificato in shadow mode e i criteri di non-regressione sono soddisfatti.

`State.md` è la fonte aggiornata sullo stato, sulle milestone e sulle decisioni di fase.

## Obiettivo

Convertire manuali PDF TTRPG in Markdown ed EPUB semantici, preservando il contenuto e permettendo:

- revisione visuale;
- profili riutilizzabili;
- decisioni tracciabili;
- job riprendibili;
- AI locale opzionale;
- una IR comune ai renderer.

## Vincoli permanenti

- elaborazione locale;
- nessun servizio cloud obbligatorio;
- Python 3.14.x (versione effettiva in uso e unico target verificato)
  Compatibilità con versioni Python precedenti alla 3.14 non è garantita né richiesta; eventuali pattern che dipendono da comportamenti version-specific di CPython (es. `slots=True` con ereditarietà) vanno verificati sulla 3.14, non assunti portabili;
- dipendenze minime;
- open source preferito;
- compatibilità con PDF digitali e, in futuro, scansioni;
- nessuna invenzione del contenuto mancante;
- output e decisioni verificabili;
- nessun commit automatico;
- output, workspace, dump e diagnostica non committati salvo documento sorgente esplicitamente previsto dal task.

## Toolchain corrente

Core attuale:

- PyMuPDF;
- pdfplumber;
- EbookLib;
- Pillow;
- requests;
- Ollama opzionale.

Qualità:

- Ruff;
- BasedPyright;
- unittest.

Non introdurre nuove dipendenze, framework GUI o storage aggiuntivi senza decisione esplicita di Chat A e motivazione verificabile.

## Ruoli operativi

### Chat A

Chat A è la fonte decisionale.

In Modalità I:

- legge `State.md` e `AGENTS.MD`;
- identifica il livello del problema;
- restringe lo scope;
- stabilisce file ammessi e vietati;
- definisce test e criteri di accettazione;
- prepara il task per Zed agent o per implementazione manuale;
- revisiona diff, test e output;
- decide se accettare, correggere o dividere il task.
- Verifica singola, non duplicata: ruff, basedpyright e la suite test si eseguono una sola volta per task, da chi ha l'ambiente di riferimento (utente o Zed agent). Chat A non ri-esegue autonomamente controlli già riportati, e li considera validi salvo incongruenza esplicita nei dati forniti (es. output contraddittorio, comando diverso da quello richiesto, ambiente non dichiarato). In caso di dubbio, Chat A chiede l'output mancante invece di rieseguire in proprio.

### Chat B

Chat B viene usata per:

- diagnostica indipendente;
- revisione critica di regressioni complesse;
- verifica di ipotesi;
- modifiche architetturali non previste dal piano.

Chat B non decide il commit e non sostituisce Chat A.

### Zed agent

Zed agent:

- esegue soltanto task già definiti;
- modifica solo i file autorizzati;
- non allarga lo scope;
- non sceglie l'architettura;
- non aggiunge dipendenze senza autorizzazione;
- non fa commit;
- mostra diff, test e stato finale.

## Architettura approvata

Pipeline target:

```text
PDF snapshot
→ BackendPageCapture
→ NormalizedPrimitivePage
→ PageAnalysis
→ DocumentAnalysis
→ Resolution
→ ResolvedSemanticDocument
→ DocumentIR 2
→ renderer Markdown / EPUB
```

### Confini obbligatori

```text
osservazione backend
≠ primitive normalizzate
≠ layout
≠ candidati
≠ semantica
≠ politica editoriale
≠ IR
≠ rendering
```

- `PageData` è legacy e non è raw canonico.
- PyMuPDF è il backend principale.
- pdfplumber è un analizzatore specializzato per candidati tabella.
- Asset fisico, occorrenza, regione layout e nodo semantico sono entità differenti.
- Un candidato non entra direttamente nella IR.
- Il layout è principalmente page-centric.
- La semantica e la IR devono supportare provenienza multipagina.
- I renderer non devono reinterpretare il PDF.

## Invarianti da non violare

### Sorgente e raw

- La sorgente di un futuro job deve essere immutabile o verificata prima del resume.
- La cattura backend non viene modificata dalle fasi successive.
- I dump completi del backend sono diagnostici opzionali, non il contratto canonico.

### Primitive

- Le primitive normalizzate sono immutabili.
- Non contengono ruoli semantici.
- Non contengono classificazioni definitive come `decorative`, `structural`, `table`, `callout` o `marginalia`.
- Conservano coordinate canoniche e riferimenti alla cattura.

### Layout e candidati

- `LayoutRegion` è un fatto strutturale dell’analisi e contiene soltanto dati strutturali.
- `RegionCandidate` è una proposta strutturale non approvata.
- `RegionCandidate` non contiene confidence, ranking, ownership, coverage, semantica o decisione.
- `proposed_structural_kind` deve restare strutturale: valori come `layout.side_band` sono ammessi, mentre `marginalia` non è uno structural kind.
- Candidati sovrapposti e concorrenti sono ammessi.
- Le primitive possono essere condivise fra candidati; la condivisione non implica ownership.
- Confidence geometrica e confidence semantica devono essere separate.
- Tabelle, marginalia, callout e liste detector-side sono candidati.
- Un candidato tabella non rimuove testo e non produce CSV definitivo prima della resolution.
- L'isolamento fra producer è una proprietà voluta, non un limite da superare: la relazione fra candidati di producer diversi si decide in Resolution o nel consumer, mai dentro un producer. Fino ai candidati ragionare a pezzi isolati è corretto; dal consumer in poi la combinazione è inevitabile, perché una regione influisce sull'altra.
- Il precedente è ratificato due volte: Milestone 24 (`page_edge_visual`/`side_band`) e Milestone 30 (`interior_visual_frame`/`embedded_visual`, esplicitamente "stesso precedente" di Milestone 24). Milestone 33 ha invece **rinviato** la sovrapposizione banda/`table_candidate`/`embedded_visual` alla futura milestone del producer: è un rinvio, non una ratifica.
- Questione aperta, non ancora un invariante: se un producer possa filtrare i propri candidati per anticipare una decisione del consumer. Il caso che la solleva è `column_band`, che con `too_few_wordy_lines` può accettare come banda la colonna dei numeri di una tabella (misurato su Vil p.223, tabella di dadi) oppure scartarla, a seconda di quanti caratteri portano quei numeri. Una versione precedente di questo bullet citava un esempio diverso, poi **ritirato perché falso** (su DB p.18 il gutter scartato era un rientro sospeso, non una colonna di tabella), e un criterio `too_few_chars` che nel codice non esiste più. Il caso che la complica è `embedded_visual`, già wired, che filtra il proprio output con soglie duplicate localmente da `page_covering_visual` e `page_edge_visual` — alla lettera un filtro su criterio altrui, nello spirito ciò che tiene isolati i due producer. Finché la distinzione fra i due casi non è formulata, la regola non è applicabile e non va trattata come vincolante.

### Coverage e ownership

- La coverage è obbligatoria per le primitive che possono trasportare contenuto.
- Le support primitive possono essere registrate come `layout_evidence`.
- Una primitiva testuale non può appartenere a più nodi finali salvo duplicazione esplicita.
- Nessuna esclusione può essere silenziosa.

### Semantica e IR

- La continuità multipagina viene inizialmente proposta come relation candidate.
- I nodi non vengono uniti automaticamente in modo aggressivo.
- L'adapter IR 2 → IR 1 è ammesso solo nei casi senza perdita.
- Markdown ed EPUB devono progressivamente diventare IR-first.

### AI

L'AI locale può proporre:

- classificazioni;
- associazioni;
- marker;
- anomalie;
- decisioni di review;
- enrichment.

Non deve:

- riscrivere il contenuto estratto;
- generare codice specifico per un manuale;
- creare target inesistenti;
- cancellare file;
- modificare raw o primitive;
- applicare esclusioni irreversibili senza validazione;
- sostituire il profilo persistente.

## Regole operative di implementazione

Per ogni task:

1. Leggere `State.md` e questo file.
2. Confermare la milestone corrente.
3. Definire un solo obiettivo.
4. Elencare file ammessi e vietati.
5. Non allargare lo scope durante l'esecuzione.
6. Non mescolare riorganizzazione e cambio funzionale.
7. Non introdurre hardcode su manuale, pagina, filename, titolo o parola come soluzione primaria.
8. Non usare `git add .`.
9. Non committare automaticamente.
10. Non committare output, workspace, crop, dump o diagnostica.
11. Aggiungere test sintetici per nuovi contratti o regole.
12. Usare benchmark reali per verificare la generalizzazione quando il comportamento diventa attivo.
13. Mostrare diff, test e `git status --short` finali.
14. Se una proposta (Modalità P) asserisce cosa mostrano visivamente delle pagine di un
    manuale, ispezionare quelle pagine prima di progettare la diagnostica attorno a
    quell'assunzione, non dopo (lezione di Milestone 35: la premessa d'origine, mai
    verificata visivamente, si è rivelata fattualmente sbagliata dopo sette giri di
    revisione basati solo sui numeri).
15. Prima di eseguire una misura che deve decidere se una linea di lavoro prosegue,
    registrare per iscritto il criterio di falsificazione — statistica, soglia, ambito,
    esclusioni — e il modello nullo con la sua debolezza dichiarata. Il criterio deve
    vincolare esplicitamente **il caso da cui l'affermazione è nata**, non un caso qualsiasi
    del campione. Lezione della chiusura del contenimento IVF/EV: il criterio registrato
    vincolava Fab e ha prodotto una ritrattazione netta, mentre una lettura post-hoc degli
    stessi identici dati avrebbe dichiarato l'esito positivo su altri due manuali sopra
    soglia. Vale anche per le esclusioni: fissarle prima impedisce di scartare a posteriori
    i casi scomodi.
16. `State.md` termina con una riga sentinella HTML che ne dichiara la fine. Chi lo legge
    deve verificare di averla ricevuta: se non compare, la copia è troncata e va dichiarato
    invece di ragionarci sopra. Lezione della migrazione di Milestone 36: il file aveva
    superato il cap di lettura degli strumenti di fetch, e una sessione ha ragionato per un
    giro intero su una fonte mutilata credendola integra, convinta da tre mirror che
    troncavano allo stesso punto perché passavano dallo stesso strumento.

Verifiche minime per un commit di codice:

```bash
ruff check <file coinvolti>
basedpyright <file coinvolti>
python -m unittest <test mirati>
python -m unittest
git diff --check
git status --short
```

Eseguire lo smoke DB quando la modifica può influire su estrazione, IR o renderer.

## Baseline legacy da preservare

Finché la nuova pipeline non è attiva, restano non-regressione:

- callout DB stabilizzati;
- tabelle DB e filtro del testo duplicato;
- classificazione clutter;
- immagini readable;
- reading order DB, incluso `MONETE`/`CIMELIO`;
- dropcap irrisolti senza invenzione;
- IR 1.0 e Markdown correnti;
- comportamento EPUB legacy non modificato salvo milestone dedicata.

## Stato delle milestone

Le Milestone 1–35 sono completate.

La pipeline legacy, IR, Markdown ed EPUB restano autorevoli; i nuovi contratti restano in shadow mode.

La Milestone 8 resta completata; la Milestone 6 resta completata e congelata come baseline diagnostica. Singleton e local-fragment non sono detector affidabili.

### Stato delle milestone precedenti

La Milestone 1 è completata. Sono presenti e approvati:

- `geometry_model.py`;
- `capture_model.py`;
- `primitive_model.py`;
- `tests/test_capture_primitive_models.py`.

La Milestone 2 è completata. Sono presenti e approvati:

- `pymupdf_capture.py`;
- `tests/test_pymupdf_capture.py`;
- `tests/test_pymupdf_visual_capture.py`.

La capture PyMuPDF copre geometria, text run raw, immagini raster e drawing
vettoriali senza usare i modelli elaborati della pipeline legacy.

La Milestone 3 è completata. Sono presenti e approvati:

- `primitive_normalizer.py`;

- `tests/test_primitive_normalizer.py`;
- `tests/test_pymupdf_primitive_normalization.py`;
- `pymupdf_capture_dump.py`;
- `tests/test_pymupdf_capture_dump.py`.

La Milestone 3 ha prodotto una `NormalizedPrimitivePage` reale a partire da
`BackendPageCapture`, senza cambiare l'output autorevole.

### Milestone 4–19 — sintesi (dettaglio completo in `State_Archive.md`, Parte 2)

- Milestone 4 — job/workspace minimo: `verified_file_model.py`, `job_manifest_model.py`,
  `job_manifest_store.py`, `job_workspace.py`, `job_source_snapshot.py`,
  `job_initializer.py`, `job_capture_progress.py`, `job_capture_page_update.py`,
  `job_capture_page_store.py`, `job_capture_resume.py`, `job_capture_phase_summary.py`,
  `job_capture_page_runner.py`. Snapshot verificato, manifest versionato,
  `capture_progress` unica fonte, resume per pagina, runner PyMuPDF single-page. Nessuna
  atomicità, locking, reflink, reset, job manager o batch runner.
- Milestone 5 — region graph shadow: `PageAnalysis` schema `1.2`,
  `PageAnalysisProvenance`, `LayoutRegion`/`RegionRelation` immutabili, validazione
  cross-model, store JSON, producer `region:page-root`/`region:primitive-extent`, stage
  diagnostico `analysis`.
- Milestone 6 — marginalia e bande laterali: `RegionCandidate`,
  `GeometricTextHypothesis`, producer `layout.side_band` singleton e local-fragment
  (entrambi congelati come baseline diagnostiche, non detector affidabili),
  `PrimitivePairMeasurements`, producer `layout.page_covering_visual`/
  `layout.page_edge_visual`.
- Milestone 7 — contesto strutturale page-level: `CandidatePageContextMeasurements`,
  `CandidateExtentRelationMeasurements`, diagnostiche shadow separate.
- Milestone 8 — `DocumentAnalysis` schema `1.0`, `PageAnalysisReference`,
  `DocumentAnalysisProvenance`, `build_validated_page_analysis_reference(...)`.
- Milestone 9 — `DocumentSourceAttestation` schema `1.0`, `inspect_verified_bytes(...)`,
  `attest_pymupdf_document_source(...)` — lettura byte singola e verificata,
  PyMuPDF-only, chiusa.
- Milestone 10 — `build_attested_document_analysis(...)`: deriva `page_count` e
  `source_id` da una `DocumentSourceAttestation`.
- Milestone 11 — `BoundPageAnalysis`, `BoundDocumentAnalysis`,
  `bind_document_analysis(...)`: binding posizionale completo rispetto a
  `DocumentAnalysis.pages`.
- Milestone 12 — `CandidateKindPageCount`, `CandidateKindOccurrenceMeasurements`,
  `DocumentCandidateKindOccurrenceMeasurements`,
  `measure_document_candidate_kind_occurrences(...)`.
- Milestone 13–19 — infrastruttura page-local per correnti di analisi co-riferite, un
  sottosistema chiuso e mai riesteso da lavoro successivo: `CoReferencedPageAnalyses`/
  `build_co_referenced_page_analyses(...)` (13); `BoundCoReferencedPageAnalyses`/
  `bind_co_referenced_page_analyses(...)` (14); `CoReferencedPageCandidateReference`
  con build/resolve (15); `CoReferencedPageCandidatePairMeasurements`/
  `measure_co_referenced_page_candidate_pair(...)` (16); stage diagnostici
  `co-referenced-candidate-inventory`/`co-referenced-candidate-pair-measurements` in
  `pymupdf_capture_dump.py` (17); `CoReferencedPageCandidatePrimitiveSetMeasurements`/
  `measure_co_referenced_page_candidate_primitive_sets(...)` (18); stage
  `co-referenced-candidate-primitive-set-measurements` (19).

## Milestone 20 - TableCandidateProducer (producer tabelle, configurazione unica `text_lines`) — completata

Tre fasi completate in sequenza: prototipo standalone fuori dal job system che valida il
contratto `RegionCandidate` con candidate pdfplumber (`30d9f4e`); strumento diagnostico
che confronta tre regole geometriche di appartenenza primitiva/candidate su otto blocchi
tabella noti (`62f98f3`), seguito dalla ratifica di `positive_intersection`
(`overlap_ratio > 0`, nessuna soglia) come regola di produzione (`4568276`); producer di
produzione `build_table_candidate_page_analysis` con binding `BoundTableCandidatePage` e
modulo condiviso `measure_candidate_primitive_overlap_ratio`, verificato contro i
conteggi già noti su Dag.pdf p.137 (114/57 primitive) (`e41d10c`).

Punto architetturale verificato in chiusura: nessun producer delle Milestone 13+ è oggi
invocato da alcun modulo `job_*.py` — le uniche invocazioni reali fuori dai test sono in
strumenti diagnostici read-only (`pymupdf_capture_dump.py` e tre file `*_diagnostics.py`).
Questo producer sarebbe il primo, quando verrà wired. L'integrazione nel job/workspace
resta esplicitamente rinviata a una milestone futura, non ancora aperta né numerata.
Baseline finale verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite
completa 1131 test OK e 7 skipped, `git diff --check` verde. Dettagli completi in
`State.md`.

## Milestone 21 - wiring del primo producer nel job (esecuzione runtime, senza persistenza) — completata

Prima infrastruttura generica per eseguire un producer di `PageAnalysis` dentro il job.
`table_candidate` è il primo consumer wired, non l'unico beneficiario dichiarato. Due
moduli nuovi: `pymupdf_pdfplumber_document_source_binding.py`
(`bind_pymupdf_pdfplumber_document_source` → `BoundDocumentSource`, apertura di `fitz` e
`pdfplumber` dallo stesso buffer verificato una sola volta, `ValueError` su mismatch
digest/size/`page_count`) e `job_page_analysis_runner.py`
(`run_job_page_analysis` → `PageAnalysisRunResult`, lista chiusa di producer supportati,
richiede pagina già catturata e risolvibile, riapplica le guardie pagina
`rotation != 0`/`mediabox != cropbox` di Milestone 20 assenti dalla produzione, ricalcola
la capture a runtime invece di leggere l'artifact persistito — nessun deserializzatore di
`BackendPageCapture` esiste in produzione —, nessuna persistenza del risultato).
`job_capture_page_runner.py` resta capture-only, invariato; nessuna modifica a
`CapturePageState`/`CaptureProgress`/`JobManifest`/`WorkspacePaths` né ai contratti
Milestone 20. Verificato contro l'oracolo Dag.pdf p.137 (114/57 primitive) attraverso il
percorso wired. Implementato nel commit `93ee631`. Baseline verificata: Ruff verde,
BasedPyright 0 errori/0 warning/0 note, suite completa 1140 test OK (1131 preesistenti +
9 nuovi) e 7 skipped, `git diff --check` verde. Dettagli completi in `State.md`.

Restano fuori scope, rinviati a milestone future non numerate: persistenza del
`PageAnalysis` prodotto; resume/batch multi-pagina; estensione di `CapturePageState` per
un secondo artifact; wiring di un secondo producer reale; CLI/diagnostica dedicata.

## Milestone 22 - cache opportunistica del PageAnalysis - completata

`job_page_analysis_cache.py` introduce `read_cached_page_analysis`/
`write_page_analysis_cache`, riuso di `page_analysis_store.py` (Milestone 5, mai
collegato prima). Cache non tracciata dal manifest sotto
`job_dir/analysis_cache/<producer_name>/page-NNNN.json`; chiave di validità = i sette
campi di `PageAnalysisProvenance` (non `generation_id`, gestito con `dataclasses.replace`
su hit, senza riscrivere il file); qualunque mismatch o file assente/corrotto degrada al
ricalcolo completo, mai a un errore. `run_job_page_analysis` guadagna
`force_recompute: bool = False`. Nessuna modifica a `WorkspacePaths`/`JobManifest`/
`CapturePageState`/`CaptureProgress`; nessun versionamento della logica di cattura
(solo schema-version esistenti), mitigato con logging esplicito su ogni cache hit, non
risolto. Implementato nel commit `fce90e2`. Baseline verificata: Ruff verde, BasedPyright
0 errori/0 warning/0 note, suite completa 1146 test OK e 7 skipped, `git diff --check`
verde. Dettagli completi in `State.md`.

Restano fuori scope: persistenza tracciata nel manifest; versionamento della logica di
cattura; concorrenza in scrittura; deserializzatore di `BackendPageCapture` (valore
ridotto per `table_candidate`, verificato che le bbox tabella vengano solo da
`plumber_page.find_tables`, mai da `BackendPageCapture`).

## Milestone 23 - wiring del secondo producer nel job (page_covering_visual, apertura selettiva del backend) — completata

Secondo producer wired nel job dopo `table_candidate` (Milestone 21). Trovato e
corretto un mismatch fra la chiave di dispatch del runner e il `producer_name` interno
scritto da `page_analysis_page_covering_visual.py`
(`"page_analysis.page_covering_visual"`), che avrebbe vanificato silenziosamente la
cache Milestone 22 per questo producer. `bind_pymupdf_pdfplumber_document_source`
guadagna `include_pdfplumber: bool = True` (`BoundDocumentSource.plumber_pdf: PDF |
None`); nessuna apertura pdfplumber per i producer che non la richiedono.
`_SUPPORTED_PRODUCERS`/`_producer_cache_identity` sostituiti da `_PRODUCER_SPECS:
dict[str, _ProducerSpec]` (nome interno, versione, configuration_id, necessità di
pdfplumber); il dispatcher di esecuzione resta `if`/`elif`, non giustificato un
registry a interfaccia comune con due soli producer di forma diversa. Implementato nel
commit `3bda611`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0
note, suite completa 1149 test OK (1146 preesistenti + 3 nuovi) e 7 skipped,
`git diff --check` verde. Dettagli completi, inclusa la verifica su manuali reali, in
`State.md`.

Restano fuori scope: CLI/diagnostica dedicata; wiring di un terzo producer;
classificazione decorative/structural delle candidate `page_covering_visual`; un
consumer document-level di ricorrenza per `content_digest`.

## Milestone 24 - wiring del terzo producer nel job (page_edge_visual, ratifica

side_band/page_edge_visual) — completata

Terzo producer wired nel job dopo `table_candidate` (Milestone 21) e
`page_covering_visual` (Milestone 23), stesso pattern (`_PRODUCER_SPECS` +
`elif`, nessuna modifica al binding pdfplumber). Ratificata la relazione fra
`page_edge_visual` e `side_band`: nessuna unificazione a livello di producer
(primitive di tipo diverso, co-occorrenza reale <1% su 5 manuali/1381 pagine); la
relazione resta lavoro futuro di Resolution/consumer secondo l'invariante di
`State.md` ("Resolution è l'unico livello che può accettare, rifiutare o lasciare
irrisolto un candidato"), con nota di design su una futura soglia di magnitudo per
distinguere containment genuino da coincidenza di margine. Implementato nel commit
`27af1ef`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note,
suite completa N test OK (1149 preesistenti + 2 nuovi) e 7 skipped, `git diff --check`
verde. Dettagli completi, inclusa la verifica empirica sui 5 manuali, in `State.md`.

Restano fuori scope: soglia di magnitudo/containment in produzione; quarto producer;
classificazione decorative/structural; consumer document-level di ricorrenza.

## Milestone 25 - diagnostica pura per visuali interne (interior-visual-diagnostics) — completata

Nuovo stage diagnostico, nessun producer: descrive ogni primitivo visivo rispetto
alle soglie esistenti di `page_covering_visual`/`page_edge_visual`
(`is_residual_interior_visual`) più due campi su testo contenuto calcolati
componendo `measure_primitive_pair` (Milestone 6), ispirati nel segnale (non
nell'implementazione) alla classificazione legacy `_asset_is_box_like_text_region`.
Soddisfa la precondizione di `State_Archive.md:133/894` ("osservate con la
diagnostica prima"), che resta in vigore: nessun producer aperto qui. Implementato
nel commit `c5aea29`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0
warning/0 note, suite completa 1157 test OK (1150 preesistenti + 7 nuovi) e 7 skipped,
`git diff --check` verde. Dettagli completi in `State.md`.

Restano fuori scope: producer per visuali interne, wiring nel job, classificazione
decorativo/contenuto, callout/box, elenchi.

## Milestone 26 - diagnostica di clustering geometrico per DrawingPrimitive (drawing-cluster-diagnostics) — completata

Decisione architetturale dedicata che sblocca "clustering" come categoria —
vietata separatamente dalla moratoria "visuali interne" in almeno sei punti di
`State_Archive.md` (righe 117, 135, 160, 228, 894, 921-926, 962), sempre "salvo
una futura decisione architetturale dedicata" (894, 962). Perimetro stretto: solo
`DrawingPrimitive`, solo diagnostica read-only (nessun nuovo tipo pubblico
`Cluster`/`Block`/`Group`/`Span`, nessun `RegionCandidate`, `PageAnalysis`,
`structural_kind`, nessun uso come meccanismo di producer o candidate), nessuna
estensione a `TextPrimitive`/`side_band` o a `ImageOccurrencePrimitive` (già
identificata via `content_digest`). Nuovo stage `drawing-cluster-diagnostics`:
union-find su bbox espanse di un margine esplicito (`cluster_margin`), pre-filtro
esplicito (`min_member_area`, `max_member_page_width/height_ratio`) con
`excluded_reason` non silenzioso, `dispersion_ratio` per cluster. Implementato nel
commit `f3e16cf`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0
warning/0 note, suite completa 1164 test OK (1157 preesistenti + 7 nuovi) e 7
skipped, `git diff --check` verde. Dettagli completi in `State.md`.

Restano fuori scope: producer, wiring nel job, estensione a testo/immagini,
ottimizzazione O(n²), soglie legacy come default definitivo.

## Milestone 27 - producer per visuali interne (embedded_visual, no wiring) — completata

Chiude la precondizione soddisfatta da Milestone 25/26 (`State_Archive.md:133`,
ripetuta 894: "osservate con la diagnostica prima"). Nuovo modulo
`page_analysis_embedded_visual.py`, `build_embedded_visual_page_analysis`, stesso
pattern di `page_analysis_page_edge_visual.py`: riusa invariate
`dump_interior_visual_diagnostics` (Milestone 25) e `dump_drawing_cluster_diagnostics`
(Milestone 26) come funzioni pure. Un solo `structural_kind`, `layout.embedded_visual`,
per raster e vettoriale (nessun consumer oggi dimostra la necessità di due kind
separati, coerente con `State_Archive.md:915`). Punto trovato in revisione Chat B e
risolto prima dell'implementazione:
`dump_drawing_cluster_diagnostics` calcola `is_residual_interior_visual` anche per i
singleton scartati dal pre-filtro di Milestone 26 (`excluded_reason` valorizzato); il
producer filtra esplicitamente su `is_residual_interior_visual is True` e
`excluded_reason is None`, altrimenti ogni frammento vettoriale marginale verrebbe
promosso a candidate. Nessun campo nuovo su `RegionCandidate`, nessuna modifica ai
moduli diagnostici riusati. Implementato nel commit `1701544`. Baseline verificata:
Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite completa 1172 test OK
(1164 preesistenti + 8 nuovi) e 7 skipped, `git diff --check` verde.

Restano fuori scope: wiring nel job, due `structural_kind` separati, campo
document-level su `RegionCandidate` ispirato a `content_digest`, limite di
cardinalità cluster.

## Milestone 28 - wiring del quarto producer nel job (embedded_visual) — completata

Chiude il rinvio esplicito di Milestone 27. Wired `embedded_visual` accanto a
`table_candidate`, `page_covering_visual`, `page_edge_visual`: nuova entry in
`_PRODUCER_SPECS` (`producer_version="0.1"`, `configuration_id="embedded-visual-v1"`,
`requires_pdfplumber=False`), nuovo ramo nel dispatcher `if`/`elif` esistente. Nessuna
modifica al producer (Milestone 27), agli altri producer, alla cache o al binding
documento. Test di simmetria `include_pdfplumber` esteso al quarto producer; nuovo
test end-to-end con cache-hit verificato (bind/capture forzati ad `AssertionError`).
Implementato nel commit `94e846d`. Baseline verificata: Ruff verde, BasedPyright 0
errori/0 warning/0 note, suite completa 1173 test OK (1172 preesistenti + 1 nuovo) e 7
skipped, `git diff --check` verde.

Restano fuori scope: modifiche al producer, parametrizzazione di `cluster_margin`
attraverso il runner.

## Milestone 29 - diagnostica esplorativa per riquadri di testo (box-like interior visual) — completata

Script `scripts/scan_interior_visual_frame_diagnostics.py` committato (a differenza
della prima decisione, corretta in revisione: la base empirica citata va resa
verificabile, stesso standard già applicato ai moduli di Milestone 25/26). Eseguito
su 4 manuali reali (Apo, Dag, DB,
Fab). Segnale (visuale residua + testo contenuto nel range legacy 0,6%-28%) confermato
su contenuto reale (box editoriali, banner di titolo, box statistici affiancati), con
due limiti rilevanti per Milestone 30: sovrapposizione sistematica, non rara, con
`table_candidate` (tabelle a bordo decorativo lette come box); un pattern vettoriale
ricorrente più vicino a `layout.side_band` che a un callout. `contained_text_area_ratio`
può legittimamente superare 1.0 su testo fitto sovrapposto (non un errore).

Restano fuori scope: producer, wiring nel job, distinzione box/tabella/fascia
laterale, soglie di produzione definitive.

## Migrazione e shadow mode

Modalità transitorie:

```text
legacy
shadow
new
```

- `legacy`: produce il risultato corrente.
- `shadow`: calcola il nuovo dato senza cambiare l'output.
- `new`: usa il nuovo percorso per il comportamento approvato.

Lo shadow mode deve avere criteri di equivalenza e una milestone di uscita.

**Stato: la milestone di uscita non esiste.** Verificato su tutto `State.md` e su questo file:
i criteri di equivalenza sono scritti qui sotto, la milestone di uscita non è mai stata
numerata né rinviata esplicitamente. È una decisione aperta e bloccante, registrata in
`State.md` §Stato operativo. Finché resta tale, ogni nuova milestone diagnostica allunga la
distanza dal primo output verificabile della pipeline nuova senza che nessuno abbia deciso
quando quella distanza va chiusa.

L'equivalenza non richiede JSON identici, ma almeno:

- stesso contenuto conservato;
- stessi asset readable;
- nessuna nuova perdita;
- nessuna nuova duplicazione;
- ordine osservabile equivalente sui casi stabilizzati;
- callout e tabelle DB preservati;
- differenze spiegabili.

## Attività non autorizzate senza decisione architetturale dedicata

Non avviare:

- refactor generale di `extractor.py`;
- detector finale o decisione automatica su marginalia e bande laterali;
- esclusione automatica di marginalia;
- hardcode su Fabula, Lancer, Kult, Vileborn, DB o altri manuali;
- hardcode su pagina, titolo, parola o dimensione carta;
- resolution;
- policy editoriale;
- ownership finale;
- coverage finale;
- profili;
- workspace completo;
- job manager completo;
- decision event log;
- IR 2;
- modifica dei renderer;
- GUI;
- AI di calibrazione;
- EPUB IR-first;
- tabelle, callout o liste come nuovo comportamento attivo;
- OCR;
- SQLite;
- nuova struttura completa del repository.

## Aggiornamento documenti

Aggiornare:

- `State.md` a fine milestone o cambio di fase;
- `AGENTS.MD` quando cambiano regole permanenti, milestone o pipeline approvata;
- workflow due-chat solo quando cambiano ruoli e modalità operative.

Regola di processo: qualunque script/modulo che produce un numero o esempio
citato in `State.md` va committato nel repo insieme all'aggiornamento — non
basta che il risultato sia riportato nel testo (regola già praticata da
Milestone 29, resa esplicita qui dopo la sanatoria di Milestone 35,
`ecb5b72`, per tre script rimasti non tracciati da Milestone 24/26).
Gli script sanati sotto questa regola possono contenere etichette di
manuale e numeri di pagina fissati: sono il verbale di cosa e' stato verificato, non
una soluzione, e rimuoverli distruggerebbe la riproducibilita' che la regola cerca.
L'eccezione vale per gli script diagnostici committati in sanatoria, non per il codice
di produzione, dove il divieto di §Regole operative punto 7 resta pieno.

## Milestone 30 - producer per riquadri di testo (layout.interior_visual_frame, no wiring) — completata

Nuovo modulo `page_analysis_interior_visual_frame.py`, sottoinsieme più specifico di
`embedded_visual` (Milestone 27): stesso pattern a due rami, riuso invariato delle
diagnostiche Milestone 25/26, con due assi di filtro aggiuntivi —
`contained_text_primitive_count > 0` e un range esplicito `min_area_ratio`/
`max_area_ratio` (default 0,6%-28%, range legacy verificato su dati reali in
Milestone 29). Un solo `structural_kind`, `layout.interior_visual_frame`. Relazione
con `embedded_visual` = stesso precedente di `page_edge_visual`/`side_band`
(Milestone 24): overlap strutturale accettato (`AGENTS.MD:157`), nessuna
unificazione di contratto. Containment vettoriale via funzione locale portata dallo
script committato di Milestone 29 (`_contains` duplicata: terza istanza reale nel
repo, dopo Milestone 6 e Milestone 7, sotto la soglia per un helper condiviso
secondo `State_Archive.md:143`). Nessun wiring nel job — milestone separata.
Implementato nel commit `16eb91c`. Baseline verificata: Ruff verde, BasedPyright 0
errori/0 warning/0 note, suite completa 1187 test OK (1173 preesistenti + 14 nuovi)
e 7 skipped.

Restano fuori scope: wiring nel job, distinzione box/tabella/fascia laterale
(overlap noto con `table_candidate`/`side_band`, non risolto), deduplica
document-level, soglie di area come default definitivo.

## Milestone 31 - wiring del quinto producer nel job (interior_visual_frame) — completata

Wired `interior_visual_frame` (Milestone 30) accanto a `table_candidate`,
`page_covering_visual`, `page_edge_visual`, `embedded_visual`: nuova entry in
`_PRODUCER_SPECS` (`producer_version="0.1"`, `configuration_id="interior-visual-frame-v1"`,
`requires_pdfplumber=False`), nuovo ramo nel dispatcher `if`/`elif` esistente.
Fixture di test dedicata (`_create_interior_visual_frame_job`, con testo inserito,
a differenza di quella riusata per `embedded_visual`): `interior_visual_frame`
richiede `contained_text_primitive_count > 0` su entrambi i rami, la fixture di
Milestone 28 non lo forniva. Test di simmetria `include_pdfplumber` esteso a 5
producer. Nessuna modifica al producer (Milestone 30), agli altri producer, alla
cache o al binding documento. Implementato nel commit `57f8074`. Baseline
verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite completa 1188
test OK (1187 preesistenti + 1 nuovo) e 7 skipped, `git diff --check` verde.

Restano fuori scope: modifiche al producer; i fili già rinviati al consumer/
Resolution (soglia side_band × page_edge_visual, overlap
interior_visual_frame × table_candidate, dedup `content_digest`, raffinamento
`dispersion_ratio`).

## Milestone 32 - diagnostica esplorativa per struttura colonne (column-structure-diagnostics) — completata

Chiude la moratoria "colonne" di Milestone 7, stessa famiglia di divieto
"clustering" sbloccata con lo stesso schema di Milestone 26 (`State_Archive.md`,
righe 117/135/160-161/228/894/921-926/962). Script
`scripts/scan_column_structure_diagnostics.py` committato nel commit `935556d`:
segmenta le righe di una pagina (overlap verticale delle bbox) in bande
consecutive con conteggio locale di colonne stabile, riportando i gap orizzontali
persistenti per banda. Tre iterazioni (whole-page → persistenza per riga →
bande), ciascuna motivata da un fallimento empirico su DB.pdf/Lan.pdf/Apo.pdf,
non da preferenza. Nessun producer, nessun `RegionCandidate`, nessun wiring.

Cinque confound osservati oltre al segnale di corpo a due colonne reale:
struttura tabellare con colonne interne (sovrapposizione nota con
`table_candidate`), side band di testo, intestazione/piè di pagina a posizione y
fissa (supporto sempre 0.0 o 1.0 per costruzione su bande a una riga), flicker
del conteggio colonne per riga isolata (granularità per-riga, non per finestra).

Decisione presa in chiusura: né `RegionCandidate` singolo né un fatto
page-global scalare descrivono da soli il fenomeno — è una sequenza di regioni
lungo l'asse verticale della pagina. Tre opzioni per una futura milestone di
design dedicata, nessuna scelta qui: nuovo tipo di fatto page-global strutturato;
più `RegionCandidate` per pagina (già ammesso dal contratto esistente, nessun
vincolo di cardinalità in `page_analysis_model.py:107-118`); una combinazione
delle due.

Restano fuori scope: producer, wiring, scelta architetturale fra le tre opzioni,
mitigazione dei cinque confound, soglie di produzione definitive
(`bin_width`/`min_gap_width`/`min_support_ratio`, stesso status di
`cluster_margin`). Verifica Ruff/BasedPyright/test sull'ambiente reale (Python
3.14) da completare come azione dell'utente, non ripetuta esplicitamente dopo le
ultime due riscritture. Nessun test automatico committato per le funzioni dello
script (diagnostico esplorativo, stesso standard di Milestone 25/26/29).

**Milestone chiusa nel commit `935556d`.**

## Milestone 33 - contratto per le bande di colonne (decisione architetturale, no build) — completata

Prende la decisione lasciata aperta in chiusura di Milestone 32: struttura a
colonne rappresentata come `RegionCandidate` minimale per banda
(`proposed_structural_kind="layout.column_band"`) più una misura satellite
pura non ancora scritta (`ColumnBandMeasurements`), stesso pattern di
Milestone 7 (`measure_candidate_page_context`). Nessuna modifica a
`RegionCandidate`/`PageAnalysis`: cardinalità multipla dei candidate già
ammessa senza vincoli (`page_analysis_model.py:199-205`).

Scartate: nuovo tipo di fatto page-global (nessun precedente nel repo, status
epistemico ambiguo); più `RegionCandidate` senza misura satellite (nessun
modo pulito di portare `column_count`/gap senza toccare `structural_kind` o
estendere `RegionCandidate`).

Ordine fra bande ricostruibile da `bbox.y0` (proprietà dell'algoritmo
Milestone 32), non un campo esplicito — distinto dall'interpretazione della
sequenza (transizione reale vs. eccezione locale annidata), non risolta qui.
Riferimento fra candidate (banda vs. `table_candidate`) non passa da
`RegionRelation` (vincolato a `LayoutRegion`, non a `RegionCandidate`). I
moduli satellite di Milestone 7 non vedono un candidato diverso da quello
ricevuto in input, ma il sottosistema Milestone 13-19 (chiuso,
`page_analysis_co_reference*.py`) fornisce già misure geometriche pure fra
due candidate anche di producer diversi sulla stessa pagina
(`measure_co_referenced_page_candidate_pair`). ...Non serve una funzione nuova
nella futura milestone del producer: serve il producer `column_band` e una
politica di decisione (Resolution).

Quattro punti bloccanti rinviati alla futura milestone del producer
`column_band` (non ancora aperta né numerata): trattamento del flicker
per-riga rispetto all'invariante "Resolution è l'unico livello che può
accettare, rifiutare o lasciare irrisolto un candidato" (`State.md:134`);
sovrapposizione banda/`table_candidate`/`embedded_visual`; campi della misura
satellite; `structural_kind` unico vs. distinzione corpo/struttura interna.

Restano fuori scope: producer, wiring, misura satellite effettivamente
scritta, soglie di produzione definitive.

**Milestone chiusa nel commit `e18a4a5`.**

## Milestone 34 - Resolution: design (Modalità P) e prima regola (deduplicazione IVF/EV) — completata

Design in `Proposta_ResolutionDesign_v3.md` (non nel repo, stessa prassi di
Milestone 33), due giri di revisione Chat B integrati, ogni citazione
verificata prima di integrare. E1 (riapertura Milestone 13-19 per una misura
pura di ratio candidato×candidato, dichiarata bloccante nel documento) è
stata sbloccata in discussione diretta Chat A/utente, non messa per iscritto
in un documento dedicato: l'aggiornamento di questo file era stato sospeso
in attesa di testing e non fatto in tempo reale, sanato ora retroattivamente.

Decisione registrata, non presa qui: la duplicazione esatta
`interior_visual_frame`/`embedded_visual` è un caso di Resolution per
applicazione del precedente già ratificato in Milestone 24
(`page_edge_visual`/`side_band`) e confermato in Milestone 30 (docstring di
`page_analysis_interior_visual_frame.py:23-29`, `AGENTS.MD:157-158`).
Nessuna modifica ai due producer.

Commit: `32a3389` (test di sottoinsieme IVF⊆EV, precondizione tecnica del
prototipo — `Proposta_ResolutionDesign_v3.md` §8.2.1), `cc89248`
(`resolution_model.py`/`resolution_page_candidates.py`, prima regola:
identità esatta di primitive fra IVF ed EV → accetta il più specifico,
`reason_token="superseded_by_more_specific"`), `9368a5c` (riapertura
Milestone 13-19: `page_analysis_co_reference_candidate_overlap_ratio_measurements.py`,
overlap_area / min(area1, area2) — E1 soddisfatta), `ba94a34` (script
standalone `scripts/prototype_resolve_page_candidates_real_pages.py`,
esecuzione su pagine reali non ancora revisionata).

Fuori scope, invariato dal documento: `§8.2.2` (`layout.table` × IVF/EV,
tabelle a bordo decorativo) resta da fare — E1 sblocca il sottosistema di
misura, non fornisce ancora evidenza sufficiente per una regola su quella
coppia (vedi Milestone 35).

**Milestone chiusa nei commit `32a3389`..`ba94a34`.**

## Milestone 35 - diagnostica di clustering vettoriale: filtro mancante, colore, frequenza — completata

Design in `Proposta_Milestone35_ClusteringColorDiagnostics_v1..v10.md` e `Chiusura_Milestone35.md`
(non nel repo), sette giri di revisione Chat B. Premessa di origine (quattro pagine Lancer lette
come pannelli decorativi impilati) falsificata per ispezione visiva diretta: tre sono box di
regole/stat-block, una è sfondo di tabella. Le quattro misure previste (area/testo/colore) non
discriminano su 80 cluster target in 7 manuali; `dispersion_ratio` esclusa come soglia operativa
dopo verifica sul controesempio Kul p.169/167. Nessuna milestone di clustering per colore si apre.
Test di fattibilità sul rilevatore di callout della pipeline legacy (`ir_builder.py`): 7/9 casi
corretti, candidato per un futuro producer, non deciso qui.

**Milestone chiusa in `2fda096`.**

Lavoro esplorativo successivo alla chiusura, registrato in `State.md` e senza milestone aperta:
otto ipotesi di discriminazione arredamento/contenuto falsificate in sequenza, tutte con la
stessa firma (separano dentro un manuale, non fra manuali). Regge un solo criterio, la forma
page-local (lato minore in punti sul corpo stimato dalla moda delle `font_size` della pagina,
incrociato col rapporto d'aspetto): precisione alta su 72 celle a campionamento casuale in tre
manuali, zero contenuto catturato, copertura parziale, modo di fallire conservativo, non
estendibile con una soglia unica. L'ottava — contenimento
`interior_visual_frame ⊃ embedded_visual`, l'unica relazione che `State.md` indicasse come da
guardare per prima — è caduta contro criterio pre-registrato: 1,94×/1,24× su Fab contro una
barra di 3×, e il 40,6% d'origine si è rivelato prodotto per il 90% da due pagine su quaranta.
