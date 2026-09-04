# Istruzione della proposta esterna «lo statblock come classe di asset»

Verifica delle affermazioni della proposta contro il repo, alla revisione
`3a2238d` — la stessa che la proposta dichiara di aver letto.

**Cos'e' questo documento.** La proposta si chiude (§10) dicendo che non e'
pronta per un giro di revisione: tutte le sue affermazioni sul repo sono
dichiarate A PRIORI, e vanno «ridotte a cio' che Chat A ha verificato in
proprio». Questo file e' quella riduzione. Non e' una proposta: non chiede di
aprire niente, e la sua unica raccomandazione operativa (§7) e' di non aprire.

**Perche' e' nel repo, contro la prassi.** I documenti di progettazione stanno
fuori dal repo (Milestone 33, 34, 35, 36: «non nel repo, stessa prassi»). Questo
non e' un documento di progettazione ma un verbale di verifica di fonte esterna,
ed e' la sola forma in cui le correzioni qui sotto sopravvivono alla sessione che
le ha prodotte. Se l'utente estende la prassi anche ai verbali, si toglie: nessun
altro artefatto ne dipende.

**Cosa ho letto**: `AGENTS.MD` per intero, `ManReader_TwoChat_Agent_Workflow.md`,
i cinque `Criterio_*.md`, `README.md`, `deduplicator.py`, i modelli
(`page_analysis_model.py`, `primitive_model.py`), i sei producer,
`job_page_analysis_runner.py`, `scripts/prototype_vertical_slice_page.py`,
`scripts/milestone35_oracle_cases.csv`, e di `State.md` le Milestone 35, 36, 37.

**Cosa non ho potuto verificare, e vale come limite di tutto il resto**: in questo
ambiente non esiste nessun PDF di benchmark. **Nessuna misura e' stata eseguita e
nessuna era eseguibile.** Ogni affermazione quantitativa qui sotto e' una citazione
di misure gia' a verbale nel repo, mai una misura nuova. Non ho letto il plugin
`arrowedisgaming/arroweds-adversary-bank`: tutto cio' che la proposta dice dello
schema YAML, del campo `raw`, della formula dell'`id` e della regola
environment = assenza di `hp`/`stress` resta riportato dal suo autore e non
verificato qui.

---

## 1. La correzione che viene prima di tutte le altre: §0 non regge piu'

La proposta poggia il proprio diritto di esistere su una tesi sola (§0): che
avvicini un markdown leggibile perche' «rende leggibile una classe di pagine
senza passare dal reading order multicolonna, **che e' il punto in cui il
progetto e' fermo**».

Il progetto non e' fermo li'. Alla revisione `3a2238d` — quella che la proposta
dichiara di aver letto — Milestone 37 e' chiusa: il producer `column_band`
esiste (`page_analysis_column_band.py`), ha la sua misura satellite
(`page_analysis_column_band_measurements.py`), ed e' montato nel job
(`job_page_analysis_runner.py:69-70`), che passa **da cinque a sei producer**.
`State.md:917`:

> la pipeline nuova ordina il testo per colonne, e su un campione **cieco** di 10
> pagine — seed 20260817 — il giudizio dell'utente e' che l'incolonnamento e'
> corretto. [...] E' la prima volta che la pipeline nuova produce un ordine di
> lettura che una persona riconosce su pagine mai viste prima.

La proposta cita quel commit nella propria intestazione, per soggetto —
«Milestone 37 chiusa: column_band e' un producer, ha la sua misura satellite ed
e' wired» — e dichiara nella stessa riga di non aver letto `State.md`. E' li' che
l'errore entra, e non e' una svista di dettaglio: §0 e' l'unico argomento della
proposta, e senza di esso non ha risposta alla domanda del workflow.

Una risposta diversa esiste, e viene dal repo, non dalla proposta — §2 qui sotto.
Ma va costruita da capo, non recuperata da §0.

## 2. Il caso e' gia' registrato, e da un lato che la proposta non guarda

`State.md:903`, chiusura di Milestone 36, appunto per una futura passata di
raffinamento (non aperta, non numerata):

> le schede statistiche mostro nel bestiario (es. `DB.pdf`,
> GUERRIERO/ARCIERE/CAMPIONE, riquadro a colonne non allineate) non sono
> `table_candidate` (nessuna griglia regolare, verificato per ispezione visiva)
> ne' riconducibili a un riquadro puramente visivo
> (`embedded_visual`/`interior_visual_frame`): contengono testo strutturato a
> **campi etichetta:valore da preservare**, reso oggi con sfondo decorativo che
> andrebbe rimosso in resa, mantenendo la struttura leggibile. Nessuna decisione
> presa: possibile candidato per un futuro `structural_kind` dedicato **o per un
> trattamento di rendering separato dalla classificazione geometrica**. Tocca il
> quarto punto bloccante di Milestone 33 (`structural_kind` unico vs. distinzione
> corpo/struttura interna).

Il repo era gia' arrivato, da solo e per ispezione visiva, a quattro delle
intuizioni della proposta: la classe esiste, non e' una tabella, non e' un
riquadro visivo, e il suo contenuto e' `etichetta: valore` — che e' letteralmente
il segnale del livello 2 di §5. La convergenza e' reale e va detta.

Ma l'appunto contiene **un ramo che la proposta non nomina mai**: «trattamento di
rendering separato dalla classificazione geometrica». Cioe': lo sfondo decorativo
si toglie e la struttura a campi si preserva **in resa**, senza nessun producer
nuovo, nessun vocabolario, nessuno schema, nessun riconoscimento di campi. E' il
ramo piu' economico dei due, ed e' quello che la proposta salta per andare
direttamente al piu' costoso.

Non basta: la classe ha gia' un'etichetta e quattro casi ispezionati a occhio,
`scripts/milestone35_oracle_cases.csv`, `label = modulo_ui_statblock`:

| manuale | pagina (indice) | cosa e' |
| --- | --- | --- |
| Dag | 24 | scheda personaggio **esempio** |
| Lan | 36 | riquadro statistiche mech RAIJIN |
| DB | 124 | scheda personaggio Dragonbane **vuota** |
| DB | 124 | idem, secondo cluster |

Tre casi su quattro **non sono statblock da bestiario**: sono schede personaggio,
due delle quali a campi vuoti. La proposta descrive un formato di avversario con
valori pieni. La classe che il repo ha etichettato e la classe di cui la proposta
parla si sovrappongono ma non coincidono, e il caso da cui la proposta nasce —
lo statblock d'avversario Daggerheart — **non e' fra i quattro casi che qualcuno
in questo progetto ha guardato**.

## 3. Verdetto sulle voci «A PRIORI»

Sono due elenchi: i sei punti di §9 e i tre di §3. Si sovrappongono in parte; qui
sono fusi e ordinati per peso, non per elenco di provenienza.

### 3.1 «che una classe di asset `statblock` stia nel perimetro corrente» — NO, ma non e' vietata

`AGENTS.MD:592` elenca le attivita' non autorizzate **senza decisione
architetturale dedicata**. `statblock` non c'e' per nome; il vicino piu' prossimo
e' `AGENTS.MD:614`, «tabelle, callout o liste come nuovo comportamento attivo»,
che ha esattamente la stessa forma (una classe di contenuto strutturato che
diventa comportamento). Il progetto e' in Modalita' I (`AGENTS.MD:5`) e una
classe di asset nuova e' una decisione di Modalita' P.

Quindi: non proibita, non avviabile cosi' com'e'. Serve la decisione dedicata che
il titolo di quella sezione nomina.

### 3.2 «che un producer `statblock` sia ammissibile accanto agli altri» — la regione si', il field bag no

E' la correzione architetturale piu' importante, e taglia la proposta in due.

**La regione e' ammissibile.** La cardinalita' multipla dei candidati e' gia'
libera (Milestone 33), `_STRUCTURAL_KIND_PATTERN`
(`page_analysis_model.py:32`) accetta qualunque nome minuscolo con namespace,
quindi `layout.statblock` validerebbe, e sei producer sono il precedente.

**Il field bag non lo e'.** `page_analysis_model.py:108-112`, docstring di
`RegionCandidate`:

> A candidate is not an approved layout fact, confidence score, ranking,
> ownership claim, coverage claim, **semantic classification**, or decision.

e `AGENTS.MD:168`: «`proposed_structural_kind` deve restare strutturale: valori
come `layout.side_band` sono ammessi, mentre `marginalia` non e' uno structural
kind». Riempire `hp`, `stress`, `thresholds`, `motives` e' classificazione
semantica senza margini di lettura. Il §1 e il §2 della proposta — render → campi
— **non possono stare in un producer**: stanno a valle di Resolution, dove il
progetto non e' ancora arrivato.

La proposta e' quindi due proposte con costi e collocazioni diverse, e le tratta
come una:

- **§4, la regione per inviluppo di ancore**: forma ammissibile in un producer,
  e per giunta della forma che il progetto preferisce — emette una misura, non un
  booleano, come `ColumnBandMeasurements` (Milestone 33/37);
- **§1-§2, i campi in YAML**: semantica, fuori dal perimetro dei producer, e
  a valle di un livello che oggi ha **una** regola (Milestone 34,
  `resolution_page_candidates.py`).

**Un fatto che nessuna delle due parti dice, e che va dichiarato**: oggi nessun
producer legge il **contenuto** del testo. L'unico accesso a `TextPrimitive.text`
nei sei producer e' `page_analysis_column_band.py:1087`, che ne conta i caratteri
non-spazio. Un producer a vocabolario sarebbe il primo a leggere **parole**. Non
viola un invariante scritto, ma sfiora `AGENTS.MD:223` («Non introdurre hardcode
su manuale, pagina, filename, titolo o **parola** come soluzione primaria»): la
via d'uscita e' che il vocabolario sia dato e non codice, che e' esattamente cio'
che §5 sostiene — ma allora va detto anche che il dato va prodotto e mantenuto
per ogni manuale, e §5 lo stima per sistema (vedi §5 qui sotto).

### 3.3 «che un producer sia ammissibile senza la Resolution mancante» — la premessa e' sbagliata, il blocco e' un altro

Resolution **non manca come livello**: Milestone 34 l'ha progettata e ne ha
scritto la prima regola (`resolution_model.py`,
`resolution_page_candidates.py`, commit `cc89248`). Cio' che manca e' una regola
di Resolution per `column_band` — condizione condivisa con `table_candidate`,
`page_covering_visual` e `page_edge_visual` da Milestone 21/23/24, quindi non
un'eccezione (`State.md`, chiusura Milestone 37).

Il blocco vero e' un altro, ed e' peggiore per la proposta. `AGENTS.MD:575`:

> **Stato: la milestone di uscita [dallo shadow mode] non esiste.** [...] E' una
> decisione aperta e bloccante [...] Finche' resta tale, **ogni nuova milestone
> diagnostica allunga la distanza dal primo output verificabile della pipeline
> nuova** senza che nessuno abbia deciso quando quella distanza va chiusa.

Il test di §7 e' una nuova milestone diagnostica. «Costa un pomeriggio» e' vero
come costo di calendario e falso come costo di progetto: la cosa di cui questo
repo ha gia' troppo, e lo ha messo per iscritto, sono le diagnostiche a basso
costo unitario.

### 3.4 «che il meccanismo del deduplicatore sia riusabile per template a contenuto variabile» — NO, verificato

`deduplicator.py:232-248`: `_hash_image` e' `md5` dei byte grezzi dell'immagine,
`_hash_vector` e' `md5` del contenuto SVG. Il docstring (righe 17-21) lo dice
senza margine: «due asset identici estratti da pagine diverse avranno lo stesso
hash **se il contenuto PDF e' identico**». Nessun confronto strutturale, nessuna
tolleranza, nessuna nozione di template. Identita' esatta e basta.

E in piu' e' nella pipeline **legacy**: importa `ImageBlock, PageData,
VectorBlock` da `extractor.py`, e `AGENTS.MD:139` dichiara «`PageData` e' legacy
e non e' raw canonico».

Il meccanismo di ricorrenza della pipeline nuova e' `content_digest`
(`scripts/verify_page_covering_visual_content_digest_recurrence.py`), anch'esso a
digest, e il consumer document-level che lo userebbe e' esplicitamente **rinviato
e non costruito** (`State.md`, §Stato operativo).

Conseguenza diretta: **il segnale su cui §5 fonda il livello 2 — «uno statblock
non compare una volta, compare in un bestiario con lo stesso template e contenuto
variabile» — non ha in questo repo nessun meccanismo su cui appoggiarsi**, in
nessuna delle due pipeline. Va costruito da zero. Il livello 2 costa piu' del
livello 1, non meno, ed e' l'inverso di come §5 lo presenta.

### 3.5 «che le ancore diano segnale netto sui manuali reali» — non misurabile qui, e il precedente e' peggiore di quanto la proposta assuma

Non misurabile in questo ambiente: nessun PDF presente.

Ma l'esperimento piu' vicino e' gia' stato fatto. `State.md:543`, Milestone 35,
test di fattibilita' richiesto dall'utente: il rilevatore di callout della
pipeline legacy — **un pattern testuale**, titolo maiuscolo breve + corpo ≥40
caratteri — separa 7 casi su 9 dell'oracolo. E subito dopo, nello stesso
paragrafo:

> **Concordanza valutata post-hoc sullo stesso insieme di 9 casi**, dopo rimozione
> di un fallback [...] che produceva un falso positivo su Kul p.0 — **non una
> stima fuori campione**. [...] **Non un discriminante pronto** — un candidato per
> un futuro producer, non deciso qui.

E i due falsi negativi sono `DB p.124 ×2`, «modulo a campi vuoti, nessun
paragrafo di corpo per costruzione»: cioe' proprio le schede a campi vuoti, che
sono la meta' dei casi statblock etichettati nel repo e che **nessuna ancora di
valore** (`N/M`, `+N`, `NdM+K`) puo' trovare, perche' i valori non ci sono.

Quindi il precedente non dice «segnale promettente da confermare»: dice che un
test di questa forma su questo repo ha gia' prodotto una volta un numero che
sembrava buono ed era post-hoc, e che la classe contiene per costruzione un
sottoinsieme su cui l'approccio a valori non puo' funzionare.

### 3.6 «l'inversione di dipendenza con `column_band`» — il problema si dissolve, ma per un motivo diverso da quello che la proposta teme

La proposta (§4, corollario) teme che una regione statblock riconosciuta senza
`column_band` diventi *evidenza* per `column_band` invece che sua consumatrice, e
rinvia la questione a `Criterio_SubordinazioneProbatoria_v1.md` — che pero'
riguarda tutt'altro: quel criterio decide se `_is_subordinate` usi lo `span` o
gli estremi probatori dentro `column_band`, e non parla di rapporti fra producer.

La regola che governa e' `AGENTS.MD:174`:

> L'isolamento fra producer e' una proprieta' voluta, non un limite da superare:
> la relazione fra candidati di producer diversi si decide in Resolution o nel
> consumer, **mai dentro un producer**.

ratificata due volte (`AGENTS.MD:175`, Milestone 24 e 30). Sotto quella regola non
c'e' nessuna inversione: un producer `statblock` e `column_band` restano isolati,
e a metterli in relazione e' il consumer — che e' esattamente cio' che
`Criterio_InterruzioneCorridoio_v1.md` §2 gia' fa con `embedded_visual`, che
interrompe le bande dal consumer. Il pattern esiste, e' ratificato, ed e' in
esercizio.

Questa e' una **semplificazione a favore della proposta**: il punto che il suo
autore segnalava come il piu' rischioso e' l'unico gia' risolto.

### 3.7 le affermazioni negative — due implicite, entrambe false

L'autore si vieta le affermazioni negative e fa bene, ma due gli sfuggono.

La prima e' §0 («il punto in cui il progetto e' fermo»), gia' trattata in §1.

La seconda e' §3, «Perche' non e' un'architettura nuova»: il ciclo estrai →
referenzia → rirenderizza citato da `README.md` e' **della pipeline legacy**
(`README.md` descrive `pdf_to_epub v1.1`), e la re-resa inline delle tabelle e'
un `<table>` **nell'EPUB**, non in markdown. Nella pipeline nuova la fetta
verticale estrae **solo asset raster**, per scelta esplicita
(`scripts/prototype_vertical_slice_page.py`, docstring righe 37-40: i vettoriali
sono esclusi), e `AGENTS.MD:173` vieta la strada delle tabelle: «Un candidato
tabella non rimuove testo e non produce CSV definitivo prima della resolution».

Quindi §3 e' vero della pipeline che si sta sostituendo e non ancora vero di
quella che si sta costruendo. La «quarta classe di asset» non si aggiungerebbe a
tre classi esistenti: si aggiungerebbe a una.

## 4. Cosa la proposta aggiunge, che il repo non aveva

Va detto per intero, perche' §1-§3 sono quasi tutte correzioni.

1. **L'inviluppo di ancore (§4)**, cioe' non cercare i bordi ma ricavarli dalla
   densita' di token ad alta specificita'. E' un capovolgimento che il repo non
   aveva formulato, ed e' della forma giusta: produce una misura, non un
   booleano, e non dipende dall'ordine, quindi non dipende da `column_band`.
   Sopravvive alla verifica come **idea di producer**, non come pipeline di campi.
2. **Il principio del fallimento rumoroso e del testo grezzo conservato (§6)**.
   Coincide con due regole gia' scritte — `AGENTS.MD:45` «nessuna invenzione del
   contenuto mancante» e `AGENTS.MD:183` «Nessuna esclusione puo' essere
   silenziosa» — e ne e' la forma applicata a un field bag. **Va registrato
   adesso**, come vincolo su qualunque futura estrazione a campi, indipendentemente
   dal fatto che questa linea si apra: costa una riga oggi e una milestone dopo.
3. **Il pericolo dell'`id` (§6)**: se un giorno si emette YAML per quel plugin, il
   campo `id` non va scritto, perche' un `id` esplicito vince sull'assegnazione
   `??=` e condivide lo stato fra tutte le istanze nel vault. Verificato dal suo
   autore sul sorgente del plugin, **non da me**. Costa zero registrarlo, e non e'
   scopribile da questo lato.
4. Un consumatore reale a valle del formato. Ma §8 lo dichiara gia' come
   beneficio e non argomento, e la domanda del workflow e' d'accordo: non entra
   nella valutazione.

## 5. Un costo che la proposta non vede: la lingua

I manuali di benchmark sono **edizioni italiane**. Due citazioni di testo
interno a `Dag.pdf` presenti nel repo lo mostrano: `SOTTOCLASSI DEL RANGER`
(Dag p.48, `State.md:128`) e `Capitolo 1: Guida Aggiuntiva per i Giocatori`
(Dag p.84, `Criterio_WiringColumnBand_v1.md` §2). L'esempio di bestiario di
`State.md:903` e' `GUERRIERO/ARCIERE/CAMPIONE` da `DB.pdf`. Le sigle sono la
radice del nome file (`scripts/`). Per alcuni manuali il titolo esteso e'
registrato — `DB` e' Dragonbane (`scripts/milestone35_oracle_cases.csv:9-10`,
«scheda personaggio Dragonbane vuota») e `Lan` e' Lancer (`State.md:509`) — ma
**«Daggerheart» non compare in nessun file del repo**: che `Dag.pdf` sia quel
manuale e' coerente con tutto cio' che si legge, non e' scritto, e non lo affermo.

Il vocabolario del livello 1 (`Vulnerable`, `Restrained`, `Melee`, `phy`,
`Halberd`) e' inglese e viene da un plugin inglese. Conseguenze:

- **le ancore che sopravvivono alla traduzione sono quelle sintattiche** (`N/M`,
  `+N`, `NdM+K`), non quelle lessicali. Che e' un argomento per provare prima il
  segnale strutturale del livello 2 che il vocabolario del livello 1 — l'inverso
  della raccomandazione di §5;
- «un JSON per sistema» diventa «un JSON per sistema **e per edizione
  linguistica**», e la stima «un JSON per manuale, ~un'ora» va riferita alla
  coppia (sistema, edizione), non al sistema;
- serve in piu' una mappa etichetta-italiana → chiave-inglese che la proposta non
  prevede, perche' assume che le etichette del PDF siano i nomi dei campi;
- **§8 si indebolisce ma non cade**: lo YAML emesso resterebbe valido per il
  plugin (le chiavi restano inglesi), ma «lo stesso artefatto» non e' vero — il
  lessico italiano serve all'estrazione e non serve al render.

## 6. Se il giro si facesse, la forma che dovrebbe avere

Non lo raccomando (§7), ma la forma va fissata comunque, perche' il modo in cui
questo test puo' fallire e' gia' documentato nel repo.

`AGENTS.MD:235` (§Regole operative, punto 15) impone di registrare **prima di guardare i dati** il
criterio di falsificazione (statistica, soglia, ambito, esclusioni) e il modello
nullo con la sua debolezza dichiarata, e aggiunge il vincolo che conta qui:

> Il criterio deve vincolare esplicitamente **il caso da cui l'affermazione e'
> nata**, non un caso qualsiasi del campione.

Il caso da cui questa affermazione e' nata e' lo statblock d'avversario
Daggerheart. Come mostra §2, **quel caso non e' fra i quattro che qualcuno in
questo progetto ha guardato**: Dag p.24 e' una scheda personaggio. Quindi il
punto 14 della stessa sezione (`AGENTS.MD:230`) si applica per intero — se una proposta asserisce
cosa mostrano visivamente delle pagine, quelle pagine si ispezionano **prima** di
progettarci attorno la diagnostica, «non dopo (lezione di Milestone 35: la
premessa d'origine, mai verificata visivamente, si e' rivelata fattualmente
sbagliata dopo sette giri di revisione basati solo sui numeri)».

Precondizioni, in ordine, prima di qualunque riga di codice:

1. **trovare e guardare** una pagina di bestiario Daggerheart in `Dag.pdf`, e
   registrare che esiste. Se non esiste, la proposta perde il proprio caso
   d'origine e va riscritta sul caso DB del bestiario, che invece e' ispezionato;
2. dichiarare il **modello nullo** e la sua debolezza: il nullo ovvio e' «stesso
   conteggio di ancore su pagine di sola prosa dello stesso manuale», e la sua
   debolezza dichiarata e' che i negativi difficili non sono la prosa media ma la
   prosa che **cita** le meccaniche — che e' il rischio che §6 della proposta
   segnala e non misura;
3. **campione estratto con regola dichiarata prima e guardato dopo**, escludendo
   per costruzione le pagine gia' usate come ancore per altri meccanismi
   (`Criterio_WiringColumnBand_v1.md` §3 ne e' il modello, elenco di esclusioni
   compreso);
4. le **esclusioni fissate prima**, per lo stesso motivo del punto 15: fissarle
   dopo permette di scartare i casi scomodi;
5. il criterio deve poter **chiudere la linea**, non solo aprirla: §7 lo dice
   («cade qui»), e la prassi del repo aggiunge la clausola che i cinque
   `Criterio_*.md` portano tutti in fondo — «nessun altro giro viene proposto
   dall'interno di questo».

Precondizione d'ambiente, banale e bloccante: **serve `Dag.pdf`**. In questa
sessione non c'e', e nessuna delle misure di §7 e' eseguibile.

## 7. Raccomandazione

**Non aprire la linea adesso, e non partire dal test di §7.** Tre ragioni, in
ordine di peso.

1. **La proposta non ha piu' una risposta alla domanda del workflow.** Il suo
   unico argomento (§0) era che sbloccava il punto in cui il progetto e' fermo, e
   quel punto e' stato sbloccato da Milestone 37 nella stessa revisione che la
   proposta ha letto (§1). Una risposta nuova esiste, ma e' quella di
   `State.md:903`, e punta altrove: quelle pagine oggi escono con lo **sfondo
   decorativo non rimosso** e la struttura a campi non preservata. E' un problema
   di **resa e di Resolution**, non di rilevamento — e l'appunto offre gia' il
   ramo «trattamento di rendering separato dalla classificazione geometrica», che
   non richiede ne' producer, ne' vocabolario, ne' schema (§2).
2. **La decisione aperta e bloccante del progetto e' un'altra**, e questo giro la
   allontanerebbe: `AGENTS.MD:575` dice che la milestone di uscita dallo shadow
   mode non esiste e che ogni nuova milestone diagnostica allunga la distanza dal
   primo output verificabile (§3.3).
3. **Il test di §7 nella forma proposta ripeterebbe un errore gia' fatto**: un
   test di pattern testuale su questo oracolo e' gia' stato eseguito, ha dato 7/9
   post-hoc sullo stesso insieme, ed e' registrato come «non un discriminante
   pronto»; e i suoi due falsi negativi sono la meta' vuota della classe, su cui
   le ancore a valore non possono funzionare per costruzione (§3.5).

**Se e quando la linea si apre**, si apre cosi': sul ramo gia' registrato in
`State.md:903` (`structural_kind` dedicato **vs** trattamento di resa — che e' il
quarto punto bloccante di Milestone 33, non una domanda nuova); sul bestiario
`DB.pdf`, che e' gia' ispezionato, invece che su Daggerheart che non lo e'; con
le sole ancore **sintattiche**, perche' quelle lessicali non sopravvivono
all'edizione italiana (§5); e con la regione come unico oggetto in gioco, perche'
i campi sono semantica e non stanno in un producer (§3.2).

**Due cose vanno registrate adesso a costo zero**, e non dipendono da nessuna di
queste decisioni: il vincolo di fallimento rumoroso su qualunque futura
estrazione a campi (mai assegnare male un campo in silenzio; conservare il testo
grezzo accanto al parsed), e il divieto di emettere il campo `id` se un giorno si
produce quello YAML.

## 8. Cosa resta non verificato, da me

- **Tutto il plugin.** Schema, campi, formula dell'`id`, campo `raw`, regola
  environment = assenza di `hp`/`stress`: riportati dall'autore della proposta,
  fuori dal perimetro di repository di questa sessione, non verificati qui.
- **L'identita' di `Dag.pdf`.** Del suo titolo esteso il repo registra solo il
  nome file; «Daggerheart» non compare da nessuna parte (a differenza di
  Dragonbane e Lancer, che compaiono).
- **Se `Dag.pdf` contenga statblock d'avversario.** Nessuno in questo progetto ha
  guardato una pagina di bestiario Daggerheart, per quanto risulta dai documenti.
- **Qualunque misura.** Nessun PDF in questo ambiente; nessuna misura eseguita,
  nessun numero nuovo prodotto. I numeri citati sono tutti gia' a verbale nel
  repo, con la loro fonte.
