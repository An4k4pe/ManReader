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

Le Milestone 1–17 sono completate. Nessuna nuova milestone è aperta o autorizzata.

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

### Milestone 8 — contratto document-local di analisi — completata

La milestone ha definito un contenitore immutabile, puro e versionato per una singola generazione documentale coerente, con riferimenti logici a un massimo di una `PageAnalysis` disponibile per pagina, in ordine sorgente e con pagine mancanti ammesse. Non identifica pattern documentali né introduce semantica, Resolution o decisioni sulle candidate.

Micro-step completati: il modello puro `DocumentAnalysis`, schema `1.0`, con `PageAnalysisReference` e `DocumentAnalysisProvenance`; e la factory validata di un singolo `PageAnalysisReference`, `build_validated_page_analysis_reference(...)`.

Quando sono disponibili una `NormalizedPrimitivePage` e la relativa `PageAnalysis`, il percorso canonico deve usare `build_validated_page_analysis_reference(...)`: riusa la validazione cross-model e deriva il `page_index` dalla pagina normalizzata, senza riceverlo nuovamente dal chiamante. Non serve un terzo micro-step nella Milestone 8; qualsiasi lavoro successivo richiede l'apertura esplicita di una nuova milestone. L'acquisizione attestata di `page_count`, esclusa dalla Milestone 8, è ora assegnata alla Milestone 9. Restano esclusi builder documentale, descrittori della sorgente, serializzazione, store, filesystem, artifact resolution, manifest, workspace, CLI, diagnostica, relazioni multipagina, detector, Resolution, modifiche a `PageAnalysis`, schema `1.3`, IR, Markdown, EPUB e pipeline legacy.

### Milestone 9 — attestazione della sorgente documentale — completata

La milestone ha definito un'attestazione tecnica locale, pura e immutabile della precisa sequenza di byte verificata, del `source_id` prodotto e del `page_count` letto da quegli stessi byte. Non è firma, autenticità editoriale, certificazione esterna, prova persistente o garanzia futura del path. `source_id` resta opaco nei contratti generali; il producer PDF/PyMuPDF lo deriva internamente dal digest SHA-256 e attribuisce l'autorità di `page_count` al reader applicato agli stessi byte verificati.

Il micro-step completato fornisce `DocumentSourceAttestation`, schema `1.0`, `inspect_verified_bytes(data: bytes) -> VerifiedFileReference` e `attest_pymupdf_document_source(...)`. Il producer legge una sola volta lo `snapshot_path`, confronta digest e dimensione del buffer con `expected_file` prima di PyMuPDF e apre il medesimo buffer verificato; `source_id` deriva dal digest osservato e `page_count` è letto da quegli stessi byte.

La chiusura attesta che il producer canonico PyMuPDF ha acquisito una precisa sequenza di byte dallo snapshot, ne ha verificato SHA-256 e dimensione rispetto al riferimento atteso, ha derivato da essa il `source_id` e ha letto il `page_count` aprendo quegli stessi byte. Non attesta autenticità editoriale, firma, certificazione esterna, futura immutabilità del path, persistenza dell'attestazione, provenance o audit trail persistenti, utilizzo dei byte attestati da parte della capture, né utilizzo da parte di `DocumentAnalysis` o altri consumer.

Non serve un secondo micro-step: contratto e producer soddisfano già l'obiettivo. Un builder verso `DocumentAnalysis` richiederebbe generation ID, provenance, riferimenti pagina, selezione e ordinamento senza rafforzare la garanzia byte–digest–conteggio; l'integrazione nel capture runner è una modifica operativa separata; modifiche a `JobManifest` o `initialize_job(...)` introdurrebbero schema, migrazione, lifecycle e persistenza. Streaming, mmap, locking o file temporanei sono ottimizzazioni rinviabili e devono preservare l'identità degli stessi byte; questa motivazione non è una roadmap implicita.

Restano debiti operativi separati e non bloccanti: il capture runner verifica il file e successivamente riapre il path, conservando una propria finestra TOCTOU; una pagina già completata può essere saltata prima della nuova verifica dello snapshot. Non invalidano la Milestone 9 perché essa non dichiara che la capture utilizzi già l'attestazione; non vanno ulteriormente diagnosticati né ne è autorizzata la correzione.

Restano fuori scope persistenza e serializzazione; provenance del producer nel contratto; audit trail; password per PDF cifrati; producer alternativi; ottimizzazione della memoria per PDF grandi; builder di `DocumentAnalysis`; caricamento o selezione di `PageAnalysis`; manifest e capture integration; artifact resolution; CLI e diagnostica; detector, relazioni multipagina e Resolution; modifiche a `PageAnalysis`; pipeline legacy, IR, Markdown ed EPUB. La Milestone 9 non autorizza ulteriori lavori oltre al proprio contratto e producer completati.

### Milestone 10 — costruzione attestata di DocumentAnalysis — completata

La milestone ha definito un bridge puro e validato per un solo `DocumentAnalysis`: quando è disponibile una `DocumentSourceAttestation`, il percorso canonico ne deriva sia `page_count` sia `DocumentAnalysisProvenance.source_id`, delegando gli invarianti document-local ai modelli esistenti. La garanzia riguarda il percorso costruttivo, non aggiunge campi o prova persistita a `DocumentAnalysis`, che resta un contratto dati di basso livello utilizzabile direttamente.

Il micro-step completato (`20b240b` — `Add attested document analysis factory`) espone `build_attested_document_analysis(...)`: controlla direttamente solo il tipo di `DocumentSourceAttestation`, deriva da essa `page_count` e source ID della provenance, fissa lo schema corrente e delega a `DocumentAnalysisProvenance` e `DocumentAnalysis` tutti gli altri invarianti. Non offre override per source ID, page count, schema o provenance completa; non converte, ordina, seleziona o muta le pagine e non inferisce il conteggio. Il risultato non conserva attestazione, riferimento verificato, digest, path, prova costruttiva o audit trail; un `DocumentAnalysis` isolato non prova il passaggio dalla factory e il costruttore diretto resta disponibile. Restano esclusi modifiche ai modelli esistenti o agli schemi, factory batch/end-to-end, riferimenti pagina, caricamento/selezione/ordinamento automatico di `PageAnalysis`, filesystem/PDF, manifest, workspace, capture runner, persistenza, serializer, store, artifact resolution, CLI, diagnostica, osservazioni o relazioni multipagina, pattern ricorrenti, detector, classificazioni, score, confidence, Resolution, pipeline legacy, IR, Markdown ed EPUB. Nessun ulteriore codice o comportamento è autorizzato prima di una nuova decisione architetturale esplicita.

### Milestone 11 — binding in memoria delle analisi pagina documentali — completata

La milestone ha definito un contratto pubblico, puro, immutabile e validato per associare posizionalmente un `DocumentAnalysis` a tutte e sole le `PageAnalysis` indicate da `DocumentAnalysis.pages`. Il documento può essere parziale rispetto al PDF, ma il binding non può essere ulteriormente parziale.

Il primo e unico micro-step è completato (`5bd634a` — `Add document analysis binding`) in `document_analysis_binding.py` e `tests/test_document_analysis_binding.py`, con `BoundPageAnalysis`, `BoundDocumentAnalysis` e `bind_document_analysis(...)`. I contratti sono pubblici, puri, immutabili, non versionati e validati; il binding è completo rispetto a `DocumentAnalysis.pages`, accetta solo una tuple della medesima lunghezza e associa esclusivamente per posizione. Verifica page ID, schema, generation ID e provenance completa; usa uguaglianza logica per i riferimenti e conserva l'identità degli oggetti ricevuti. Ammette documenti vuoti e documenti parziali rispetto al PDF con gap, ma non carica, cerca, ordina, seleziona o risolve artifact. Non rivalida contro `NormalizedPrimitivePage` né attesta il percorso di costruzione page-local.

La revisione indipendente ha dato verdetto **CHIUDIBILE** senza rilevare difetti bloccanti, controlli identitari mancanti o allargamenti di scope. Non serve un secondo micro-step: l'obiettivo è soddisfatto e i limiti residui sono fuori scope dichiarati, non lacune del binding.

Restano esclusi modifiche ai modelli o schemi esistenti, `NormalizedPrimitivePage`, loader/mapping/lookup/artifact resolution, serializer/store/filesystem, analisi concorrenti, osservazioni o relazioni multipagina, pattern e continuation, candidate↔candidate, detector, classificazioni, score, confidence, ranking, evidence, Resolution, manifest, workspace, capture runner, pipeline legacy, IR, Markdown ed EPUB. Alla chiusura della Milestone 11 non era aperta né autorizzata alcuna milestone successiva.

### Milestone 12 — inventario document-local delle candidate per structural kind — completata

La milestone ha definito il primo consumer puro di `BoundDocumentAnalysis`: descrive la distribuzione osservata dei `RegionCandidate.proposed_structural_kind` in tutte e sole le pagine incluse nel binding, senza interpretare i conteggi come frequenza, ricorrenza, importanza o copertura dell'intero PDF.

Il primo micro-step è completato (`bbe3ea0` — `Add document candidate kind occurrence measurements`): `document_analysis_candidate_kind_measurements.py` e `tests/test_document_analysis_candidate_kind_measurements.py` introducono i contratti pubblici, puri, `frozen=True`, `slots=True`, non versionati e validati `CandidateKindPageCount(page_index, candidate_count)`, `CandidateKindOccurrenceMeasurements(proposed_structural_kind, total_candidate_count, page_counts)` e `DocumentCandidateKindOccurrenceMeasurements(document_page_count, included_page_indices, candidate_kind_occurrences)`, oltre a `measure_document_candidate_kind_occurrences(bound_document_analysis: BoundDocumentAnalysis) -> DocumentCandidateKindOccurrenceMeasurements`.

Tutti gli interi rifiutano `bool`; `page_index >= 0`, `candidate_count > 0`, `total_candidate_count > 0` e `document_page_count >= 0`. Il kind è una stringa non vuota; `page_counts` è una tuple non vuota di elementi corretti, strettamente ordinata per `page_index`, e il totale è la somma dei conteggi page-local. Gli indici inclusi sono interi non negativi, strettamente crescenti e inferiori a `document_page_count`; le occurrence sono del tipo corretto, con kind unici e ordinati lessicograficamente per valore esatto, e ogni indice nei page count è incluso. Pagine incluse senza candidate sono valide, selezioni senza candidate producono aggregazione vuota e kind assenti sono omessi. `included_page_count` è escluso perché derivabile da `len(included_page_indices)`.

La factory accetta esclusivamente `BoundDocumentAnalysis`, deriva conteggio documentale e indici inclusi esattamente dal `DocumentAnalysis` e dai riferimenti del binding, conta tutte e sole le candidate legate una volta per voce, raggruppate per kind esatto e `page_index`, e produce kind lessicografici e distribuzioni in ordine sorgente. Non dipende dall'ordine rappresentativo di `PageAnalysis.candidates`, non muta input e non conserva candidate, candidate ID, bbox, primitive ID o provenance. Documenti parziali, gap e pagine incluse senza candidate restano ammessi; il risultato non descrive automaticamente l'intero PDF né rappresenta frequenza, prevalenza, ricorrenza, affidabilità, coverage, ranking o classificazione. La costruzione diretta valida forma minima e coerenza interna, inclusa soltanto la non-vuotezza del kind; la factory garantisce inoltre che il kind provenga da una `RegionCandidate` già valida, senza importare il validator privato di `page_analysis_model` né duplicarne la regex.

Una occurrence è esclusivamente una singola voce `RegionCandidate` osservata in una `PageAnalysis` inclusa, contata sotto il valore esatto del suo `proposed_structural_kind`; non implica identità cross-page, stesso elemento editoriale, ricorrenza, conferma del kind, indipendenza fra candidate o validità semantica.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti né correzioni funzionali richieste. Il primo e unico micro-step soddisfa l'obiettivo; l'osservazione non bloccante non costituisce un debito obbligatorio o una correzione richiesta.

Restano fuori scope `LayoutRegion`; candidate ID, bbox e primitive ID nel risultato; candidate↔candidate; adiacenza/gap; ratio, percentuali, medie, densità, frequenza, prevalenza, kind dominante e ordinamento per conteggio; pattern, ricorrenza e continuation; classificazione, semantica, score, confidence, ranking, coverage, ownership, Resolution, modifiche a modelli o schemi, pipeline legacy, IR, Markdown ed EPUB. Alla chiusura della Milestone 12 non era aperta né autorizzata alcuna nuova milestone e non era autorizzato nuovo codice, test, diagnostica, persistenza o consumer.

### Milestone 13 — collezione page-local di analisi co-riferite — completata

La milestone ha affrontato la disponibilità osservativa di più `PageAnalysis` co-riferite alla stessa pagina, senza fondere o preferire le correnti. Il primo micro-step è implementato e verificato nel commit `c5bc2f2` — `Add co-referenced page analyses`: `page_analysis_co_reference.py` e `tests/test_page_analysis_co_reference.py` espongono `CoReferencedPageAnalyses` e `build_co_referenced_page_analyses(...)`.

Il contenitore è pubblico, puro, non versionato, `frozen=True`, `slots=True`, con quattro identità page-local esplicite e una tuple non vuota di `PageAnalysis`. Garantisce solo uguaglianza dichiarata di source, capture, pagina, schema primitive e compatibilità rappresentativa dello schema `PageAnalysis`; la chiave interna canonica è `(producer_name, producer_version, configuration_id, generation_id)`. La costruzione diretta richiede ordine strettamente crescente, la factory canonicalizza un input arbitrario e ogni chiave duplicata è rifiutata. Il confronto usa stringhe esatte; correnti di producer, versione, configurazione o generazione differenti possono coesistere. Gli oggetti `PageAnalysis` sono conservati per identità, senza copia, merge, filtro o deduplicazione.

Non garantisce validazione contro una stessa `NormalizedPrimitivePage`, componibilità, semantica, completezza, preferenza, deduplicazione dei contenuti o Resolution; non introduce `page_index`, lookup, conteggi derivati, famiglie di producer o relazioni cross-analysis. Il primo e unico micro-step soddisfa l'obiettivo; la revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità e senza correzioni richieste. Restano fuori scope binding document-local delle collezioni, modifiche a `DocumentAnalysis`/`BoundDocumentAnalysis`, `NormalizedPrimitivePage`, validazione cross-model, lookup o riferimenti cross-analysis, candidate↔candidate, merge, selezione, score/confidence/ranking, coverage/ownership, persistenza, serializer/store/filesystem, manifest/workspace/CLI/diagnostica, nuovi producer, codice o test, pipeline legacy, IR, Markdown ed EPUB. Alla chiusura della Milestone 13 non era aperta né autorizzata alcuna milestone successiva.

### Milestone 14 — binding page-local delle analisi co-riferite alla pagina normalizzata — completata

Il primo micro-step è implementato e verificato nel commit `ca2d631` — `Add co-referenced page analysis binding`: `page_analysis_co_reference_binding.py` e `tests/test_page_analysis_co_reference_binding.py` espongono `BoundCoReferencedPageAnalyses` e `bind_co_referenced_page_analyses(...)`.

Il contratto è pubblico, puro, non versionato, `frozen=True`, `slots=True`, con esattamente `primitive_page: NormalizedPrimitivePage` e `co_referenced_page_analyses: CoReferencedPageAnalyses`. Costruzione diretta e factory riusano `validate_page_analysis_against_primitive_page(...)` per rivalidare individualmente tutte le analisi contro la stessa pagina normalizzata; pagina e collezione sono conservate per identità, mentre identità e ordine canonico delle analisi restano preservati, senza ricostruzione, riordino, filtro, fusione o deduplicazione. Il binding non espone `page_index`; il co-riferimento dichiarativo resta utilizzabile senza pagina normalizzata.

Garantisce soltanto la validità in memoria di ogni corrente rispetto alla stessa pagina e quindi il medesimo namespace page-local effettivo per i `primitive_id`; non prova l'origine storica delle analisi e non è un'attestazione persistente. Il primo e unico micro-step soddisfa l'obiettivo; la revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità e senza correzioni richieste. Restano esclusi equivalenza o conflitto fra correnti, semantica, preferenza, selezione, completezza, bbox rispetto alle primitive, binding document-local, modifiche a modelli/schemi/consumer, lookup o riferimenti cross-analysis, candidate↔candidate, merge, score/confidence/ranking, coverage/ownership, Resolution, persistenza, filesystem, manifest, workspace, CLI, diagnostica, producer, pipeline legacy, IR, Markdown ed EPUB. Alla chiusura della Milestone 14 non era aperta né autorizzata alcuna milestone successiva.

### Milestone 15 — riferimento page-scoped a una candidate di una corrente co-riferita — completata

Il primo e unico micro-step è implementato nel commit `9a4538f` — `Add co-referenced page candidate reference`, in `page_analysis_co_reference_candidate_reference.py` e `tests/test_page_analysis_co_reference_candidate_reference.py`. Baseline funzionale verificata: 1074 test OK, 7 skipped; Ruff canonico sui due file coinvolti verde; BasedPyright canonico: 0 errori, 0 warning, 0 note; `git diff --check` verde; worktree pulito dopo il commit.

`CoReferencedPageCandidateReference` è un valore pubblico, puro, non versionato, `frozen=True`, `slots=True`, con i cinque token esatti `producer_name`, `producer_version`, `configuration_id`, `generation_id`, `candidate_id`, validati come stringhe non vuote senza normalizzazioni. `build_co_referenced_page_candidate_reference(...)` verifica per identità Python che l’analisi appartenga alla collezione conservata nel `BoundCoReferencedPageAnalyses` e che la candidate appartenga all’analisi esplicitamente indicata; `resolve_co_referenced_page_candidate_reference(...)` cerca esattamente la corrente e poi il candidate ID, restituendo l'oggetto conservato per identità. L’analisi è esplicita perché lo stesso oggetto `RegionCandidate` può appartenere a correnti differenti. Non hanno fallback né dipendenza dalla posizione canonica; i riferimenti diretti sono ammessi quando i cinque token corrispondono. Il riferimento non ha identità globale, di pagina o binding, schema persistente né protezione dal cross-binding aliasing; serializer, store e persistenza non sono introdotti.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti, correzioni richieste, scope creep o coupling improprio. Possibili rafforzamenti mutation-oriented non giustificano modifiche; non esiste una ragione concreta per un secondo micro-step.

Restano fuori scope candidate↔candidate, equivalenza, conflitto, merge, selezione, deduplicazione, score/confidence/ranking, coverage/ownership, Resolution, modelli/schemi, producer, consumer, diagnostica, filesystem, manifest, workspace, CLI, persistenza, pipeline legacy, IR, Markdown ed EPUB. La chiusura non autorizza nuovi file, codice, test o una milestone successiva.

### Milestone 16 — misure geometriche page-local fra due candidate co-riferite — completata

L'apertura documentale è `e20e1b2`; il primo e unico micro-step implementato è `89dfb8e` — `Add co-referenced page candidate pair measurements`, in `page_analysis_co_reference_candidate_pair_measurements.py` e `tests/test_page_analysis_co_reference_candidate_pair_measurements.py`. Baseline verificata: 10 test mirati OK, 1084 test complessivi OK e 7 skipped; Ruff verde; BasedPyright 0 errori, 0 warning, 0 note; `git diff --check` verde.

`CoReferencedPageCandidatePairMeasurements` è un valore pubblico, puro, non versionato, `frozen=True`, `slots=True`, con due riferimenti, due bbox, quattro gap/overlap e quattro delta. `measure_co_referenced_page_candidate_pair(...)` risolve entrambi i riferimenti nello stesso `BoundCoReferencedPageAnalyses`, conserva riferimenti e bbox per identità e non applica clipping, normalizzazione, ricostruzione o fallback. Gap e overlap sono simmetrici, i delta (seconda coordinata meno la prima) cambiano segno allo scambio; first/second non esprime priorità. Le misure usano l’unità della `PageGeometry`; il risultato non conserva unit o binding e resta contestuale al binding usato. Costruzione diretta e funzione contestuale restano rispettivamente validazione della forma e percorso canonico.

Sono ammessi stessa corrente o correnti differenti, self-relation, riferimenti identici o logicamente uguali, candidate e ID coincidenti fra correnti, riferimenti diretti risolvibili, primitive vuote/disgiunte/condivise e cross-binding aliasing della Milestone 15. `NormalizedPrimitivePage` impone attualmente `top_left_y_down`; `x0`, `y0`, `x1`, `y1` restano nomi neutrali senza semantica top/bottom e non sono dichiarati binding validi `bottom_left_y_up`.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti, correzioni funzionali richieste, scope creep o coupling improprio. Non esiste una giustificazione concreta per un secondo micro-step. Restano fuori scope equivalenza, matching, conflitto, deduplicazione, selezione, score/confidence/ranking, Resolution, enumerazione, area/unione/IoU/ratio, centri e distanze, booleane e tolleranze geometriche, primitive condivise e relativi dati, diagnostica, consumer, producer, modelli/schemi, serializer/store/filesystem/persistenza, relazioni document-local/cross-page e promozione di helper geometrici privati. La chiusura non apre né nomina una milestone successiva.

### Milestone 17 — flusso diagnostico page-local delle candidate co-riferite — completata

La milestone è completata da `2f80335` (inventario) ed `e817084` (misura di coppia): Ruff verde, BasedPyright 0 errori/0 warning/0 note, 79 test mirati OK, suite completa 1102 OK e 7 skipped, `git diff --check` verde. Entrambe le revisioni indipendenti hanno dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**.

I due adapter read-only, senza nuovi modelli o contratti di dominio, sono `dump_co_referenced_page_candidate_inventory(...)` e `dump_co_referenced_page_candidate_pair_measurements(...)`, con stage `co-referenced-candidate-inventory` e `co-referenced-candidate-pair-measurements`. L'inventario usa `--candidate-producer` e la lista chiusa `singleton-side-band`, `local-fragment-side-band`, `page-edge-visual`, `page-covering-visual`; la misura usa due riferimenti JSON rigorosamente validati tramite `--first-candidate-reference` e `--second-candidate-reference`, esegue solo le correnti implicate, verifica esattamente producer/version/configuration/generation e delega binding, risoluzione e geometria alle API pubbliche delle Milestone 14–16. I dump restano JSON-compatible, effimeri e senza `schema_version`; i riferimenti inclusi rendono il risultato auditabile.

Restano fuori scope persistenza o contratti diagnostici versionati, serializer/store/filesystem/manifest/workspace, autodiscovery o producer fuori lista chiusa, `primitive-extent` come operando candidate, selezione o enumerazione automatica, matching/equivalenza/conflitto/deduplicazione, merge/scelta/preferenza/ranking/score/confidence, Resolution, nuove metriche, modifiche a modelli/schemi/producer/consumer e pipeline legacy, IR, Markdown ed EPUB. La chiusura non autorizza nuovi file, codice, test o una milestone successiva.

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
