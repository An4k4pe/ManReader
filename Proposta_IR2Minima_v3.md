# Proposta — IR 2 minima a uno stadio, bersaglio Markdown (v3)

Chat A, Modalità P. 17 agosto 2026. Fuori dal repo (prassi di Milestone 33/34/35).
Base: `3a2238d`, suite 1263 verde, sei producer wired.

Chiude le quattro condizioni bloccanti del giro architetturale. Changelog in §13.

---

## 1. Cosa si chiede di approvare

Aprire lo stadio **`DocumentIR 2`**, e con esso — dichiarato, perché la v2 lo
attraversava in silenzio — **la prima assegnazione primitiva → nodo**, che è
ownership. `AGENTS.MD` §Attività non autorizzate elenca `IR 2`, `ownership
finale` e `coverage finale`: la v2 apriva il primo e passava sugli altri due
senza nominarli. Rilievo E3 del giro architetturale.

La formulazione che si chiede di approvare: ownership e coverage prodotte qui
sono **di stadio e rigenerabili**, non finali. Un nodo IR 2 si ricostruisce da
capo a ogni run dalle primitive e dai candidati; nessuna decisione diventa
irreversibile. È la stessa disciplina con cui lo shadow mode tiene il legacy
autorevole.

Il cancello è quello di `AGENTS.MD` («senza decisione architetturale dedicata»),
non un divieto di merito. Due precedenti: Milestone 34 per `resolution`,
Milestone 26 per `clustering`. Il criterio si soddisfa **al completamento del
secondo giro di revisione**, non con l'esistenza di questo documento.

---

## 2. Il difetto osservato, con la pagina e il render

**DB p.99 posizionale (stampata 97, verificata a render).** Comando eseguito:
`main.py DB.pdf --pages 99 --format markdown --no-ai`. Confrontato con il render
della pagina.

Sei difetti nel Markdown legacy:

1. Il watermark `Andrea Bruna - 550401` è **incollato dentro un paragrafo di
   prosa**.
2. Prosa della colonna sinistra e sua continuazione **separate da due asset e da
   un box**: l'ordine di lettura interlaccia le colonne.
3. Tre stat block **identici** escono come due `## titolo` e un `> [!INFO]`.
4. Le righe etichetta-valore **fuse in una riga sola**, in grassetto.
5. `CAPITOLO 7 – BESTIARIO` — intestazione corrente, arredo — promossa a **H2**.
6. La nota d'asset è il **nome del file**, e cita 3 asset su 6 immagini e 2
   vettoriali estratti (dipende da `--no-ai`; diverse delle non citate sono
   arredo, che per decisione dell'utente **non va nominato affatto**, §6).

I difetti 3, 4 e 5 sono la ri-derivazione geometrica del §4, **osservata** e non
predetta.

**Confronto con la pipeline nuova sulla stessa pagina.** Vince su tre punti:
ordine di lettura corretto, righe dello stat block separate, watermark in fondo
dov'è. Perde su uno: nessun titolo — e per decisione dell'utente **v0 resta senza
titoli**, §10.

### Il difetto strutturale

- `PageAnalysis` ha un round-trip completo (`page_analysis_serialization.py`,
  `page_analysis_store.py`).
- `BackendPageCapture` e `NormalizedPrimitivePage` hanno un **serializzatore
  diagnostico** (`pymupdf_capture_dump.py:544,547`, `asdict`) e **nessun
  deserializzatore**. *Correzione B1 del giro architetturale: la v2 diceva
  «nessuna serializzazione», ed era falso per metà. L'asimmetria è ciò che conta:
  nessuno può **rileggere** una capture.*
- `RegionCandidate` (`page_analysis_model.py:107-118`) porta `bbox`,
  `proposed_structural_kind`, `primitive_ids` **opachi**.
- `ResolvedSemanticDocument` non esiste **in nessun file di codice** (compare solo
  in `AGENTS.MD:121` e `State.md:350`, cioè nei due documenti che lo
  prescrivono).

> **La pipeline nuova ha il lato struttura e non ha il lato contenuto.**

---

## 3. Il testo: cosa esce, e il limite misurato

**L'atomo è la riga della sorgente, non il blocco.** Le righe si concatenano fra
loro, e il **testo** decide dove finisce un paragrafo. Nessuna geometria, e nessun
rientro.

1. **dentro una riga si concatena** senza separatore, ordinando per `span_index`;
2. **fra due righe consecutive si va a capo** se una di queste è vera, altrimenti
   si uniscono con un singolo spazio:
   - la riga successiva **non** comincia in minuscola;
   - la riga precedente finisce con `.` `;` `!` `?`;
   - la riga precedente finisce con `:` **e** la successiva comincia con un
     trattino o una cifra (guardia elenchi);
3. **de-sillabazione con la regex del Markdown**, `ir_builder.py:18` applicata a
   `:689` — decisione dell'utente, presa dopo che il giro architetturale (B7) ha
   mostrato che esiste già nel percorso Markdown e **diverge** da quella di
   `epub_builder.py:30`. Le due vanno unificate su quella di `ir_builder`. La
   condizione è quella della regex — lettera prima del trattino, minuscola dopo —
   e non il solo trattino finale.

Il `:` **non** termina il paragrafo, a differenza del legacy: è ciò che tiene
`Non-Mostri:` attaccato al suo testo. La guardia elenchi esiste perché dopo un `:`
che introduce un elenco andare a capo è giusto. **La guardia non è stata
esercitata**: su DB p.99 zero righe finiscono con `:`. Va provata su una pagina che
ne contenga.

**Perché la regola 1.** Gli span portano già la propria spaziatura; il consumer
attuale fa `" ".join` su ogni span e ne aggiunge una seconda. Misurato su DB p.99:
`'a '` + `'PERSUADERE'` + `'.'` dà `a PERSUADERE.` concatenato, e
`a  PERSUADERE .` con lo join. Gli span sono spezzati dai **cambi di font**, e
ogni confine di stile diventava uno spazio. È la terza volta che il progetto
ricostruisce qualcosa che la sorgente ha già.

Esito verificato su DB p.99: `Non-Mostri: in`, `a PERSUADERE.`, `PV: 15`,
`danno 2D8` — tutti corretti.

### 3.1 Il blocco non serve, e una mia affermazione precedente era falsa

**Su DB p.99 il blocco di sorgente non è il paragrafo.** Il box *Non-Mostri* ha
tre voci a rientro sospeso, e i blocchi le tagliano di traverso:

```
b0003: 'contano come mostri, ma come normali PNG.' | 'Resistenza: … sono dimez-'
b0004: 'zati (arrotondando per eccesso).'          | 'Immunità: … alla paura e '
```

`b0003` contiene la fine della prima voce **e** l'inizio della seconda; e `dimez-`
chiude `b0003` mentre `zati` apre `b0004`, quindi il confine cade anche in mezzo a
una parola.

**Ritratto quello che avevo scritto**: che il confine di voce fosse visibile «solo
nel rientro» e richiedesse geometria. **È falso.** Il testo lo porta — punto finale
più maiuscola successiva — e le regole del §3, applicate **fra righe**, lo trovano
senza nessuna geometria. L'errore era mio: le avevo applicate fra blocchi, e dentro
un blocco univo le righe senza guardare niente. Rilievo dell'utente.

**Esito verificato su DB p.99**: 46 righe di sorgente → 33 paragrafi. Il box esce
in **tre voci separate e corrette**:

```
Non-Mostri: in combattimento, gli scheletri non contano come mostri, ma come normali PNG.
Resistenza: tutti i danni perforanti sono dimezzati (arrotondando per eccesso).
Immunità: gli scheletri sono immuni alla paura e a PERSUADERE.
```

E si ricongiunge la prosa spezzata fra le due colonne — il **difetto 2 del §2** —
appoggiandosi all'ordine che `column_band` già dà.

**Due conseguenze.**

`text.labelled_entry` **non serve più**: le voci escono come paragrafi distinti e
corretti. Il tipo di nodo che la v2 dichiarava non opzionale sparisce dal §3.

E `Criterio_ParagrafoDaBlocco_v1.md` non va emendato, va **superato**: il paragrafo
non viene dal blocco, viene dalla sequenza di righe più l'evidenza testuale, e su
questa pagina **il blocco non gioca alcun ruolo**. Il che è un cambio di meccanismo,
non una postilla. *Limite dichiarato: è una pagina. Il criterio era stato
verificato su DB p.53, ed è lì che va provato il meccanismo nuovo prima di
superarlo — se lì il blocco serve ancora, la conclusione va rivista.*

**Somiglianza con il legacy, dichiarata perché non passi inosservata.** La regola 2
usa lo stesso segnale di `_ends_with_strong_punctuation`
(`markdown_builder.py:164`), che il §4 di questa proposta critica. Tre differenze:
il legacy termina anche su `:` e qui no; qui c'è la guardia della minuscola, che il
legacy non ha; e soprattutto il legacy la applica **insieme alla geometria**
(`vertical_gap`, transizione di colonna), mentre qui non c'è geometria.

**Non è un tradeoff di lunghezza**: la larghezza del paragrafo è irrilevante, il
Markdown è monocolonna e la larghezza la gestisce chi lo rende.

### 3.2 I box vanno resi come callout — valutazione di fattibilità

Requisito dell'utente: i box diventano callout, come fa il legacy
(`markdown_builder._render_callout`, ramo `block.role == "callout"`).

**L'informazione esiste già come candidato, e nessun producer nuovo serve.** Su
DB p.99 `interior_visual_frame` (Milestone 30, già wired) emette:

- `x53,2-307,3 y602,8-700,9` — **il box *Non-Mostri***, 11 primitive dentro;
- `x305,4-559,5 y296,9-700,9` — **il pannello statistiche**, 52 primitive.

Entrambi corretti. Metterli in relazione con i nodi di testo è mestiere del
consumer, come `AGENTS.MD` §Layout e candidati prescrive.

**Ma l'uscita grezza non è usabile così com'è: 10 candidati per circa 3 box
reali.** Due annidati dentro il pannello (`y332,6-385,5` e `y445,0-497,9`, le
righe di due stat block), uno che ingloba box e pannello insieme
(`x53,8-558,7 y581,8-708,3`), due frammenti (`a PERSUADERE.` e
`2D8), scudo grande`), e **tre sul fregio del piè di pagina**, che è arredo.

**`column_band` dimezza il rumore, ed è l'idea dell'utente.** Su DB p.99 la banda
ha gutter `x296-314`; un box di colonna non può attraversarlo. Il test elimina
**5 candidati su 10**, e sono la classe peggiore: quello che ingloba box e pannello
insieme, un frammento, e **tutti e tre quelli sul fregio del piè di pagina**.
Combinare due producer nel consumer è esattamente ciò che `AGENTS.MD` §Layout e
candidati prescrive, e non serve nulla di nuovo.

Restano 5: i **2 box veri**, 2 sotto-riquadri annidati dentro il pannello, e un
frammento. Il residuo è quindi un problema di **contenimento**, che ha una regola
ovvia — dentro una colonna vince il più esterno — mentre la classe di errore che
contava è già chiusa.

**Conseguenza**: il callout richiede comunque una regola che scelga fra candidati
annidati, e quella è una decisione di **Resolution**, che per
`interior_visual_frame` non esiste oltre alla deduplicazione con `embedded_visual`
(`resolution_page_candidates.py:7-9`).

Questa proposta **non la scrive**: il §7 tiene Resolution fuori dal perimetro, e
inventarla qui riaprirebbe il modulo che il giro architetturale ha appena tolto.
`text.callout` entra nel **vocabolario** (pattern aperto, costo zero) e non in
emissione, come `text.heading`. È il primo candidato per la milestone successiva,
e a differenza dei titoli **ha già un producer che lo trova**: gli manca solo chi
sceglie fra i suoi candidati.

---

## 4. Perché un emettitore nuovo e non l'adapter a IR 1

`markdown_builder.py` ri-deriva dalla geometria ciò che IR 2 gli porterebbe già
deciso. Tre condizioni, di cui **due non pilotabili da un adapter** (rilievo B3,
che rafforza l'argomento della v2 invece di indebolirlo):

- `:99-100` — `if not _ends_with_strong_punctuation(previous.text): return False`.
  Un paragrafo che non finisce con `.!?:;` viene fuso col successivo **a
  prescindere da qualunque geometria**. Nessun campo di `BlockIR` la sopprime.
- `:189-190` — `if stripped.isupper() and len(stripped) <= 40: return True`,
  valutata **prima** dello stile. Un nodo dichiarato `text.paragraph` con testo
  maiuscolo e breve viene promosso a H2 comunque.
- `:94-107` — `vertical_gap >= font_size * 1.2` e la transizione di colonna.

E la granularità non è l'obiezione che sembrava: `ir_builder.py:167` produce un
`BlockIR` per blocco-sorgente, cioè **`BlockIR` è già alla granularità giusta e
`build_markdown` lo rifonde lo stesso**. L'esperimento è in produzione da sempre e
il suo esito è il Markdown del §2, difetti 3-4-5.

**L'argomento corretto**: nel contratto `BlockIR` non esiste alcun canale per
dichiarare un `kind`; ottenere l'effetto voluto richiederebbe di fabbricare
geometria e stile falsi, cioè far mentire l'adapter sul PDF.

Conseguenza: **emettitore Markdown IR2-first nuovo**, renderer legacy
**intoccati**.

---

## 5. Il modello

```
DocumentIR2
    schema_version: str
    provenance: IR2Provenance
    pages: tuple[PageIR2, ...]

PageIR2
    page_id: str
    nodes: tuple[NodeIR2, ...]

NodeIR2
    node_id: str                          # page-qualified, derivato dal BLOCCO
    order: int                            # esplicito, non la posizione in tupla
    kind: str                             # pattern aperto
    text: str | None
    asset: AssetRefIR2 | None
    primitive_ids: tuple[str, ...]
    page_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    resolution: ResolvedCandidateOutcome | None
```

**`resolution` riusa il tipo di Resolution, non una stringa parallela.** La v2
scriveva `"accepted" | "unresolved" | "no_candidate"`: ometteva `rejected` — che
`resolution_model.py:32` definisce e che è **l'unico esito non banale che la regola
esistente produce** — e inventava `no_candidate`, che Resolution non emette.
`None` significa «nessun candidato», e non finge di essere un esito. Rilievo E2.

**`order` esplicito** invece della posizione nella tupla: precedente `BlockIR.order`
(`ir_model.py:45`) più `_renumber_blocks`. Costa un intero e rende l'ordine
diffabile. *E cade l'affermazione della v2 che l'ordine come contratto fosse una
prima volta: IR 1 lo fa già. Rilievo B4.*

**`kind` è un pattern aperto**, come `_STRUCTURAL_KIND_PATTERN`
(`page_analysis_model.py:32`). Limite dichiarato (B5): vale per i kind **senza
struttura interna**. Un kind che debba distinguere etichetta e valore non ha dove
metterla, e allora la scelta è fra campo nuovo, misura satellite (precedente
Milestone 7/33/37) o codifica nel testo. In v0 non si presenta.

**`page_ids` è una tupla dal primo giorno**: `AGENTS.MD` §Semantica e IR richiede
provenienza multipagina.

### 5.1 Persistenza e identità

**IR 2 v0 persiste.** Decisione dell'utente: IR 2 è dove atterrano
l'arricchimento dell'AI e le correzioni umane, e da lì si rigenera il Markdown.

`AGENTS.MD` §AI vieta all'AI di riscrivere il contenuto estratto e di toccare raw
o primitive. Le correzioni sono quindi uno **strato separato** che prende di mira
un nodo. **IR 1 ha già quella forma** e va riusata come precedente:
`AIProposal(target_id, …)`, `HumanOverride(target_id, …)`, `ReviewItem`, `Issue`
(`ir_model.py:74-120`), docstring `kept separate from extracted source data`.

**`node_id` page-qualified e derivato dal blocco.** La v2 lo derivava da
`source_observation_id` a livello di span, ed era rotto: `State.md:553-556`
registra già che `primitive_id` **non è univoco nel manuale, solo nella pagina**,
con l'etichetta «Nota per futuri consumer» — e IR 2 è quel consumer. Un
`node_id` non qualificato fa collidere il paragrafo di p.12 con quello di p.13, e
con essi le correzioni umane, che sono l'unica ragione della persistenza. Rilievo
E4. Il **blocco** e non lo span perché è invariante alla rimozione di span interni,
cioè sopravvive alla rimozione dell'arredo (§6), che è il primo evento previsto.

**Limiti della stabilità, tutti dichiarati** (la v2 ne dichiarava uno):

1. la **composizione del nodo** — togliere l'arredo (§6) cambia quali span entrano
   in un nodo; su DB p.99 il watermark sta dentro un paragrafo di prosa;
2. la **cura della degenerazione di cattura** — `State.md:68` la prescrive come
   milestone a sé, e cambierà `block_index` su un numero di pagine **mai
   misurato**;
3. la **capture non è versionata** — `PageAnalysisProvenance`
   (`page_analysis_model.py:145-151`) ha sette campi e nessuno è la versione della
   logica di cattura; `AGENTS.MD:414-416` lo registra come noto e non risolto. Un
   aggiornamento di PyMuPDF può riordinare `block_index` senza che nulla se ne
   accorga;
4. il caso di capture degenere già a verbale (Kul p.233).

---

## 6. L'arredo: rimosso, non annotato, non referenziato

Decisione dell'utente: sfondi e glifi ricorrenti «creano solo ridondanza di
segnali senza apportare nulla; lo scopo è leggere il manuale, non vedere come è
costituito, per quello c'è il PDF». **Nessuna nota, nessun riferimento nel
Markdown**; gli asset vanno in una cartella separata, identificati come arredo.

Questo **non** viola «Nessuna esclusione può essere silenziosa»: un asset in una
cartella dedicata più la sua riga nell'indice è registrato, semplicemente non è
nel flusso di lettura.

**Quanto copre il meccanismo, con la correzione B6.** La v2 diceva che il
meccanismo «esiste già». Sovrastimato: `State.md:598` misura che `content_digest`
**non separa** in generale — i filetti Fab danno 21 digest su 27 occorrenze,
arredamento che non condivide identità — e `DrawingPrimitive` non ha alcun campo
di identità. Resta valido l'uso stretto: **arte raster ripetuta identica**. I
fondi di pagina ci ricadono (stesso digest su ogni pagina); i glifi ricorrenti
solo se identici.

**Fuori perimetro** (document-level; questo passo è page-level), e dichiarato
precondizione parziale.

---

## 7. Perimetro

**Quattro moduli nuovi.** Il quarto è il validatore, accolto dal giro
architetturale: il repo affianca un validatore a ciascuno dei contratti confinanti
(`page_analysis_validate.py`, `ir_validate.py`), e la v2 ometteva l'unico modulo
che questo repo aggiunge sempre — proprio dove serve, perché la coverage «per
costruzione» va **verificata**, non asserita.

1. modello IR 2 più serializzazione con round-trip;
2. costruttore da (primitive + `PageAnalysis` + esiti di Resolution);
3. emettitore Markdown IR2-first;
4. validatore: ogni `TextPrimitive` della pagina in **esattamente un** nodo;
   nessun `primitive_id` in due nodi senza duplicazione dichiarata
   (`AGENTS.MD` §Coverage; oggi il non-doppione è misurato su quattro pagine,
   `State.md:194`, non garantito dal contratto).

La serializzazione segue la forma **validante** di `page_analysis_serialization.py`
(`_require_dict`, `_validate_exact_keys`), non quella permissiva di `ir_store.py`:
un contratto che regge correzioni umane persistenti non può accettare input non
validato.

**Resolution non si tocca.** Il nodo porta l'esito attuale.

**Provenienza del codice, dichiarata** (rilievo E5): `State.md:899-901` stabilisce
che l'emettitore diagnostico **non è** il punto di partenza del renderer IR-first
e che una sua promozione è una decisione esplicita. Questa proposta **non lo
promuove**: i moduli 2 e 3 si scrivono nuovi. Da
`scripts/prototype_vertical_slice_page.py` si riusano solo gli **invarianti
eseguibili** (`:867-868`, `:976-998`), portati dentro il validatore, dove è il loro
posto.

**Intoccati**: ogni `page_analysis_*.py`; `resolution_*.py`;
`page_analysis_model.py`, `primitive_model.py`; `markdown_builder.py`,
`epub_builder.py`, `ir_*.py`; `extractor.py`.

**Chi invoca l'emettitore**: uno script diagnostico dedicato, non `main.py`. Il
Markdown nuovo si scrive accanto, mai al posto del legacy.

---

## 8. Il primo passo e il criterio di uscita

**Tre pagine**, scelte per falsificare:

1. **DB p.99** — caso nominale, con render e Markdown legacy già a confronto;
2. **Dag p.84 o DB p.18** — struttura di colonna **mista**, entrambe già a verbale
   con il difetto descritto. *Sostituisce la pagina a esplosione di occorrenze
   della v2, che misurava una precondizione fuori perimetro e che per il criterio
   sotto non poteva comunque far fallire nulla. Rilievo D1.*
3. **una pagina con un titolo evidente** — per vedere il paragrafo emesso al posto
   del titolo, che è il difetto che aprirà la milestone del criterio dei titoli.

### Criterio di uscita, nella forma che può fallire

**La v2 aveva un criterio che non poteva fallire, ed era il rilievo principale del
giro architetturale (E1).** Diceva: squalificante è il *contenuto perso*. Ma il §7
garantisce la copertura per costruzione, quindi il contenuto perso è impossibile
per design e il criterio rilevava solo bug di implementazione. È la stessa cecità
che `State.md` registra tre volte (`:82`, `:144`, `:951-952`) e che `AGENTS.MD:683`
chiama «il terzo invariante sull'ordine, che continua a mancare».

Criterio corretto, **due errori squalificanti**:

- **contenuto perso** — testo sulla pagina, assente dall'uscita. Resta, come
  guardia contro i bug, e non come misura del design.
- **ordine sbagliato** — l'ordine emesso confrontato con un **riferimento umano**
  su poche pagine **trascritte a mano**, scelte **prima** della misura. È il terzo
  invariante che manca al progetto da sempre, e questo stadio è il primo punto in
  cui è formulabile: senza, il criterio è cieco all'ordine e un IR 2 perfetto e uno
  pessimo lo passano identici.

Più le condizioni di procedura, dalla prassi del campione cieco di Milestone 37:
**almeno dieci pagine da manuali differenti** (decisione dell'utente), estratte a
caso da un pool non condizionato con **seed dichiarato prima**; la domanda fissata
**per iscritto prima** che il render esista; giudizio a vista dell'utente con il
render accanto.

Le tre pagine di sviluppo sopra **non sono** il campione: servono a costruire, e
`State.md` registra due volte la differenza fra campione di sviluppo e campione
cieco su questo progetto.

**Escluso dal giudizio, dichiarato prima**: il rumore da note d'asset in eccesso
sulle pagine ricche di arredo. È causato da una precondizione fuori perimetro
(§6) e non deve far fallire questo stadio.

**Distinzione da non confondere**: non è la milestone di uscita dallo shadow mode.
Quella richiede la lista di `AGENTS.MD` §Migrazione, che include «callout e tabelle
DB preservati», qui non preservabili. **Uscire dallo shadow mode a v0 è
impossibile.**

---

## 9. Fuori scope

`text.heading` in **emissione** (§10, decisione presa: v0 senza titoli, il criterio
è milestone sua); `text.callout` in **emissione** (§3.2: il producer che li trova
c'è, manca la regola di Resolution che sceglie fra i suoi candidati — è la
milestone successiva più matura); il tipo tabella. *`text.labelled_entry` non è
fuori scope: è **caduto**, perché le regole del §3 producono già le voci come
paragrafi corretti (§3.1).* La rimozione
dell'arredo (§6); EPUB e `epub_builder.py`, che non è nemmeno IR-first
(`main.py:436` gli passa l'extractor, `:425` passa la IR a `build_markdown`); la
persistenza di `NormalizedPrimitivePage`; le schede mostro come forma propria; la
separazione in due stadi; ogni regola di Resolution.

---

## 10. Decisioni prese in questa sessione

**v0 senza titoli.** `text.heading` entra nel **vocabolario** (il pattern aperto lo
ammette, costo zero) e **non in emissione**. Ragione misurata su DB p.99: la moda
delle `font_size` è 9,0; `SCHELETRO` sta a 34,0 (3,8×) e il criterio page-local lo
prenderebbe, scartando correttamente l'arredo (`CAPITOLO 7 – BESTIARIO` a 7,0) e il
numero di pagina (9,0) — cioè meglio del legacy; ma `GUERRIERO`, `ARCIERE` e
`CAMPIONE` stanno a 10,0, l'11% sopra il corpo, e sulla pagina ci sono altri 13
span a 10,0 che titoli non sono. **Su quattro titoli ne prende uno.** Emettere un
kind il cui criterio è insufficiente sulla prima pagina su cui lo si applica è
Milestone 33 daccapo. Costo accettato e dichiarato: v0 produce Markdown senza
titoli, cioè peggio del legacy su quell'unico punto.

**De-sillabazione**: quella di `ir_builder.py:18`, e le due definizioni divergenti
in produzione vanno unificate su di essa.

**Sillabazione a cavallo di due blocchi: si uniscono i blocchi** (§3.1, regola 4).
Scartato il rientro come segnale, con la ragione dell'utente: non varrebbe in tutti
i casi, mentre il trattino a fine riga è un fatto del testo. Il confine di voce
resta non riparato, ed è il limite accettato di v0.

### 10.1 Aperta

Se il criterio del §8 vada eseguito su tre pagine o su un campione più largo, dato
che il secondo errore squalificante richiede **trascrizione a mano**.

---

## 11. Affermazioni non verificate

Nessuna: le quattro negative della v2 sono state verificate dal giro
architetturale. Tre reggevano, una era falsa per metà ed è corretta nel §2.

**Numeri della v1 ritirati e non ricitati**: l'85,2% e le sue derivate. Lo script
che li produceva è stato cancellato e non sono riproducibili.

---

## 12. Verificato in questa sessione, da non rifare

`pymupdf_capture_dump.py:544,547`; `ir_builder.py:18,689` e `epub_builder.py:30`
(le due de-sillabazioni divergenti); `ir_model.py:45` (`BlockIR.order`) e `:74-120`;
`resolution_model.py:32`; `primitive_normalizer.py:141` con `State.md:553-556`;
`State.md:598` (`content_digest` non separa), `:68`, `:899-901`;
`AGENTS.MD:414-416`; `markdown_builder.py:12,94-107,179-195`;
`page_analysis_model.py:32,107-118,145-151`; `main.py:425,436`;
`resolution_page_candidates.py:7-9`. Più, su DB p.99: i blocchi del box
*Non-Mostri*, le `font_size` dei quattro titoli, e l'esito delle tre regole di §3.

---

## 13. Changelog rispetto alla v2

**Condizioni bloccanti chiuse:** E1 (secondo errore squalificante sull'ordine,
§8); E2 (`ResolvedCandidateOutcome`, §5); E3 (ownership dichiarata, §1); E4
(`node_id` page-qualified dal blocco, §5.1).

**Correzioni di fatto accolte**, tutte verificate da Chat A prima di integrarle:
B1 (il serializzatore diagnostico esiste, manca il deserializzatore); B4
(`BlockIR.order` — l'ordine come contratto non è una prima volta); B6
(`content_digest` non separa in generale); B7 (la de-sillabazione c'è già nel
percorso Markdown, in doppia definizione divergente).

**Accolti**: B3 (l'anello del §4 riscritto con le due condizioni non pilotabili);
B5 (limite del pattern aperto); B9 (quattro limiti di stabilità invece di uno);
D1 (pagina 2 sostituita); D2 (forma validante); F1 (validatore, quarto modulo);
F4 (`order` esplicito); E5 (provenienza del codice dichiarata); C4 (rumore da
arredo escluso dal giudizio, dichiarato prima).

**Deciso dall'utente dopo il giro, e corretto due volte da lui.** Le regole di
paragrafo si applicano **fra righe**, non fra blocchi: applicandole fra blocchi il
box usciva fuso in un paragrafo solo, ed era un mio errore. Terminatori `. ; ! ?`;
il `:` non termina, con guardia elenchi su trattino o cifra. Misurato su DB p.99:
46 righe → 33 paragrafi, il box esce in **tre voci corrette**, e si chiude il
**difetto 2 del §2**. **Ritirata** la mia affermazione che il confine di voce
richiedesse il rientro: il testo lo porta. **Caduto** `text.labelled_entry`, che
non serve più. `Criterio_ParagrafoDaBlocco_v1.md` non va emendato ma **superato**,
con la verifica su DB p.53 dichiarata come condizione.

Aggiunta la valutazione dei callout (§3.2), con l'idea dell'utente di usare
`column_band`: elimina 5 candidati su 10, fra cui tutti e tre quelli sul fregio.
Criterio di uscita: **almeno dieci pagine da manuali differenti** (§8).

**Rifiutato, con dati**: la posizione del giro architetturale su §10.1, secondo cui
il box *Non-Mostri* si romperebbe solo nel legacy e il paragrafo-da-blocco lo
risolverebbe. Il dump dei blocchi (§3.1) mostra che `b0003` contiene la fine di una
voce e l'inizio della successiva: il difetto è nella pipeline nuova, e la sua causa
è che su quel box il blocco non è il paragrafo.
