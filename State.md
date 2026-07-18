# ManReader — Stato progetto

## Versione corrente

**v0.22** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–12 sono completate. La Milestone 12 è la più recente completata; nessuna nuova milestone è aperta o autorizzata.

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

La Milestone 12 è completata. Nessuna nuova milestone è aperta o autorizzata e nessun codice, test, diagnostica, persistenza o nuovo consumer è autorizzato. I debiti del capture runner restano separati, quelli dell'audit vanno valutati separatamente e JSON/PNG diagnostici reali non vanno committati.

## Ultima baseline funzionale verificata

Commit `bbe3ea0` — `Add document candidate kind occurrence measurements`: 1043 test OK, 7 skipped; Ruff verde; BasedPyright: 0 errori, 0 warning, 0 note; `git diff --check` verde.

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
