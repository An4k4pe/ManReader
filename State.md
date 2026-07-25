# ManReader — Stato progetto

## Versione corrente

**v0.22** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–21 sono completate. Il primo producer Milestone 13+ è ora wired nel job
(`table_candidate`, Milestone 21, commit `93ee631`): esecuzione runtime-only sopra una
pagina già catturata, nessuna persistenza del risultato. Restano rinviate a milestone
future non ancora aperte né numerate: persistenza tracciata del `PageAnalysis` prodotto,
resume/batch multi-pagina, estensione di `CapturePageState` per un secondo artifact
(es. capture pdfplumber), wiring di un secondo producer.

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

## Milestone 6 — marginalia e bande laterali — completata

Obiettivo: proporre candidate strutturali di banda laterale senza cambiare output legacy.

La milestone ha consegnato candidate strutturali e strumenti diagnostici shadow per osservare side-band e geometria visuale senza modificare Resolution, IR, Markdown, EPUB o output legacy. La chiusura attesta il completamento del substrato diagnostico autorizzato, non un riconoscimento affidabile o concluso della marginalia. I producer text-only singleton e local-fragment restano baseline diagnostiche congelate.

```text
NormalizedPrimitivePage
→ hypothesis testuale geometrica
→ misura geometrica
→ candidate layout.side_band
→ diagnostica shadow separata
```

Micro-step completati:

1. `a7afdc7` — contratto `RegionCandidate` e `PageAnalysis.candidates`;
2. `a926c7c` — `TextHypothesisMeasurements` e `measure_geometric_text_hypothesis(...)`;
3. `e25eaa4` — `GeometricTextHypothesis` e hypothesis singleton canoniche;
4. `0d7f416` — rename neutrale delle measurements;
5. `e308fac` — `build_side_band_candidate_from_text_hypothesis(...)`;
6. `265ca16` — producer singleton side-band;
7. `1fc65ce` — diagnostica shadow singleton `analysis-side-band`;
8. `94d28dd` — helper privato `_build_local_horizontal_fragment_hypotheses(...)`;
9. `41863dc` — `build_local_fragment_side_band_page_analysis(...)`;
10. `f829850` — `Add local-fragment side-band diagnostic stage`.
11. `dcefd53` — `PrimitivePairMeasurements` e `measure_primitive_pair(...)`.
12. `624599c` — stage diagnostico `primitive-pair` in `pymupdf_capture_dump.py`.
13. `fd12ce6` — opzione diagnostica `--render-page-image PATH`.
14. `2943670` — stage diagnostico `primitive-neighborhood` in `pymupdf_capture_dump.py`.
15. `2fa3c69` — coverage ratio diagnostiche per `primitive-neighborhood`.
16. `0f33915` — producer `layout.page_covering_visual`, modulo dedicato e stage CLI `analysis-page-covering-visual`.
17. `831eae5` — producer `layout.page_edge_visual`, modulo dedicato e stage CLI `analysis-page-edge-visual`.
18. `9bb3fce` — stage read-only `side-band-local-fragment-diagnostics`.
19. `95ce905` — flag Unicode uppercase nella diagnostica read-only local-fragment.
20. `dfca953` — eccezione tipizzata per primitive prive di intersezione visibile positiva con la pagina.

Contratti disponibili:

- `RegionCandidate` e `PageAnalysis.candidates`, con `PageAnalysis` schema `1.2`, validazione e serializzazione;
- `GeometricTextHypothesis` e `TextHypothesisMeasurements` per selezioni testuali compatibili;
- `build_side_band_candidate_from_text_hypothesis(...)`, che converte primitive ID espliciti in `RegionCandidate(layout.side_band)` senza selezionare o raggruppare;
- `analysis-side-band`, `dump_singleton_side_band_page_analysis(...)` e CLI `--stage analysis-side-band` per il producer singleton;
- `analysis-side-band-local-fragment`, `dump_local_fragment_side_band_page_analysis(...)` e CLI `--stage analysis-side-band-local-fragment` per il producer local-fragment;
- `dump_side_band_local_fragment_diagnostics(...)` e CLI `--stage side-band-local-fragment-diagnostics`, diagnostica read-only dei candidate local-fragment side-band con JSON plain, non `PageAnalysis`; include `has_cased_characters_and_all_are_uppercase`, derivato direttamente e Unicode-aware da `normalized_text.isupper()`;
- `PrimitivePairMeasurements` e `measure_primitive_pair(...)` per la misura pura di una coppia esplicita text/image/drawing; `PrimitiveNotVisibleOnPageError` è una sottoclasse compatibile con `ValueError`, espone `primitive_id` e rappresenta esclusivamente una primitiva richiesta senza intersezione visibile positiva con la pagina;
- `dump_primitive_pair_measurements(...)` e CLI `--stage primitive-pair`, con `--first-primitive-id` e `--second-primitive-id`, per misurare due primitive esplicite;
- `dump_primitive_neighborhood_measurements(...)` e CLI `--stage primitive-neighborhood`, con `--primitive-id`, per osservare una primitiva esplicita rispetto alle altre primitive visibili della pagina; include `first_visible_width_ratio`, `first_visible_height_ratio`, `first_visible_area_ratio`, `neighbor_visible_width_ratio`, `neighbor_visible_height_ratio` e `neighbor_visible_area_ratio`;
- `build_page_covering_visual_page_analysis(...)`, `dump_page_covering_visual_page_analysis(...)` e CLI `--stage analysis-page-covering-visual` per candidate `layout.page_covering_visual`;
- `build_page_edge_visual_page_analysis(...)`, `dump_page_edge_visual_page_analysis(...)` e CLI `--stage analysis-page-edge-visual` per candidate `layout.page_edge_visual`;
- `--render-page-image PATH`, opzione trasversale che rende in PNG la stessa pagina analizzata per qualunque stage diagnostico.

### Producer distinti

```text
build_singleton_side_band_page_analysis(...)
→ page_analysis.singleton_side_band
→ singleton-side-band-v1
```

Il producer singleton usa solo hypothesis singleton e resta invariato.

```text
build_local_fragment_side_band_page_analysis(...)
→ page_analysis.local_fragment_side_band
→ local-fragment-side-band-v1
```

Il producer local-fragment è separato, usa il helper privato locale, misura ogni hypothesis e può produrre candidate `layout.side_band` multi-primitiva con ID deterministici. Non sostituisce il singleton.

Gli stage diagnostici sono separati:

```text
analysis-side-band
→ page_analysis.singleton_side_band
→ singleton-side-band-v1

analysis-side-band-local-fragment
→ page_analysis.local_fragment_side_band
→ local-fragment-side-band-v1
```

### Decisione di direzione dopo confronto side-band

Il percorso side-band text-only ha prodotto diagnostica utile, ma i producer sono ora congelati come baseline diagnostiche confrontabili: `singleton-side-band-v1` e `local-fragment-side-band-v1` restano invariati. Non sono autorizzate ulteriori calibrazioni locali delle soglie né altri flag lessicali. Il congelamento non significa detector completato, precisione o recall sufficienti, classificazione di marginalia o input pronto per Resolution.

I benchmark reali confermano il limite: DB p28 ha 12 candidate local-fragment (frammenti di corpo, intestazione tabellare e numeri); Lan p267 ne ha 8 (uppercase, punteggiatura, marker e frammenti); Lan p255 una candidate numerica `272`; Fab p271 ne ha 14, con veri elementi di banda `4` e `CAPITOLO` ma anche falsi positivi tabellari. DB p35 confronta singleton 22 e local-fragment 15: il footer è escluso, ma restano candidate corrispondenti a normali estremità di colonna. Kul p213 confronta 82 e 65: intercetta marginalia sinistra e riferimenti pagina, con molto rumore di punteggiatura. Apo p39 confronta 21 e 17: la banda destra larga è intercettata solo parzialmente e compaiono frammenti della colonna principale. Dag p92 confronta 12 e 9: il footer è escluso, ma restano normali frammenti di colonna.

La conclusione è che restringere l'outer band perderebbe contenuto positivo, mentre allargarla recupererebbe parte della banda larga di Apo aumentando i falsi positivi. I flag lessicali descrivono casi ma non separano marginalia, tabelle e corpo; local-fragment aggrega o riduce alcune candidate ma non ricostruisce una regione di banda completa. Il limite residuo richiede contesto strutturale più ampio, non un'altra soglia locale: non introdurre ora detector colonne, detector tabelle, clustering o Resolution.

I risultati reali indicano inoltre che il riconoscimento affidabile di bande laterali o marginalia non può basarsi soltanto su testo orizzontale vicino ai bordi; immagini, drawing e bbox visuali possono definire confini strutturali quanto il testo.

La nuova linea principale è quindi un substrato geometrico comune, multimodale, puro e non persistito. Il micro-step completato introduce `PrimitivePairMeasurements` e `measure_primitive_pair(...)`: misura una coppia esplicita di primitive text/image/drawing usando bbox originale e bbox visibile dopo clipping, e restituisce gap, overlap, ratio, contenimento, distanze dai bordi pagina e delta fra bordi e centri. Non classifica e non produce `RegionCandidate`.

Lo stage `primitive-pair` espone questa misura soltanto per i due ID forniti esplicitamente: non seleziona coppie, non produce candidate e non cambia `PageAnalysis`. L'opzione `--render-page-image PATH` produce esclusivamente il PNG diagnostico della pagina, senza overlay, crop o annotazioni, e non modifica il JSON dello stage.

`primitive-neighborhood` è solo osservazione diagnostica delle relazioni di una primitiva esplicita rispetto alle altre primitive visibili della pagina: non seleziona automaticamente candidate né introduce decisioni strutturali. Salta soltanto un neighbor quando riceve `PrimitiveNotVisibleOnPageError` con l'ID del neighbor corrente; l'errore della primitiva centrale e qualunque altro errore vengono propagati. Le coverage ratio sono derivate solo da bbox visibili e geometria pagina, non modificano `PrimitivePairMeasurements` né l'ordinamento dei neighbor, e non sono classificazioni, score, confidence o ranking.

Lo stage `side-band-local-fragment-diagnostics` non crea, filtra o modifica candidate e non produce `PageAnalysis`: descrive testo aggregato, ratio pagina, distanze dai bordi, flag formali e diagnostica same-baseline delle candidate local-fragment esistenti. `has_cased_characters_and_all_are_uppercase` coincide direttamente con `normalized_text.isupper()`: è Unicode-aware e puramente descrittivo. Lo stage non introduce evidence persistite, score, confidence, ranking, classificazioni semantiche o Resolution e non modifica candidate, producer o configurazioni.

Il producer page-covering produce `RegionCandidate`, non `LayoutRegion`: considera solo `ImageOccurrencePrimitive` e `DrawingPrimitive`, usa bbox visibile clipped alla pagina e soglie conservative `visible_width_ratio >= 0.95` e `visible_height_ratio >= 0.95`. Non classifica come background/decorative, non decide rimozione o export policy e non modifica neighborhood, IR, Markdown, EPUB o output legacy. Lo smoke reale ha individuato candidate page-covering dove presenti e non ne ha prodotto su una pagina sommario priva di visual full-page.

Il producer page-edge produce `RegionCandidate`, non `LayoutRegion`: considera solo `ImageOccurrencePrimitive` e `DrawingPrimitive`, usa bbox visibile clipped alla pagina e soglie conservative page-relative per visuali lunghe, sottili e aderenti ai bordi. Non importa né dipende da page-covering visual, non classifica come `decorative`, non decide rimozione o export policy e non modifica neighborhood, IR, Markdown, EPUB o output legacy.

Decisione architetturale: per ora non introdurre producer per visuali interne. Full-page e edge visual sono sufficienti come primo substrato visuale diagnostico; eventuali visuali interne vanno prima osservate con la diagnostica, non trasformate subito in candidate. Non introdurre ora `layout.visual_separator`, `layout.interior_visual_frame`, `layout.section_background` o structural kind analoghi.

Questa linea non introduce ancora detector generale, selezione automatica generalizzata di candidate, score, confidence, ranking semantico, clustering, grafo geometrico persistito, descrizione geometrica completa della pagina, modifiche a `PageAnalysis`, schema `1.3`, IR, Markdown, EPUB o output legacy.

### Debiti emersi dall'audit read-only

Osservazioni da riesaminare prima di ogni consolidamento: `_visible_bbox` è replicato in più moduli (duplicazione inizialmente utile per isolamento); il controllo dell'orientamento è duplicato fra hypothesis builder e measurements (difesa intenzionale dei contratti, con rischio di divergenza); `_is_conservative_side_band_singleton` è usato anche dal local-fragment e ha un nome più stretto dell'uso effettivo; `same_baseline_*` e `_same_baseline_diagnostics` misurano sovrapposizione verticale delle bbox, non una baseline tipografica verificata.

Restano inoltre ridondanza computazionale perché producer e candidate builder misurano nuovamente una hypothesis, mantenendo però il builder autonomo; nomi di stage CLI e funzioni pubbliche `dump_*` non sono uniformi; l'ordinamento di `primitive-neighborhood` è solo presentazione diagnostica e non va interpretato o riutilizzato come ranking.

Queste sono osservazioni, non autorizzazioni: nessun rename, rimozione, helper comune o refactor trasversale è autorizzato. Ogni eventuale intervento richiederà una decisione architetturale esplicita e un micro-commit separato, con verifica dei call site e della compatibilità diagnostica.

## Vincoli attivi della Milestone 6

- I producer propongono candidate, non semantica marginalia né decisioni finali.
- Le bbox sono canoniche e page-local; primitive condivise e candidate concorrenti sono ammessi, senza implicare ownership.
- Le hypothesis singleton sono ordinate canonicamente, non in reading order. Il raggruppamento local-fragment resta privato, side-band-specifico e non è un layer neutrale riusabile.
- I producer non introducono evidence persistite, score, confidence, ranking o provenance candidate-level.
- `build_singleton_side_band_page_analysis(...)`, `page_analysis.singleton_side_band`, `singleton-side-band-v1`, `analysis-side-band`, `PageAnalysis` schema `1.2`, IR, Markdown, EPUB e output legacy restano invariati; il confronto local-fragment usa lo stage separato `analysis-side-band-local-fragment`.
- I JSON diagnostici reali non vanno committati. Ogni modifica futura a soglie o semantica deve cambiare il relativo `configuration_id`.
- I test sintetici, diff e stato Git sono obbligatori; eseguire smoke DB quando una modifica influenza pipeline o renderer.

## Fuori scope corrente

Non sono autorizzati:

- schema `1.3`, modifiche a `PageAnalysis`, evidence persistite, score, confidence o ranking;
- nuovi tipi pubblici `Block`, `Cluster`, `Span` o `Group`; clustering generico o framework di clustering;
- detector colonne, tabelle, callout o liste; scanner generale di marginalia o produzione generale di candidate;
- IR, Markdown, EPUB, output legacy, resolution, policy editoriale, ownership, coverage, profili, GUI, AI o SQLite;
- refactor generale di `extractor.py`, hardcode su manuale/pagina/titolo/parola o formati carta nominali.

## Prossimo passo operativo

Prima di qualunque nuova milestone serve una nuova decisione architetturale esplicita in Chat A. Non sono autorizzati nuovi file, codice, test o comportamento. I debiti del capture runner restano separati, quelli dell'audit vanno valutati separatamente e JSON/PNG diagnostici reali non vanno committati.

## Ultima baseline funzionale verificata

Commit `5e2c91d` — `Diagnosis local page`: 87 test mirati OK, 1120 test complessivi OK e 7 skipped; Ruff verde; BasedPyright: 0 errori, 0 warning, 0 note; `git diff --check` verde.

## Milestone 7 — contesto strutturale page-level — completata

Obiettivo: produrre osservazioni page-local, verificabili e non decisionali sul rapporto fra candidate esistenti, primitive visibili e contesto complessivo della pagina. Non identifica ancora corpo pagina, colonne, tabelle, marginalia, header/footer, callout o decorazioni.

Risultati completati: `CandidatePageContextMeasurements` e `measure_candidate_page_context(...)`; diagnostica JSON local-fragment page-context; `CandidateExtentRelationMeasurements`, `CandidateNonCandidateExtentRelationMeasurements` e `measure_candidate_non_candidate_extent_relations(...)`; diagnostica JSON relazionale local-fragment e stage CLI diagnostici separati. Gli smoke reali coprono DB p28, Fab p271 e Lan p255.

Primo contratto puro disponibile, implementato:

```python
CandidatePageContextMeasurements

measure_candidate_page_context(
    primitive_page: NormalizedPrimitivePage,
    *,
    candidate: RegionCandidate,
) -> CandidatePageContextMeasurements
```

Il contratto è disponibile in `page_analysis_candidate_page_context_measurements.py`, con test sintetici in `tests/test_page_analysis_candidate_page_context_measurements.py`.

Micro-step completato: `7779715` introduce `page_analysis_candidate_extent_relation_measurements.py` e `measure_candidate_non_candidate_extent_relations(...)`. Riceve direttamente un `CandidatePageContextMeasurements` e restituisce `CandidateNonCandidateExtentRelationMeasurements`, con relazioni separate per extent text, image e drawing tramite `CandidateExtentRelationMeasurements`.

Le relazioni espongono soltanto gap e overlap sui due assi e contenimento inclusivo nei due versi. La bbox della candidate è usata invariata; una famiglia senza extent ha extent e relation entrambi `None`. Il contratto è puro, derivato, deterministico e non persistito: non esegue una nuova scansione delle primitive, clipping, chiamate ai producer o produzione di `PageAnalysis`.

Non introduce `intersects`, ratio, distanza euclidea, direzioni nominali, soglie, score, confidence, ranking, evidence o classificazioni. Non modifica producer, diagnostica CLI, schema `1.2`, serializzazione, store, Resolution, IR, Markdown, EPUB, renderer o pipeline legacy.

Micro-step completato: `page_analysis_candidate_page_context_diagnostics.py` espone `dump_local_fragment_side_band_candidate_page_context(...)` e lo stage CLI `candidate-page-context-local-fragment-side-band`. Riusa `measure_candidate_page_context(...)` sulle candidate, nello stesso ordine, del producer local-fragment side-band congelato e restituisce JSON plain, non `PageAnalysis`. Non modifica producer, schema, IR, Markdown, EPUB, legacy, Resolution, persistenza, score, confidence, ranking o evidence.

Micro-step completato: `b5d2321` introduce `page_analysis_candidate_extent_relation_diagnostics.py`, `dump_local_fragment_side_band_candidate_extent_relations(...)` e lo stage CLI `candidate-page-context-extent-relations-local-fragment-side-band`. Compone il producer local-fragment side-band esistente, `measure_candidate_page_context(...)` e `measure_candidate_non_candidate_extent_relations(...)`, conserva l'ordine delle candidate e converte il risultato in JSON plain separato dallo stage page-context precedente. Non modifica producer, measurements, `PageAnalysis`, schema o pipeline autorevoli.

Smoke reali: DB p28 ha 12 candidate, con text extent non-candidate ampio e separato da image/drawing quasi page-covering; Fab p271 ha 14 candidate e pattern analogo con image extent quasi full-page; Lan p255 ha una candidate, text extent nella parte bassa e image/drawing page-wide su canali separati.

Conclusione: separare text, image e drawing evita che background, immagini o drawing page-wide nascondano il contesto testuale. Non è una classificazione e non autorizza detector, ranking o Resolution.

Smoke relazionali: DB p28 ha 12 candidate, tutte contenute negli extent text, image e drawing con gap nulli. Fab p271 ha 14 candidate: image e drawing le contengono tutte, text ne contiene 13; `primitive:text:text:b0000:l0000:s0000` oltrepassa il bordo destro del text extent ed è solo parzialmente sovrapposta. Lan p255 ha una candidate: text e drawing la contengono, mentre image termina circa 1.0005 pt sopra la candidate, con vertical gap positivo, vertical overlap nullo e nessun contenimento.

Conclusione relazionale: l'invarianza osservata degli extent è comportamento atteso, non un difetto. Le relazioni aggiungono informazione verificabile nei casi di bordo; per candidate interne a extent ampi descrivono soprattutto il contenimento. Gli smoke non autorizzano ratio, nuove distanze, score, confidence, ranking, evidence, detector o classificazioni.

Smoke temporaneo page-edge, tramite sole API pubbliche: Fab p246 conferma 3 candidate `layout.page_edge_visual`, tutte misurate senza eccezioni e con output deterministico. Le candidate visuali sono basate su primitive image; il leave-one-candidate-out funziona e l'image extent non-candidate contiene tutte e tre le candidate per la presenza di altre immagini. Le relazioni text differiscono: barra verticale e barra superiore sono sovrapposte al text extent, mentre la linea sottile superiore ne è separata verticalmente di circa 0.3429 pt, con vertical overlap nullo. Non emergono incoerenze fra extent e relation e nessun file diagnostico è stato committato.

Campi minimi disponibili:

```text
candidate_id: str
page_id: str
candidate_bbox: BBox
candidate_primitive_ids: tuple[str, ...]
non_candidate_visible_text_primitive_count: int
non_candidate_visible_text_extent_bbox: BBox | None
non_candidate_visible_image_primitive_count: int
non_candidate_visible_image_extent_bbox: BBox | None
non_candidate_visible_drawing_primitive_count: int
non_candidate_visible_drawing_extent_bbox: BBox | None
```

Vincoli: misura pubblica, pura, deterministica e non persistita, senza mutare gli input, produrre `PageAnalysis`, CLI, chiamate interne ai producer esistenti o extent misto. Gli extent restano separati per text, image e drawing. Non introduce gap, overlap, distanza, ratio, score, confidence, ranking, evidence, classificazione, schema `1.3`, modifiche a `PageAnalysis`, nuovi `LayoutRegion`, `RegionCandidate` o structural kind, persistenza, detector generale, clustering, Resolution, ownership, coverage finale o refactor trasversale di `_visible_bbox`.

Semantica: sono escluse tutte le primitive in `candidate.primitive_ids`, anche se non visibili; le altre sono considerate solo nella loro intersezione visibile positiva con la pagina. Le primitive non-candidate completamente invisibili sono ignorate e quelle parzialmente fuori pagina sono clipped prima dell'extent. Per ogni tipo senza primitive non-candidate visibili il risultato è `count == 0` ed `extent is None`; `candidate.primitive_ids == ()` è valido.

Edge case: `candidate.page_id` diverso da `primitive_page.page_id` deve sollevare `ValueError` con il page ID rilevante; un ID candidate inesistente deve sollevare `ValueError` che identifichi il `primitive_id`; input runtime di tipo errato saranno rifiutati coerentemente con lo stile dei contratti esistenti.

Conclusione architetturale: gli obiettivi della Milestone 7 sono soddisfatti. I contratti sono puri, pubblici, deterministici, producer-agnostic e non persistiti; descrivono contesto page-local e relazioni geometriche senza produrre fatti strutturali. Non identificano body, colonne, tabelle, marginalia, header/footer, callout o decorazioni e non introducono ratio aggiuntivi, score, confidence, ranking, evidence, detector, classificazioni o Resolution. `PageAnalysis` resta schema `1.2`; pipeline legacy, IR, Markdown ed EPUB restano autorevoli e invariati. Page-covering non è stato esteso nella Milestone 7 e non serve altro codice per la chiusura.

Compatibilità: la Milestone 6 resta completata e congelata come baseline diagnostica; singleton e local-fragment restano baseline diagnostiche, non detector affidabili.

## Milestone 8 — contratto document-local di analisi — completata

Obiettivo completato: definire un contenitore immutabile, puro e versionato per una singola generazione documentale coerente, che riferisca in ordine sorgente al massimo una `PageAnalysis` disponibile per pagina e ammetta documenti parziali.

Document-local significa una sola sorgente PDF immutabile, ordine delle pagine sorgente e non reading order, riferimenti logici a `PageAnalysis` e pagine mancanti ammesse. Non identifica ancora pattern documentali e non introduce semantica, Resolution o decisioni sulle candidate.

Primo contratto disponibile, implementato:

```text
document_analysis_model.py
tests/test_document_analysis_model.py
DOCUMENT_ANALYSIS_SCHEMA_VERSION = "1.0"
```

```text
PageAnalysisReference
  page_index: int
  page_id: str
  page_analysis_schema_version: str
  page_analysis_generation_id: str
  provenance: PageAnalysisProvenance

DocumentAnalysisProvenance
  source_id: str
  producer_name: str
  producer_version: str
  configuration_id: str

DocumentAnalysis
  schema_version: str
  generation_id: str
  page_count: int
  provenance: DocumentAnalysisProvenance
  pages: tuple[PageAnalysisReference, ...] = ()
```

Micro-step completato: `b950201` introduce `document_analysis_model.py` e `tests/test_document_analysis_model.py`, con `DocumentAnalysisProvenance`, `PageAnalysisReference` e `DocumentAnalysis`. `DOCUMENT_ANALYSIS_SCHEMA_VERSION = "1.0"`. Il contratto è immutabile, puro, deterministico e non persistito; rappresenta una selezione document-local coerente, ordinata per `page_index`, con al massimo un riferimento per pagina e gap ammessi.

Secondo micro-step completato: `308f5db` introduce `document_analysis_reference.py` e `tests/test_document_analysis_reference.py`, con `build_validated_page_analysis_reference(...)`. Riceve una `NormalizedPrimitivePage` e la relativa `PageAnalysis`, riusa integralmente `validate_page_analysis_against_primitive_page(...)` e produce un solo `PageAnalysisReference`: `page_index` deriva esclusivamente da `NormalizedPrimitivePage.page_index`, mentre `page_id`, schema, generation ID e provenance derivano dalla `PageAnalysis`. Non ordina, non muta e non carica artifact. Il costruttore diretto della dataclass resta disponibile come contratto dati di basso livello; il percorso canonico da oggetti reali usa la factory validata.

La factory attesta soltanto la coerenza page-local: non attesta che `page_count` o l'indice appartengano a un'autorità documentale superiore, non inferisce `page_count` e non costruisce `DocumentAnalysis`.

Conclusione di chiusura: esiste ora il contratto document-local puro e versionato, con una selezione coerente e ordinata di riferimenti pagina, documenti parziali ammessi e un percorso canonico validato per costruire un singolo riferimento. Non introduce semantica, Resolution o decisioni editoriali e non modifica pipeline legacy, IR, Markdown o EPUB.

Al momento della chiusura della Milestone 8 non era ancora scelta l'autorità concreta per l'acquisizione attestata di `page_count`. La Milestone 9 ha ora scelto come primo confine il producer PDF/PyMuPDF applicato agli stessi byte dello snapshot verificato; manifest, capture completa e altre autorità restano fuori dalla decisione corrente. Resta invariato il vincolo storico: non inferire `page_count` da pagine parziali né da `max(page_index) + 1`.

Decisioni identitarie: non esiste `document_id`; `source_id` identifica il PDF immutabile e il soggetto tecnico dell'analisi, mentre `DocumentAnalysis.generation_id` identifica la generazione documentale. Il riferimento pagina riusa `PageAnalysisProvenance`; `page_id` deve coincidere con `provenance.source_page_id` e `page_analysis_schema_version` con `PAGE_ANALYSIS_SCHEMA_VERSION` (oggi `1.2`). Non vengono riferiti path, digest o artifact fisici.

Semantica di `pages`: tuple strettamente ordinata per `page_index`, zero-based, con ogni indice in `0 <= page_index < page_count`, al massimo un riferimento per indice e `page_id` unici. Gap iniziali, interni e finali sono ammessi; `page_count > 0` con `pages == ()` è valido, mentre `page_count == 0` richiede `pages == ()`. I `page_analysis_generation_id` possono essere uguali o differenti fra pagine; i `source_capture_id` devono essere unici fra i riferimenti inclusi.

Le analisi pagina incluse riusano `PageAnalysisProvenance` e devono condividere `source_id`, schema `PageAnalysis`, schema primitive, producer `PageAnalysis`, versione producer e configurazione. Il producer documentale può differire dal producer pagina. Il modello `DocumentAnalysis` non carica né valida oggetti `PageAnalysis` completi; la validazione cross-model avviene esclusivamente nella factory quando il riferimento viene costruito da oggetti reali. `DocumentAnalysis` resta una selezione coerente di analisi pagina, non un catalogo multiproducer, una fusione di analisi concorrenti, una Resolution, una scelta della migliore analisi o un artifact persistito.

Restano fuori scope: builder documentale; filesystem e artifact fisici, artifact resolution, serializzazione e store; CLI e diagnostica; `JobManifest`, capture progress e workspace; relazioni multipagina, pattern ricorrenti, continuation candidate, candidate↔candidate; Resolution e accept/reject/unresolved; body, colonne, tabelle, marginalia, header/footer e callout; detector, score, confidence, ranking, evidence, ownership e coverage; modifiche a `PageAnalysis` o schema `1.3`; IR, Markdown, EPUB, renderer, pipeline legacy e refactor dei debiti delle Milestone 6–7.

## Milestone 9 — attestazione della sorgente documentale — completata

Obiettivo completato: definire un risultato tecnico locale, puro e immutabile che leghi l'identità verificata di una precisa sequenza di byte, il `source_id` prodotto e il `page_count` letto da quegli stessi byte.

Attestazione non significa firma, autenticità editoriale, certificazione esterna, prova persistente o garanzia che il path mantenga in futuro gli stessi byte.

Decisioni consolidate:

- `source_id` resta opaco nei contratti generali; il primo producer PDF/PyMuPDF lo deriva internamente dal digest SHA-256;
- l'autorità su `page_count` appartiene al reader applicato agli stessi byte verificati; `CaptureProgress.page_count` è un dato operativo registrato, non l'autorità che determina il conteggio;
- il controllo corrente in `capture_job_page(...)` resta una precondizione locale e non un'attestazione riusabile;
- hash, dimensione e `page_count` devono essere calcolati dalla stessa sequenza immutabile di byte acquisita una sola volta, eliminando la finestra TOCTOU fra verifica del file e apertura PDF;
- il contratto puro resta backend-neutral, mentre il primo producer può essere specifico per PDF/PyMuPDF;
- `page_count == 0` resta ammesso dal contratto se restituito validamente dal backend; non esiste attestazione parziale.

Primo micro-step completato: `65d4b2c` — `Add document source attestation`.

```text
document_source_attestation_model.py
pymupdf_document_source_attestation.py
tests/test_document_source_attestation_model.py
tests/test_pymupdf_document_source_attestation.py
verified_file_model.py
tests/test_verified_file_model.py
```

Contratto puro implementato:

```text
DOCUMENT_SOURCE_ATTESTATION_SCHEMA_VERSION = "1.0"

DocumentSourceAttestation
  schema_version: str
  verified_file: VerifiedFileReference
  source_id: str
  page_count: int
```

`DocumentSourceAttestation` è una dataclass `frozen=True, slots=True`, pura, immutabile e backend-neutral: schema esattamente `1.0`, `verified_file` del tipo corretto, `source_id` stringa non vuota e `page_count` intero non booleano e non negativo; `page_count == 0` è valido. Non conserva path, byte buffer, handle, oggetti `fitz` o dati backend-specifici; non esiste un invariante generale `source_id == verified_file.sha256`. La costruzione diretta valida soltanto la forma, mentre la provenienza verificata è garantita dal producer canonico. Non è firma, autenticità editoriale o certificazione esterna.

`inspect_verified_bytes(data: bytes) -> VerifiedFileReference` è il helper puro e deterministico per una sequenza `bytes` esplicita: calcola SHA-256 e dimensione senza modificare `inspect_verified_file(...)` o `verify_file(...)`, le cui firme e comportamenti restano invariati.

Producer canonico implementato:

```python
attest_pymupdf_document_source(
    snapshot_path: Path,
    *,
    expected_file: VerifiedFileReference,
) -> DocumentSourceAttestation
```

Il producer legge lo snapshot una sola volta, calcola digest e dimensione sul buffer acquisito e confronta separatamente entrambi con `expected_file` prima di invocare PyMuPDF. PyMuPDF apre lo stesso buffer verificato e non riapre il path: ciò elimina la finestra TOCTOU fra verifica e parsing. Il producer rifiuta mismatch, PDF malformati e documenti che richiedono autenticazione, legge `page_count` dallo stesso buffer, deriva internamente `source_id` dal digest osservato e restituisce il `VerifiedFileReference` ricostruito dai byte acquisiti. Accetta sottoclassi valide di `VerifiedFileReference`, incluso `SourceReference`, senza dipendere da `job_manifest_model`; chiude sempre il documento PyMuPDF e non scrive file né produce artifact o stato. L'attestazione descrive i byte acquisiti e non garantisce che il path resti invariato dopo il ritorno.

Conclusione di chiusura: la Milestone 9 attesta che il producer canonico PyMuPDF ha acquisito una precisa sequenza di byte dallo snapshot, ne ha verificato SHA-256 e dimensione rispetto al riferimento atteso, ha derivato da essa il `source_id` e ha letto il `page_count` aprendo quegli stessi byte.

Non attesta autenticità editoriale, firma, certificazione esterna, futura immutabilità del path, persistenza dell'attestazione, provenance o audit trail persistenti, utilizzo dei byte attestati da parte della capture, né utilizzo da parte di `DocumentAnalysis` o di altri consumer.

Non è necessario un secondo micro-step: contratto e producer soddisfano già l'obiettivo della milestone. Un builder verso `DocumentAnalysis` richiederebbe generation ID, provenance, riferimenti pagina, selezione e ordinamento senza rafforzare la garanzia byte–digest–conteggio; l'integrazione nel capture runner sarebbe una modifica operativa separata; modifiche a `JobManifest` o `initialize_job(...)` introdurrebbero schema, migrazione, lifecycle e persistenza. Streaming, mmap, locking o file temporanei sono ottimizzazioni rinviabili e devono comunque preservare l'identità degli stessi byte. Questa motivazione non costituisce una roadmap implicita.

Debiti operativi separati e non bloccanti: il capture runner verifica il file e successivamente riapre il path, conservando una propria finestra TOCTOU; inoltre una pagina già completata può essere saltata prima della nuova verifica dello snapshot. Questi punti non invalidano la Milestone 9 perché la milestone non dichiara che la capture utilizzi già l'attestazione; non vanno qui ulteriormente diagnosticati né è autorizzata la loro correzione.

Restano fuori scope: persistenza e serializzazione; provenance del producer nel contratto; audit trail; password per PDF cifrati; producer alternativi; ottimizzazione della memoria per PDF grandi; builder di `DocumentAnalysis`; caricamento o selezione di `PageAnalysis`; manifest e capture integration; artifact resolution; CLI e diagnostica; detector, relazioni multipagina e Resolution; modifiche a `PageAnalysis`; pipeline legacy, IR, Markdown ed EPUB.

## Milestone 10 — costruzione attestata di DocumentAnalysis — completata

La milestone ha definito un bridge puro e validato che costruisce un solo `DocumentAnalysis`, derivando `page_count` e `DocumentAnalysisProvenance.source_id` esclusivamente dalla stessa `DocumentSourceAttestation` e delegando ai modelli tutti gli invarianti document-local già esistenti.

Nel percorso canonico da una sorgente reale attestata, `DocumentAnalysis.page_count` e `DocumentAnalysisProvenance.source_id` derivano dalla stessa `DocumentSourceAttestation`.

Il costruttore diretto di `DocumentAnalysis` resta disponibile come contratto dati di basso livello; la factory è il percorso canonico quando è disponibile una `DocumentSourceAttestation`. `DocumentAnalysis` non incorpora né conserva l'attestazione, `VerifiedFileReference`, digest, path o prova del percorso costruttivo: un oggetto isolato non può dimostrare da solo di essere stato costruito tramite factory. La garanzia riguarda il percorso canonico e non è una nuova proprietà persistita nello schema; nessuno schema viene modificato.

Primo micro-step completato: `20b240b` — `Add attested document analysis factory`.

```text
document_analysis_from_attestation.py
tests/test_document_analysis_from_attestation.py
```

```python
build_attested_document_analysis(
    attestation: DocumentSourceAttestation,
    *,
    generation_id: str,
    producer_name: str,
    producer_version: str,
    configuration_id: str,
    pages: tuple[PageAnalysisReference, ...] = (),
) -> DocumentAnalysis
```

La factory verifica direttamente soltanto che `attestation` sia una `DocumentSourceAttestation`, altrimenti solleva `ValueError("attestation must be a DocumentSourceAttestation")`. Fissa `DocumentAnalysis.schema_version` a `DOCUMENT_ANALYSIS_SCHEMA_VERSION`, deriva esclusivamente dalla stessa attestazione `page_count` e `DocumentAnalysisProvenance.source_id`, costruisce la provenance con i tre metadati producer forniti e usa il `generation_id` del chiamante. Passa `pages` direttamente al costruttore di `DocumentAnalysis` e restituisce un solo oggetto; la firma non permette di fornire `source_id`, `page_count`, `schema_version` o una `DocumentAnalysisProvenance` completa. Restano responsabilità del chiamante `generation_id`, i tre metadati producer e la tuple già selezionata e ordinata dei riferimenti.

La factory non duplica i controlli di `DocumentAnalysisProvenance` e `DocumentAnalysis`: metadati producer, `generation_id`, tipo e contenuto di `pages`, ordine, unicità, limiti rispetto a `page_count`, coerenza dei `source_id`, omogeneità page-level, documenti parziali, gap, tuple vuota e `page_count == 0` restano delegati ai modelli. Le loro eccezioni propagano senza wrapping.

`pages` accetta esclusivamente una `tuple[PageAnalysisReference, ...]`, con default `()`, già selezionata e ordinata: la factory non converte iterable generici, non ordina, deduplica, filtra, seleziona, muta o costruisce riferimenti pagina. Non inferisce `page_count` da `len(pages)`, `max(page_index) + 1` o dalla presenza/assenza delle pagine finali.

I test verificano derivazione di `page_count` e source ID dall'attestazione, assenza di parametri di override, provenance documentale corretta e schema corrente; documenti parziali con gap, `pages == ()` con `page_count > 0` e attestazione con `page_count == 0` e tuple vuota; rifiuto di riferimenti fuori intervallo, source ID incoerente, pagine non ordinate e `pages` non tuple; determinismo, assenza di mutazione e nessun ordinamento implicito.

Conclusione di chiusura: quando una `DocumentSourceAttestation` è fornita al percorso costruttivo canonico `build_attested_document_analysis(...)`, il `DocumentAnalysis` risultante riceve `page_count` e `DocumentAnalysisProvenance.source_id` esclusivamente dalla stessa attestazione, senza override pubblico né inferenza dalle pagine. `DocumentAnalysisProvenance` e `DocumentAnalysis` continuano ad applicare ordine, unicità, limiti rispetto a `page_count`, coerenza della sorgente, omogeneità page-level, documenti parziali, gap e tuple vuote.

La milestone non garantisce che un `DocumentAnalysis` isolato dimostri di essere stato costruito dalla factory. Il risultato non incorpora né conserva `DocumentSourceAttestation`, `VerifiedFileReference`, digest, path, prova del percorso costruttivo o audit trail. Non costruisce i singoli `PageAnalysisReference`, non carica, seleziona o ordina pagine, non integra manifest, capture o filesystem, non persiste il risultato, non introduce osservazioni multipagina né modifica schemi esistenti. Il costruttore diretto di `DocumentAnalysis` resta disponibile come contratto dati di basso livello.

Non è stato necessario un secondo micro-step: la factory introduce già la garanzia cross-model prevista, la firma impedisce override di source ID, page count, schema e provenance completa, non inferisce il conteggio dalle pagine e delega gli invarianti ai modelli. Un eventuale test di composizione con `build_validated_page_analysis_reference(...)` sarebbe una copertura ridondante e non bloccante, perché documenterebbe un uso già possibile senza introdurre un nuovo invariante; una factory end-to-end o batch, l'incorporazione o persistenza dell'attestazione, manifest, capture, filesystem e osservazioni document-local richiederebbero politiche o contratti distinti. Queste motivazioni non costituiscono una roadmap implicita.

Restano fuori scope: modifiche a `DocumentAnalysis`, `DocumentAnalysisProvenance`, `PageAnalysis`, `DocumentSourceAttestation` o relativi schema; factory batch o end-to-end; costruzione dei singoli `PageAnalysisReference`; caricamento e selezione di `PageAnalysis`; ordinamento automatico; filesystem e PDF; manifest, workspace e capture runner; persistenza, serializer, store e artifact resolution; CLI e diagnostica; osservazioni o relazioni multipagina; pattern ricorrenti; detector, classificazioni, score e confidence; Resolution; pipeline legacy, IR, Markdown ed EPUB.

## Milestone 11 — binding in memoria delle analisi pagina documentali — completata

La milestone ha definito un contratto pubblico, puro, immutabile e validato che associa posizionalmente un `DocumentAnalysis` a tutte e sole le `PageAnalysis` indicate dai suoi riferimenti. Il binding è completo rispetto a `DocumentAnalysis.pages`: il documento può essere parziale rispetto al PDF, ma il binding non può esserlo ulteriormente.

Primo e unico micro-step completato: `5bd634a` — `Add document analysis binding`.

```text
document_analysis_binding.py
tests/test_document_analysis_binding.py
```

Tipi e factory ratificati:

```python
BoundPageAnalysis(
    reference: PageAnalysisReference,
    analysis: PageAnalysis,
)

BoundDocumentAnalysis(
    document_analysis: DocumentAnalysis,
    pages: tuple[BoundPageAnalysis, ...],
)

bind_document_analysis(
    document_analysis: DocumentAnalysis,
    *,
    analyses: tuple[PageAnalysis, ...],
) -> BoundDocumentAnalysis
```

I contratti implementati sono `BoundPageAnalysis`, `BoundDocumentAnalysis` e `bind_document_analysis(...)`: pubblici, puri, immutabili, non versionati e validati anche nella costruzione diretta. Il binding è completo rispetto a `DocumentAnalysis.pages`; accetta esclusivamente una `tuple` in `analyses`, della stessa lunghezza dei riferimenti, e `DocumentAnalysis.pages == ()` richiede e ammette `analyses == ()`. L'associazione è esclusivamente posizionale: non carica, cerca, converte, ordina, seleziona, deduplica, filtra o risolve artifact.

Ogni coppia verifica `page_id`, schema `PageAnalysis`, generation ID e uguaglianza completa della provenance. Il contenitore verifica inoltre che ciascun riferimento coincida logicamente con quello nella stessa posizione di `DocumentAnalysis.pages`. Gli invarianti usano uguaglianza logica, non identità Python; factory e contenitori conservano l'identità di documento, riferimenti e analisi ricevuti senza copiarli. Gli errori restano `ValueError` con token identificativi stabili, senza rendere stabile l'intera frase. Documenti vuoti e documenti parziali rispetto al PDF con gap sono ammessi quando tutte e sole le analisi riferite sono fornite.

Conclusione di chiusura: il binding associa posizionalmente un `DocumentAnalysis` a tutte e sole le `PageAnalysis` indicate; costruzione diretta e factory sono validate, l'uguaglianza logica e l'identità degli input sono preservate secondo il contratto. Non sono stati introdotti loader, lookup, ordinamento, selezione, persistenza o Resolution.

La revisione indipendente ha dato verdetto **CHIUDIBILE**: non ha rilevato difetti bloccanti, controlli identitari mancanti o allargamenti di scope. Non serve un secondo micro-step perché l'obiettivo della milestone è interamente soddisfatto; i limiti residui sono fuori scope dichiarati, non lacune del binding.

Il binding garantisce la corrispondenza riferimento–`PageAnalysis`, ma non attesta che il riferimento sia stato costruito tramite la factory page-local e non rivalida contro `NormalizedPrimitivePage`.

Restano fuori scope: modifiche ai modelli o agli schemi esistenti; `NormalizedPrimitivePage`; loader, mapping, lookup e artifact resolution; serializer, store e filesystem; selezione o fusione di analisi concorrenti; osservazioni o relazioni multipagina; pattern ricorrenti e continuation; candidate↔candidate; detector, classificazioni, score, confidence, ranking ed evidence; Resolution; manifest, workspace e capture runner; pipeline legacy, IR, Markdown ed EPUB.

## Milestone 12 — inventario document-local delle candidate per structural kind — completata

La milestone ha definito il primo consumer puro di `BoundDocumentAnalysis`, capace di descrivere la distribuzione osservata dei `RegionCandidate.proposed_structural_kind` in tutte e sole le pagine incluse nel binding, senza interpretare i conteggi come frequenza, ricorrenza, importanza o copertura dell'intero PDF.

Tipi ratificati:

```text
CandidateKindPageCount
  page_index: int
  candidate_count: int

CandidateKindOccurrenceMeasurements
  proposed_structural_kind: str
  total_candidate_count: int
  page_counts: tuple[CandidateKindPageCount, ...]

DocumentCandidateKindOccurrenceMeasurements
  document_page_count: int
  included_page_indices: tuple[int, ...]
  candidate_kind_occurrences: tuple[CandidateKindOccurrenceMeasurements, ...]
```

Factory ratificata:

```python
measure_document_candidate_kind_occurrences(
    bound_document_analysis: BoundDocumentAnalysis,
) -> DocumentCandidateKindOccurrenceMeasurements
```

I tipi sono pubblici, puri, `frozen=True`, `slots=True`, non versionati e validati nella costruzione diretta. Tutti gli interi rifiutano `bool`; `page_index >= 0`, `candidate_count > 0`, `total_candidate_count > 0` e `document_page_count >= 0`. `proposed_structural_kind` è una stringa non vuota; `page_counts` è una tuple non vuota di `CandidateKindPageCount`, strettamente ordinata per `page_index`, e il totale coincide con la somma dei conteggi page-local. `included_page_indices` è una tuple di interi non negativi, strettamente crescente e con ogni indice inferiore a `document_page_count`. `candidate_kind_occurrences` è una tuple di elementi del tipo corretto, con kind unici e ordinati lessicograficamente per valore esatto; ogni indice presente in `page_counts` appartiene agli indici inclusi. Pagine incluse senza candidate sono valide, selezioni senza candidate producono aggregazione vuota e kind assenti sono omessi. `included_page_count` non fa parte del contratto perché è interamente derivabile da `len(included_page_indices)`.

La factory canonica `measure_document_candidate_kind_occurrences(...)` consuma esclusivamente `BoundDocumentAnalysis`; deriva `document_page_count` esattamente da `DocumentAnalysis.page_count` e `included_page_indices` esattamente e nello stesso ordine dai riferimenti del binding. Conta tutte e sole le candidate delle analisi legate, ciascuna voce `RegionCandidate` esattamente una volta, raggruppandola per valore esatto di `proposed_structural_kind` e `page_index`. Produce kind in ordine lessicografico e distribuzioni in ordine sorgente, non dipende dall'ordine rappresentativo di `PageAnalysis.candidates`, non muta gli input e non conserva candidate, candidate ID, bbox, primitive ID o provenance. Non descrive automaticamente l'intero PDF e non rappresenta frequenza, prevalenza, ricorrenza, affidabilità, coverage, ranking o classificazione.

La costruzione diretta valida forma minima e coerenza interna e valida il kind soltanto come stringa non vuota. La factory canonica garantisce inoltre che il kind provenga da una `RegionCandidate` già valida; non deve importare il validator privato di `page_analysis_model` né duplicarne la regex.

Per questa milestone, una occurrence è esclusivamente una singola voce `RegionCandidate` osservata in una `PageAnalysis` inclusa, contata sotto il valore esatto del suo `proposed_structural_kind`. Non implica identità cross-page, stesso elemento editoriale, ricorrenza, conferma del kind, indipendenza fra candidate o validità semantica.

Primo micro-step completato: `bbe3ea0` — `Add document candidate kind occurrence measurements`.

```text
document_analysis_candidate_kind_measurements.py
tests/test_document_analysis_candidate_kind_measurements.py
```

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**: nessuna criticità bloccante e nessuna correzione funzionale richiesta. L'obiettivo è soddisfatto dal primo e unico micro-step; l'osservazione non bloccante della revisione non è un debito obbligatorio né una correzione richiesta.

Restano invariati v0.22, schema `PageAnalysis` 1.2, schema `DocumentAnalysis` 1.0, schema `DocumentSourceAttestation` 1.0, pipeline legacy autorevole e shadow mode. Restano fuori scope `LayoutRegion`; candidate ID, bbox e primitive ID nel risultato; candidate↔candidate; adiacenza e gap espliciti; ratio, percentuali, medie e densità; frequenza, prevalenza, kind dominante e ordinamento per conteggio; pattern, ricorrenza e continuation; classificazione e semantica; score, confidence e ranking; coverage e ownership finali; Resolution; persistenza, serializer, store, filesystem, manifest e CLI; modifiche a modelli o schemi esistenti; pipeline legacy, IR, Markdown ed EPUB.

## Milestone 13 — collezione page-local di analisi co-riferite — completata

HEAD di partenza: `91898d6`. Producer diversi generano `PageAnalysis` separate per la stessa pagina, mentre `DocumentAnalysis` e il relativo binding espongono una sola corrente per pagina. Il primo micro-step completato (`c5bc2f2` — `Add co-referenced page analyses`) introduce in `page_analysis_co_reference.py`, con test sintetici in `tests/test_page_analysis_co_reference.py`, il confine page-local osservativo che rende disponibili più analisi co-riferite mantenendole integre e tracciabili.

Contratto implementato:

```python
CoReferencedPageAnalyses(
    source_id: str,
    source_capture_id: str,
    page_id: str,
    source_primitive_schema_version: str,
    analyses: tuple[PageAnalysis, ...],
)

build_co_referenced_page_analyses(
    analyses: tuple[PageAnalysis, ...],
) -> CoReferencedPageAnalyses
```

Il tipo è pubblico, puro, non versionato, `frozen=True`, `slots=True`. I quattro campi espliciti sono stringhe non vuote; `analyses` è una tuple non vuota di `PageAnalysis` e anche una sola analisi è valida. Tutte le analisi dichiarano gli stessi `source_id`, `source_capture_id`, `page_id` e `source_primitive_schema_version`, coincidenti con i campi del contenitore, e lo stesso `PageAnalysis.schema_version` (oggi 1.2).

L'identità canonica interna della corrente è la tupla esatta `(producer_name, producer_version, configuration_id, generation_id)`. La costruzione diretta richiede ordine strettamente crescente per questa chiave; la factory accetta ordine arbitrario e canonicalizza. La comparazione usa stringhe esatte, senza case folding, normalizzazione Unicode, parsing delle versioni, ordine naturale o semantica temporale. Una chiave duplicata è sempre rifiutata, sia per analisi uguali sia per collisione identitaria fra analisi differenti.

Generazioni, versioni, configurazioni e producer differenti possono coesistere: singleton e local-fragment sono correnti concorrenti. Structural kind, candidate ID, region ID, relation ID, primitive ID e bbox possono coincidere fra analisi diverse; gli ID restano scoped alla `PageAnalysis` originaria e le relazioni interne alla propria analisi. La factory conserva l'identità degli oggetti `PageAnalysis`, senza copiarli, fonderli, filtrarli o deduplicare regioni, relazioni o candidate.

Il confine garantisce esclusivamente stesso soggetto page-local dichiarato, stessa capture dichiarata, stesso schema primitive dichiarato e compatibilità rappresentativa dello schema `PageAnalysis`. Non garantisce validazione contro la stessa `NormalizedPrimitivePage`, componibilità, compatibilità semantica, completezza rispetto ai producer, preferenza fra correnti, deduplicazione dei contenuti o Resolution. Non include `page_index`, `NormalizedPrimitivePage`, lookup, conteggi derivati, famiglie di producer o relazioni cross-analysis.

Il primo e unico micro-step soddisfa l'obiettivo della milestone. La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti o non bloccanti e senza correzioni funzionali o documentali richieste. La baseline documentale revisionata è `9f10dab` — `Record co-referenced page analyses baseline`; la baseline funzionale resta `c5bc2f2`.

Restano fuori scope binding document-local delle collezioni; modifiche a `DocumentAnalysis` o `BoundDocumentAnalysis`; `NormalizedPrimitivePage`; validazione cross-model; lookup o riferimenti cross-analysis; candidate↔candidate; merge o selezione di `PageAnalysis`; score, confidence, ranking, coverage e ownership; Resolution; persistenza, serializer, store, filesystem, CLI e diagnostica; nuovi producer, codice o test; pipeline legacy, IR, Markdown ed EPUB. Restano invariati v0.22, schema `PageAnalysis` 1.2, schema `DocumentAnalysis` 1.0, schema `DocumentSourceAttestation` 1.0, pipeline legacy autorevole e shadow mode. Alla chiusura della Milestone 13 non era aperta né autorizzata alcuna milestone successiva.

## Milestone 14 — binding page-local delle analisi co-riferite alla pagina normalizzata — completata

HEAD di partenza: `bd93878`. Il confronto architetturale indipendente ha identificato il problema successivo e giudicato ratificabile il contratto: i consumer primitive-dependent della Milestone 7 usano namespace delle primitive e geometria di `NormalizedPrimitivePage`, mentre la Milestone 13 garantisce soltanto co-riferimento dichiarato. Il primo e unico micro-step è implementato nel commit `ca2d631` — `Add co-referenced page analysis binding`, in `page_analysis_co_reference_binding.py` e `tests/test_page_analysis_co_reference_binding.py`; rende verificabile la composizione fra questi contratti pubblici senza cambiare i consumer, fondere correnti o introdurre decisioni semantiche. Non è una correzione di bug delle diagnostiche esistenti: i percorsi live attuali producono e validano già le analisi contro la pagina ricevuta.

Contratto implementato:

```python
BoundCoReferencedPageAnalyses(
    primitive_page: NormalizedPrimitivePage,
    co_referenced_page_analyses: CoReferencedPageAnalyses,
)

bind_co_referenced_page_analyses(
    primitive_page: NormalizedPrimitivePage,
    *,
    co_referenced_page_analyses: CoReferencedPageAnalyses,
) -> BoundCoReferencedPageAnalyses
```

Il tipo è pubblico, puro, non versionato, `@dataclass(frozen=True, slots=True)`, senza property o campi derivati e composto esattamente dai due campi ratificati. Costruzione diretta e factory validano completamente il binding e offrono le stesse garanzie sostanziali: accettano esclusivamente `NormalizedPrimitivePage` e `CoReferencedPageAnalyses`; ogni `PageAnalysis` della collezione è rivalidata individualmente contro la stessa pagina mediante `validate_page_analysis_against_primitive_page(...)`, riusando il validatore pubblico esistente senza copiarne funzioni private o grammatica. L'incompatibilità di una sola analisi fa fallire il binding.

Pagina e collezione sono conservate per identità; identità e ordine canonico delle analisi restano preservati e la collezione non viene ricostruita, riordinata, filtrata, fusa o deduplicata. La factory non accetta tuple grezze o iterable di `PageAnalysis`, rende esplicita l'operazione e delega la validazione al costruttore. `page_index` resta autorevole esclusivamente in `NormalizedPrimitivePage`: il binding non lo contiene né espone come property, e non duplica alcuna identità già presente negli input. Il co-riferimento dichiarativo della Milestone 13 resta autonomamente utilizzabile senza pagina normalizzata.

Il binding garantisce esclusivamente la validità in memoria al momento della costruzione: ogni analisi della collezione supera il validatore esistente rispetto alla stessa pagina normalizzata fornita. Questo consente di interpretare i `primitive_id` delle diverse correnti nel medesimo namespace page-local effettivo, ma non prova l'origine storica delle analisi e non è un'attestazione persistente. Non introduce equivalenza fra primitive, candidate o regioni; identità editoriale, componibilità semantica o conflitto fra correnti; preferenza, selezione o completezza rispetto ai producer; corrispondenza della bbox con l'estensione delle primitive referenziate; lookup cross-analysis, binding document-local o Resolution.

La copertura dedicata verifica costruzione diretta e factory valide, uguaglianza/immutabilità/slots, singleton e più correnti, tipi runtime errati, mismatch di source/capture/pagina/schema primitive, primitive ID inesistenti in regioni o candidate, bbox incompatibili, rivalidazione di tutte le correnti, conservazione per identità e dell’ordine canonico, determinismo e assenza di mutazione. Verifica la struttura esatta dei campi, l’assenza di `page_index`, nessuna selezione/fusione/filtro/deduplicazione e l’accettazione di contenuti o riferimenti locali coincidenti fra correnti; non usa corruzioni con `object.__setattr__`, duplicazioni integrali dei test dei modelli o controlli su nomi arbitrari.

Il primo e unico micro-step soddisfa l'obiettivo della milestone. La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti o non bloccanti e senza correzioni funzionali o documentali richieste. La baseline documentale revisionata è `32248ac` — `Record co-referenced page analysis binding baseline`; la baseline funzionale resta `ca2d631`.

Restano fuori scope binding document-local delle collezioni; modifiche a `DocumentAnalysis`, `BoundDocumentAnalysis`, `CoReferencedPageAnalyses` o schemi esistenti; estensione o modifica dei consumer della Milestone 7; lookup o riferimenti cross-analysis; candidate↔candidate; equivalenza, conflitto o voto fra candidate; merge, selezione, filtro o deduplicazione; score, confidence, ranking, coverage, ownership, completezza dei producer o Resolution; persistenza, serializer, store, filesystem, manifest, workspace, CLI e diagnostica; nuovi producer o modifiche ai producer; pipeline legacy, IR, Markdown ed EPUB; qualsiasi secondo micro-step. Alla chiusura della Milestone 14 non era aperta né autorizzata alcuna milestone successiva.

## Milestone 15 — riferimento page-scoped a una candidate di una corrente co-riferita — completata

Il primo e unico micro-step (`9a4538f` — `Add co-referenced page candidate reference`) introduce esclusivamente `page_analysis_co_reference_candidate_reference.py` e `tests/test_page_analysis_co_reference_candidate_reference.py`, soddisfacendo l'obiettivo della milestone.

`CoReferencedPageCandidateReference` è un valore pubblico, puro, non versionato, `frozen=True`, `slots=True`, con esattamente `producer_name`, `producer_version`, `configuration_id`, `generation_id` e `candidate_id`. La costruzione diretta valida soltanto che i cinque campi siano stringhe non vuote, senza normalizzazioni e senza verificare l'esistenza della corrente o della candidate.

`build_co_referenced_page_candidate_reference(...)` riceve un `BoundCoReferencedPageAnalyses`, una `PageAnalysis` esplicita e una `RegionCandidate`: verifica per identità Python che l'analisi appartenga al binding e che la candidate appartenga all'analisi indicata, quindi deriva il riferimento dai quattro token della corrente e dal `candidate_id`. `resolve_co_referenced_page_candidate_reference(...)` individua la corrente mediante confronto esatto dei quattro token, cerca il `candidate_id` soltanto nella corrente individuata e restituisce per identità la `RegionCandidate` conservata. Accetta anche riferimenti costruiti direttamente; non usa fallback né la posizione canonica come identità.

L’analisi esplicita è necessaria perché lo stesso oggetto `RegionCandidate` può appartenere a correnti differenti. `ValueError` è sufficiente; i messaggi degli errori sono diagnostici e non costituiscono protocollo pubblico per i consumer.

Il riferimento resta relativo al `BoundCoReferencedPageAnalyses` fornito. È materialmente serializzabile, ma non possiede identità globale, identità di pagina o binding, schema ufficiale di persistenza o protezione dal cross-binding aliasing quando binding differenti presentano gli stessi cinque token. Il limite è intenzionale; non sono introdotti serializer, store o persistenza.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**: non sono emerse criticità bloccanti, correzioni richieste, scope creep o coupling improprio. Le osservazioni su ulteriori mismatch isolati dei token e sulla non-mutazione dedicata del resolver sono soltanto possibili rafforzamenti mutation-oriented e non giustificano modifiche. Non esiste una giustificazione concreta per un secondo micro-step.

Restano fuori scope candidate↔candidate ed enumerazione di coppie; equivalenza, conflitto, merge, selezione o deduplicazione; score, confidence, ranking, coverage e ownership; Resolution; modifiche a modelli o schemi; producer, consumer e diagnostica; filesystem, manifest, workspace, CLI e persistenza; pipeline legacy, IR, Markdown ed EPUB. La chiusura non autorizza nuovi file, codice, test o una milestone successiva.

## Milestone 16 — misure geometriche page-local fra due candidate co-riferite — completata

Apertura documentale: `e20e1b2` — `Open milestone 16 co-referenced page candidate pair measurements`. Il primo e unico micro-step (`89dfb8e` — `Add co-referenced page candidate pair measurements`) introduce `page_analysis_co_reference_candidate_pair_measurements.py` e `tests/test_page_analysis_co_reference_candidate_pair_measurements.py`: 10 test mirati OK, suite completa 1084 test OK e 7 skipped, Ruff verde, BasedPyright 0 errori/0 warning/0 note e `git diff --check` verde.

Contratto implementato:

```python
CoReferencedPageCandidatePairMeasurements
measure_co_referenced_page_candidate_pair(
    bound_co_referenced_page_analyses,
    *,
    first_candidate_reference,
    second_candidate_reference,
)
```

`CoReferencedPageCandidatePairMeasurements` è pubblico, puro, non versionato, `frozen=True`, `slots=True`, con esattamente, in questo ordine: `first_candidate_reference`, `second_candidate_reference`, `first_candidate_bbox`, `second_candidate_bbox`, `horizontal_gap`, `vertical_gap`, `horizontal_overlap`, `vertical_overlap`, `x0_delta`, `y0_delta`, `x1_delta`, `y1_delta`. I due riferimenti sono `CoReferencedPageCandidateReference`, le due bbox sono `BBox` e gli otto campi geometrici sono `float`.

`measure_co_referenced_page_candidate_pair(...)` risolve due riferimenti espliciti nello stesso `BoundCoReferencedPageAnalyses`, li conserva per identità e usa le bbox delle candidate risolte senza clipping, normalizzazione o ricostruzione. Gap è positivo soltanto per intervalli disgiunti; overlap è la lunghezza positiva dell'intersezione; ogni delta è la seconda coordinata meno la prima. Gap e overlap sono simmetrici allo scambio, i delta cambiano segno e first/second è soltanto operativo, senza priorità. La costruzione diretta valida solo la forma e non attesta la derivazione dal binding; non esiste fallback.

Le misure usano l’unità della `PageGeometry` del binding. Il risultato non conserva un campo unit né il binding e resta relativo al `BoundCoReferencedPageAnalyses` usato.

La validazione richiede istanze dei tipi previsti per il binding e i riferimenti, bbox finite e non degeneri, gap e overlap finiti e non negativi e delta finiti. `ValueError` è sufficiente; i messaggi restano diagnostici e non costituiscono protocollo pubblico per i consumer. La costruzione diretta non prova la coerenza matematica o la derivazione dei valori dal binding.

Sono supportati candidate della stessa corrente o di correnti differenti, self-relation, riferimenti identici o logicamente uguali, lo stesso oggetto `RegionCandidate` condiviso fra correnti, collisioni cross-analysis di `candidate_id`, bbox o kind uguali, riferimenti diretti risolvibili, primitive vuote/disgiunte/condivise e cross-binding aliasing intenzionale ereditato dalla Milestone 15. La self-relation produce bbox coincidenti, gap nulli, overlap completi e delta nulli.

`NormalizedPrimitivePage` impone attualmente `top_left_y_down`; il contratto usa comunque i nomi neutrali `x0`, `y0`, `x1`, `y1` e non attribuisce semantica top/bottom a `y0` o `y1`. Non dichiara supporto attuale di binding validi `bottom_left_y_up`.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**: non sono emerse criticità bloccanti, correzioni funzionali richieste, scope creep o coupling improprio. Il primo e unico micro-step soddisfa l'obiettivo e non esiste una giustificazione concreta per un secondo micro-step.

Restano fuori scope equivalenza, matching, conflitto e deduplicazione; selezione, score, confidence e ranking; Resolution; enumerazione o generazione di coppie; area, unione, IoU e ratio; centri, distanze euclidee e dai bordi; booleane geometriche e tolleranze; primitive condivise, relativi ID, conteggi o ratio; diagnostica, consumer e producer; modifiche a modelli o schemi; serializer, store, filesystem e persistenza; relazioni document-local o cross-page; promozione o consolidamento degli helper geometrici privati. La chiusura non apre né nomina una milestone successiva.

## Milestone 17 — flusso diagnostico page-local delle candidate co-riferite — completata

L'apertura documentale è `dd6b073`; la milestone è completata in due micro-step. Pipeline legacy, IR, Markdown ed EPUB restano autorevoli, i nuovi contratti e le diagnostiche restano in shadow mode e non è introdotta Resolution.

L'inventario (`2f80335` — `Add co-referenced page candidate inventory diagnostics`) introduce `dump_co_referenced_page_candidate_inventory(...)`, lo stage `co-referenced-candidate-inventory` e l'opzione ripetibile `--candidate-producer`. Esegue esclusivamente le producer key della lista chiusa `singleton-side-band`, `local-fragment-side-band`, `page-edge-visual` e `page-covering-visual`, costruisce collezione e binding sulla stessa pagina e rende osservabili correnti, candidate e riferimenti effimeri completi. `primitive-extent` resta escluso perché non produce `RegionCandidate`. La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**.

La misura esplicita (`e817084` — `Add co-referenced page candidate pair diagnostics`) introduce `dump_co_referenced_page_candidate_pair_measurements(...)`, lo stage `co-referenced-candidate-pair-measurements` e le opzioni `--first-candidate-reference` e `--second-candidate-reference`. Il parsing JSON richiede esattamente i cinque token del riferimento e rifiuta JSON invalido o non object, campi mancanti o extra, tipi invalidi e chiavi duplicate. Riesegue solo le correnti implicate, verifica dopo la produzione `producer_name`, `producer_version`, `configuration_id` e `generation_id`, costruisce `CoReferencedPageAnalyses` e `BoundCoReferencedPageAnalyses`, risolve mediante l'API della Milestone 15 e misura mediante l'API della Milestone 16. Il dump JSON-compatible read-only non contiene `schema_version`; include `first_candidate_reference` e `second_candidate_reference`, scelta coerente con auditabilità e natura effimera del dump, senza richiedere correzioni. La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**.

Smoke reale: su `/home/an4k4pe/Documenti/ManReader/DB.pdf`, pagina CLI 28 (`page_index` 27), l'inventario ha osservato 12 candidate local-fragment, 1 page-covering visual, 1 page-edge visual e 22 singleton, con riferimenti completi e generation ID coerenti. Due riferimenti effimeri estratti dall'inventario, local-fragment side-band e page-edge visual, hanno prodotto una misura coerente con `diagnostic_kind` `co-referenced-candidate-pair-measurements`, bbox, gap, overlap e delta attesi.

La milestone completa il primo flusso diagnostico page-local in due passaggi: inventario delle candidate co-riferite osservabili e misura geometrica di una coppia esplicita scelta dal chiamante. Il flusso resta diagnostico, read-only, effimero e in shadow mode.

Restano fuori scope nuovi contratti pubblici persistenti o `schema_version` diagnostico; serializer, store, filesystem persistente, manifest o workspace; autodiscovery o registry generale; producer fuori dalla lista chiusa; `primitive-extent` come operando candidate; selezione automatica o "prima candidate" semantica; enumerazione di coppie; matching, equivalenza, conflitto, deduplicazione, merge, scelta, preferenza, ranking, score, confidence o Resolution; nuove metriche geometriche; modifiche a modelli, schemi, producer o consumer; pipeline legacy, IR, Markdown ed EPUB.

## Milestone 18 — misure page-local degli insiemi di primitive referenziate da candidate co-riferite — completata

L'apertura documentale parte da `0328d9f` — `Close milestone 17 co-referenced page candidate diagnostics`; la baseline funzionale resta `e817084` — `Add co-referenced page candidate pair diagnostics`: 79 test mirati OK, 1102 test complessivi OK e 7 skipped, Ruff verde, BasedPyright 0 errori/0 warning/0 note e `git diff --check` verde. Pipeline legacy, IR, Markdown ed EPUB restano autorevoli; i nuovi contratti e le diagnostiche restano in shadow mode e non è introdotta Resolution.

Le Milestone 14–17 consentono di validare più correnti contro la stessa `NormalizedPrimitivePage`, riferire due candidate esplicite, misurarne la geometria e usare il flusso su una pagina reale. I `primitive_ids` delle candidate sono già accessibili tramite il resolver pubblico, ma manca un contratto uniforme che rappresenti la loro relazione come insiemi ordinati. La misura geometrica della Milestone 16 usa esclusivamente le bbox e tratta allo stesso modo primitive vuote, disgiunte o condivise quando la geometria non cambia.

La revisione architetturale indipendente ha dato verdetto **PROBLEMA E PROPOSTA RATIFICABILI**. Il contratto resta separato dalla geometria e descrive esclusivamente appartenenza relativa alla coppia osservata, senza equivalenza, conflitto, preferenza, ownership o decisione.

Contratto ratificato:

```python
CoReferencedPageCandidatePrimitiveSetMeasurements

measure_co_referenced_page_candidate_primitive_sets(
    bound_co_referenced_page_analyses,
    *,
    first_candidate_reference,
    second_candidate_reference,
)
```

Il valore è pubblico, puro, non versionato, `frozen=True`, `slots=True`, con esattamente, in questo ordine:

```text
first_candidate_reference
second_candidate_reference
first_candidate_primitive_ids
second_candidate_primitive_ids
shared_primitive_ids
first_only_primitive_ids
second_only_primitive_ids
```

La factory riceverà esclusivamente un `BoundCoReferencedPageAnalyses`, risolverà entrambi i riferimenti mediante il resolver pubblico della Milestone 15, conserverà per identità i riferimenti ricevuti e le tuple `primitive_ids` delle candidate risolte e produrrà le tre tuple derivate senza riesaminare le primitive della pagina, applicare fallback, ordinamenti lessicografici o normalizzazioni.

Le tuple derivate sono definite come sottosequenze filtrate:

```text
shared = primitive ID della prima candidate presenti anche nella seconda,
         nell'ordine della prima candidate

first_only = primitive ID della prima candidate assenti dalla seconda,
             nell'ordine della prima candidate

second_only = primitive ID della seconda candidate assenti dalla prima,
              nell'ordine della seconda candidate
```

L'ordine è intenzionalmente operativo e asimmetrico: invertendo first e second può cambiare l'ordine di `shared_primitive_ids`, senza esprimere priorità, preferenza o ranking. `first_only` e `second_only` significano soltanto presenza in una tuple e assenza nell'altra all'interno della coppia osservata; non implicano ownership, esclusività rispetto a terze candidate o assegnazione editoriale.

La costruzione diretta validerà tipi, tuple, stringhe non vuote, assenza di duplicati e uguaglianza esatta delle tre tuple derivate con le sottosequenze filtrate degli operandi. Non attesterà che il valore derivi da uno specifico binding. Tuple vuote, candidate disgiunte, insiemi identici con ordine uguale o differente, subset proprio, overlap parziale, self-relation, stessa candidate, stesso oggetto condiviso fra correnti, collisioni di candidate ID fra correnti e riferimenti logicamente uguali ma distinti restano casi validi quando risolvibili nel binding.

Lo scope pianificato, non ancora autorizzato, comprende esclusivamente:

```text
page_analysis_co_reference_candidate_primitive_set_measurements.py
tests/test_page_analysis_co_reference_candidate_primitive_set_measurements.py
```

È previsto un solo micro-step. Restano fuori scope diagnostica e CLI; modifiche ai contratti delle Milestone 14–17; modifiche a `RegionCandidate`, `PageAnalysis`, `DocumentAnalysis` o agli schemi; enumerazione o selezione di candidate o coppie; famiglie primitive; conteggi, booleani derivati, ratio, Jaccard o altre metriche; equivalenza, matching, conflitto, deduplicazione, merge, scelta, preferenza, ranking, score, confidence, ownership, coverage o Resolution; binding document-local delle correnti; persistenza, serializer, store, filesystem, manifest o workspace; modifiche ai producer, alla pipeline legacy, a IR, Markdown o EPUB.

L'apertura non autorizza ancora il micro-step implementativo. Dopo la revisione e il commit del diff documentale sarà preparato separatamente il task manuale per i due soli file previsti.

Il micro-step è stato implementato e verificato nel commit `89228cd` — `Add co-referenced page candidate primitive set measurements`. Il contratto e la factory rispettano esattamente la specifica ratificata sopra. La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti o correzioni richieste. Restano fuori scope tutti i punti già elencati in apertura. Alla chiusura della Milestone 18 non è aperta né autorizzata alcuna milestone successiva.

## Milestone 19 — diagnostica page-local delle relazioni fra insiemi di primitive di candidate co-riferite — completata

M18 ha chiuso il contratto puro `CoReferencedPageCandidatePrimitiveSetMeasurements`
e la factory `measure_co_referenced_page_candidate_primitive_sets(...)`,
escludendo esplicitamente "diagnostica e CLI" dal proprio scope. M17 ha già
stabilito il pattern per esporre in JSON, read-only ed effimero, una misura
di coppia risolta da due riferimenti candidate espliciti
(`dump_co_referenced_page_candidate_pair_measurements`, commit e817084).
Manca l'equivalente per il contratto insiemistico di M18.

Obiettivo unico: aggiungere `dump_co_referenced_page_candidate_primitive_set_measurements(...)`
e lo stage CLI `co-referenced-candidate-primitive-set-measurements`, stesso
pattern di M17, senza toccare contratto o validazione dei riferimenti.

Revisione architetturale indipendente: verdetto RATIFICABILE (Chat B),
condizionato alla fissazione dei nomi letterali (stage, funzione,
diagnostic_kind) e della formulazione della mutua esclusività CLI — entrambe
risolte in apertura, vedi sotto.

Restano fuori scope: nuove misure o campi derivati; persistenza o
schema_version; selezione automatica di candidate o coppie; equivalenza,
conflitto, score, ranking, Resolution; modifiche al resolver di M15 o alla
factory di M18; modifiche ai contratti e producer delle Milestone 13-18;
pipeline legacy, IR, Markdown, EPUB.

Il primo e unico micro-step (`5e2c91d` — `Diagnosis local page`)
introduce `dump_co_referenced_page_candidate_primitive_set_measurements(...)`
in `page_analysis_co_reference_candidate_diagnostics.py` e lo stage CLI
`co-referenced-candidate-primitive-set-measurements` in
`pymupdf_capture_dump.py`, riusando esattamente il pattern già ratificato
in Milestone 17 (`dump_co_referenced_page_candidate_pair_measurements`).

Scope autorizzato, elencato esplicitamente (integrazione retroattiva
rispetto all'apertura):

```text
page_analysis_co_reference_candidate_diagnostics.py
pymupdf_capture_dump.py
tests/test_page_analysis_co_reference_candidate_diagnostics.py
tests/test_pymupdf_capture_dump.py
```

Il contratto e la factory di Milestone 18, il resolver di Milestone 15 e
`_parse_candidate_reference_json` non sono stati modificati.
`_build_required_analyses` e `_reference_to_dict` sono riusati senza
duplicazione né promozione a pubblico. La mutua esclusività CLI delle
opzioni `--first-candidate-reference`/`--second-candidate-reference` è
generalizzata su un insieme chiuso esplicito dei due stage che le
condividono (`co-referenced-candidate-pair-measurements` e
`co-referenced-candidate-primitive-set-measurements`), non allentata
genericamente; docstring di modulo e stringhe di help aggiornati di
conseguenza per restare accurati sui due stage supportati.

Test aggiunti verificano, oltre alla struttura del payload: pass-through
delle proprietà già garantite da Milestone 18 (ordine asimmetrico di
`shared_primitive_ids`, self-relation, collisioni di `candidate_id` fra
correnti); esecuzione delle sole correnti implicate con `wraps` sulla
factory pubblica reale; rifiuto di riferimenti non risolvibili senza
fallback; a livello CLI, accettazione delle opzioni condivise da entrambi
gli stage e rifiuto per uno stage non correlato.

Revisione architetturale indipendente (Chat B): verdetto RATIFICABILE,
condizionato alla fissazione dei nomi letterali (stage, funzione,
`diagnostic_kind`) e della formulazione della mutua esclusività CLI —
entrambe risolte come sopra.

Baseline verificata: Ruff verde su tutti i file coinvolti; BasedPyright
0 errori/0 warning/0 note sui due file sorgente; 87 test mirati OK; suite
completa 1120 test OK e 7 skipped; `git diff --check` verde.

Non esiste una giustificazione concreta per un secondo micro-step. Restano
fuori scope tutti i punti già elencati in apertura.

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
