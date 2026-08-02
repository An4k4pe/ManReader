# ManReader — Stato progetto

## Versione corrente

**v0.22** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–35 sono completate. Cinque producer Milestone 13+ sono wired nel job:
`table_candidate` (Milestone 21, commit `93ee631`), `page_covering_visual`
(Milestone 23, commit `3bda611`), `page_edge_visual` (Milestone 24),
`embedded_visual` (Milestone 27, wired in Milestone 28) ed `interior_visual_frame`
(Milestone 30, wired in Milestone 31).
`run_job_page_analysis` ha una cache opportunistica non tracciata dal manifest
(Milestone 22, commit `fce90e2`) e apre selettivamente il
backend pdfplumber solo per i producer che lo richiedono (Milestone 23).
Restano rinviate a milestone future non ancora aperte né numerate: persistenza tracciata del
`PageAnalysis` prodotto, resume/batch multi-pagina, estensione di `CapturePageState`
per un secondo artifact, un consumer document-level di ricorrenza per `content_digest`
(vedi appunto sotto).

Milestone 24 ha ratificato la relazione fra `layout.page_edge_visual` e
`layout.side_band` (singleton e local-fragment): restano due producer indipendenti,
nessuna unificazione di contratto — operano su primitive di tipo diverso (`text` vs.
`image`/`drawing`) e la co-occorrenza reale è rara (<1% delle pagine su 5 manuali
interi testati, 1381 pagine). La relazione resta lavoro futuro di Resolution/consumer
(invariante `State.md`: "Resolution è l'unico livello che può accettare, rifiutare o
lasciare irrisolto un candidato"), con una nota di design: quando quel lavoro verrà
aperto, distinguere contenuto reale (es. testo di intestazione capitolo contenuto in
una fascia decorativa) da coincidenza di margine (overlap geometrico presente ma di
magnitudo trascurabile, es. un bullet decorativo che sfiora il bordo di uno sfondo)
richiederà una soglia sul rapporto fra overlap e dimensione del candidato più piccolo,
non un booleano overlap/disjoint — coerente con la scelta di Milestone 16 di non
esporre containment/ratio in `measure_co_referenced_page_candidate_pair`.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
`layout.page_covering_visual` non distingue geometricamente sfondo ripetuto da
illustrazione unica (regola page-local, nessuna visibilità sul documento). Verificato su
tre manuali reali: `ImageOccurrencePrimitive.content_digest` (già in
`primitive_model.py`, popolato da `pymupdf_capture.py`/`primitive_normalizer.py` via
`get_image_info(hashes=True)`) permette di raggruppare le candidate per identità di
contenuto — digest su decine/centinaia di pagine (spesso a passo 2) è sfondo; digest su
una pagina, o poche non sistematiche, è candidato a illustrazione unica. Un futuro
consumer document-level nello stile di `measure_document_candidate_kind_occurrences`
(Milestone 12), raggruppato per `content_digest`, non richiederebbe modifiche di schema
per il caso immagine. `DrawingPrimitive` non ha invece alcun campo di identità
(`primitive_model.py`): non bloccante nei tre manuali testati, perché lo sfondo
ricorrente è sempre risultato un'immagine raster; le candidate `drawing` erano rare,
concentrate su coppie di pagine adiacenti, coerenti con spread illustrativi doppi.

**Sanatoria (Milestone 35, retroattiva)**: gli script che hanno prodotto la verifica sopra
(`verify_page_covering_visual_content_digest_recurrence.py`, tre manuali) e la sua
controparte per `page_edge_visual` (`verify_page_edge_visual_content_digest_recurrence.py`,
stesso approccio, i suoi numeri non sono riportati in questa nota) non erano stati
committati all'epoca — trovati non tracciati durante il riordino di Milestone 35,
committati ora in `ecb5b72`.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
il progetto originale (pipeline legacy) distingueva già immagini raster e vettoriali
(`ImageBlock`/`VectorBlock`, `extractor.py`). Potrebbe essere utile, in un futuro
non immediato, permettere di salvare le immagini raster estratte in alta qualità o
di preferire un'estrazione vettoriale quando disponibile, invece della sola
rasterizzazione attuale. Nessuna decisione presa, nessun impatto sul lavoro corrente.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
la verifica su manuali reali di Milestone 26 (`dump_drawing_cluster_diagnostics`)
mostra che `dispersion_ratio` basso ha due cause strutturalmente opposte,
indistinguibili senza ispezione visiva. Su Kul p.169/p.167 un'unica illustrazione
xilografica densa (fregio floreale di apertura capitolo) viene frammentata dal
clustering in piu' cluster separati (margine 5pt insufficiente a riunirla): dispersion
bassa per spazio negativo naturale dell'incisione, non per errore di fusione. Su DB
p.125 (scheda personaggio) decine di piccole icone decorative non correlate (diamanti
di spunta accanto a ogni abilita', fregi a nastro) vengono invece incatenate in un
unico cluster nominale da 68 membri via transitivita' del union-find, coprendo quasi
l'intera pagina: qui la dispersion bassa segnala un vero bridging fra elementi
scollegati. Una soglia fissa uniforme su `dispersion_ratio` non basta a separare i due
casi; un eventuale raffinamento futuro (parametro sul margine, limite sulla lunghezza
della catena, o altro) andrebbe informato da altri esempi reali, non solo da questi
due. Nessuna decisione presa, nessun impatto sul modulo Milestone 26 (resta
diagnostica pura, corretta per lo scopo dichiarato).

La pipeline legacy, IR, Markdown ed EPUB restano autorevoli. I nuovi contratti lavorano in shadow mode e non producono ancora decisioni editoriali, IR o output finale.

## Pipeline legacy e baseline da preservare

Pipeline attiva:

```text
PDF
→ extractor.py
→ PageData / TextBlock / ImageBlock / VectorBlock / TableBlock
→ ir_builder.py
→ DocumentIR 1.0
→ markdown_builder.py
→ Markdown
```

L'EPUB resta legacy/parzialmente IR-first. Restano non-regressione:

- callout DB region-first e callout affiancati;
- tabelle DB e rimozione del testo tabellare duplicato;
- reading order DB stabilizzato, incluso `MONETE`/`CIMELIO`;
- immagini readable e classificazione clutter `decorative`/`structural`;
- dropcap unresolved senza invenzione di testo;
- IR 1, Markdown corrente ed EPUB legacy invariati.

`PageData` è legacy, non raw canonico: può servire solo come riferimento di non-regressione, adapter diagnostico o fallback temporaneo.

## Architettura target approvata

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

Confini invarianti:

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

- Raw e primitive normalizzate sono immutabili; i derivati dichiarano input, configurazione, versione e generation ID.
- `LayoutRegion` è un fatto strutturale; `RegionCandidate` è una proposta page-local non approvata, non ownership, coverage, ranking, confidence o decisione.
- `layout.side_band` è strutturale; `marginalia` è un possibile ruolo semantico successivo.
- Resolution è l'unico livello che può accettare, rifiutare o lasciare irrisolto un candidato.
- Nessuna esclusione o rimozione di contenuto è silenziosa. Markdown ed EPUB dovranno consumare IR validata, non reinterpretare il PDF.

## Milestone completate — sintesi

Milestone 1–5 completate. Hanno consolidato:

- capture backend-neutral e primitive normalizzate canoniche;
- adapter PyMuPDF shadow, normalizzazione deterministica e dump diagnostici locali;
- workspace/job minimo: snapshot verificato, manifest versionato, capture progress e resume per pagina;
- `PageAnalysis` schema `1.2`, provenance page-level, validazione cross-model, serializzazione e store JSON;
- producer root pagina e visible primitive extent, più diagnostica shadow `analysis`.

I dettagli storici di file, test e commit sono disponibili nei commit precedenti e nelle versioni pregresse di `State.md`.

Milestone 6–19 completate. Dettaglio narrativo completo spostato in `State_Archive.md`
(Parte 1) — non necessario per le decisioni correnti, i contratti restano vigenti e
descritti in forma permanente in `AGENTS.MD`. Hanno consolidato, in ordine:

- Milestone 6: candidate `layout.side_band` (producer singleton e local-fragment,
  entrambi congelati come baseline diagnostiche, non detector affidabili) e un primo
  substrato geometrico page-local puro (`PrimitivePairMeasurements`,
  `measure_primitive_pair`, stage diagnostici `primitive-pair`/`primitive-neighborhood`,
  producer `layout.page_covering_visual` e `layout.page_edge_visual`);
- Milestone 7: misure page-local pure e non decisionali fra candidate esistenti e
  primitive non-candidate (`CandidatePageContextMeasurements`,
  `CandidateExtentRelationMeasurements`), senza identificare corpo pagina, colonne,
  tabelle o marginalia;
- Milestone 8: contratto `DocumentAnalysis` — contenitore document-local immutabile,
  puro e versionato, al più una `PageAnalysis` per pagina, documenti parziali ammessi;
- Milestone 9: `DocumentSourceAttestation` e `attest_pymupdf_document_source` — identità
  verificata di una precisa sequenza di byte, `source_id` e `page_count` letti dagli
  stessi byte, PyMuPDF-only;
- Milestone 10: costruzione attestata di `DocumentAnalysis` a partire
  dall'attestazione di Milestone 9;
- Milestone 11: `BoundDocumentAnalysis` — binding in memoria, per identità, delle
  `PageAnalysis` di un documento;
- Milestone 12: inventario document-local delle candidate per structural kind;
- Milestone 13–19: infrastruttura page-local per correnti di analisi co-riferite —
  collezione (`BoundCoReferencedPageAnalyses`, Milestone 13), binding alla pagina
  normalizzata (Milestone 14), riferimento page-scoped a una candidate
  (`CoReferencedPageCandidateReference`, Milestone 15), misure geometriche fra due
  candidate co-riferite (Milestone 16), flusso diagnostico (Milestone 17), misure degli
  insiemi di primitive referenziate (Milestone 18) e diagnostica delle relazioni fra
  quegli insiemi (Milestone 19) — un sottosistema chiuso, non esteso da lavoro
  successivo alla sua chiusura.

## Milestone 20 — TableCandidateProducer (producer tabelle, configurazione unica `text_lines`) — completata

Chiude un filone di progettazione Modalità P condotto in una sessione separata (documento
`Proposta_TableCandidateProducer_v5.md`, versioni v1→v5, con revisione Chat B integrata),
fin qui non riflesso come milestone numerata. Il documento non è incluso nel repo: è
un'analisi offline su un dump pdfplumber già estratto, non un contratto di codice; la
sintesi utile alle decisioni è qui. La baseline funzionale resta quella di chiusura della
Milestone 19 (`b1548e7` — "Close milestone 19 co-referenced page candidate primitive set
diagnostics").

Obiettivo: introdurre un `TableCandidateProducer` che rilevi tabelle a livello di singola
pagina ed emetta `RegionCandidate` coerenti col contratto delle Milestone 13+.

Decisioni ratificate in Modalità P (dettaglio quantitativo completo nel documento di
progettazione, consegnato separatamente):

1. `text_lines` è l'unica configurazione del producer; la configurazione `default`
   (line-based) è **eliminata**, non derubricata a fallback. Verificato con analisi
   quantitativa su un dump di 3946 record grezzi (7 manuali) e poi con ispezione visiva
   diretta dell'utente su tutte le 35 pagine dove `default` rilevava tabelle non vuote
   assenti da `text_lines`: nessuna delle 35 (100% del campione, incluso il caso incerto
   Apo.pdf p.16) è una tabella reale — sono sfondi decorativi di apertura capitolo,
   copertine, illustrazioni o bande/titoli laterali.
2. La deduplicazione cross-config non è un requisito del producer. Una stesura precedente
   dello stesso thread l'aveva definita obbligatoria (senza di essa il 65.9% delle tabelle
   del corpus sarebbe emerso come candidate duplicate), ma quel calcolo presupponeva
   entrambe le configurazioni attive. Con `default` eliminato non c'è più nulla da
   riconciliare fra configurazioni: verificato che `text_lines` da sola non produce mai
   duplicati sulla stessa pagina in tutto il corpus (0 casi su 1170 record non vuoti, 251
   pagine con più record).
3. Il pattern "≥3 blocchi affiancati sulla stessa pagina" è raro e confermato tale su
   dataset completo (3 casi su 1241 tabelle fisiche, 7 manuali): non giustifica una logica
   di clustering same-page generale nel producer.
4. Il pattern di continuazione multi-pagina (2 blocchi per pagina, numerazione continua)
   esiste ed è confermato su un caso reale verificato end-to-end (Dag.pdf p.136-137, offset
   di pagina PDF→stampata +2). La frequenza generale nel corpus non è quantificata (207
   pagine candidate, 44 run multi-pagina, un solo caso verificato manualmente): non blocca
   la decisione producer/configuration_id, ma resta fuori scope per il primo micro-step.

Rinviabili portati esplicitamente alla fase di implementazione (non richiusi da questa
progettazione):

- `text_lines` sottostima l'area reale della tabella in almeno un caso, confermato non più
  solo sospettato: il blocco sinistro di Dag.pdf p.137, rilevato raw (senza merge) dal
  prototipo, ha bbox x 72.5–234.6 (~162pt) — sensibilmente più stretta di quella riportata
  in `Proposta_TableCandidateProducer_v5.md` §6 per lo stesso blocco (x 70.9–306.1, ~235pt,
  ottenuta con merge di adiacenza, esplicitamente fuori scope per questo producer). Il
  blocco destro della stessa pagina e i blocchi di Dag p.136 invece coincidono con v5.
  Non risolvibile dal producer da solo: richiede una bbox strutturale indipendente non
  derivata dal contenuto testuale. Resta un problema per un consumer/Resolution futuro,
  non per questo producer;
- offset pagina PDF→stampata (+2 osservato per una zona di Dag.pdf), non verificato come
  costante sull'intero file o sul corpus;
- classificazione delle tabelle a riga singola (11.2% del totale finale, dopo dedup e
  merge) come rumore residuo vs. contenuto legittimo;
- **Chiuso dal prototipo (commit `30d9f4e`)**: lo spot-check dell'ambiente pdfplumber
  reale (0.11.10) è stato eseguito — i quattro run manuali del prototipo girano
  nell'ambiente reale dell'utente, non nel sandbox 0.11.9 usato per il solo
  post-processing in v5. Risultato: coincidenza quasi completa con i numeri di v5,
  unica eccezione il blocco sinistro di Dag p.137 (vedi rinviabile sopra);
- Lo strumento diagnostico di cross-reference è stato implementato e verificato nel commit
  `62f98f3` — "Add diagnostic cross-reference for table candidates and text primitives".
  Introduce `scripts/prototype_table_candidate_primitive_cross_reference.py`, che confronta
  tre regole geometriche indipendenti (contenimento completo, centro nella bbox,
  intersezione positiva con `overlap_ratio = overlap_area / primitive_area`) fra le
  candidate tabella e le `TextPrimitive` PyMuPDF, senza ratificarne alcuna: produce solo i
  dati per una scelta informata successiva. Stesse guardie del prototipo esistente
  (bound pagina, rotazione, CropBox/MediaBox), reimplementate localmente senza dipendenza
  diretta dall'altro script. Nessuna regola è ancora ratificata: l'ispezione dell'output
  sugli otto blocchi già validati (`State.md`, prototipo) resta il prossimo passo, non
  ancora eseguito. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note,
  suite completa 1122 test OK (invariata) e 7 skipped, `git diff --check` verde.
- Ispezione dell'output sugli otto blocchi noti (Dag.pdf `page_number` 136, 137, 286,
  Vil.pdf `page_number` 91) eseguita. Confronto quantitativo delle tre regole:
  `full_containment` fallisce a zero primitive su un blocco (Dag 286, terza colonna
  "Tutti gli ingredienti" — nessuna riga interamente contenuta) e sottostima negli altri
  sei blocchi non perfettamente rettangolari; `center_in_bbox` coincide con
  `positive_intersection` in sette blocchi su otto, ma ne perde 7 primitive proprio sul
  blocco con la sottostima d'area nota (Dag 137, blocco sinistro — le stesse primitive
  tagliate dal bordo sottostimato hanno centro fuori bbox ma sovrapposizione positiva).
  `positive_intersection` (`overlap_ratio > 0`, nessuna soglia minima) è l'unica regola
  senza fallimenti sugli otto blocchi ed è quella ratificata per popolare `primitive_ids`
  nel producer di produzione. Verificato anche il rischio opposto (falsi positivi da
  sovrapposizioni marginali con testo esterno): su Dag 137 il vicino esterno più vicino
  resta a ~85pt di distanza, nessuna primitiva in una zona grigia tra "dentro" e "fuori".
  Limite esplicito, non risolto: nessun fixture con due tabelle a distanza minima (1-3pt)
  è stato testato — un caso del genere potrebbe comportarsi diversamente con una regola
  priva di soglia minima. Da verificare se e quando un caso reale simile viene
  identificato; non blocca la ratifica sugli otto blocchi noti.
  Nota emersa durante l'ispezione visiva delle pagine, non specifica di questo producer:
  il numero di pagina stampato sul manuale (quello leggibile dall'utente, es. "284") non
  coincide con `page_number` PDF one-based usato da script e producer (es. 286, per via di
  pagine di frontespizio/sommario non numerate) — la differenza non è necessariamente
  costante in tutto il documento. Script e producer lavorano sempre in spazio `page_number`
  PDF, mai in spazio "numero stampato"; un'eventuale mappatura fra i due resta un problema
  distinto, per una fase di rendering/cross-reference futura verso l'utente, non per
  questo producer né per la rilevazione delle tabelle.
- Il producer di produzione è stato implementato e verificato nel commit `e41d10c` —
  "Add production TableCandidateProducer with ratified overlap rule". Introduce tre moduli
  puri: `page_analysis_candidate_primitive_overlap_measurements.py`
  (`measure_candidate_primitive_overlap_ratio`, sede pubblica condivisa della formula
  `intersection_area / primitive_area`, non importata da `ir_builder.py` né dagli script
  diagnostici, che mantengono le proprie copie indipendenti), `page_analysis_table_candidate_binding.py`
  (`BoundTableCandidatePage`, verifica la corrispondenza `page_id`/`plumber_page.page_number`
  in `__post_init__`, rifiuta mismatch numerico e formato inatteso con `ValueError`
  esplicito) e `page_analysis_table_candidate.py`
  (`build_table_candidate_page_analysis`, nessuna apertura di file, `primitive_ids`
  popolato con la regola `overlap_ratio > 0` ratificata). Una candidate con bbox fuori dai
  limiti pagina viene scartata singolarmente con warning loggato, non causa il rifiuto
  dell'intera pagina — comportamento deciso esplicitamente nella proposta di design (v3),
  non lasciato all'implementazione.

  Nessuna integrazione con job/workspace in questo passo, per scelta esplicita: il
  producer è una funzione pura, non wired in nessun modulo `job_*.py`. Verificato (grep
  sul repo) che nessun producer Milestone 13+ è oggi invocato dal job — le uniche
  invocazioni reali fuori dai test sono in moduli diagnostici read-only
  (`pymupdf_capture_dump.py` e tre file `*_diagnostics.py`); questo producer sarebbe il
  primo, quando verrà wired. Dove vive quell'orchestrazione (nuovo modulo dedicato,
  orientamento indicato, non deciso) resta un giro futuro separato.

  Verificato con confronto diretto contro dati già noti: su Dag.pdf `page_number` 137, i
  conteggi di `primitive_ids` per le due candidate (114 e 57) coincidono esattamente con i
  conteggi `positive_intersection` già registrati dalla diagnostica cross-reference.
  Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite completa
  1131 test OK (1122 preesistenti + 9 nuovi) e 7 skipped, `git diff --check` verde.

- Apo.pdf p.16: confermato non-tabella dall'ispezione visiva dell'utente, ma non
  identificato con certezza — non bloccante, da non perdere in una passata futura.

**Milestone chiusa nel commit `b32c833`** — "Close milestone 20 TableCandidateProducer".
Le tre fasi pianificate (prototipo standalone, diagnostica cross-reference con ratifica
della regola geometrica, producer di produzione) sono tutte completate e verificate.
L'integrazione nel job/workspace resta esplicitamente rinviata a una milestone futura,
non ancora aperta né numerata — sarebbe il primo producer Milestone 13+ mai eseguito
dentro il job (verificato: nessun modulo `job_*.py` invoca oggi alcun producer).

Fuori scope per il primo micro-step di implementazione: logica di clustering same-page,
continuation multi-pagina, deduplicazione o merge cross-config.

**Punto architetturale nuovo, non affrontato dalla progettazione originale**: tutti i
producer esistenti delle Milestone 13+ (`page_analysis_root.py`,
`page_analysis_page_covering_visual.py`, `page_analysis_side_band.py`, ecc.) hanno la
stessa forma — `build_..._page_analysis(primitive_page: NormalizedPrimitivePage, *,
generation_id) -> PageAnalysis` — e derivano `RegionCandidate.primitive_ids`
esclusivamente da primitive già normalizzate da PyMuPDF. `text_lines` è invece una
strategia di rilevamento tabelle di **pdfplumber**, mai integrata nel modello a primitive:
nel repo pdfplumber è oggi usato solo dalla pipeline legacy (`extractor.py`, `main.py`) e
da script diagnostici, non da alcun producer Milestone 13+. Verificato anche che
`CaptureProgress`/`CapturePageState` (`job_capture_progress.py`) traccia oggi esattamente
un artifact per pagina: un capture pdfplumber persistito e resumable come quello PyMuPDF
richiederebbe estendere questo schema.

**Decisione presa in un breve giro di Modalità P dedicato**: per il primo prototipo, la
rilevazione pdfplumber non entra nel job/workspace. Un prototipo standalone, fuori dal job
system (analogo per collocazione a `scripts/debug_pdfplumber_table_settings.py`, non un
producer definitivo), riceve un PDF passato direttamente, invoca pdfplumber con
`text_lines` e verifica il contratto `RegionCandidate` su casi reali. Le candidate
prodotte useranno `primitive_ids=()`: il contratto attuale lo permette già
(`RegionCandidate.primitive_ids` ha default `()` e la validazione non richiede tupla non
vuota — nessuna modifica di schema necessaria), e il cross-reference con le
`TextPrimitive` PyMuPDF contenute nella bbox resta un rinviabile esplicito, non
necessario per validare la forma della candidate.

Restano esplicitamente rinviate, non decise oggi: l'integrazione nel job/workspace
(persistenza resumable di un capture pdfplumber, vs. esecuzione a runtime su uno snapshot
già verificato — sono due alternative concrete, nessuna scelta ancora fra le due) e
qualunque cross-reference fra candidate tabella e primitive PyMuPDF.

Apertura non autorizza ancora un micro-step implementativo nel job system. Il prototipo
standalone descritto sopra è autorizzato come passo di validazione, non come codice di
produzione.

Il prototipo è stato implementato e verificato nel commit `30d9f4e` — "Add standalone
prototype validating pdfplumber table candidates". Introduce
`scripts/prototype_table_candidate_producer.py` e
`tests/test_prototype_table_candidate_producer.py`, con guardie esplicite su bound pagina
(`1 <= page_number <= page_count`), rotazione (`rotation != 0`) e frame pagina
(`CropBox != MediaBox`). Quest'ultima guardia è stata aggiunta dopo un secondo giro di
revisione Chat B: un failure mode indipendente dalla rotazione, stessa firma (bbox
pdfplumber contenuta nei bound pagina ma in un frame diverso da quello usato da PyMuPDF),
innescato da CropBox più piccola della MediaBox — comune in PDF scansionati con margini
di stampa ritagliati. Entrambe le guardie rifiutano esplicitamente (`PRECONDITION_FAIL`,
exit code 3) invece di produrre candidate silenziosamente errate.

Verificato su quattro pagine reali nell'ambiente utente (pdfplumber 0.11.10, non il
sandbox 0.11.9 usato per il solo post-processing in v5): Dag.pdf `page_number` 136, 137,
286 e Vil.pdf `page_number` 91, tutte con esito `PASS`. Le bbox del blocco destro di Dag
p.136 e p.137 e del blocco unico di Vil p.91 coincidono con quelle già riportate in
`Proposta_TableCandidateProducer_v5.md` §6; il cluster di Dag p.286 conferma il pattern a
3 colonne parallele di v5 §5 (vedi anche rinviabile aggiornato sotto per una discrepanza
osservata sul blocco sinistro di Dag p.137). Baseline verificata: Ruff verde, BasedPyright
0 errori/0 warning/0 note, suite completa 1122 test OK (1120 preesistenti + 2 nuovi) e 7
skipped, `git diff --check` verde.

## Milestone 21 — wiring del primo producer nel job (esecuzione runtime, senza persistenza) — completata

Chiude un giro di progettazione Modalità P breve, condotto in sessione separata da questo
State.md (documenti `Proposta_Milestone21_ProducerJobWiring_v1.md`,
`Revisione_ChatB_Milestone21_ProducerJobWiring_v1.md`,
`Milestone21_Decisioni_e_PromptZed_v1.md`, non inclusi nel repo). Obiettivo: introdurre la
prima infrastruttura generica per eseguire un producer di `PageAnalysis` dentro il job,
sopra una pagina già catturata. `table_candidate` (Milestone 20) è il primo consumer
concreto e il caso più esigente, non l'unico beneficiario dichiarato: qualunque producer
PyMuPDF-only futuro userà la stessa infrastruttura senza modifiche strutturali attese.

Punto di partenza verificato in apertura: nessun modulo `job_*.py` invocava alcun
producer Milestone 13+ prima di questa milestone (stesso punto architetturale già
registrato in chiusura Milestone 20).

Decisioni ratificate in Modalità P, con revisione Chat B indipendente e verifica
empirica delle citazioni contro il codice reale, non per fiducia:

1. Nessuna persistenza del `PageAnalysis` prodotto in questo giro. Il runner lo
   restituisce al chiamante; `page_analysis_store.py` (Milestone 5, mai collegato prima
   d'ora e non collegato nemmeno qui) resta un mattone disponibile per una milestone
   futura. Persistenza tracciata avrebbe richiesto un nuovo campo in `WorkspacePaths` e
   un bump di `JOB_MANIFEST_SCHEMA_VERSION`, lavoro comparabile a quello già rinviato per
   `CapturePageState` — non aperto in questo giro.
2. Apertura document-scoped a doppio backend in un modulo dedicato, non
   nell'attestazione PyMuPDF-only di Milestone 9 (`attest_pymupdf_document_source`,
   chiusa, non riaperta) e non inline nel runner.
3. Dispatcher a lista chiusa (`frozenset`) sul nome del producer richiesto, non un
   registry dinamico: un solo producer reale (`table_candidate`) non giustifica quella
   complessità. Forma da rivedere quando arriverà un secondo producer con un caso
   concreto davanti, non indovinata ora.
4. Le guardie pagina `rotation != 0` e `mediabox != cropbox`, verificate nel prototipo
   standalone di Milestone 20 (`30d9f4e`) ma assenti dalla produzione (`page_analysis_table_candidate.py`,
   `page_analysis_table_candidate_binding.py`, `pymupdf_capture.py` — quest'ultimo anzi
   ammette rotazioni 90/180/270), vanno riapplicate nel runner a livello di pagina
   specifica, prima di costruire `BoundTableCandidatePage`. Trovato da Chat A durante il
   dettaglio implementativo, non presente né nella proposta iniziale né nella revisione
   di Chat B.
5. Il runner non legge l'artifact di capture persistito da `job_capture_page_runner.py`:
   verificato che nessuna funzione `*_from_dict` ricostruisce un `BackendPageCapture` dal
   JSON persistito in produzione (i test esistenti lo leggono solo come dict grezzo).
   Il runner ricalcola la capture PyMuPDF a runtime dalla pagina già aperta, stesso
   pattern già usato da `pymupdf_capture_dump.py` e dal prototipo Milestone 20. Costo
   noto e accettato: la capture PyMuPDF viene rifatta due volte (persistenza al momento
   della cattura, ricalcolo al momento dell'analisi) — inefficienza rinviabile a un
   futuro deserializzatore, non costruito qui. Anche questo trovato da Chat A durante il
   dettaglio implementativo, non nei due documenti precedenti.

Implementato e verificato nel commit `93ee631` — "Add job-wired page analysis runner for
the table_candidate producer". Due moduli nuovi: `pymupdf_pdfplumber_document_source_binding.py`
(`BoundDocumentSource`, dataclass pura senza semantica di context manager;
`bind_pymupdf_pdfplumber_document_source(snapshot_path, *, expected_file)`, legge i byte
una sola volta, verifica digest/size con gli stessi messaggi di `attest_pymupdf_document_source`,
apre `fitz` e `pdfplumber` dallo stesso buffer — confermato `pdfplumber.open is PDF.open`,
non un aggiramento —, `ValueError` esplicito su mismatch `page_count` fra i due backend,
chiusura di quanto già aperto su ogni percorso di errore) e `job_page_analysis_runner.py`
(`run_job_page_analysis`, `PageAnalysisRunResult`). Il runner valida `producer_name`
contro la lista chiusa prima di aprire qualunque file, richiede la pagina già `COMPLETED`
e risolvibile (`is_capture_page_resumable`) come gate di precondizione — nessuna cattura
implicita —, applica le guardie pagina del punto 4, ricalcola la capture come da punto 5,
per `table_candidate` costruisce `BoundTableCandidatePage` e chiama
`build_table_candidate_page_analysis` invariato dalla Milestone 20, chiude entrambi i
backend in un blocco `finally`. Aggiunta non richiesta dal design ma verificata coerente:
un controllo `page_count` PDF-vs-manifest, a specchio di quello già presente in
`job_capture_page_runner.py`.

`job_capture_page_runner.py` resta invariato (capture-only, come da nome e da vincolo
esplicito). Nessuna modifica a `CapturePageState`, `CaptureProgress`, `JobManifest`,
`WorkspacePaths`. Nessuna modifica ai contratti Milestone 20
(`BoundTableCandidatePage`, `measure_candidate_primitive_overlap_ratio`,
`build_table_candidate_page_analysis`, regola `positive_intersection`).

Verificato con test end-to-end su Dag.pdf `page_number` 137: i conteggi `primitive_ids`
delle due candidate (114 e 57) coincidono con l'oracolo già stabilito in Milestone 20,
attraverso il nuovo percorso wired nel job anziché lo script diagnostico standalone.
Test aggiuntivi: rifiuto di pagina non catturata (nessuna cattura implicita), rifiuto di
pagina catturata con artifact invalido, rifiuto di `producer_name` sconosciuto, rifiuto
di pagina ruotata, rifiuto di pagina con `cropbox != mediabox`, apertura corretta dei due
backend dallo stesso buffer, rifiuto e cleanup su mismatch digest/size/`page_count`.
Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite completa
1140 test OK (1131 preesistenti + 9 nuovi) e 7 skipped, `git diff --check` verde.

Fuori scope per questo micro-step, esplicitamente rinviato: persistenza tracciata o non
tracciata del `PageAnalysis` prodotto; resume o esecuzione batch su più pagine; estensione
di `CapturePageState` per un secondo artifact (es. capture pdfplumber persistita); wiring
di un secondo producer reale (nessuno oggi pronto oltre `table_candidate`); un punto di
invocazione manuale/CLI dedicato (non richiesto in questo giro, `pymupdf_capture_dump.py`
resta invariato, PyMuPDF-only).

**Milestone chiusa nel commit `93ee631`.** Il deliverable pianificato in Modalità P
(apertura document-scoped a doppio backend, runner generico, wiring di `table_candidate`)
è l'unico previsto per questa milestone, non multi-fase come la Milestone 20: nessuna
fase ulteriore risultava pianificata in chiusura di progettazione.

Riferimento documentale: `Proposta_TableCandidateProducer_v5.md` (consegnato all'utente,
non incluso nel repo).

## Milestone 22 — cache opportunistica del PageAnalysis — completata

Emersa da una domanda diretta sul costo reale di `run_job_page_analysis`: un
deserializzatore di `BackendPageCapture` (discusso e poi scartato in Modalità P) avrebbe
risolto solo la ricattura PyMuPDF, non il costo del parsing pdfplumber (`find_tables`),
verosimilmente il più pesante dei due — verificato leggendo `page_analysis_table_candidate.py`,
le bbox delle tabelle vengono esclusivamente da `bound_page.plumber_page.find_tables(...)`,
mai da `BackendPageCapture`. Per `table_candidate` l'output di pdfplumber è già
candidate-shaped: non esiste un livello "capture pdfplumber grezzo" utile da persistere
separatamente dalle candidate. "Leggere una volta e poter riaccedere ai dati" coincide,
per questo producer, con persistere il `PageAnalysis` prodotto.

Decisioni ratificate in Modalità P, con revisione Chat B indipendente e verifica empirica
delle citazioni:

1. Cache non tracciata dal manifest — nessuna modifica a `WorkspacePaths`, `JobManifest`,
   `CapturePageState`, `CaptureProgress`. Non fa parte del contratto di resumability del
   job: se assente o invalida, degrada sempre al ricalcolo completo, mai a un errore o a
   un dato scorretto.
2. Chiave di validità = i sette campi di `PageAnalysisProvenance` (`source_id`,
   `source_capture_id`, `source_page_id`, `source_primitive_schema_version`,
   `producer_name`, `producer_version`, `configuration_id`), tutti noti staticamente senza
   aprire il PDF. Corretto in revisione (Chat B): la proposta iniziale includeva anche
   `sha256`/`size_bytes` di `CapturePageState`, scartati perché `run_job_page_analysis` non
   li consuma mai come input — l'identità del contenuto documentale è già interamente
   verificata da `source_id` a ogni chiamata via digest check in
   `bind_pymupdf_pdfplumber_document_source`.
3. `generation_id` escluso dalla chiave, gestito con `dataclasses.replace(cached_analysis,
generation_id=generation_id)` su cache hit, senza mai riscrivere il file. Necessario
   perché `BoundPageAnalysis.__post_init__` (`document_analysis_binding.py`) impone
   `reference.page_analysis_generation_id == analysis.generation_id` — un gap trovato in
   revisione (Chat B), assente dalla proposta iniziale.
4. Percorso convenzionale `job_dir / "analysis_cache" / producer_name /
f"page-{page_num:04d}.json"`, nome deliberatamente diverso da `raw_dir`/`analysis` per
   segnalare che non è tracciato dal manifest.
5. Logging esplicito (INFO) su ogni cache hit — mitigazione proporzionata a un rischio
   segnalato in revisione: nessuna versione della logica di cattura è oggi tracciata
   (solo `CAPTURE_SCHEMA_VERSION`, `NORMALIZED_PRIMITIVE_SCHEMA_VERSION`,
   `PAGE_ANALYSIS_SCHEMA_VERSION`, tutte sullo _schema_ dei dati, non sulla _logica_); un
   futuro bug fix in `capture_pymupdf_page`/`normalize_backend_page_capture` che cambi
   l'output senza bump di schema non invaliderebbe la cache. Non risolto — reso
   diagnosticabile via log, non lasciato silenzioso. Un vero versionamento della logica di
   cattura resta esplicitamente rinviato.
6. `force_recompute: bool = False` su `run_job_page_analysis`: bypassa una cache valida e
   riscrive comunque il file.

Implementato e verificato nel commit `fce90e2` — "Add opportunistic PageAnalysis cache to
job_page_analysis_runner". Nuovo modulo `job_page_analysis_cache.py`
(`read_cached_page_analysis`, `write_page_analysis_cache`, riuso di `page_analysis_store.py`
Milestone 5, mai collegato prima d'ora). `run_job_page_analysis` modificato: prova la
lettura cache prima di aprire qualunque backend, usando solo valori noti staticamente dal
manifest; su hit restituisce `dataclasses.replace(...)`; su miss o `force_recompute=True`
procede come in Milestone 21 e scrive la cache a calcolo completato. Le costanti
`producer_version`/`configuration_id` di `table_candidate` sono duplicate come costanti
private in `job_page_analysis_runner.py` (il file `page_analysis_table_candidate.py` era
fuori scope, quei valori vi restano letterali inline, non esportabili) — verificato che
coincidano esattamente, nessuna deriva.

Verificato con test end-to-end su Dag.pdf `page_number` 137: al primo run i conteggi
`primitive_ids` (114, 57) coincidono con l'oracolo già stabilito; al secondo run, con
`bind_pymupdf_pdfplumber_document_source`/`capture_pymupdf_page` forzati a sollevare
`AssertionError` se chiamati, il cache hit restituisce lo stesso risultato con solo
`generation_id` sostituito, confermando che nessun backend viene riaperto. Baseline
verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note, suite completa 1146 test
OK (1140 preesistenti + 12 nuovi, di cui alcuni sostitutivi) e 7 skipped, `git diff --check`
verde.

Fuori scope, esplicitamente rinviato: persistenza _tracciata_ nel manifest (resterebbe
un'alternativa distinta se servirà il resume); versionamento della logica di cattura;
gestione della concorrenza in scrittura (nessun job manager/batch runner esiste oggi);
deserializzatore di `BackendPageCapture` (valore ridotto per `table_candidate`, resta
un'idea per un eventuale producer PyMuPDF-only futuro).

**Milestone chiusa nel commit `fce90e2`.** Documenti di progettazione (non inclusi nel
repo): `Proposta_PageAnalysisCache_v1.md`, `PageAnalysisCache_Decisioni_e_PromptZed_v1.md`.

## Milestone 23 — wiring del secondo producer nel job (page_covering_visual, apertura selettiva del backend) — completata

Chiude il rinvio esplicito di Milestone 21/22 ("wiring di un secondo producer"). Giro di
Modalità P con revisione Chat B indipendente (documenti non inclusi nel repo).

Wired `page_covering_visual` (Milestone 6, `producer_version="0.1"`,
`configuration_id="page-covering-visual-v1"`) accanto a `table_candidate`. A differenza
di quest'ultimo consuma solo `NormalizedPrimitivePage`, senza pdfplumber.

Scoperta di Chat A, confermata da Chat B: il runner usava la chiave di dispatch
(`producer_name`) anche come `producer_name` atteso nella cache Milestone 22. Per
`table_candidate` coincidono per costruzione; per `page_covering_visual` no (il modulo
scrive internamente `"page_analysis.page_covering_visual"`), causando cache-miss
sistematico e silenzioso se non corretto.

Decisioni: `bind_pymupdf_pdfplumber_document_source` guadagna
`include_pdfplumber: bool = True` (`BoundDocumentSource.plumber_pdf: PDF | None`),
nessun secondo backend aperto quando non richiesto — unico chiamante di produzione, una
funzione separata avrebbe solo duplicato la verifica digest/size.
`_SUPPORTED_PRODUCERS`/`_producer_cache_identity` sostituiti da `_PRODUCER_SPECS:
dict[str, _ProducerSpec]` (nome interno, versione, configuration_id, necessità di
pdfplumber), che risolve anche la scoperta sopra. Dispatcher di esecuzione resta
`if`/`elif`: due builder con firme diverse, un adapter comune non è giustificato da due
casi. Narrowing esplicito su `plumber_pdf` (`AssertionError` se `None` nel ramo
`table_candidate`, guardia nel `finally`).

Implementato nel commit `3bda611`. Baseline: Ruff verde, BasedPyright 0/0/0, 1149 test OK
(1146 + 3 nuovi), 7 skipped, `git diff --check` verde.

Verifica reale su tre manuali (Dag/Vil/DB, 11 pagine campione più scansione completa
379/272/126 pagine): wiring corretto su tutte, nessun rifiuto da guardie. La scansione
per `content_digest` conferma che il producer non distingue sfondi ripetuti da
illustrazioni uniche (comportamento già dichiarato non-obiettivo in Milestone 6, non una
regressione). Dettaglio e possibile seguito nell'appunto sotto.

Fuori scope: CLI dedicata; terzo producer; classificazione decorative/structural;
consumer document-level di ricorrenza. Nessuna modifica a
`page_analysis_page_covering_visual.py`, `page_analysis_table_candidate*.py`,
`page_analysis_model.py`, `job_page_analysis_cache.py`, `job_capture_page_runner.py`,
manifest/workspace.

**Milestone chiusa nel commit `3bda611`.**

## Milestone 24 — wiring del terzo producer nel job (page_edge_visual, ratifica

side_band/page_edge_visual) — completata

Chiude il blocco esplicito posto dall'utente su un terzo producer prima di ratificare
la relazione fra `page_edge_visual` e `side_band`. Giro di Modalità P con revisione
Chat B indipendente (documenti non inclusi nel repo).

Wired `page_edge_visual` (Milestone 6, `producer_version="0.1"`,
`configuration_id="page-edge-visual-v1"`) accanto a `table_candidate` e
`page_covering_visual`, stesso pattern di Milestone 23: nessuna modifica a
`bind_pymupdf_pdfplumber_document_source`, `job_page_analysis_cache.py`,
`page_analysis_page_edge_visual.py`, `page_analysis_side_band.py`.

Ratifica: `side_band` e `page_edge_visual` restano due producer indipendenti (vedi
appunto sopra). Nessun bisogno tecnico di unificarli — tipi di primitive diversi,
co-occorrenza reale rara. Verifica empirica su 5 manuali interi (Vil 272p, Dag 379p,
DB 126p, Kul 242p, Fab 362p, 1381 pagine totali), riusando solo API già ratificate
(Milestone 6, 13-19): >99% delle coppie side_band × page_edge_visual sono disgiunte
su tutti i manuali; le eccezioni si dividono in containment genuino (Fab p.271
stampata: testo "4"/"CAPITOLO" interamente dentro la tab decorativa margine destro)
e coincidenza di margine (DB p.119, Fab p.106/p.324: overlap di 0.3pt su candidate
larghe 2-15pt, un simbolo decorativo che sfiora il bordo fisso di uno sfondo).

Implementato nel commit `27af1ef`. Baseline: Ruff verde, BasedPyright 0/0/0, N test OK
(1149 + 2 nuovi), 7 skipped, `git diff --check` verde.

Fuori scope: soglia di magnitudo/containment nel codice di produzione (resta nota di
design); quarto producer; classificazione decorative/structural; consumer
document-level. Nessuna modifica a `page_analysis_page_edge_visual.py`,
`page_analysis_side_band.py`, `page_analysis_co_reference*.py`.

**Sanatoria (Milestone 35, retroattiva)**: lo script che ha prodotto i numeri sopra
(`scan_side_band_vs_edge_visual_co_occurrence.py`/`_aggregated.py`) non era stato
committato all'epoca — trovato non tracciato durante il riordino di Milestone 35,
committato ora in `ecb5b72`.

**Milestone chiusa nel commit `27af1ef`.**

## Milestone 25 — diagnostica pura per visuali interne (interior-visual-diagnostics) — completata

Nuovo stage diagnostico `interior-visual-diagnostics` (`pymupdf_capture_dump.py`),
modulo `page_analysis_interior_visual_diagnostics.py`. Per ogni primitivo visivo
(immagine o drawing) descrive se soddisfa le soglie di `page_covering_visual`,
quelle di `page_edge_visual`, o nessuna delle due (`is_residual_interior_visual`),
più due campi su testo contenuto (`contained_text_primitive_count`,
`contained_text_area_ratio`, calcolati componendo `measure_primitive_pair`,
Milestone 6). Nessun `RegionCandidate`, nessun `PageAnalysis`, nessuno
`structural_kind`, nessun wiring nel job.

`State_Archive.md:133` (ripetuta a riga 894) vieta un producer per "visuali interne"
senza prima osservarle con la diagnostica. La moratoria resta in vigore: questa
milestone ne soddisfa la precondizione, non la supera — l'apertura di un eventuale
producer resta rinviata a una ratifica dedicata futura, informata da quanto questo
stage osserverà su manuali reali.

I campi `contained_text_*` sono ispirati alla classificazione della pipeline legacy
(`extractor.py`, `_asset_is_box_like_text_region`) solo nel segnale — testo
contenuto in una visuale come indizio di box/callout — non nell'implementazione né
nelle soglie numeriche legacy, tarate su un modello di dati diverso e non
rivalidate. Nessun codice legacy importato o duplicato.

Implementato nel commit `<hash>`. Baseline: Ruff verde, BasedPyright 0/0/0, 1157 test OK
(1150 preesistenti + 7 nuovi), 7 skipped, `git diff --check` verde.

Fuori scope: producer, wiring nel job, classificazione decorativo/contenuto, soglie
legacy, callout/box (`layout.interior_visual_frame`, non-obiettivo Milestone 6,
ancora non aperto), elenchi.

**Milestone chiusa nel commit `<c5aea29>`.**

## Milestone 26 — diagnostica di clustering geometrico per DrawingPrimitive (drawing-cluster-diagnostics) — completata

Questa milestone è la decisione architetturale dedicata che sblocca "clustering"
come categoria — vietata separatamente dalla moratoria "visuali interne" in almeno
sei punti di `State_Archive.md` (righe 117, 135, 160, 228, 894, 921-926, 962),
sempre "salvo una futura decisione architetturale dedicata" (894, 962). La ratifica
ha perimetro stretto: solo `DrawingPrimitive`, solo diagnostica read-only (nessun
nuovo tipo pubblico `Cluster`/`Block`/`Group`/`Span`, nessun `RegionCandidate`,
`PageAnalysis`, `structural_kind`, nessun uso come meccanismo di producer o
candidate), nessuna estensione a `TextPrimitive`/`side_band` o a
`ImageOccurrencePrimitive` (già identificata via `content_digest`).

Nuovo stage `drawing-cluster-diagnostics`, modulo
`page_analysis_drawing_cluster_diagnostics.py`: union-find su bbox di
`DrawingPrimitive` espanse di un margine esplicito (`cluster_margin`, default 5.0pt,
ispirato a `extractor.py:_extract_vectors`, legacy, mai validato sul nuovo modello
dati). Pre-filtro esplicito (`min_member_area`, `max_member_page_width/height_ratio`,
default legacy) esclude dal confronto a coppie i frammenti troppo piccoli o
bordo-simili, riportati comunque in output con `excluded_reason` (nessuna esclusione
silenziosa). Ogni cluster espone `dispersion_ratio` (somma aree membri / area
bbox-unione) per distinguere un'unione compatta da una dispersa prima di applicare
le soglie di `page_covering_visual`/`page_edge_visual` (duplicate localmente) al
bbox-unione.

Implementato nel commit `<f3e16cf>`. Baseline: Ruff verde, BasedPyright 0/0/0, 1164 test OK
(1157 preesistenti + 7 nuovi), 7 skipped, `git diff --check` verde.

Fuori scope: producer, wiring nel job, estensione a testo/immagini, ottimizzazione
O(n²), soglie legacy come default definitivo (restano punto di partenza esplicito).

**Sanatoria (Milestone 35, retroattiva)**: lo script dietro la nota successiva su
`dispersion_ratio` (Kul p.169/167, DB p.125) non era stato committato all'epoca —
trovato non tracciato durante il riordino di Milestone 35, committato ora in
`ecb5b72` (`scan_drawing_cluster_diagnostics.py`).

**Milestone chiusa nel commit `<f3e16cf>`.**

## Milestone 27 — producer per visuali interne (embedded_visual, no wiring) — completata

Chiude la precondizione soddisfatta da Milestone 25/26 (`State_Archive.md:133`,
ripetuta 894: "osservate con la diagnostica prima"). Giro di Modalità P con revisione
Chat B indipendente (documenti non inclusi nel repo:
`Proposta_Milestone27_EmbeddedVisualProducer_v1.md`,
`Revisione_ChatB_Milestone27_EmbeddedVisualProducer_v1.md`).

Nuovo modulo `page_analysis_embedded_visual.py`, `build_embedded_visual_page_analysis`,
stesso pattern di `page_analysis_page_edge_visual.py`: riusa invariate
`dump_interior_visual_diagnostics` (Milestone 25) e `dump_drawing_cluster_diagnostics`
(Milestone 26) come funzioni pure. Un solo `structural_kind`, `layout.embedded_visual`,
per entrambi i tipi (opzione A del §4 della proposta, preferita a due kind separati:
nessun consumer oggi dimostra la necessità di distinguerli, coerente con
`State_Archive.md:915`).

Blocco trovato in revisione Chat B, risolto prima dell'implementazione:
`dump_drawing_cluster_diagnostics` calcola `is_residual_interior_visual` anche per i
singleton scartati dal pre-filtro di Milestone 26 (`excluded_reason` valorizzato, es.
`tiny`/`border_like`). Il producer filtra esplicitamente su
`is_residual_interior_visual is True` **e** `excluded_reason is None`; senza questo
secondo controllo ogni frammento vettoriale marginale verrebbe promosso a candidate,
vanificando la stima di rumore contenuto della proposta (che copriva solo cluster
multi-membro da chaining, non i singleton esclusi).

Rinviati esplicitamente, non decisi in questa milestone: due `structural_kind`
separati per raster/vettoriale (riapertura solo con un consumer reale che lo
richieda); un campo su `RegionCandidate` che rispecchi `content_digest` per il caso
raster (tocca un tipo condiviso da tutti i producer e dal validatore cross-model,
decisione a sé); cardinalità massima di un cluster (rinviato a Resolution, invariante
`State.md:108`); deduplica document-level per `content_digest` (lavoro di consumer
futuro, già annotato dopo Milestone 23).

Nessun wiring nel job in questa milestone, per scelta esplicita — stesso schema già
seguito da `page_covering_visual`/`page_edge_visual`, costruiti standalone e wired
solo in milestone dedicate successive (23-24).

Implementato nel commit `<hash>`. Baseline: Ruff verde, BasedPyright 0/0/0, 1172 test
OK (1164 preesistenti + 8 nuovi), 7 skipped, `git diff --check` verde.

Fuori scope: wiring nel job, due `structural_kind`, campo document-level su
`RegionCandidate`, limite di cardinalità cluster, estrazione raster/vettoriale in
alta qualità (vedi appunto sopra).

**Milestone chiusa nel commit `<1701544>`.**

## Milestone 28 — wiring del quarto producer nel job (embedded_visual) — completata

Chiude il rinvio esplicito di Milestone 27 ("wiring nel job, per scelta esplicita").
Giro di Modalità P breve con revisione Chat B indipendente
(`Proposta_Milestone28_EmbeddedVisualWiring_v1.md`, non nel repo).

Wired `embedded_visual` (Milestone 27, `producer_version="0.1"`,
`configuration_id="embedded-visual-v1"`) accanto a `table_candidate`,
`page_covering_visual`, `page_edge_visual`, stesso pattern di Milestone 23/24: nuova
entry in `_PRODUCER_SPECS` (`requires_pdfplumber=False`, nessun parametro
`cluster_margin` esposto dal runner — il producer usa il proprio default), nuovo ramo
nel dispatcher `if`/`elif` esistente. Nessuna modifica a
`page_analysis_embedded_visual.py`, agli altri producer, a `job_page_analysis_cache.py`
o a `pymupdf_pdfplumber_document_source_binding.py`.

Punto di revisione Chat B verificato e adottato:
`test_include_pdfplumber_is_symmetric_per_producer` esteso al quarto producer,
`include_pdfplumber=False` confermato anche per `embedded_visual`. Un secondo punto
della stessa revisione (presunto disallineamento di `State.md`/`AGENTS.MD` a
Milestone 18) è stato verificato falso da Chat A con un clone diretto del branch
`main` e scartato — causa più probabile: cache CDN di `raw.githubusercontent.com`
usata da Chat B invece di un clone diretto.

Nuovo test end-to-end `test_runs_embedded_visual_for_synthetic_interior_visual`:
verifica `proposed_structural_kind == "layout.embedded_visual"` su un residuo
interiore sintetico (immagine centrale, né covering né edge), verifica cache hit con
`bind_pymupdf_pdfplumber_document_source`/`capture_pymupdf_page` forzati ad
`AssertionError` se richiamati.

Implementato nel commit `<94e846d>`. Baseline: Ruff verde, BasedPyright 0/0/0, 1173 test
OK (1172 preesistenti + 1 nuovo — il secondo requisito era un'estensione di un test
esistente, non una nuova funzione), 7 skipped, `git diff --check` verde.

Fuori scope: modifiche al producer stesso; parametrizzazione di `cluster_margin`
attraverso il runner.

**Milestone chiusa nel commit `<94e846d>`.**

## Milestone 29 — diagnostica esplorativa per riquadri di testo (box-like interior visual) — completata

`scripts/scan_interior_visual_frame_diagnostics.py` committato — a differenza della
prima decisione presa (script non tracciato), corretta in revisione: M25/M26 hanno
sempre committato il modulo/script che produce la base empirica citata in `State.md`,
non solo il risultato. Restano non tracciati solo gli script di scansione ad-hoc di
altre milestone (`scan_interior_visual_diagnostics.py`,
`scan_drawing_cluster_diagnostics.py`), diversi da questo caso perché qui lo script
contiene l'unica implementazione esistente del containment vettoriale sul
bbox-unione, poi riusata come riferimento in Milestone 30.

Giro di Modalità P breve con revisione Chat B indipendente
(`Proposta_Milestone29_InteriorVisualFrameDiagnostics_v1.md`, non nel repo; revisione
fornita in chat, non salvata come file separato). Blocco
tecnico trovato in revisione e risolto prima dell'implementazione: `measure_primitive_pair`
non accetta un bbox arbitrario (richiede `primitive_id` risolvibili tramite
`_primitives_by_id`); il ramo vettoriale richiede una funzione locale di containment
testo/bbox-unione, che duplica `_contains`
(`page_analysis_primitive_pair_measurements.py:349`, containment stretto, nessuna
tolleranza) — stesso principio di duplicazione locale già usato da Milestone 26
(`State_Archive.md:143`).

Script: una sola capture+normalize per pagina, `dump_interior_visual_diagnostics`
(Milestone 25, ramo raster) e `dump_drawing_cluster_diagnostics` (Milestone 26, ramo
vettoriale, filtrato su `excluded_reason is None` — stessa lezione di Milestone 27/28)
eseguiti sulla stessa `NormalizedPrimitivePage`, filtro su area ratio nel range legacy
(0,6%-28%, `extractor.py:_asset_is_box_like_text_region`).

Eseguito su 4 manuali reali (Apo, Dag, DB, Fab), ispezione visiva mirata su un
campione di pagine segnalate dall'utente, non solo teorica:

- Segnale confermato su contenuto reale: box editoriali con bordo tratteggiato
  (Apo p.86/p.131), due box statistica affiancati (DB p.99, `page_area_ratio=0.630`),
  banner di titolo capitolo ricorrente (Fab, 5 pagine con lo stesso pattern esatto,
  `page_area_ratio≈0.03`). Altri casi confermati: Dag p.354 (`0.022`-`0.201` a
  seconda del candidate), Apo p.90/p.135 (`0.101`/`0.062`). Il range legacy
  (0,6%-28%) copre tutti i casi reali osservati, ma il campione non forza il limite
  superiore (il caso più alto, DB p.99, è a 0,630, già nella fascia alta) — non
  validato oltre quel punto.
- `contained_text_area_ratio` può superare 1.0 su pagine con testo fitto vicino a
  loghi piccoli (Dag p.379, retro copertina; Fab, pattern sistematico su 5 pagine) —
  non è un errore di containment, primitive di testo si sovrappongono fra loro; da
  tenere presente per le soglie di un eventuale producer, non un difetto della
  diagnostica.
- Il rischio di falso positivo da bridging (`dispersion_ratio` basso + testo
  contenuto alto, previsto in revisione Chat B) non si è materializzato nei casi
  ispezionati su Dag (2/2 confermati box reali); 2 casi analoghi su DB non ancora
  ispezionati visivamente.
- **Sovrapposizione sistematica, non rara, con `table_candidate` (Milestone 20):**
  tabelle con bordo decorativo (es. tabelle D6 di DB, più pagine) vengono lette dal
  ramo vettoriale come "box" — stessa forma geometrica (rettangolo con testo
  contenuto), origine diversa (`DrawingPrimitive` cluster vs pdfplumber
  `text_lines`). Non e' rumore casuale: e' un secondo tipo strutturale reale che
  condivide la stessa firma geometrica di un box editoriale. Rilevante per il design
  di Milestone 30, non risolto qui.
- Un pattern vettoriale ricorrente (Apo, 6 pagine) è una fascia laterale verticale
  con testo, concettualmente più vicina a `layout.side_band` (Milestone 6) che a un
  callout — stessa famiglia di questione già aperta per `side_band` × `page_edge_visual`
  (nota Milestone 24), ora estesa anche a `side_band` × box vettoriale.
- Confermato il caso noto di chaining (DB p.125, Milestone 26): 57 righe su 74 hanno
  testo contenuto — griglia fitta di icone/etichette di scheda personaggio, genere
  visivo diverso da un box editoriale, non falso allarme ma categoria attesa.

Criterio di uscita (§6 della proposta) soddisfatto in forma riveduta: il segnale
geometrico (visuale residua + testo contenuto nel range legacy) trova affidabilmente
"testo incorniciato da una visuale" — categoria che include box editoriali, banner di
titolo, fasce laterali e tabelle con bordo, non solo callout in senso stretto. Non
distingue il sottotipo semantico, per costruzione (`RegionCandidate` non porta
semantica) — la sovrapposizione con `table_candidate` è un fatto strutturale reale da
progettare, non un fallimento della diagnostica.

Fuori scope: producer, wiring nel job, distinzione box/tabella/fascia laterale,
soglie di produzione definitive (il range legacy resta punto di partenza, non
validato come soglia finale).

**Milestone chiusa nei commit `f1db066` (script `scan_interior_visual_frame_diagnostics.py`)
e `f1db066` (aggiornamento `State.md`/`AGENTS.MD`).**

## Milestone 30 — producer per riquadri di testo (layout.interior_visual_frame, no wiring) — completata

Chiude la precondizione soddisfatta da Milestone 29 (diagnostica esplorativa,
script committato `scripts/scan_interior_visual_frame_diagnostics.py`, verificabile
su 4 manuali reali). Giro di Modalità P con revisione Chat B indipendente
(`Proposta_Milestone30_InteriorVisualFrameProducer_v1.md`, non nel repo), due giri:
il primo ha corretto un'analogia di design sbagliata (§5, sostituita con il
precedente corretto `page_edge_visual`/`side_band`, Milestone 24), il conteggio
delle duplicazioni di `_contains` (tre istanze reali committate, non due — trovata
da Chat A una seconda duplicazione preesistente in
`page_analysis_candidate_extent_relation_measurements.py:164`, Milestone 7, non
citata dalla proposta originale) e l'esclusione intenzionale del tetto legacy
`text_area_ratio <= 0.70`; il secondo (sulla chiusura di Milestone 29) ha bloccato
temporaneamente questa milestone finché la base empirica non è stata resa
verificabile (vedi Milestone 29, script committato dopo un primo errore di
staging corretto).

Nuovo modulo `page_analysis_interior_visual_frame.py`,
`build_interior_visual_frame_page_analysis`: stesso pattern a due rami di
`embedded_visual` (Milestone 27), riuso invariato delle diagnostiche Milestone 25/26.
Sottoinsieme più specifico di `embedded_visual`: oltre a `is_residual_interior_visual`
ed `excluded_reason is None` (ramo vettoriale), richiede `contained_text_primitive_count > 0`
su entrambi i rami e un range esplicito `min_area_ratio`/`max_area_ratio` (default
0,6%-28%, range legacy verificato su dati reali in Milestone 29, non validato oltre
il punto più alto osservato — DB p.99, `0.630`). Un solo `structural_kind`,
`layout.interior_visual_frame`. Containment testo sul ramo vettoriale calcolato con
una funzione locale portata dallo script di Milestone 29 (`_union_bbox_contained_text`/
`_contains`, containment stretto, nessuna tolleranza — `measure_primitive_pair` non
utilizzabile su un bbox-unione arbitrario). Tre note esplicite in docstring: filtro
non simmetrico rispetto a `embedded_visual`; esclusione intenzionale del tetto legacy
0.70 (casi reali con `contained_text_area_ratio > 1.0` osservati in Milestone 29, non
un errore); relazione con `embedded_visual` = stesso precedente di governance di
`page_edge_visual`/`side_band` (overlap strutturale accettato, `AGENTS.MD:157`), non
un'analogia strutturale/semantica.

Nessuna modifica a `embedded_visual`, alle diagnostiche Milestone 25/26, a
`page_analysis_primitive_pair_measurements.py`. Nessun wiring nel job — milestone
separata, stesso schema di `embedded_visual` (Milestone 27 → wiring Milestone 28).

Implementato nel commit `16eb91c`. Baseline: Ruff verde, BasedPyright 0/0/0, 1187
test OK (1173 preesistenti + 14 nuovi), 7 skipped. Verificato da Chat A con clone
fresco post-commit (HEAD `16eb91c`): costanti di provenance, tutti e tre i filtri e
tutte e tre le note di docstring confermati presenti nel codice reale, non solo nel
diff revisionato.

Fuori scope: wiring nel job; distinzione box/tabella/fascia laterale (sovrapposizione
nota e accettata con `table_candidate` e `layout.side_band`, non risolta);
deduplica document-level; soglie di area come default definitivo (restano punto di
partenza esplicito, come `cluster_margin`).

**Milestone chiusa nel commit `16eb91c`.**

## Milestone 31 — wiring del quinto producer nel job (interior_visual_frame) — completata

Chiude il rinvio esplicito di Milestone 30 ("nessun wiring nel job"). Giro di
Modalità P breve con revisione Chat B indipendente
(`Proposta_Milestone31_InteriorVisualFrameWiring_v1.md`, non nel repo).

Wired `interior_visual_frame` (Milestone 30, `producer_version="0.1"`,
`configuration_id="interior-visual-frame-v1"`) accanto a `table_candidate`,
`page_covering_visual`, `page_edge_visual`, `embedded_visual` — stesso pattern di
Milestone 23/24/28: nuova entry in `_PRODUCER_SPECS` (`requires_pdfplumber=False`,
verificato indipendentemente da Chat B: nessun riferimento a pdfplumber nel
producer né nelle due diagnostiche da cui dipende), nuovo ramo nel dispatcher
`if`/`elif` esistente. Nessuna modifica a `page_analysis_interior_visual_frame.py`,
agli altri quattro producer, a `job_page_analysis_cache.py` o al binding documento.

Punto tecnico trovato in revisione, non anticipato dalla proposta: la fixture
`_create_interior_visual_job` (riusata da Milestone 28 per `embedded_visual`) non
inserisce testo — corretto per `embedded_visual`, che non lo richiede, ma
insufficiente per `interior_visual_frame`, che richiede `contained_text_primitive_count > 0`
su entrambi i rami. Nuova fixture dedicata `_create_interior_visual_frame_job`
(immagine più `page.insert_text`), con bbox del testo verificato empiricamente
prima di scrivere il test (`(130.0, 97.1, 139.3, 113.6)`, ampio margine dentro il
bbox immagine `(100, 80, 200, 140)`) per evitare un fallimento di containment
stretto per un pixel.

Test end-to-end `test_runs_interior_visual_frame_for_synthetic_framed_text`:
verifica `proposed_structural_kind == "layout.interior_visual_frame"` su un
candidate realmente prodotto, cache hit con `bind_pymupdf_pdfplumber_document_source`/
`capture_pymupdf_page` forzati ad `AssertionError` se richiamati. Test di simmetria
`include_pdfplumber` esteso a 5 producer.

Nota di processo: due incidenti git durante la chiusura, entrambi risolti senza
perdita di dati — un `git commit --amend` su un commit già pushato (rejection
non-fast-forward, il repo locale non aveva ancora `2a66f38` quando è iniziato il
lavoro su questa milestone) risolto con `git rebase origin/main` (nessun conflitto,
i due commit non toccano gli stessi file).

Implementato nel commit `a1a3269` (rebased a `57f8074`). Baseline: Ruff verde,
BasedPyright 0/0/0, 1188 test OK (1187 preesistenti + 1 nuovo — il secondo
requisito era un'estensione di un test esistente), 7 skipped, `git diff --check`
verde.

Fuori scope: modifiche al producer stesso; i fili già esplicitamente rinviati al
consumer/Resolution (soglia side_band × page_edge_visual, overlap
interior_visual_frame × table_candidate, dedup document-level per `content_digest`,
raffinamento `dispersion_ratio`) restano tali, non toccati da questa milestone.

**Milestone chiusa nel commit `57f8074`.**

## Milestone 32 — diagnostica esplorativa per struttura colonne (column-structure-diagnostics) — completata

Chiude la moratoria "colonne" mai affrontata da Milestone 7 (`State_Archive.md:175,
234, 290, 962`) e appartenente alla stessa famiglia di divieto "clustering"
sbloccata con lo stesso schema di cautela in Milestone 26 (`State_Archive.md:117,
135, 160-161, 228, 894, 921-926, 962`, sempre "salvo una futura decisione
architetturale dedicata"). Giro di Modalità P con revisione Chat B indipendente su
tre round successivi (documenti non inclusi nel repo:
`Proposta_Milestone32_ColumnStructureDiagnostics_v1/v2/v3.md`,
`Milestone32_Chiusura_FaseDiagnostica_v1/v2.md`).

`scripts/scan_column_structure_diagnostics.py` committato nel commit `935556d`,
stesso standard fissato in Milestone 29 (la base empirica citata in una proposta
resta verificabile nel repo). Nessun nuovo contratto pubblico, nessun
`RegionCandidate`, nessun `PageAnalysis`, nessun wiring nel job.

Segnale osservato: bande consecutive di righe (raggruppamento per overlap
verticale delle bbox, stessa approssimazione di `same_baseline_*`,
`State_Archive.md:139`) con conteggio locale di colonne stabile — determinato dai
gap orizzontali persistenti su una quota di righe (default 60%) all'interno di
ciascuna banda. Tre iterazioni, ciascuna motivata da un fallimento empirico reale,
non da preferenza:

1. whole-page: un istogramma unico su tutta l'altezza pagina, verificato fallire
   quasi ovunque su DB.pdf (`gap_count=0` su pagine con centinaia di primitive) —
   un solo elemento a piena larghezza (titolo, bordo tabella) cancella il gap per
   l'intera pagina nell'aggregazione OR;
2. persistenza per riga: recupera il segnale su DB.pdf, ma resta a livello di
   intera pagina — non descrive le pagine miste (due colonne interrotte da
   elementi a piena larghezza, poi due colonne di nuovo);
3. bande a conteggio colonne stabile (versione committata): segmenta le righe in
   bande consecutive con lo stesso conteggio locale di colonne, calcola la
   persistenza per banda separatamente. Verificato su un'immagine reale fornita
   dall'utente (corpo a due colonne → tabella a piena larghezza → titolo a piena
   larghezza → due colonne) e su casi sintetici, riprodotti indipendentemente da
   entrambe le Chat sul codice committato: sequenza 2→1→2 rilevata correttamente;
   un box con due sotto-colonne annidato in una colonna di corpo dà 2→3→2, con il
   gap originale del corpo ancora presente nella banda a 3 colonne — distinzione
   geometrica fra le due situazioni, non un'interpretazione del codice.

Eseguito su tre manuali reali con impaginazioni diverse (DB.pdf a due colonne con
tabelle, Lan.pdf a due colonne pulito, Apo.pdf mono-colonna con side band),
risultati ispezionati via CSV. Cinque confound osservati, distinti dal segnale di
corpo a due colonne reale:

- struttura tabellare/statblock con colonne interne (DB.pdf, `column_count` fino
  a 8-9) — coerente con la sovrapposizione già nota fra questo segnale e
  `table_candidate` (Milestone 29);
- side band di testo (Apo.pdf) — un gap persistente su un manuale confermato
  mono-colonna nel corpo;
- intestazione/piè di pagina ricorrente a posizione y fissa (Apo.pdf, DB.pdf) —
  una banda finale di una sola riga, sempre alla stessa y pagina dopo pagina; per
  costruzione una banda a una riga ha supporto sempre esattamente 0.0 o 1.0
  (proprietà matematica di `_persistent_gaps_for_rows`, non osservazione soggetta
  a rumore), quindi non distinguibile dal segnale reale guardando solo il
  supporto;
- flicker del conteggio colonne per riga isolata (trovato in revisione Chat B,
  verificato da Chat A sul codice reale): il conteggio è calcolato riga per riga,
  non su finestra — una singola riga sbilanciata dentro una regione a due colonne
  genuina spezza la sequenza (es. `[2,1,2,1,2]` invece di `[2]`).

Nessuna delle soglie (`bin_width`, `min_gap_width`, `min_support_ratio`) è
ratificata come default di produzione — stesso status di `cluster_margin`
(Milestone 26).

**Decisione architetturale presa in chiusura** (§1/§4 della proposta): né
`RegionCandidate` singolo né un fatto page-global scalare (analogo a
`CandidatePageContextMeasurements`, verificato più debole del previsto: misura
per-candidate, non page-global) descrivono da soli il fenomeno osservato — è
intrinsecamente una sequenza di regioni lungo l'asse verticale della pagina, non
un valore singolo né una proposta singola. Tre opzioni concrete, nessuna scelta
qui, per una futura milestone di progettazione dedicata (non numerata): un nuovo
tipo di fatto page-global strutturato (sequenza di bande, senza precedente
diretto nel repo); più istanze di `RegionCandidate` per pagina, una per banda —
il contratto lo permette già senza modifiche (nessun vincolo di cardinalità in
`page_analysis_model.py:107-118`, pattern già in uso per `side_band`/
`table_candidate`); una combinazione delle due. Quella milestone dovrà anche
specificare come distinguere una transizione reale (2→1→2) da un'eccezione
locale annidata (2→3→2) e dai confound di rumore (intestazioni/piè di pagina,
flicker per-riga).

Verificato in sandbox (Python 3.10, target dichiarato in `pyproject.toml` 3.14):
Ruff pulito, BasedPyright 0/0/0 con `--pythonversion 3.14`, controllo di
supporto non sostitutivo. Esecuzione funzionale confermata sull'ambiente reale
dell'utente su tre manuali e tre round di CSV; verifica Ruff/BasedPyright
esplicita sull'ambiente reale eseguita solo sulla prima versione dello script
(whole-page), non ripetuta esplicitamente dopo le riscritture v2/v3 — da fare
come parte della chiusura effettiva, non eseguita in questa sede.

Nessun test automatico committato per le funzioni dello script (verificato,
`tests/` non contiene file relativi a colonne): le verifiche sintetiche citate
sopra sono riproducibili solo estraendo manualmente le funzioni pure, come fatto
da entrambe le Chat in questo giro. Non bloccante per uno script diagnostico
esplorativo, stesso standard di Milestone 25/26/29, ma va detto esplicitamente,
non lasciato implicito.

Fuori scope: producer, wiring nel job, `RegionCandidate` o `structural_kind` per
colonne, scelta fra le tre opzioni architetturali del paragrafo sopra,
mitigazione dei cinque confound, soglie di produzione definitive.

**Milestone chiusa nel commit `935556d`**

## Milestone 33 — contratto per le bande di colonne (decisione architetturale, no build) — completata

Giro di Modalità P con revisione Chat B indipendente su tre round successivi
(documenti non inclusi nel repo: `Proposta_Milestone33_ColumnBandContract_v1/v2/v3.md`,
`Milestone33_Chiusura_v1.md`), ogni punto verificato sul codice reale prima di
essere integrato. Prende la decisione lasciata aperta in chiusura di Milestone
32 su come rappresentare la struttura a bande di colonne. Nessun codice
prodotto: solo documenti di decisione.

**Decisione**: struttura a colonne rappresentata come una `RegionCandidate`
minimale per banda (`proposed_structural_kind="layout.column_band"`, bbox =
estensione y della banda × larghezza pagina, `primitive_ids` = le primitive
della banda) più una misura satellite pura non ancora scritta
(`ColumnBandMeasurements`/`measure_column_band(...)`), stesso pattern già
stabilito da `measure_candidate_page_context` (Milestone 7,
`page_analysis_candidate_page_context_measurements.py`). Nessuna modifica a
`RegionCandidate` o `PageAnalysis`: `candidates` ammette già cardinalità
multipla per pagina senza vincoli (`page_analysis_model.py:199-205`, pattern
già in uso da `side_band`/`table_candidate`).

Scartate esplicitamente, con motivazione verificata: un nuovo tipo di fatto
page-global strutturato (nessun precedente nel repo per un fatto che sia esso
stesso una sequenza ordinata di sotto-fatti, status epistemico ambiguo dato
che deriva da soglie non ratificate); più `RegionCandidate` senza misura
satellite (nessun modo pulito di portare `column_count`/gap senza toccare
`structural_kind` con un pattern non usato altrove, o estendere
`RegionCandidate` stesso — decisione a sé, precedente Milestone 27).

Due punti verificati durante la revisione, risolti senza modifiche di
schema: l'ordine fra bande è ricostruibile ordinando i futuri `RegionCandidate`
per `bbox.y0`, proprietà garantita dall'algoritmo committato in Milestone 32
(`_cluster_rows`/`_segment_column_bands`, righe ordinate per `y0`, bande come
intervalli riga consecutivi non sovrapposti) — non un campo esplicito
necessario, e distinto dall'**interpretazione** della sequenza (transizione
reale 2→1→2 vs. eccezione locale annidata 2→3→2), non risolta qui;
il riferimento fra due candidate (es. banda vs. `table_candidate` sovrapposti)
non passa da `RegionRelation` (esiste già nello schema ma vincolato a
`LayoutRegion`, non a `RegionCandidate`, `page_analysis_model.py:167-182,
238-241`). I moduli satellite di Milestone 7
(`page_analysis_candidate_page_context_measurements.py`,
`page_analysis_candidate_extent_relation_measurements.py`) non vedono un
candidato diverso da quello ricevuto in input, ma il sottosistema Milestone
13-19 (`page_analysis_co_reference*.py`, chiuso) fornisce già questo:
`CoReferencedPageAnalyses` lega più `PageAnalysis` per la stessa pagina (una
per producer), `CoReferencedPageCandidateReference` identifica un candidato
specifico in uno di quegli stream, `measure_co_referenced_page_candidate_pair`
calcola gap/overlap/delta puri fra due candidate anche di producer diversi.
**Correzione rispetto alla chiusura originale**: non serve una funzione
satellite nuova in Milestone 34 — serve che il producer `column_band` esista
ed emetta il proprio stream, e una politica che usi quella misura per
decidere (materia di Resolution, non risolta da questa correzione).

Quattro decisioni esplicitamente rinviate a Milestone 34 (producer),
marcate come bloccanti per quella milestone, non come dettagli: trattamento
del flicker per-riga rispetto all'invariante `State.md:134` ("Resolution è
l'unico livello che può accettare, rifiutare o lasciare irrisolto un
candidato") — escludere dalla proposta (compatibile, pattern
`excluded_reason`/Milestone 26) vs. fondere bande adiacenti (decisione
strutturale, non compatibile, competenza di Resolution); gestione della
sovrapposizione banda/`table_candidate`/`embedded_visual` (DB.pdf,
`column_count` fino a 8-9); campi esatti della misura satellite
`ColumnBandMeasurements`, non schizzati qui; `proposed_structural_kind`
unico vs. distinzione già a livello di structural_kind fra bande "corpo" e
"struttura interna" (rischio di anticipare classificazione semantica in un
campo dichiarato strutturale, `AGENTS.MD:156`).

Fuori scope: producer, wiring, `RegionCandidate` o misura satellite
effettivamente scritti, soglie di produzione definitive
(`bin_width`/`min_gap_width`/`min_support_ratio`, invariate da Milestone 32).

**Milestone chiusa nel commit `e18a4a5`.**

## Milestone 34 — Resolution: design (Modalità P) e prima regola (deduplicazione IVF/EV) — completata

Design in `Proposta_ResolutionDesign_v3.md` (non nel repo, come da prassi già in uso per
Milestone 33 — `Proposta_Milestone33_ColumnBandContract_v1/v2/v3.md`), due giri di revisione
indipendente Chat B integrati (v1→v2, v2→v3), ogni citazione verificata prima di integrare.

**E1** (riapertura del sottosistema Milestone 13-19 per una misura pura di ratio candidato×
candidato, dichiarata bloccante in `Proposta_ResolutionDesign_v3.md` §10) è stata sbloccata in
sede di discussione diretta Chat A/utente, non messa per iscritto in un documento dedicato.
L'aggiornamento di questo file era stato sospeso in attesa dei risultati di testing e non è stato
fatto in tempo reale — sanato ora, retroattivamente, con questa voce.

**Decisione registrata** (non presa qui, solo trascritta): la duplicazione esatta
`interior_visual_frame`/`embedded_visual` è un caso di Resolution per applicazione del precedente
già ratificato in Milestone 24 (`page_edge_visual`/`side_band`) e confermato in Milestone 30
(docstring di `page_analysis_interior_visual_frame.py:23-29`, `AGENTS.MD:157-158`). Nessuna
modifica ai due producer.

**Commit**: `32a3389` (test di sottoinsieme IVF⊆EV, precondizione tecnica del prototipo, non
lavoro separato — `Proposta_ResolutionDesign_v3.md` §8.2.1), `cc89248`
(`resolution_model.py`/`resolution_page_candidates.py`, prima regola: identità esatta di
primitive fra IVF ed EV → accetta il più specifico, `reason_token="superseded_by_more_specific"`),
`9368a5c` (riapertura Milestone 13-19: `page_analysis_co_reference_candidate_overlap_ratio_measurements.py`,
overlap_area / min(area1, area2) — E1 soddisfatta), `ba94a34` (script standalone
`scripts/prototype_resolve_page_candidates_real_pages.py`, esecuzione su pagine reali non ancora
revisionata).

Fuori scope, invariato dal documento: `§8.2.2` (layout.table × IVF/EV, tabelle a bordo decorativo)
resta da fare — E1 sblocca il sottosistema di misura, non fornisce ancora evidenza sufficiente per
una regola su quella coppia (vedi Milestone 35).

**Milestone chiusa nei commit `32a3389`..`ba94a34`.**

## Milestone 35 — diagnostica di clustering vettoriale: filtro mancante, colore, frequenza — completata

Artefatto di origine: `3e10304` (diagnostica esplorativa `scan_table_candidate_visual_area_coverage.py`,
mai attribuito prima — assente sia dalla chiusura di Milestone 34 sia dalle prime versioni di
questa). Design in `Proposta_Milestone35_ClusteringColorDiagnostics_v1.md`..`v10.md` e
`Chiusura_Milestone35.md` (non nel repo, stessa prassi di Milestone 33/34), sette giri di
revisione Chat B integrati, ogni citazione verificata prima di integrare. Commit:
`610031c` (`scan_table_candidate_visual_area_coverage.py`), `d50eaee`
(`scan_embedded_visual_interior_visual_frame_twin_diagnostics.py`,
`summarize_milestone35_measures.py`), `c3742e1` (`inspect_milestone35_population_structure.py`),
`615db35` (fix chiave di join), `af821e7` (colonne `dispersion_ratio`/`avg_stroke_width`/
`is_closed_share`, opzione `--pages`), `63d4c25` (oracolo, rigenerato con `csv.writer` dopo
malformazione — v. nota sotto), `0a185a4`/`230c7fe` (test callout), `2fda096` (chiusura).

**Esito**: la premessa che ha originato la milestone (quattro pagine Lancer con un cluster
`embedded_visual` privo di gemello `interior_visual_frame`, lette come "pannelli decorativi
impilati") è stata **falsificata per ispezione visiva diretta**, non dalle quattro misure (i)-(iv)
originariamente previste — nessuno dei tre esiti previsti in §Criteri di chiusura si è verificato
alla lettera; la milestone chiude per falsificazione della premessa per via esterna alle misure, un
quarto esito non contemplato dai criteri originali, non da ricondurre a uno dei tre (in particolare:
non equivale all'esito 2, che richiedeva sotto-cluster color-partizionati fuori range o senza
testo — non osservato, criterio 1 è risultato 79/80 positivo). Tre delle quattro pagine sono box di
regole/stat-block a sfondo colorato, la quarta è lo sfondo a righe di una tabella dati reale —
nessuna è un pannello decorativo. Le misure (i)-(iv), eseguite comunque sui 7 manuali disponibili
(80 cluster target), non discriminano: criterio 3 (assenza di testo come causa) 0/80; criterio 1
(79/80) soddisfatto alla lettera ma non discriminante — un caso confermato falso (Dag p.24, scheda
personaggio) passa gli stessi filtri numerici di un caso confermato vero (Kul p.42, cornice
decorativa).

**Nessuna milestone di progettazione di un criterio di clustering per colore si apre**: oltre alla
non-discriminazione sopra, D5 quantifica il rischio già segnalato per pag. 119 (fondo zebra) — un
futuro criterio di clustering per colore, applicato senza eccezioni, produrrebbe 4-12 sotto-
candidati spuri per cluster sulle quattro pagine di origine (p.37 7 fill/7 stroke; p.114 8/12; p.119
5/4; p.131 4/7), la ragione concreta per cui la linea non viene aperta, non solo la decisione.

`dispersion_ratio` (Milestone 26): il gap osservato su etichette corrette (modulo/tabella ≤2.324,
decorativo ≥2.860) reggeva solo su n=2 dal lato decorativo, stesso manuale — verificato sul
controesempio già noto di `State.md` (Kul, illustrazione xilografica frammentata dal clustering;
indice 0-based 166/168, offset dedotto per tentativi con verifica visiva del contenuto, non
documentato in precedenza — analogo all'offset già noto per Lan, +2 pagine di frontespizio non
numerate). 72 cluster vettoriali reali su quelle pagine, `dispersion_ratio` 0.051–1.062 (mediana
0.773), tutti bassi quanto i moduli UI — **ma nessuno di questi 72 è nella fascia `above_max` che
questa milestone indaga** (0/150 righe totali, raster incluso). Il controesempio dimostra quindi che
`dispersion_ratio` basso ha due cause opposte su cluster piccoli/frammentati, non che il segnale
fallisca specificamente nella fascia d'uso dei cluster fuori tetto d'area — distinzione che non
cambia la conclusione operativa (n=2 era comunque insufficiente per una soglia) ma cambia lo stato
epistemico: il segnale non è escluso nella fascia rilevante, resta non provato.

Test di fattibilità (domanda dell'utente, indipendente da Chat B): il rilevatore di callout della
pipeline legacy (`ir_builder.py`, `_merge_callout_blocks`, pattern testuale titolo maiuscolo breve +
corpo ≥40 caratteri, riprodotto localmente solo nella logica stringa) separa 7 casi su 9
dell'oracolo secondo la mappatura `modulo_ui_*`/`tabella_zebra` → pattern atteso presente,
`pannello_decorativo*` → pattern atteso assente. **Concordanza valutata post-hoc sullo stesso
insieme di 9 casi**, dopo rimozione di un fallback (concatenazione testo del bbox) che produceva un
falso positivo su Kul p.0 — non una stima fuori campione. Falso negativo (DB p.124 ×2) spiegato
strutturalmente: modulo a campi vuoti, nessun paragrafo di corpo per costruzione. Non un
discriminante pronto — un candidato per un futuro producer, non deciso qui.

Bug trovato e corretto in corso di lavoro, non specifico di questa milestone: `cluster_id`/
`primitive_id` (`primitive_normalizer.py:141`) non sono univoci nel manuale, solo nella pagina
(`page_analysis_model.py:262`) — qualunque aggregazione cross-pagina che usi `cluster_id` da solo
come chiave rischia di fondere sotto-cluster di pagine diverse. Nota per futuri consumer.

Fuori scope, invariato: nessuna regola di Resolution su `layout.table`×`layout.embedded_visual`/
`layout.interior_visual_frame` (`Proposta_ResolutionDesign_v3.md` §8.2.2) — questa milestone
forniva evidenza, non l'ha trovata a supporto di una regola specifica basata su colore/clustering.
Non decisa: proposta di regola di processo per `AGENTS.MD` (ispezione visiva preventiva prima di
progettare una diagnostica attorno a un'assunzione sul contenuto delle pagine) — rimandata a
discussione separata.

**Milestone chiusa in `2fda096`.**
