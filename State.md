# ManReader — Stato progetto

## Versione corrente: v0.7 — migrazione architetturale incrementale

## 1. Decisione di fase

La fase di progettazione globale è conclusa.

La proposta architetturale A-0.2 è stata revisionata criticamente da Chat B e consolidata da Chat A. La direzione target, gli invarianti e l'ordine generale della migrazione sono approvati.

Il progetto entra ora in **Modalità I — implementazione incrementale**.

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

Workspace persistente, resume, invalidazione e pubblicazione atomica restano parte dell'architettura target, ma non sono il primo step implementativo.

L'ordine approvato è:

```text
contratto capture
→ capture shadow reale
→ primitive normalizzate
→ job/workspace minimo
```

Il workspace è infrastruttura di persistenza e non deve entrare nel dominio semantico.

La prima versione del job/workspace dovrà includere soltanto:

- job ID;
- source snapshot;
- manifest minimo;
- directory raw;
- stato della cattura;
- resume per pagina.

Profili complessi, decision log completo, GUI, AI e build gate globale verranno dopo.

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

### Milestone 1 — Contratto minimo di cattura e primitive

Introdurre soltanto modelli dati backend-neutral o backend-descrittivi, senza collegarli alla pipeline.

Scope previsto:

- `PageGeometry`;
- `BackendPageCapture`;
- osservazioni testo/immagine/drawing;
- `TextPrimitive`;
- `ImageOccurrencePrimitive`;
- `DrawingPrimitive`;
- `NormalizedPrimitivePage`;
- test dei modelli.

Vincoli:

- nessuna modifica a `extractor.py`;
- nessuna modifica a `ir_builder.py`;
- nessuna modifica ai renderer;
- nessun nuovo output;
- nessuna dipendenza nuova;
- nessun import PyMuPDF/pdfplumber nei modelli.

### Milestone 2 — Cattura PyMuPDF shadow

Per pagine selezionate:

```text
PDF
→ BackendPageCapture
→ JSON diagnostico
```

La pipeline legacy continua a produrre l'output.

### Milestone 3 — Normalizzazione

```text
BackendPageCapture
→ NormalizedPrimitivePage
```

Verificare coordinate, source reference, identità deterministica e assenza di perdita delle osservazioni richieste.

### Milestone 4 — Job/workspace minimo

Solo dopo la cattura reale:

- source snapshot;
- manifest minimo;
- stato delle fasi;
- resume della cattura.

### Milestone 5 — Region graph shadow

Costruire regioni, relazioni, vincoli e diagnostica senza cambiare output.

### Milestone 6 — Marginalia e bande laterali

Primo vertical slice funzionale, inizialmente limitato a:

- detection;
- region candidate;
- preview/diagnostica;
- decisione esplicita;
- output ancora legacy.

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

## 16. Primo passo operativo

Dopo il commit documentale di `State.md` e `AGENTS.MD`, il primo task implementativo sarà la **Milestone 1 — contratto minimo di cattura e primitive**.

Il task dovrà essere preparato come micro-commit senza collegamento alla pipeline e senza modifica dell'output.
