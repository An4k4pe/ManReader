# ManReader — Regole per agenti e sviluppo

## Stato corrente

Il progetto è in fase di progettazione globale v0.6.

La pipeline attuale è una baseline legacy funzionante. Non deve essere rimossa o rifattorizzata finché non sono approvati:

- architettura target;
- piano di migrazione;
- compatibilità;
- test di non regressione;
- primo step operativo.

`State.md` è la fonte aggiornata sullo stato e sulle decisioni di fase.

## Obiettivo

Convertire manuali PDF TTRPG in Markdown ed EPUB semantici, preservando il contenuto e permettendo revisione, profili riutilizzabili e AI locale opzionale.

## Vincoli permanenti

- elaborazione locale;
- nessun servizio cloud obbligatorio;
- Python 3.12+;
- dipendenze minime;
- open source preferito;
- compatibilità con PDF digitali e, in futuro, scansioni;
- nessuna invenzione del contenuto mancante;
- output e decisioni verificabili;
- nessun commit automatico.

## Toolchain corrente

Core attuale:

- PyMuPDF;
- pdfplumber;
- EbookLib;
- Pillow;
- requests;
- Ollama opzionale.

Qualità:

- Ruff;
- BasedPyright;
- unittest.

Non introdurre nuove dipendenze o framework GUI senza decisione architetturale e motivazione.

## Fase progettuale

Durante la fase progettuale:

- non modificare codice funzionale;
- non preparare commit;
- non avviare refactor di `extractor.py`;
- non aggiungere euristiche specifiche per i manuali benchmark;
- non scegliere il framework GUI;
- non implementare workspace, profili o AI calibration;
- produrre documenti, schemi, alternative, rischi e piani di migrazione.

Chat A decide.
Chat B revisiona.
Zed agent non riceve task progettuali.

## Refactor

La regola non è “niente refactor ampi”, ma:

> niente refactor ampi non progettati.

Un refactor approvato può spostare responsabilità fuori da `extractor.py`, `ir_builder.py` o altri moduli, purché:

- sia previsto dal documento architetturale;
- abbia una migrazione incrementale;
- preservi la baseline finché il nuovo percorso non è verificato;
- sia diviso in commit testabili;
- abbia rollback chiaro;
- non mescoli riorganizzazione e cambi funzionali non necessari.

Le responsabilità correnti dei moduli sono descrittive, non vincoli permanenti della futura architettura.

## Principi architetturali in valutazione

La progettazione deve mantenere separati:

```text
primitive osservate
→ regioni e relazioni
→ semantica
→ IR
→ renderer
```

Inoltre:

- core headless;
- CLI e GUI come client;
- workspace persistente per raw, candidati e review;
- output finale separato;
- profili salvabili/importabili/versionati;
- archetipi di pagina;
- AI locale opzionale tramite JSON validabili;
- nessun codice generato dall'AI per manuale;
- tracciabilità delle decisioni.

Questi principi sono direzione approvata di massima, ma gli schemi e i moduli definitivi devono ancora essere progettati.

## Regole AI

L'AI locale può proporre:

- classificazioni;
- archetipi;
- mapping glifi;
- anomalie;
- decisioni di review.

Non deve:

- riscrivere direttamente il contenuto estratto;
- generare codice specifico per un manuale;
- cancellare file;
- applicare modifiche irreversibili senza validazione;
- sostituire il profilo persistente.

Ogni proposta AI deve riferirsi a ID stabili e passare da schema validation e policy checks.

## Dati e output

Durante la futura pipeline:

- workspace e output finale devono essere separati;
- candidati non approvati non entrano nell'output;
- raw e primitive non devono essere distrutti prematuramente;
- asset fisico, regione layout e blocco semantico sono entità diverse;
- profili e decisioni devono essere leggibili e modificabili;
- i file generati non vanno committati.

## Regole operative di implementazione

Quando si tornerà all'implementazione:

- leggere `State.md` e questo file;
- un task per commit;
- file ammessi e vietati;
- niente hardcode su manuale, pagina, titolo, filename o parola;
- non usare `git add .`;
- non committare output, workspace, dump o diagnostica;
- test sintetici per nuove regole;
- benchmark reali per generalizzazione;
- verificare:
  - Ruff;
  - BasedPyright;
  - test mirati;
  - suite completa;
  - diff;
  - `git status --short`.

I builder e la GUI non devono reinterpretare direttamente il PDF: devono consumare dati del core.

## Baseline da preservare

Finché la nuova pipeline non è attiva, restano non-regressione:

- callout DB stabilizzati;
- tabelle DB e filtro testo duplicato;
- classificazione clutter;
- immagini readable;
- reading order DB, incluso MONETE/CIMELIO;
- dropcap irrisolti senza invenzione;
- IR e Markdown correnti.

## Aggiornamento documenti

Aggiornare:

- `State.md` a fine milestone o cambio di fase;
- `AGENTS.MD` quando cambiano regole permanenti o pipeline approvata;
- workflow due-chat quando cambiano ruoli e modalità operative.
