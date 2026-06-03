# ManReader — Stato progetto

## Versione corrente: v1.3

## Moduli
- `main.py` — CLI, orchestrazione
- `config.py` — parametri layout (dataclass)
- `extractor.py` — estrazione testo/immagini/vettoriali/tabelle; rilevamento colonne per-pagina; filtro ripetizioni; lettura TOC
- `deduplicator.py` — deduplicazione asset grafici ripetuti (sfondi, ribbon, watermark)
- `describer.py` — descrizioni AI via backend selezionabile (Anthropic, Gemini, Ollama)
- `epub_builder.py` — assemblaggio EPUB; rilevamento capitoli; rendering HTML
- `requirements.txt`

## Funzionalità implementate
- Estrazione testo con rilevamento capitoli via TOC embedded (get_toc()), euristica font come fallback
- **Rilevamento colonne per-pagina (v1.2)**: modalità auto analizza ogni pagina indipendentemente; gestisce layout misto; i blocchi full-width vengono separati dai blocchi di colonna e posizionati correttamente
- Filtro statistico testo ripetuto (header/footer/watermark) via hash testo normalizzato e analisi zona Y
- Estrazione immagini raster via PyMuPDF
- Estrazione tabelle via pdfplumber, salvate come CSV
- Estrazione vettoriali via get_drawings() con clustering union-find, esportati come SVG
- **Descrizioni AI multi-backend (v1.3)**: selezionabile via `--vision-backend anthropic|gemini|ollama`
  - `anthropic`: Claude Sonnet via API Anthropic (richiede ANTHROPIC_API_KEY)
  - `gemini`: Google Gemini 2.0 Flash, tier gratuito 1500 req/giorno (richiede GEMINI_API_KEY)
  - `ollama`: inferenza locale, nessuna API key (richiede Ollama in esecuzione con modello vision)
- Generazione EPUB via ebooklib; asset come blocchi di riferimento (non embedded); tabelle inline HTML
- Deduplicazione asset ripetuti via MD5: prompt interattivo (sfondo/ignora/mantieni) o --auto-background

## Architettura describer.py (v1.3)
Pattern strategy: classe base astratta `BaseDescriber` + implementazioni `AnthropicDescriber`, `GeminiDescriber`, `OllamaDescriber`. Factory function `create_describer()` istanzia il backend corretto. Interfaccia pubblica (`describe_image`, `describe_table`) identica per tutti i backend. Alias `AIDescriber = AnthropicDescriber` per retrocompatibilità con eventuali import diretti.

## Apprendimenti tecnici
- ebooklib richiede contenuto capitoli come bytes UTF-8; body vuoto causa crash lxml "Document is empty"
- XHTML senza DOCTYPE esterno XHTML 1.1 (evita risoluzione DTD offline)
- Fish shell: activate.fish, non activate; pip potrebbe non essere in PATH su Arch
- TOC embedded più affidabile di euristiche font per rilevamento capitoli
- Blocchi full-width (>60% larghezza pagina) vanno esclusi dal rilevamento colonne e gestiti separatamente nell'ordinamento
- Gemini API: usa `google-generativeai`, immagini passate come dict `{mime_type, data}` non base64
- Ollama API: endpoint REST `/api/generate`, immagini come lista base64 nel campo `images`; verificare disponibilità modello su `/api/tags` prima dell'uso

## Parametri CLI rilevanti (v1.3)
- `--columns auto|1|2` — default auto (rileva per pagina)
- `--column-gap 0.08` — soglia gap per classificare doppia colonna
- `--column-split 0.5` — override manuale posizione divisore
- `--no-dedup` / `--auto-background` — deduplicazione asset
- `--header-zone` / `--repeat-threshold` — filtro testo ripetuto
- `--pages 1-20` — test su sottoinsieme
- `--vision-backend anthropic|gemini|ollama` — backend AI (default: anthropic)
- `--ollama-model NOME` — modello Ollama (default: llama3.2-vision)
- `--ollama-host URL` — URL server Ollama (default: http://localhost:11434)

## Variabili d'ambiente
- `ANTHROPIC_API_KEY` — per backend anthropic
- `GEMINI_API_KEY` — per backend gemini

## Dipendenze opzionali (non in requirements.txt di base)
- `google-generativeai>=0.8.0` — necessaria solo con `--vision-backend gemini`
- `requests>=2.31.0` — necessaria solo con `--vision-backend ollama`

## Ambiente
- CachyOS (Arch-based Linux), Fish shell, Python virtualenv
- PyMuPDF, pdfplumber, ebooklib, anthropic, Pillow

## Prossimi step
- Test su manuali reali con layout misto e verifica qualità rilevamento colonne
- Eventuale tuning column_gap_threshold per tipi di PDF diversi
- Selettore di cartella di input e output dei file
- Test backend Gemini e Ollama (RX 7800 XT con ROCm) su manuali reali
