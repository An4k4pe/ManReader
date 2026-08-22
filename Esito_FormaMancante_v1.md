# Esito di `Criterio_FormaMancante_v3.md` — **nessun verdetto, e va bene così**

**Stato in una riga**: il §6.A non raggiunge la sua precondizione e si riporta
**senza verdetto**; il criterio prevedeva questo caso e lo dichiarava «di per sé
il risultato più importante del giro» — **16 pagine su 20 sono usabili così come
sono**. E il testo libero, che non doveva decidere niente, ha trovato un difetto
che nessuna delle due linee in gara aveva previsto.

---

## 1. Il risultato che va in testa, perché il criterio lo prescriveva

Su 20 pagine di un campione cieco, l'utente ne giudica **16 usabili così come
sono** per consultare il manuale. La distribuzione del giudizio:

| giudizio | pagine |
| --- | --- |
| molto buona | 9 |
| buona | 2 |
| discreto | 2 |
| abbastanza | 3 |
| poco | 1 |
| quasi nulla | 2 |
| no | 1 |

La linea fra leggibile e illeggibile l'ha tracciata l'utente **dopo** aver dato i
verdetti e **prima** di vedere i conteggi, sul criterio semantico dichiarato nel
foglio («leggibile = lo useresti così com'è»): illeggibili sono `poco` e sotto,
cioè **4 pagine** — 01, 17, 19, 20.

`State.md` registrava che l'uscita di IR 2 su Wil p.245 era «terribile» e che
quella pagina era il metro del giro. Su un campione cieco non lo è: quattro
pagine su venti stanno come lei, sedici no.

## 2. Il §6.A — senza verdetto

> Precondizione: almeno **8** pagine su 20 illeggibili **con causa dominante in
> una delle due categorie che decidono**.

Pagine illeggibili: **4**. La precondizione **non è raggiunta**, e il §6.A si
riporta senza verdetto. Il giro successivo **non è deciso da questa misura**.

**Il conteggio delle cause, che si riporta e non promuovo a verdetto.** Su tutte
e venti le righe l'utente ha scritto `forma mancante`; `arredo di troppo` non
compare **mai**. La direzione è unanime, e resta un'indicazione forte — ma
promuoverla a esito adesso sarebbe esattamente la lettura post-hoc che il §3
vieta: la precondizione era scritta prima proprio per impedire che una manciata
di pagine decidesse una linea di lavoro.

## 3. Che cosa dice il testo libero, ed è il risultato vero

Il §4 imponeva la causa dominante **prima in testo libero** e solo dopo mappata.
La mappatura ha prodotto una sola categoria venti volte; il testo libero ha
prodotto altro:

| che cosa chiede il testo libero | pagine |
| --- | --- |
| **spaziature** | **17 / 20** |
| **grassetti** | **13 / 20** |
| tabella o scheda mancante | 4 |
| callout o raggruppamenti | 4 |
| elenchi da rendere evidenti | 4 |
| arredo finito nel testo (nome capitolo, numero pagina) | 5 |
| colonne mancanti | 2 |
| ordine sbagliato | 1 |
| contenuto perso | 2 |

**Il progetto cercava la cosa sbagliata.** Due milestone hanno chiesto *quale
nodo* mancasse — `text.heading`, `text.labelled_entry` — e su tre quarti delle
pagine la risposta è **il grassetto e lo spazio fra i paragrafi**. Nessuno dei
due è un kind di nodo, nessuno dei due era fra le sette categorie del §5, e
nessuno dei due richiede un criterio da inventare: sono informazione che la
sorgente ha già.

## 4. Dove muore il grassetto — tracciato, non supposto

| passo | che cosa succede |
| --- | --- |
| `pymupdf_capture.py:146` | cattura `font_flags` dallo span PyMuPDF — **il grassetto c'è** |
| `capture_model.py:108` | lo conserva: `font_flags: int \| None` |
| **`primitive_normalizer.py:98`** | **scrive `font_traits=()`** — costante vuota, i flag non vengono mai tradotti |
| `ir2_model.py` | nessun campo di stile: `NodeIR2.text` è una stringa nuda |

Il campo `font_traits` esiste su `TextPrimitive` (`primitive_model.py:69`), è
validato, e non viene **mai popolato**.

**Conferma dal vivo, sulla pagina che l'utente ha segnalato.** Su Wil idx 103 il
titolo `I Wilder` ha `font=GaramondPremrPro-Bd`, `size=22.0`, `flags=20` — cioè
bold (16) più grazie (4). Il grassetto è nella cattura, sul titolo che in uscita
è indistinguibile dal corpo.

**Su questo lo stadio nuovo è più povero del vecchio**, come già lo era sulla
conservazione dei caratteri: il legacy rende lo stile inline
(`markdown_builder.py:213`, `_format_inline_text`). E stavolta l'informazione non
va ricostruita né dedotta: è già in mano alla pipeline e viene buttata in una
riga.

## 5. Due difetti trovati dai verdetti, verificati

**Pagina 20 — Lan idx 192, full art: manca il riferimento all'immagine.**
Verdetto dell'utente: «ci sono i pezzi dei capitoli, numero pagina e mio nome, ma
manca la cosa più importante, il riferimento all'immagine». È il **cancello di
emissione** deciso in Milestone 38 (`5bbb5f5`): le note d'asset il cui candidato
non è stato accettato non entrano nel corpo e finiscono in `review_ir2.md`. Su
una pagina che *è* un'illustrazione, quella decisione toglie l'unico contenuto
che la pagina porta — e sostituire immagini con note brevi è metà dell'obiettivo
di `AGENTS.MD`, non un dettaglio di resa. La decisione va riaperta almeno per il
caso in cui la nota scartata sia l'unico contenuto non testuale della pagina.

**Pagina 12 — Wil idx 103: un paragrafo emesso due volte.** «I Wilder» compare
due volte su 13 paragrafi. Guardata la pagina: il titolo c'è **una volta sola**.
Causa verificata e non supposta: il PDF contiene **due span identici** — stesso
testo, stessa bbox al decimale, stesso font, stessi flag — cioè il titolo è
disegnato due volte, effetto tipografico comune in questi manuali. La pipeline
emette entrambi. È una **nuova duplicazione** rispetto al contenuto visibile, e
`AGENTS.MD` §Migrazione la elenca fra i criteri di equivalenza dello shadow mode.
`deduplicator.py` riguarda asset grafici ripetuti fra pagine, non span di testo
identici sulla stessa pagina; se il filtro del testo duplicato di `extractor.py`
copra questo caso **non è stato verificato**.

## 6. Le misure riportate del §6.C

**La distribuzione delle quote di paragrafi corti** su 37 pagine (3 delle 40
sotto i 10 paragrafi, ben dentro il cancello del quarto):

| | |
| --- | --- |
| minimo | 6,7% |
| **mediana** | **23,1%** |
| massimo | 74,3% |

**Il rango della pagina d'origine: 3 su 38.** Il passo 0 ha ricalcolato Wil idx
244 sotto la configurazione del §3 e ha ottenuto **55 paragrafi, 38 corti,
69,1%** — identico al numero pubblicato, quindi la quarantena del §1 si chiude e
il 69% è confrontabile. Sopra di lui solo Kul idx 219 (74,3%) e Fab idx 286
(69,2%).

**Va detto per intero**: con la barra della v2 del criterio — «cade se il rango è
≤ 4» — **il test sarebbe caduto**. È stato declassato a misura riportata su
decisione dell'utente *prima* che questi dati esistessero. È il caso in cui la
pre-registrazione ha impedito ciò per cui esiste, e va a verbale in questa forma.

Quel che se ne può concludere, e non di più: la densità di frammenti corti di Wil
p.245 è atipica, la pagina mediana sta a 23,1%, e quindi **quel proxy misurava un
estremo**. Non dice che la forma non manchi altrove — il §3 del testo libero dice
che manca eccome, in una forma diversa da quella che il proxy conta.

## 7. Che cosa NON è stato fatto, e perché

**Le 53 etichette per frammento del §4 passo 5 non sono state date.** Il §6.C
della scomposizione era già stato ridotto a conteggio riportato dalla revisione
architetturale; con il §6.A senza verdetto, la scomposizione non ha più niente da
smentire, e il testo libero ha già risposto alla domanda «quale forma manca» in
modo che nessuna delle sette categorie del §5 avrebbe potuto esprimere. Cinquanta
giudizi umani per informare una regola che non decide più, su una domanda già
risposta altrove, è il giro di rifinitura che `CLAUDE.md` chiede di fermare.

Le due precondizioni del §6.B erano soddisfatte (53 frammenti, la pagina più
fitta ne porta 22 su 53), quindi la rinuncia è una scelta e non un impedimento.
Il foglio resta prodotto e rieseguibile.

## 8. Limiti di questo giro, dichiarati

**Il foglio del verdetto invitava a rispondere alla domanda sbagliata.** La
colonna «causa dominante» compariva su tutte le righe, comprese quelle delle
pagine buone, quindi l'utente ha scritto **che cosa migliorerebbe**, non **perché
non si legge**. Responsabilità di chi ha costruito il foglio. Non invalida i dati,
li rende diversi: l'affermazione che reggono è «17 pagine su 20 chiedono
spaziature, 13 chiedono grassetti», **non** «N pagine sono illeggibili per forma
mancante». È anche la ragione per cui il §2 non promuove l'unanimità a verdetto.

**Il protocollo di lettura è stato prescritto ma non è verificabile.** Verdetto
sul solo `.md`, render solo dopo, deciso e registrato prima del primo verdetto,
con la direzione del bias dichiarata: leggere alla cieca rende *più* facile
giudicare illeggibile, quindi era la condizione meno prudente per l'ipotesi
sotto esame. Che sia stato seguito è dichiarato, non osservato.

**`DB` non è nel campione.** È l'unico dei 16 manuali assente, ed è un effetto
diretto delle esclusioni per costruzione: DB 98, 17, 52, 49, 89, 61, 75, 122, più
DB 53 fra le 60. È anche il manuale su cui la maggior parte del lavoro precedente
è stata fatta e da cui vengono molti esempi a verbale.

**Le esclusioni tirano il campione dalla parte facile**, come il §8 del criterio
dichiarava: le ~113 pagine escluse furono scelte a suo tempo *perché difficili*.
Il «16 su 20 usabili» va letto sapendolo — è una stima ottimistica, e di quanto
non è misurabile da qui.

## 9. I venti verdetti, verbatim

Il §4 impone che il testo libero si conservi **integralmente** e non al posto
suo. Riprodotto come dato, refusi compresi: è il verbale di ciò che è stato
scritto, non una parafrasi. La colonna `idx` è quella del campione, non quella
digitata nel foglio (tre righe l'avevano lasciata vuota e una portava `5` per
`56`).

| # | manuale | idx | giudizio | causa dominante, verbatim |
| --- | --- | --- | --- | --- |
| 01 | DrW | 227 | poco | tutto troppo uguale, servono meno spazi, manca la tabella e secondo me vanno legati in callout o altro le abilità per farle spiccare |
| 02 | DIE | 379 | abbastanza | mancano le colonne, spaziature e rgassetti |
| 03 | BiD | 76 | abbastanza | Le barre del capitolo sono entrate a cso non testo, spaziature, grassetti |
| 04 | Fab | 247 | buona | elenco a paragrefi dei vari punti, spazi |
| 05 | Wil | 154 | discreto | manca la tabella (scheda), spaziature |
| 06 | FWK | 70 | buona | spaziature, grassetti e callout o altri ragruppamenti per migliorare la lettura, il numero di pagina è finito a caso nel testo |
| 07 | Wil | 7 | molto buono | spaziature e grassetti |
| 08 | SV | 180 | molto buona | qui ci sono le corrette colonne, mancano i grassetti e ridurrei le spaziature, il nome del capitolo finisce a caso nel testo |
| 09 | FW | 138 | molto buona | mancano i grassetti e ridurrei le spaziature, il numero di pagina finisce nel testo |
| 10 | SV | 178 | molto buona | qui ci sono le corrette colonne, mancano i grassetti e ridurrei le spaziature, il nome del capitolo finisce nel testo |
| 11 | BiD | 8 | Molto buona | spaziature e grassetti |
| 12 | Wil | 103 | molto buona | parole ripetute, spaziature |
| 13 | Lan | 243 | discreta | qui ci sono le corrette colonne, mancano i grassetti e ridurrei le spaziature, farei dei callout per la leggibilità e cercherei di riprodurre glifi o comunque simboli specifici per ricosdtruire la cosa |
| 14 | Vil | 21 | Molto buona | spaziature e grassetti |
| 15 | DIE | 286 | abbastanza | mancano le colonne, spaziature e rgassetti, migliorare gli elenchi |
| 16 | Vil | 70 | molto buona | spaziature e grassetti, elenco più evidente |
| 17 | Apo | 56 | quasi nulla | ordine sbagliato, mancano le tabelle |
| 18 | Fab | 307 | molto buona | spaziature e grassetti, elenco più evidente |
| 19 | DrM | 361 | quasi nulla | sheet o tabelle e callout |
| 20 | Lan | 192 | no | è una full art, ci sono i pezzi del cpaitoli, numero pagina e mio nome, ma manca la cosa più importante, il riferiemnto all'immagine |

Categoria assegnata dall'utente: `forma mancante` su tutte e venti, più
`contenuto perso o sbagliato` sulla 20.

**Una cosa che il verbatim mostra e la tabella del §3 no**: cinque righe
segnalano arredo dentro il testo — nome del capitolo o numero di pagina — e in
nessuna di esse l'utente l'ha scelto come causa **dominante**. L'arredo c'è, dà
fastidio, e non è il difetto principale di nessuna pagina.

## 10. Che cosa segue

Il giro successivo **non è deciso da questa misura**, che non ha dato verdetto. È
deciso, se l'utente lo accetta, da un difetto trovato per ispezione con la causa
tracciata riga per riga, che non dipende da nessuna precondizione statistica:
**lo stile inline esiste nella cattura e viene scartato in `primitive_normalizer.py:98`.**

Quel lavoro non è né la «forma» né la «sottrazione» che il criterio metteva in
gara. Non costruisce un kind nuovo — quindi non tocca la milestone che
`ir2_model.py:62` riserva a `text.heading` — e non toglie testo dal flusso —
quindi non entra nell'«esclusione automatica di marginalia» che `AGENTS.MD:599`
gata. È conservazione di informazione già catturata, lungo un percorso che oggi
la butta.

Restano aperti e non decisi qui: il cancello di emissione sulle pagine full art
(§5), la duplicazione degli span identici (§5), e i due porting del §10 del
criterio, di cui quello sulla conservazione dei caratteri richiede prima una
decisione sul trattino di sillabazione.
