# Esito di `Criterio_ArredoRicorrente_v3.md` — **il veto tiene sul campione, il pavimento cade, la giunzione non è stata fatta**

**Stato in una riga**: nessuna delle 12 voci tolte è giudicata contenuto, da
nessuno dei due etichettatori; il pavimento **cade al 67,4%** contro una barra di
tre quarti; la clausola della giunzione **non è stata eseguita**. Il criterio
**non è scaricato**.

Il primo numero che questo verbale aveva scritto era **84%, e diceva che il
pavimento reggeva**. Era falso, e il §2 dice come.

---

## 1. Il veto — tiene sul campione, e il campione è piccolo

12 voci estratte col seed `20260829` **dichiarato nel criterio prima**
dell'estrazione (`9f1710e` precede `b678247`), dai dieci manuali mai usati,
stratificate metà fra il 25% e il 40% di ricorrenza e metà sopra.

| voce | manuale | slot | quota | **ramo** | agente | utente |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | Vil | (6, 95) | 35% | etichetta | arredo | — |
| 02 | BoB | (4, 18) | 45% | etichetta | arredo | — |
| 03 | Dag | (10, 96) | 45% | etichetta | arredo | — |
| 04 | DrW | (95, 97) | 42% | etichetta | arredo | — |
| 05 | Kul | (25, 4) | 28% | etichetta | arredo | — |
| 06 | DrM | (93, 96) | 48% | etichetta | arredo | — |
| 07 | Vil | (92, 95) | 38% | etichetta | arredo | — |
| 08 | Dag | (15, 96) | 48% | **ricorrenza** | arredo | **arredo** |
| 09 | Vil | (13, 95) | 35% | **ricorrenza** | arredo | — |
| 10 | Apo | (72, 95) | 25% | **ricorrenza** | arredo | **arredo** |
| 11 | Vil | (79, 95) | 38% | **ricorrenza** | arredo | **arredo** |
| 12 | BiD | (6, 93) | 48% | etichetta | arredo | **arredo** |

> **Nessuna voce tolta è giudicata contenuto.** Il veto, come clausola, non è
> stato violato.

**Il ramo va riportato distinto, e il codice lo diceva già.** Il docstring di
`FurnitureSlots` avverte che «un verbale che li sommasse renderebbe invisibile
quale dei due ha deciso». **8 voci dal ramo 1** (nessun parametro) e **4 dal ramo
2** (`EDGE_BAND=0.08`, `RECURRENCE_SHARE=0.25`). Il ramo tarabile è stato
esercitato, e **tre delle quattro voci viste dall'utente** — 08, 10, 11 — vengono
proprio da lì. Rilievo della revisione indipendente, che temeva l'opposto; i dati
dicono che il ramo con i parametri è la parte più controllata del campione.

**Quanto poco vincoli una barra a zero su 12 voci.** Zero contenuto osservato su
12 mette il tasso di contenuto fra le voci tolte **sotto il 22%** al 95%, non
vicino a zero. Il verdetto formale è corretto — la clausola chiedeva zero
osservato e zero osservato c'è stato — ma il numero dice quanto è larga la
banda che resta.

### Il controllo dell'utente è n=2, non n=4

Le voci 08 e 10 erano **già state decise dall'utente** prima di essergli
sottoposte come controllo: l'agente le aveva segnalate come le uniche
semanticamente reali — informazione di navigazione, forse metadato di struttura
invece che scarto — e la decisione («sono piè di pagina con intestazioni di
capitolo, vanno tolte come le altre») è arrivata prima del sorteggio. Il sorteggio
le ha poi pescate entrambe. **Il «4 su 4» contiene due conferme di sé stesso**;
il controllo indipendente è sulle voci 11 e 12.

Su 4 osservazioni concordi e zero discordi, la regola del tre mette il tasso di
disaccordo **sotto il 53%**. Su 2, non lo mette praticamente da nessuna parte.

E il seed del sorteggio di controllo, `20260830`, **non era pre-registrato**:
compare solo in questo verbale, scelto dopo aver visto l'uscita dell'agente, e
nessuno script committato lo consuma. Non cambia l'esito — le voci sono quelle —
ma è la stessa forma di difetto che il §15 esiste per impedire, e va nel criterio
successivo come regola, non qui come scusa.

### `0 incerto` è vero come etichetta e non come sostanza

L'agente ha prodotto `arredo` su 12 su 12 — ma su **4 voci su 12** ha espresso un
dubbio in prosa: 08 e 10 come «le uniche semanticamente reali» con un'ipotesi
alternativa esplicita, 09 e 11 con la condizione «se fossero il sopratitolo il mio
giudizio sarebbe `incerto`» (verificato: la chiave dà `(13,95)` e `(79,95)`, cioè
il piede, e il suo ragionamento dai conteggi era corretto).

Il §4 chiama `incerto` «l'unico canale che porta i dubbi all'umano». I dubbi sono
arrivati all'umano **fuori da quel canale**. Non è una perdita di informazione
qui, perché li ho riportati; è una **deviazione di instradamento** che va corretta
nel protocollo, perché con quattro `incerto` il §4 avrebbe portato all'utente 6-7
voci invece di 4, di cui almeno due non pre-decise.

**La cecità dell'agente sul meccanismo era debole, e il criterio lo diceva già**
(§4: «il cieco sul meccanismo no e va dichiarato debole: sotto il ramo 2 le voci
sono tutte in fondo alla pagina, e il meccanismo si inferisce dall'elenco»). Una
versione precedente di questo verbale scriveva «cieco su meccanismo ed esito
atteso» senza la riserva, cioè rendeva più forte una cecità che il documento in
giudizio aveva già dichiarato debole di suo pugno.

### Che cosa il campione non può dire

Le voci sono **per costruzione quelle che la regola toglie**, quindi il campione
misura la precisione e **mai la copertura**: non contiene nessun caso di confine,
e conferma la distinzione invece di metterla alla prova. Rilievo dell'agente,
coincidente con quello della revisione cieca. È esattamente ciò per cui il §5 ha
**anche** un pavimento — ed è il pavimento che ha deciso questo giro.

L'agente ha nominato due classi che la regola **manca** e che nessuna voce
rappresenta: l'etichetta verticale al bordo (`IL COLPO`, `GRIFFONS`, `TACTICIAN`)
e il numero di capitolo in alto a sinistra su BiD.

## 2. Il pavimento — **cade**, e il primo numero era prodotto da un difetto

`./venv/bin/python scripts/measure_furniture_coverage.py --pdf-dir . --pagine 40 --modo completo`

| manuale | pagine | presenti | tolte | copertura |
| --- | ---: | ---: | ---: | ---: |
| Apo | 40 | 38 | 36 | 95% |
| BiD | 40 | 38 | 35 | 92% |
| BoB | 40 | 37 | 35 | 95% |
| Dag | 40 | 41 | 38 | 93% |
| DrM | 40 | 38 | 32 | 84% |
| DrW | 40 | 37 | 34 | 92% |
| **FW** | 40 | **40** | **0** | **0%** |
| **FWK** | 40 | **34** | **0** | **0%** |
| **Kul** | 40 | 29 | 11 | **38%** |
| Vil | 40 | 39 | 29 | 74% |
| **TOTALE** | | **371** | **250** | **67,4%** |

> Barra del §5: almeno tre quarti. **CADE.**

### Come il primo numero è diventato 84%

La prima misura contava solo le pagine con **etichetta dichiarata**. FW e FWK non
dichiarano `/PageLabels`, quindi le loro 74 occorrenze non entravano né sopra né
sotto la frazione: **i due manuali che la regola manca completamente sparivano dal
denominatore invece di abbassarlo**. Il risultato era 250/297 = 84,2%, ed è
riproducibile con `--modo dichiarato`.

Non è un arrotondamento: è il **difetto già confessato al §5 di una versione
precedente di questo verbale** — «il conteggio saltava le pagine senza etichetta
dichiarata» — che era stato corretto come *affermazione* e lasciato in piedi come
*numero*. La revisione indipendente l'ha ricavato **dall'aritmetica sui numeri del
verbale stesso**, senza rifare la misura, e la sua stima (~68%) è caduta a mezzo
punto dal vero.

La misura corretta ha poi avuto due difetti suoi, entrambi trovati mentre la
scrivevo e nessuno dei due da solo:

- **passava le etichette dedotte alla politica**, facendole eseguire il terzo
  ramo che non esiste: FW risultava al 100%. Verità di riferimento e regola in
  giudizio ora sono separate, ed è scritto nel modulo perché;
- **prendeva un solo slot** quando il numero è stampato **a lati alterni**. FW ha
  due slot da 20 pagine, FWK da 18 e 16: il denominatore restava dimezzato dopo
  essere già stato azzerato una volta. Il test che ha trovato il caso in cui la
  fusione non deve avvenire — due colonne che rivendicano la stessa pagina —
  **è nato fallendo**, e senza di lui `update` ne sceglieva una in silenzio.

### La caduta non è «i manuali senza etichetta»: sono i numeri **ai lati**

**Wil non dichiara le etichette e sta al 100%**, perché stampa in basso e il ramo
2 lo raggiunge. FW e FWK stampano al **centro dei lati** — `x=0,94` e `x=0,01`,
`y=0,49`, alternati recto/verso, testo normale e selezionabile — e lì **nessuna
geometria dei due rami arriva**: il ramo 1 non ha con che confrontare, il ramo 2
guarda solo la fascia bassa.

Senza quei due, la copertura sui restanti otto è 84,2%. **La caduta è
interamente attribuibile a una posizione che la regola non prevede**, non a una
taratura sbagliata dei parametri del ramo 2.

**Togliere la fascia non li recupera gratis**: misurato, senza vincolo di fascia
su FWK entrano `Gli infliggi danno come se stessi pilota` e `I Cavalieri Lumaca
Giganti sono mostri g`, cioè corpo. E le quote non separano — i numeri stanno al
45-50%, il corpo che compete al 38-55%. Quello che separerebbe è la posizione
**ai lati**, `x` agli estremi: la stessa idea di margine applicata agli altri due
bordi.

### Il pavimento eseguito non è quello registrato, su tre punti

| clausola registrata (§5) | eseguito |
| --- | --- |
| «nelle pagine del campione» | 400 pagine, 10 manuali × 40 |
| «numero di pagina **e di filigrana**» | solo numero di pagina |
| «contate **dall'utente**» | contate dallo strumento dell'agente |

L'allargamento della popolazione è conservativo. L'omissione delle filigrane va
nel verso che **abbassa** la copertura dichiarata — sono la classe che il ramo 2
prende meglio — quindi non è auto-servente, ma resta un cambio di ambito non
dichiarato, che è ciò che il §15 vieta nominatamente. Il terzo punto è il più
serio: la clausola nominava l'utente come contatore **proprio perché** lo
strumento dell'agente è la cosa che, due paragrafi più su, si è rivelata
difettosa due volte.

**Non è stato rifatto contando a mano**, e questo verbale non pretende che sia
equivalente. Con il pavimento che cade di sette punti la differenza non cambia il
verdetto; se fosse caduto per mezzo punto, l'avrebbe cambiato.

### Un parametro di costo non dichiarato

La finestra è **40 pagine contigue a metà manuale**; il default di
`--arredo-pagine` è 60, e il criterio non fissa nulla. Il docstring di
`document_furniture_slots` avverte che non è neutra: «un campione contiguo corto
**sovrastima le intestazioni di capitolo**, che su una finestra stretta sono su
tutte le pagine e su un manuale intero no». Riguarda proprio le voci 08 e 10.

## 3. La conservazione — non è un controllo superato, ed è una clausola che non c'è più

Verificato su due pagine con e senza `--arredo`: **`document_ir2.json` è identico
byte per byte**, e ciò che esce dal corpo compare in `review_ir2.md` col suo
testo. `scripts/prototype_ir2_page.py` scrive il JSON **prima** di calcolare
`excluded_node_ids`, quindi l'identità è garantita dall'ordine delle operazioni.

**La clausola era il §6 della v2 e la v3 non l'ha più**: il §6 della v3 parla
d'altro (perché non serve una decisione architetturale dedicata). Una versione
precedente di questo verbale ci rimandava come se fosse la clausola in giudizio, e
chi avesse seguito il rimando sarebbe atterrato su un argomento diverso. Va detto
nel verso utile: **la v3 ha lasciato cadere la conservazione**, e quanto segue è
il motivo per cui aveva ragione a farlo.

Il meccanismo non distrugge niente — il nodo resta, cambia la resa — quindi il
multiinsieme dei caratteri è identico **per costruzione del renderer corrente**,
non per definizione: dipende da `review_lines_for`, codice scritto due commit
prima e regredibile. Come guardia di regressione resta utile; come «errore
squalificante» era etichettato troppo forte.

## 4. Che cosa NON è stato eseguito

> **La giunzione.** Per ogni voce tolta si guarda il paragrafo immediatamente
> sopra e sotto. Cade se due paragrafi si saldano male dove l'arredo li separava.

Non fatta. È la clausola che `State.md` Milestone 39 indica come il difetto atteso
di **ogni** meccanismo che sottragga testo — «succederà a ogni meccanismo che
tolga primitive, l'arredo per primo» — e nessun'altra clausola può vederla: la
conservazione è cieca ai confini di paragrafo, e il §5 giudica le voci tolte, non
il testo rimasto.

**E lo strumento che sembrerebbe adatto non lo è.**
`scripts/check_paragraph_conservation.py` confronta due `document_ir2.json`, e la
politica d'arredo non tocca `document_ir2.json` — è quella l'identità byte per
byte del §3. Il difetto della giunzione vive **nel Markdown**, dove nessuno
strumento committato guarda. Chi riaprirà il fascicolo lo sappia prima di
perderci un giro.

## 5. Un terzo ramo, ora con numeri e non con un'intuizione

La deduzione scritta per il **denominatore** di questa misura — uno slot che porta
un numero su almeno un quarto delle pagine, sequenza strettamente crescente, slot
fusi quando il numero alterna i lati — trova il numero stampato su **FW 40 pagine
su 40**, **FWK 34 su 40**, **Wil 40 su 40**.

Distinzione che questo esito registra e che il criterio non aveva: un `page_label`
**dichiarato** dal documento e uno **dedotto** leggendolo non sono lo stesso
fatto, e il contratto deve poterli distinguere. Mettere `idx + 1` in `page_label`
sarebbe inventare: su DIE l'etichetta a idx 50 è `39`, non `51`.

**Perché dedurre per contare è lecito e dedurre per togliere no.** Qui la
deduzione è verità di riferimento per misurare ciò che la regola **manca**; usarla
per decidere che cosa esce dal corpo sarebbe il terzo ramo, e va scritto in un
criterio **prima** di essere eseguito — il §3 vieta di aggiungere un ramo dopo aver
visto l'esito, ed è esattamente l'errore che ho commesso per sbaglio a metà misura
(FW al 100%, §2).

Un criterio successivo deve poterlo **falsificare**, non solo tararlo: la
monotonia come condizione scritta prima, il confronto con `idx + 1` come controllo
e non come definizione, e una barra che dica quando la deduzione va rifiutata.

## 6. Che cosa questo giro ha spedito, e la domanda che non ha posto

Oltre alla rimozione: il numero di pagina è diventato **provenienza**
(`page_label` su `PageIR2`, `> **[pagina N]**` in uscita, `6da291b`), che è la
metà del §1 del criterio che chiedeva di non buttare il fatto insieme
all'arredo.

**Questo verbale non dice da nessuna parte se una pagina, tolto l'arredo e messo
il riferimento, si legga meglio di prima.** Misura la copertura del numero di
pagina, che è un numero sull'arredo, non sul Markdown. `State.md` dichiara la
rimozione dell'arredo «la precondizione del primo `page.md` consultabile», e la
misura di questo round — dichiarata dall'utente — è **un file Markdown leggibile
a occhio umano**. Rilievo della revisione indipendente, accolto senza riserve: è
l'unica domanda che l'obiettivo pone, e l'unica a cui questo giro non ha
risposto.

## 7. Un difetto trovato dal campione, non dal progettista

La misura è **crashata** alla prima esecuzione sui manuali mai spesi: `y` può
essere **negativo**, perché un testo può stare oltre il bordo superiore — il vivo
di stampa, già a verbale in Milestone 38 con un'occorrenza a `x 699-1284` su una
pagina larga 581. La validazione lo rifiutava. `x` e `y` sono **posizioni, non
conteggi**, e ora il contratto lo dice. È ciò per cui la regola dei dieci manuali
non spesi esiste.

## 8. Che cosa di questo verbale è ricontrollabile dal repo

`AGENTS.MD` §18 chiede che un numero citato porti con sé ciò che permette di
rifarlo. Il §7 del criterio si era già iscritto questo debito.

**Riproducibile:**

| numero | come |
| --- | --- |
| copertura 250/371, e la tabella per manuale | `scripts/measure_furniture_coverage.py` |
| il 84,2% difettoso, per confronto | lo stesso, `--modo dichiarato` |
| FW 40/40, FWK 34/40, Wil 40/40 | lo stesso, `--manuali Wil FW FWK` |
| le 12 voci, seed `20260829`, stratificazione, **ramo** | `scripts/sample_furniture_items.py` |
| 13 manuali su 16 con `/PageLabels` | `scripts/scan_page_labels.py` |
| suite 1416, ruff | rieseguiti |

**Non riproducibile dal repo**, e va detto invece che sottinteso: gli slot esatti
di FW e FWK come coordinate; il caso di FWK senza fascia (`Gli infliggi danno…`) e
le quote 45-50% contro 38-55%; l'etichetta di DIE a idx 50; le 12 risposte grezze
dell'agente e il sorteggio con seed `20260830`; l'identità byte per byte del §3.
Le prime stanno in comandi ad hoc, le ultime in una cartella di lavoro — che è il
caso che ha fatto scrivere il §18.

## 9. Verifiche

Suite **1416** test, un solo fallimento, quello ambientale già a verbale
(`test_runs_table_candidate_for_known_dag_page` cerca `Dag.pdf` nella root), 8
skip. Ruff verde sui file nuovi.

## 10. Conseguenza, secondo il criterio

Il §5 dice: «**Se cade**: non si esegue il ramo 2 in altra forma senza un criterio
nuovo. Il ramo 1 non ha parametri, quindi una sua caduta è un difetto
d'implementazione, non di taratura.»

La caduta **non è del ramo 2 come taratura**: i suoi due parametri non sono
implicati: su Wil il ramo 2 raggiunge il 100%, e sugli otto manuali che una
qualche geometria copre la media è 84,2%. Manca una **posizione** che nessuno dei
due rami prevede. La conseguenza letterale del §5 — non ritoccare il ramo 2 senza
un criterio nuovo — resta comunque il vincolo operativo, e il criterio nuovo è
quello che il §5 di questo verbale descrive.

**Che cosa resta vero e utilizzabile**: il ramo 1 non ha parametri e trova lo slot
su 13 manuali su 13 che dichiarano le etichette; su otto dei dieci manuali di
prova la regola toglie fra l'84% e il 95% delle occorrenze; nessuna voce tolta è
stata giudicata contenuto. **Che cosa non si può dire**: che il criterio sia
scaricato, che l'arredo sia risolto, o che il pavimento regga.
