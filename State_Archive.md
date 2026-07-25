# ManReader — Archivio milestone chiuse (Milestone 4–19)

Contenuto spostato qui da `State.md` e `AGENTS.MD` per tenere quei due file al livello
di dettaglio utile alle decisioni correnti. Nessuna informazione è stata riassunta o
riscritta: il testo sotto è identico a quello rimosso dai due file, verificato riga per
riga al momento dello spostamento.

Non rientra nella lettura obbligatoria a inizio sessione (`ManReader_TwoChat_Agent_Workflow.md`
§3, §11): consultarlo solo quando serve il dettaglio storico di una milestone specifica,
non a ogni task. Le milestone 1–3 restano riassunte in `AGENTS.MD` §"Stato delle milestone
precedenti"; le milestone 1–5 restano riassunte in `State.md` §"Milestone completate —
sintesi". Le milestone 20–21 restano in chiaro in entrambi i file: sono le più recenti,
ancora citate per contenuto (non solo per hash di commit) da decisioni in corso.

I contratti, le classi e le regole introdotti in queste milestone restano vigenti e
vincolanti anche da archiviati: l'archiviazione riguarda solo dove vive la narrazione
storica, non lo stato dei contratti stessi, che restano descritti in forma permanente in
`AGENTS.MD` §"Architettura approvata" e §"Invarianti da non violare".

---

# Parte 1 — da `State.md` (Milestone 6–19)

Include, all'inizio della Milestone 6, alcune sezioni di "stato corrente" dell'epoca
(`Vincoli attivi della Milestone 6`, `Fuori scope corrente`, `Prossimo passo operativo`,
`Ultima baseline funzionale verificata`) che a quel tempo riflettevano lo stato attuale del
progetto: non descrivono più lo stato corrente, sono storiche quanto il resto del blocco.

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


---

# Parte 2 — da `AGENTS.MD` (Milestone 4–19)

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

### Milestone 18 — misure page-local degli insiemi di primitive referenziate da candidate co-riferite — completata

Il primo e unico micro-step (`89228cd` — `Add co-referenced page candidate primitive set measurements`) introduce esclusivamente `page_analysis_co_reference_candidate_primitive_set_measurements.py` e `tests/test_page_analysis_co_reference_candidate_primitive_set_measurements.py`, soddisfacendo l'obiettivo della milestone.

`CoReferencedPageCandidatePrimitiveSetMeasurements` è un valore pubblico, puro, non versionato, `frozen=True`, `slots=True`, con esattamente, in questo ordine: `first_candidate_reference`, `second_candidate_reference`, `first_candidate_primitive_ids`, `second_candidate_primitive_ids`, `shared_primitive_ids`, `first_only_primitive_ids`, `second_only_primitive_ids`. I due riferimenti sono `CoReferencedPageCandidateReference`; le cinque tuple sono `tuple[str, ...]` di ID non vuoti e senza duplicati.

`measure_co_referenced_page_candidate_primitive_sets(...)` risolve entrambi i riferimenti nello stesso `BoundCoReferencedPageAnalyses` tramite il resolver della Milestone 15, conserva per identità riferimenti e tuple `primitive_ids` delle candidate risolte e deriva le tre tuple come sottosequenze filtrate, senza riesaminare le primitive della pagina, applicare fallback o normalizzazioni. `shared_primitive_ids` e `first_only_primitive_ids` seguono l'ordine della prima candidate; `second_only_primitive_ids` segue l'ordine della seconda. L'ordine è intenzionalmente operativo e asimmetrico: invertire first e second può cambiare l'ordine di `shared_primitive_ids`, senza esprimere priorità, preferenza o ranking. `only` esprime soltanto presenza relativa nella coppia osservata, non ownership, esclusività editoriale o assenza da terze candidate.

La costruzione diretta valida tipi, tupla, stringhe non vuote, assenza di duplicati e l'uguaglianza esatta delle tre tuple derivate con le sottosequenze filtrate degli operandi; non attesta che il valore derivi da uno specifico binding. Tuple vuote, candidate disgiunte, insiemi identici con ordine uguale o differente, subset proprio, overlap parziale, self-relation, stessa candidate, stesso oggetto condiviso fra correnti, collisioni di candidate ID fra correnti e riferimenti logicamente uguali ma distinti restano casi validi quando risolvibili nel binding.

La revisione indipendente ha dato verdetto **BASELINE ARCHITETTURALE ACCETTABILE**, senza criticità bloccanti, correzioni funzionali richieste, scope creep o coupling improprio. Non esiste una giustificazione concreta per un secondo micro-step.

Restano fuori scope modifiche a contratti o schemi esistenti; diagnostica e CLI; producer; enumerazione o selezione; conteggi e booleani derivati; ratio o coefficienti; famiglie primitive; equivalenza, matching, conflitto, deduplicazione, merge, preferenza, ranking, score, confidence, ownership, coverage o Resolution; binding document-local; persistenza; pipeline legacy, IR, Markdown ed EPUB. La chiusura non apre né nomina una milestone successiva.

### Milestone 19 — diagnostica page-local delle relazioni fra insiemi di primitive di candidate co-riferite — completata

Il primo e unico micro-step (`5e2c91d` — `Diagnosis local page`) introduce `dump_co_referenced_page_candidate_primitive_set_measurements(...)` in `page_analysis_co_reference_candidate_diagnostics.py` e lo stage CLI `co-referenced-candidate-primitive-set-measurements` in `pymupdf_capture_dump.py`, riusando esattamente il pattern già ratificato in Milestone 17. Il contratto e la factory di Milestone 18, il resolver di Milestone 15 e `_parse_candidate_reference_json` restano invariati; `_build_required_analyses` e `_reference_to_dict` sono riusati senza duplicazione. La mutua esclusività CLI delle opzioni `--first-candidate-reference`/`--second-candidate-reference` è generalizzata su un insieme chiuso esplicito dei due stage che le condividono, non allentata genericamente.

La revisione architetturale indipendente (Chat B) ha dato verdetto RATIFICABILE, condizionato alla fissazione dei nomi letterali (stage, funzione, `diagnostic_kind`) e della formulazione della mutua esclusività CLI, entrambe risolte in chiusura. Baseline verificata: Ruff verde, BasedPyright 0 errori/0 warning/0 note sui due file sorgente, 87 test mirati OK, suite completa 1120 test OK e 7 skipped, `git diff --check` verde. Dettagli completi in `State.md`.

Restano fuori scope nuove misure o campi derivati; persistenza o `schema_version`; selezione automatica di candidate o coppie; equivalenza, conflitto, score, ranking, Resolution; modifiche al resolver di Milestone 15 o alla factory di Milestone 18; modifiche ai contratti e producer delle Milestone 13–18; pipeline legacy, IR, Markdown, EPUB. La chiusura non apre né nomina una milestone successiva.

