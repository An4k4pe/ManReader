# Criterio di accettazione — giunzione `column_band` ↔ fetta verticale

> **SUPERATO IN PARTE da `Criterio_ParagrafoDaBlocco_v1.md`.** Il §2 qui sotto
> dichiara invariata «la regola di paragrafo»: quel criterio la cambia. Chi cita
> questo documento come garanzia che la segmentazione in paragrafi non è stata
> toccata cita un documento falso. Rilievo della revisione indipendente.

Scritto **prima** di costruire la giunzione e **prima** di guardare qualunque
output, come prescritto da `CLAUDE.md`. Il commit che introduce questo file non
contiene **nulla della giunzione**: è la prova della precedenza, ed è l'unica
cosa che distingue una pre-registrazione da una razionalizzazione. Contiene
invece `scripts/inspect_span_line_identity.py`, perché il §5-bis cita numeri e
`AGENTS.MD` §Aggiornamento documenti impone di committare lo script che li
produce insieme al testo che li riporta.

Origine: `State.md` §Diagnostica pre-milestone per column_band, righe 78, 88 e
112, che indicano la stessa azione da tre angoli diversi.

---

## 1. Scopo, e le domande a cui questo giro NON risponde

**Domanda a cui risponde**: la fetta verticale, che ha i cinque producer e non
ha le bande, e il confronto di reading order, che ha le bande e non ha i
producer, sono due artefatti disgiunti (verificato:
`compare_reading_order_with_column_bands.py:62-69` contro
`prototype_vertical_slice_page.py:64-84`). Unendoli, **il quadro cambia rispetto
al confronto isolato, e in che direzione?**

**Domande a cui questo giro NON risponde, e che nessuno deve citarlo per
chiudere**:

- Quanto spesso `column_band` ha ragione. Le pagine sono ancore di sviluppo già
  viste (§7).
- Il criterio di uscita della milestone `column_band` (State.md:76 e 114), che
  richiede un riferimento umano su pagine trascritte a mano e non esiste ancora.
- Se un producer possa filtrare i propri candidati (`AGENTS.MD` §Layout e
  candidati, questione aperta).
- Se aprire la milestone. Questo giro produce un fatto, non una decisione.

## 2. Perimetro di ciò che viene costruito

Un flag su `scripts/prototype_vertical_slice_page.py` che sostituisce
l'ordinamento di `_sorted_text_primitives` (`:219-220`, oggi `(y0, x0)` puro) con
`_tree_aware_order` (`compare_reading_order_with_column_bands.py:115`).

**La giunzione toglie un assemblaggio geometrico, non ne aggiunge uno** (§5-bis).
`_tree_aware_order` usa oggi `_by_visual_line`/`_group_visual_lines`, che ricava
la riga tipografica dalla sovrapposizione delle y; va sostituito con il
raggruppamento per `(block_index, line_index)` letto dal
`source_observation_id`, ordinando dentro la riga per `span_index`.

Invariati: cattura, normalizzazione, i cinque producer, la co-reference,
`resolve_page_candidates`, l'estrazione asset, la regola di paragrafo, i due
invarianti auto-verificati. Nessun producer nuovo, nessun contratto, nessun
wiring nel job, nessuna regola di Resolution, nessuna modifica ai renderer
(`AGENTS.MD` §Attività non autorizzate).

**I candidati visuali restano disponibili e non usati per ordinare.** La
giunzione li rende presenti; non insegna al consumer a leggerli. Questa è una
scelta dichiarata ora, non una dimenticanza scoperta dopo, ed è ciò che rende
falsificabile la predizione su DrW p.97 (§4).

## 3. Pagine, fissate adesso

Due obbligatorie — «una pagina che sbaglia e una che indovina», State.md:78:

| Pagina (posizionale) | Ruolo | Perché questa |
| --- | --- | --- |
| **DrW p.97** | quella che sbaglia | Unica pagina di prova dove la giunzione può aggiungere informazione: il suo difetto è documentato come **non correggibile dentro `column_band`**, e l'informazione mancante sta nei producer visuali che esistono solo nella fetta (State.md:86). È anche l'unica peggiorata dall'albero (107/171, State.md:100). |
| **Dag p.164** | controllo | Corretta nel confronto isolato (State.md:90). Verifica che la giunzione in sé — note, asset, Resolution interleavati al testo — non rompa un ordine che funzionava. |

Una terza, facoltativa, da leggere solo se le prime due non bastano a decidere:

| **DB p.18** | banco di prova dei visuali | È la pagina dove le uscite dei producer visuali sono già misurate (1 `page_covering_visual`, 17 `embedded_visual`, State.md:96) ed è quella che l'albero ha riparato (State.md:92). |

**Esclusa di proposito: DIE p.127.** L'esito è già noto (194/195, baseline
illeggibile, State.md:100): sarebbe una dimostrazione, non una prova, e costa
una lettura a vista come le altre.

Numeri **posizionali** (`page_index = N - 1`, `CLAUDE.md`). Da verificare con un
render prima di citare qualunque risultato, e prima di leggere.

## 4. Predizioni pre-registrate

Registrate ora perché possano fallire. **Non concorrono a pass/fail** (§6): sono
un controllo sul modello, tenuto separato dal giudizio per non poterlo
rimodellare a posteriori.

- **DrW p.97 — predizione: l'ordine resta sbagliato**, e nel modo esatto
  descritto in State.md:86 — prima la colonna destra alta (y 46-396, fuori
  banda), poi la banda (396-652), poi la colonna sinistra bassa (652-761),
  mentre l'ordine giusto è tutta la sinistra e poi tutta la destra. La giunzione
  rende disponibili i candidati visuali ma nessuno li usa per ordinare.
  *Se invece esce corretto*, il modello del difetto in State.md:86 è sbagliato e
  va capito prima di qualunque altra cosa.
- **Dag p.164 — predizione: resta corretto.** Se peggiora, il difetto è nella
  giunzione e non nelle bande, e va isolato prima di giudicare qualsiasi pagina.

## 5. Termine di paragone, e perché non è quello ovvio

Tre varianti per pagina:

1. `page.md` — invariato, `(y0, x0)` puro. Status quo di Milestone 36.
2. `page_lines.md` — **sola** unità di riga presa dalla sorgente (§5-bis),
   nessuna banda.
3. `page_bands.md` — ordinamento ad albero con le bande, sulla stessa unità di
   riga della variante 2.

**Il giudizio è 3 contro 2, mai 3 contro 1.** Il quinto giro di revisione ha
trovato il confronto truccato esattamente così: la correzione di riga applicata
al solo ramo a bande, con l'85% del guadagno apparente su DIE p.127 che veniva
da quella e non dalle bande (State.md:98). La fetta oggi ordina senza
raggruppare le righe, quindi **la variante 2 va costruita**: è un requisito sul
codice che discende dal criterio, ed è la ragione per cui il criterio andava
fissato prima di scrivere la giunzione.

## 5-bis. L'unità di riga viene dalla sorgente, e l'assemblaggio geometrico è difettoso

Rilievo dell'utente, verificato con `scripts/inspect_span_line_identity.py`
(committato con questo file, `AGENTS.MD` §Aggiornamento documenti).

`pymupdf_capture.py:123-125` emette **una primitiva per span** e scrive la riga
nell'id: `text:b{block}:l{line}:s{span}`. La riga tipografica è quindi già data
dalla sorgente. `_group_visual_lines` la scarta e la ricostruisce per
sovrapposizione delle y dei punti medi, confrontando ogni candidato **solo
contro il primo** elemento della riga.

**Misurato, non dedotto.** Sulle due pagine di prova i due raggruppamenti
divergono, e l'assemblaggio geometrico **fonde righe di blocchi diversi**:

| Pagina | span | righe geometriche | righe da sorgente | fusioni solo geometriche |
| --- | --- | --- | --- | --- |
| Dag p.48 | 102 | 54 | 75 | 21 |
| Dag p.164 | 76 | 50 | 75 | 25 |

Esempi, entrambi fusioni fra blocchi distinti: su Dag p.48 il titolo
`SOTTOCLASSI DEL RANGER` (`b0:l0`) finisce nella stessa "riga visiva" del corpo
`I ranger sono cacciatori...` (`b12:l0`); su Dag p.164 due intestazioni diverse,
`VANTAGGIO E SVANTAGGIO` (`b0:l0`) e `VANTAGGIO VS. DIFFICOLTÀ` (`b3:l0`). È la
sovra-fusione di `_cluster_rows` (State.md:30) ricomparsa nel consumer, ed è la
forma peggiore per questo lavoro: una "riga" a cavallo di due colonne non è
assegnabile a una banda.

Il caso che la funzione cita a propria giustificazione **non la giustifica**: i
sette span di Dag p.48 a y 410,89-411,01 sono un'unica riga di sorgente
(`b8:l2`), e ordinati per `x0` dentro quella riga danno il testo corretto. Il
difetto che quella docstring descrive esiste, ma nasce dalla **y** del sort
globale `(y0, x0)`, non dalla x: identificata la riga, la x basta.

Ordine dentro la riga: `span_index`. Divergere da `x0` è raro — 2 righe
multi-span su 6.335 (0,03%, cinque manuali) — quindi la scelta non è portante, e
`span_index` si prende perché è l'ordine che la sorgente dichiara.

**Conseguenza che va a verbale**: i giudizi a vista di reading order in
State.md:80 e :90 sono stati dati su output prodotti con l'assemblaggio
geometrico difettoso. Non è noto se e quanto questo li abbia cambiati, e questo
giro non è progettato per stabilirlo.

**Riserva chiusa, per non riaprirla.** La degenerazione del livello `dict`
(Kul p.233, 245 span `'.'`, State.md:62) non è un argomento per tenere
l'assemblaggio geometrico: le primitive sono le stesse nei due rami, e da
geometria degenere il raggruppamento geometrico non ricostruisce nulla di
meglio. Sui gutter la degenerazione è già intercettata a monte da
`too_few_wordy_lines`, che chiede ≥5 caratteri per riga fiancheggiante — con la
precisazione che lì "gestita" significa **nessuna banda emessa**, che su un
glossario a tre colonne reale è un falso negativo. Fuori dal perimetro di questo
giro; resta la milestone sul rilevatore di degenerazione in cattura.

## 6. Regola di accettazione

**Precondizioni.** Se una di queste cade, non si giudica nulla: l'artefatto è
rotto e il giro non è cominciato.

- **P0** — a flag spento, l'uscita è **identica** a quella di oggi. Il flag non
  deve poter cambiare Milestone 36 in silenzio.
- **P1** — i due invarianti auto-verificati (conservazione multiset dei
  caratteri non-spazio, integrità dei riferimenti, uscita `4`) passano su tutte
  le varianti e tutte le pagine. Nota: il multiset è **cieco all'ordine**
  (State.md:76) — passa contro qualunque ordinamento, e non è evidenza di
  qualità. È una guardia contro testo perso o duplicato, nient'altro.

**Il giro regge** se, giudicato a vista dall'utente sul `page.md` e non su
conteggi di primitive dentro banda:

- **A1 — nessun falso negativo su regione multicolonna reale.** Su nessuna
  pagina che contenga davvero una regione multicolonna, `page_bands.md` deve
  produrre il modo di fallire illeggibile — le due colonne concatenate riga per
  riga (il fallimento di DB p.99 che ha motivato Milestone 36). È l'errore
  squalificante, e non lo è per convenzione: non è recuperabile da nessun
  livello, perché Resolution non può emettere un candidato mai prodotto
  (State.md:82).
- **A2 — nessuna regressione contro `page_lines.md`** su una pagina dove
  `page_lines.md` è già corretto.

**Esclusione dichiarata ora, non dopo**: il difetto noto di DrW p.97 —
ordine a blocchi sbagliato per via dell'immagine che occupa mezza colonna — **non
conta come violazione di A1**, perché State.md:86 lo registra già come non
correggibile dentro `column_band`. Vale solo se si presenta nella forma prevista
al §4; una forma diversa è un fatto nuovo e va giudicata come tale.

**I falsi positivi si contano e si scrivono, non fanno fallire** — ma con una
precisazione che l'asimmetria di State.md:82 non copre. Quell'asimmetria vale
nell'architettura producer → Resolution → consumer, dove un falso positivo è
recuperabile perché Resolution lo rifiuta. **Qui non c'è nessuna regola di
Resolution per `column_band`**: il consumer è l'ultima fermata, e un falso
positivo arriva intatto nel markdown. Quindi in questo artefatto misuriamo il
comportamento congiunto di meccanismo + consumer ingenuo. Farli fallire sarebbe
giudicare il meccanismo per una regola che non esiste ancora; ignorarli
nasconderebbe una regressione vera. Si contano, si nominano, e A2 li intercetta
dove fanno danno.

## 7. Limiti dichiarati

- **Le pagine sono ancore di sviluppo, già viste, scelte da me.** Questo giro
  misura coerenza col campione su cui il meccanismo è stato costruito, non
  accuratezza. È la stessa distinzione che ha smontato l'«11 su 11»
  (State.md:54), e vale qui identica.
- **Nessun campione cieco, di proposito.** Con due o tre pagine non avrebbe
  potere statistico: il campione del 13 agosto, con sedici pagine e zero errori,
  limita il tasso di falso negativo solo sotto il 31% (State.md:102).
- **La configurazione non è mai stata guardata da nessuno.** Il meccanismo è
  cambiato dopo l'ultima verifica a vista (State.md:100), inclusi il ripristino
  di «vince la banda più profonda» (`7f839bc`) e il ritorno di M a 5
  (`619f4f8`). Le pagine vanno lette con i parametri di **adesso**; nessun
  numero ereditato dalle sessioni precedenti va riportato senza rimisurarlo.

## 8. Cosa succede dopo, nei due esiti

In **entrambi** i casi il giro si chiude scrivendo il risultato in `State.md`, e
**non propone un altro giro di misure dal proprio interno**. È la clausola
anti-avvitamento: le fasi 3 e 4 si sono avvitate esattamente così, e State.md:112
lo registra come cosa da non rifare.

- **Se regge**: il fatto va a verbale; la decisione se aprire la milestone
  `column_band`, e con quale criterio di uscita, resta all'utente e resta
  vincolata al terzo invariante mancante (State.md:76).
- **Se cade**: si scrive quale delle due condizioni è caduta e su quale pagina.
  Nessuna variante correttiva viene proposta qui — proporla dentro il giro che
  l'ha motivata è la forma dell'errore, non il rimedio.
