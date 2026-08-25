# Criterio — «è la forma che manca»: generalizza, e quale forma (v2)

Registrato **prima** della misura, prima dell'estrazione del campione e prima di
scrivere lo script che la esegue. Da committare in un commit **senza codice**
(`AGENTS.MD` §15).

Decide due cose: se la diagnosi nata su Wil p.245 valga per il corpus o solo per
quella pagina; e se il giro successivo debba **togliere** testo dal flusso o
**costruire** una forma. Sotto la prima domanda non c'è niente da costruire, e
questo criterio esiste per poterlo scoprire prima di costruirlo.

Posizione dichiarata entrando, che è dell'utente e non ipotesi di Chat A: gli
altri producer vanno sfruttati per **sottrarre** elementi già identificati, così
che ogni meccanismo successivo abbia meno rumore da giudicare; e `column_band`
deve funzionare benissimo, perché da un suo errore sbagliano troppe cose e
l'ordine di lettura è fra le prime cose che si vedono in un Markdown. La linea
tabelle è **in pausa** per decisione dell'utente.

---

## 0. Changelog — che cosa cambia dalla v1, e chi l'ha trovato

La v1 non è stata committata. È stata sottoposta a un giro di revisione
indipendente **metodologico** (Chat B, workflow §8) prima del commit, per non
spendere ore di misura su un criterio difettoso. Verdetto: **non committare
così**. Le voci sotto sono le sue, verificate da Chat A prima di essere integrate.

**Accolte, e cambiano la sostanza:**

1. **Il 69% viene da una configurazione che il criterio non dichiarava**, e il §3
   ne fissa una che quasi certamente non è quella. Verificato:
   `Esito_TabellaInIR2_v1.md` §5 dice che senza `--tables` il comportamento è
   identico su **11 pagine su 12**, «e la dodicesima differisce solo con il flag
   acceso» — e la dodicesima è Wil p.245, l'unica pagina del campione in cui una
   tabella sia stata costruita. La §6.A avrebbe confrontato **due strumenti**
   chiamandolo confronto fra due pagine. → **passo 0** (§4).
2. **«Non c'è una soglia perché non ce n'è una difendibile» era falso**: il 90°
   percentile *è* una soglia, traslocata dall'asse della quota a quello della
   frequenza. → sostituito dal **rango**, dichiarato come scelta (§6.A).
3. **Manca una categoria per lo spezzone di paragrafo**, cioè per il difetto che
   il §10 della v1 nominava come precondizione del giro successivo: il progetto
   sa che esiste, la tassonomia non lo prevedeva, e con `altro ≥ 20%` che impone
   campione nuovo un difetto noto aveva una via diretta per far rifare tutto.
   → categoria `spezzone` (§5).
4. **Le barre erano in frammenti e il campione dimensionato in pagine.** →
   minimo di frammenti, pooling dichiarato, tetto per pagina (§6.E).
5. **Il veto del proxy era troppo largo**: la §6.A è un confronto posizionale e
   un'inflazione uniforme del proxy si cancella in gran parte in un rango. →
   veto ristretto (§6.E).
6. **Optional stopping non chiuso**: il seed proteggeva da *quali* pagine, non da
   *quante*. → terminalità dichiarata (§4).
7. **«Campione cieco» nominava due oggetti diversi** nello stesso documento, uno
   dei quali escluso per costruzione. → il denominatore si chiama sempre «il
   campione da 40 del §4».
8. **«Molto sopra il 4%»** lasciava margine a chi applica. → tolto (§8).
9. **Il ripiego del §9 sovra-rivendicava** e non aveva cancello di costo. →
   riscritto come affermazione sullo strumento, con la regola di pausa (§9).

**Accolta su indicazione dell'utente, dopo la revisione:** il **verdetto di
pagina** passa da conteggio riportato a **misura che decide** (§6.B), su un
insieme più largo. Ragione, che era di Chat B: era il numero più vicino
all'obiettivo di tutto il giro, e la v1 lo declassava per affidare la decisione a
un proxy che il §9 stesso dichiara cieco a una parte del fenomeno. La
scomposizione per frammento resta, e decide **quale** forma costruire — cosa che
il verdetto di pagina non può dire.

**Respinta:** «i numeri scadono perché il lavoro successivo cambia la fusione dei
paragrafi». Le due precondizioni del §10 sono **strumenti** — un invariante di
conservazione e una misura della fusione — non modifiche all'emissione: non
cambiano il conteggio dei paragrafi. Il numero scadrebbe solo dopo il giro che
sottrae davvero del testo, che sta a valle di questa decisione. Resta accolta la
metà giusta del rilievo: il §10 della v1 appiattiva tutti gli esiti sulla stessa
azione successiva, ed era un errore di scrittura. → §10 riscritto.

**Respinta:** «40 pagine estratte possono non essere 40 utilizzabili». Il
campionatore continua a pescare fino a raggiungere la taglia e riporta gli scarti
a parte (`scripts/sample_ir2_verification_pages.py:148-159`). Chat B non legge
codice al giro 1 e l'aveva correttamente messa fra le voci da verificare.

## 1. Il caso d'origine, che questo criterio deve vincolare

`Esito_TabellaInIR2_v1.md` §1-ter, su **Wil idx 244** (pagina del file 245):

| | |
| --- | --- |
| paragrafi emessi | 55 |
| paragrafi di ≤2 parole | **38 (69%)** |
| risalite di oltre 30pt fra paragrafi consecutivi | 2 (4%) |

Conclusione tratta allora: «l'ordine è quasi giusto, è la forma che manca», e il
69% mescolerebbe titoli di sezione e coppie etichetta-valore.

**Questi tre numeri non sono utilizzabili come stanno.** La configurazione che li
ha prodotti non è dichiarata in nessun documento, e su quella pagina — l'unica
delle dodici in cui una tabella sia stata costruita — la lista dei paragrafi
cambia a seconda di `--tables`. Il **passo 0** del §4 li rifà sotto la
configurazione del §3. Finché non è eseguito, il 69% resta citabile solo come «il
numero pubblicato», mai come termine di paragone.

**Una pagina sola.** `AGENTS.MD` §15 impone che il criterio vincoli il caso da
cui l'affermazione è nata: è il §6.A, e Wil idx 244 è escluso dal campione di
confronto proprio perché è il caso sotto esame.

**E il conteggio nudo non è interpretabile.** Una linguetta di capitolo fatta di
testo, un'intestazione corrente, un numero di pagina, un glifo di elenco separato
dal suo testo — difetto già a verbale su DB p.53 in Milestone 38 — e lo spezzone
di un paragrafo rotto dall'estrazione sono tutti paragrafi di ≤2 parole. Il
conteggio non distingue «manca una forma» da «avanza dell'arredo» da «l'emissione
ha spezzato una frase», e le tre cose indicano lavori diversi.

## 2. Il proxy, fissato prima

**Paragrafo emesso** = un nodo con `kind == "text.paragraph"` nella IR 2 della
pagina, letto da `document_ir2.json` e non dal Markdown reso. I nodi `asset.note`
e gli eventuali nodi con `structure` **non** sono paragrafi e non entrano né a
numeratore né a denominatore. Con la configurazione del §3 l'esclusione dei nodi
`structure` è un **no-op** — `--tables` è l'unica sorgente di `structure`,
verificato in `Esito_TabellaInIR2_v1.md` §5 — ed è scritta per non dipendere da
quel fatto.

**Paragrafo corto** = `len(node.text.split()) <= 2`. Separazione sui soli spazi,
**nessuna pulizia**: niente rimozione di punteggiatura, niente scarto dei token
di soli simboli. Qualunque pulizia sarebbe un giudizio, e un giudizio è ciò che
si può ricalibrare dopo aver visto l'esito. La chiusura di Milestone 38 ha già
mostrato un caso in cui i caratteri non sono ciò che sembrano — sui badge di
DrW p.97 `á` è U+00E1 e il simbolo del bersaglio è la lettera `o`.

**Quota della pagina** = paragrafi corti / paragrafi emessi.

**Pagine troppo corte**: una pagina che emette **meno di 10** paragrafi non entra
nel calcolo della distribuzione e si riporta a parte. Una quota su tre paragrafi
è rumore. La soglia è fissata qui, prima, e non è tarata. Se queste pagine sono
più di **un quarto** del campione da 40, la §6.A non è interpretabile e va detto
invece di calcolarla lo stesso.

Nessuna di queste costanti è una soglia geometrica nella pipeline: sono costanti
di protocollo di misura, e la regola «soglie mai hardcoded» riguarda le prime.

## 3. La configurazione, fissata prima

**Una sola**, dichiarata prima di vedere il campione perché la misura non diventi
una scelta fra varianti:

```
./venv/bin/python scripts/prototype_ir2_page.py \
    --pdf <manuale>.pdf --page-number <idx+1> --output-dir <dir>
```

`--tables` **spento** (il suo criterio è caduto, `Esito_TabellaInIR2_v1.md`).
`--interrupt-corridor` **spento** (decisione di Milestone 37, non riaperta qui).
`--base` non passato.

Vale **identica per il passo 0**: è tutto il punto del passo 0.

Cambiare configurazione dopo aver visto l'esito richiede un criterio nuovo.
Cambiarla qui sarebbe la lettura post-hoc che `AGENTS.MD` §15 vieta, e in questo
progetto è già successo quattro volte per criteri scelti iterando.

## 4. Il campione, e l'ordine dei passi

**Seed `20260824`**, dichiarato qui prima dell'estrazione. **40 pagine**
uniformi dal pool dei 16 manuali (5.194 pagine, conteggio precedente alle guardie
di ammissibilità; il campionatore continua a pescare fino a raggiungere la taglia
e riporta gli scarti).

**Escluse per costruzione**, indici 0-based:

| gruppo | pagine |
| --- | --- |
| sviluppo IR 2 (Milestone 38) | DB 98, DB 17, DB 52, DB 49, Dag 83, Dag 163, DrW 96 |
| criterio schede mostro | DB 89, DrM 86, Vil 222 |
| sviluppo tabelle, già in `NORMAL_TABLE_EXCLUSIONS` | Dag 117/133/135/136/194, DB 75/122, DrM 32/35/267, DrW 32/239/247, BoB 238, Wil 73/244, Lan 40/109/118/284, Fab 52/256/272/280, SV 43/189, Apo 46, Vil 166, FW 62 |
| **sviluppo tabelle, mancanti dallo script** | **DB 61, Lan 18, Lan 51, Wil 77** |
| campione di verifica di Milestone 38, già giudicato | FWK 122, BiD 287, Apo 34, Vil 64, FWK 31, Wil 71, Dag 199, Fab 126, BoB 297, BiD 314 |
| campione di `Criterio_TabellaNormale_v1.md` (seed `20260822`, 60 pagine) | l'elenco di `Campione_TabellaNormale_v1.md` §«Le 60 pagine» |

Le quattro pagine della riga in grassetto **non sono un sospetto**:
`Criterio_EstensioneRegioneTabella_v1.md:41-42` le elenca fra le pagine di
sviluppo, e due compaiono nelle righe di comando committate di
`scripts/inspect_table_gutter_regularity.py` e
`scripts/compare_table_gutters_with_column_band.py`. Mancano da
`NORMAL_TABLE_EXCLUSIONS`: è un difetto dello script.

**L'estrazione avviene DOPO la correzione di quella lista.** Il campione è
funzione di (seed, pool, esclusioni, procedura): dichiarare il seed prima e
cambiare le esclusioni dopo non vincolerebbe niente.

Le 60 pagine del campione tabelle si escludono perché su quelle l'utente ha già
dato un'etichetta a vista sul render. Costa 60 pagine su 5.194.

**Guardie di ammissibilità**: le stesse di `_is_admissible` — `rotation != 0`,
`mediabox != cropbox`, pagina senza testo. Gli scarti si riportano.

**La procedura di estrazione annidata**, perché l'esito non dipenda dall'ordine
delle operazioni. Dall'ordine casuale che il seed produce sul pool:

- le prime **40** ammissibili sono **il campione da 40 del §4**;
- le prime **20** di quelle 40, nel loro ordine di estrazione, sono l'**insieme
  del verdetto**;
- le prime **5** di quelle 20, nello stesso ordine, scartando una pagina il cui
  manuale sia già uscito e le pagine «troppo corte» del §2, sono l'**insieme
  delle etichette**. Le pagine scartate si elencano.

Il filtro «troppo corte» dipende dall'uscita del codice, ed è dichiarato prima
per questo: è l'unico punto in cui l'estrazione non è funzione del solo seed.

**40, 20 e 5 sono terminali.** Aumentare una qualunque delle tre dopo aver visto
un esito è un criterio nuovo con campione nuovo. **Non esiste «guardiamone altre
cinque»**: il seed protegge da *quali* pagine, non da *quante*, e questa riga
chiude la seconda porta.

**I passi, in quest'ordine:**

0. **Si ricalcola Wil idx 244** sotto la configurazione del §3, e si registra la
   sua quota. È **una pagina**, e senza di essa la §6.A confronta due strumenti.
   Il numero risultante va nell'esito, non in questo criterio: la regola della
   §6.A è dichiarata **prima** di conoscerlo.
1. Si estraggono le 40 pagine col seed, dopo la correzione delle esclusioni. Si
   scrive il verbale dell'estrazione come per i campioni precedenti.
2. Per ciascuna si producono, con la configurazione del §3, `page_ir2.md`,
   `document_ir2.json` e il **render** della pagina.
3. **Conteggio automatico, nessuna etichetta umana**: per pagina, paragrafi
   emessi e paragrafi corti. Chiude la §6.A.
4. **L'utente dà il verdetto** sulle 20 pagine dell'insieme del verdetto: letto
   il `page_ir2.md`, **leggibile** o **illeggibile**; se illeggibile, la causa
   dominante **prima in testo libero**, e solo dopo mappata su una delle quattro
   categorie del §6.B. Il testo libero si conserva nell'esito.
5. **L'utente etichetta i frammenti** delle 5 pagine dell'insieme delle etichette:
   per ogni paragrafo corto, in ordine di lettura, una categoria del §5.
6. Solo allora si contano le §6.C, §6.D e §6.E.

Invertire 4/5 e 6 rende l'etichetta una lettura post-hoc. È il protocollo di
`Criterio_TabellaNormale_v1.md` §3, che ha retto.

**La quota non è realmente nascosta all'etichettatore, e non ci si conta.** Il
passo 3 non la mostra, ma chi etichetta trenta frammenti su una pagina e quattro
su un'altra ha il numeratore sotto gli occhi. È scritto qui perché la protezione
non venga citata come se fosse reale.

**Le tre numerazioni**, che hanno già fatto perdere un giro di etichette:
`idx` 0-based degli script; **pagina del file** 1-based, quella del lettore PDF;
numero **stampato** sulla carta. I render si chiamano
`<M>_pagina{1-based}_idx{0-based}.png` per questo. Le etichette si danno sul
render. **Il numero stampato non si cita.**

## 5. Le categorie dei frammenti, fissate prima

Una sola categoria per frammento, la dominante. Nessun frammento ne prende due.
**Non si aggiungono categorie dopo aver visto i frammenti.**

| categoria | che cos'è sulla pagina |
| --- | --- |
| `titolo` | titolo di sezione, di pannello o di capitolo |
| `etichetta-valore` | una delle due metà di una coppia etichetta:valore — sta insieme a un frammento adiacente |
| `arredo` | intestazione corrente, piè di pagina, numero di pagina, linguetta di capitolo: testo che non dovrebbe stare nel flusso del corpo |
| `elenco` | glifo o numero di elenco separato dal testo della sua voce |
| `spezzone` | frammento di un paragrafo più lungo, spezzato dall'emissione: sulla pagina la frase continua e in uscita si interrompe |
| `corto-legittimo` | è davvero un paragrafo di due parole, ed esce giusto così |
| `altro` | nessuna delle precedenti; richiede una riga di nota |

**`spezzone` esiste perché il §10 dichiara la fusione dei paragrafi come
precondizione del giro successivo**: il progetto sa che quel difetto esiste, e
una tassonomia che non gli desse una casella lo spingerebbe in `altro`, dove la
§6.E impone campione nuovo. Un difetto noto non deve avere una via diretta per
far rifare la misura.

**Lo spareggio fra `titolo` e `etichetta-valore`, fissato qui**: se sulla pagina
il frammento ha un valore attaccato — adiacente, sulla stessa riga o
immediatamente a destra o sotto, e si legge come il suo valore — è
`etichetta-valore`. Altrimenti è `titolo`. Serve perché su una scheda `POSSENTE`
può sembrare l'uno o l'altro, ed è esattamente il caso da cui nasce la domanda.

## 6. Le regole di pass/fail

### 6.A — la diagnosi generalizza, o è di quella pagina

La quota di Wil idx 244 ricalcolata al passo 0 si inserisce nella distribuzione
delle quote del **campione da 40 del §4**, ottenendo un rango fra **1 e 41**
(1 = la più alta).

> **Cade** se il rango è **≤ 4**: meno del 10% delle pagine arriva alla densità
> di frammenti corti della pagina d'origine, quindi quella pagina è un estremo e
> la diagnosi non generalizza al corpus.
>
> **Regge** altrimenti.

**Il 4 è una soglia ed è una scelta, non una derivazione.** La v1 sosteneva di
non averne una: era falso, il percentile era la stessa soglia sull'asse della
frequenza. L'unica giustificazione del 4 è la robustezza — spostare il valore di
una singola pagina non può ribaltare il verdetto — e chiunque voglia applicare
una barra diversa deve poterlo fare, quindi **l'esito riporta il rango esatto e
la distribuzione intera**: minimo, quartili, massimo, e la ripartizione per
manuale.

Un rango **alto** non fa cadere niente: vorrebbe dire che il corpus sta peggio
della pagina da cui la diagnosi è nata.

**Che cosa afferma davvero.** Il test dice se la quota di frammenti corti di
quella pagina è anomala rispetto al corpus. **Non** dice che la forma manchi o
non manchi: il §9 stabilisce che una forma mancante fatta di frammenti da tre
parole è invisibile a questa misura. Le conclusioni vanno scritte deboli quanto
il test.

### 6.B — togliere o costruire: decide il verdetto di pagina

Sulle **20 pagine** dell'insieme del verdetto, fra quelle giudicate
**illeggibili** si contano le cause dominanti mappate su quattro categorie:
`forma mancante`, `arredo di troppo`, `ordine sbagliato`, `contenuto perso o
sbagliato`.

> **Precondizione**: almeno **8** pagine su 20 giudicate illeggibili. Sotto, la
> §6.B si riporta **senza verdetto** — con meno di otto, un margine di 3 è una
> quasi-unanimità di una manciata di pagine travestita da misura. *Meno di otto
> pagine illeggibili su venti è di per sé il risultato più importante del giro e
> va scritto in testa all'esito.*
>
> **`arredo di troppo` supera `forma mancante` di almeno 3 pagine** → il giro
> successivo è la **sottrazione**.
>
> **`forma mancante` supera `arredo di troppo` di almeno 3 pagine** → il giro
> successivo è la **forma**.
>
> **Differenza minore di 3** → **nessuna delle due linee è giustificata da questa
> misura**, e la scelta successiva va fatta su un fatto nuovo, non rileggendo
> questi numeri.

Il margine è 3 e non 1 per lo stesso principio del §6.E: cambiare il verdetto di
una sola pagina muove la differenza di 2 e non deve poter ribaltare la decisione.

Il terzo ramo esiste perché la misura non sia costretta a produrre un vincitore.
Le due cause possono convivere sulla stessa pagina, ed è il caso più probabile.

`ordine sbagliato` e `contenuto perso o sbagliato` non decidono qui e si
riportano: sono due linee diverse, e una di esse — la conservazione dei
caratteri — è già nominata al §10.

### 6.C — quale forma, dalla scomposizione

Si interpreta **solo se la §6.B ha detto «forma»**. Sui frammenti etichettati
delle 5 pagine:

> `titolo` supera `etichetta-valore` di almeno **10 punti percentuali** → si
> costruisce prima il titolo.
>
> `etichetta-valore` supera `titolo` di almeno **10 punti** → prima la coppia.
>
> Differenza minore di 10 punti → si costruiscono nell'ordine che l'utente
> preferisce, e la misura non ha una preferenza da dichiarare.

Questa regola **ordina un lavoro già deciso**, non decide se farlo. Per questo la
sua barra è più bassa e il suo ramo neutro non blocca niente.

### 6.D — che cosa si riporta e non decide

**`arredo` + `elenco` + `spezzone` sui frammenti.** Nella v1 questi numeri
decidevano; ora il verdetto di pagina decide e questi confermano o smentiscono.
Una divergenza forte fra i due — il verdetto dice «forma», i frammenti dicono
`arredo` — è essa stessa un risultato, e va scritta invece di essere appianata.

**L'ordine.** Risalite di oltre 30pt fra paragrafi consecutivi, per pagina, sulle
40. Si riporta e non fa fallire: misurare due cose insieme significa non saperne
falsificare nessuna. Nessuna soglia qui — la v1 diceva «se risulta molto sopra il
4%», e «molto sopra» è esattamente il margine lasciato a chi applica che questo
progetto ha imparato a togliere.

**La quota per manuale**, per vedere se il fenomeno è di un manuale o di tutti:
la firma con cui otto ipotesi sono cadute dopo Milestone 35 è «separano dentro un
manuale, non fra manuali».

### 6.E — lo strumento falsifica se stesso

**Precondizione di numerosità.** Le percentuali della §6.C e della §6.E sono
**pooled** su tutti i frammenti delle 5 pagine.

> Meno di **50 frammenti** etichettati in totale → §6.C e §6.E si riportano
> **senza verdetto**, e non si pescano altre pagine (§4, terminalità).
>
> Una sola pagina fornisce più della metà dei frammenti → idem.

Il 50 è derivato, non scelto: perché un singolo giudizio di etichetta non muova
una barra di più di due punti percentuali, servono almeno 50 frammenti.

**Il veto:**

> `corto-legittimo` ≥ **30%** → il proxy conta come difetto ciò che difetto non
> è. La §6.C **non è interpretabile**, e il 69% va ritirato come diagnosi.
>
> `altro` ≥ **20%** → la tassonomia del §5 era sbagliata e la scomposizione non è
> interpretabile. **Non si aggiungono categorie a posteriori**: si riscrive il
> criterio e si rifà la misura su un campione nuovo.

**Il veto non tocca la §6.A né la §6.B.** La §6.A è un confronto **posizionale**:
un proxy che gonfia la quota in modo uniforme la gonfia sia sulla pagina
d'origine sia sulle 40, e l'errore di modo comune si cancella in gran parte in un
confronto di rango. Il veto sarebbe legittimo solo se il gonfiaggio fosse
*differenziale* fra tipi di pagina, e cinque pagine non possono stabilirlo — un
esito rumoroso su cinque pagine non deve annullare una misura automatica su
quaranta. La §6.B non usa il proxy affatto. **Se il veto scatta**, la §6.A si
riporta col rango e con l'avvertenza che il proxy sovrastima: il **livello** non
va mai citato, solo il rango.

## 7. Il modello nullo, e la sua debolezza dichiarata

**Nullo della §6.A**: la quota di paragrafi corti è una proprietà di Wil p.245 —
una pagina di scheda fitta di badge — e non del corpus; su una pagina tipica i
paragrafi emessi sono prosa e la quota è bassa.

**Debolezza**: il nullo non fa una previsione numerica. Dice «bassa» senza dire
quanto, quindi può essere falsificato solo dalla **posizione** della pagina
d'origine nella distribuzione. È la ragione per cui la §6.A è ordinale. E il
rango della quarta pagina su 41 resta una barra scelta: è dichiarata come tale al
§6.A, e la distribuzione intera si riporta perché chiunque possa applicarne
un'altra.

**Nullo della §6.B**: le pagine illeggibili lo sono in maggioranza per arredo di
troppo, cioè ciò che manca non è una forma ma una sottrazione.

**Debolezza**: il verdetto di pagina è un giudizio unico su un oggetto complesso,
dato da una sola persona che conosce l'ipotesi sotto esame. Il testo libero prima
del menu limita la suggestione, non la elimina. Venti pagine con margine 3
distinguono una maggioranza netta, non una tendenza.

## 8. Limiti dichiarati prima

**I frammenti etichettati sono quelli che il codice ha selezionato.** Una forma
mancante le cui due metà hanno tre parole ciascuna è invisibile alla §6.C. Un
esito basso **non** significa che la forma sia a posto: significa che questa
misura non la vede. È anche la ragione per cui la decisione togliere-o-costruire
è passata al verdetto di pagina, che quel limite non ce l'ha.

**Le esclusioni per costruzione impoveriscono la coda che il test interroga.** Le
circa 114 pagine escluse non sono un campione casuale: furono scelte a suo tempo
*perché difficili*. Toglierle abbassa la distribuzione delle quote sulle 40, il
che rende il rango dell'origine **più basso** e la §6.A **più propensa a cadere**.
Il bias è quindi conservativo per la tesi «generalizza», ma una parte di un
eventuale «cade» sarebbe prodotta dalla costruzione del campione e nessuno potrà
dire quanta.

**Wil p.245 è una pagina di scheda**: vedi §9.

**Il cancello delle note d'asset è chiuso** (Milestone 38, `5bbb5f5`): le note nel
corpo sono 10 e non 75 sul campione di verifica. Chi confronta con numeri
precedenti alla chiusura deve saperlo.

**Le note d'asset non sporcano il proxy**, verificato: escono come riga di
citazione (`> **[immagine inserita]** 120×80 pt — file`), e sono `asset.note`,
escluse dal §2.

**Nessun invariante di conservazione dei caratteri** esiste nel percorso IR 2:
`ir2_validate.py:84` verifica la copertura per **id di primitiva**. Questa misura
non sottrae niente, quindi non ne ha bisogno; il giro successivo sì (§10).

**I numeri di questo giro hanno una scadenza**, ed è dichiarata: il primo
meccanismo che sottragga testo dal flusso cambierà il conteggio dei paragrafi.
Chi citerà il rango della §6.A dopo quel giro deve rifarlo, non ricopiarlo.

## 9. Se la §6.A cade

**Ciò che è stato mostrato è che questo proxy non vede il problema di forma fuori
dalle pagine di scheda** — non che la forma manchi sulle schede. La v1 scriveva
la seconda, che è un'affermazione sul mondo ricavata da un risultato sullo
strumento, e la stessa mossa che il §8 vieta due paragrafi sopra.

**Conseguenza, con il suo cancello di costo.** Una linea «forma sulle schede»
richiede un criterio proprio e un campione **di schede**, che ha lo stesso
problema di costruzione del campione di tabelle — 60 pagine uniformi ne
contengono tre, e le schede hanno lo stesso profilo. È esattamente il costo che
ha messo in pausa la linea tabelle. **Quindi va in pausa con essa**, salvo
decisione esplicita dell'utente che ne accetti il costo. Non è un ripiego a
disposizione: è un cancello.

## 10. Che cosa decidono gli esiti, e che cosa NON decide questo criterio

**Gli esiti portano a lavori diversi**, ed è la correzione del difetto principale
della v1, che li appiattiva tutti sulla stessa azione successiva:

| esito | giro successivo |
| --- | --- |
| §6.A cade | la linea forma non prosegue sul corpus; §9 |
| §6.B = sottrazione | si toglie testo dal flusso — precondizione: **entrambi** i porting |
| §6.B = forma | si costruisce un nodo, nell'ordine della §6.C — precondizione: la sola conservazione dei caratteri, perché costruire un nodo non sottrae primitive |
| §6.B terzo ramo, o senza verdetto | serve un fatto nuovo |

**I due porting procedono in parallelo a questa misura**, per decisione
dell'utente: l'invariante di conservazione dei caratteri in IR 2, e una misura
della fusione dei paragrafi che non sia il criterio della tabella. Sono
**strumenti** e non toccano l'emissione, quindi non cambiano i numeri che questa
misura conta, e sono l'unico punto in cui lo stadio nuovo è più debole del
vecchio (`_verify_content_conservation` esiste in
`scripts/prototype_vertical_slice_page.py:1013`).

**Se la §6.A cade, la §6.B resta valida**: le 20 pagine del verdetto vengono
dalle 40, non da Wil idx 244, e la loro leggibilità non dipende dal rango
dell'origine. Dichiarato qui perché post-esito lo si potrebbe sostenere in
entrambi i sensi.

**Che cosa NON decide.** Il criterio di `text.heading` né la forma della coppia
etichetta-valore: solo se valga la pena costruirli e in quale ordine. Non tocca
nessun producer, non apre Resolution, non accende `--tables` né
`--interrupt-corridor`, non modifica IR 2. Non riapre la linea tabelle, in pausa
per decisione dell'utente. Non decide niente sull'AI locale: l'idea del VLM
locale come **oracolo per costruire un campione** — non come detector in pipeline
— resta aperta, separata, e richiede la sua decisione di Modalità P.
