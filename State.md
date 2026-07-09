# ManReader — Stato progetto

## Versione corrente: v0.12 — Milestone 5 completata

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

Un detector produce un candidato. Soltanto la resolution può accettarlo, rifiutarlo o lasciarlo irrisolto.

Un candidato tabella non può rimuovere testo o produrre una tabella finale prima della resolution.

### 7.5 Layout, semantica e politica editoriale separati

Esempio:

```text
structural_kind = sidebar
semantic_role = marginalia
editorial_disposition = exclude | note | secondary_content | unresolved
```

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

- `PageAnalysis` con schema versionato, generation ID e page ID;
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

Ultima verifica riportata:

```text
619 test eseguiti
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

Il primo micro-step potrà includere soltanto uno dei seguenti livelli, da decidere in un task successivo:

- contratto minimo per un candidato strutturale;
- feature geometriche necessarie al candidato;
- producer shadow di candidati;
- diagnostica separata;
- test sintetici;
- verifica su manuali reali.

Non sono ancora decisi detector, soglie numeriche o euristiche specifiche. Non è autorizzato hardcodare Lancer, Fabula, Kult, Vileborn, DB, pagine, titoli, parole o dimensioni carta.

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

Preparare il primo vertical slice shadow per candidati strutturali di marginalia o banda laterale a partire da `NormalizedPrimitivePage` e `PageAnalysis`, senza modificare output autorevoli.

Il primo micro-step non è ancora scelto. Potrà riguardare soltanto uno dei livelli iniziali autorizzabili:

- contratto minimo per un candidato strutturale;
- feature geometriche necessarie al candidato;
- producer shadow di candidati;
- diagnostica separata;
- test sintetici;
- verifica su manuali reali.

Non deve ancora includere:

- detector definitivo o comportamento hardcoded;
- soglie numeriche non motivate e non diagnostiche;
- esclusione automatica di marginalia;
- modifica o rimozione di primitive dal contenuto;
- modifica a IR, Markdown o EPUB;
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

La Milestone 5 è stata chiusa dopo la sequenza di commit che ha introdotto il contratto `PageAnalysis`, la validazione cross-model, serializzazione e store JSON, producer strutturali deterministici e dump diagnostico `analysis`.

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

- schema `PageAnalysis` corrente a `1.1` con provenance obbligatoria;
- relazioni strutturali `layout.contains` e `layout.precedes` validate senza dipendere dalla ricorsione Python;
- validazione pura contro `NormalizedPrimitivePage`;
- serializzazione/deserializzazione stretta e store JSON minimale;
- root page region deterministica;
- visible primitive extent calcolata tramite intersezione con la geometria effettiva della pagina;
- stage diagnostico `analysis` in `pymupdf_capture_dump.py`.

Ultime verifiche riportate:

- Ruff verde;
- BasedPyright: 0 errori, 0 warning, 0 note;
- suite completa: 619 test eseguiti, 7 skipped;
- `git diff --check` verde;
- pipeline legacy, IR 1, Markdown ed EPUB invariati.

Stato successivo approvato:

```text
Milestone 6
→ candidati strutturali marginalia/side-band
→ diagnostica shadow
→ nessuna decisione finale o modifica dell'output
→ pipeline legacy autorevole
```
