## L'obiettivo, che si rilegge e non si ricorda

`AGENTS.MD` §Obiettivo per intero. In breve: **PDF TTRPG → Markdown ed EPUB
semantici**, contenuto preservato, **e** immagini, sfondi ed elementi ripetuti
**sostituiti da note brevi che dicono cosa sostituiscono**, con gli asset in una
cartella referenziata.

La domanda che vale su qualunque proposta, inclusa quella che stai per fare:
**questo avvicina un EPUB leggibile, o solo la coerenza interna del meccanismo su
cui stiamo lavorando?**

## Cosa leggere, e cosa no

`CLAUDE.md`, `AGENTS.MD` e `ManReader_TwoChat_Agent_Workflow.md` **interi**.

Di `State.md`, la **sola Milestone 39** — contiene lo stato, i quattro modi in cui
una scheda esce male, la misura 69%/4%, e l'elenco aperto in ordine di quanto
blocca. Verifica di aver ricevuto la riga sentinella in fondo al file: se non
compare, la copia è troncata, fermati e dillo.

**Mai `State_Archive.md`.**

Poi i quattro verbali che riguardano le tabelle, tutti brevi:
`Esito_StrategiaTabella_v1.md`, `Esito_TabellaInIR2_v1.md`,
`Criterio_TabellaRisolvibile_v1.md` (registrato e **mai eseguito**),
`Campione_TabellaInIR2_v1.md`.

## Dove siamo

`main` a `a2f5e18`, suite 1369 verde. Sei producer wired. **IR 2 esiste** e produce
Markdown verificato: contratto, serializzazione validante, costruttore,
validatore, emettitore. Sa portare una griglia (`NodeIR2.structure`,
`TableIR2`, `CellIR2`) ma il meccanismo è **a default spento**, `--tables` lo
accende, perché il suo criterio è caduto.

## Il compito

**Costruire il producer delle regioni tabella.** Decisione dell'utente, con questa
ragione: avere una struttura in più prima di affrontare le schede mostro — e una
scheda **contiene** una tabella, quindi non è una pista parallela ma un pezzo di
cui la scheda è fatta (la colonna `PARTE × RESISTENZA` di Wil p.245).

### Il difetto da chiudere, misurato

Non i gutter: **la regione**. `table_candidate` usa `text/lines` da Milestone 20,
e quella configurazione:

- **taglia il 61% degli span** nelle proprie regioni (215 su 353);
- produce regioni che **inghiottono aree non correlate** — su Wil p.245 una sola
  regione copre STILI, ABILITÀ, TRATTI, AGGIUNTIVI e PARTI insieme.

`lines/lines`, la strategia di default:

- **non taglia mai una parola** (0 span su 35) e risolve tutto ciò che trova
  (8 su 8);
- ma **tace su 3 pagine utili su 5**.

Esito registrato: **affiancare**, raggiunto da una regola scritta prima
(`Esito_StrategiaTabella_v1.md`). Il campione utile era **5 pagine, non 12**, e va
citato con quel limite.

### Il precedente che esiste già, e il suo difetto

`extractor.py:159-175` (`_find_table_regions`) **affianca già le due strategie**:
prende come base le regioni `lines/lines` e ammette una regione `text/lines` solo
se supera `_is_valid_text_line_table_region` (`:205-226`). La direzione è quella —
`lines/lines` riferimento, `text/lines` raffina dentro.

**Non è trapiantabile così com'è**: la validazione è fatta di costanti fissate a
mano (3, 3, 8, 0,75, 0,5), e la posizione permanente dell'utente è che le soglie
geometriche si desumono dal documento. E `_text_block_covered_by_table` **non ha
test** — verificato con `grep -rln "covered_by_table\|reading_flow_table" tests/`.

Il repo ha però già ratificato una regola di subordinazione **senza soglia**:
`positive_intersection`, `overlap_ratio > 0` (Milestone 20).

## Cosa vale come argomento, e cosa no

**Non vale**: «il meccanismo è incompleto» senza una pagina in cui
quell'incompletezza produce output sbagliato. In questa sessione **tre criteri
pre-registrati sono caduti** e sei affermazioni sono state ritirate davanti a uno
sguardo.

**Vale**: un difetto osservato su una pagina reale, con il render accanto.

**Prima di qualunque misura che decida se una linea prosegue, registra scopo e
criterio di falsificazione per iscritto e committali in un commit che non contiene
codice** (`AGENTS.MD` §15). In questa sessione la pratica ha retto: un criterio
pre-registrato ha falsificato l'implementazione di chi l'aveva scritta.

## Trappole misurate in questa sessione, da non ripetere

- **Il repo ha già la risposta più spesso di quanto sembri.** Tre volte in una
  sessione Chat A ha proposto qualcosa che il progetto aveva già deciso e scritto:
  la porta di emissione delle note, i confini di colonna dai gutter, e il
  trattamento delle tabelle nel legacy. **Cerca prima di proporre.**
- **`--page N` è un indice posizionale**, non il numero stampato.
- **Due copie del progetto sul disco**: la cartella principale e i worktree.
- **Un conteggio non sostituisce uno sguardo.** In questa sessione una diagnosi è
  stata scritta senza aprire la pagina e tre sue affermazioni erano false.
- **Un criterio si giudica su come può fallire.** Prima versione: tre criteri che
  non potevano fallire. Seconda: due che non potevano passare. Terza: uno.
- **Il testo viene dalla sorgente.** Riga da `line_index`, paragrafo dal blocco più
  l'evidenza testuale, ordine nella riga da `span_index`. La geometria posiziona e
  controlla, mai ricostruisce.

## Cosa resta aperto e dichiarato, da non riscoprire

La fusione di paragrafi quando si sottrae testo dal flusso — colpirà ogni
meccanismo che tolga primitive; nessun invariante di conservazione dei
**caratteri** nel percorso IR 2, che garantisce gli **id**; l'ancora delle note
d'asset per `y` che sbaglia colonna; `text.heading` senza criterio;
`text.labelled_entry`, la cui ritrattazione è stata a sua volta ritirata; la
rimozione dell'arredo; la milestone di uscita dallo shadow mode, che non esiste.

## Cosa consegnare

Una proposta sola, con: il difetto osservato che la motiva **con la pagina**, il
criterio di accettazione scritto prima, il perimetro chiuso, e cosa resta
esplicitamente fuori. Poi il giro di revisione a due chat — prima metodologico,
poi architetturale, in conversazioni separate.

Non toccare `table_candidate` senza dichiararlo: ha oracoli propri (Milestone 20,
Dag p.137, 114/57 primitive) da rieseguire.
