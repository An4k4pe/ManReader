# ManReader — Stato progetto

## Versione corrente: v2.0

## Moduli

- `main.py` — CLI, orchestrazione
- `config.py` — parametri layout (dataclass)
- `extractor.py` — estrazione testo/immagini/vettoriali/tabelle; AssetIndex CSV; rilevamento colonne per-pagina; filtro ripetizioni; lettura TOC
- `deduplicator.py` — deduplicazione asset grafici ripetuti (sfondi, ribbon, watermark)
- `describer.py` — descrizioni AI via backend selezionabile (Ollama)
- `epub_builder.py` — assemblaggio EPUB; titoli leggibili da asset_index; rendering HTML
- `asset_manager.py` — applicazione post-build di rename/edit da asset_index.csv all'EPUB
- `requirements.txt`

## Funzionalità implementate

- Estrazione testo con rilevamento capitoli via TOC embedded (get_toc()), euristica font come fallback
- Rilevamento colonne per-pagina: modalità auto analizza ogni pagina indipendentemente
- Filtro statistico testo ripetuto (header/footer/watermark)
- Estrazione immagini raster, tabelle CSV, vettoriali SVG
- Descrizioni AI via Ollama locale
- Generazione EPUB via ebooklib
- Deduplicazione asset ripetuti via MD5

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

Problemi noti:

- `extractor.py` produce ancora frammenti testuali separati in alcuni casi
- Il merge testo attuale è euristico e non sostituisce un refactor di `extractor.py`
- Gestione canonica asset/occurrences/pages ancora da implementare
- AI enrichment ancora da separare pienamente dalla fase estrattiva

Prossimo step consigliato:

- Introdurre test minimi per `ir_builder.py` e `markdown_builder.py`, oppure iniziare un refactor controllato di `extractor.py`/`deduplicator.py`

## Asset Index (v2.0)

Registro centrale `extracted/asset_index.csv` con campi:
sha, nome_file, tipo, pagina, titolo, descrizione, modificato

- Sostituisce i file .txt per-asset delle versioni precedenti
- SHA = MD5 del contenuto binario (chiave stabile che sopravvive ai rename)
- Campo `modificato=si` protegge le entry editate manualmente dal sovrascrittura
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

- ollama: inferenza locale REST /api/generate, immagini come base64
  Modello consigliato: gemma4:12b
  Compatibile con RX 7800 XT (16GB VRAM) via ROCm su CachyOS

## Apprendimenti tecnici

- ebooklib: body vuoto causa crash lxml; XHTML senza DOCTYPE esterno
- TOC embedded più affidabile di euristiche font
- Blocchi full-width (>60% larghezza) vanno esclusi dal rilevamento colonne
- Ollama API: endpoint /api/generate; num_predict:256 causa output vuoto su gemma4 — evitare
- PyMuPDF: Rect.expand() non esiste (espansione manuale coordinate); Rect.is_infinite corretto
- Full-page background: non aggiungere a excluded_bboxes (il testo è layer separato)
- Regex con DOTALL pericolosa per edit su sorgenti Python — usare str.replace() con blocchi letterali

## Parametri CLI

- `--ollama-model NOME` — default: gemma4:12b
- `--ollama-host URL` — default: http://localhost:11434
- `--columns auto|1|2`, `--column-gap`, `--column-split`
- `--no-dedup`, `--auto-background`
- `--header-zone`, `--repeat-threshold`
- `--pages 1-20`

## Ambiente sviluppo

- CachyOS (Arch-based Linux), Fish shell, Python virtualenv
- PyMuPDF, pdfplumber, ebooklib, Pillow, requests

## Prossimi step

- Test asset_manager su EPUB reale con rename
- Aggiungere epub:type alle footnote (standard EPUB)
- Valutare qualità descrizioni gemma4:12b su manuali reali
- gestire i box o simili, se non sono già gestiti come callout o note in linea
- creare una versione markdown del manuale strippato con link alle immagini e/o descrizione
- Known follow-up: remaining artifacts such as "resistent e", "gl i" and
  "deci mata" are now visible in DocumentIR as separate adjacent text blocks,
  so they require a future block-level merge pass rather than span-level join.
- Aggiunti test `unittest` per `markdown_builder.py` e `ir_builder.py`
- EPUB: rimossa pagina TOC manuale duplicata; resta la navigazione standard EPUB
- Markdown: supporto heading-like e inline emphasis prudente
- Nota: italic puro non viene ancora renderizzato perché lo stile estratto è troppo rumoroso
- Follow-up extractor: preservare enfasi inline quando i gruppi di TextBlock frammentati vengono ricostruiti tramite get_text("blocks"). Il rebuild attuale migliora molto il testo pre-IR e corregge artefatti come resistent e, p urtroppo, gl i, suoam ico, deci mata, ma nei gruppi ricostruiti collassa gli span in un solo TextSpan, quindi può perdere bold/italic inline, per esempio nomi resi prima come enfasi Markdown.
- Follow-up extractor: preservare enfasi inline quando i gruppi di `TextBlock` vengono ricostruiti da `get_text("blocks")`; il rebuild attuale migliora il testo ma può collassare più span in uno solo.
- Follow-up extractor/heading: gestire titoli con lettere spaziate o decorative, es. `L’A RRIVO DELL ’O RDA`.
- Follow-up IR/extractor: classificare blocchi con marker `❖` come liste/question prompts, separando gli item invece di renderli come unico paragrafo continuo.
- Follow-up IR/extractor: distinguere testo body da label/celle/box/table-like text; casi osservati: `**La piccola cappella uberiana del villaggio**`, `**Un'offerta votiva bruciata davanti alla statua di Uberia**`, `**5 La casa del parroco**`, `**Un sermone incompiuto sul leggio**`.
- Follow-up IR model: valutare metadati `role`/`subtype` su `BlockIR` per descrivere funzioni semantiche come `question_list`, `table_label`, `caption`, `boxed_text`, senza introdurre per ora una granularità parola-per-parola.
