# Criterio — l'arredo esce dal flusso, e il numero di pagina diventa provenienza

Sostituisce la v2, non eseguita. Due giri di revisione indipendente — uno cieco,
uno con il repo — hanno prodotto le correzioni del §0.

## 0. Che cosa cade dalla v2

**Il criterio non poteva scegliere: aveva un veto e nessun pavimento.** «Regge se
nessuna voce tolta è contenuto» è passato a pieni voti dalla **regola che non
toglie niente**. Rilievo della revisione cieca. → §5 ha ora un pavimento.

**La barra a zero su 12 pagine era quasi cieca.** Il difetto misurato della
regola B sta su al più 2 pagine su 50: pescandone 2 per manuale, la probabilità
di ritrovarlo è **~8%**. La procedura scritta dopo aver trovato quel difetto lo
avrebbe lasciato passare nove volte su dieci. → §5 campiona le **voci**, non le
pagine.

**Nessuno guardava il testo che resta.** `State.md` Milestone 39 mette al secondo
posto fra gli aperti: «la fusione di paragrafi quando si sottrae testo dal
flusso: succederà a ogni meccanismo che tolga primitive, **l'arredo per primo**».
Il controllo di conservazione è cieco per costruzione — la fusione cambia i
confini, non i caratteri — e il giudizio guardava solo le voci tolte. → §5 include
la **giunzione**.

**Un'affermazione mia era falsa sul codice.** La v2 diceva «stesso cancello delle
note d'asset»: `ir2_markdown.py:170` è `if node.kind != KIND_ASSET_NOTE: return
True`, cioè ogni nodo che non sia una nota va nel corpo. Usare quel cancello
richiede **cambiarlo**, e l'argomento per farlo è al §6.

**La regola B è ritirata.** Contraddiceva il precedente da cui prendeva il numero:
`extractor.py:3258` usa il 25% **solo ai bordi** e il **60% nel corpo**
(`min_body`), e B portava il 25% ovunque. Il suo unico fallimento misurato è
esattamente ciò che quell'asimmetria previene. E la linguetta verticale, l'unica
cosa che B comprava, è già un fatto del documento in produzione:
`page_analysis_column_band.py:318` consuma `TextPrimitive.direction`.

**Una correzione dell'utente, e vale più delle altre.** L'argomento con cui
entrambi i revisori declassavano questo lavoro — «arredo 5 pagine su 20, mai
causa dominante» — poggia su un numero che **non misura il fenomeno**: l'utente
non ha segnalato il clutter di pagine e capitoli perché **non era nello scope
della verifica**, ed era presente **su ogni pagina guardata**. Il 5/20 è un
pavimento, non una misura, e `Esito_FormaMancante_v1.md` va letto con questa
riga accanto.

**E una semplificazione proposta cade su un fatto.** La revisione col repo
suggeriva di misurare la fascia bassa **da sola**: se bastasse, l'apparato
document-level sarebbe superfluo. Misurato: non basta. Su Lan la fascia senza
ricorrenza tira dentro `+1`, `.`, `La`, `PNU Classe Student`; con la ricorrenza
restano 7 slot, tutti arredo. Il document-level è portante.

## 1. La regola, a due rami

### Ramo 1 — l'etichetta di pagina, che è un fatto e non una soglia

Il PDF **dichiara** il numero stampato: `page.get_label()` di PyMuPDF. Cinque
manuali su sei del corpus lo dichiarano.

> Nella fascia bassa, un testo che **contiene l'etichetta della sua pagina** e non
> è più lungo di essa di oltre tre caratteri **è** il numero di pagina.

Nessuna ricorrenza, nessuna percentuale, nessun parametro tarato. Misurato su
sei manuali, 40 pagine ciascuno: **DIE 39/40, DB 33/40, Lan 38/40, SV 39/40,
Fab 40/40**; Wil non dichiara etichette e cade nel ramo 2. Il margine dei tre
caratteri esiste perché Lan stampa `[99]` per l'etichetta `99`.

**E il numero non si butta: diventa provenienza.** `PageIR2` guadagna
`page_label`, preso da `get_label()` — additivo, e disponibile **anche dove il
testo non viene riconosciuto**, perché il fatto non dipende dal riconoscimento.
L'uscita dice quindi di quale pagina stampata si tratta invece di avere un `329`
in mezzo a un paragrafo. Indicazione dell'utente: referenziare il numero serve a
sapere che pagina si sta trattando.

Chiude di sbieco anche la **terza numerazione** che è già costata un giro di
etichette: `idx`, pagina del file, numero stampato — l'ultima finora dichiarata
«non verificata e da non citare».

### Ramo 2 — la ricorrenza, dove l'etichetta non c'è o non basta

> Uno slot esce dal flusso se sta nell'**8% inferiore** della pagina ed è
> occupato su almeno il **25%** delle pagine del documento.

Entrambi i numeri sono di `extractor.filter_repeated_blocks`, nei ruoli che il
legacy gli dà — la fascia restringe alla zona, il 25% è la soglia **di quella
zona**. Non sono numeri miei. Prende filigrane, intestazioni correnti, e i numeri
di pagina dei manuali senza etichetta.

Solo la fascia bassa: quella alta tira dentro corpo su tre manuali su sei. Il
prezzo è che i titoli correnti in cima restano, ed è il verso giusto in cui
sbagliare.

## 2. Che cosa succede a ciò che esce

Il nodo **resta** — `ir2_validate` esige la copertura — e cambia la resa: fuori
dal corpo, dentro `review_ir2.md` con il suo testo. Il writer di quel file oggi
stampa solo note d'asset e va esteso, altrimenti il §5 non è materialmente
eseguibile.

## 3. Il campione

**12 voci rimosse**, non 12 pagine, estratte dai **dieci manuali mai usati** del
corpus, seed `20260829` dichiarato qui prima dell'estrazione. Stratificate: metà
fra il 25% e il 40% di ricorrenza, metà sopra — le decisioni rischiose sono
quelle vicine alla soglia, e un campione di pagine le vedrebbe meno spesso
proprio perché sono rare.

I sei manuali del §0 e del §1 sono **spesi**: cinque formulazioni sono state
tarate su quelli, e la cecità alle pagine non basta quando l'adattamento è a una
tipografia.

## 4. Come si giudica

**Due etichettatori, gerarchia dichiarata.** Un **agente** riceve il render nudo
e le voci, **senza sapere quale meccanismo le abbia prodotte né quale esito sia
atteso**, e per ognuna dice `arredo`, `contenuto`, oppure **`incerto`** — l'opzione
che la v2 aveva tolto e che sotto una barra a zero è l'unico canale che porta i
dubbi all'umano. **L'utente decide**, e guarda: tutte le voci `contenuto` o
`incerto`, più **un terzo** di quelle `arredo`, scelto a caso.

Il cieco sull'esito regge; il cieco sul **meccanismo** no e va dichiarato debole:
sotto il ramo 2 le voci sono tutte in fondo alla pagina, e il meccanismo si
inferisce dall'elenco. L'accordo si riporta come tabella **2×2**, non come un
numero solo.

## 5. Pass/fail — un veto **e** un pavimento

> **Veto.** Cade se una sola voce tolta è giudicata `contenuto`.
>
> **Pavimento.** Regge solo se toglie almeno **tre quarti** delle occorrenze di
> numero di pagina e di filigrana presenti nelle pagine del campione, contate
> dall'utente.

Il pavimento esiste perché la v2 poteva essere superata dalla regola nulla. Il
veto è a zero perché l'errore è perdita di contenuto, e la ragione è di
attenzione più che di informazione: un paragrafo finito in review è **invisibile**
a chi legge, un'intestazione rimasta nel corpo è un fastidio **visibile**.

> **La giunzione.** Per ogni voce tolta si guarda il paragrafo immediatamente
> **sopra e sotto**. Cade se due paragrafi si saldano male dove l'arredo li
> separava.

È il difetto che `State.md` dichiara atteso per ogni meccanismo che sottragga
testo, e nessun'altra clausola può vederlo.

**Se cade**: non si esegue il ramo 2 in altra forma senza un criterio nuovo. Il
ramo 1 non ha parametri, quindi una sua caduta è un difetto d'implementazione,
non di taratura.

## 6. Perché non serve una decisione architetturale dedicata

La lista gated vieta l'«esclusione automatica di marginalia». L'argomento non è
che il meccanismo non pronunci quella parola — sarebbe lessicale — ma che **il
cancello di resa è già aperto**: `5bbb5f5` ha deciso che gli asset il cui
candidato Resolution non ha accettato non entrano nel corpo, «il nodo continua a
esistere e a filtrare è la resa», senza decisione dedicata. `AGENTS.MD` §«Aprire
uno stadio non è estenderlo» rende additiva l'estensione ai nodi di testo.

**La differenza va dichiarata e non nascosta**: il cancello d'asset chiave su
`resolution`, cioè su una decisione che Resolution ha preso su un candidato. Qui
non c'è candidato e non c'è Resolution, quindi **niente potrà rifiutare questa
esclusione**. È la ragione per cui il §5 ha un veto a zero e la giunzione: se
nessuno può rifiutare a valle, il controllo dev'essere qui.

## 7. Che cosa resta fuori

I titoli correnti **in cima** (§1 ramo 2). L'anticipazione ai producer: nessuno
consulta la misura prima dell'analisi di pagina, il beneficio **non è misurato** e
la precondizione tecnica — normalizzare tutte le pagine prima di renderne una —
non esiste, perché `NormalizedPrimitivePage` non ha deserializzatore. Va però
nominato il debito che `State.md` iscrive due volte: `column_band` deve poter
togliere piè di pagina e numeri dalle proprie bande, «decisione dell'utente,
lavoro dovuto e non limite accettato».

Il codice che ha prodotto i numeri del §0 e del §1 va committato con i manuali e
gli indici, sotto l'eccezione di `AGENTS.MD` §Aggiornamento documenti: oggi
quelle tabelle non sono riproducibili dal repo, ed è il difetto che il §18,
scritto da me tre giorni fa, esiste per impedire.
