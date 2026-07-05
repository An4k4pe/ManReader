# ManReader — Regole per agenti e sviluppo

## Stato corrente

Il progetto è in **Modalità I — implementazione incrementale**, versione di fase v0.8.

L'architettura target e il piano generale di migrazione sono approvati.

La pipeline corrente resta la baseline legacy funzionante e non deve essere rimossa o riscritta finché il nuovo percorso non è stato verificato in shadow mode e i criteri di non-regressione sono soddisfatti.

`State.md` è la fonte aggiornata sullo stato, sulle milestone e sulle decisioni di fase.

## Obiettivo

Convertire manuali PDF TTRPG in Markdown ed EPUB semantici, preservando il contenuto e permettendo:

- revisione visuale;
- profili riutilizzabili;
- decisioni tracciabili;
- job riprendibili;
- AI locale opzionale;
- una IR comune ai renderer.

## Vincoli permanenti

- elaborazione locale;
- nessun servizio cloud obbligatorio;
- Python 3.12+;
- dipendenze minime;
- open source preferito;
- compatibilità con PDF digitali e, in futuro, scansioni;
- nessuna invenzione del contenuto mancante;
- output e decisioni verificabili;
- nessun commit automatico;
- output, workspace, dump e diagnostica non committati salvo documento sorgente esplicitamente previsto dal task.

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

Non introdurre nuove dipendenze, framework GUI o storage aggiuntivi senza decisione esplicita di Chat A e motivazione verificabile.

## Ruoli operativi

### Chat A

Chat A è la fonte decisionale.

In Modalità I:

- legge `State.md` e `AGENTS.MD`;
- identifica il livello del problema;
- restringe lo scope;
- stabilisce file ammessi e vietati;
- definisce test e criteri di accettazione;
- prepara il task per Zed agent o per implementazione manuale;
- revisiona diff, test e output;
- decide se accettare, correggere o dividere il task.

### Chat B

Chat B viene usata per:

- diagnostica indipendente;
- revisione critica di regressioni complesse;
- verifica di ipotesi;
- modifiche architetturali non previste dal piano.

Chat B non decide il commit e non sostituisce Chat A.

### Zed agent

Zed agent:

- esegue soltanto task già definiti;
- modifica solo i file autorizzati;
- non allarga lo scope;
- non sceglie l'architettura;
- non aggiunge dipendenze senza autorizzazione;
- non fa commit;
- mostra diff, test e stato finale.

## Architettura approvata

Pipeline target:

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

### Confini obbligatori

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

- `PageData` è legacy e non è raw canonico.
- PyMuPDF è il backend principale.
- pdfplumber è un analizzatore specializzato per candidati tabella.
- Asset fisico, occorrenza, regione layout e nodo semantico sono entità differenti.
- Un candidato non entra direttamente nella IR.
- Il layout è principalmente page-centric.
- La semantica e la IR devono supportare provenienza multipagina.
- I renderer non devono reinterpretare il PDF.

## Invarianti da non violare

### Sorgente e raw

- La sorgente di un futuro job deve essere immutabile o verificata prima del resume.
- La cattura backend non viene modificata dalle fasi successive.
- I dump completi del backend sono diagnostici opzionali, non il contratto canonico.

### Primitive

- Le primitive normalizzate sono immutabili.
- Non contengono ruoli semantici.
- Non contengono classificazioni definitive come `decorative`, `structural`, `table`, `callout` o `marginalia`.
- Conservano coordinate canoniche e riferimenti alla cattura.

### Layout e candidati

- `LayoutRegion` contiene soltanto dati strutturali.
- Confidence geometrica e confidence semantica devono essere separate.
- Tabelle, marginalia, callout e liste detector-side sono candidati.
- Un candidato tabella non rimuove testo e non produce CSV definitivo prima della resolution.

### Coverage e ownership

- La coverage è obbligatoria per le primitive che possono trasportare contenuto.
- Le support primitive possono essere registrate come `layout_evidence`.
- Una primitiva testuale non può appartenere a più nodi finali salvo duplicazione esplicita.
- Nessuna esclusione può essere silenziosa.

### Semantica e IR

- La continuità multipagina viene inizialmente proposta come relation candidate.
- I nodi non vengono uniti automaticamente in modo aggressivo.
- L'adapter IR 2 → IR 1 è ammesso solo nei casi senza perdita.
- Markdown ed EPUB devono progressivamente diventare IR-first.

### AI

L'AI locale può proporre:

- classificazioni;
- associazioni;
- marker;
- anomalie;
- decisioni di review;
- enrichment.

Non deve:

- riscrivere il contenuto estratto;
- generare codice specifico per un manuale;
- creare target inesistenti;
- cancellare file;
- modificare raw o primitive;
- applicare esclusioni irreversibili senza validazione;
- sostituire il profilo persistente.

## Regole operative di implementazione

Per ogni task:

1. Leggere `State.md` e questo file.
2. Confermare la milestone corrente.
3. Definire un solo obiettivo.
4. Elencare file ammessi e vietati.
5. Non allargare lo scope durante l'esecuzione.
6. Non mescolare riorganizzazione e cambio funzionale.
7. Non introdurre hardcode su manuale, pagina, filename, titolo o parola come soluzione primaria.
8. Non usare `git add .`.
9. Non committare automaticamente.
10. Non committare output, workspace, crop, dump o diagnostica.
11. Aggiungere test sintetici per nuovi contratti o regole.
12. Usare benchmark reali per verificare la generalizzazione quando il comportamento diventa attivo.
13. Mostrare diff, test e `git status --short` finali.

Verifiche minime per un commit di codice:

```bash
ruff check <file coinvolti>
basedpyright <file coinvolti>
python -m unittest <test mirati>
python -m unittest
git diff --check
git status --short
```

Eseguire lo smoke DB quando la modifica può influire su estrazione, IR o renderer.

## Baseline legacy da preservare

Finché la nuova pipeline non è attiva, restano non-regressione:

- callout DB stabilizzati;
- tabelle DB e filtro del testo duplicato;
- classificazione clutter;
- immagini readable;
- reading order DB, incluso `MONETE`/`CIMELIO`;
- dropcap irrisolti senza invenzione;
- IR 1.0 e Markdown correnti;
- comportamento EPUB legacy non modificato salvo milestone dedicata.

## Milestone corrente

La milestone corrente è:

> **Milestone 2 — cattura PyMuPDF shadow**

### Stato della Milestone 1

La Milestone 1 è completata. Sono presenti e approvati:

- `geometry_model.py`;
- `capture_model.py`;
- `primitive_model.py`;
- `tests/test_capture_primitive_models.py`.

I contratti distinguono capture backend, primitive canoniche, risorsa raster e occorrenza, e non sono collegati alla pipeline legacy.

### Obiettivo della Milestone 2

Produrre una `BackendPageCapture` reale tramite PyMuPDF in shadow mode, senza cambiare l'output autorevole.

Primo percorso previsto:

```text
PDF
→ adapter PyMuPDF shadow
→ BackendPageCapture
→ diagnostica o confronto controllato
```

### Scope iniziale autorizzabile

Il primo micro-step della milestone può includere soltanto ciò che Chat A approva esplicitamente fra:

- geometria pagina;
- metadati backend;
- text run raw;
- identità di sorgente, pagina e capture;
- serializzazione o diagnostica shadow controllata;
- test sintetici del nuovo adapter.

Immagini, drawing, link e annotazioni devono essere aggiunti solo in micro-step successivi o se inclusi esplicitamente nel task.

### Vincoli della milestone

- non derivare la capture da `PageData`;
- non usare `TextBlock`, `ImageBlock`, `VectorBlock` o `TableBlock` come raw canonico;
- nessuna modifica al risultato Markdown o EPUB;
- nessuna sostituzione del percorso legacy;
- nessun refactor generale di `extractor.py`;
- nessuna ricostruzione testuale, deduplicazione, classificazione o reading order nella capture;
- nessun ruolo semantico o decisione editoriale;
- nessun region graph, profilo, workspace completo, AI o IR 2;
- nessuna nuova dipendenza senza decisione esplicita;
- ogni output shadow deve essere diagnostico e chiaramente separato dagli output utente;
- lo smoke DB va eseguito solo se il micro-step può influire sulla pipeline legacy.

### Criteri minimi

- adapter indipendente dai modelli legacy elaborati;
- `BackendPageCapture` costruibile da una pagina reale;
- testo raw conservato senza trim, join o normalizzazione;
- coordinate e rotazione dichiarate coerentemente;
- nessuna perdita silenziosa delle osservazioni coperte;
- test mirati verdi;
- Ruff e BasedPyright verdi;
- suite legacy invariata quando pertinente;
- diff limitato ai file autorizzati.

## Migrazione e shadow mode

Modalità transitorie:

```text
legacy
shadow
new
```

- `legacy`: produce il risultato corrente.
- `shadow`: calcola il nuovo dato senza cambiare l'output.
- `new`: usa il nuovo percorso per il comportamento approvato.

Lo shadow mode deve avere criteri di equivalenza e una milestone di uscita.

L'equivalenza non richiede JSON identici, ma almeno:

- stesso contenuto conservato;
- stessi asset readable;
- nessuna nuova perdita;
- nessuna nuova duplicazione;
- ordine osservabile equivalente sui casi stabilizzati;
- callout e tabelle DB preservati;
- differenze spiegabili.

## Attività non autorizzate nella milestone corrente

Non avviare:

- refactor generale di `extractor.py`;
- region graph;
- marginalia detector;
- nuove euristiche per Fabula, Lancer, Kult o Vileborn;
- profili;
- workspace completo;
- job manager completo;
- decision event log;
- IR 2;
- modifica dei renderer;
- GUI;
- AI di calibrazione;
- EPUB IR-first;
- OCR;
- SQLite;
- nuova struttura completa del repository.

## Aggiornamento documenti

Aggiornare:

- `State.md` a fine milestone o cambio di fase;
- `AGENTS.MD` quando cambiano regole permanenti, milestone o pipeline approvata;
- workflow due-chat solo quando cambiano ruoli e modalità operative.
