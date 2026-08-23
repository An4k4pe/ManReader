# Criterio — la regola che rompe il paragrafo (v2)

Registrato **prima** dell'implementazione e prima di qualunque confronto A/B.
Da committare in un commit **senza codice** (`AGENTS.MD` §15).

**La macchina di accettazione non si muove dalla v1** — campione, protocollo,
barra, errore squalificante: tutti fissati prima di questo lavoro di design e
riportati qui invariati. Cambia la **descrizione del meccanismo sotto esame**,
perché quello che la v1 nominava è caduto e la regola che ha vinto in
progettazione non era fra quelle in gara.

---

## 0. Che cosa è caduto dalla v1, e come si è saputo

**Il candidato del §3 della v1 è falsificato.** La v1 indicava come «candidato
naturale» la regola tipografica: una riga che arriva al margine destro della sua
colonna continua, una che resta corta chiude. Misurata su tre pagine, con lo
scarto dal margine normalizzato sulla larghezza di carattere della riga:

| pagina | righe che continuano | righe che chiudono |
| --- | --- | --- |
| DIE p.380 | fino a 12,0 | da 0,0, il grosso ≥ 10 |
| DB p.99 | fino a **38,2** | otto a **0,0** |
| DrW p.97 | fino a **48,8** | diciassette a **0,0** |

Le due popolazioni si sovrappongono. La separazione pulita su DIE p.380 è una
proprietà di quella pagina — prosa uniforme a colonna singola — non del corpus.
**Limite della misura, dichiarato**: per etichettare «riga che chiude» ho usato
l'ultima riga del blocco come proxy, e su DB p.99 e DrW p.97 quel proxy è
inaffidabile proprio perché i blocchi lì tagliano le voci di traverso. La misura
quindi **non falsifica la regola tipografica**: dice che non c'era un'etichetta
su cui giudicarla.

**La regola non era nuova, ed era già nel repo.** Rilievo dell'utente, verificato:
il `block_index` sta in ogni `source_observation_id`
(`text:b{block}:l{line}:s{span}`), `_SourceLine.block` lo porta, e **nessuno lo
legge** — `grep "\.block\b" ir2_builder.py` non restituisce niente.
`Criterio_ParagrafoDaBlocco_v1.md` l'aveva ratificata («blocco nuovo → paragrafo
nuovo») prima che Milestone 38 la spegnesse sull'evidenza di **una pagina**.

**Le etichette dell'utente su DB p.99**, date a vista sulle 46 righe di sorgente
in ordine di lettura, hanno misurato le tre regole sulla pagina che era stata
l'unica prova per abbandonare il blocco:

| regola | corrette su 43 | rotture mancate | rotture in più |
| --- | --- | --- | --- |
| lessicale (in produzione) | 33 | 0 | **10** |
| blocco nudo | 37 | 2 | 4 |
| **blocco + veto minuscola** | **39** | 3 | **1** |

Le 10 rotture in più del lessicale sono le schede spezzate per campo
(`Movimento: 8`, `PF: 8`, `Mov.: 10`) — il difetto per cui
`Criterio_ParagrafoDaRiga_v1.md` §5 era già caduto. I 4 errori della combinata
stanno **tutti dentro il box a rientro sospeso**; sulle altre 39 giunzioni non
sbaglia mai. Due di quei quattro non sono errori di paragrafo: la prosa va dalla
riga 2 alla 6 e riprende alla 13, con il box infilato in mezzo dall'**ordine di
lettura**, che nessuna regola di paragrafo può ricucire.

**Il blocco nudo però fallisce sulle due colonne.** Su SV p.181 produce **più**
paragrafi del lessicale — 27 contro 23 — perché rompe dove un periodo passa dal
fondo di una colonna alla cima della successiva, che per PyMuPDF sono due
blocchi. Nessuna delle due regole in gara nella v1 regge da sola: falliscono su
casi complementari.

**Verifica su venti pagine** (le 20 già giudicate del campione, spese e non
riutilizzabili come cieche), con un proxy dichiarato prima: i paragrafi che
finiscono senza punteggiatura terminale, che coglie l'**eccesso** di rotture e
**non vede le fusioni**.

| regola | paragrafi | troncati | esito |
| --- | --- | --- | --- |
| lessicale | 579 | 334 | — |
| blocco | 426 | 228 | — |
| combinata | **368** | **183** | vince su 18/20, pareggia 2, non perde mai |

Il livello assoluto non è un tasso di difetto: il proxy conta come troncati anche
`SCHELETRO` e `PF: 8`, che finiscono senza punteggiatura ed è corretto così.

**E un terzo difetto è emerso, che non riguarda i paragrafi.** Su Fab p.248 la
combinata fonde nove voci di elenco in un paragrafo solo. Causa verificata: i
pallini sono la lettera **`w` in Wingdings-Regular**. È lo stesso difetto già a
verbale in `Esito_ParagrafoDaRiga_Par5_v1.md` — «i glifi dei badge sono caratteri
minuscoli per la codifica, e la guardia elenchi copre trattino e cifra, non i
glifi di un font simbolico» — che nella combinata cambia solo di ruolo: prima
faceva rompere dove non si doveva, ora fa **non rompere** dove si dovrebbe.

## 1. La regola sotto esame

> **Si rompe dove cambia il blocco di sorgente, a meno che la riga successiva non
> cominci con un carattere minuscolo del font del corpo.**

Tre segnali, tutti già presenti nella pipeline, **zero parametri**:

1. `block_index`, dal `source_observation_id`;
2. il carattere iniziale della riga successiva;
3. il **font** di quel carattere, da `TextPrimitive.font_name`, che
   `primitive_normalizer.py:96` popola già.

Il terzo è ciò che chiude il difetto dei glifi simbolici alla radice invece che
per enumerazione: un pallino Wingdings non è una minuscola del corpo, quindi non
può vietare la rottura. **Il font del corpo si desume dalla pagina** — la moda
dei `font_name` delle primitive testuali — non da un elenco di nomi di font.

**Il ruolo del test lessicale si rovescia, ed è la ragione per cui non è la
lista di eccezioni che il §2 vieta.** Oggi quel test **impone** una rottura
quando la riga dopo non è minuscola; qui può solo **vietarne** una che il confine
di blocco ha già proposto. Il suo modo di fallire si capovolge da «rompe troppo»
a «rompe troppo poco», ed è una scelta dichiarata: preferire un difetto che
unisce due paragrafi a uno che ne spezza uno in tre. È una preferenza, non una
misura.

## 2. Il perimetro, e il vincolo sul meccanismo

**Si tocca**: `breaks_paragraph` in `ir2_builder.py`, che riceverà le due righe
di sorgente invece delle due stringhe — i primitivi sono già su `_SourceLine`; il
suo chiamante alla riga 353; i test.

**Non si tocca**: nessun producer, `primitive_normalizer.py` (il `font_name`
serve già), `ir2_model.py`, `ir2_markdown.py`, `ir2_validate.py`, i renderer
legacy, `join_lines`. Nessun flag nuovo, nessun cambio di contratto.

**Resta fuori, dichiarato**: **emettere** grassetto e corsivo nel Markdown, che
richiede a `NodeIR2` di portare lo stile e non una stringa nuda — è il difetto
misurato su 13 pagine su 20 e resta aperto; `font_traits=()` a
`primitive_normalizer.py:98`; il colore delle note a margine; l'ancoraggio delle
note; il cancello di emissione sulle full art; la deduplicazione degli span
identici.

> **Il vincolo della v1, invariato: la regola non può essere una lista di
> eccezioni.** Niente elenchi di acronimi, di caratteri ammessi o di nomi di
> font. Ogni grandezza su cui si decide va desunta dal documento.

## 3. Il campione e il protocollo — INVARIATI dalla v1

Fissati prima di tutto il lavoro di design descritto nel §0, e riportati qui
senza modifiche.

Le 40 pagine di `Campione_FormaMancante_v1.md`, seed `20260824`, prodotte con la
configurazione del §3 di `Criterio_FormaMancante_v3.md`.

| insieme | pagine | ruolo |
| --- | --- | --- |
| **primario** | le 20 **mai giudicate** (righe 21-40) | decide il §4 |
| secondario | le 20 già giudicate (righe 1-20) | si riporta, non decide |

Le 20 del secondario sono state **spese in progettazione** (§0) e non sono più
cieche per nessuno scopo. Il primario non è mai stato guardato da nessuno.

**Confronto A/B cieco.** Per ogni pagina due `page_ir2.md`, prima e dopo, presentati
come **A** e **B**, con l'assegnazione estratta per pagina con seed `20260825`,
dichiarato nella v1. Per ogni pagina una sola risposta: **A si legge meglio** ·
**B si legge meglio** · **uguali**. Nessuna causa, nessuna categoria. La
corrispondenza A/B → vecchio/nuovo non si guarda finché tutte le risposte non
sono date.

## 4. La regola di pass/fail — INVARIATA dalla v1

Sulle **20 pagine del primario**:

> **Regge** se «nuovo» vince su **almeno 10** pagine **e** «vecchio» vince su
> **al più 2**. **Cade** altrimenti.

Le due condizioni sono congiunte: «nuovo ≥ 10» da solo si soddisfa anche
peggiorando cinque pagine, e il tetto di 2 è ciò che impedisce di scambiare un
difetto con un altro.

## 5. L'errore squalificante — INVARIATO dalla v1

> **Cade comunque** se su **una sola** pagina delle 40 il testo emesso non si
> conserva: il multiinsieme dei caratteri di tutti i nodi `text.paragraph`,
> ignorando spazi **e trattini**, dev'essere identico prima e dopo.

I trattini si ignorano perché `join_lines` ne toglie uno a ogni giunzione di
sillabazione (`ir2_builder.py:197`): unire due righe prima separate **deve** far
sparire dei trattini. Si riporta quindi anche il loro conteggio dai due lati: un
calo è atteso, un aumento è impossibile e sarebbe un difetto. Limite dichiarato:
questo rende invisibile la perdita di un trattino legittimo.

## 6. I controlli a vista

| pagina | che cosa deve NON peggiorare | quando è stata fissata |
| --- | --- | --- |
| **DB p.99** | gli stat block, spezzati per campo dalla regola vecchia | v1 |
| **DrW p.97** | i badge, glifi minuscoli per codifica | v1 |
| **Fab p.248** | l'elenco a pallini Wingdings | **v2** |

> **Cade** se una delle tre peggiora a giudizio dell'utente.

**Il terzo controllo è stato aggiunto dopo aver visto il difetto**, ed è
dichiarato: rende il criterio **più severo**, non più permissivo, ed è l'unico
modo di legare la regola al difetto che il design ha scoperto. Un controllo
aggiunto per rilassare sarebbe l'opposto e non è questo il caso.

## 7. Il modello nullo, e la sua debolezza

**Nullo**: la regola vecchia e quella nuova producono Markdown che una persona
non distingue; le «spaziature» dei venti verdetti erano una preferenza generica e
non l'effetto di questa regola.

**Debolezza**: falsificabile solo attraverso un giudizio umano, dato da una
persona sola che sa su che cosa si sta lavorando. La cecità A/B toglie il sapere
*quale* versione è nuova, non il sapere *che cosa* si cerca. E la barra non è
simmetrica: un miglioramento reale ma piccolo — sette pagine su venti — verrebbe
dichiarato caduto, di proposito, perché sette su venti non giustifica un cambio
che tocca la segmentazione di ogni pagina di ogni manuale.

## 8. Limiti dichiarati

**Il design ha iterato tre volte su pagine ispezionate** — tipografica, blocco,
blocco+veto — e ogni passo è nato da un fallimento su una pagina guardata. È il
modo in cui questo progetto si è già avvitato tre volte, ed è la ragione per cui
il primario non è mai stato aperto e la barra è stata fissata prima.

**Cambia i numeri già a verbale.** La quota di paragrafi corti, la distribuzione
del §6.C di `Esito_FormaMancante_v1.md` e il rango 3 su 38 di Wil idx 244 sono
proprietà della segmentazione vecchia quanto delle pagine: vanno **rifatti, non
ricopiati**.

**E cambia la base di E-B**: il confronto `--base` verifica l'elenco dei
paragrafi e divergerà per costruzione. **L'ordine di lettura non cambia** — la
sequenza delle righe di sorgente è la stessa, cambia solo il raggruppamento — ma
va verificato e non assunto.

**Il difetto del box a rientro sospeso resta**, misurato: 4 errori su 43 su
DB p.99, tutti dentro il box, di cui 2 causati dall'ordine di lettura che infila
il box in mezzo a un paragrafo di prosa. Nessuna regola di paragrafo lo chiude.

## 9. Che cosa NON decide

Non decide l'emissione dello stile inline, che è il difetto misurato su 13 pagine
su 20 e richiede un cambio di contratto su `NodeIR2`. Non decide niente sulle
note a margine né sul loro ancoraggio, e non apre il detector di marginalia che
`AGENTS.MD:598` gata. Non tocca l'uscita dallo shadow mode. Non riapre la linea
tabelle, in pausa. Non decide se `text.heading` vada emesso, che
`ir2_model.py:62` riserva a una milestone propria.
