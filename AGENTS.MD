# ManReader

Obiettivo:
Convertire manuali PDF TTRPG in EPUB e Markdown semantici.

Vincoli:

- Elaborazione 100% locale
- Python 3.12+
- Open source preferito
- Nessun servizio cloud obbligatorio

Stack:

- PyMuPDF
- Docling
- EbookLib
- Ollama
- Qwen2.5-VL
- SQLite

Priorità attuali:

1. Output Markdown
2. Intermediate Representation (IR)
3. Entity Extraction
4. Cross-linking EPUB

Regole:

- Soluzioni semplici prima di quelle complesse
- Non introdurre framework inutili
- Mantenere compatibilità con PDF digitali e scansioni

# Regola AI enrichment

L'AI locale non deve riscrivere direttamente il contenuto estratto dal PDF.

Pipeline:

1. estrazione deterministica → document_ir.json
2. AI enrichment → enriched_ir.json
3. modifiche sicure auto-applicate sopra soglia
4. casi dubbi → review_queue.json
5. correzioni manuali → human_overrides.json

Soglie iniziali:

- confidence >= 0.85: auto-apply
- 0.60 <= confidence < 0.85: review_queue
- confidence < 0.60: issues

L'utente deve poter correggere nome file, descrizione, alt text e classificazione.

# Stile commenti

- Tutti i moduli devono avere una docstring iniziale.
- Tutte le funzioni pubbliche devono avere una docstring.
- Commentare il "perché", non il "cosa".
- Non rimuovere commenti esistenti senza motivo.
- Aggiornare i commenti quando il comportamento cambia.
- Preferire nomi chiari a commenti superflui.

# Dipendenze

- Usare il minor numero possibile di librerie.
- Preferire sempre la standard library.
- Ogni nuova dipendenza deve essere giustificata.
- Non introdurre librerie per funzionalità semplici già coperte dalla standard library.
- Evitare dipendenze fragili o non essenziali.
- Separare dipendenze opzionali, come AI/OCR/export, dalle dipendenze core.

# Qualità codice

Il codice deve essere compatibile con:

- Ruff
- BasedPyright

Ogni commit deve passare:

ruff check .
basedpyright
