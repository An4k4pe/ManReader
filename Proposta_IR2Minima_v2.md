# Proposta — IR 2 minima a uno stadio, bersaglio Markdown (v2)

Chat A, Modalità P. 17 agosto 2026. Fuori dal repo (prassi di Milestone 33/34/35).
Base: `3a2238d`, suite 1263 verde, sei producer wired.

Sostituisce la v1, revisionata dal giro metodologico di Chat B. Changelog in §12.

---

## 1. Cosa si chiede di approvare

Aprire lo stadio **`DocumentIR 2`** con la decisione architetturale dedicata che
`AGENTS.MD` richiede.

`IR 2` è nella lista «Attività non autorizzate **senza decisione architetturale
dedicata**»: un cancello, non un divieto di merito. Due precedenti di come si
passa: Milestone 34 per `resolution` (documento di Modalità P **più due giri
Chat B**) e Milestone 26 per `clustering`. Il criterio non è soddisfatto dallo
scrivere questa proposta — sarebbe un criterio che non può fallire — ma dal
completamento del secondo giro. Rilievo A6 di Chat B, accolto.

Nel merito `IR 2` non è un'alternativa: è il bersaglio dell'architettura
approvata (`AGENTS.MD` §Architettura approvata).

---

## 2. Il difetto osservato, con la pagina e il render

**La v1 chiedeva un'esenzione dalla regola «una pagina che esce sbagliata»
sostenendo che non esistesse nessuna pagina da guardare. Era falso**, e il rilievo
B4 di Chat B lo ha smontato: un Markdown esiste, prodotto dalla pipeline legacy.
Eseguito e guardato accanto al render.

**DB p.99 posizionale (stampata 97, verificata a render.)** Scheda del mostro
SCHELETRO. Comando: `main.py DB.pdf --pages 99 --format markdown --no-ai`.

Sei difetti nel Markdown legacy, confrontati con la pagina:

1. Il watermark `Andrea Bruna - 550401` è **incollato dentro un paragrafo di
   prosa** («…550401 gallerie, smuovere il terreno…»).
2. La prosa della colonna sinistra e la sua continuazione sono **separate da due
   asset e da un box**: l'ordine di lettura interlaccia le colonne.
3. Tre stat block **identici** escono come due `## titolo` e un `> [!INFO]`
   callout. Stessa struttura, tre rese diverse.
4. Le righe etichetta-valore sono **fuse in una riga sola**, tutta in grassetto.
5. `CAPITOLO 7 – BESTIARIO`, l'intestazione corrente, è promossa a **titolo H2**.
6. La nota d'asset è il **nome del file** (`[Immagine: p99_img12.jpeg]`), e cita
   3 asset su 6 immagini e 2 vettoriali estratti.

I difetti 3, 4 e 5 sono **esattamente** la ri-derivazione geometrica documentata
al §4. Non erano previsti: sono stati osservati.

Sul difetto 6 va detto ciò che la v1 aveva frainteso: il nome di file al posto del
titolo dipende da `--no-ai` (nel legacy l'AI nomina le immagini in un secondo
passaggio), e diverse delle immagini non citate sono **glifi ricorrenti e sfondi**,
che non vanno nominati ma **rimossi** — vedi §6.

**Confronto con la pipeline nuova sulla stessa pagina.** Vince già su tre punti:
ordine di lettura corretto, righe dello stat block separate, watermark in fondo
dov'è davvero. Perde su due: nessun titolo (`SCHELETRO` esce come testo semplice)
e note d'asset opache.

### Il difetto strutturale che ci sta sotto

- `PageAnalysis` ha serializzazione andata e ritorno (`page_analysis_serialization.py`,
  `page_analysis_store.py`).
- `BackendPageCapture` e `NormalizedPrimitivePage` **non ne hanno alcuna**.
- `RegionCandidate` (`page_analysis_model.py:107-118`) porta `bbox`,
  `proposed_structural_kind` e `primitive_ids` **opachi**. Il testo vive in
  `TextPrimitive.text`, cioè nell'oggetto che non persiste.
- `ResolvedSemanticDocument` non compare in nessun file.

> **La pipeline nuova ha il lato struttura e non ha il lato contenuto.**

---

## 3. Quanti tipi di nodo servono perché DB p.99 esca corretta

Determinato guardando la pagina ingrandita, non dedotto.

| serve | stato | perché |
| --- | --- | --- |
| `text.paragraph` | **c'è** | sulla prosa funziona già |
| `text.heading` | **manca** | quattro titoli su questa pagina (`SCHELETRO`, `GUERRIERO`, `ARCIERE`, `CAMPIONE`); senza, un bestiario è un muro |
| `asset.note` | **c'è, da sistemare** | su questa pagina serve per **una** cosa: l'illustrazione |
| `text.labelled_entry` | **manca** | vedi sotto |

Più **due meccanismi che non sono tipi di nodo**:

- **rimozione dell'arredo ricorrente** — fregi, cornici, separatori, sfondo,
  intestazione corrente, numero di pagina, watermark (§6);
- **ricongiunzione della sillabazione** — `dimez-/zati`, `riani-/mati`.
  `epub_builder.py` ha già `_dehyphenate`; il Markdown no. È resa, non struttura.

**Perché `text.labelled_entry` non è opzionale.** Nel box *Non-Mostri* (tre voci a
rientro sospeso: `Non-Mostri:`, `Resistenza:`, `Immunità:`) l'uscita attuale
spezza «gli scheletri **non**» da «**contano** come mostri» e incolla la coda
della prima voce all'inizio della seconda. Una frase tagliata a metà non è «poco
marcata», è sbagliata. Le righe del pannello statistiche hanno la stessa forma.

Per `text.heading` la forma del criterio esiste già ed è **page-local**: il corpo
stimato dalla moda delle `font_size` della pagina, l'unico criterio sopravvissuto
al lavoro esplorativo dopo Milestone 35. Non è una soglia fissa, ed è coerente con
la regola «le soglie geometriche si desumono dal documento». **Questa proposta non
lo progetta**: dichiara che il tipo di nodo serve e che il criterio ha una forma
con precedente.

---

## 4. Il fatto che ha cambiato il piano, ora con l'anello mancante

L'idea ovvia era: adapter **IR 2 → IR 1** e riuso di `markdown_builder.py`
invariato — anche l'unica direzione di adapter che `AGENTS.MD` §Semantica e IR
contempla.

**Non regge**, e il rilievo B7 di Chat B chiedeva l'anello che la v1 non mostrava.
Eccolo:

- `markdown_builder.py:94-107` — `_should_start_new_paragraph` decide il confine
  di paragrafo da `vertical_gap >= font_size * 1.2` e da una transizione di
  colonna geometrica.
- `markdown_builder.py:179-195` — `_is_heading_text` decide i titoli da maiuscolo
  ≤ 40 caratteri, da `avg_font_size >= 14.0`, e da `startswith("Scena ")`.
- **L'anello**: nel ramo di default `build_markdown` fa
  `current_paragraph = _join_text_fragments(current_paragraph, text)` e spezza
  **solo** se `_should_start_new_paragraph` è vero. Due paragrafi IR 2 adiacenti
  verrebbero quindi **fusi** salvo che la geometria dica altrimenti.

Cioè il renderer legacy ri-deriva dalla geometria ciò che IR 2 gli porta già
deciso dalla sorgente, e rimetterebbe il difetto che
`Criterio_ParagrafoDaBlocco_v1.md` ha tolto. I difetti 3, 4 e 5 del §2 sono la
prova osservata.

**Conseguenza**: emettitore Markdown **IR2-first nuovo**, renderer legacy
**intoccati**. Non è «modifica dei renderer»: è un modulo nuovo accanto, ed è la
direzione che `AGENTS.MD` chiede.

---

## 5. Il modello

```
DocumentIR2
    schema_version: str
    provenance: IR2Provenance
    pages: tuple[PageIR2, ...]

PageIR2
    page_id: str
    nodes: tuple[NodeIR2, ...]     # l'ordine della tupla E' l'ordine di lettura

NodeIR2
    node_id: str                   # STABILE fra rigenerazioni -- vedi sotto
    kind: str                      # pattern aperto
    text: str | None
    asset: AssetRefIR2 | None
    primitive_ids: tuple[str, ...]
    page_ids: tuple[str, ...]      # >1 = provenienza multipagina
    candidate_ids: tuple[str, ...]
    resolution: str                # "accepted" | "unresolved" | "no_candidate"
```

**`kind` è un pattern aperto**, stessa disciplina di `_STRUCTURAL_KIND_PATTERN`
(`page_analysis_model.py:32`): aggiungere `text.heading` o `text.labelled_entry`
non tocca il modello. È la proprietà che rende sostenibile «cresce di un tipo alla
volta».

**`page_ids` è una tupla dal primo giorno**: `AGENTS.MD` §Semantica e IR richiede
provenienza multipagina, e aggiungerla dopo cambierebbe il tipo.

**L'ordine dei nodi È l'ordine di lettura.** `page_analysis_model.py` nega
esplicitamente che l'ordine dei candidati lo sia; in IR 2 diventa contratto, ed è
la prima volta che il progetto lo dichiara. Va scritto nel modello.

### 5.1 Persistenza, e il requisito che ne discende

**IR 2 v0 persiste.** Decisione dell'utente, con una ragione che aggiunge un
vincolo: IR 2 è il posto dove atterrano l'arricchimento dell'AI e le correzioni
umane, e da lì si rigenera il Markdown.

`AGENTS.MD` §AI vieta all'AI di riscrivere il contenuto estratto e di modificare
raw o primitive. Quindi le correzioni **non riscrivono il nodo**: sono uno strato
separato che lo prende di mira. **IR 1 ha già quella forma** e va riusata come
precedente, non reinventata: `AIProposal(target_id, fields, confidence, backend,
model, status, reason)`, `HumanOverride(target_id, fields, updated_at, source)`,
`ReviewItem`, `Issue` — con la docstring che dice `kept separate from extracted
source data`.

**Il vincolo**: se una correzione punta a un nodo via `target_id`, allora
`node_id` **deve restare lo stesso fra due rigenerazioni**, altrimenti rieseguire
la pipeline orfana ogni correzione. Quindi `node_id` non può essere un contatore:
va derivato dalla sorgente, dove l'identità già esiste
(`source_observation_id`, `text:b{block}:l{line}:s{span}`).

**Limite dichiarato**: è stabile **modulo la capture**. Esiste già un caso a
verbale in cui la capture degenera (Kul p.233 posizionale, il livello `dict` di
PyMuPDF restituisce span spazzatura). L'identità è stabile finché lo è la
cattura, e va scritto.

---

## 6. L'arredo ricorrente: rimosso, non annotato

Posizione dell'utente, messa agli atti perché **ribalta il §7 della v1**: sfondi e
glifi ricorrenti «creano solo ridondanza di segnali senza apportare nulla; lo
scopo è leggere il manuale, non vedere come è costituito, per quello c'è il PDF».

La v1 proponeva la regola «un candidato senza concorrenti è accettato». Quella
regola promuoverebbe a nodo ogni fregio, ogni cornice e ogni sfondo — l'opposto
di ciò che serve, e il failure mode C4 che Chat B aveva già trovato per altra via
(75 note dentro una tabella non sono «note brevi»).

**Il meccanismo esiste già ed è un conteggio, non una soglia sulla forma**: la
ricorrenza di `content_digest` sul documento, rinviata da Milestone 23 e mai
aperta. Un fondo che compare su 300 pagine è arredo **per ricorrenza**. Questo
evita il discriminatore arredamento/contenuto che il lavoro dopo Milestone 35 ha
cercato in otto modi e non ha trovato.

**Non è nel perimetro di questa proposta** (è document-level, e questo passo è
page-level), ma va dichiarato come la precondizione che è: finché non esiste,
`asset.note` su una pagina come DB p.99 produce rumore.

---

## 7. Perimetro

**Moduli nuovi, tre** (non quattro: il §7 della v1 è caduto, vedi §12):

1. il modello IR 2 più la sua serializzazione andata e ritorno;
2. il costruttore da (primitive + `PageAnalysis` + esiti di Resolution);
3. l'emettitore Markdown IR2-first.

**Resolution non si tocca.** Chat B (B2) ha mostrato che il §5 e il §7 della v1 si
contraddicevano: se un nodo esiste anche per i candidati non accettati — e il §5
lo richiede citando «Nessuna esclusione può essere silenziosa» — allora la regola
nuova non fa esistere nulla, cambia il valore di un campo stringa. Il nodo porta
`resolution` con l'esito attuale, e la copertura è soddisfatta per costruzione
invece che per regola.

**Intoccati**: tutti i `page_analysis_*.py`; `resolution_*.py`;
`page_analysis_model.py`, `primitive_model.py`; `markdown_builder.py`,
`epub_builder.py`, `ir_*.py`; `extractor.py`.

**Shadow mode**: il Markdown nuovo si scrive accanto, mai al posto del legacy.

---

## 8. Il primo passo, e il criterio di uscita

**Tre pagine, non una** (rilievo §10.3 di Chat B, accolto con la sua ragione: una
pagina sola non può falsificare niente). Scelte per falsificare:

1. **DB p.99** — caso nominale, già guardata, con il render e il Markdown legacy
   a confronto;
2. **DB idx 27 o Fab idx 283** — l'esplosione di occorrenze (56 e 75), cioè il
   caso che decide se l'arredo va rimosso prima o dopo;
3. **una pagina con un titolo evidente** — per vedere il paragrafo emesso al posto
   del titolo, che è il difetto che aprirà il tipo di nodo successivo.

### Criterio di uscita, nella forma che può fallire

`AGENTS.MD` §Migrazione dichiara che la milestone di uscita dallo shadow mode
**non esiste** ed è bloccante. Chat B (E2) chiede almeno un criterio provvisorio
scritto. Questo è quello, ed è **di questo stadio, non della pipeline**:

- **N pagine estratte a caso** da un pool non condizionato, **seed dichiarato
  prima** (prassi del campione cieco di Milestone 37);
- **la domanda fissata per iscritto prima** che il render esista: il Markdown si
  legge come la pagina — ordine giusto, paragrafi giusti, e ogni immagine tolta è
  nominata dove stava;
- **giudizio a vista dell'utente**, con il render accanto;
- **tipo di errore squalificante dichiarato prima**: **contenuto perso** — testo
  presente sulla pagina e assente dall'uscita. Errori di paragrafo o di titolo si
  contano ma non fanno fallire.

**Distinzione da non confondere**: non è la milestone di uscita dallo shadow mode.
Quella richiede la lista di `AGENTS.MD` §Migrazione, che include «callout e
tabelle DB preservati» — e con questi tipi di nodo callout e tabelle non sono
preservabili. **Uscire davvero dallo shadow mode a v0 è impossibile**, e dire il
contrario sarebbe il criterio che non può fallire.

---

## 9. Fuori scope, esplicito

EPUB e `epub_builder.py`, che oggi non è nemmeno IR-first (`main.py:436` gli passa
l'extractor, `main.py:425` passa la IR a `build_markdown`); i tipi di nodo tabella
e callout; la rimozione dell'arredo ricorrente (§6, document-level, dichiarata
precondizione); la persistenza di `NormalizedPrimitivePage`; le schede mostro come
forma propria; la separazione in due stadi; ogni regola di Resolution.

---

## 10. Decisioni aperte

1. **`text.heading` e `text.labelled_entry` entrano nel primo passo o no.** Il §3
   dimostra che servono perché DB p.99 esca corretta. Ma il §8 dice «tre pagine
   per falsificare» e il §5 dice «cresce di un tipo alla volta»: quattro tipi al
   primo passo è già una crescita. **Non lo so, ed è la domanda che porto al giro
   architetturale.**
2. **L'arredo va rimosso prima o dopo il primo passo.** Se dopo, il primo passo
   produce Markdown rumoroso su pagine come DB p.99 e il criterio del §8 rischia
   di fallire per una causa fuori perimetro.
3. **La sillabazione**: resa (come in `epub_builder`) o dato del nodo? Se il testo
   viene dalla sorgente, ricongiungere è una modifica del testo, e la regola
   «non si ricompone» merita di essere interrogata su questo caso.

---

## 11. Affermazioni non verificate, per il giro architetturale

Affermazioni **negative**, la classe su cui Chat A è meno affidabile:

- `ResolvedSemanticDocument` non esiste in nessun file;
- `BackendPageCapture` e `NormalizedPrimitivePage` non hanno né serializzatore né
  deserializzatore;
- nessun producer emette uno `structural_kind` nel namespace `text.*`;
- niente, nella pipeline nuova, produce un `DocumentIR`.

Già verificate riga per riga, da non rifare salvo dubbio motivato:
`page_analysis_model.py:32`, `:107-118`; `markdown_builder.py:12`, `:94-107`,
`:179-195`; `ir_model.py:74-120` (`AIProposal`/`ReviewItem`/`HumanOverride`);
`main.py:425`, `:436`; `resolution_page_candidates.py:7-9`.

**Numeri della v1 ritirati e non ricitati qui**: l'85,2% e le sue derivate. Lo
script che li produceva è stato cancellato e non sono riproducibili; se servissero,
va riscritto e committato (`AGENTS.MD` §Aggiornamento documenti).

---

## 12. Changelog rispetto alla v1 — rilievi di Chat B, giro metodologico

**Integrati:**

- **B2** — contraddizione §5/§7: la regola di Resolution esce dal perimetro, che
  passa da quattro moduli a tre. *Il rilievo più costoso e il più utile.*
- **B1** — la misura del §7 confermava per costruzione («nessuna delle non contese
  è accettata» è conseguenza definitoria della regola implementata), e 85,2% e
  «35 su 236» erano i due lati della stessa partizione presentati come due
  evidenze. **Ritirati.** Verificato inoltre il ramo peggiore di B1b: Fab idx 283 e
  DB idx 27 **sono** nel campione, quindi 131 occorrenze su 236 (55,5%) venivano
  da 2 pagine su 20.
- **B4** — l'eccezione del §2 era dichiarata, non argomentata. Sostituita da una
  pagina reale eseguita e guardata.
- **B3** — persistenza dichiarata (§5.1).
- **B5** — «nessuna soglia» era falso; il punto cade con la regola.
- **B6** — il criterio di crescita era saturo dal primo giorno: sostituito dalla
  scelta di tre pagine per falsificare (§8).
- **B8** — l'«11 kind» era verificato e mal collocato; la conseguenza che ne
  traeva è accolta e sta nel §3.
- **C1, C4, E1, E2, E3, §10.3** — accolti, vedi §6, §7, §8.
- **B9** in parte: il fondamento del §3(c) della v1 è la decisione dell'utente, e
  ora è detto così invece di appoggiarsi a un invariante con una violazione in
  produzione.

**Rifiutati, con la ragione:**

- **D2 e la posizione sul §10.2** («un nodo per asset distinto per pagina, con
  `occurrence_count`»). Cade sulla condizione di ribaltamento che Chat B stessa
  aveva indicato in F5: le 75 occorrenze di Fab idx 283 hanno **62 digest
  distinti** (DB idx 27: 42 su 56). Accorpare per digest darebbe 62 nodi, non uno.
  La risposta è invece la rimozione per ricorrenza document-level (§6).
- **B7 nella conclusione**. L'analisi della v1 era incompleta e il rilievo è
  giusto; la conclusione regge, e l'anello mancante è ora nel §4.
- **§10.1** (che cosa significhi «senza perdita»): non rifiutato ma **tolto dallo
  scope**, come Chat B suggerisce — l'adapter IR 2 → IR 1 non ha committente,
  visto che il §4 esclude il renderer legacy.
