# ManReader — Stato progetto

## Versione corrente: v1.2

## Moduli
- `main.py` — CLI, orchestrazione
- `config.py` — parametri layout (dataclass)
- `extractor.py` — estrazione testo/immagini/vettoriali/tabelle; rilevamento colonne per-pagina; filtro ripetizioni; lettura TOC
- `deduplicator.py` — deduplicazione asset grafici ripetuti (sfondi, ribbon, watermark)
- `describer.py` — descrizioni AI via API Anthropic
- `epub_builder.py` — assemblaggio EPUB; rilevamento capitoli; rendering HTML
- `requirements.txt`

## Funzionalità implementate
- Estrazione testo con rilevamento capitoli via TOC embedded (get_toc()), euristica font come fallback
- **Rilevamento colonne per-pagina (v1.2)**: modalità auto analizza ogni pagina indipendentemente; gestisce layout misto (intro singola colonna + corpo doppia colonna nello stesso PDF); i blocchi full-width (titoli, intestazioni di sezione) vengono separati dai blocchi di colonna e posizionati correttamente
- Filtro statistico testo ripetuto (header/footer/watermark) via hash testo normalizzato e analisi zona Y
- Estrazione immagini raster via PyMuPDF
- Estrazione tabelle via pdfplumber, salvate come CSV
- Estrazione vettoriali via get_drawings() con clustering union-find, esportati come SVG
- Descrizioni AI immagini e tabelle via API Anthropic
- Generazione EPUB via ebooklib; asset come blocchi di riferimento (non embedded); tabelle inline HTML
- Deduplicazione asset ripetuti via MD5: prompt interattivo (sfondo/ignora/mantieni) o --auto-background

## Apprendimenti tecnici
- ebooklib richiede contenuto capitoli come bytes UTF-8; body vuoto causa crash lxml "Document is empty"
- XHTML senza DOCTYPE esterno XHTML 1.1 (evita risoluzione DTD offline)
- Fish shell: activate.fish, non activate; pip potrebbe non essere in PATH su Arch
- TOC embedded più affidabile di euristiche font per rilevamento capitoli
- Blocchi full-width (>60% larghezza pagina) vanno esclusi dal rilevamento colonne e gestiti separatamente nell'ordinamento

## Parametri CLI rilevanti (v1.2)
- `--columns auto|1|2` — default auto (rileva per pagina)
- `--column-gap 0.08` — soglia gap per classificare doppia colonna
- `--column-split 0.5` — override manuale posizione divisore
- `--no-dedup` / `--auto-background` — deduplicazione asset
- `--header-zone` / `--repeat-threshold` — filtro testo ripetuto
- `--pages 1-20` — test su sottoinsieme

## Ambiente
- CachyOS (Arch-based Linux), Fish shell, Python virtualenv
- PyMuPDF, pdfplumber, ebooklib, anthropic, Pillow

## Prossimi step
- Test su manuali reali con layout misto e verifica qualità rilevamento colonne
- Eventuale tuning column_gap_threshold per tipi di PDF diversi
- selettore di cartella di imput e output dei file
