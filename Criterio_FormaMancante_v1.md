# Criterio — «è la forma che manca»: generalizza, e quale forma

Registrato **prima** della misura, prima dell'estrazione del campione e prima di
scrivere lo script che la esegue. Da committare in un commit **senza codice**
(`AGENTS.MD` §15).

Decide due cose, in quest'ordine: se la diagnosi nata su Wil p.245 vale per il
corpus o solo per quella pagina; e, se vale, se il giro successivo debba
**togliere** testo dal flusso o **costruire** una forma. Sotto la prima domanda
non c'è niente da costruire, e questo criterio esiste per poterlo scoprire prima
di costruirlo.

Posizione dichiarata entrando, che è dell'utente e non ipotesi di Chat A: gli
altri producer vanno sfruttati per **sottrarre** elementi già identificati, così
che ogni meccanismo successivo abbia meno rumore da giudicare; e `column_band`
deve funzionare benissimo, perché da un suo errore sbagliano troppe cose e
l'ordine di lettura è fra le prime cose che si vedono in un Markdown. La linea
tabelle è **in pausa** per decisione dell'utente fino a che le esclusioni non
sono maggiori.

---

## 1. Il caso d'origine, che questo criterio deve vincolare

`Esito_TabellaInIR2_v1.md` §1-ter, su **Wil idx 244** (pagina del file 245):

| | |
| --- | --- |
| paragrafi emessi | 55 |
| paragrafi di ≤2 parole | **38 (69%)** |
| risalite di oltre 30pt fra paragrafi consecutivi | 2 (4%) |

Conclusione tratta allora: «l'ordine è quasi giusto, è la forma che manca», e il
69% mescolerebbe titoli di sezione e coppie etichetta-valore.

**Una pagina sola.** `AGENTS.MD` §15 impone che il criterio vincoli il caso da
cui l'affermazione è nata: è il §6.A, e Wil idx 244 è escluso dal campione
proprio perché è il caso sotto esame, non un elemento del campione.

**E il 69% non è interpretabile com'è.** Una linguetta di capitolo fatta di
testo, un'intestazione corrente, un numero di pagina e un glifo di elenco
separato dal suo testo — difetto già a verbale su DB p.53 in Milestone 38 — sono
tutti paragrafi di ≤2 parole. Il conteggio nudo non distingue «manca una forma»
da «avanza dell'arredo», e le due cose indicano lavori diversi. Per questo la
misura è una **scomposizione**, non un conteggio.

## 2. Il proxy, fissato prima

**Paragrafo emesso** = un nodo con `kind == "text.paragraph"` nella IR 2 della
pagina, letto da `document_ir2.json` e non dal Markdown reso. I nodi
`asset.note` e gli eventuali nodi con `structure` **non** sono paragrafi e non
entrano né a numeratore né a denominatore.

**Paragrafo corto** = `len(node.text.split()) <= 2`. Separazione sui soli spazi,
**nessuna pulizia**: niente rimozione di punteggiatura, niente scarto dei token
di soli simboli. Qualunque pulizia sarebbe una decisione, e la chiusura di
Milestone 38 ha già mostrato un caso in cui i caratteri non sono ciò che
sembrano — sui badge di DrW p.97 `á` è U+00E1 e il simbolo del bersaglio è la
lettera `o`. Lo split sugli spazi è l'unica regola che non richiede un giudizio.

**Quota della pagina** = paragrafi corti / paragrafi emessi.

**Pagine troppo corte**: una pagina che emette **meno di 10** paragrafi non entra
nel calcolo della distribuzione e si riporta a parte. Una quota su tre paragrafi
è rumore. La soglia è fissata qui, prima, e non è tarata. Se queste pagine sono
più di **un quarto** del campione, la §6.A non è interpretabile e va detto invece
di calcolarla lo stesso.

## 3. La configurazione, fissata prima

**Una sola**, dichiarata prima di vedere il campione perché la misura non diventi
una scelta fra varianti:

```
./venv/bin/python scripts/prototype_ir2_page.py \
    --pdf <manuale>.pdf --page-number <idx+1> --output-dir <dir>
```

`--tables` **spento** (il suo criterio è caduto, `Esito_TabellaInIR2_v1.md`).
`--interrupt-corridor` **spento** (decisione di Milestone 37, non riaperta qui).
`--base` non passato: questo criterio non misura l'ordine, vedi §7.

Cambiare configurazione dopo aver visto l'esito richiede un criterio nuovo.
Cambiarla qui sarebbe la lettura post-hoc che `AGENTS.MD` §15 vieta, e in questo
progetto è già successo quattro volte per criteri scelti iterando.

## 4. Il campione, e l'ordine dei passi

**Seed `20260824`**, dichiarato qui prima dell'estrazione. **40 pagine**
uniformi dal pool dei 16 manuali (5.194 pagine).

**Escluse per costruzione**, indici 0-based:

| gruppo | pagine |
| --- | --- |
| sviluppo IR 2 (Milestone 38) | DB 98, DB 17, DB 52, DB 49, Dag 83, Dag 163, DrW 96 |
| criterio schede mostro | DB 89, DrM 86, Vil 222 |
| sviluppo tabelle, già in `NORMAL_TABLE_EXCLUSIONS` | Dag 117/133/135/136/194, DB 75/122, DrM 32/35/267, DrW 32/239/247, BoB 238, Wil 73/244, Lan 40/109/118/284, Fab 52/256/272/280, SV 43/189, Apo 46, Vil 166, FW 62 |
| **sviluppo tabelle, mancanti dallo script** | **DB 61, Lan 18, Lan 51, Wil 77** |
| campione cieco di Milestone 38, già giudicato | FWK 122, BiD 287, Apo 34, Vil 64, FWK 31, Wil 71, Dag 199, Fab 126, BoB 297, BiD 314 |
| campione di `Criterio_TabellaNormale_v1.md` (seed `20260822`, 60 pagine) | l'elenco di `Campione_TabellaNormale_v1.md` §«Le 60 pagine» |

Le quattro pagine della riga in grassetto **non sono un sospetto**:
`Criterio_EstensioneRegioneTabella_v1.md:41-42` le elenca fra le pagine di
sviluppo, e due compaiono nelle righe di comando committate di
`scripts/inspect_table_gutter_regularity.py` e
`scripts/compare_table_gutters_with_column_band.py`. Mancano da
`NORMAL_TABLE_EXCLUSIONS`: è un difetto dello script, verificato, e va corretto
nel commit che implementa questo criterio.

Le 60 pagine del campione tabelle si escludono perché su quelle l'utente ha già
dato **un'etichetta a vista sul render**. Costa 60 pagine su 5.194 e toglie una
discussione.

**Guardie di ammissibilità**: le stesse di `_is_admissible` —
`rotation != 0`, `mediabox != cropbox`, pagina senza testo. Gli scarti si
riportano.

**I passi, in quest'ordine:**

1. Si estraggono le 40 pagine col seed. Si riporta il verbale dell'estrazione
   come per i campioni precedenti.
2. Per ciascuna si producono, con la configurazione del §3, `page_ir2.md`,
   `document_ir2.json` e il **render** della pagina.
3. **Conteggio automatico, nessuna etichetta umana**: per pagina, paragrafi
   emessi e paragrafi corti. Questo passo chiude da solo la §6.A, che non
   dipende da nessuna etichetta.
4. Si estraggono **5 pagine** dalle 40 con lo stesso seed, scartando una pagina
   il cui manuale sia già uscito e le pagine del §2 «troppo corte». L'estrazione
   è per seed, **mai** guidata dai numeri del passo 3.
5. **L'utente etichetta**, e in quest'ordine:
   a. letto il `page_ir2.md` della pagina, **un** verdetto: leggibile /
      illeggibile;
      se illeggibile, **una sola** causa dominante fra «forma mancante»,
      «arredo di troppo», «ordine sbagliato», «contenuto perso o sbagliato»;
   b. per **ogni** paragrafo corto della pagina, in ordine di lettura, una
      categoria del §5.
   La quota della pagina calcolata al passo 3 **non viene mostrata** prima che
   l'etichettatura sia finita.
6. Solo allora si contano le §6.B e §6.C.

Invertire 5 e 6 rende l'etichetta una lettura post-hoc. È il protocollo di
`Criterio_TabellaNormale_v1.md` §3, che ha retto.

**Le tre numerazioni**, che hanno già fatto perdere un giro di etichette:
`idx` 0-based degli script; **pagina del file** 1-based, quella del lettore PDF;
numero **stampato** sulla carta. I render si chiamano
`<M>_pagina{1-based}_idx{0-based}.png` per questo. Le etichette si danno sul
render. **Il numero stampato non si cita.**

## 5. Le categorie, fissate prima

Una sola categoria per frammento, la dominante. Nessun frammento ne prende due.
**Non si aggiungono categorie dopo aver visto i frammenti.**

| categoria | che cos'è sulla pagina |
| --- | --- |
| `titolo` | titolo di sezione, di pannello o di capitolo |
| `etichetta-valore` | una delle due metà di una coppia etichetta:valore — sta insieme a un frammento adiacente |
| `arredo` | intestazione corrente, piè di pagina, numero di pagina, linguetta di capitolo: testo che non dovrebbe stare nel flusso del corpo |
| `elenco` | glifo o numero di elenco separato dal testo della sua voce |
| `corto-legittimo` | è davvero un paragrafo di due parole, ed esce giusto così |
| `altro` | nessuna delle precedenti; richiede una riga di nota |

**Lo spareggio fra `titolo` e `etichetta-valore`, fissato qui**: se sulla pagina
il frammento ha un valore attaccato — adiacente, sulla stessa riga o
immediatamente a destra o sotto, e si legge come il suo valore — è
`etichetta-valore`. Altrimenti è `titolo`. Serve perché su una scheda `POSSENTE`
può sembrare l'uno o l'altro, ed è esattamente il caso da cui nasce la domanda.

## 6. Le regole di pass/fail

### 6.A — la diagnosi generalizza, o è di quella pagina

> **Cade** se la quota di Wil idx 244 (**69%**) sta **sopra il 90° percentile**
> delle quote per pagina del campione cieco: allora il 69% è una proprietà di
> quella pagina, non del corpus, e la diagnosi «è la forma che manca» non
> generalizza.
>
> **Regge** se ci sta dentro.

Una quota d'origine **sotto** il 10° percentile non fa cadere niente: vorrebbe
dire che il corpus sta peggio della pagina da cui la diagnosi è nata.

Non c'è una soglia di livello perché non ce n'è una difendibile: il confronto è
posizionale contro il campione, e chiede esattamente la domanda che falsifica.

### 6.B — che cosa costruire, dalla scomposizione

Sui frammenti etichettati delle 5 pagine:

> `arredo` + `elenco` ≥ **50%** → il giro successivo è la **sottrazione**.
>
> `titolo` + `etichetta-valore` ≥ **50%** → il giro successivo è la **forma**.
>
> Nessuna delle due arriva al 50% → **nessuna delle due linee è giustificata da
> questa misura**, e la scelta successiva va fatta su un fatto nuovo, non
> rileggendo questi numeri.

Il terzo ramo esiste perché la misura non sia costretta a produrre un vincitore.
Le due cause possono convivere sulla stessa pagina, ed è il caso più probabile.

### 6.C — lo strumento falsifica se stesso

> `corto-legittimo` ≥ **30%** → il proxy conta come difetto ciò che difetto non
> è. Il 69% va **ritirato come diagnosi**, non ridimensionato, e né la §6.A né la
> §6.B sono interpretabili.
>
> `altro` ≥ **20%** → la tassonomia del §5 era sbagliata e la scomposizione non è
> interpretabile. **Non si aggiungono categorie a posteriori**: si riscrive il
> criterio e si rifà la misura su un campione nuovo.

## 7. Il modello nullo, e la sua debolezza dichiarata

**Nullo della §6.A**: la quota di paragrafi corti è una proprietà di Wil p.245 —
una pagina di scheda fitta di badge — e non del corpus; su una pagina tipica i
paragrafi emessi sono prosa e la quota è bassa.

**Debolezza**: il nullo non fa una previsione numerica. Dice «bassa» senza dire
quanto, quindi può essere falsificato solo dalla **posizione** della pagina
d'origine nella distribuzione, non da un livello assoluto. È la ragione per cui
la §6.A è comparativa. E su 40 pagine il 90° percentile è la quarta pagina più
alta: è un estimatore grossolano, e per questo l'esito riporta la distribuzione
intera — minimo, quartili, massimo, e la ripartizione per manuale — non il solo
percentile.

**Nullo della §6.B**: i frammenti corti sono in maggioranza arredo, cioè ciò che
manca non è una forma ma una sottrazione.

**Debolezza**: cinque pagine distinguono un 80/20 da un 50/50, non un 55/45 da un
45/55. La barra del 50% è uno strumento grossolano **per costruzione**, ed è
scritto qui perché nessuno la citi come precisa.

## 8. I conteggi che si riportano e non decidono

**L'ordine.** Risalite di oltre 30pt fra paragrafi consecutivi, per pagina.
Si riporta e non fa fallire: misurare due cose insieme significa non saperne
falsificare nessuna (stessa ragione di `Criterio_TabellaNormale_v1.md` §6). Ma se
risulta molto sopra il 4% di Wil p.245, è la cosa che deciderebbe il giro dopo, e
va scritta anche se scomoda.

**Il verdetto di pagina.** Quante delle 5 pagine l'utente giudica leggibili, e
con quale causa dominante quando non lo sono. È il numero più vicino all'obiettivo
di tutto il giro, e non può decidere qui perché non esiste una base con cui
confrontarlo. Va registrato: diventa la base della prossima volta.

**La quota per manuale.** Serve a vedere se il fenomeno è di un manuale o di
tutti — la firma con cui otto ipotesi sono cadute dopo Milestone 35 è
«separano dentro un manuale, non fra manuali».

## 9. Limiti dichiarati prima

**I frammenti etichettati sono quelli che il codice ha selezionato.** Una forma
mancante le cui due metà hanno tre parole ciascuna è invisibile a questa misura.
Un esito basso della §6.B **non** significa che la forma sia a posto: significa
che questa misura non la vede. Non c'è modo di chiuderlo qui.

**Wil p.245 è una pagina di scheda.** Se la §6.A cade, la conclusione onesta non è
«la forma non serve»: è «la forma manca sulle schede, non sul corpus». È una
linea più stretta, con un costo dichiarato — richiede un criterio proprio e un
campione **di schede**, che ha lo stesso problema di costruzione del campione di
tabelle. Scritto qui prima perché non diventi un salvataggio a posteriori.

**Il cancello delle note d'asset è chiuso** (Milestone 38, `5bbb5f5`): le note nel
corpo sono 10 e non 75 sul campione cieco. Chi confronta con numeri precedenti
alla chiusura deve saperlo.

**Le note d'asset non sporcano il proxy**, verificato: escono come una riga di
citazione (`> **[immagine inserita]** 120×80 pt — file`), e comunque sono
`asset.note`, escluse dal §2.

**Nessun invariante di conservazione dei caratteri** esiste nel percorso IR 2:
`ir2_validate.py:84` verifica la copertura per **id di primitiva**. Questa misura
non sottrae niente, quindi non ne ha bisogno; il giro successivo, qualunque sia,
sì.

## 10. Che cosa NON decide

Non decide il **criterio** di `text.heading` né la **forma** della coppia
etichetta-valore: decide solo se valga la pena costruirli.

Non tocca nessun producer, non apre Resolution, non accende `--tables` né
`--interrupt-corridor`, non modifica IR 2.

Non riapre la linea tabelle, in pausa per decisione dell'utente.

Non decide niente sull'AI locale. L'idea del VLM locale come **oracolo per
costruire un campione** — non come detector in pipeline — resta aperta e separata,
e richiede la sua decisione di Modalità P; questa misura non la usa e non ne
dipende.

Non decide se portare in IR 2 l'invariante di conservazione dei caratteri né la
misura della fusione dei paragrafi: sono le precondizioni del giro **successivo**,
qualunque dei due esca dalla §6.B.
