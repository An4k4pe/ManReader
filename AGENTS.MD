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

Le Milestone 1–29 sono completate.

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
commit `<hash>`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0
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
`<hash>`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note,
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
nel commit `<hash>`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0
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
commit `<hash>`. Baseline verificata: Ruff verde, BasedPyright 0 errori/0
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
moduli diagnostici riusati. Implementato nel commit `<hash>`. Baseline verificata:
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
Implementato nel commit `<94e846d>`. Baseline verificata: Ruff verde, BasedPyright 0
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
