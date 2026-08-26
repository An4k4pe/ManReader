# Criterio — il numero di pagina **dedotto**, dove il documento non lo dichiara

**Scritto prima di eseguirlo.** Le barre del §5 sono fissate qui e non si toccano
dopo aver visto i risultati. Il giro precedente ha aggiunto per sbaglio un ramo a
metà misura — la deduzione passata alla politica, FW risultava al 100% — e questo
criterio esiste perché quella cosa venga fatta apposta, dichiarata, e messa in
condizione di fallire.

## 0. Che cosa deve chiudere, e che cosa so già

`Esito_ArredoRicorrente_v1.md` registra una caduta misurata: il pavimento
dell'arredo sta al **67,4%** contro una barra di tre quarti, e la caduta è
**interamente** dovuta a due manuali coperti allo 0%.

La causa è nominata e non è «i manuali senza etichetta»: **Wil non dichiara le
etichette e sta al 100%**, perché stampa il numero in basso dove il ramo 2 lo
raggiunge. FW e FWK lo stampano al **centro dei lati**, alternato recto/verso, e
lì nessuna geometria dei due rami arriva.

**Che cosa ho già visto, e va dichiarato perché nessuno creda che questo criterio
sia scritto alla cieca.** La deduzione descritta al §1 esiste già, scritta come
*denominatore* della misura di copertura (`scripts/measure_furniture_coverage.py`),
e su quei manuali trova il numero stampato su **FW 40 pagine su 40, FWK 34 su 40,
Wil 40 su 40**. So quindi che la deduzione *individua* qualcosa. Non so — ed è
ciò che questo criterio mette alla prova — se quello che individua sia **il numero
giusto**, né che cosa succeda al Markdown quando lo si toglie.

## 1. La regola

> **Ramo 3 — la sequenza crescente al margine.**
>
> Si applica **solo a documenti che non dichiarano nessuna etichetta**
> (`page.get_label()` vuoto su tutte le pagine esaminate). Dove il documento
> dichiara, il ramo 1 ha un fatto con cui confrontare e questo ramo tace.
>
> Uno **slot candidato** è un punto della griglia che porta un testo interamente
> numerico su almeno `RECURRENCE_SHARE` delle pagine, e i cui valori sono
> **strettamente crescenti** nell'ordine delle pagine.
>
> Gli slot candidati si **fondono**: un numero stampato a lati alterni vive in
> due slot che sono la stessa cosa. Se due slot rivendicano la **stessa** pagina
> con valori **diversi**, la deduzione **rifiuta** e il documento resta senza
> numero dedotto.
>
> La sequenza fusa dev'essere a sua volta strettamente crescente. Se non lo è,
> **rifiuta**.

**Nessun numero nuovo.** `RECURRENCE_SHARE` è lo 0,25 che il ramo 2 già usa, che
a sua volta viene da `extractor.filter_repeated_blocks`. Un quarto e non metà
perché il numero a lati alterni mette in ogni slot **metà** delle pagine: una
soglia a metà ne prendeva uno solo, ed è il difetto che ha dimezzato il
denominatore della misura precedente. Non c'è vincolo di posizione, per la stessa
ragione per cui il ramo 1 non ce l'ha.

**Rifiutare è una risposta, e dev'essere quella di default.** Le tre condizioni di
rifiuto non sono guardie di comodo: sono il motivo per cui la deduzione può dire
«non lo so». Un meccanismo che deduce sempre qualcosa non è falsificabile.

### Perché non `idx + 1`

Il numero **si legge dalla pagina**, non si sintetizza dalla posizione. Su DIE
l'etichetta a `idx` 50 è `39`: una regola `idx + 1` produrrebbe `51`, cioè
inventerebbe. Il confronto con `idx + 1` resta come **controllo** al §5, mai come
definizione.

## 2. Che cosa succede a ciò che il ramo trova

Due cose distinte, e vanno decise separatamente perché possono fallire
separatamente.

**Rimozione.** Gli slot dedotti entrano negli slot d'arredo, e i nodi interamente
contenuti in essi escono dal corpo verso il canale review — esattamente come per i
primi due rami, senza nessuna macchina nuova.

**Provenienza.** Il numero dedotto diventa la riga `> **[pagina N]**` come per gli
altri manuali. Ma il docstring di `PageIR2` promette oggi che `page_label` è «un
fatto del documento e **non una deduzione**», e questo ramo lo violerebbe in
silenzio.

> **Decisione dichiarata**: `PageIR2` prende un campo additivo
> `page_label_deduced: bool = False`. `page_label` continua a portare il numero
> stampato; il campo dice **come lo sappiamo**. Il docstring va corretto, non
> aggirato.

**Reso identico nel corpo, distinto nell'IR.** Chi legge il Markdown vuole sapere
a che pagina è, e una nota che dica «dedotto» è rumore per lui. Chi consuma l'IR
deve poter rifiutare una deduzione. La distinzione vive dove serve. Questa scelta
è difendibile **solo** se il veto del §5.A regge: se la deduzione potesse
sbagliare numero, renderla indistinguibile sarebbe far mentire il documento.

## 3. Il campione

**Il fatto scomodo di questo ramo**: i manuali su cui deve funzionare — FW, FWK,
Wil — sono gli unici tre senza etichetta dichiarata, quindi sono insieme il
bersaglio e l'intero universo. Non esiste un campione di manuali non spesi su cui
riprovarlo, e questo criterio non può fingere di averne uno.

Da qui la forma del §5: il controllo principale **non** è sui tre manuali del
bersaglio, ma sui **13 che dichiarano** — dove la verità di riferimento esiste e
la deduzione non la può vedere.

Per il veto di contenuto: **8 voci** estratte con seed **`20260904`**, dichiarato
qui, dalle voci che il ramo 3 aggiunge su FW e FWK. Se ne aggiunge meno di 8, si
giudicano tutte e il numero effettivo si riporta.

## 4. Come si giudica

Come il criterio precedente: un agente cieco sull'esito atteso etichetta ogni
voce `arredo` / `contenuto` / `incerto`, l'utente vede le contestate più un terzo
delle altre.

**Tre correzioni al protocollo, dai difetti misurati del giro scorso:**

1. Il sorteggio del terzo di controllo usa il seed **`20260905`**, dichiarato qui
   e non dopo aver visto le risposte.
2. Nessuna voce può essere **pre-decisa** dall'utente prima di essergli
   sottoposta come controllo: il giro scorso due delle quattro lo erano, e il
   controllo indipendente era n=2 mentre il verbale diceva 4.
3. Un dubbio espresso in prosa **è** un `incerto`. Il giro scorso l'agente ha
   dichiarato 12 `arredo` su 12 e ha scritto dubbi su 4, che sono arrivati
   all'umano fuori dal canale previsto.

L'esito si riporta **per ramo**, e le voci del ramo 3 si contano separate da
quelle dei rami 1 e 2.

## 5. Pass/fail

### A. Veto di verità — il controllo principale

> Si esegue la deduzione sui **13 manuali che dichiarano le etichette**,
> ignorando le etichette dichiarate, e si confronta il numero dedotto con quello
> dichiarato, pagina per pagina.
>
> **Cade se su una sola pagina la deduzione produce un numero diverso da quello
> dichiarato.**

Zero tolleranza, e la ragione non è di stile: un numero sbagliato reso come
provenienza è **invenzione**, cioè la cosa che il §1 di `PageIR2` esiste per
impedire, e il §2 di questo criterio ha scelto di renderla indistinguibile da un
fatto. Se la deduzione può sbagliare, quella scelta va rifatta.

**Astenersi non è sbagliare**: un manuale su cui la deduzione rifiuta non fa
cadere niente, si conta e si riporta. Un ramo che tace su metà dei manuali è
debole, non falso, e la debolezza la misura il pavimento.

**Questa barra ha i denti, e lo si può mostrare prima di eseguirla**: la regola
nulla `idx + 1` la fallisce, perché su DIE produce `51` dove il documento dichiara
`39`. Si esegue anche il modello nullo, e **se il modello nullo passasse, la barra
sarebbe finta** e il criterio andrebbe riscritto invece che dichiarato scaricato.

**Il campione esercita il meccanismo dove non lavorerà mai**, ed è voluto: i 13
manuali con etichetta sono l'unico posto dove esiste una verità di riferimento che
la deduzione non ha prodotto lei stessa. È l'esatto rovescio del difetto del giro
scorso, dove il campione poteva solo confermare.

### B. Pavimento — la barra che è caduta, invariata

> La copertura totale sui **dieci manuali mai spesi**, misurata da
> `scripts/measure_furniture_coverage.py --modo completo`, deve raggiungere
> **tre quarti**.

Oggi sta a **67,4%** (250/371). La barra è quella di
`Criterio_ArredoRicorrente_v3.md` §5 e non si muove: spostarla adesso sarebbe
tarare sul risultato che è appena mancato.

Si riporta **anche** la copertura per manuale, perché la media nasconde: Kul sta
al 38% e **resta fuori dalla portata di questo ramo** (dichiara le etichette,
quindi il ramo 3 tace). Kul è un difetto del **ramo 1** — trova un solo slot dove
il manuale stampa il numero in più posti — ed è un fascicolo suo, non da sanare
qui di straforo.

### C. Veto di contenuto — invariato

> Cade se una sola voce tolta dal ramo 3 è giudicata `contenuto`.

Vale per le voci nuove. Come il giro scorso, il campione misura la precisione e
non la copertura: la copertura è la barra B, e le due si leggono insieme.

### D. La giunzione — la clausola che il giro scorso **non ha eseguito**

> Per ogni voce tolta si guarda il paragrafo immediatamente **sopra e sotto**.
> Cade se due paragrafi si saldano male dove l'arredo li separava.

Non è una ripetizione: è un debito. `State.md` la dichiara il difetto atteso di
ogni meccanismo che sottragga testo, il giro scorso l'ha lasciata in bianco, e il
criterio è rimasto non scaricato per questo.

**E lo strumento ovvio non serve**: `scripts/check_paragraph_conservation.py`
confronta due `document_ir2.json`, che l'arredo non tocca. Il difetto vive **nel
Markdown**, e va guardato lì, a occhio, su pagine rese.

### Se cade

- **A** — la deduzione è falsa: il ramo non si spedisce in nessuna forma, e la
  provenienza dedotta del §2 va ritirata con lui.
- **B** — il ramo non basta: si riporta quanto ha aggiunto e **non si ritocca
  nessuna soglia** per superare la barra. Il §5 del criterio precedente lo vieta
  già per il ramo 2; vale identico qui.
- **C** o **D** — difetto di rimozione, non di deduzione: il numero dedotto può
  restare come provenienza anche se la rimozione va rifatta. Sono due cose
  separate proprio perché possano fallire separate.

## 6. Che cosa resta fuori

- **Kul e il ramo 1** (§5.B).
- **I titoli correnti in cima**, che il ramo 2 lascia per scelta dichiarata.
- **L'etichetta verticale al bordo** (`IL COLPO`, `GRIFFONS`, `TACTICIAN`) e il
  numero di capitolo in alto a sinistra su BiD, nominati dall'agente il giro
  scorso e non rappresentati da nessuna voce.
- **Allargare il ramo 3 ai documenti che dichiarano.** Se il veto A regge
  perfettamente su 13 manuali, la tentazione sarà di farlo scattare anche dove il
  ramo 1 manca qualcosa — cioè su Kul. **Richiede un criterio nuovo**: allargare
  la portata dopo aver visto che il meccanismo funziona è la stessa mossa che il
  §3 vieta, e il fatto che questo criterio la nomini in anticipo non la autorizza.
- **La domanda che conta.** Questo criterio misura numeri sull'arredo, non la
  leggibilità del Markdown. `State.md` chiama la rimozione dell'arredo «la
  precondizione del primo `page.md` consultabile», e la misura di questo round è
  un file leggibile a occhio umano. Il §5.D è il solo pezzo che guarda il
  Markdown, e non basta a rispondere.

## 7. Debiti che questo criterio si iscrive

Il codice che produce i numeri del §5.A va committato con il criterio, non dopo:
`AGENTS.MD` §18, e il giro scorso il debito identico è stato iscritto dal criterio
precedente e pagato solo a esito riscritto.
