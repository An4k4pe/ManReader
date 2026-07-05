# ManReader — Stato progetto

## Versione corrente: v0.6 — fase progettuale globale

## 1. Decisione di fase

ManReader entra temporaneamente in una fase di progettazione globale.

La pipeline corrente rimane la baseline funzionante e non deve essere riscritta o smontata finché non esiste un'architettura approvata, un piano di migrazione e una strategia di non regressione.

Durante questa fase:

- non aggiungere nuove euristiche locali salvo regressioni bloccanti;
- non avviare refactor di `extractor.py` senza progetto approvato;
- non preparare commit funzionali;
- usare i manuali campione per definire requisiti, invarianti e casi limite;
- separare chiaramente progettazione, revisione architetturale e implementazione;
- aggiornare questo file quando cambia la fase del progetto.

Il refactor di `extractor.py` è ammesso e probabilmente necessario, ma solo dopo aver deciso i confini della nuova pipeline.

## 2. Obiettivo del prodotto

ManReader converte manuali PDF TTRPG in output semantici leggibili, con priorità a Markdown ed EPUB.

Obiettivi permanenti:

- elaborazione locale;
- core utilizzabile senza servizi cloud;
- conservazione del contenuto originale senza invenzioni;
- output verificabile e correggibile;
- supporto sia a PDF digitali sia, in futuro, a scansioni;
- AI/OCR opzionali e separati dal nucleo deterministico;
- profili dei manuali salvabili, importabili e riutilizzabili;
- revisione visuale gestibile anche da un utente non tecnico.

## 3. Baseline corrente

### 3.1 Pipeline legacy

```text
PDF
→ extractor.py
→ PageData / TextBlock / ImageBlock / VectorBlock / TableBlock
→ ir_builder.py
→ DocumentIR
→ markdown_builder.py
→ Markdown
```

L'EPUB è ancora parzialmente legacy e non è completamente IR-first.

### 3.2 Responsabilità correnti

- `main.py` — CLI e orchestrazione.
- `config.py` — parametri layout.
- `extractor.py` — accesso PDF, estrazione testo/immagini/vector/tabelle, ricostruzione testo, colonne, reading order, filtro ripetizioni, classificazione asset e dropcap.
- `deduplicator.py` — deduplicazione asset.
- `ir_model.py` — modelli della IR corrente.
- `ir_builder.py` — reading flow finale e parte della classificazione semantica.
- `ir_store.py` — persistenza JSON.
- `ir_validate.py` — validazione IR.
- `markdown_builder.py` — rendering Markdown.
- `epub_builder.py` — rendering EPUB legacy/parzialmente IR.
- `describer.py` — AI locale opzionale tramite Ollama.
- `asset_manager.py` — applicazione post-build delle modifiche da `asset_index.csv`.

`extractor.py` svolge troppe responsabilità. Questo è un problema architetturale riconosciuto, non ancora un task di refactor operativo.

## 4. Baseline stabilizzata su DB

Restano validi come non-regressione:

- callout region-first sui casi DB verificati;
- supporto a callout affiancati;
- ordine corretto di `MONETE` e `CIMELIO` dopo il fix cross-gutter;
- tabelle preservate nel reading flow e testo tabellare duplicato rimosso;
- classificazione extractor-side `decorative` e `structural`;
- forte riduzione del clutter Markdown;
- immagini readable preservate;
- vector di layout e tabelle filtrati quando riconosciuti;
- dropcap grafici preservati come crop PNG, `role="dropcap"`, `status="unresolved"` e placeholder Markdown;
- nessuna lettera inventata;
- suite completa e smoke DB verdi nell'ultima verifica nota.

Prima di iniziare una nuova fase operativa verificare comunque:

```bash
git status --short
python -m unittest
```

## 5. Esito del generalization audit

Il confronto con Fabula, Lancer, Kult e Vileborn mostra che la pipeline corrente generalizza male fuori dai layout simili a DB.

Problemi osservati:

- marginalia e bande laterali entrano nel reading flow;
- liste puntate vengono appiattite;
- procedure numerate grafiche perdono struttura e ordine;
- tabelle reali non vengono riconosciute;
- parti di callout vengono classificate come tabelle;
- box grandi, compositi o drawing-based non vengono ricostruiti;
- una regione semantica non coincide necessariamente con un singolo raster/vector;
- pagine molto grafiche richiedono talvolta una politica editoriale, non una sola classificazione automatica;
- lo stesso manuale contiene più archetipi di pagina;
- alcune decisioni, come escludere un indice laterale o preservare una scheda come immagine, dipendono dall'utente.

Conclusione:

> Non è realistico affidare tutta la semantica a una singola raccolta di soglie universali.

È invece realistico rendere universali:

- osservazione delle primitive;
- geometria;
- relazioni;
- statistiche del documento;
- clustering delle pagine;
- rilevamento di candidati e ambiguità.

La semantica finale deve poter combinare:

```text
evidenze deterministiche
+ profilo del documento
+ archetipi di pagina
+ politica editoriale
+ revisione utente/AI opzionale
```

## 6. Direzione architetturale condivisa

Pipeline da progettare:

```text
PDF
→ primitive raw
→ workspace persistente
→ firme e archetipi di pagina
→ profilo del documento
→ regioni e relazioni di layout
→ classificazione semantica
→ IR
→ renderer Markdown/EPUB
```

Principi:

1. Le primitive raw devono essere disponibili prima delle decisioni legacy.
2. Asset fisico, regione di layout e blocco semantico sono entità diverse.
3. Tabelle detector-side sono candidati, non verità semantiche immediate.
4. Reading order deve operare su regioni o gruppi logici, non solo su blocchi testuali grezzi.
5. Il core deve essere headless.
6. CLI e GUI devono essere client dello stesso core.
7. La GUI serve per revisione visuale, non per contenere logica di estrazione.
8. Il sistema deve poter funzionare senza AI.
9. L'AI locale deve proporre decisioni strutturate, non generare codice specifico per manuale.
10. Ogni decisione deve essere tracciabile e riproducibile.

## 7. Workspace persistente

Serve un'area di lavoro separata dall'output finale.

Principio:

```text
workspace = raw, candidati, preview, diagnostica, decisioni, profilo in bozza
output    = solo elementi finalizzati
```

Struttura indicativa da progettare:

```text
workspace/<job-id>/
  manifest.json
  raw/
  candidates/
  previews/
  overlays/
  diagnostics/
  decisions/
  profile_draft/
  logs/
```

Requisiti:

- recuperabile dopo crash o riavvio;
- eliminabile esplicitamente;
- nessun candidato deve finire automaticamente nell'output definitivo;
- manifest con stato del job, versione motore, fingerprint sorgente, profilo, candidati, decisioni e warning;
- nomi e JSON semplici, leggibili anche da strumenti esterni e AI locali.

Il nome definitivo della directory e lo schema non sono ancora approvati.

## 8. Profili dei manuali

La calibrazione non deve essere ripetuta a ogni run.

Un profilo dovrà poter essere:

- salvato;
- importato ed esportato;
- versionato;
- validato;
- riutilizzato;
- duplicato per edizioni differenti;
- esteso con override;
- associato tramite fingerprint senza dipendere dal path locale.

Il profilo deve distinguere:

1. convenzioni grafiche del documento;
2. archetipi di pagina;
3. mapping di glifi e marker;
4. politiche editoriali;
5. override dell'edizione;
6. override temporanei del job.

Non deve contenere codice Python generato o hardcode testuali come regola primaria.

## 9. Interazione utente e GUI

La calibrazione visuale difficilmente rimane gestibile solo da CLI.

Requisiti minimi della futura GUI:

- importazione PDF e profilo;
- scansione e stato del job;
- raggruppamento delle pagine per archetipo;
- scelta di pagine rappresentative;
- render della pagina con overlay;
- elenco regioni e candidati;
- azioni: conserva come testo, struttura, conserva come immagine, escludi, unisci, separa, incerto;
- revisione e salvataggio del profilo;
- coda degli outlier;
- avvio dell'elaborazione finale.

Non è ancora scelto il framework GUI.

La CLI deve restare pienamente utilizzabile per:

- test;
- diagnostica;
- batch;
- esecuzione con profilo già pronto;
- import/export profili;
- automazione.

## 10. AI locale

L'AI locale è opzionale.

Può:

- proporre ruolo di regioni;
- suggerire archetipi;
- segnalare anomalie;
- proporre mapping di glifi;
- assistere la calibrazione;
- lavorare sui soli outlier.

Non può:

- riscrivere direttamente il contenuto estratto;
- generare codice specifico per un manuale;
- cancellare file;
- applicare modifiche irreversibili senza validazione;
- sostituire il profilo persistente.

Input e output devono usare contratti JSON validabili e riferimenti stabili a job, pagina, regione e candidato.

## 11. Benchmark manuali

Campione corrente:

- DB — baseline stabilizzata;
- Fabula — box grandi/drawing-based, marginalia, liste, procedure, tabelle e falsi positivi;
- Lancer — layout complessi, simboli speciali, tabelle, callout, pagine molto grafiche;
- Kult — colonne, rimandi laterali, box e contenuto potenzialmente da escludere;
- Vileborn — prosa, callout, procedure, tabelle e stat block.

L'utente seleziona e annota semanticamente le pagine, senza misurare pixel o bbox.

Annotazioni manuali sufficienti:

- fenomeni presenti;
- cosa conservare come testo;
- cosa convertire in struttura;
- cosa preservare come immagine;
- cosa escludere;
- cosa resta incerto;
- note editoriali.

Primitive, bbox, font, drawing e candidate table saranno estratti automaticamente in una fase successiva.

## 12. Attività sospese

Non riaprire durante la progettazione globale salvo regressione bloccante:

- fix specifico di `p29_vec2.svg`;
- nuove soglie globali per callout/vector;
- canonicalizzazione asset;
- pulizia fisica delle cartelle output;
- qualità CSV;
- heading;
- crop dropcap;
- EPUB;
- nuove euristiche isolate per Fabula/Lancer/Kult/Vileborn;
- scelta del framework GUI;
- implementazione AI di calibrazione.

## 13. Deliverable della fase progettuale

Prima del primo refactor devono essere approvati:

1. visione del sistema e non-obiettivi;
2. pipeline completa e confini dei moduli;
3. modello primitive/regioni/semantica/IR;
4. ciclo di vita del job;
5. schema del workspace e del manifest;
6. schema e versionamento dei profili;
7. archetipi di pagina e clustering;
8. workflow utente;
9. requisiti GUI e CLI;
10. contratti AI locali;
11. strategia di migrazione dalla pipeline legacy;
12. piano di test e benchmark;
13. criteri di compatibilità e rollback;
14. ordine dei refactor;
15. decision record delle scelte principali.

## 14. Criteri per uscire dalla fase progettuale

La progettazione è conclusa quando:

- Chat A ha prodotto un documento architetturale unico;
- Chat B ha eseguito una revisione critica;
- le decisioni bloccanti sono risolte o esplicitamente rinviate;
- esiste una pipeline target approvata;
- esiste un piano di migrazione incrementale;
- è chiaro cosa resta legacy durante la transizione;
- il primo commit ha uno scope strutturale preciso;
- sono definiti test di non regressione DB e fixture di generalizzazione;
- `State.md`, `AGENTS.MD` e il workflow due-chat sono coerenti con la nuova fase.

## 15. Workflow corrente

Durante la progettazione:

```text
Chat A Architettura
→ proposta globale
→ Chat B Revisione
→ integrazione in Chat A
→ documento approvato
→ aggiornamento State/AGENTS
→ piano di migrazione
→ primo commit
```

Zed agent non riceve task progettuali.

Durante l'implementazione successiva:

- commit piccoli e verificabili;
- file ammessi/vietati;
- diff e test obbligatori;
- nessun commit automatico;
- output generati non committati;
- refactor ampi solo se previsti dal piano approvato e scomposti in fasi.
