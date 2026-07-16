# ManReader — Stato progetto

## Versione corrente

**v0.22** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–8 sono completate. Nessuna nuova milestone è ancora aperta.

La pipeline legacy resta autorevole. I nuovi contratti lavorano in shadow mode e non producono ancora decisioni editoriali, IR o output finale.

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

Prima di aprire una milestone successiva è richiesta una nuova decisione architetturale esplicita. Nessun ulteriore codice o comportamento è autorizzato; i debiti dell'audit restano da valutare singolarmente e JSON/PNG reali non vanno committati.

## Ultima baseline funzionale verificata

Commit `308f5db` — `Add validated page analysis reference factory`: 997 test OK, 7 skipped; Ruff verde; BasedPyright: 0 errori, 0 warning, 0 note; `git diff --check` verde.

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

L'acquisizione attestata di `page_count` è rinviata a una futura integrazione con un'autorità documentale concreta. Tale integrazione dovrà ottenere `source_id` e `page_count` dalla medesima sorgente immutabile verificata, includere solo riferimenti appartenenti a quella sorgente e non inferire `page_count` da pagine parziali né da `max(page_index) + 1`. Non è deciso ora se l'autorità sarà PDF snapshot, manifest, capture documentale o un altro componente.

Decisioni identitarie: non esiste `document_id`; `source_id` identifica il PDF immutabile e il soggetto tecnico dell'analisi, mentre `DocumentAnalysis.generation_id` identifica la generazione documentale. Il riferimento pagina riusa `PageAnalysisProvenance`; `page_id` deve coincidere con `provenance.source_page_id` e `page_analysis_schema_version` con `PAGE_ANALYSIS_SCHEMA_VERSION` (oggi `1.2`). Non vengono riferiti path, digest o artifact fisici.

Semantica di `pages`: tuple strettamente ordinata per `page_index`, zero-based, con ogni indice in `0 <= page_index < page_count`, al massimo un riferimento per indice e `page_id` unici. Gap iniziali, interni e finali sono ammessi; `page_count > 0` con `pages == ()` è valido, mentre `page_count == 0` richiede `pages == ()`. I `page_analysis_generation_id` possono essere uguali o differenti fra pagine; i `source_capture_id` devono essere unici fra i riferimenti inclusi.

Le analisi pagina incluse riusano `PageAnalysisProvenance` e devono condividere `source_id`, schema `PageAnalysis`, schema primitive, producer `PageAnalysis`, versione producer e configurazione. Il producer documentale può differire dal producer pagina. Il modello `DocumentAnalysis` non carica né valida oggetti `PageAnalysis` completi; la validazione cross-model avviene esclusivamente nella factory quando il riferimento viene costruito da oggetti reali. `DocumentAnalysis` resta una selezione coerente di analisi pagina, non un catalogo multiproducer, una fusione di analisi concorrenti, una Resolution, una scelta della migliore analisi o un artifact persistito.

Restano fuori scope: builder documentale; filesystem e artifact fisici, artifact resolution, serializzazione e store; CLI e diagnostica; `JobManifest`, capture progress e workspace; relazioni multipagina, pattern ricorrenti, continuation candidate, candidate↔candidate; Resolution e accept/reject/unresolved; body, colonne, tabelle, marginalia, header/footer e callout; detector, score, confidence, ranking, evidence, ownership e coverage; modifiche a `PageAnalysis` o schema `1.3`; IR, Markdown, EPUB, renderer, pipeline legacy e refactor dei debiti delle Milestone 6–7.
