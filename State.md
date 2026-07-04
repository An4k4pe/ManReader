# ManReader — Stato progetto

## Versione corrente: v0.5

## 1. Obiettivo e principi

ManReader converte manuali PDF per giochi di ruolo in output semantici leggibili, con priorità a Markdown ed EPUB.

Principi correnti:

- pipeline locale e deterministica;
- AI/OCR opzionali solo come enrichment o revisione;
- correzioni il più possibile upstream;
- builder Markdown basato sulla IR, senza reinterpretare direttamente il PDF;
- commit piccoli, verificabili e limitati a un problema reale;
- niente hardcode su manuale, pagina, titolo, filename o parola;
- asset decorativi e strutturali preservabili come metadata, ma esclusi dal reading flow;
- tabelle reali preservate come asset leggibili;
- nessuna ricostruzione automatica di contenuto non presente nel text layer.

## 2. Architettura corrente

### 2.1 Pipeline principale

```text
PDF
→ extractor.py
→ PageData / text_blocks / images / vectors / tables
→ ir_builder.py
→ DocumentIR
→ markdown_builder.py
→ Markdown
```

L’EPUB è ancora parzialmente su un percorso legacy e non è completamente allineato alla IR.

### 2.2 Moduli

- `main.py` — CLI e orchestrazione.
- `config.py` — parametri layout.
- `extractor.py` — estrazione testo, immagini, vettoriali e tabelle; TOC; colonne; filtro ripetizioni; classificazione asset; rilevamento dropcap grafici.
- `deduplicator.py` — deduplicazione asset grafici ripetuti.
- `describer.py` — descrizioni AI locali tramite Ollama.
- `ir_model.py` — dataclass IR: `DocumentIR`, `PageIR`, `BlockIR`, `AssetIR`, review/override/entity model.
- `ir_store.py` — persistenza JSON della IR.
- `ir_validate.py` — validazione leggera della IR.
- `ir_builder.py` — costruzione del reading flow e classificazione semantica.
- `markdown_builder.py` — rendering Markdown dalla IR.
- `epub_builder.py` — generazione EPUB; non ancora pienamente IR-first.
- `asset_manager.py` — applicazione post-build di rename/edit da `asset_index.csv`.
- `requirements.txt` — dipendenze principali.

## 3. Funzionalità implementate

### 3.1 Estrazione e layout

- Estrazione testo con TOC embedded come fonte principale per i capitoli.
- Euristiche font come fallback.
- Rilevamento colonne per pagina.
- Ordinamento prudente per layout a colonne e zone locali.
- Filtro statistico di header/footer/watermark ripetuti.
- Estrazione immagini raster, vettoriali SVG e tabelle CSV.
- Rebuild prudente dei blocchi PyMuPDF: i block hint fusi o cross-column non devono sostituire blocchi `dict` separabili geometricamente.
- Split prudente di blocchi raw con cluster orizzontali distinti.
- Deduplicazione di `TextBlock` sovrapposti o quasi identici.
- Merge testuale prudente per frammenti adiacenti.

### 3.2 IR e builder

- Dataclass IR disponibili:
  - `DocumentIR`
  - `PageIR`
  - `BlockIR`
  - `AssetIR`
  - `AIProposal`
  - `ReviewItem`
  - `HumanOverride`
  - `Issue`
  - `EntityIR`
- IR salvata sempre in `output/<book>/ir/document_ir.json`.
- Validazione tramite `ir_validate.py`.
- Markdown generato dalla IR.
- CLI `--format epub|markdown|both`.
- Default ancora `epub`.
- Asset con `is_background=True` o `is_duplicate=True` esclusi dal reading flow.
- Asset classificati `decorative` esclusi dal reading flow.
- Asset classificati `structural` disponibili durante il riconoscimento dei callout e rimossi dal flusso finale.
- Tabelle preservate nel reading flow come CSV.
- Asset con ruolo semantico `dropcap` hanno precedenza sul filtro clutter.

## 4. Milestone stabilizzate

### 4.1 Callout e box testuali

Il riconoscimento prudente dei callout è stabilizzato sui casi DB pagine 8–30.

Principi:

- approccio region-first;
- title e body devono appartenere geometricamente alla stessa regione grafica;
- supporto a body `role="bullet_list"`;
- supporto a body composto da più blocchi;
- asset non testuali fuori regione possono essere ignorati durante la ricerca del body;
- supporto a callout affiancati;
- impedito il doppio consumo dello stesso body;
- rendering Markdown come callout Obsidian `> [!INFO]`;
- evitare ulteriori scan permissivi senza una regressione concreta.

Casi verificati:

- `TU E GLI ALTRI`
- `ABBREVIAZIONI`
- `CREARE IL TUO PERSONAGGIO`
- `CAPACITÀ: ADATTABILE`
- `CAPACITÀ: RANCOROSO`
- `CAPACITÀ: DIFFICILE DA PRENDERE`
- `CAPACITÀ: PACE INTERIORE`
- `CAPACITÀ: SCONTROSO`
- `CAPACITÀ: PALMIPEDE`
- `CAPACITÀ: ISTINTI DA CACCIATORE`
- `ALTRI METODI`
- `MAGIA` pagina 22
- `MAGIA` pagina 28
- `DEBOLEZZA`
- `CAPACITÀ ALTERNATIVE`
- `CIMELIO`
- `MONETE`

Follow-up separato:

- distinguere colore, stile e tipo dei box;
- aggiungere eventuali metadata visuali come `callout_color`, `callout_kind`, `region_bbox`, `visual_classification`;
- valutare AI locale opzionale su crop del callout, non sull’intera pagina.

### 4.2 Tabelle nel reading flow

Implementato il filtro IR per evitare duplicazione del testo tabellare:

- i blocchi testo contenuti o fortemente sovrapposti alla bbox di una tabella riconosciuta vengono esclusi dal flusso leggibile;
- il CSV resta l’asset leggibile;
- note esterne alla bbox della tabella vengono preservate;
- la regola è geometrica, non testuale.

Caso verificato:

- DB pagina 26, `EFFETTI DELL’ETÀ`: rimosse le righe duplicate dal Markdown, preservata la nota sotto tabella e preservato `p26_tbl1.csv`.

### 4.3 Pulizia clutter asset nel Markdown

Implementata una classificazione geometrica conservativa lato extractor per image/vector.

Classificazioni usate:

- `decorative`
- `structural`
- `table`
- `None` per readable o incerti

Comportamento:

- piccoli glifi marginali, decorazioni header/footer, titolo e corner ad alta confidenza → `decorative`;
- fondi box/callout, table-background e vector associati a tabelle → `structural`;
- immagini grandi, centrali, illustrative o ambigue → `None`;
- tabelle CSV sempre preservate;
- nessuna whitelist di file, pagine, titoli o parole;
- asset esportati comunque nelle cartelle `extracted/`.

Verifica DB pagine 8–15:

- `[Immagine:]`: 29 → 7
- `[Vettoriale:]`: 11 → 0
- `[Tabella:]`: 10 → 10
- immagini readable note preservate;
- callout preservati;
- asset fisici ancora esportati.

Verifica DB pagine 8–30:

- Markdown pulito e callout ancora leggibili;
- asset residui principalmente illustrazioni e tabelle reali;
- un vector residuo su pagina 29 da diagnosticare separatamente.

### 4.4 Capolettere grafici irrisolti

Implementato supporto per capolettere grafici non presenti nel text layer.

Principi:

- nessuna lettera viene inventata;
- nessuna correzione automatica del testo;
- nessun OCR o AI nella fase deterministica;
- la geometria è il segnale dominante;
- apostrofo, minuscola o punteggiatura iniziale sono segnali contestuali validi;
- i candidati vengono ricavati da raw image rect e raw drawing rect PyMuPDF;
- candidati sovrapposti associati alla stessa prima riga vengono deduplicati;
- viene scelto il candidato meglio allineato all’inizio della prima riga;
- il capolettera viene esportato come page crop PNG;
- `ImageBlock.role = "dropcap"`;
- `status = "unresolved"`;
- la IR preserva ruolo, stato, bbox, pagina e path;
- il Markdown emette un commento placeholder;
- il testo raw resta invariato.

Forma Markdown:

```markdown
<!-- dropcap: unresolved; image: ...; page: ...; bbox: [...]; alt: "Capolettera decorato non risolto" -->
```

Verifica DB pagine 8–33:

- `p0011_dropcap_0001.png`
- `p0033_dropcap_0001.png`
- un solo placeholder per capolettera reale;
- nessun duplicato image/drawing sulla pagina 11;
- IR valida;
- testo pagina 11 resta `’avventuriero...`;
- crop ancora migliorabile e può includere una piccola porzione di testo.

Follow-up separato:

- restringere la bbox del crop senza rischiare di tagliare il glifo;
- risolvere lettera e alt-text definitivo tramite AI/OCR/manual override;
- non bloccare la pipeline attuale per la qualità del crop.

## 5. Problemi noti

### 5.1 Extractor e segmentazione testo

- Restano frammenti testuali separati o ricostruiti in modo imperfetto.
- Esempi storici:
  - `resistent e`
  - `gl i`
  - `deci mata`
  - `p urtroppo`
  - `suoam ico`
- Prima di ogni fix: confrontare raw PyMuPDF `dict`, `blocks`, extractor, IR e Markdown.
- Il rebuild da `get_text("blocks")` può collassare più span e perdere enfasi inline.
- Follow-up: preservare enfasi inline durante la ricostruzione dei `TextBlock`.
- Evitare merge generici senza evidenza geometrica.

### 5.2 Heading e struttura

- Titoli con lettere spaziate o decorative, esempio `L’A RRIVO DELL ’O RDA`.
- Heading incollati, esempio `MECCANICHE ECOMPLICAZIONI`.
- Gerarchia heading TOC/font ancora da verificare:
  - capitoli principali talvolta `##` invece di `#`;
  - sottosezioni talvolta heading errato o testo normale.
- Possibili residui di indice/manual TOC e footer su run molto brevi.

### 5.3 Tabelle

- Qualità CSV ancora imperfetta in alcuni casi.
- Caso noto: DB pagina 26, `p26_tbl1.csv`, riga `1–3` con contenuto da verificare.
- Possibili tabelle frammentate o parzialmente riconosciute.
- Caso storico: DB pagina 8, possibili frammenti `p8_tbl2.csv`, `p8_tbl3.csv`, `p8_tbl4.csv`.
- Distinguere meglio body text, label, celle e testo table-like quando il riconoscimento è parziale.

### 5.4 Asset, output e deduplicazione

Il reading flow Markdown è molto più pulito, ma l’output fisico resta grezzo.

Problemi aperti:

- molti asset decorativi o strutturali restano in `extracted/images` e `extracted/vectors`;
- alcuni asset sono utili solo come regioni o metadata;
- manca una distinzione chiara tra:
  - asset esportato;
  - asset usato nel Markdown;
  - asset usato solo dalla IR;
  - asset decorativo;
  - asset strutturale;
  - asset semantico irrisolto;
- canonicalizzazione asset/occurrences/pages ancora da progettare;
- differenza tra conteggio asset logici e file fisici da diagnosticare;
- possibili asset non referenziati dal Markdown o dalla IR;
- `p29_vec2.svg` è un residuo da diagnosticare separatamente;
- il crop dropcap può includere una piccola porzione di testo.

Non eliminare asset structural necessari a callout, regioni o future analisi.

### 5.5 AI enrichment

- L’AI deve restare separata dalla fase estrattiva.
- Non deve riscrivere il contenuto deterministico.
- Deve produrre enrichment, proposta o review.
- Casi futuri:
  - risoluzione dropcap;
  - alt-text immagini;
  - descrizione diagrammi/mappe;
  - classificazione visuale callout;
  - supporto a human override.

### 5.6 EPUB

- Il builder EPUB non è ancora completamente IR-first.
- Non introdurre fix EPUB dentro commit Markdown/extractor.
- Allineamento EPUB da trattare come milestone separata.

## 6. Prossime milestone

### 6.1 Priorità immediata — diagnostica output asset

Prima di refactor o cancellazioni:

1. contare asset fisici per tipo;
2. contare asset logici in IR;
3. contare asset usati nel Markdown;
4. distinguere `decorative`, `structural`, `table`, `dropcap`, readable e unknown;
5. individuare duplicati per hash;
6. individuare asset non referenziati;
7. verificare differenza tra conteggi log e file fisici;
8. proporre un modello minimo per asset index e output.

Obiettivo:

```text
preservare ciò che serve alla ricostruzione
mostrare all’utente solo ciò che è utile
evitare duplicazioni fisiche non necessarie
```

### 6.2 Priorità successiva — modello asset/output

Valutare campi come:

- `role`
- `classification`
- `status`
- `used_in_markdown`
- `used_in_ir`
- `canonical_sha`
- `occurrence_count`
- `source_page`
- `source_bbox`
- `alt_text`
- `description`

Non spostare o cancellare file prima di aver definito il modello.

### 6.3 Priorità media

- migliorare qualità CSV/table reconstruction;
- rivedere heading hierarchy;
- correggere frammentazione testo con casi reali e test mirati;
- diagnosticare `p29_vec2.svg`;
- rifinire crop dropcap;
- progettare metadata visuali dei callout.

### 6.4 Priorità futura — refactor/comment pass

- eliminare ridondanze senza cambiare comportamento;
- commentare in inglese le euristiche non ovvie;
- mantenere test invariati prima/dopo;
- procedere per area:
  - extractor;
  - IR;
  - Markdown;
  - tests;
- documentare soprattutto:
  - PyMuPDF `dict` vs `blocks`;
  - colonne e zone;
  - callout region-first;
  - classificazione asset;
  - dedup overlap;
  - dropcap raw graphics;
  - paragraphing across columns.

## 7. Asset Index

Registro centrale:

```text
output/<book>/extracted/asset_index.csv
```

Campi correnti:

```text
sha, nome_file, tipo, pagina, titolo, descrizione, modificato
```

Comportamento:

- SHA MD5 come chiave stabile;
- `modificato=si` protegge entry editate manualmente;
- merge su rebuild:
  - entry protette intoccabili;
  - nuove entry aggiunte;
  - entry non protette aggiornate;
- il builder EPUB usa `titolo` per il testo inline.

Follow-up:

- aggiungere metadata coerenti con classificazione, ruolo, stato e uso effettivo;
- progettare canonical asset e occurrences senza rompere rename/edit manuali.

## 8. asset_manager.py

Uso:

```bash
python asset_manager.py output/NomePDF/
```

Flusso:

1. legge `asset_index.csv`;
2. trova entry con `modificato=si`;
3. rinomina i file fisici;
4. aggiorna path e titolo negli XHTML EPUB;
5. resetta `modificato=no`;
6. salva il CSV aggiornato.

## 9. AI locale

### 9.1 Architettura

Pattern strategy:

```text
BaseDescriber (ABC)
→ OllamaDescriber
```

Factory:

```text
create_describer(backend, ...)
```

Backend Gemini rimosso.

### 9.2 Backend vision

- Ollama REST `/api/generate`;
- immagini inviate come base64;
- modello consigliato corrente: `gemma4:12b`;
- AI solo opzionale e locale.

## 10. CLI e ambiente

### 10.1 Parametri CLI principali

- `--format epub|markdown|both`
- `--ollama-model NOME`
- `--ollama-host URL`
- `--columns auto|1|2`
- `--column-gap`
- `--column-split`
- `--no-dedup`
- `--auto-background`
- `--header-zone`
- `--repeat-threshold`
- `--pages 1-20`
- `--no-ai`

### 10.2 Ambiente sviluppo

- CachyOS Linux;
- Fish shell;
- Python virtualenv;
- PyMuPDF;
- pdfplumber;
- ebooklib;
- Pillow;
- requests;
- Ruff;
- BasedPyright;
- unittest.

## 11. Verifiche recenti

- Suite completa dopo dropcap: 241 test, tutti verdi.
- DB smoke pagine 8–30: verde.
- DB pagine 8–33:
  - IR valida;
  - Markdown generato;
  - due dropcap reali preservati;
  - nessun duplicato pagina 11;
  - callout noti ancora leggibili;
  - tabelle preservate;
  - clutter asset fortemente ridotto.
- `test.pdf` completo:
  - una tabella vera;
  - zero vettoriali.
- EPUB:
  - rimossa pagina TOC manuale duplicata;
  - navigazione EPUB standard preservata.

## 12. Regole operative

- Leggere sempre `State.md` e `AGENTS.MD` prima di proporre modifiche.
- Non fare commit automatici.
- Non usare `git add .`.
- Un commit deve affrontare un solo problema reale.
- Test sintetici obbligatori per ogni nuova euristica.
- Verifica manuale DB obbligatoria quando il fix nasce da DB.
- Non committare `output/`, file diagnostici o `tools_tmp/`.
- Non modificare `State.md` insieme a codice funzionale, salvo decisione esplicita.
- Prima del commit:
  - `ruff`;
  - `basedpyright`;
  - test mirati;
  - suite completa;
  - diff;
  - `git status --short`.
