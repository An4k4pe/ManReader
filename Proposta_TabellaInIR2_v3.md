# Proposta — una tabella vera nel Markdown, da IR 2 (v3)

Chat A, Modalità P. Fuori dal repo. Sostituisce la v2 dopo il giro
architetturale, che l'ha dichiarata **non approvabile** e ha trovato nel repo la
risposta che le mancava.

**Registra `AGENTS.MD` §614**: «tabelle, callout o liste come nuovo comportamento
attivo» richiede una decisione architetturale dedicata. Questo documento è quella
decisione.

---

## 1. Cosa è cambiato, e perché la v2 era sbagliata

La v2 cercava i confini di colonna in una strategia di estrazione nuova, e ci
costruiva sopra due sezioni: quale strategia (§3) e una misura satellite che la
producesse (§5).

**Erano già nel contratto.** `State.md:122`: «`column_band` non deve leggere le
tabelle, **deve dire dove sono i confini di colonna**, e se una regione è una
tabella la gestisce il consumer di tabelle **aiutato da questi gutter**»; e «i
sette gutter annidati di DB p.76 non sono una patologia ma **la descrizione
corretta di una tabella a nove colonne**». Ripetuto a `:128`. E `:204` chiude:
**Milestone 37 ha tolto la restrizione al primo livello proprio per renderli
disponibili** — «Toglierla restituisce i gutter annidati che questa sezione
assegna al consumer di tabelle: DB p.76 torna a 7 gutter invece di 1».

`scripts/prototype_ir2_page.py:151-153` **li calcola già**, per l'ordinamento.

È la terza volta in questa sessione che il repo aveva una risposta che Chat A non
ha ritrovato. Cadono §3, §5, e con essi la scelta della strategia, il modulo
nuovo e il criterio A3 che li guardava.

## 2. Il bersaglio e la regola di metodo

**Una tabella che si legge come una tabella in `page_ir2.md`.**

> **Niente si costruisce senza un consumatore scritto nello stesso giro.**

La v2 si esentava da questa regola per l'igiene di contratto («il suo consumatore
è il contratto stesso»), il che la svuotava: se il contratto può essere
consumatore di sé, la regola non taglia più nulla. **Esenzione ritirata**: l'unica
igiene che resta nel §5 ha un consumatore vero, ed è dichiarato lì.

## 3. Da dove vengono griglia e celle — **zero moduli nuovi, zero pdfplumber in più**

| | da dove |
| --- | --- |
| **la regione** | `table_candidate`, producer già wired, che dà la bbox |
| **le colonne** | `ColumnBandMeasurements.gutter_x_intervals` — già nel contratto, già calcolati dallo script |
| **le righe** | le **righe di sorgente** raggruppate per sovrapposizione in y |
| **il testo** | le `TextPrimitive`, assegnate alla cella per sovrapposizione |

**Le righe vengono dalla sorgente, non da pdfplumber.** Una riga di tabella è
l'insieme delle righe di sorgente le cui estensioni y si sovrappongono — è
esattamente il caso di DB p.99, dove `Movimento:`, `Danno Bonus:` e `PF` sono tre
righe di sorgente sulla stessa riga visiva. La `y` dice **quali righe stanno
affiancate**; non ricostruisce testo, che resta quello della sorgente. È l'uso
sanzionato: «la geometria serve a posizionare e a controllare, mai a ricostruire».

**Nessuna chiamata a `find_tables` oltre a quella che il producer già fa.**

### 3.1 L'ipotesi che questo introduce, dichiarata prima di misurarla

Che i gutter di `column_band` descrivano **bene** le colonne di una tabella
**non è misurato**.

- **A favore**: DB p.76, sette gutter annidati che `State.md` chiama «la
  descrizione corretta di una tabella a nove colonne», e Milestone 37 che ha
  cambiato il wiring per averli.
- **Contro**: `State.md:128` — «accetta una colonna di tabella e **ne rifiuta le
  sorelle**» (Dag p.117, ispezionata a vista); e G2, che conta 109 confini di
  banda ancora dentro il bbox di una primitiva.

È un'ipotesi con un precedente forte e un controesempio noto. Il criterio del §6
la mette alla prova; **non è data per buona**.

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

**`structure` e non `table`**: alla seconda volta — callout, scheda mostro — si
allarga un'unione invece di aggiungere un quarto braccio all'invariante.

**La cella porta una stringa.** Il contenuto di una cella **non è prosa**, e
`Criterio_ParagrafoDaRiga_v1.md` §5 è **CADUTO** proprio fuori dalla prosa:
con una tupla di paragrafi bisognerebbe decidere adesso cosa succede a
`breaks_paragraph` dentro una cella. La tupla entrerà quando esisterà un renderer
che la usa, e allora avrà un consumatore.

**I residui.** Le primitive dentro la regione ma **fuori da ogni cella** — titolo
della tabella, nota a piè — restano nodi paragrafo, fuori dal nodo tabella. Senza
questa regola sparirebbero.

**L'ordine.** Il nodo tabella prende la posizione della sua prima primitiva
nell'ordine ricevuto, come i paragrafi.

### 4.1 Il difetto che i residui introducono, e che la v2 non vedeva

`ir2_builder.py` decide i paragrafi sull'**adiacenza** nella sequenza ricevuta.
Estrarre le primitive delle celle rende **adiacenti due righe che prima non lo
erano**: il titolo della tabella può saldarsi alla nota a piè.

Non lo coglie né il validatore — gli id restano coperti — né un confronto sulla
sequenza dei caratteri, perché `_normalised_sequence` butta gli spazi e due
paragrafi fusi danno la stessa stringa di due separati. **Per questo il criterio
del §6 confronta l'elenco dei paragrafi, non la sequenza dei caratteri.**
Rilievo B8 del giro architetturale.

### 4.2 Perché non le celle come nodi — chiuso

L'alternativa dava la correzione umana per cella. Condizione posta all'utente e
**non si dà**: *«è un lavoro di consultazione il motivo per cui stiamo creando
questo programma»*, e `AGENTS.MD` §Obiettivo dice «perché la consultazione resti
comoda». I tre costi che la scartano restano **argomentati, non misurati**.

## 5. Igiene del contratto

**`text=""` è accettato**: un nodo può dichiarare testo e non averne. Va vietato.
Consumatore: il validatore, che senza questo divieto non può distinguere un nodo
vuoto da uno pieno.

**Tolto il gate su `schema_version`**, che la v2 chiedeva. Due ragioni: nessuno
rilegge un IR 2 persistito — `document_ir2_from_dict` ha un solo chiamante fuori
dai test, il round-trip in memoria — quindi non ha consumatore; e la v2 ne
descriveva male l'effetto, dicendo che un file vecchio fallirebbe con «chiave
sconosciuta» mentre **fallisce con `is missing required keys`**, verificato
eseguendo. Un'igiene senza consumatore, descritta male, esce.

**Tolto il divieto nel modello** che la v2 voleva sulla porta di resa. Era una
politica di resa messa nel contratto, e contraddiceva una decisione di quattro
giorni fa che l'aveva voluta **parametro con default dichiarato**. Il timore è già
coperto: `render_node` solleva su un kind che non conosce. Se serve di più è un
test, non una riga di contratto.

## 6. Criterio di accettazione — **uno solo**

La v1 aveva tre criteri che non potevano fallire; la v2 li ha sostituiti con due
che non potevano passare e uno ancora vacuo. Qui ce n'è **uno**, con un errore
squalificante e due conteggi che si riportano.

**Il campione e le etichette** riusano il protocollo già registrato in
`Criterio_TabellaRisolvibile_v1.md` §4, mai eseguito: **12 pagine**, seed
**`20260820`**, esclusioni per costruzione, e **l'etichetta la dà l'utente a
vista sul render — «tabella», «scheda», «nessuna delle due» — PRIMA di vedere
qualunque uscita**.

**L'errore squalificante, uno solo: una regressione fuori dalla tabella.** Su
ogni pagina del campione, l'**elenco dei paragrafi** che non appartengono a una
regione tabella deve essere **identico** a un baseline **salvato su disco prima**
della modifica. Elenco, non sequenza di caratteri: due paragrafi fusi danno la
stessa sequenza e un elenco diverso (§4.1).

**Due conteggi, che si riportano e non fissano una soglia**:

1. quante regioni etichettate «tabella» escono **come tabella**, giudicate a vista
   dall'utente con il render accanto;
2. quante escono sbagliate, e in che modo.

**Perché nessuna soglia sul secondo asse.** Quante tabelle si ottengano dipende da
un'ipotesi non misurata (§3.1); fissare adesso un numero significherebbe o
inventarlo, o tararlo su ciò che l'implementazione produrrà. Il conteggio si
riporta e **lo giudica l'utente**, che è la stessa forma con cui è stato giudicato
il campione cieco di Milestone 38.

**Regola d'arresto**: una sola regressione fuori dalla tabella ferma il giro. Zero
tabelle riuscite non lo ferma, ma va scritto come esito — «non ha rotto niente e
non ha prodotto nulla» è un esito, e su questo progetto è il più frequente.

## 7. Perimetro

**Ammessi**: `ir2_model.py`, `ir2_serialization.py`, `ir2_builder.py`,
`ir2_markdown.py`, `ir2_validate.py`, `scripts/prototype_ir2_page.py`, i test.

**Nessun modulo nuovo.** La v2 ne prevedeva uno per la misura della griglia; con i
gutter dal contratto non serve, e cade con esso il rilievo che quel modulo
apparteneva per nome alla famiglia `page_analysis_*` che il perimetro vieta.

**Vietati**: ogni `page_analysis_*.py`, **incluso** `table_candidate`;
`resolution_*.py`; `primitive_model.py`; `markdown_builder.py`, `epub_builder.py`,
`ir_*.py`, `extractor.py`.

**Il perimetro regge, verificato due volte.** `build_page_ir2` non legge
Resolution — riceve ciò che il chiamante passa — e `is_rendered_in_body` non tocca
i nodi che non sono `asset.note`: un nodo `structure` irrisolto **viene reso**.
Confermato dal giro architetturale. E ora regge anche nella sostanza, perché la
regione e i suoi confini vengono da due producer **già wired** invece che
fabbricati dentro il perimetro saltando il livello dei candidati.

## 8. Fuori scope

L'affiancamento delle strategie di estrazione. La categoria scheda mostro.
`text.heading` e `text.callout` in emissione. La rimozione dell'arredo. L'EPUB.
La modifica di `table_candidate`. La correzione per cella. La cella
multi-paragrafo.

**L'invariante di conservazione dei caratteri** esce dal perimetro e torna dove
il documento gemello lo metteva: **primo della lista aperta, come cosa a sé**, in
`ir2_validate.py` e contro `NormalizedPrimitivePage`. La v2 lo chiamava A2 e lo
infilava qui, ma quello che aveva scritto era un confronto prima/dopo dell'uscita
— cioè P0 allargato, non l'invariante mancante. Rilievo B6.

## 9. Cosa resta non risolto

**Nessuna regola di Resolution accetta un `layout.table`.** La tabella entra
nell'uscita come `unresolved` e nessuno ha deciso se debba esserlo. Non blocca —
la porta di resa non tocca i nodi strutturati — ma è una decisione che manca, e
va presa prima o poi da chi decide, non aggirata scrivendola nel contratto.

**Quanto pesino le tabelle sull'illeggibilità non è misurato.** 55 dei 65 nodi in
review sul campione sono arredo: «l'unica che si vede nell'uscita» può essere vero
**e piccolo insieme**.

**Se i gutter descrivano le colonne** (§3.1). È l'ipotesi su cui poggia tutto il
§3, ed è quella che il criterio mette alla prova per prima.
