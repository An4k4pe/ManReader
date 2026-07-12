# ManReader — Stato progetto

## Versione corrente: v0.17 — Milestone 6 in corso

## 1. Decisione di fase

La fase di progettazione globale è conclusa.

La proposta architetturale A-0.2 è stata revisionata criticamente da Chat B e consolidata da Chat A. La direzione target, gli invarianti e l'ordine generale della migrazione sono approvati.

Il progetto è in **Modalità I — implementazione incrementale**.

La Milestone 1, la Milestone 2, la Milestone 3, la Milestone 4 e la Milestone 5 sono completate.
La milestone corrente è la Milestone 6 — marginalia e bande laterali.

Stato sintetico delle milestone:

- Milestone 1 — completata;
- Milestone 2 — completata;
- Milestone 3 — completata;
- Milestone 4 — completata;
- Milestone 5 — completata;
- Milestone 6 — corrente.

I primi micro-step della Milestone 6 completati sono:

```text
a7afdc7 Add page-level region candidate contract
a926c7c Add side-band geometric measurements
e25eaa4 Add singleton geometric text hypotheses
32382e1 Update Milestone 6 hypothesis state
0d7f416 Rename text hypothesis measurements
e308fac Add explicit side-band candidate builder
265ca16 Add singleton side-band producer
```

Questo cambio di fase non autorizza una riscrittura generale della pipeline. Ogni modifica deve:

- avere un solo obiettivo verificabile;
- essere prevista dal piano di migrazione;
- mantenere disponibile la baseline legacy;
- distinguere chiaramente percorso legacy, shadow e nuovo percorso;
- avere file ammessi e vietati;
- includere test, diff e stato Git;
- essere committata soltanto dall'utente dopo revisione di Chat A.

La prima fase implementativa non modifica ancora l'output Markdown o EPUB.

## 2. Obiettivo del prodotto

ManReader converte manuali PDF TTRPG in output semantici leggibili, con priorità a Markdown ed EPUB.

Obiettivi permanenti:

- elaborazione locale;
- core utilizzabile senza servizi cloud;
- conservazione del contenuto originale senza invenzioni;
- output verificabile e correggibile;
- supporto sia a PDF digitali sia, in futuro, a scansioni;
- AI/OCR opzionali e separati dal nucleo deterministico;
- profili dei manuali salvabili, importabili e riutilizzabili;
- revisione visuale gestibile anche da un utente non tecnico;
- job riprendibili e decisioni tracciabili;
- stessa IR finale per Markdown ed EPUB.

## 3. Baseline legacy corrente

### 3.1 Pipeline attiva

```text
PDF
→ extractor.py
→ PageData / TextBlock / ImageBlock / VectorBlock / TableBlock
→ ir_builder.py
→ DocumentIR 1.0
→ markdown_builder.py
→ Markdown
```

L'EPUB è ancora parzialmente legacy e non è completamente IR-first.

### 3.2 Responsabilità correnti

- `main.py` — CLI e orchestrazione.
- `config.py` — parametri layout.
- `extractor.py` — accesso PDF, estrazione testo/immagini/vector/tabelle, ricostruzione testo, colonne, reading order, filtro ripetizioni, classificazione asset e dropcap.
- `deduplicator.py` — deduplicazione asset.
- `ir_model.py` — modelli della IR corrente.
- `ir_builder.py` — reading flow finale e parte della classificazione semantica.
- `ir_store.py` — persistenza JSON.
- `ir_validate.py` — validazione IR.
- `markdown_builder.py` — rendering Markdown con alcune decisioni semantiche ancora legacy.
- `epub_builder.py` — rendering EPUB legacy/parzialmente IR.
- `describer.py` — AI locale opzionale tramite Ollama.
- `asset_manager.py` — applicazione post-build delle modifiche da `asset_index.csv`.

`extractor.py` svolge troppe responsabilità, ma non deve essere rifattorizzato in modo ampio prima che i nuovi contratti siano esercitati in shadow mode.

## 4. Baseline da preservare

Restano non-regressione:

- callout region-first sui casi DB verificati;
- supporto a callout affiancati;
- ordine corretto di `MONETE` e `CIMELIO` dopo il fix cross-gutter;
- tabelle preservate nel reading flow e testo tabellare duplicato rimosso;
- classificazione extractor-side `decorative` e `structural`;
- forte riduzione del clutter Markdown;
- immagini readable preservate;
- vector di layout e tabelle filtrati quando riconosciuti;
- dropcap grafici preservati come crop PNG, `role="dropcap"`, `status="unresolved"` e placeholder Markdown;
- nessuna lettera inventata;
- suite completa e smoke DB verdi nell'ultima verifica nota.

Prima di ogni commit operativo verificare almeno:

```bash
git status --short
ruff check <file coinvolti>
basedpyright <file coinvolti>
python -m unittest <test mirati>
python -m unittest
```

Lo smoke DB viene eseguito quando il task può influire sulla pipeline o sui renderer.

## 5. Esito del generalization audit

Il confronto con Fabula, Lancer, Kult e Vileborn mostra che la pipeline corrente generalizza male fuori dai layout simili a DB.

Problemi osservati:

- marginalia e bande laterali entrano nel reading flow;
- liste puntate vengono appiattite;
- procedure numerate grafiche perdono struttura e ordine;
- tabelle reali non vengono riconosciute;
- parti di callout vengono classificate come tabelle;
- box grandi, compositi o drawing-based non vengono ricostruiti;
- una regione semantica non coincide necessariamente con un singolo raster/vector;
- pagine molto grafiche richiedono talvolta una politica editoriale;
- la stessa pagina può combinare più convenzioni e pattern;
- alcune decisioni dipendono dall'utente e non possono essere dedotte dalla sola geometria.

Conclusione:

> Non è realistico affidare tutta la semantica a una singola raccolta di soglie universali.

È invece realistico rendere generali:

- osservazione backend;
- primitive normalizzate;
- geometria;
- relazioni;
- pattern documentali;
- candidati e ambiguità;
- tracciabilità delle decisioni.

## 6. Architettura target approvata

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
→ validazione
→ renderer Markdown / EPUB
```

### 6.1 Livelli distinti

- `BackendPageCapture` — osservazione backend-specifica, serializzabile e versionata.
- `NormalizedPrimitivePage` — primitive canoniche e immutabili.
- `PageAnalysis` — regioni, relazioni, feature, ordine parziale e candidati.
- `DocumentAnalysis` — pattern ricorrenti, continuità multipagina e famiglie suggerite.
- `Resolution` — applicazione di profilo, policy e decisioni.
- `ResolvedSemanticDocument` — documento semanticamente risolto e document-centric.
- `DocumentIR 2` — contratto dei renderer.

### 6.2 Ruolo della pipeline legacy

`PageData` non è raw canonico, perché contiene già ricostruzione, deduplicazione, classificazioni e reading order.

Durante la migrazione può essere usato soltanto come:

- riferimento di non-regressione;
- adapter diagnostico;
- fallback temporaneo;
- sorgente di confronti in shadow mode.

## 7. Invarianti architetturali

### 7.1 Sorgente verificabile

Ogni futuro job deve lavorare su una sorgente immutabile o verificata prima del resume.

Default previsto:

```text
reflink, quando supportato
altrimenti copia
```

La modalità reference-only sarà esplicita.

### 7.2 Raw non modificabile

La cattura backend non viene corretta, filtrata o riscritta dalle fasi successive.

### 7.3 Derivati invalidabili

Ogni artifact derivato deve poter dichiarare input, configurazione, versione e generation ID.

### 7.4 Candidato non definitivo

I confini restano:

```text
primitive normalizzate
≠ layout
≠ candidati
≠ semantica
≠ decisione
```

`LayoutRegion` è un fatto strutturale presente nell’analisi.

`RegionCandidate` è una proposta strutturale non approvata. Un `RegionCandidate` è page-local, usa coordinate canoniche, contiene una bbox e un `proposed_structural_kind`, può riferire primitive della pagina e può avere `primitive_ids=()`. Candidati concorrenti o sovrapposti sono ammessi e possono condividere primitive.

Un `RegionCandidate` non rappresenta ownership, coverage, ranking, confidence, decisione o semantica editoriale.

Un detector produce un candidato. Soltanto la resolution può accettarlo, rifiutarlo o lasciarlo irrisolto.

Un candidato tabella non può rimuovere testo o produrre una tabella finale prima della resolution.

### 7.5 Layout, semantica e politica editoriale separati

Esempio:

```text
structural_kind = layout.side_band
semantic_role = marginalia
editorial_disposition = exclude | note | secondary_content | unresolved
```

`layout.side_band` è strutturale. `marginalia` è un possibile ruolo semantico successivo e non deve essere usato come `structural_kind` o `proposed_structural_kind`.

### 7.6 Coverage e ownership

La coverage è obbligatoria per le primitive che possono trasportare contenuto.

Ogni content primitive deve risultare:

```text
resolved + semantic_content
resolved + excluded
resolved + duplicated_explicitly
unresolved
```

Le support primitive, come bordi, fill, separatori e linee di griglia, possono risultare `layout_evidence` senza diventare contenuto finale.

Una primitiva testuale non può appartenere a più nodi finali salvo duplicazione esplicita e tracciata.

### 7.7 Semantica document-centric

Il layout resta principalmente page-centric.

Il documento semantico e la IR devono supportare nodi con più `source_fragments`, anche su pagine differenti.

La continuità multipagina è inizialmente conservativa:

```text
continuation candidate
→ relation
→ resolution
→ eventuale merge
```

Nessun merge multipagina aggressivo durante le prime milestone.

### 7.8 Renderer IR-only

Markdown ed EPUB devono in futuro consumare soltanto la IR validata.

I renderer non devono riconoscere heading, liste, callout o colonne tramite bbox e font.

### 7.9 AI senza autorità diretta

L'AI locale può proporre decisioni strutturate, ma non modifica raw, profilo o stato risolto senza validazione e accettazione.

## 8. Modelli minimi approvati

### 8.1 Backend capture

Il contratto minimo deve includere:

```text
schema_version
backend_name
backend_version
source_id
page_id
page_geometry
rotation
crop_box
media_box
text_observations
image_observations
drawing_observations
link_observations
annotation_observations
backend_order
errors
```

I dump completi del backend sono opzionali e diagnostici, non parte obbligatoria del contratto canonico.

### 8.2 Primitive normalizzate

Tipi iniziali:

- `TextPrimitive`;
- `ImageOccurrencePrimitive`;
- `DrawingPrimitive`;
- `NormalizedPrimitivePage`.

Le primitive:

- sono immutabili;
- non contengono ruoli semantici;
- non contengono classificazioni `decorative`, `structural`, `table`, `callout` o `marginalia`;
- conservano coordinate canoniche e riferimenti alla cattura.

La primitiva testuale iniziale è una text run o unità osservata stabile, non un paragrafo ricostruito.

### 8.3 Layout region

`LayoutRegion` contiene soltanto dati strutturali:

```text
region_id
generation_id
page_id
bbox
structural_kind
primitive_ids
child_region_ids
features
order_constraints
provenance
geometry_confidence
```

Candidati, alternative semantiche e confidence semantica restano fuori dalla regione.

`RegionCandidate` resta distinto da `LayoutRegion`: è una proposta strutturale page-local non approvata, non una regione accettata e non una decisione editoriale.

### 8.4 IR 2 minima

Prima dei vertical slice che richiedono gerarchia deve essere definito almeno:

```text
SemanticNode
  node_id
  node_type
  role
  children
  source_fragments
  payload
  disposition
  provenance
  metadata
```

Payload iniziali previsti:

- `TextPayload`;
- `ListPayload`;
- `TablePayload`;
- `AssetPayload`;
- `ContainerPayload`.

L'adapter IR 2 → IR 1 è ammesso solo nei casi senza perdita strutturale.

## 9. Profili, archetipi e policy

### 9.1 Separazione

- `DocumentProfile` descrive convenzioni e struttura del documento.
- `EditorialPolicy` descrive le preferenze dell'utente.
- `JobOverrides` contiene eccezioni temporanee.

### 9.2 Profilo v1

La prima versione sarà legata a un fingerprint esatto e supporterà soltanto:

- dimensioni pagina;
- gruppi pagina espliciti;
- layout family;
- edge e colonne ricorrenti;
- orientamenti;
- pattern ripetuti;
- marker conosciuti;
- region pattern;
- reading-order template.

Non sono ancora approvati linguaggi di espressione, profili di famiglia automatici o ereditarietà complessa.

### 9.3 Famiglie e pattern componibili

Una pagina non è descritta da un solo archetipo monolitico.

Può combinare:

```text
layout_family
+ conventions
+ region_patterns
```

Il clustering resta propositivo e non obbligatorio.

## 10. Workspace e job

Il job/workspace minimo è stato implementato e verificato come infrastruttura separata dal dominio semantico.

L'ordine completato è:

```text
contratto capture
→ capture shadow reale
→ primitive normalizzate
→ job/workspace minimo
```

La prima versione implementata include:

- job ID;
- source snapshot copiato e verificato tramite SHA-256 e dimensione;
- manifest JSON minimo, immutabile e versionato;
- percorsi workspace relativi e validati;
- directory raw;
- stato persistente della cattura per pagina;
- artifact raw verificati tramite SHA-256 e dimensione;
- piano di resume che distingue pagine verificabili, pagine da catturare e completed invalide;
- riepilogo derivato della fase capture;
- runner PyMuPDF per una singola pagina.

Il manifest non persiste uno stato globale delle fasi: `capture_progress` è l'unica fonte persistente dello stato della cattura e il riepilogo complessivo viene derivato.

Restano deliberatamente fuori dalla prima versione:

- reflink;
- locking e concorrenza;
- pubblicazione atomica;
- rollback e cleanup automatico;
- reset/riparazione delle completed invalide;
- job manager completo;
- invalidazione generale dei derivati;
- profili complessi;
- decision log completo;
- GUI;
- AI;
- build gate globale.

## 11. GUI, CLI e AI

### 11.1 Core headless

CLI e GUI devono usare gli stessi use case applicativi.

### 11.2 CLI

Deve rimanere utilizzabile per:

- test;
- diagnostica;
- batch;
- automazione;
- esecuzione senza GUI e senza AI.

### 11.3 GUI

La futura GUI minima servirà per:

- elenco e ripresa job;
- pagina con overlay;
- review queue;
- decisione puntuale;
- preview dell'impatto di regole più ampie;
- salvataggio profilo;
- avvio build.

Il framework non è ancora scelto.

### 11.4 AI locale

Resta opzionale e proposal-only.

Non entra nelle prime milestone implementative.

## 12. Piano di migrazione approvato

### Milestone 0 — Baseline e benchmark

- suite corrente;
- smoke DB quando pertinente;
- snapshot IR e Markdown;
- fixture benchmark annotate;
- stato Git noto.

### Milestone 1 — Contratto minimo di cattura e primitive — completata

La milestone ha introdotto modelli dati backend-neutral e immutabili, senza collegarli alla pipeline legacy.

File introdotti:

- `geometry_model.py`;
- `capture_model.py`;
- `primitive_model.py`;
- `tests/test_capture_primitive_models.py`.

Contratti introdotti:

- `PageGeometry` e tipi geometrici condivisi;
- `BackendPageCapture`;
- osservazioni testo, immagine, drawing, link e annotazione;
- `CaptureError` strutturato;
- `DrawingCommand` tipizzato e backend-neutral;
- `TextPrimitive`;
- `ImageOccurrencePrimitive`;
- `DrawingPrimitive`;
- `NormalizedPrimitivePage`.

Decisioni consolidate:

- capture e primitive sono dataclass immutabili;
- le coordinate capture dichiarano unità e sistema di coordinate;
- le primitive usano coordinate canoniche in punti, origine in alto a sinistra e asse Y verso il basso;
- la trasformazione affine usa la convenzione `(a, b, c, d, e, f)` con `x' = a*x + c*y + e` e `y' = b*x + d*y + f`;
- rotazione sorgente e trasformazione applicata restano concetti distinti;
- occorrenza raster e risorsa backend sono separate;
- `resource_ref` resta confinato alla capture;
- ogni primitiva v1 conserva una singola source observation;
- i drawing conservano comandi geometrici tipizzati senza payload PyMuPDF opaco;
- le primitive non contengono ruoli semantici, classificazioni, reading order o decisioni editoriali.

Verifiche di chiusura:

- Ruff verde;
- BasedPyright: 0 errori, 0 warning, 0 note;
- 27 test mirati verdi;
- suite completa: 270 test verdi, incluso smoke DB;
- nessuna modifica alla pipeline legacy, a IR 1.0 o ai renderer.

### Milestone 2 — Cattura PyMuPDF shadow — completata

La milestone ha introdotto un adapter PyMuPDF indipendente dalla pipeline legacy:

```text
fitz.Page
→ pymupdf_capture.py
→ BackendPageCapture
```

File introdotti o estesi:

- `pymupdf_capture.py`;
- `tests/test_pymupdf_capture.py`;
- `tests/test_pymupdf_visual_capture.py`.

Copertura implementata:

- geometria pagina nello spazio di coordinate non ruotato;
- metadati backend e identità della capture;
- text run raw tramite `sort=False`;
- immagini raster come occorrenze distinte dalla risorsa backend;
- drawing vettoriali convertiti in comandi backend-neutral;
- colori, fill, stroke, opacità e trasformazioni quando esposti dal backend;
- errori strutturati senza perdita silenziosa delle altre osservazioni;
- ordine backend conservato soltanto per il testo;
- link e annotazioni presenti nel contratto ma non ancora catturati.

Decisioni consolidate:

- la capture non deriva da `PageData`;
- nessun trim, join, deduplicazione, reading order o classificazione nella capture;
- raster, drawing e testo restano canali osservativi separati;
- due posizionamenti della stessa risorsa raster sono due occorrenze distinte;
- nessun oggetto `fitz.*` entra nel contratto serializzabile;
- dump JSON completi sono diagnostici locali e non vengono committati;
- nessuna modifica a Markdown, EPUB, IR 1 o pipeline legacy.

Benchmark reali verificati:

- Dragonbane: testo, tabelle, dropcap, box e composizioni raster/vector;
- Fabula: callout compositi, tabelle, box chiari/scuri e linee raster sottili;
- l'ordine backend è utile localmente ma non affidabile come reading order globale;
- geometrie, stili e relazioni spaziali sono sufficientemente ricchi per iniziare la normalizzazione.

Ultime verifiche riportate durante la milestone:

- Ruff verde;
- BasedPyright verde dopo il narrowing esplicito degli Optional nei test;
- test mirati verdi;
- suite completa verde;
- pipeline legacy invariata.

### Milestone 3 — Normalizzazione — completata

Obiettivo:

```text
BackendPageCapture
→ NormalizedPrimitivePage
```

Implementazione completata:

- conversione deterministica delle observation testuali, raster e drawing
  nelle primitive già definite;
- coordinate canoniche;
- source reference verificabile;
- identità deterministiche;
- nessuna semantica, classificazione, regione o reading order;
- test sintetici e integrazione reale PyMuPDF;
- dump diagnostico della pagina normalizzata.

Le primitive equivalenti provenienti da canali backend differenti non vengono
fuse. L'eventuale riconoscimento strutturale di linee, separatori, bordi e
support primitive appartiene alle successive milestone di analisi layout.

File introdotti o estesi:

- `primitive_normalizer.py`;
- `tests/test_primitive_normalizer.py`;
- `tests/test_pymupdf_primitive_normalization.py`;
- `pymupdf_capture_dump.py`;
- `tests/test_pymupdf_capture_dump.py`.

Risultato:

```text
BackendPageCapture
→ NormalizedPrimitivePage
```

Garanzie:

- conversione uno-a-uno;
- identità deterministiche;
- source_observation_id conservato;
- coordinate canoniche;
- nessuna fusione;
- nessun reading order;
- nessuna classificazione semantica;
- nessuna modifica alla pipeline legacy.

Limitazioni esplicite:

- solo geometria già in punti/top-left;
- font_flags non convertiti in font_traits;
- link e annotazioni non ancora normalizzati;
- bbox raster degeneri rifiutati;
- nessuna deduplicazione o normalizzazione strutturale.

### Milestone 4 — Job/workspace minimo — completata

La milestone ha introdotto un workspace persistente minimo e verificabile senza collegarlo alla pipeline legacy.

File introdotti o estesi:

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
- relativi test unitari e di integrazione.

Contratti e comportamento implementati:

- `VerifiedFileReference` immutabile con SHA-256 canonico e dimensione;
- `JobManifest` minimo con schema `1.0`, identità, sorgente, workspace e `capture_progress`;
- serializzazione JSON deterministica;
- creazione delle directory del workspace separata dalla pubblicazione del manifest;
- manifest iniziale pubblicato soltanto dopo la copia e verifica dello snapshot;
- stato pagina `pending | completed | failed`;
- completed page con artifact relativo, digest e dimensione obbligatori;
- artifact completed vincolati strettamente sotto `workspace.raw_dir`;
- completamento pagina immutabile e persistenza esplicita;
- resume verificato per digest e dimensione;
- completed invalide separate dalle pagine direttamente catturabili;
- riepilogo derivato `pending | partial | completed | invalid`;
- runner PyMuPDF single-page con artifact JSON deterministico e skip delle completed valide.

Decisioni consolidate:

- `capture_progress` è l'unica fonte persistente dello stato della cattura;
- nessun campo globale `phases` viene persistito;
- lo stato complessivo viene derivato;
- una completed invalida richiede un futuro reset/riparazione esplicito;
- gli artifact orfani non vengono sovrascritti automaticamente;
- nessuna integrazione con la pipeline legacy;
- nessuna autorità sull'output Markdown o EPUB.

Limitazioni esplicite:

- scrittura artifact e manifest non atomica;
- nessun rollback;
- nessun locking o supporto multi-processo;
- nessun controllo di containment tramite symlink;
- nessun reflink;
- nessun reset delle completed invalide;
- nessun batch runner o job manager;
- `page_count` viene fornito al job e verificato dal runner contro il PDF.

Verifiche finali riportate:

- Ruff verde;
- BasedPyright: 0 errori, 0 warning, 0 note;
- suite completa: 403 test eseguiti, 7 skipped;
- `git diff --check` verde;
- pipeline legacy e output autorevoli invariati.

### Milestone 5 — Region graph shadow — completata

La milestone ha introdotto un percorso shadow page-level separato dalla pipeline legacy:

```text
NormalizedPrimitivePage
→ PageAnalysis
→ validazione
→ JSON diagnostico
```

Contratti presenti:

- `PageAnalysis` schema `1.2` con generation ID e page ID;
- `PageAnalysisProvenance` obbligatoria per input normalizzato, producer, versione producer e configurazione;
- `LayoutRegion` immutabile con bbox canoniche, `structural_kind` non semantico e riferimenti a primitive;
- `RegionRelation` immutabile per relazioni strutturali direzionali;
- modelli dataclass immutabili e con slot.

Validazioni implementate:

- identificatori obbligatori e non vuoti;
- bbox finite, non invertite e non degeneri per le regioni;
- regioni contenute nella geometria canonica della pagina nella validazione cross-model;
- riferimenti delle relazioni a regioni esistenti;
- riferimenti delle regioni a primitive esistenti;
- coerenza della provenance con `NormalizedPrimitivePage`;
- divieto di cicli per i grafi strutturali soggetti al vincolo, validati separatamente per relation kind;
- validazione cross-model pura tra `PageAnalysis` e `NormalizedPrimitivePage`.

Serializzazione e persistenza:

- conversione deterministica `PageAnalysis → dict` JSON-safe;
- deserializzazione stretta `dict → PageAnalysis` con rifiuto di chiavi mancanti o sconosciute;
- round-trip del modello, regioni, relazioni e provenance;
- store JSON minimale per `PageAnalysis` con UTF-8, formato deterministico e caricamento validato;
- separazione dagli artifact autorevoli, dal workspace job e dalla pipeline legacy.

Producer strutturali presenti:

- page root:
  - `region:page-root`;
  - `structural_kind = layout.page`;
  - bbox pari alla geometria canonica completa della pagina;
  - riferimenti a tutte le primitive normalizzate nell'ordine `text → image → drawing`.
- visible primitive extent:
  - `region:primitive-extent`;
  - `structural_kind = layout.primitive_extent`;
  - unione delle porzioni delle primitive visibili nella pagina;
  - uso dinamico della geometria della singola pagina, senza assunzioni su A4, Letter, B5 o altri formati nominali;
  - ordine primitive `text → image → drawing` conservato;
  - esclusione soltanto delle primitive senza intersezione positiva con la pagina;
  - nessuna creazione della extent quando nessuna primitiva ha area visibile.

Relazione strutturale prodotta quando la extent esiste:

```text
region:page-root
-- layout.contains -->
region:primitive-extent
```

Il doppio riferimento della stessa primitiva nella root e nella extent non rappresenta ownership semantica, non rappresenta coverage finale ed è soltanto informazione strutturale shadow.

Diagnostica reale:

- `pymupdf_capture_dump.py` supporta gli stage `capture`, `primitives` e `analysis`;
- lo stage `analysis` usa cattura PyMuPDF reale, normalizzazione, costruzione di `PageAnalysis`, validazione e serializzazione;
- Markdown, EPUB, IR e pipeline legacy non vengono modificati.

Verifica reale registrata su Lancer pagina 11, come controllo diagnostico della geometria e non come comportamento hardcoded del prodotto:

```text
page geometry: 612 × 792
root IDs: 109
extent IDs: 109
visible extent:
[54.43199920654297, 3.6800003051757812, 612.0, 792.0]
```

In quel campione alcune primitive oltrepassavano i bordi pagina; la extent usa l'intersezione con la geometria canonica senza perdere gli ID delle primitive che mantengono area visibile positiva.

La Milestone 5 non ha introdotto:

- detector reali;
- marginalia;
- sidebar semantiche;
- callout;
- tabelle;
- liste;
- reading order finale;
- confidence semantica;
- ownership finale;
- coverage finale;
- resolution;
- profili;
- IR 2;
- modifiche a Markdown;
- modifiche a EPUB;
- modifiche alla pipeline legacy;
- GUI;
- AI;
- SQLite.

Criteri di chiusura soddisfatti:

- modelli strutturali presenti;
- validazioni locali, di grafo e cross-model presenti;
- serializzazione e store JSON presenti;
- producer deterministici root ed extent presenti;
- dump shadow su PDF reale presente;
- formati pagina non hardcoded;
- primitive fuori bordo gestite geometricamente tramite intersezione visibile;
- test sintetici e suite completa verdi nell'ultima verifica;
- pipeline legacy invariata.

Baseline globale corrente dopo il primo commit della Milestone 6:

```text
734 test eseguiti
7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

### Milestone 6 — Marginalia e bande laterali — corrente

Obiettivo: definire il primo vertical slice funzionale per identificare candidati strutturali di marginalia o banda laterale mantenendo l'output legacy autorevole.

Pipeline prevista per la milestone:

```text
NormalizedPrimitivePage
→ PageAnalysis strutturale
→ marginalia/side-band candidate
→ diagnostica shadow
```

Il candidato non entra direttamente in IR, Markdown o EPUB.

Micro-step 1 — contratto `RegionCandidate` — completato con:

```text
a7afdc7 Add page-level region candidate contract
```

Sono ora presenti e approvati:

- `RegionCandidate`;
- `PageAnalysis.candidates`;
- schema `PageAnalysis 1.2`;
- validazione locale dei candidate ID, page ID, bbox, kind e primitive IDs;
- validazione cross-model di bbox e riferimenti alle primitive;
- serializzazione stretta e round-trip;
- store compatibile tramite il serializer;
- candidati concorrenti, sovrapposti e con primitive condivise ammessi;
- root ed extent invariati e con `candidates=()`.

Il commit ha inoltre corretto un bug preesistente di discovery in `tests/test_page_analysis_model.py`; il conteggio del modulo è passato da 42 test scoperti a 119 test scoperti. Questa correzione non è una feature della milestone.

Decisione consolidata sulle evidence: nessuna evidence persistita nel primo producer side-band.

Motivazione:

- nessun consumatore concreto richiede ancora evidence persistite;
- nessun bump a `PageAnalysis 1.3`;
- nessun `dict[str, object]` o feature map generica;
- nessuna provenance candidate-level;
- la provenance resta page-level nel primo producer singolo;
- le misure saranno interne, tipizzate, deterministiche e testabili.

La persistenza delle evidence sarà rivalutata soltanto in presenza di un consumatore reale, per esempio composizione multi-producer, resolution basata sulle misure, audit persistente, confronto storico o riproduzione senza rieseguire il producer. Il modello futuro delle evidence non viene progettato ora.

Micro-step 2 — misure geometriche per ipotesi testuali — completato con:

```text
a926c7c Add side-band geometric measurements
```

Il commit storico usava ancora una terminologia side-band-specifica. Il contratto corrente è stato poi rinominato per neutralità terminologica.

Sono ora presenti e approvati:

- `page_analysis_text_hypothesis_measurements.py`;
- `tests/test_page_analysis_text_hypothesis_measurements.py`;
- `TextHypothesisMeasurements`;
- `measure_geometric_text_hypothesis(...)`;
- input come selezione esplicita di `TextPrimitive`;
- bbox visibile aggregata tramite clipping alla pagina;
- rapporti geometrici rispetto alla pagina;
- orientamento compatibile: `direction=None`, direzione circa `(1, 0)` o `(-1, 0)`;
- rifiuto di immagini, drawing, testo verticale/diagonale e primitive invisibili quando selezionate esplicitamente;
- nessun clustering;
- nessuna soglia classificatoria;
- nessuna classificazione `layout.side_band`;
- nessun `RegionCandidate`;
- nessuna modifica a `PageAnalysis`.

Verifiche riportate:

```text
test nuovo modulo: 35
suite completa: 769 test, 7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

Micro-step 3 — ipotesi testuali geometriche singleton — completato con:

```text
e25eaa4 Add singleton geometric text hypotheses
```

Sono ora presenti e approvati:

- `page_analysis_text_hypotheses.py`;
- `tests/test_page_analysis_text_hypotheses.py`;
- `GeometricTextHypothesis`;
- `build_geometric_text_hypotheses(...)`;
- una ipotesi singleton per ogni `TextPrimitive` ammissibile;
- contratto che ammette più `primitive_ids`, ma il primo builder produce solo singleton;
- filtro su sole primitive testuali;
- esclusione di testo verticale e diagonale;
- inclusione di `direction=None` e di direzioni compatibili con l'asse X entro tolleranza `1e-6`;
- clipping usato solo per visibilità e ordinamento;
- ordinamento canonico tramite bbox visibile:

  ```text
  (visible_y0, visible_x0, visible_y1, visible_x1, primitive_id)
  ```

- ordine canonico esplicitamente non equivalente al reading order;
- nessun clustering;
- nessun raggruppamento multi-primitiva;
- nessun misuratore chiamato;
- nessun `RegionCandidate`;
- nessuna modifica a `PageAnalysis`.

Verifiche riportate:

```text
test nuovo modulo: 44
suite completa: 813 test, 7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

Micro-step 4 — rename neutrale delle measurements — completato con:

```text
0d7f416 Rename text hypothesis measurements
```

Il comportamento è invariato: il modulo misura una selezione esplicita di primitive testuali compatibili. Il vecchio nome era troppo specifico perché suggeriva una side-band già riconosciuta; il nuovo nome esplicita che il modulo misura una selezione testuale geometrica esplicita. Il modulo resta privo di clustering, classificazione `layout.side_band` e produzione di `RegionCandidate`. `PageAnalysis` schema `1.2` resta invariato. `State.md` e `AGENTS.MD` sono gli unici file previsti per questo riallineamento documentale.

Micro-step 5 — builder esplicito di candidate side-band — completato con:

```text
e308fac Add explicit side-band candidate builder
```

Sono ora presenti e approvati:

- `page_analysis_side_band_candidate.py`;
- `tests/test_page_analysis_side_band_candidate.py`;
- `build_side_band_candidate_from_text_hypothesis(...)`.

Comportamento:

```text
NormalizedPrimitivePage
+ primitive_ids espliciti
→ measure_geometric_text_hypothesis(...)
→ RegionCandidate(proposed_structural_kind="layout.side_band")
```

Il builder non seleziona primitive, non scansiona la pagina, non chiama `build_geometric_text_hypotheses(...)`, non raggruppa, non introduce soglie e non decide che la candidate sia accettata. La bbox del candidate deriva da `TextHypothesisMeasurements`; `primitive_ids` sono conservati nell'ordine fornito e il `page_id` deriva da `NormalizedPrimitivePage`. Lo schema `PageAnalysis 1.2` resta invariato. Non sono presenti evidence, score, confidence, ranking o provenance candidate-level.

Verifiche riportate:

```text
test nuovo modulo: 11
suite completa: 824 test, 7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

Micro-step 6 — producer singleton side-band — completato con:

```text
265ca16 Add singleton side-band producer
```

Sono ora presenti e approvati:

- `page_analysis_side_band.py`;
- `tests/test_page_analysis_side_band.py`;
- `build_singleton_side_band_page_analysis(...)`.

Comportamento:

```text
NormalizedPrimitivePage
→ build_geometric_text_hypotheses(...)
→ measure_geometric_text_hypothesis(...)
→ filtro geometrico conservativo su singleton
→ build_side_band_candidate_from_text_hypothesis(...)
→ PageAnalysis(schema 1.2, candidates=...)
```

Il producer restituisce una `PageAnalysis` validata e produce zero o più `RegionCandidate(proposed_structural_kind="layout.side_band")`, esclusivamente singleton. I candidate ID sono deterministici e derivati dal `primitive_id`; le bbox sono quelle visibili misurate da `TextHypothesisMeasurements`. Le soglie geometriche sono private, page-relative e tracciate da `configuration_id="singleton-side-band-v1"`. Nel primo micro-step il risultato conserva `regions=()` e `relations=()`.

Il producer non raggruppa primitive, non ricostruisce bande laterali complete, non deduce semantica marginalia e non introduce score, confidence, ranking o evidence. Non modifica `PageAnalysis`, non cambia lo schema `1.2` e non modifica IR, Markdown, EPUB o output legacy.

Verifiche riportate:

```text
test nuovo modulo: 23
suite completa: 847 test, 7 skipped
Ruff verde
BasedPyright: 0 errori, 0 warning, 0 note
git diff --check verde
```

Pipeline interna corrente della Milestone 6:

```text
NormalizedPrimitivePage
→ GeometricTextHypothesis singleton
→ TextHypothesisMeasurements su selezione esplicita
→ explicit side-band candidate builder
→ singleton side-band producer
→ futuro affinamento producer / diagnostica shadow
```

`GeometricTextHypothesis` resta il tipo generale per una selezione testuale geometrica. Non è una side-band, una regione, un candidato persistito, una decisione, una evidence persistita o reading order. Il contratto ammette più `primitive_ids`, ma il builder corrente produce solo singleton.

`TextHypothesisMeasurements` non è evidence persistita, score, confidence, classificazione o candidato.

Decisione su blocchi e raggruppamento: non viene introdotto ora un nuovo tipo pubblico `GeometricTextBlock`, `GeometricTextCluster`, `GeometricTextSpan`, `TextRunGroup` o equivalente. La membership multi-primitiva è il punto non neutrale: la union della bbox è meccanica, ma la scelta delle primitive no.

Un eventuale futuro raggruppamento multi-primitiva non è autorizzato come layer neutrale adesso. Potrà essere un helper privato del futuro producer, dovrà rimanere separato dalla classificazione `layout.side_band`, dovrà essere testato localmente e potrà essere estratto solo se dimostrato riuso da più producer o diagnostica.

Tassonomia sintetica delle bbox:

- bbox meccanica:
  - page root;
  - visible primitive extent;
  - bbox visibile di una singola primitiva.
- bbox di osservazione aggregata:
  - bbox restituita da `TextHypothesisMeasurements` per una selezione fornita dal chiamante.
- bbox di ipotesi strutturale:
  - futura `GeometricTextHypothesis` multi-ID prodotta da una regola di membership.
- bbox di candidato layout:
  - `RegionCandidate` singleton prodotto con `proposed_structural_kind="layout.side_band"`; eventuali candidati multi-primitiva restano futuri.
- bbox semantica o risolta:
  - futuro marginalia semantico dopo resolution.

Prossimo punto autorizzabile: decidere se collegare il producer singleton side-band alla diagnostica shadow `analysis`, oppure prima valutare su campioni reali i candidati generati per stabilire se serva un raggruppamento multi-primitiva privato e side-band-specifico. Il producer singleton è volutamente incompleto: rileva frammenti singleton compatibili con side-band, non regioni marginalia complete.

Il prossimo step non deve ancora includere modifica di `PageAnalysis`, schema `1.3`, evidence persistite, score, confidence, ranking, nuovo tipo `Block/Cluster/Span`, raggruppatore neutrale pubblico, framework di clustering, diagnostica CLI, IR, Markdown, EPUB, output legacy, resolution, coverage, ownership, policy editoriale, profili, GUI o AI.

Vincoli iniziali:

- un detector produce un candidato, non una decisione finale;
- nessuna primitiva viene rimossa dal contenuto;
- nessuna marginalia viene esclusa automaticamente;
- nessun candidato modifica IR, Markdown o EPUB;
- la pipeline legacy resta autorevole;
- il risultato è diagnostico e reversibile;
- geometria, semantica e disposizione editoriale restano distinte;
- eventuale confidence geometrica non è confidence semantica;
- i formati pagina devono essere trattati tramite coordinate relative o geometria effettiva, non tramite formati nominali.

Fuori scope iniziale:

- resolution;
- esclusione automatica;
- policy editoriale;
- ownership finale;
- coverage finale;
- rendering;
- IR 2;
- profili;
- GUI;
- AI;
- tabelle;
- callout;
- liste;
- OCR;
- SQLite;
- refactor generale di `extractor.py`.

### Milestone 7 — Coverage minimo e decisioni

Prima di attivare un nuovo risultato nell'output:

- coverage delle content primitive;
- ownership testuale;
- unresolved;
- decisione puntuale;
- rollback al legacy.

### Milestone 8 — Liste e procedure numerate

Introduce children, marker grafici e primo rendering IR 2.

### Milestone 9 — Profili esatti e policy

Solo quando esistono decisioni reali da riutilizzare.

### Milestone 10 — Tabelle

```text
proposal
→ candidate
→ resolution
→ semantic table
```

### Milestone 11 — Callout compositi e visual panel

La logica DB rimane fallback finché non viene raggiunta equivalenza.

### Milestone successive

- Markdown IR 2;
- GUI minimale;
- AI locale;
- EPUB IR-first;
- ritiro progressivo del legacy.

## 13. Equivalenza e shadow mode

L'equivalenza con la pipeline legacy non richiede JSON identici.

In shadow mode deve significare almeno:

- stesso contenuto testuale conservato;
- stessi asset readable;
- nessuna nuova perdita;
- nessuna nuova duplicazione;
- stesso ordine osservabile nei casi DB stabilizzati;
- callout e tabelle DB preservati;
- differenze registrate e spiegabili;
- suite legacy invariata.

Modalità transitorie:

```text
legacy
shadow
new
```

Lo shadow mode deve avere criteri espliciti di uscita e non diventare una seconda pipeline permanente.

## 14. Attività sospese

Non riaprire salvo regressione bloccante o milestone dedicata:

- fix specifico di `p29_vec2.svg`;
- nuove soglie globali per callout/vector;
- canonicalizzazione asset;
- pulizia fisica delle cartelle output;
- qualità CSV;
- heading;
- crop dropcap;
- EPUB;
- nuove euristiche isolate per Fabula/Lancer/Kult/Vileborn;
- framework GUI;
- AI di calibrazione;
- profili di famiglia;
- structural fingerprint;
- SQLite;
- OCR.

## 15. Workflow corrente

Chat A è ora in Modalità I — implementazione incrementale.

Per ogni task:

```text
Chat A
→ definisce scope e criteri
→ prepara istruzioni per Zed agent o implementazione manuale
→ utente esegue
→ Chat A revisiona diff, test e output
→ utente committa
```

Chat B viene usata quando servono:

- diagnostica indipendente;
- revisione di una decisione architetturale non prevista;
- analisi di regressioni complesse;
- confronto critico su un cambio di direzione.

Zed agent non decide l'architettura e non fa commit.

## 16. Prossimo passo operativo

Il prossimo task implementativo appartiene alla **Milestone 6 — marginalia e bande laterali**.

### Obiettivo iniziale

Il contratto `RegionCandidate`, le ipotesi testuali geometriche singleton, le misure geometriche per ipotesi testuali, il builder esplicito side-band e il producer singleton side-band sono stati introdotti.

Il prossimo punto è decidere se collegare il producer singleton side-band alla diagnostica shadow `analysis`, oppure prima valutare su campioni reali i candidati generati per stabilire se serva un raggruppamento multi-primitiva privato e side-band-specifico.

Il prossimo step deve restare separato da:

- modifica di `PageAnalysis`;
- schema `1.3`;
- evidence persistite;
- score;
- confidence;
- ranking;
- nuovo tipo `Block/Cluster/Span`;
- raggruppatore neutrale pubblico;
- framework di clustering;
- diagnostica CLI;
- modifica a IR, Markdown o EPUB;
- modifica dell'output legacy;
- resolution;
- policy editoriale;
- ownership finale;
- coverage finale;
- profili;
- GUI;
- AI;
- SQLite;
- refactor generale di `extractor.py`.

La Milestone 6 deve restare in shadow mode e produrre dati diagnostici separati.

## 17. Ultimo avanzamento verificato

La Milestone 5 è stata chiusa dopo la sequenza di commit che ha introdotto il contratto `PageAnalysis`, la validazione cross-model, serializzazione e store JSON, producer strutturali deterministici e dump diagnostico `analysis`. I micro-step completati della Milestone 6 includono `a7afdc7 Add page-level region candidate contract`, `a926c7c Add side-band geometric measurements`, `e25eaa4 Add singleton geometric text hypotheses`, `32382e1 Update Milestone 6 hypothesis state`, `0d7f416 Rename text hypothesis measurements`, `e308fac Add explicit side-band candidate builder` e `265ca16 Add singleton side-band producer`.

Commit principali della milestone:

```text
7a3a1d0 Add minimal page analysis contract
9f4e2ff Add structural region relations
4681368 Validate page analysis against primitives
8694779 Add page analysis serialization
15dd2f8 Add page analysis provenance
5a1c2f5 Add page analysis JSON store
5244893 Add page analysis diagnostic dump
6b117b2 Add diagnostic page root region
4d29f3c Extract page root analysis producer
ec3be98 Add visible primitive extent analysis
```

Correzioni finali consolidate:

- schema `PageAnalysis` corrente a `1.2` con provenance obbligatoria e candidati strutturali;
- relazioni strutturali `layout.contains` e `layout.precedes` validate senza dipendere dalla ricorsione Python;
- validazione pura contro `NormalizedPrimitivePage`;
- serializzazione/deserializzazione stretta e store JSON minimale;
- root page region deterministica;
- visible primitive extent calcolata tramite intersezione con la geometria effettiva della pagina;
- stage diagnostico `analysis` in `pymupdf_capture_dump.py`.

Ultime verifiche riportate dopo i micro-step completati della Milestone 6:

- Micro-step 2: test nuovo modulo 35, suite completa 769 test eseguiti, 7 skipped;
- Micro-step 3: test nuovo modulo 44, suite completa 813 test eseguiti, 7 skipped;
- Micro-step 5: test nuovo modulo 11, suite completa 824 test eseguiti, 7 skipped;
- Micro-step 6: test nuovo modulo 23, suite completa 847 test eseguiti, 7 skipped;
- Ruff verde;
- BasedPyright: 0 errori, 0 warning, 0 note;
- `git diff --check` verde;
- pipeline legacy, IR 1, Markdown ed EPUB invariati.

Stato successivo approvato:

```text
Milestone 6
→ GeometricTextHypothesis singleton
→ TextHypothesisMeasurements su selezione esplicita
→ explicit side-band candidate builder
→ singleton side-band producer
→ diagnostica shadow o valutazione su campioni reali
→ nessuna decisione finale o modifica dell'output
→ pipeline legacy autorevole
```
