# Proposta — una tabella vera nel Markdown, da IR 2 (v2)

Chat A, Modalità P. 19 agosto 2026. Fuori dal repo. Sostituisce la v1 dopo il
giro metodologico, i cui rilievi hanno riscritto **tre criteri su quattro**.

**Registra `AGENTS.MD` §614**: «tabelle, callout o liste come nuovo comportamento
attivo» è fra le attività che richiedono una decisione architetturale dedicata.
Questo documento è quella decisione.

---

## 1. Il bersaglio, e la regola di metodo **riformulata**

**Una tabella che si legge come una tabella in `page_ir2.md`.**

La v1 introduceva la regola «non si costruisce niente che non finisca
nell'uscita». **Era formulata male, e condannava la proposta stessa**: presa alla
lettera vieta qualunque IR — una IR fedele contiene per definizione più di quanto
un renderer emetta — e vieta anche l'igiene di contratto del §6, che in nessun
`page_ir2.md` finisce. Rilievi B‑8 e B‑9.

Formulazione corretta, dal giro metodologico:

> **Niente si costruisce senza un consumatore scritto nello stesso giro.**

Dice ciò che la v1 voleva dire, non condanna l'igiene, e taglia da sola il lavoro
orfano — a partire da un pezzo di questa stessa proposta, §5.

## 2. Cosa esiste già, **con i limiti che la v1 aveva omesso**

- **Dove `lines/lines` risolve, non taglia mai una parola**: 0 span tagliati su
  35. `text/lines`, la configurazione dell'unico producer, ne taglia il **61%**
  (215 su 353).
- **`lines/lines` tace spesso**: su 5 pagine utili non trova nulla su 3.
  «Risolve tutto ciò che trova, 8 su 8» **non sostiene «le tabelle si
  risolvono»**: il denominatore è definito dal numeratore. Rilievo B‑4, e la v1
  usava quella frase in grassetto come premessa.
- **Il limite del campione, che la v1 ometteva e il documento gemello
  dichiarava**: **5 pagine utili, non 12**. Rilievo B‑5. Su quella base non si
  può appoggiare una scelta a scope pipeline: vedi §3.
- **IR 2 produce Markdown verificato**, E‑B 10 su 10 sul campione cieco.
- **`layout.table` esiste già** come `structural_kind` emesso.

## 3. La strategia in v0: **solo `lines/lines`**

La v1 prevedeva di affiancare le due strategie, con la regola di ammissione presa
«nella direzione» di `extractor.py:159-175` ma senza le sue costanti. Il giro
metodologico ha mostrato che **così non resta niente**: tolte le costanti, la
validazione era esattamente quelle costanti. Rilievo B‑6, ed era la decisione
centrale, assente.

**v0 usa `lines/lines` e basta.** Dove tace, non c'è tabella: quel testo resta
paragrafi, come oggi.

Non è prudenza, è la sola formulazione senza soglie inventate — ed è coerente con
la posizione permanente dell'utente sulle soglie desunte dal documento. Il costo è
dichiarato e misurato: **meno tabelle**. Su 5 pagine utili, 3 non ne avrebbero.

**L'affiancamento diventa una decisione a sé**, con un criterio proprio, quando
esisterà una regola di ammissione non hardcoded. Fuori scope qui, e non «adiacente».

## 4. La forma: un nodo con dentro la griglia

`NodeIR2` guadagna un terzo campo alternativo: «esattamente uno fra `text`,
`asset`, `structure`».

```
NodeIR2.structure: StructureIR2 | None

TableIR2(rows: tuple[tuple[CellIR2, ...], ...])
CellIR2(row: int, column: int,
        primitive_ids: tuple[str, ...],
        text: str)
```

**Il campo si chiama `structure`, non `table`**: alla seconda volta — callout,
scheda mostro — si allarga un'unione invece di aggiungere un quarto braccio.

**La cella porta una stringa, non una tupla di paragrafi.** Cambiato dalla v1
(D‑1 del giro metodologico), e chiude una decisione bloccante: il contenuto di una
cella **non è prosa**, e `Criterio_ParagrafoDaRiga_v1.md` §5 è **CADUTO** proprio
fuori dalla prosa. Con la tupla bisognerebbe decidere adesso cosa succede a
`breaks_paragraph` dentro una cella; con la stringa no. La tupla entrerà quando
esisterà un renderer che la usa — l'EPUB con `<p>` in cella — e allora la
decisione avrà un consumatore, come chiede il §1.

**Il testo delle celle viene dalla sorgente.** Da pdfplumber **solo la geometria**
dei confini; le `TextPrimitive` alle celle per sovrapposizione, come
`table_candidate` fa già per le bbox (Milestone 20, `positive_intersection`).

**I residui.** Le primitive dentro la bbox della regione ma **fuori da ogni
cella** — titolo della tabella, nota a piè di tabella, testo sopra un filetto —
**restano nodi paragrafo normali, fuori dal nodo tabella**. Rilievo C‑5: senza
questa regola sparirebbero. La copertura regge perché ogni primitiva sta comunque
in esattamente un nodo.

**L'ordine.** Il nodo tabella prende la posizione della **sua prima primitiva**
nell'ordine ricevuto, come i paragrafi. Se le primitive della regione arrivano
interlacciate con il testo circostante, estrarle le sposta rispetto a quel testo —
ed è esattamente ciò che P0 deve cogliere. Rilievo B‑10, dichiarato invece che
sottinteso.

### 4.1 Perché non le celle come nodi — chiuso

L'alternativa aveva **un vantaggio reale**: la correzione umana per cella.
Condizione posta all'utente e **non si dà**, per una ragione che viene
dall'obiettivo e non da una preferenza: *«è un lavoro di consultazione il motivo
per cui stiamo creando questo programma»*. `AGENTS.MD` §Obiettivo dice «perché la
consultazione resti comoda». L'unità di correzione resta il nodo tabella.

I tre costi che la scartano — due campi nuovi comunque, l'ordine che `column_band`
legge per colonne, i `node_id` che cambiano tarando la strategia — restano
**argomentati, non misurati**. La v1 li chiamava «verificati»: rilievo B‑13.

## 5. Da dove viene la griglia

**Una misura satellite** sul pattern di Milestone 7/33/37, che per ogni
`table_candidate` riporta **dove cadono i confini di riga e colonna** secondo
`lines/lines`, e i **residui** del §4.

Nessun producer toccato: `table_candidate` ha oracoli propri (Milestone 20,
Dag p.137, 114/57 primitive).

**Tolta la seconda metà.** La v1 faceva rispondere alla misura anche «la griglia si
risolve?», salvando così `Criterio_TabellaRisolvibile_v1.md`. Ma il consumatore di
quel dato è la discriminazione scheda/tabella, che la v1 stessa metteva fuori
scope: nell'uscita «non risolta» e «risolta ma scartata» producono la stessa cosa.
Due rami, una conseguenza — il difetto che la v1 rimproverava agli altri criteri.
Rilievo B‑7. **Il terzo criterio resta registrato e non eseguito**, senza fingere
che questo giro lo chiuda.

## 6. Igiene del contratto, prima di toccare il nodo

Non finisce nell'uscita, e sotto la regola riformulata del §1 va bene così: il suo
consumatore è il contratto stesso, ed è scritto qui.

- **`schema_version` non è controllata**: `'9.9-inventata'` passa. Aggiungere il
  gate sul modello di `page_analysis_model.py`, altrimenti un IR 2 vecchio
  fallirà dicendo «chiave sconosciuta» invece di «sei vecchio».
- **`text=""` è accettato**: un nodo può dichiarare testo e non averne. Vietarlo.
- **La porta di resa non deve mai applicarsi ai nodi strutturati.** Verificato:
  `is_rendered_in_body` rende `True` per ogni nodo che non sia `asset.note`,
  quindi oggi una tabella `unresolved` **viene resa**. Va scritto **nel modello**,
  perché il giorno in cui qualcuno estendesse la porta le tabelle sparirebbero in
  silenzio — che è come è morta l'opzione «tabella come asset».

## 7. Criterio di accettazione — da committare prima del codice

**La v1 aveva tre criteri su quattro che non potevano fallire.** Riscritti.

**P0 — il testo attorno alla tabella non si muove.** Su un set dichiarato di
pagine **con** tabella, il testo **fuori** dalla regione tabella è identico a un
**baseline congelato prima** della modifica — salvato su disco, non ricordato.
*La v1 diceva «sulle pagine senza tabelle», dove non c'è niente da togliere:
tautologia, rilievo B‑3.*

**A1 — si legge come una tabella.** Su **tutte** le pagine del set dichiarato, il
Markdown contiene una tabella le cui **celle** corrispondono alle celle della
pagina, giudicata a vista dall'utente con il render accanto.
*La v1 non aveva quantificatore e diceva «le righe»: una tabella a una colonna con
le righe giuste la superava. Rilievo B‑11.*

**A2 — conservazione dei caratteri.** La sequenza dei caratteri non‑spazio
dell'uscita di pagina, prima e dopo, identica **modulo la sola de‑sillabazione
dichiarata**.
*La v1 si intitolava «nessun contenuto perso» e verificava gli **id**, mentre il
documento gemello dichiara che il buco è nei caratteri. Rilievo B‑2 ed E‑4:
l'invariante **entra nel perimetro** invece di essere rinviato, altrimenti il
criterio prometteva più di quanto misurasse.*

**A3 — nessuna parola tagliata, con denominatore fisso.** Su **tutte** le regioni
del set — comprese quelle che **non** diventano tabelle — nessuno span
attraversato da un confine di colonna. E il set è su pagine **diverse** dalle
cinque che hanno selezionato la strategia.
*La v1 aveva il denominatore definito dall'esito ed era calcolata con la misura
che aveva scelto la strategia: circolare due volte. Rilievo B‑1, il principale.*

**Regola d'arresto, con la zona «uguale» chiusa.** Il giro si ferma se su una
pagina del set la tabella **non esce come tabella** — non basta «non peggio di
oggi». *Rilievo B‑12: «non peggio ma non leggibile» superava sia A1 sia la regola
d'arresto della v1, ed è la zona dove finiscono i giri a vuoto.*

## 8. Perimetro

**Ammessi**: `ir2_model.py`, `ir2_serialization.py`, `ir2_builder.py`,
`ir2_markdown.py`, `ir2_validate.py`, un modulo nuovo per la misura della griglia,
`scripts/prototype_ir2_page.py`, i test.

**Vietati**: ogni `page_analysis_*.py`, **incluso** `table_candidate`;
`resolution_*.py`; `primitive_model.py`; `markdown_builder.py`, `epub_builder.py`,
`ir_*.py`, `extractor.py`.

**Il perimetro regge, e la v1 lo dava per dubbio.** Il giro metodologico dichiarava
bloccante che il builder non potesse ricevere una regione tabella, dato che ogni
candidato esce `unresolved`. **Verificato e respinto**: `build_page_ir2` non legge
Resolution — riceve ciò che il chiamante gli passa, come già fa per le note
d'asset irrisolte — e la porta di resa non tocca i nodi non‑`asset.note`.
`resolution_*.py` resta fuori. Il timore sotto resta valido e diventa la terza
voce del §6.

## 9. Fuori scope

L'affiancamento delle strategie (§3). La categoria scheda mostro.
`text.heading` e `text.callout` in emissione. La rimozione dell'arredo. L'EPUB.
La modifica di `table_candidate`. La correzione per cella (§4.1). La cella
multi‑paragrafo (§4).

## 10. Cosa resta non risolto, e va detto

**Nessuna regola di Resolution accetta un `layout.table`.** Non blocca — §8 — ma
resta: la tabella entra nell'uscita come `unresolved`, e nessuno ha deciso se
debba esserlo.

**Quanto pesano le tabelle sull'illeggibilità.** Non misurato. Il documento gemello
riporta che 55 dei 65 nodi in review sono `embedded_visual`, cioè arredo: «l'unica
che si vede nell'uscita» può essere vero **e piccolo insieme**. Rilievo del giro
metodologico, e non è stato risolto qui.
