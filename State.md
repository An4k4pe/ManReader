# ManReader — Stato progetto

## Versione corrente: v1.4

## Moduli
- `main.py` — CLI, orchestrazione
- `config.py` — parametri layout (dataclass)
- `extractor.py` — estrazione testo/immagini/vettoriali/tabelle; rilevamento colonne per-pagina; filtro ripetizioni; lettura TOC
- `deduplicator.py` — deduplicazione asset grafici ripetuti (sfondi, ribbon, watermark)
- `describer.py` — descrizioni AI via backend selezionabile (Anthropic, Ollama)
- `epub_builder.py` — assemblaggio EPUB; rilevamento capitoli; rendering HTML
- `requirements.txt`

## Funzionalità implementate
- Estrazione testo con rilevamento capitoli via TOC embedded (get_toc()), euristica font come fallback
- Rilevamento colonne per-pagina (v1.2): modalità auto analizza ogni pagina indipendentemente
- Filtro statistico testo ripetuto (header/footer/watermark)
- Estrazione immagini raster, tabelle CSV, vettoriali SVG
- Descrizioni AI multi-backend (v1.4): anthropic | ollama
- Generazione EPUB via ebooklib
- Deduplicazione asset ripetuti via MD5

## Architettura describer.py (v1.4)
Pattern strategy: BaseDescriber (ABC) → AnthropicDescriber, OllamaDescriber.
Factory function create_describer(backend, ...). Alias AIDescriber = AnthropicDescriber.
Backend Gemini rimosso: free tier Google tagliato a dicembre 2025, quota effettiva
0-20 req/giorno su molti account, inaffidabile per uso batch.

## Backend vision
- anthropic: Claude Sonnet via API (richiede ANTHROPIC_API_KEY)
- ollama: inferenza locale REST /api/generate, immagini come base64 nel campo images
  Modello consigliato: llama3.2-vision (11B, ~7GB VRAM in Q4)
  Compatibile con RX 7800 XT (16GB VRAM) via ROCm su CachyOS

## Apprendimenti tecnici
- ebooklib: body vuoto causa crash lxml; XHTML senza DOCTYPE esterno
- TOC embedded più affidabile di euristiche font
- Blocchi full-width (>60% larghezza) vanno esclusi dal rilevamento colonne
- Ollama API: endpoint /api/generate, immagini come lista base64; verificare /api/tags prima
- Gemini free tier: inaffidabile da dic 2025, rimosso dal progetto

## Parametri CLI (v1.4)
- `--vision-backend anthropic|ollama` — default: anthropic
- `--ollama-model NOME` — default: llama3.2-vision
- `--ollama-host URL` — default: http://localhost:11434
- `--columns auto|1|2`, `--column-gap`, `--column-split`
- `--no-dedup`, `--auto-background`
- `--header-zone`, `--repeat-threshold`
- `--pages 1-20`

## Variabili d'ambiente
- ANTHROPIC_API_KEY — per backend anthropic

## Ambiente sviluppo
- CachyOS (Arch-based Linux), Fish shell, Python virtualenv
- PyMuPDF, pdfplumber, ebooklib, anthropic, Pillow, requests

## Prossimi step
- rimuovere la scritta p1 dai nomi file, intanto è numerata sbagliata
- nel file pdf rimuovere le diciture del tipo file: imm vettoriale....
- aggiungere modalità per modificare a mano i titoli o le descrizioni e uploadarle nei file
- Test llama3.2-vision su manuali reali
- Valutare qualità descrizioni rispetto ad Anthropic
