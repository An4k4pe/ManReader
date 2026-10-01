# Proposta — IR 2 minima a uno stadio, bersaglio Markdown

Chat A, Modalità P. 17 agosto 2026. Fuori dal repo (prassi di Milestone 33/34/35).
Base: `3a2238d`, suite 1263 verde, sei producer wired.

---

## 1. Cosa si chiede di approvare

Aprire lo stadio **`DocumentIR 2`** con la decisione architetturale dedicata che
`AGENTS.MD` richiede.

`IR 2` compare nella lista **«Attività non autorizzate senza decisione
architetturale dedicata»**. Il titolo di quella sezione è un cancello, non un
divieto di merito, e il modo di passarlo ha due precedenti nel repo:
Milestone 34 per `resolution` (voce della stessa lista, aperta con un documento
di Modalità P e due giri Chat B) e Milestone 26 per `clustering` (vietato in sei
punti «salvo una futura decisione architetturale dedicata»).

Nel merito, `IR 2` non è un'alternativa a qualcosa: è **il bersaglio
dell'architettura approvata**, `AGENTS.MD` §Architettura approvata:

```
… → PageAnalysis → DocumentAnalysis → Resolution
  → ResolvedSemanticDocument → DocumentIR 2 → renderer Markdown / EPUB
```

---

## 2. Il difetto che la motiva, e non è su una pagina

Le proposte di questo progetto si giudicano su una pagina che esce sbagliata.
Questa no, e va detto subito: **il difetto è che non esiste nessuna pagina da
guardare.** Sei producer wired, e nessun percorso che produca una riga di
Markdown.

Il fatto strutturale, letto nel codice:

- **`PageAnalysis` ha serializzazione andata e ritorno**
  (`page_analysis_serialization.py`, `page_analysis_store.py`, Milestone 5).
- **`BackendPageCapture` e `NormalizedPrimitivePage` non ne hanno alcuna.**
  Nessun `to_dict`, nessun `from_dict`, nessuno store.
- **`RegionCandidate`** (`page_analysis_model.py:107-118`) porta `candidate_id`,
  `page_id`, `bbox`, `proposed_structural_kind`, `primitive_ids`. I
  `primitive_ids` sono **stringhe opache**. Il testo vive in
  `TextPrimitive.text`, cioè nell'oggetto che non persiste.
- **`ResolvedSemanticDocument` non compare in nessun file.** `resolution_model.py`
  definisce `ResolvedCandidateOutcome` e `ResolvedPageCandidates`: esiti per
  candidato, nessun contenuto.

> **La pipeline nuova ha il lato struttura e non ha il lato contenuto.**

Da qui discendono tre cose che sembravano separate:

1. **Ogni consumer deve riaprire il PDF** e rifare capture + normalizzazione +
   tutti i producer, perché non c'è artefatto da cui partire. La composizione dei
   producer è duplicata in `job_page_analysis_runner.py` e in almeno quattro
   script; `prototype_vertical_slice_page.py` lo dichiara in docstring.
2. **`page.md` è usa e getta.** È scritto da un diagnostico che ricalcola tutto in
   memoria. Non è un producer di Markdown, e non esiste.
3. **La cache di Milestone 22** salva il `PageAnalysis` ed evita la ricattura, ma
   un `PageAnalysis` da solo non produce una riga di testo.

---

## 3. Le tre decisioni prese, con la ragione

**(a) Uno stadio, non due.** `ResolvedSemanticDocument` e `DocumentIR 2` guadagnano
il proprio costo quando semantica e resa divergono, cioè con più renderer dai
bisogni diversi. Con il solo Markdown e due tipi di nodo sarebbero lo stesso
oggetto con due nomi, e il confine andrebbe indovinato adesso. Separare dopo è un
rinominare più un confine che si vede; separare ora è un confine ipotizzato.
*Costo dichiarato, ridimensionato dall'utente e accettato*: quando arriverà
l'EPUB la separazione andrà probabilmente fatta, ma poiché l'EPUB leggerà solo
ciò che esce dai producer attraverso IR 2, sarà un'**estensione** di IR 2, non un
rifacimento della pipeline.

**(b) Bersaglio Markdown.** L'EPUB si affronta dopo, e solo se il Markdown non
basta. Restringe la decisione da «progettare la IR» a «cosa deve portare un nodo
perché una riga di Markdown esca giusta».

**(c) «I producer lavorano in concerto» = Resolution più forte, non producer che
si parlano.** Producer che si chiamano fra loro o condividono soglie sono ciò che
`AGENTS.MD` §Layout e candidati vieta, con due ratifiche misurate (Milestone 24 e
30). La combinazione avviene in Resolution o nel consumer — e Resolution ha
**una regola per sei producer**. Decisione dell'utente, con riserva esplicita di
riaprirla.
*Onestà sul punto*: l'invariante non è pulito nemmeno nel documento —
`embedded_visual`, già wired, filtra con soglie duplicate da altri due producer, e
`AGENTS.MD` lo definisce «alla lettera un filtro su criterio altrui», dichiarando
la questione aperta.

---

## 4. Il fatto che ha cambiato il piano in corso di scrittura

L'idea ovvia era: adapter **IR 2 → IR 1** e riuso di `markdown_builder.py`
invariato. È anche l'unica direzione di adapter che `AGENTS.MD` §Semantica e IR
contempla («ammesso solo nei casi senza perdita»), e `build_markdown` prende già
un `DocumentIR`.

**Non regge, ed è verificabile in due punti:**

- `markdown_builder.py:94-107` — `_should_start_new_paragraph` decide il confine
  di paragrafo da `vertical_gap >= font_size * 1.2` e da una transizione di
  colonna geometrica.
- `markdown_builder.py:179-195` — `_is_heading_text` decide i titoli da
  maiuscolo ≤ 40 caratteri, da `avg_font_size >= 14.0`, e da
  `stripped.startswith("Scena ")`.

Cioè il renderer legacy **ri-deriva dalla geometria** la struttura che IR 2 gli
porterebbe già decisa dalla sorgente. Passare per lui rimetterebbe esattamente il
difetto che `Criterio_ParagrafoDaBlocco_v1.md` ha tolto — la posizione permanente
dell'utente, corretta tre volte: *riga e paragrafo vengono dalla sorgente, la
geometria serve a posizionare e a controllare, mai a ricostruire*.

**Conseguenza**: serve un **emettitore Markdown IR2-first nuovo**, e i renderer
legacy restano **intoccati**. Non è «modifica dei renderer» (voce della lista
gated): è un modulo nuovo accanto, ed è la direzione che `AGENTS.MD` §Semantica e
IR chiede («Markdown ed EPUB devono progressivamente diventare IR-first»).

---

## 5. Il modello, minimo

Due tipi di nodo, perché due sono quelli che la pipeline sa riempire **oggi**:
il paragrafo (dal blocco della sorgente) e la nota d'asset (dai candidati
visuali).

```
DocumentIR2
    schema_version: str
    provenance: IR2Provenance      # source_id, generation_id, producer set
    pages: tuple[PageIR2, ...]

PageIR2
    page_id: str
    nodes: tuple[NodeIR2, ...]     # l'ordine della tupla E' l'ordine di lettura

NodeIR2
    node_id: str
    kind: str                      # "text.paragraph" | "asset.note"
    text: str | None
    asset: AssetRefIR2 | None
    primitive_ids: tuple[str, ...] # provenienza, mai vuota
    page_ids: tuple[str, ...]      # >1 = provenienza multipagina
    candidate_ids: tuple[str, ...] # da quali candidati viene, se ne viene
    resolution: str                # "accepted" | "unresolved" | "no_candidate"

AssetRefIR2
    digest: str
    file_name: str
    proposed_structural_kind: str  # dal candidato, riportato non deciso
    bbox: BBox
    occurrence_count: int          # su questa pagina
```

Tre scelte, con la ragione:

- **`kind` è un pattern aperto**, non una lista chiusa — stessa disciplina di
  `_STRUCTURAL_KIND_PATTERN` in `page_analysis_model.py:32`. Aggiungere
  `text.heading`, `text.list_item` o `layout.stat_block` **non richiede nessuna
  modifica al modello**. È la proprietà che rende sostenibile «cresce di un tipo
  di nodo alla volta».
- **`page_ids` è una tupla dal primo giorno** anche se in v0 avrà sempre un
  elemento: `AGENTS.MD` §Semantica e IR richiede provenienza multipagina, e
  aggiungerla dopo cambierebbe il tipo. Costa una tupla.
- **`resolution` è riportata sul nodo, non decisa.** Serve perché Resolution
  lascia `unresolved` la grande maggioranza dei candidati e «Nessuna esclusione
  può essere silenziosa» (§Coverage e ownership) vale anche qui.

**Ordine di lettura**: `page_analysis_model.py` nega esplicitamente che l'ordine
dei candidati sia un ordine di lettura. In IR 2 invece **l'ordine dei nodi È
l'ordine di lettura**, ed è la prima volta che il progetto lo dichiara come
contratto. Va scritto nel modello, non lasciato implicito.

---

## 6. Il primo passo, e come cresce

**Una pagina, end-to-end, con due tipi di nodo.** Pagina proposta: **DB p.99
posizionale (stampata 97, verificata a render)** — già la pagina P0 di
Milestone 36, e contiene prosa a due colonne, uno sfondo, un'illustrazione a
colonna piena e due riquadri, quindi esercita entrambi i tipi.

Poi: **ogni tipo di nodo nuovo lo apre una pagina che esce sbagliata.** Non un
giro di misure, non una tassonomia preventiva — la stessa disciplina che il
progetto pretende dalle proposte, applicata alla roadmap.

È la terza via fra le due che l'utente aveva in mente, e tutte e due hanno un
precedente misurato qui dentro: «prima la IR, poi le mancanze» è Milestone 33
(contratto deciso, producer mai scritto, riaperto quattro milestone dopo);
«prima tutti i pezzi, poi incastro» sono le Milestone 20-37, diciotto milestone
di pezzi e zero output.

---

## 7. Resolution più forte: la porzione minima

Serve solo quanto basta a far esistere i nodi `asset.note`. Oggi l'unica regola
accetta un `interior_visual_frame` **solo quando un `embedded_visual` referenzia
le stesse identiche primitive** — cioè solo in caso di conflitto.

Misurato su 20 pagine estratte uniformemente (seed `20260817b`, DB/Dag/DrW/Fab,
236 occorrenze immagine): **85,2% delle occorrenze è referenziata da candidati di
un solo producer**, e nessuna di quelle è accettata. L'insieme delle accettate
coincide con quello delle contese (35 su 236).

> La pipeline nuova mostra un'immagine solo quando due producer se la contendono.

Regola minima proposta: **un candidato senza concorrenti sulle stesse primitive è
accettato.** Nessuna soglia, nessun discriminatore.

*Decisione aperta, non risolta qui*: quella regola accetta anche ogni fregio
ripetuto, e su una tabella con un'icona per riga produce decine di nodi
(misurato: 75 occorrenze su Fab idx 283, tabella dell'equipaggiamento verificata
a render; 56 su DB idx 27, campiture di riga). Se sia un problema di IR 2 o del
renderer è una domanda vera e la porto a Chat B senza risposta.

---

## 8. Perimetro

**Moduli nuovi**: il modello IR 2, il costruttore da (primitive + `PageAnalysis` +
esiti Resolution), l'emettitore Markdown IR2-first, la regola di Resolution del §7.

**Intoccati**: tutti i `page_analysis_*.py` (nessun producer si tocca);
`page_analysis_model.py`, `primitive_model.py` (nessun campo nuovo sui contratti
esistenti); `markdown_builder.py`, `epub_builder.py`, `ir_*.py` (IR 1 e i renderer
legacy restano autorevoli e invariati); `extractor.py`.

**Shadow mode**: il Markdown nuovo si scrive accanto, mai al posto di quello
legacy. È il primo punto in cui il confronto di equivalenza previsto da
`AGENTS.MD` §Migrazione diventa possibile — e quella sezione dichiara che **la
milestone di uscita dallo shadow mode non esiste ed è una decisione aperta e
bloccante**.

---

## 9. Fuori scope, esplicito

EPUB e `epub_builder.py`, che oggi non è nemmeno IR-first (`main.py:436` gli passa
l'extractor, mentre `main.py:425` passa la IR a `build_markdown`); i tipi di nodo
titolo, elenco, tabella, callout, che nessun producer sa riempire; la persistenza
di `NormalizedPrimitivePage` (ottimizzazione, non precondizione: se IR 2 persiste,
un giro da PDF a IR 2 in un processo solo non ha bisogno di rileggere la capture);
le schede mostro come forma propria; la deduplicazione document-level; la
separazione in due stadi; ogni regola di Resolution oltre quella del §7.

---

## 10. Decisioni aperte, quelle su cui sono davvero indeciso

1. **«Senza perdita» riferito a cosa.** `AGENTS.MD` ammette l'adapter IR 2 → IR 1
   «solo nei casi senza perdita». IR 2 porta provenienza (`primitive_ids`,
   `candidate_ids`, `resolution`) che `BlockIR` può tenere solo dentro
   `metadata: dict[str, str]`. Se «senza perdita» riguarda il contenuto,
   l'adapter è ammissibile; se riguarda tutto, non lo è mai. Non lo so, e la
   risposta decide se l'adapter esiste.
2. **La regola del §7 e i fregi ripetuti**: problema di IR 2 o del renderer?
3. **Se il primo passo debba essere una pagina o tre.** Una pagina è la
   disciplina del progetto; tre eviterebbero di progettare su un caso singolo.
4. **Se `resolution` sul nodo sia il posto giusto** per l'esito, o se un nodo
   debba esistere solo per ciò che è accettato, con il resto altrove.

---

## 11. Affermazioni che non ho verificato, per il giro 2

Sono affermazioni **negative**, cioè quelle su cui Chat A è meno affidabile:

- `ResolvedSemanticDocument` non esiste in nessun file del repo;
- `BackendPageCapture` e `NormalizedPrimitivePage` non hanno né serializzatore né
  deserializzatore;
- nessun producer emette uno `structural_kind` nel namespace `text.*` (11 kind
  oggi, tutti `layout.*`);
- niente, nella pipeline nuova, produce un `DocumentIR`.

Già verificate da me riga per riga, da non rifare salvo dubbio motivato:
`page_analysis_model.py:32` (pattern del kind), `:107-118` (`RegionCandidate`);
`markdown_builder.py:12` (firma), `:94-107`, `:179-195`; `main.py:425`, `:436`;
`resolution_page_candidates.py:7-9` (docstring della regola unica).
