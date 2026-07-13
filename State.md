# ManReader — Stato progetto

## Versione corrente

**v0.20** — **Modalità I: implementazione incrementale**.

La progettazione globale è conclusa. La direzione architetturale A-0.2 e il piano di migrazione sono approvati; ogni task resta piccolo, verificabile, con file ammessi espliciti e senza commit automatici.

## Stato operativo

Le Milestone 1–5 sono completate. La milestone corrente è:

> **Milestone 6 — marginalia e bande laterali**

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

## Milestone 6 — stato corrente

Obiettivo: proporre candidate strutturali di banda laterale senza cambiare output legacy.

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

Contratti disponibili:

- `RegionCandidate` e `PageAnalysis.candidates`, con `PageAnalysis` schema `1.2`, validazione e serializzazione;
- `GeometricTextHypothesis` e `TextHypothesisMeasurements` per selezioni testuali compatibili;
- `build_side_band_candidate_from_text_hypothesis(...)`, che converte primitive ID espliciti in `RegionCandidate(layout.side_band)` senza selezionare o raggruppare;
- `analysis-side-band`, `dump_singleton_side_band_page_analysis(...)` e CLI `--stage analysis-side-band` per il producer singleton;
- `analysis-side-band-local-fragment`, `dump_local_fragment_side_band_page_analysis(...)` e CLI `--stage analysis-side-band-local-fragment` per il producer local-fragment;
- `dump_side_band_local_fragment_diagnostics(...)` e CLI `--stage side-band-local-fragment-diagnostics`, diagnostica read-only dei candidate local-fragment side-band con JSON plain, non `PageAnalysis`;
- `PrimitivePairMeasurements` e `measure_primitive_pair(...)` per la misura pura di una coppia esplicita text/image/drawing;
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

Il percorso side-band text-only ha prodotto diagnostica utile e resta mantenuto: singleton e local-fragment sono baseline diagnostiche confrontabili. I risultati reali indicano però che il riconoscimento affidabile di bande laterali o marginalia non può basarsi soltanto su testo orizzontale vicino ai bordi; immagini, drawing e bbox visuali possono definire confini strutturali quanto il testo.

La nuova linea principale è quindi un substrato geometrico comune, multimodale, puro e non persistito. Il micro-step completato introduce `PrimitivePairMeasurements` e `measure_primitive_pair(...)`: misura una coppia esplicita di primitive text/image/drawing usando bbox originale e bbox visibile dopo clipping, e restituisce gap, overlap, ratio, contenimento, distanze dai bordi pagina e delta fra bordi e centri. Non classifica e non produce `RegionCandidate`.

Lo stage `primitive-pair` espone questa misura soltanto per i due ID forniti esplicitamente: non seleziona coppie, non produce candidate e non cambia `PageAnalysis`. L'opzione `--render-page-image PATH` produce esclusivamente il PNG diagnostico della pagina, senza overlay, crop o annotazioni, e non modifica il JSON dello stage.

`primitive-neighborhood` è solo osservazione diagnostica delle relazioni di una primitiva esplicita rispetto alle altre primitive visibili della pagina: non seleziona automaticamente candidate né introduce decisioni strutturali. Le coverage ratio sono derivate solo da bbox visibili e geometria pagina, non modificano `PrimitivePairMeasurements` né l'ordinamento dei neighbor, e non sono classificazioni, score, confidence o ranking.

Lo stage `side-band-local-fragment-diagnostics` non crea, filtra o modifica candidate e non produce `PageAnalysis`: descrive testo aggregato, ratio pagina, distanze dai bordi, flag formali e diagnostica same-baseline delle candidate local-fragment esistenti. Non introduce score, confidence, ranking, classificazioni semantiche o Resolution. Lo smoke reale su DB p28 e Lan p267 conferma che numeri, punteggiatura, marker/bullet e molti frammenti di riga sono spiegabili descrittivamente senza stringere il producer.

Il producer page-covering produce `RegionCandidate`, non `LayoutRegion`: considera solo `ImageOccurrencePrimitive` e `DrawingPrimitive`, usa bbox visibile clipped alla pagina e soglie conservative `visible_width_ratio >= 0.95` e `visible_height_ratio >= 0.95`. Non classifica come background/decorative, non decide rimozione o export policy e non modifica neighborhood, IR, Markdown, EPUB o output legacy. Lo smoke reale ha individuato candidate page-covering dove presenti e non ne ha prodotto su una pagina sommario priva di visual full-page.

Il producer page-edge produce `RegionCandidate`, non `LayoutRegion`: considera solo `ImageOccurrencePrimitive` e `DrawingPrimitive`, usa bbox visibile clipped alla pagina e soglie conservative page-relative per visuali lunghe, sottili e aderenti ai bordi. Non importa né dipende da page-covering visual, non classifica come `decorative`, non decide rimozione o export policy e non modifica neighborhood, IR, Markdown, EPUB o output legacy.

Decisione architetturale: per ora non introdurre producer per visuali interne. Full-page e edge visual sono sufficienti come primo substrato visuale diagnostico; eventuali visuali interne vanno prima osservate con la diagnostica, non trasformate subito in candidate. Non introdurre ora `layout.visual_separator`, `layout.interior_visual_frame`, `layout.section_background` o structural kind analoghi.

Questa linea non introduce ancora detector generale, selezione automatica generalizzata di candidate, score, confidence, ranking semantico, clustering, grafo geometrico persistito, descrizione geometrica completa della pagina, modifiche a `PageAnalysis`, schema `1.3`, IR, Markdown, EPUB o output legacy.

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

Continuare a usare la diagnostica per interpretare i candidate side-band; non stringere ancora `local-fragment` e mantenere recall alto. Eventuali filtro o Resolution restano una fase separata futura. Non committare JSON o PNG generati.

## Ultima baseline verificata

Commit 9bb3fce: Ruff e BasedPyright verdi; 5 test diagnostica e 52 test dump OK; 927 test complessivi OK, 7 skipped; `git diff --check` verde.

State.md verrà compattato nuovamente solo in un commit documentale separato, se approvato.
