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
- Python 3.12+;
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

La milestone corrente è:

> **Milestone 8 — contratto document-local di analisi**

La Milestone 7 è la più recente completata; la Milestone 6 resta completata e congelata come baseline diagnostica. Singleton e local-fragment non sono detector affidabili.

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

### Milestone 4 — job/workspace minimo — completata

Sono presenti e approvati:

- `verified_file_model.py`;
- `job_manifest_model.py`;
- `job_manifest_store.py`;
- `job_workspace.py`;
- `job_source_snapshot.py`;
- `job_initializer.py`;
- `job_capture_progress.py`;
- `job_capture_page_update.py`;
- `job_capture_page_store.py`;
- `job_capture_resume.py`;
- `job_capture_phase_summary.py`;
- `job_capture_page_runner.py`;
- relativi test.

Garanzie consolidate:

- snapshot sorgente copiato e verificato;
- manifest JSON minimo e versionato;
- `capture_progress` come unica fonte persistente dello stato capture;
- artifact completed verificati e confinati sotto `raw_dir`;
- resume per pagina basato su digest e dimensione;
- completed invalide non direttamente catturabili;
- manifest pubblicato dopo snapshot verificato;
- runner PyMuPDF single-page;
- nessuna modifica alla pipeline legacy o agli output autorevoli.

Limitazioni da non colmare incidentalmente:

- nessuna atomicità;
- nessun locking o concorrenza;
- nessun reflink;
- nessun reset/riparazione;
- nessun job manager o batch runner;
- nessun containment tramite symlink.

### Milestone 5 — region graph shadow — completata

Sono presenti e approvati:

- contratto `PageAnalysis` schema `1.2`;
- `PageAnalysisProvenance` obbligatoria a livello pagina;
- `LayoutRegion` e `RegionRelation` immutabili;
- validazione cross-model contro `NormalizedPrimitivePage`;
- serializzazione stretta e round-trip JSON-safe;
- store JSON minimale e deterministico per `PageAnalysis`;
- producer strutturali deterministici per root pagina e visible primitive extent;
- stage diagnostico `analysis` in `pymupdf_capture_dump.py`.

Garanzie consolidate:

- identificatori, bbox, endpoint di relazione e riferimenti a primitive validati;
- provenance coerente con la pagina normalizzata;
- regioni contenute nella geometria pagina;
- relazioni strutturali soggette al vincolo acicliche;
- `region:page-root` copre la geometria canonica completa della pagina;
- `region:primitive-extent` usa `structural_kind = layout.primitive_extent` e rappresenta l'unione delle porzioni visibili delle primitive;
- la root riferisce tutte le primitive normalizzate in ordine `text → image → drawing`;
- la extent conserva lo stesso ordine ed esclude solo primitive senza intersezione positiva con la pagina;
- la relazione `layout.contains` collega root ed extent;
- nessun formato pagina nominale è hardcoded;
- primitive parzialmente fuori bordo sono intersecate con la geometria effettiva della pagina;
- il riferimento della stessa primitiva in root ed extent non rappresenta ownership o coverage finale;
- nessuna modifica a pipeline legacy, IR, Markdown, EPUB o renderer.

Ultima verifica consolidata della milestone:

```text
619 test eseguiti
7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

La Milestone 5 non ha introdotto detector reali, marginalia, sidebar semantiche, callout, tabelle, liste, reading order finale, confidence semantica, ownership finale, coverage finale, resolution, profili, IR 2, GUI, AI o SQLite.

### Milestone 6 — marginalia e bande laterali — completata

Obiettivo completato:

```text
NormalizedPrimitivePage
→ PageAnalysis strutturale
→ marginalia/side-band candidate
→ diagnostica shadow
```

La Milestone 6 ha definito il primo vertical slice diagnostico per osservare candidati strutturali di marginalia o banda laterale, mantenendo l'output legacy autorevole; non attesta un detector affidabile o concluso di marginalia.

Micro-step completati:

- Micro-step 1 — contratto `RegionCandidate` — completato;
- Micro-step 2 — misure geometriche per ipotesi testuali — completato;
- Micro-step 3 — ipotesi testuali geometriche singleton — completato;
- Micro-step 4 — rename neutrale delle measurements — completato;
- Micro-step 5 — builder esplicito di candidate side-band — completato;
- Micro-step 6 — producer singleton side-band — completato;
- Micro-step 7 — diagnostica shadow singleton side-band — completato;
- Micro-step 8 — helper privato di raggruppamento local-fragment — completato;
- Micro-step 9 — local-fragment side-band producer — completato.

Sono approvati:

- `RegionCandidate`;
- `PageAnalysis.candidates`;
- schema `1.2`;
- validazione e serializzazione;
- `TextHypothesisMeasurements` e `measure_geometric_text_hypothesis(...)`;
- `GeometricTextHypothesis` e `build_geometric_text_hypotheses(...)`;
- ipotesi singleton ordinate in modo canonico ma non equivalente al reading order;
- `build_side_band_candidate_from_text_hypothesis(...)`;
- builder esplicito da `primitive_ids` a `RegionCandidate(layout.side_band)`;
- `build_singleton_side_band_page_analysis(...)`;
- producer conservativo singleton `layout.side_band`;
- soglie geometriche private, page-relative e tracciate da `configuration_id="singleton-side-band-v1"`;
- `_build_local_horizontal_fragment_hypotheses(...)` privato e side-band-specifico;
- `build_local_fragment_side_band_page_analysis(...)`;
- producer locale separato con candidate `layout.side_band`, anche multi-primitiva;
- provenance locale `page_analysis.local_fragment_side_band`, versione `0.1`, `configuration_id="local-fragment-side-band-v1"`;
- stage diagnostico `analysis-side-band`;
- `dump_singleton_side_band_page_analysis(...)`;
- CLI `--stage analysis-side-band`;
- diagnostica JSON per `PageAnalysis` con candidate singleton side-band;
- nessuna evidence persistita;
- nessuna provenance candidate-level;
- nessun producer generale di candidati.

Stato aggiornato: oltre ai micro-step side-band singleton e local-fragment, sono approvati `PrimitivePairMeasurements`, lo stage `primitive-pair`, l'opzione `--render-page-image`, lo stage `primitive-neighborhood` con coverage ratio diagnostiche, e i producer `layout.page_covering_visual` e `layout.page_edge_visual`.

Il contesto strutturale page-level necessario a interpretare i candidate esistenti è stato affrontato dalla Milestone 7, ora completata. Nessun ulteriore comportamento funzionale è autorizzato senza una decisione architetturale dedicata.

Non sono autorizzati ora producer per visuali interne, `layout.visual_separator`, `layout.interior_visual_frame`, `layout.section_background`, detector generale, clustering, score/confidence/ranking, classificazione `decorative` definitiva, rimozione editoriale o modifiche a IR, Markdown, EPUB e output legacy.

Vincoli permanenti:

- `TextHypothesisMeasurements` misura selezioni esplicite di primitive testuali compatibili;
- `TextHypothesisMeasurements` non classifica side-band;
- `TextHypothesisMeasurements` non produce `RegionCandidate`;
- il builder esplicito side-band non è un detector, non seleziona primitive, non raggruppa, non introduce soglie e non decide l'accettazione;
- il producer singleton side-band produce candidati, non decisioni finali; non riconosce bande laterali complete, non raggruppa primitive, non produce semantica marginalia e non modifica l'output legacy;
- il producer singleton side-band non introduce score, confidence, ranking o evidence;
- il producer local-fragment è separato dal singleton, usa il helper privato locale e può produrre candidate multi-primitiva, ma non introduce score, confidence, ranking o evidence;
- `build_singleton_side_band_page_analysis(...)`, `producer_name="page_analysis.singleton_side_band"` e `configuration_id="singleton-side-band-v1"` restano invariati;
- `analysis-side-band` è diagnostica shadow, non output finale; non modifica lo stage `analysis` esistente, legacy, IR, Markdown o EPUB;
- i JSON diagnostici reali generati durante le prove non devono essere committati;
- eventuali risultati reali servono per decidere il prossimo micro-step, non per attivare comportamento produttivo;
- eventuali cambi alle soglie o alla loro semantica devono cambiare `configuration_id`;
- il producer futuro può usare il builder esplicito, ma la generazione delle selezioni resta una decisione separata;
- `GeometricTextHypothesis` resta il tipo generale per selezioni testuali geometriche;
- il builder corrente di `GeometricTextHypothesis` produce solo singleton;
- non è autorizzato ora un nuovo tipo pubblico `GeometricTextBlock`, `GeometricTextCluster`, `GeometricTextSpan` o equivalente;
- non è autorizzato ora un raggruppatore neutrale pubblico;
- eventuali raggruppamenti multi-primitiva devono restare interni al futuro producer finché non esiste riuso dimostrato;
- il raggruppamento local-fragment approvato resta privato, side-band-specifico e non costituisce un raggruppatore neutrale pubblico;
- l'ordine canonico non è reading order.

Non sono ancora autorizzati:

- clustering generico;
- framework di clustering;
- `ClusterStrategy`;
- `GroupingEngine`;
- `GeometricTextBlock`;
- `GeometricTextCluster`;
- `GeometricTextSpan`;
- registry;
- scoring;
- ranking;
- confidence;
- scanner generale di marginalia;
- produzione generale di candidati;
- detector con soglie non approvate;
- schema `1.3`;
- evidence persistite;
- modifica di `PageAnalysis`;
- semantica marginalia;
- scelta di un detector specifico;
- soglie numeriche non approvate;
- hardcode su Lancer, Fabula, Kult, Vileborn, DB o altri manuali;
- hardcode su pagina, titolo, parola o dimensione carta;
- ingresso diretto dei candidati in IR, Markdown o EPUB;
- modifica dell'output legacy.

Vincoli della milestone:

- un detector produce un candidato, non una decisione finale;
- nessuna primitiva viene rimossa dal contenuto;
- nessuna marginalia viene esclusa automaticamente;
- nessun candidato modifica IR, Markdown o EPUB;
- la pipeline legacy resta autorevole;
- il risultato è diagnostico e reversibile;
- geometria, semantica e disposizione editoriale restano distinte;
- eventuale confidence geometrica non è confidence semantica;
- i formati pagina devono essere trattati tramite coordinate relative o geometria effettiva, non tramite formati nominali.

### Milestone 7 — contesto strutturale page-level — completata

La milestone ha osservato in modo page-local, verificabile e non decisionale il rapporto fra candidate esistenti, primitive visibili e contesto pagina, senza identificare corpo, colonne, tabelle, marginalia, header/footer, callout o decorazioni. Ha completato i contratti puri page-context e candidate ↔ extent con diagnostiche shadow separate; dettagli, semantica e vincoli restano in `State.md`.

Restano esclusi ulteriori CLI o producer, modifiche a `PageAnalysis`, nuovi candidate o structural kind, persistenza, detector, clustering, Resolution, ownership, coverage finale, schema `1.3`, IR, Markdown, EPUB e output legacy, salvo una futura decisione architetturale dedicata.

### Milestone 8 — contratto document-local di analisi

La milestone definisce un contenitore immutabile, puro e versionato per una singola generazione documentale coerente, con riferimenti logici a un massimo di una `PageAnalysis` disponibile per pagina, in ordine sorgente e con pagine mancanti ammesse. Non identifica pattern documentali né introduce semantica, Resolution o decisioni sulle candidate.

Il primo micro-step, non ancora implementato, è limitato a `document_analysis_model.py` e `tests/test_document_analysis_model.py`: modello puro e test sintetici per `DOCUMENT_ANALYSIS_SCHEMA_VERSION = "1.0"`, `PageAnalysisReference`, `DocumentAnalysisProvenance` e `DocumentAnalysis`. Nessun comportamento funzionale, serializzazione, store, filesystem, CLI, diagnostica, relazioni multipagina, detector, modifiche a `PageAnalysis`, schema `1.3`, IR, Markdown, EPUB o pipeline legacy è autorizzato oltre tale micro-step; dettagli e vincoli completi sono in `State.md`.

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
