# ManReader — Stato progetto

## Versione corrente: v0.3

## Moduli

- `main.py` — CLI, orchestrazione
- `config.py` — parametri layout (dataclass)
- `extractor.py` — estrazione testo/immagini/vettoriali/tabelle; AssetIndex CSV; rilevamento colonne per-pagina; filtro ripetizioni; lettura TOC
- `deduplicator.py` — deduplicazione asset grafici ripetuti (sfondi, ribbon, watermark)
- `describer.py` — descrizioni AI via backend selezionabile (Ollama)
- `ir_model.py` — dataclass IR (`DocumentIR`, `PageIR`, `BlockIR`, `AssetIR`, entity/review model)
- `ir_store.py` — persistenza JSON della IR
- `ir_validate.py` — validazione leggera della IR
- `ir_builder.py` — costruzione e classificazione semantica della IR
- `markdown_builder.py` — rendering Markdown da IR
- `epub_builder.py` — assemblaggio EPUB; titoli leggibili da asset_index; rendering HTML
- `asset_manager.py` — applicazione post-build di rename/edit da asset_index.csv all'EPUB
- `requirements.txt`

## Funzionalità implementate

- Estrazione testo con rilevamento capitoli via TOC embedded (`get_toc()`), euristica font come fallback
- Rilevamento colonne per-pagina: modalità auto analizza ogni pagina indipendentemente
- Filtro statistico testo ripetuto (header/footer/watermark)
- Estrazione immagini raster, tabelle CSV, vettoriali SVG
- Deduplicazione asset ripetuti via MD5
- Descrizioni AI via Ollama locale
- Generazione EPUB via ebooklib
- Generazione Markdown da IR tramite `markdown_builder.py`
- Esportazione sempre attiva di `output/<book>/ir/document_ir.json`
- Validazione IR tramite `ir_validate.py`

## Milestone IR + Markdown

Stato attuale:

- Dataclass IR create: `DocumentIR`, `PageIR`, `BlockIR`, `AssetIR`, `AIProposal`, `ReviewItem`, `HumanOverride`, `Issue`, `EntityIR`
- Persistenza JSON della IR tramite `ir_store.py`
- Validatore leggero della IR tramite `ir_validate.py`
- `document_ir.json` esportato sempre in `output/<book>/ir/document_ir.json`
- Builder Markdown da IR tramite `markdown_builder.py`
- CLI `--format epub|markdown|both`
- Default ancora `epub`
- Asset `is_background=True` o `is_duplicate=True` esclusi dal reading flow della IR
- Builder Markdown consuma la IR e non deve reinterpretare il PDF
- EPUB non è ancora allineato completamente al percorso IR

### Callout / box testuali

Implementato riconoscimento prudente dei callout in `ir_builder.py`:

- approccio region-first: un callout richiede una regione grafica `image`/`vector` associata;
- title e body devono appartenere geometricamente alla stessa regione;
- supporto a body `role="bullet_list"` dentro regione;
- durante la ricerca del body, asset non testuali fuori regione possono essere skippati;
- supporto a body composto da più blocchi testuali dentro la stessa regione;
- supporto a due callout affiancati con ordine globale `title-title-image-image-body-body`, associando ogni title/body tramite regione grafica e impedendo doppio consumo del body;
- rendering Markdown come callout Obsidian `> [!INFO]`.

Casi DB verificati come risolti o migliorati:

- `TU E GLI ALTRI`
- `ABBREVIAZIONI`
- `CREARE IL TUO PERSONAGGIO`
- `CAPACITÀ: RANCOROSO`
- `CAPACITÀ: DIFFICILE DA PRENDERE`
- `CAPACITÀ: SCONTROSO`
- `CAPACITÀ: ISTINTI DA CACCIATORE`
- `MAGIA` pagina 22
- `MAGIA` pagina 28
- `CAPACITÀ ALTERNATIVE`
- `DEBOLEZZA`
- `CIMELIO`
- `MONETE`

### Tabelle e duplicati nel reading flow

Implementato filtro IR per evitare duplicazione del testo tabellare nel reading flow:

- i `text block` contenuti o fortemente sovrapposti alla bbox di una `table asset` già riconosciuta vengono esclusi dal flusso leggibile della IR;
- la regola è geometrica, non basata su parole/titoli/pagine;
- il CSV resta l'asset leggibile della tabella;
- le note esterne alla bbox della tabella vengono preservate.

Caso verificato:

- DB pagina 26, `EFFETTI DELL’ETÀ`: rimosse dal Markdown le righe duplicate `1–3 Giovane...` e `6 Vecchio...`; preservata la nota sotto tabella e preservata `p26_tbl1.csv`.

## Problemi noti attuali

### Extractor / segmentazione testo

- `extractor.py` produce ancora frammenti testuali separati in alcuni casi.
- Il merge testo attuale è euristico e non sostituisce un refactor controllato di `extractor.py`.
- Alcuni body sembrano mancanti già in IR, quindi non risolvibili solo in `ir_builder.py`.
  - Caso osservato: `CAPACITÀ: ADATTABILE` ha titolo + regione grafica ma non un body testuale visibile vicino.
- Alcuni blocchi title/body sono fusi nello stesso `TextBlock` e richiedono segmentazione/split upstream.
  - Caso osservato: `CAPACITÀ: PALMIPEDE` fuso con testo che visivamente appartiene al box precedente.
- Follow-up extractor: preservare enfasi inline quando i gruppi di `TextBlock` vengono ricostruiti da `get_text("blocks")`; il rebuild attuale migliora il testo ma può collassare più span in uno solo.
- Known follow-up: artefatti come `resistent e`, `gl i`, `deci mata`, `p urtroppo`, `suoam ico` sono visibili in `DocumentIR` come blocchi adiacenti separati o testi già ricostruiti in modo imperfetto; richiedono merge/split controllato a livello blocco o extractor.

### Heading / struttura

- Correggere titoli con lettere spaziate o decorative, es. `L’A RRIVO DELL ’O RDA`.
- Correggere heading incollati, es. `MECCANICHE ECOMPLICAZIONI`.
- Verificare gerarchie heading da TOC/font:
  - alcuni capitoli principali risultano `##` invece di `#`;
  - alcune sottosezioni risultano heading errato o testo normale.
- Verificare residui di indice/manual TOC e footer quando il filtro statistico non è affidabile su poche pagine.

### Callout residui

- `CAPACITÀ: PACE INTERIORE` / `CAPACITÀ: PALMIPEDE`: non risolvere con ulteriore scan permissivo; il problema sembra di segmentazione title/body e ordine visivo.
- `ALTRI METODI`: non trattarlo come semplice callout; il body corretto è nella regione sinistra, ma l'ordine IR mette in mezzo blocchi normali della colonna destra (`Agilità`, `Intelligenza`, `Volontà`, `Carisma`). Serve diagnosi di ordine colonne/geometria, non merge callout generico.
- `CAPACITÀ: ADATTABILE`: probabile body mancante o non separato già in IR/extractor.

### Tabelle

- Qualità CSV ancora imperfetta in alcuni casi.
  - Caso osservato: DB pagina 26, `p26_tbl1.csv`, riga `1–3` contiene `e +1 AGI COS`, da verificare in extractor/table reconstruction.
- Verificare doppia estrazione vector/table:
  - se i vettoriali sono solo bordi/linee della tabella, classificarli come decorativi/strutturali e non come asset leggibile.
- Verificare se tabelle frammentate siano da unire/deduplicare a livello extractor/IR.
  - Caso storico: DB pagina 8, possibili frammenti `p8_tbl2.csv`, `p8_tbl3.csv`, `p8_tbl4.csv`.
- Distinguere meglio testo body da label/celle/table-like text nei casi in cui la tabella non viene riconosciuta o viene riconosciuta parzialmente.

### Asset / deduplicazione

- Gestione canonica asset/occurrences/pages ancora da implementare.
- Gli asset duplicati dovranno essere tracciati tramite asset canonico e lista occorrenze/pagine, così che eventuali note o link puntino sempre alla prima occorrenza.
- Vettoriali decorativi residui: barcode/numeri pagina/linee di layout da classificare meglio come decorativi/strutturali.

### AI enrichment

- AI enrichment ancora da separare pienamente dalla fase estrattiva.
- L'AI locale non deve riscrivere il contenuto estratto dal PDF; deve produrre enrichment/review sopra IR deterministica.

## Prossimi step consigliati

Priorità immediata:

1. Non aggiungere ulteriori scan permissivi ai callout: i residui principali richiedono extractor/segmentazione o ordine colonne.
2. Scegliere un micro-commit singolo tra:
   - migliorare qualità CSV `p26_tbl1.csv` in extractor/table reconstruction;
   - diagnosticare `CAPACITÀ: ADATTABILE` per capire se il body manca già in extraction;
   - diagnosticare `PACE INTERIORE` / `PALMIPEDE` come problema di split `TextBlock`;
   - diagnosticare `ALTRI METODI` come problema di ordine colonne/geometria dentro box.
3. Continuare con commit piccoli e testabili: massimo 1 problema reale + test sintetici + controllo manuale DB.

Priorità media:

- Rivedere heading hierarchy usando TOC embedded + font/bbox con test mirati.
- Pulire footer/indice residui su run a poche pagine e run lunghi.
- Migliorare classificazione di vettoriali decorativi/strutturali.
- Valutare metadati `role`/`subtype` su `BlockIR` per descrivere funzioni semantiche come `question_list`, `table_label`, `caption`, `boxed_text`, senza granularità parola-per-parola.

## Asset Index (v2.0)

Registro centrale `extracted/asset_index.csv` con campi:
sha, nome_file, tipo, pagina, titolo, descrizione, modificato

- Sostituisce i file .txt per-asset delle versioni precedenti
- SHA = MD5 del contenuto binario (chiave stabile che sopravvive ai rename)
- Campo `modificato=si` protegge le entry editate manualmente dalla sovrascrittura
- Il builder usa il campo `titolo` per il testo visibile inline nell'EPUB
  (separato dal nome file che appare solo nella footnote)
- Logica merge su rebuild: entry protette intoccabili, nuove aggiunte, non-protette aggiornate

## asset_manager.py (v2.0)

Script autonomo post-build:
python asset_manager.py output/NomePDF/

Flusso:

1. Legge asset_index.csv, trova entry con modificato=si
2. Rinomina i file fisici nella sottocartella corretta (images/vectors/tables/)
3. Apre i .xhtml dell'EPUB (zip), aggiorna titolo inline e path in footnote
4. Resetta modificato=no dopo applicazione
5. Salva CSV aggiornato

## Architettura describer.py

Pattern strategy: BaseDescriber (ABC) → OllamaDescriber.
Factory function create_describer(backend, ...).
Backend Gemini rimosso: free tier Google inaffidabile da dic 2025.
Il core CLI espone solo Ollama come backend vision locale.

## Backend vision

- ollama: inferenza locale REST `/api/generate`, immagini come base64
- Modello consigliato: `gemma4:12b`
- Compatibile con RX 7800 XT (16GB VRAM) via ROCm su CachyOS

## Apprendimenti tecnici

- ebooklib: body vuoto causa crash lxml; XHTML senza DOCTYPE esterno
- TOC embedded più affidabile di euristiche font
- Blocchi full-width (>60% larghezza) vanno esclusi dal rilevamento colonne
- Ollama API: endpoint `/api/generate`; `num_predict:256` causa output vuoto su gemma4 — evitare
- PyMuPDF: `Rect.expand()` non esiste; usare espansione manuale coordinate
- PyMuPDF: `Rect.is_infinite` corretto
- Full-page background: non aggiungere a `excluded_bboxes` perché il testo è layer separato
- Regex con DOTALL pericolosa per edit su sorgenti Python: usare `str.replace()` con blocchi letterali

## Parametri CLI

- `--ollama-model NOME` — default: `gemma4:12b`
- `--ollama-host URL` — default: `http://localhost:11434`
- `--columns auto|1|2`, `--column-gap`, `--column-split`
- `--no-dedup`, `--auto-background`
- `--header-zone`, `--repeat-threshold`
- `--pages 1-20`

## Ambiente sviluppo

- CachyOS (Arch-based Linux), Fish shell, Python virtualenv
- PyMuPDF, pdfplumber, ebooklib, Pillow, requests

## Done / verifiche recenti

- Aggiunti test `unittest` per `markdown_builder.py` e `ir_builder.py`
- EPUB: rimossa pagina TOC manuale duplicata; resta la navigazione standard EPUB
- Markdown: supporto heading-like e inline emphasis prudente
- Nota: italic puro non viene ancora renderizzato perché lo stile estratto è troppo rumoroso
- test.pdf completo: ok, 1 tabella vera, 0 vettoriali
- DB.pdf pagine 1–10: 1 tabella vera recuperata, 10 falsi positivi rimossi
- DB.pdf pagine 8–30: callout region-first molto migliorati e filtro testo tabellare duplicato verificato su pagina 26
- Vettoriali DB residui identificati come barcode/numeri pagina decorativi, da trattare più avanti nella fase asset/decorazioni
