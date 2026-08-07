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

**Priorità aggiornata dopo Milestone 36 Fase A**: il producer `column_band` (contratto deciso
in Milestone 33, mai costruito, quattro punti bloccanti aperti) non è più un rinvio laterale
ma la precondizione del primo output leggibile della pipeline nuova. Vedi Milestone 36.

Diagnostica pre-milestone per column_band, non ancora una milestone aperta. Il clustering geometrico di righe di Milestone 32 (\_cluster_rows, inviluppo verticale transitivo) fonde più righe reali in una: 13,6%-45,7% delle righe stimate, misurato su DB/Fab/Kul con due metodi indipendenti convergenti al 94,5-96,0% di accordo (scripts/inspect_row_clustering_merge_diagnostics.py). Effetto sulle bande di colonna: gap dissolti o interruzioni a colonna singola nascoste, tre gravità osservate (lieve, moderata, severa), replicato su pagine sia mirate che scelte a caso da pool non condizionato (scripts/compare_strict_vs_loose_column_bands.py).

Alternativa testata: raggruppamento per (block_index, line_index) già assegnato da PyMuPDF in cattura, recuperato da TextPrimitive.source_observation_id (pymupdf_capture.py:124). Test di falsificazione pre-registrato (soglia 2% di gruppi che attraversano un gap noto, su più di un manuale) eseguito esaustivamente su 17 manuali (scripts/test_pymupdf_block_gap_straddle.py): un solo manuale (FWK.pdf, 2,24%) supera la soglia, isolato, e ispezionato — concentrato su 4 pagine di sommario, non prosa a due colonne. Ipotesi non falsificata. Non risolve l'overlap banda/table_candidate (punto bloccante 2 di Milestone 33, ora con due casi concreti: sommari e liste numerate con icona) né due casi isolati con coordinate anomale su Fab.pdf p.2, entrambi non spiegati.

Meccanismo di rilevazione proposto (non implementato, non nel repo): Proposta_ColumnBandProducer_v8.md, Chat A, in revisione con Chat B (Giro 2 architetturale). Script diagnostici committati in 53d5ffc: compare_pymupdf_line_grouping_column_bands.py, dump_pymupdf_line_grouping.py, render_pymupdf_block_overlay.py, test_pymupdf_block_gap_straddle.py. Nessuna modifica a producer, contratti o wiring: diagnostica pura, stesso standard delle altre milestone esplorative.

**Decisione aperta e bloccante, mai messa per iscritto prima d'ora.** `AGENTS.MD` §Migrazione e
shadow mode prescrive che lo shadow mode abbia "criteri di equivalenza **e una milestone di
uscita**". I criteri di equivalenza sono elencati lì; la milestone di uscita **non esiste in
nessun punto di `State.md` o `AGENTS.MD`** — non è stata rinviata, non è mai stata scritta.
Lo stato reale dopo 35 milestone: cinque producer wired, una sola regola di Resolution, nessuna
persistenza del `PageAnalysis` prodotto, nessuno stadio asset, nessuna IR 2, renderer intoccati.
La pipeline nuova non è in grado di produrre una singola pagina di output, e le decisioni
rinviate (precedenza fra regole di Resolution, stadio asset, contratto `column_band`) vengono
discusse in astratto. È lo stesso metodo che le otto falsificazioni registrate sotto Milestone 35
hanno screditato sui manuali, applicato all'architettura.

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

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 21 — wiring del primo producer nel job (esecuzione runtime, senza persistenza) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 22 — cache opportunistica del PageAnalysis — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 23 — wiring del secondo producer nel job (page_covering_visual, apertura selettiva del backend) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 24 — wiring del terzo producer nel job (page_edge_visual, ratifica

side_band/page_edge_visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 25 — diagnostica pura per visuali interne (interior-visual-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 26 — diagnostica di clustering geometrico per DrawingPrimitive (drawing-cluster-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 27 — producer per visuali interne (embedded_visual, no wiring) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 28 — wiring del quarto producer nel job (embedded_visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 29 — diagnostica esplorativa per riquadri di testo (box-like interior visual) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 30 — producer per riquadri di testo (layout.interior_visual_frame, no wiring) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 31 — wiring del quinto producer nel job (interior_visual_frame) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 32 — diagnostica esplorativa per struttura colonne (column-structure-diagnostics) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 33 — contratto per le bande di colonne (decisione architetturale, no build) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

## Milestone 34 — Resolution: design (Modalità P) e prima regola (deduplicazione IVF/EV) — completata

Testo integrale in `State_Archive.md`, stessa intestazione. Sintesi permanente dei contratti
in `AGENTS.MD`.

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
`primitive_id` (`primitive_normalizer.py:141`, `_primitive_id` deriva l'id dall'`observation_id`)
non sono univoci nel manuale, solo nella pagina — qualunque aggregazione cross-pagina che usi
`cluster_id` da solo come chiave rischia di fondere sotto-cluster di pagine diverse. Nota per futuri consumer.

Fuori scope, invariato: nessuna regola di Resolution su `layout.table`×`layout.embedded_visual`/
`layout.interior_visual_frame` (`Proposta_ResolutionDesign_v3.md` §8.2.2) — questa milestone
forniva evidenza, non l'ha trovata a supporto di una regola specifica basata su colore/clustering.
Non decisa: proposta di regola di processo per `AGENTS.MD` (ispezione visiva preventiva prima di
progettare una diagnostica attorno a un'assunzione sul contenuto delle pagine) — rimandata a
discussione separata.

**Milestone chiusa in `2fda096`.**

**Riconsiderazione del tetto d'area (`_DEFAULT_MAX_AREA_RATIO`, 0.28) — scartata su
evidenza.** L'opzione C della proposta v1, scartata al primo giro senza riesame, è
stata riesaminata puntualmente dopo la chiusura, senza scrivere codice, rieseguendo
`scripts/scan_interior_visual_frame_diagnostics.py` (Milestone 29) con
`--min-area-ratio 0.28 --max-area-ratio 0.70` su tutti e sette i manuali. I quattro
casi d'origine sono confermati e riproducibili (Lan p.114 `0.2832`, p.37 `0.2851`,
p.131 `0.2979`, p.119 `0.5890`), ma la separazione che suggerivano non esiste nella
popolazione: 407 righe con testo contenuto cadono fra `0.283` e `0.589` sui sette
manuali (dag 139, fab 91, lan 50, vil 44, db 43, apo 37, kul 3), con distribuzione
continua e senza salti (35/31/42/102/47/56/74/29/24/10 per fascia da `0.28` a `0.70`).
Anche la fetta `0.2832`–`0.2979`, che contiene tre dei quattro casi, contiene almeno
altre quattro pagine Lancer mai citate (p.163 `0.2836`, p.59 `0.2919`, p.295 `0.2932`,
p.329 `0.2975`): i "quattro casi con separazione ampia" erano quattro di almeno sette
nella stessa fascia, dello stesso manuale. Non esiste quindi un valore di
`max_area_ratio` che ammetta i box confermati ed escluda il resto, e nessun valore
sarebbe meno arbitrario di `0.28`. Il volume non è l'argomento: su DB il tetto attuale
produce 966 candidate (2552 righe nel range, 120 pagine) e la fascia alta ne
aggiungerebbe 51, +5%. L'argomento è l'assenza di separazione. `dispersion_ratio` non
separa neppure qui (p.119, caso da escludere, `1.3473`, in mezzo a p.160 `1.2991`,
p.164 `1.2268`, p.168 `1.1243`), coerentemente con la conclusione già registrata sopra.
Osservazione non promossa a criterio, n=4: `contained_text_area_ratio` va nella
direzione opposta all'intuizione (i due box `0.7637`/`0.7009`, il terzo `0.4528`, la
tabella zebra da escludere la più bassa, `0.2967`; mediana della popolazione `0.1638`).
Asimmetria strutturale da tenere presente: Apo, Fab e Vil non hanno alcuna riga
vettoriale nella fascia (0 su 37/114/57), Lan 39, Dag 30, DB 7, Kul 2 — un eventuale
tetto futuro non potrebbe essere unico per i due rami. Nota di processo: la premessa
era vera sui quattro casi ispezionati e falsa sulla popolazione, stesso schema di
errore della premessa d'origine di questa milestone nella sua variante statistica;
è emersa al primo giro di Modalità P, prima di qualunque riga di codice, per il costo
di sette esecuzioni dello script già committato.

Massa irrisolta di embedded_visual: ripetizione geometrica e identità di contenuto — entrambe scartate su evidenza. Campione casuale riproducibile di 280 pagine (40 per manuale, 7 manuali, seed 20260802, scripts/sample_resolution_prototype_pages.py): 3917 candidate embedded_visual irrisolte, di cui 2671 (68,2%) in gruppi di almeno 3 bbox identiche, IC95 bootstrap per pagina 60,6–73,7%. L'aggregato si dissolve alla disaggregazione: Kul 93,6% (1570 irrisolte), Fab 72,1% (1353), DB 27,8% (756), Vil 23,1% (52), Lan 8,9% (45), Dag e Apo 0,0% (90 e 51). Kul ha 11 sole forme distinte e la dominante 284.9×5.2 compare 27 volte per pagina su 26 pagine su 40: da sola Kul vale il 55% della massa "ripetuta" del campione. L'ispezione visiva (regola 14) mostra che la firma unifica cose opposte: su Kul è il fondo a righe della pagina, su Fab sono le icone degli oggetti nelle tabelle di equipaggiamento — contenuto da preservare, non arredamento — e sulla stessa pagina di Fab convivono icone e filetti di riga con firma di ripetizione identica. ImageOccurrencePrimitive.content_digest è stato testato come discriminante alternativo (scripts/inspect_image_content_digest_recurrence.py) e non separa: Kul 284.9×5.2 dà 1 digest su 27 occorrenze e 108 occorrenze su 4/4 pagine, le icone Fab 20.9×20.9 danno 12 digest su 12 occorrenze come atteso, ma i filetti Fab 56.0×1.0 danno 21 digest su 27 occorrenze e 231.0×1.0 ne danno 9 su 9 — arredamento che non condivide identità. Le fasce di tabella di DB sono raster e danno 2 digest su 4 occorrenze a p.33, 4 su 4 a p.53. Nessuna milestone si apre. Resta valido, e rafforzato da una seconda conferma indipendente dopo Milestone 23, il solo uso stretto già annotato in §Stato operativo: un consumer document-level per content_digest limitato all'arte raster ripetuta identica. La lacuna di identità su DrawingPrimitive non è stata esercitata: tutti i casi osservati erano raster.

Copertura fra producer delle candidate embedded_visual irrisolte — primo esito parzialmente positivo, non ratificato. Fino a qui il confronto fra producer era stato osservato solo fra embedded_visual e interior_visual_frame: il prototipo di Milestone 34 costruisce due producer su cinque, quindi table_candidate, page_covering_visual e page_edge_visual non erano mai entrati in una CoReferencedPageAnalyses reale. scripts/measure_cross_producer_candidate_coverage.py costruisce tutti e cinque i producer wired sulla stessa NormalizedPrimitivePage, li lega con il sottosistema Milestone 13-19, applica resolve_page_candidates e misura, per ogni candidate embedded_visual rimasta unresolved, la frazione della propria area coperta dalla candidate più sovrapposta di ciascun altro producer. Eseguito sulle 120 pagine di Kul/Fab/DB già estratte nel campione casuale da 280 (seed 20260802), senza riestrazione. Candidate prodotte: embedded_visual 4110, interior_visual_frame 431, page_covering_visual 122, table_candidate 71, page_edge_visual 61; 3679 embedded_visual restano irrisolte. Il risultato grezzo — 96,6% coperte a ≥0,9 — è degenere: page_covering_visual produce circa una candidate per pagina (41 su 40 pagine Kul, 39 su 40 Fab, 42 su 40 DB, presente su 116 pagine su 120) e per costruzione delle proprie soglie (visible_width_ratio >= 0.95 e visible_height_ratio >= 0.95) contiene ogni altra candidate della pagina, quindi la sua copertura non porta informazione. Correzione post-hoc, dichiarata come tale e non pre-registrata: escluso page_covering_visual dal calcolo, la copertura a ≥0,9 diventa Kul 0,0% (IC95 bootstrap per pagina 0,0–0,0%), Fab 68,8% (48,5–80,5%), DB 34,0% (27,1–40,3%); considerando il solo table_candidate, Fab 53,3% (34,3–63,2%) e DB 18,0% (12,4–23,0%). La predizione registrata prima dell'esecuzione era confermata su Kul (nessun altro producer vede il fondo rigato; table_candidate non scatta su nessuna delle 40 pagine) e su Fab, fallita su DB, dove le fasce di tabella erano attese coperte da table_candidate a ≥0,9 e lo sono per meno di un quinto. Osservazione non prevista e rilevante: su Fab il 40,6% delle irrisolte è coperto a ≥0,9 da interior_visual_frame — sono candidate senza gemello IVF a insieme di primitive identico, quindi fuori dalla regola unica di Milestone 34, ma geometricamente contenute in un riquadro IVF. È un secondo tipo di relazione fra candidate, contenimento senza identità, misurabile con i contratti Milestone 13-19 già scritti e oggi non toccato da alcuna regola. Il calcolo di sovrapposizione in linea è stato riverificato su Fab p.284 contro measure_co_referenced_page_candidate_overlap_ratio (Milestone 34): 300 coppie, 0 discordanze. Nessuna milestone si apre. Conclusione operativa: il confronto fra producer è informativo, ma non è il primo passo — finché page_covering_visual promuove a candidate lo sfondo del 97% delle pagine, qualunque misura di copertura va corretta a mano per non essere dominata da lui. La precondizione è distinguere sfondo ricorrente da illustrazione unica, cioè il consumer document-level per content_digest già annotato in §Stato operativo, che riceve qui la sua terza gamba empirica dopo Milestone 23 e dopo il caso Kul (1 digest, 108 occorrenze su 4 pagine su 4). Solo dopo ha senso rimisurare la copertura fra producer, e in quel caso il contenimento interior_visual_frame ⊃ embedded_visual è la relazione da guardare per prima.

Appunto per una futura passata di raffinamento (non aperta, non numerata):
misura esplorativa sul rumore raster, 16 manuali reali, nessun codice di produzione
toccato. La pipeline nuova conta **collocazioni** (`ImageOccurrencePrimitive` è per
occorrenza) mentre la pipeline legacy conta **immagini** (`get_images` per xref più
`rects[0]`, più deduplica MD5 document-scoped in `_extract_images`): il divario è di
uno o due ordini di grandezza. Raggruppando per `content_digest` — campo già presente
e popolato via `get_image_info(hashes=True)`, zero mancanti su 27.437 occorrenze
misurate — Kul passa da 8774 occorrenze a 107 asset distinti (collasso 82×), DB da
3534 a 991 (3,6×), Fab da 15129 a 4411 (3,4×). Il collasso è quindi forte su un
manuale su tre e non è il meccanismo dominante.

Il filtro raster del legacy (`config.min_image_width/height = 80` px, unico scarto
applicato a `_extract_images`) è **inutilizzabile** sotto l'obiettivo "ogni immagine
diventa una nota": su Fab elimina 258 digest con dimensione intrinseca 16×16 px che sono le icone degli
oggetti nelle tabelle equipaggiamento, cioè contenuto. L'asse dimensionale resta però
reale: `intrinsic_width`/`intrinsic_height` sono già sul contratto di
`ImageOccurrencePrimitive` e nessun producer li guarda.

Ipotesi verificata e falsificata, poi riformulata. La prima formulazione — filetti e
immagini si distinguono per forma, con lato minore in PIXEL ≤16 e aspetto ≥4 — è stata
falsificata secondo un criterio registrato prima dell'esecuzione, l'esistenza di una valle
di densità stabile fra editori (`scripts/inspect_aspect_density_valley.py`): quattro
manuali su sei analizzabili hanno una valle, a 1,83 / 3,67 / 29,34 / 83,0, dispersione 45×
contro una soglia di caduta di 4×. Sull'asse del lato minore, su tutti gli asset senza
prefiltro, dieci manuali su sedici hanno una valle, da 1,5 a 558 px, dispersione 362×. Le
valli non sono nemmeno lo stesso fenomeno: due sono bin vuoti in dati radi, una cade fra
due picchi entrambi quadrati. Difetto di impostazione trovato dall'utente e non da Chat A:
la dimensione in pixel intrinseci è una proprietà di come l'editore ha esportato il file,
non dell'oggetto sulla pagina.

Riformulazione: lato minore in PUNTI diviso il corpo del testo, incrociato con il rapporto
d'aspetto (`scripts/inspect_image_typographic_shape.py`, 16 manuali). Il corpo è stimato
dalla moda delle `font_size` della pagina stessa, quindi il criterio resta funzione pura di
una singola `NormalizedPrimitivePage`: nessun passaggio documentale, nessuna interferenza
con la cache di Milestone 22, con l'ordine di esecuzione o con la persistenza rinviata da
Milestone 21. La prima versione dello script stimava però il corpo accumulando le
`font_size` su tutto il documento, cioè normalizzava sul corpo del MANUALE mentre
l'argomento che sosteneva è pagina-locale — difetto trovato dalla revisione Chat B, non da
Chat A, e dello stesso genere di quello che aveva ucciso l'asse in pixel: un riferimento
sbagliato scambiato per quello giusto, annidato stavolta dentro l'argomento con cui quel
tipo di errore veniva respinto. Corretto e rimisurato. **Effetto pratico piccolo**: la
dispersione del corpo dentro un manuale è al massimo 1,12× fra p10 e p90, e su sette
manuali su sedici è esattamente 1,00, quindi le due normalizzazioni danno quasi lo stesso
risultato. Sulla mappa page-local le due cose che il filtro legacy a 80 px confondeva
restano in regioni diverse: le icone degli oggetti di Fab sono intorno a 2 corpi con
aspetto 1,0, i suoi filetti ≤0,2 corpi con aspetto ≥8 (2126 asset, 6712 occorrenze); il
fondo rigato di Kul, che in punti assoluti sembrava anomalo a 5,2 pt, normalizzato sta
nella fascia banda con aspetto 52 e 8210 occorrenze.

Due cose emerse solo dalla versione corretta. La prima: i cali osservati rispetto alla
mappa documentale non sono riclassificazioni ma **esclusioni**. Le immagini su pagine dove
il corpo non è stimabile (meno di 20 primitive testuali) prima ricevevano comunque una
regione usando il corpo del manuale, adesso non ne ricevono nessuna — e sono una quota non
trascurabile: Lan 69 occorrenze su 157 (44%), DIE 96 su 377 (25%), Vil 104 su 663 (16%),
BoB 113 su 750 (15%), DB 264 su 3534 (7%), Fab 35 su 15129 (0,2%). Le pagine senza testo di
corpo sono le tavole a piena pagina, cioè proprio dove stanno le illustrazioni grandi: non
è che il corpo di pagina sia una stima peggiore, è che su una classe intera di pagine non
esiste. Limite dell'impostazione page-local non previsto da nessuno dei tre. La seconda:
l'unico spostamento non spiegato da esclusioni è su Fab, circa 280 asset passati da
`filetto` a `banda`, tutti sul confine `0,2 corpi` scelto a mano; Fab ha corpo che oscilla
fra 9 e 10 punti e le cose vicine a un confine arbitrario migrano appena il denominatore si
muove. Conferma diretta del rilievo Chat B sui confini: la struttura grossa della mappa è
robusta, i suoi bordi non sono difendibili come numeri, solo come descrizione di zone.

A cosa serve, misurato invece che supposto
(`scripts/inspect_page_local_lines_vs_tables.py`, 40 pagine per manuale, seed 20260803).
Prima misura: la quota di linee e bande che cade per almeno metà della propria area dentro
un `table_candidate` della stessa pagina — Fab 738/982 (75%),
DrW 92/151 (61%), DrM 31/53 (58%), DB 12/16 (75%).
Letta da sola sembrava dire che le linee confermano le tabelle. **Non lo dice.**
Il controllo di permutazione (ogni linea ricollocata a caso sulla stessa
pagina, venti ripetizioni, stesso calcolo) mostra che l'atteso per caso è alto: Fab 50%,
DrM 49%, DB 46%, DrW 33%. L'arricchimento reale è quindi Fab 1,5×, DrW 2,0×, DrM 1,4×,
e nessuno raggiunge il 3× registrato come soglia prima dell'esecuzione. Quattro manuali
sono addirittura sotto 1, e Wil sta a 0,2× — le sue linee cadono dentro le tabelle MENO
del caso, essendo bordi e cornici sistematicamente dove le tabelle non sono. Il censimento
completo di DB (126 pagine, nessun campionamento) corregge il suo dato da 75% con 2,7× su
16 linee a 60% con 1,3× su 120: l'aneddoto era rumore. **L'affermazione che le linee
corroborino le tabelle è ritirata**; resta un arricchimento debole ma reale, dell'ordine
di 1,5× su 982 linee, che è troppo poco per fondarci una regola di Resolution.

Avvertenza generale, che è la cosa più utile emersa da questa misura e vale oltre questo
giro: l'atteso per caso è così alto perché i `table_candidate` sono enormi, coprendo da un
terzo a due terzi dell'area delle pagine dove compaiono. **Qualunque misura di
contenimento geometrico contro `table_candidate` è quindi quasi priva di informazione se
non accompagnata dal tasso di base.** Vale anche per `§8.2.2`, la relazione
`layout.table` × IVF/EV lasciata aperta da Milestone 34, che è esattamente una misura di
contenimento contro quelle stesse candidate. Il repository conteneva già l'avvertimento,
nella docstring di `scan_table_candidate_visual_area_coverage.py` ("a tiny box fully inside
a huge table candidate gives overlap_ratio near 1.0"), e Chat A ci è cascata lo stesso: il
rilievo è arrivato dalla revisione Chat B.

Quello che questa misura NON tocca: la capacità del criterio di forma di identificare le
linee, che poggia sulla mappa tipografica su 16 manuali e sulle 48 celle di provino a
campionamento casuale (DrW e Kul, nessun falso positivo osservato). Il tasso di base
riguarda l'uso delle linee a valle, non il loro riconoscimento. Controllo negativo su Kul
invariato: 1252 linee, zero `table_candidate` su 40 pagine — il fondo rigato non è
struttura di tabella, e per quel manuale il controllo di permutazione non ha nulla contro
cui girare.

Verifica visiva con provino a contatto e campionamento casuale su DrW e Kul, 48 celle:
tutto arredamento, nessun contenuto. Filetti sotto i titoli, righe di guida dell'indice,
campi da compilare della scheda, barre di margine, fondo rigato.
`scripts/render_image_asset_contact_sheet.py` è stato corretto: ordinava per frequenza e
mostrava quindi solo arredamento per costruzione, difetto trovato dalla revisione Chat B e
non da Chat A. L'ispezione precedente su Fab, Vil e Wil era limitata ai 24 digest più
frequenti per manuale e non misurava la precisione della regione ma solo quella dei suoi
elementi più frequenti; una previsione di Chat A su Wil era risultata sbagliata e corretta
dal provino (l'asset 38×16 px non erano i numeri dei passaggi ma il bordo della cornice).

Limiti dichiarati. Dal 2% al 22% delle pagine non ha un corpo stimabile (meno di 20
primitive testuali) e lì il criterio non si applica: su DB sono 124 immagini, circa il 12%
delle sue occorrenze. La corroborazione al 58-75% include gli indici, che pdfplumber con
la strategia `text_lines` legge legittimamente come tabelle: quanto pesino non è stato
separato. Le regioni "bollino" e "sottile" restano miste e la forma lì non decide: gli
angoli di cornice di Wil hanno la stessa firma di un'icona di contenuto. Il rilevatore di
valli è stato cambiato dopo il fallimento del primo, quindi quel passaggio è post-hoc e
vale una tacca meno di uno pre-registrato. Le pagine con `rotation != 0` o
`mediabox != cropbox` erano escluse senza contatore dalle prime due diagnostiche: la
misura successiva le ha contate e sono **zero** su tutti e sedici i manuali. Anomalia
annotata e non indagata: su SV il producer `table_candidate` ha scartato due candidate con
bbox fuori dai limiti di pagina (`y0 = -7,01` su pagina alta 652).

La revisione Chat B aveva dato verdetto **non ratificare, non aprire milestone**, con tre
misure richieste: la prima è stata eseguita e ha falsificato la formulazione in pixel; le
altre due (provino stratificato, aspetto intrinseco contro aspetto di collocazione)
decadono con essa e restano da rifare se la formulazione tipografica verrà proposta.
Vincolo architetturale emerso dalla stessa revisione e tuttora valido: una regola di forma
in Resolution dovrebbe girare **dopo** le regole relazionali, non prima, perché i bordi
che classificherebbe come arredamento sono anche l'evidenza geometrica su cui devono
lavorare `§8.2.2` e il contenimento `interior_visual_frame ⊃ embedded_visual`. Nessuna
milestone è aperta, nessuna soglia è ratificata, nessun producer o contratto è stato
modificato.

Script: `scripts/inspect_document_image_asset_inventory.py`,
`scripts/inspect_image_shape_axis.py`, `scripts/inspect_aspect_density_valley.py`,
`scripts/inspect_image_typographic_shape.py`,
`scripts/inspect_page_local_lines_vs_tables.py`,
`scripts/render_image_asset_contact_sheet.py`.

Falsi negativi, misurati (`scripts/render_image_asset_contact_sheet.py`, ora capace di
filtrare sullo spessore relativo e non solo sui pixel, campionamento casuale con seed).
Il criterio sbaglia **solo per difetto e solo su arredamento**: in 72 celle ispezionate su
tre manuali non è comparso un solo contenuto catturato, mentre molto arredamento sfugge.
La causa è la richiesta di aspetto ≥8, che lascia passare le cose sottili ma corte.

Su Fab la regione "bollino" (38 asset) contiene due popolazioni distinte: le icone dei tipi
di danno e degli oggetti, `13×12` fino a `16×16` px, 1,06–1,44 corpi, 21-38 occorrenze
ciascuna — contenuto, correttamente risparmiato; e granelli degeneri, `1×1` px a 0,11 corpi
con 60 occorrenze, `4×2` px a 0,22 con 40 — arredamento, non catturato. La regione
"sottile" (351 asset) è quasi tutta a 0,22 corpi: schegge di bordo di cella con aspetto fra
2 e 8, arredamento, non catturato. Un caso isolato e notevole: `83×12` px, 1,20 corpi, è la
frase "I confini sono un inganno della mente" composta **come immagine**, cioè testo che
diventa asset. Su Wil il complemento (108 asset) è interamente arredamento: angoli e
segmenti delle cornici, 0,33–1,26 corpi.

La correzione ovvia — rilassare l'aspetto tenendo un limite di spessore — funziona dentro
Fab, dove l'arredamento sfuggito sta a 0,11–0,35 corpi e il contenuto a 1,06–1,44, due
popolazioni nettamente separate. **Non funziona fra manuali**: su Wil l'arredamento sfuggito
sta a 0,33–1,26 corpi, cioè esattamente dove su Fab sta il contenuto. Un limite tarato su
Fab cancellerebbe le icone dei tipi di danno se applicato a Wil. Settima occorrenza dello
stesso schema: separa dentro un manuale, non fra manuali.

Bilancio del criterio di forma, completo su entrambi i lati: precisione alta (72 celle
casuali su tre manuali, nessun contenuto catturato); copertura parziale e non quantificata
globalmente (su Fab sfuggono almeno 389 asset fra bollino e sottile, su Wil 108, quasi tutti
arredamento); modo di fallire conservativo, cioè quello giusto, perché lascia rumore invece
di cancellare contenuto; non estendibile con una soglia unica. Le tre misure chieste dalla
revisione Chat B sono state eseguite tutte: la prima ha falsificato l'asse in pixel, la
seconda ha ritirato la corroborazione delle tabelle, la terza è questa.

Contenimento `interior_visual_frame ⊃ embedded_visual` — ritirato su criterio pre-registrato.
La sola relazione che `State.md` indicava come "da guardare per prima" è stata sottoposta al
controllo di permutazione che le due misure precedenti non avevano, con criterio di
falsificazione registrato per iscritto prima dell'esecuzione (`Prereg_ContenimentoIVF_EV_v1.md`,
non nel repo, stessa prassi di Milestone 33/34/35): ritiro se l'arricchimento è < 3× **su Fab**,
cioè sul manuale da cui l'affermazione è nata. Misura su tutti e sette i manuali del campione
casuale già registrato (280 pagine, 40 per manuale, seed 20260802), con
`scripts/measure_cross_producer_candidate_coverage.py` esteso di un controllo di permutazione
opt-in (`--permutations`, default 0: l'output preesistente resta identico byte per byte,
verificato). Due nulli: A ricolloca ogni candidate irrisolta a caso sulla pagina preservando
larghezza e altezza, B preserva `y0`/`y1` e randomizza solo `x`; le candidate degli altri
producer restano immobili e `resolve_page_candidates` non viene mai rieseguito sulla geometria
permutata. Zero candidate non ricollocabili su sette manuali.

Fab sta a **1,94×** (nullo A) e **1,24×** (nullo B): sotto la barra su entrambi, quindi la
ritrattazione non dipende da quale nullo si creda. Gli altri: DB 2,63×/1,43× (756 irrisolte),
Dag 3,21×/1,65× (90), Vil 7,06×/1,14× (52), Apo e Kul osservato 0,0%, Lan escluso per n<50 e
comunque a 0,0% osservato contro 13,0% atteso per caso. I conteggi di irrisolte per manuale
coincidono esattamente con quelli già registrati sopra, quindi la misura originale è
riproducibile: è la sua interpretazione a cadere, non il suo dato.

Due cose che il criterio non chiedeva e che pesano più del suo esito. La prima: **il 40,6% di
Fab non era una statistica di popolazione ma due pagine.** p.317 (248 candidate coperte) e p.354
(247) valgono 495 delle 549 totali, il 90%; solo 13 pagine su 40 hanno una singola candidate
coperta; IC95 bootstrap per pagina 5,5%–62,7%. Vil è peggio: il suo 11,5% e il suo 7,06% vengono
da una pagina sola (p.123, 6 su 6). Terza occorrenza dello stesso errore dopo il campione
ordinato per frequenza e dopo il 75% di DB sgonfiato a 60% dal censimento completo. La seconda:
**la direzione della debolezza del nullo, dichiarata ignota in pre-registrazione, ora è
misurata.** Il nullo B dà sistematicamente un tasso permutato più alto del nullo A su tutti i
manuali: IVF ed EV si concentrano nelle stesse fasce verticali, quindi il nullo uniforme
sottostima il caso e ogni arricchimento calcolato su di esso è gonfiato. Il numero difendibile è
quello del nullo B, e lì il massimo su sette manuali è 1,65×.

Segnale opposto, coerente con Wil a 0,2× nella misura linee/tabelle: su Lan le irrisolte reali
cadono dentro i riquadri IVF allo 0,0% contro un atteso per caso del 13,0%. L'arredamento sta
sistematicamente dove le cornici non sono.

Nota di metodo, la più riutilizzabile di questo giro: il criterio pre-registrato vincolava
**Fab**, non "due manuali qualsiasi". Una lettura post-hoc degli stessi identici dati avrebbe
dichiarato l'esito positivo, su Dag (3,21×) e Vil (7,06×), entrambi sopra 3× e sopra le soglie
di n e di tasso osservato. Pre-registrare non basta: il criterio deve vincolare il caso da cui
l'affermazione è nata, altrimenti si sposta la domanda invece di rispondere.

Nessuna milestone si apre, nessuna soglia è ratificata, nessun producer o contratto è
modificato. Ottava caduta consecutiva, e in una variante più stretta delle precedenti: non
separa fra manuali, e su Fab non separa nemmeno fra pagine — separa due pagine dalle altre
trentotto.

## Milestone 36 — fetta verticale end-to-end su una pagina — Fase A completata, Fase B non eseguita

Design in `Proposta_Milestone36_FettaVerticale_v1..v4.md` (non nel repo, stessa prassi di
Milestone 33/34/35). Due giri di revisione Chat B **disgiunti** — metodologico prima,
architetturale poi, con letture separate: formato nuovo, adottato dopo che un giro unico è
costato ~54.000 token in ingresso e che i contributi decisivi di Chat B, storicamente, sono
quasi tutti metodologici e non richiedono il repository.

Obiettivo: il percorso più sottile da un PDF a un frammento markdown con note che
referenziano immagini estratte su disco, attraverso i contratti già esistenti. Prima volta in
35 milestone che la pipeline nuova produce un output leggibile da un essere umano.

`scripts/prototype_vertical_slice_page.py` compone capture → normalize → i cinque producer →
co-reference (Milestone 13-19) → `resolve_page_candidates`, ed emette `page.md`,
`assets_index.csv`, `review.md` e i file asset. Nessun producer nuovo, nessun contratto,
nessun wiring nel job; la pipeline legacy non è importata né invocata.

Due invarianti **auto-verificati a ogni esecuzione**, con uscita `4` su fallimento:
conservazione del contenuto testuale come multiset di caratteri non-spazio (cieco all'ordine
di proposito, perché `page_analysis_model.py` nega esplicitamente il reading order alle
righe 189-190, 192-193, 195-196), e integrità dei riferimenti. Il criterio di uscita è
eseguibile dall'artefatto, non valutato a occhio da chi legge l'output.

Esecuzione reale su DB.pdf p.99: 30 occorrenze, 25 asset distinti, 6 note nel corpo, 24 voci
in revisione, 1230 caratteri non-spazio conservati, rapporto note/parole 0,027.

**Risultato principale, che riordina le priorità: il reading order richiede il producer
`column_band`.** Il testo emesso con ordinamento geometrico puro (`y0`, poi `x0`) concatena
riga per riga le due colonne del corpo, ed è illeggibile. La regola editoriale reale —
colonna sinistra fino a un'interruzione, poi destra, poi di nuovo sinistra riprendendo sotto
l'interruzione, con l'incolonnamento che cambia alle interruzioni — presuppone esattamente la
segmentazione in bande a conteggio di colonne stabile costruita da Milestone 32 e il
contratto deciso da Milestone 33 (`proposed_structural_kind="layout.column_band"` più misura
satellite). Quel producer non esiste, e Milestone 33 ha lasciato quattro punti bloccanti. La
proposta di Milestone 36 classificava `column_band` come "fuori dalla catena": l'artefatto
reale dice che è la prima cosa di cui la catena ha bisogno. È il motivo per cui la fetta è
stata costruita invece di continuare a decidere sulla carta, e ha risposto al primo run.

**JPEG 2000: la transcodifica a PNG o WebP è indispensabile.** `extract_image(xref)`
restituisce lo stream come è memorizzato nel PDF, senza transcodifica: DB.pdf archivia le sue
immagini in JPEG 2000, quindi gli asset estratti per xref escono in `.jpx`. Le immagini non
sono destinate alla lettura sul dispositivo — vanno in una cartella a parte e sono solo
referenziate dal markdown — ma il `.jpx` non è apribile dai visualizzatori di immagini
correnti su Windows e Linux, quindi la cartella risulterebbe inutilizzabile per lo scopo per
cui esiste. Requisito registrato, non opzionale: gli asset raster vanno transcodificati in
PNG o WebP. Non deciso qui quale dei due, né dove avvenga la conversione.

**Correzione a un resoconto di implementazione**, registrata perché il numero era già
circolato: gli asset di DB p.99 sono **13 estratti via `xref` e 12 via `rasterized_clip`**,
non 12 e 13 come riportato in prima battuta. Nessuna contraddizione con le 13 occorrenze a
`xref == 0`: occorrenze e identità sono entità distinte, le 17 occorrenze risolvibili
collassano in 13 asset e le 13 inline in 12.

Il fallback `rasterized_clip` è una proprietà dei PDF e non un difetto del nostro lookup:
verificato che `get_images(full=True)` restituisce 17 voci su 13 xref distinti, cioè non
trova un solo xref in più di quelli che `get_image_info(hashes=True, xrefs=True)` già
risolve — le restanti sono immagini inline, che non esistono come risorsa. Confronto poi
chiuso anche sugli insiemi: `solo in get_images` e `solo in get_image_info` entrambi vuoti.
Le immagini inline non estraibili sono tutte piccole (≤580×176 px intrinseci, per lo più
304×80 e 336×52: etichette e bandelle), mentre le illustrazioni grandi
(1244×1616, 845×1155, 509×809) passano correttamente per xref.
La rasterizzazione a 72 dpi del ritaglio degrada quindi elementi minori, non l'arte.
Quando `extraction_method = rasterized_clip`, i byte su disco **non**
corrispondono al `digest` sotto cui sono indicizzati: la sostituzione è registrata in
`assets_index.csv`, mai silenziosa.

**Buco nella regola di processo, non violazione.** `AGENTS.MD` §Aggiornamento documenti
impone di committare lo script che produce un numero citato, e lo script c'è. Ma
`scripts/inspect_document_image_asset_inventory.py` accetta `--pdf` come **singolo file per
invocazione** e anche l'intervallo di pagine è runtime (`--first-page`, `--last-page`), con
`--json-output` opzionale e non committato: lo scope della misura «zero mancanti su 27.437
occorrenze» su 16 manuali è il risultato di sedici o più invocazioni di cui non resta
traccia. La regola copre l'**esistenza** dello script, non la **tracciabilità delle
invocazioni**. Nessuna decisione presa qui su come chiuderlo.

Fase B (esecuzione sulle 280 pagine del campione, tassonomia dei fallimenti, distribuzione
del rapporto note/parole) **non è stata eseguita**: è un passo separato, previsto dalla
proposta e non ancora fatto. Restano fuori scope: producer nuovi, contratti, wiring nel job,
modifiche ai renderer, IR 2, regole di Resolution. L'emettitore diagnostico **non è** il
punto di partenza del renderer IR-first: una sua eventuale promozione è una decisione da
prendere esplicitamente, e nulla in questa milestone la costituisce.

Appunto per una futura passata di raffinamento (non aperta, non numerata): le schede statistiche mostro nel bestiario (es. DB.pdf, GUERRIERO/ARCIERE/CAMPIONE, riquadro a colonne non allineate) non sono table_candidate (nessuna griglia regolare, verificato per ispezione visiva) né riconducibili a un riquadro puramente visivo (embedded_visual/interior_visual_frame): contengono testo strutturato a campi etichetta:valore da preservare, reso oggi con sfondo decorativo che andrebbe rimosso in resa, mantenendo la struttura leggibile. Nessuna decisione presa: possibile candidato per un futuro structural_kind dedicato o per un trattamento di rendering separato dalla classificazione geometrica. Tocca il quarto punto bloccante di Milestone 33 (structural_kind unico vs. distinzione corpo/struttura interna).

<!-- FINE DI State.md — se non leggi questa riga, la tua copia è troncata: fermati e dillo -->
