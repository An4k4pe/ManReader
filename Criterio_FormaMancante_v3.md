# Criterio — togliere o costruire: lo decide chi legge la pagina (v3)

Registrato **prima** della misura, prima dell'estrazione del campione e prima di
scrivere lo script che la esegue. Da committare in un commit **senza codice**
(`AGENTS.MD` §15).

Decide **una** cosa: se il giro successivo debba **togliere** testo dal flusso o
**costruire** una forma. La decide un giudizio umano sul Markdown emesso, non un
proxy.

Posizione dichiarata entrando, che è dell'utente e non ipotesi di Chat A: gli
altri producer vanno sfruttati per **sottrarre** elementi già identificati, così
che ogni meccanismo successivo abbia meno rumore da giudicare; e `column_band`
deve funzionare benissimo, perché da un suo errore sbagliano troppe cose e
l'ordine di lettura è fra le prime cose che si vedono in un Markdown. La linea
tabelle è **in pausa** per decisione dell'utente.

---

## 0. Changelog

La v1 e la v2 non sono state committate. Due giri di revisione indipendente in
conversazioni disgiunte — **metodologico** sulla v1, **architetturale** sulla v2 —
prima del commit, per non spendere ore di misura su un criterio difettoso.

### Dalla v1 alla v2 (giro metodologico)

Verdetto: non committare così. Accolte: il **passo 0** (il 69% veniva da una
configurazione non dichiarata, e su quella pagina — l'unica delle dodici in cui
una tabella fosse stata costruita — la lista dei paragrafi cambia con `--tables`);
il **rango** al posto del percentile, con la soglia ammessa come scelta; la
categoria **`spezzone`**; il minimo di frammenti, il pooling, il tetto per pagina;
il veto ristretto; la **terminalità** del campione; la disambiguazione di
«campione cieco»; «molto sopra il 4%» tolto; il §9 riscritto. Su indicazione
dell'utente il **verdetto di pagina** è passato da conteggio riportato a misura
che decide.

Respinte, con ragione: «i numeri scadono perché il lavoro successivo cambia la
fusione dei paragrafi» — i due porting sono strumenti, non modifiche
all'emissione; e «40 pagine estratte possono non essere 40 utilizzabili» — il
campionatore continua a pescare fino alla taglia
(`scripts/sample_ir2_verification_pages.py:148-159`).

### Dalla v2 alla v3 (giro architetturale)

Verdetto: committabile dopo sei decisioni bloccanti, senza rifare la sequenza.
Nessun invariante di `AGENTS.MD` violato, campione da 40 immune al problema del
campione tabelle, configurazione del §3 corretta.

**La decisione più grossa, presa dall'utente**: il test di rango sulla pagina
d'origine **non decide più**. Costava metà del documento — passo 0, barra, modello
nullo, il §9 con il suo cancello, il paragrafo sul bias — mentre la v2 stessa
dichiarava che il verdetto di pagina sopravviveva comunque al suo esito. Il
vincolo di `AGENTS.MD` §15 sul caso d'origine resta soddisfatto: il verdetto di
pagina testa **la diagnosi stessa** — «è la forma che manca» — invece di un suo
correlato numerico, e Wil idx 244 resta escluso dal campione. Il rango si calcola
e si **riporta** (§6.C). Numerazione: la vecchia §6.B diventa **§6.A**, la vecchia
§6.E diventa **§6.B**, le vecchie §6.A/§6.C/§6.D confluiscono in **§6.C**.

Altre accolte: la **quinta categoria** per le note d'asset fuori posto, perché
`ordine sbagliato` era un pozzo in cui finivano due dei quattro modi in cui Wil
p.245 esce male più metà dell'obiettivo del progetto; la precondizione sul numero
di pagine che finiscono nelle **due categorie che decidono**, non sul numero di
illeggibili; il **pin di revisione** del §3; il bias delle esclusioni dichiarato
anche per il verdetto di pagina, dove spinge nella direzione scomoda; la misura
dell'ordine riscritta in una forma eseguibile; le pagine su cui lo script esce
non-zero; il pool corretto; la scelta dichiarata sulle 11 pagine di
`Campione_TabellaInIR2_v1.md`; il §6.C della v2 (quale forma costruire per prima)
**tolto come regola** e ridotto a conteggio riportato.

**Un errore di Chat A, corretto**: la v2 derivava il minimo di 50 frammenti da
«un giudizio non muove una barra di più di due punti». Vero per una **quota**,
falso per la **differenza** fra due percentuali, che si muove di 2/N — lo stesso
raddoppio che la v2 applicava correttamente due sezioni sopra. Rilievo del giro
architetturale. Caduta la regola che usava una differenza, il 50 resta corretto
per ciò che ora protegge.

**Tre precedenti nel repo che nessuna versione precedente citava**, trovati dal
giro architetturale e verificati: vedi §9.

## 1. Il caso d'origine

`Esito_TabellaInIR2_v1.md` §1-ter, su **Wil idx 244** (pagina del file 245):
55 paragrafi emessi, 38 di ≤2 parole (69%), 2 risalite oltre 30pt (4%).
Conclusione tratta allora: «l'ordine è quasi giusto, è la forma che manca».

**Quei numeri non sono utilizzabili come stanno.** La configurazione che li ha
prodotti non è dichiarata in nessun documento, e su quella pagina la lista dei
paragrafi cambia a seconda di `--tables`: `Esito_TabellaInIR2_v1.md` §5 registra
che senza il flag il comportamento è identico su **11 pagine su 12**, «e la
dodicesima differisce solo con il flag acceso» — la dodicesima è Wil p.245,
l'unica del campione in cui una tabella sia stata costruita. Il **passo 0** del §4
li rifà sotto la configurazione del §3. Finché non è eseguito, il 69% è citabile
solo come «il numero pubblicato».

Il passo 0 è una **riparazione**, non un ingresso di una regola: dopo il
declassamento del rango, nessuna decisione di questo criterio dipende da quel
numero.

**E il conteggio nudo non basterebbe comunque.** Una linguetta di capitolo fatta
di testo, un'intestazione corrente, un numero di pagina, un glifo di elenco
separato dal suo testo — difetto a verbale su DB p.53 in Milestone 38 — e lo
spezzone di un paragrafo rotto dall'emissione sono tutti paragrafi di ≤2 parole.
Il conteggio non distingue «manca una forma» da «avanza dell'arredo» da
«l'emissione ha spezzato una frase». È la ragione per cui a decidere è un
giudizio umano sulla pagina, e il conteggio si riporta.

## 2. Il proxy, fissato prima

Serve al §6.B e al §6.C. Non decide.

**Paragrafo emesso** = un nodo con `kind == "text.paragraph"`, letto da
`document_ir2.json` e non dal Markdown reso. L'esclusione delle note d'asset è
**per `kind` ed è ermetica**: `NodeIR2` porta «esattamente uno fra `text`,
`asset`, `structure`», quindi un nodo `asset.note` ha `text=None` e non può
entrare in `len(node.text.split())`. Con la configurazione del §3 l'esclusione dei
nodi `structure` è un **no-op** — `--tables` è l'unica sorgente di `structure` —
ed è scritta per non dipendere da quel fatto.

**Paragrafo corto** = `len(node.text.split()) <= 2`. Separazione sui soli spazi,
**nessuna pulizia**: niente rimozione di punteggiatura, niente scarto dei token di
soli simboli. Qualunque pulizia sarebbe un giudizio, e un giudizio è ciò che si
può ricalibrare dopo aver visto l'esito. La chiusura di Milestone 38 ha già
mostrato un caso in cui i caratteri non sono ciò che sembrano — sui badge di
DrW p.97 `á` è U+00E1 e il simbolo del bersaglio è la lettera `o`.

**Quota della pagina** = paragrafi corti / paragrafi emessi.

**Pagine troppo corte**: una pagina che emette **meno di 10** paragrafi non entra
nella distribuzione riportata e si elenca a parte. Una quota su tre paragrafi è
rumore. Soglia fissata qui, prima, non tarata.

Nessuna di queste costanti è una soglia geometrica nella pipeline: sono costanti
di protocollo di misura, e la regola «soglie mai hardcoded» riguarda le prime.

## 3. La configurazione, fissata prima

```
./venv/bin/python scripts/prototype_ir2_page.py \
    --pdf <manuale>.pdf --page-number <idx+1> --output-dir <dir>
```

`--tables` **spento** (il suo criterio è caduto). `--interrupt-corridor`
**spento** (decisione di Milestone 37). `--base` non passato — la ragione non è
che il criterio non misuri l'ordine, perché il §6.C lo misura: è che `--base`
agisce **a valle dell'emissione** (`scripts/prototype_ir2_page.py:365-390`, dopo
che `document_ir2.json` e `page_ir2.md` sono già scritti) e non può muovere né la
segmentazione né il conteggio. Vale identica per il passo 0.

**Pin di revisione.** Fra il passo 0 e il passo 4 del §4 **non atterra nulla** in
`scripts/prototype_ir2_page.py` né nei moduli `ir2_*`. Il §10 fa correre due
porting in parallelo a questa misura: se una guardia di conservazione atterrasse
in quello script a metà produzione, la stessa riga di comando smetterebbe di
produrre artefatti sulle pagine che la rompono — non cambierebbe che cosa
l'emettitore emette, ma **quali pagine contribuiscono**. Fissare i flag non basta:
va fissata la revisione. Il commit di partenza si registra nell'esito.

Cambiare configurazione dopo aver visto l'esito richiede un criterio nuovo: è la
lettura post-hoc che `AGENTS.MD` §15 vieta, ed è già successo quattro volte in
questo progetto per criteri scelti iterando.

## 4. Il campione, e l'ordine dei passi

**Seed `20260824`**, dichiarato qui prima dell'estrazione. **40 pagine** uniformi
dai 16 manuali. Corpus 5.201 pagine; tolte le ~113 esclusioni sotto, il pool
effettivo è **≈5.088**.

**Escluse per costruzione**, indici 0-based:

| gruppo | pagine |
| --- | --- |
| sviluppo IR 2 (Milestone 38) | DB 98, DB 17, DB 52, DB 49, Dag 83, Dag 163, DrW 96 |
| criterio schede mostro | DB 89, DrM 86, Vil 222 |
| sviluppo tabelle | le 29 voci distinte di `NORMAL_TABLE_EXCLUSIONS` |
| **sviluppo tabelle, mancanti da quella lista** | **DB 61, Lan 18, Lan 51, Wil 77** |
| campione di verifica di Milestone 38, già giudicato | FWK 122, BiD 287, Apo 34, Vil 64, FWK 31, Wil 71, Dag 199, Fab 126, BoB 297, BiD 314 |
| campione di `Criterio_TabellaNormale_v1.md` | l'elenco letterale di `Campione_TabellaNormale_v1.md` §«Le 60 pagine» |

**Le 60 si escludono per elenco letterale, non rieseguendo il campionatore**, ed è
ciò che immunizza questo giro da quanto segue.

**Che cosa manca dove, verificato.** Le quattro pagine in grassetto sono elencate
fra le pagine di sviluppo in `Criterio_EstensioneRegioneTabella_v1.md:41-42`, e
due compaiono nelle righe di comando committate di
`scripts/inspect_table_gutter_regularity.py:22` e
`scripts/compare_table_gutters_with_column_band.py:16`. **La sorgente della
lacuna non è lo script**: `Criterio_TabellaNormale_v1.md:59-62` elenca 18 pagine
di sviluppo e lo script le copia; le quattro mancano **nel criterio**, scritto
nello stesso commit del criterio gemello che già ne elencava 17.

**Un difetto che sta fuori da questo criterio e va scritto perché non si perda.**
`NORMAL_TABLE_EXCLUSIONS` ha oggi **29 voci distinte** (35 scritte, 6 duplicate),
mentre `Campione_TabellaNormale_v1.md:18` dichiara 28 esclusioni totali «7 + 3 +
18». Le 11 in più sono state appese allo script **dopo** l'estrazione. La riga di
comando documentata a `Campione_TabellaNormale_v1.md:9-12` oggi ne escluderebbe
39 e produrrebbe **un campione diverso da quello che quel file dichiara di
rigenerare**. Il campione da 60 **non è contaminato** — verificato voce per voce,
nessuna pagina di sviluppo vi compare, e il verdetto di `Esito_TabellaNormale_v1.md`
regge — ma quel file ha bisogno di una nota, o il prossimo che rigenera crederà di
avere le stesse 60.

**Le 11 pagine di `Campione_TabellaInIR2_v1.md` restano nel pool, ed è una
scelta.** Su di esse Milestone 39 ha eseguito la stessa riga di comando del §3 e
ne ha confrontato gli elenchi di paragrafi contro un baseline, ma **l'utente non
ne ha letto il Markdown** — l'unica letta è Wil 244, che è esclusa. Poiché a
decidere è il giudizio umano sul `page_ir2.md`, la cecità che conta è intatta.
Dichiarato qui perché il principio del §4 è «escluse per costruzione: già
guardate», e questa è un'eccezione motivata, non una dimenticanza.

**Guardie di ammissibilità**: quelle di `_is_admissible` — `rotation != 0`,
`mediabox != cropbox`, pagina senza testo. Gli scarti si riportano. Il
campionatore continua a pescare fino a raggiungere la taglia.

**Le pagine su cui lo script esce non-zero** — guardia pagina, round-trip,
esclusione silenziosa — **si elencano e non si sostituiscono**. La guardia
dell'esclusione silenziosa esiste dalle rettifiche di Milestone 38 proprio perché
scatti, e una pagina che la fa scattare è un risultato, non un intoppo.

**La procedura di estrazione annidata**, perché l'esito non dipenda dall'ordine
delle operazioni. Dall'ordine casuale che il seed produce sul pool:

- le prime **40** ammissibili sono il **campione da 40**;
- le prime **20** di quelle 40, nel loro ordine di estrazione, sono l'**insieme
  del verdetto**;
- le prime **5** di quelle 20, nello stesso ordine, scartando una pagina il cui
  manuale sia già uscito e le pagine «troppo corte» del §2, sono l'**insieme delle
  etichette**. Le pagine saltate si elencano.

Il filtro «troppo corte» dipende dall'uscita del codice, ed è dichiarato prima per
questo: è l'unico punto in cui l'estrazione non è funzione del solo seed.

**40, 20 e 5 sono terminali.** Aumentarne una dopo aver visto un esito è un
criterio nuovo con campione nuovo. **Non esiste «guardiamone altre cinque»**: il
seed protegge da *quali* pagine, non da *quante*.

**I passi, in quest'ordine:**

0. Si ricalcola **Wil idx 244** sotto la configurazione del §3 e si registra la
   sua quota nell'esito. È una pagina, e ripara un numero oggi non confrontabile.
1. Si estrae il campione col seed. Verbale dell'estrazione come per i campioni
   precedenti.
2. Per ciascuna si producono `page_ir2.md`, `document_ir2.json` e il **render**.
3. **Conteggio automatico, nessuna etichetta umana**: paragrafi emessi e
   paragrafi corti per pagina. Serve al §6.C.
4. **L'utente dà il verdetto** sulle 20 pagine: letto il `page_ir2.md`,
   **leggibile** o **illeggibile**; se illeggibile, la causa dominante **prima in
   testo libero**, e solo dopo mappata su una delle cinque categorie del §6.A. Il
   testo libero si conserva integralmente nell'esito.
5. **L'utente etichetta i frammenti** delle 5 pagine: per ogni paragrafo corto, in
   ordine di lettura, una categoria del §5.
6. Solo allora si contano §6.A, §6.B e §6.C.

Invertire 4/5 e 6 rende l'etichetta una lettura post-hoc.

**La quota non è realmente nascosta all'etichettatore, e non ci si conta.** Il
passo 3 non la mostra, ma chi etichetta trenta frammenti su una pagina e quattro
su un'altra ha il numeratore sotto gli occhi. Scritto perché la protezione non
venga citata come se fosse reale.

**Le tre numerazioni**, che hanno già fatto perdere un giro di etichette: `idx`
0-based degli script; **pagina del file** 1-based, quella del lettore PDF; numero
**stampato** sulla carta. I render si chiamano
`<M>_pagina{1-based}_idx{0-based}.png` per questo. **Il numero stampato non si
cita.**

## 5. Le categorie dei frammenti, fissate prima

Una sola categoria per frammento, la dominante. **Non si aggiungono categorie
dopo aver visto i frammenti.**

| categoria | che cos'è sulla pagina |
| --- | --- |
| `titolo` | titolo di sezione, di pannello o di capitolo |
| `etichetta-valore` | una delle due metà di una coppia etichetta:valore — sta insieme a un frammento adiacente |
| `arredo` | intestazione corrente, piè di pagina, numero di pagina, linguetta di capitolo |
| `elenco` | glifo o numero di elenco separato dal testo della sua voce |
| `spezzone` | frammento di un paragrafo più lungo, spezzato dall'emissione: sulla pagina la frase continua e in uscita si interrompe |
| `corto-legittimo` | è davvero un paragrafo di due parole, ed esce giusto così |
| `altro` | nessuna delle precedenti; richiede una riga di nota |

**`spezzone` esiste perché il §10 dichiara la fusione dei paragrafi come
precondizione del giro successivo**: il progetto sa che quel difetto esiste, e una
tassonomia che non gli desse una casella lo spingerebbe in `altro`, dove il veto
del §6.B impone campione nuovo. Un difetto noto non deve avere una via diretta per
far rifare la misura.

**Spareggio fra `titolo` e `etichetta-valore`**: se sulla pagina il frammento ha
un valore attaccato — adiacente, sulla stessa riga o immediatamente a destra o
sotto, e si legge come il suo valore — è `etichetta-valore`. Altrimenti è
`titolo`. Serve perché su una scheda `POSSENTE` può sembrare l'uno o l'altro, ed è
il caso da cui nasce la domanda.

## 6. Le regole

### 6.A — togliere o costruire: **l'unica regola che decide**

Sulle **20 pagine** dell'insieme del verdetto, ogni pagina illeggibile porta una
causa dominante mappata su cinque categorie:

`forma mancante` · `arredo di troppo` · `note d'asset fuori posto` ·
`ordine sbagliato` · `contenuto perso o sbagliato`

**Solo le prime due decidono.** Le altre tre si riportano, e ciascuna è una linea
diversa già nominata altrove: le note d'asset fuori posto sono il difetto
dell'ancora per `y`, dichiarato non risolto in Milestone 38; l'ordine e la perdita
di contenuto sono i due porting del §10.

> **Precondizione**: almeno **8** pagine su 20 illeggibili **con causa dominante
> in una delle due categorie che decidono**. Sotto, la §6.A si riporta **senza
> verdetto**.
>
> **`arredo di troppo` supera `forma mancante` di almeno 3** → il giro successivo
> è la **sottrazione**.
>
> **`forma mancante` supera `arredo di troppo` di almeno 3** → il giro successivo
> è la **forma**.
>
> **Differenza minore di 3** → **nessuna delle due linee è giustificata**, e la
> scelta va fatta su un fatto nuovo.

La precondizione è sulle due categorie che decidono e non sul totale delle
illeggibili: con dodici illeggibili di cui quattro decidenti, un margine di 3 su
quattro pagine sarebbe una quasi-unanimità travestita da misura. **La quinta
categoria esiste per questo**: senza, i difetti dell'ancora e dell'ordine
finivano nel pozzo `ordine sbagliato`, e su una pagina di scheda — la famiglia da
cui l'intera linea nasce — due dei quattro modi in cui Wil p.245 esce male sono
esattamente quelli.

*Meno di 8 pagine illeggibili in totale è di per sé il risultato più importante
del giro e va scritto in testa all'esito.*

Il margine è 3 e non 1 perché cambiare il verdetto di una sola pagina muove la
differenza di 2 e non deve poter ribaltare la decisione.

Il terzo ramo esiste perché la misura non sia costretta a produrre un vincitore.

### 6.B — lo strumento falsifica se stesso

Vale sulla **scomposizione** del §6.C, che è l'unica cosa che può smentire il
verdetto del §6.A. Percentuali **pooled** su tutti i frammenti delle 5 pagine.

> Meno di **50 frammenti** etichettati in totale, oppure una sola pagina che ne
> fornisce più della metà → la scomposizione si riporta **senza interpretazione**,
> e non si pescano altre pagine (§4, terminalità).
>
> `corto-legittimo` ≥ **30%** → il proxy conta come difetto ciò che difetto non è.
> La scomposizione non è interpretabile e il 69% va ritirato come diagnosi.
>
> `altro` ≥ **20%** → la tassonomia del §5 era sbagliata. **Non si aggiungono
> categorie a posteriori**: si riscrive il criterio e si rifà su campione nuovo.

Il 50 è derivato: perché un singolo giudizio non muova una **quota** di più di due
punti percentuali. Vale per una quota e non per una differenza fra due quote, che
si muoverebbe del doppio — la v2 confondeva le due, ed è la ragione per cui qui
non c'è nessuna regola costruita su una differenza fra categorie di frammenti.

**Il veto non tocca il §6.A**, che non usa il proxy affatto: il verdetto è un
giudizio umano sul Markdown.

### 6.C — che cosa si riporta e non decide

**Il rango della pagina d'origine.** La quota di Wil idx 244 dal passo 0,
collocata nella distribuzione delle quote del campione da 40, con la
distribuzione intera: minimo, quartili, massimo, ripartizione per manuale. Nella
v2 questo decideva; non decide più, e il §8 dice che cosa se ne può concludere.

**La scomposizione dei frammenti** per le sette categorie del §5. È la sola cosa
che può **smentire** il §6.A: una divergenza forte — il verdetto dice «forma», i
frammenti dicono `arredo` — è essa stessa un risultato e va scritta invece di
essere appianata. Non si costruisce nessuna regola su di essa: vedi §9 sul perché
il suo valore informativo è più basso di quanto la v2 assumesse.

**L'ordine**, nella sola forma eseguibile disponibile: **quante volte l'utente ha
nominato l'ordine nel testo libero** della causa dominante, prima della mappatura.
Costa zero e misura la cosa da dentro il verdetto.

La v2 chiedeva invece «risalite di oltre 30pt fra paragrafi consecutivi». **Non è
eseguibile e non è definita**: `NodeIR2` non porta geometria — i suoi campi sono
`node_id, order, kind, primitive_ids, page_ids, text, asset, structure,
candidate_ids, resolution` — e `document_ir2.json` non emette bbox per i nodi di
testo; nessuno script nel repo calcola quelle risalite; e il «4%» pubblicato non è
ricostruibile, perché 2/55 fa 3,6% e 2/54 fa 3,7%. Il 30pt è inoltre una costante
in punti, cioè la cosa che questo progetto ha già smontato una volta in
`column_band` a favore di misure desunte dal documento. Se un giorno servirà, va
definita in **interlinee mediane della pagina** e con lo script committato.

## 7. Il modello nullo, e la sua debolezza dichiarata

**Nullo del §6.A**: le pagine illeggibili lo sono in maggioranza per arredo di
troppo, cioè ciò che manca non è una forma ma una sottrazione.

**Debolezza**: il verdetto di pagina è un giudizio unico su un oggetto complesso,
dato da una sola persona che conosce l'ipotesi sotto esame. Il testo libero prima
del menu limita la suggestione, non la elimina. Venti pagine con margine 3
distinguono una maggioranza netta, non una tendenza. E la mappatura dal testo
libero alle cinque categorie è un secondo giudizio, che va fatto dalla stessa
persona e registrato accanto al testo originale, non al posto suo.

## 8. Limiti dichiarati prima

**Le esclusioni per costruzione tirano il campione dalla parte facile.** Le ~113
pagine escluse non sono un campione casuale: furono scelte a suo tempo *perché
difficili*. Le 20 pagine del verdetto sono quindi **più facili** del corpus, e la
spinta è **contro** la precondizione delle 8 pagine decidenti. Se la precondizione
non è raggiunta, non si può distinguere «l'uscita è buona» da «il campione è
stato ripulito delle pagine dure», e l'esito va scritto così. È il rovescio del
bias, e sta dalla parte scomoda: la v2 lo dichiarava solo dove era conservativo.

**Che cosa si può concludere dal rango, e che cosa no.** Se il rango mostra che
Wil idx 244 è un estremo, ciò che è stato mostrato è che **il proxy dei frammenti
corti non vede il problema fuori dalle pagine di scheda** — non che la forma
manchi sulle schede. Un risultato sullo strumento non è un'affermazione sul mondo.
E qualunque estrapolazione al corpus della diagnosi «è la forma che manca»
resterebbe ingiustificata: quella linea richiederebbe un campione **di schede**,
che ha lo stesso problema di costruzione del campione di tabelle — 60 pagine
uniformi ne contengono tre — cioè esattamente il costo che ha messo in pausa la
linea tabelle.

**I frammenti etichettati sono quelli che il codice ha selezionato.** Una forma
mancante le cui due metà hanno tre parole ciascuna è invisibile alla
scomposizione. È anche la ragione per cui a decidere è il verdetto di pagina, che
quel limite non ce l'ha.

**Il cancello delle note d'asset è chiuso** (Milestone 38, `5bbb5f5`): le note nel
corpo sono 10 e non 75. Chi confronta con numeri precedenti deve saperlo.

**I numeri di questo giro hanno una scadenza**: il primo meccanismo che sottragga
testo dal flusso cambierà il conteggio dei paragrafi. Chi citerà la distribuzione
del §6.C dopo quel giro deve rifarla, non ricopiarla.

## 9. I tre precedenti nel repo, che nessuna versione precedente citava

Trovati dal giro architetturale e verificati da Chat A. Stanno qui perché chi
eseguirà il giro successivo non creda di partire da zero.

**Un criterio di titolo desunto dal documento esiste già in produzione.**
`config.py:45` definisce `heading_font_size_threshold = 1.3`, usato a
`epub_builder.py:93` come `median_size * threshold` ed esposto come
`--heading-threshold` a `main.py:284`. **Non è una soglia in punti**: è un
moltiplicatore sulla mediana del corpo, configurabile — la forma che questo
progetto ha già ratificato, e `page_analysis_column_band.py:478` `_median_font_size`
fornisce lo stesso ingrediente nella pipeline nuova.

**E ce ne sono altri due, che si contraddicono.** `ir_builder.py:533`
`_looks_like_section_heading_block` (14.0pt fissi più l'hardcode `"Scena "`, usato
a `:356` e `:373` per impedire che un titolo di sezione sia letto come titolo di
callout) e `markdown_builder.py:179` `_is_heading_text` (≤90 caratteri, maiuscolo
≤40, 14.0pt, 18.0pt). Più `extractor.py:4313` `_double_column_zone_boundary`, che
riconosce un titolo a piena larghezza per il **reading order**. Chi legge
«`text.heading`: criterio inesistente» parte da tre implementazioni, due delle
quali in disaccordo — 14.0pt fissi contro 1,3× la mediana.

**La coppia etichetta-valore è a verbale da Milestone 36.** `State.md:913`: le
schede statistiche mostro «contengono testo strutturato a campi etichetta:valore
da preservare... possibile candidato per un futuro `structural_kind` dedicato»,
collegato al quarto punto bloccante di Milestone 33. È la stessa conclusione a cui
la scomposizione arriverebbe, messa agli atti **una milestone prima** di Wil p.245
e indipendentemente da essa. Non annulla la scomposizione — un appunto non è una
misura — ma abbassa ciò che aggiunge, ed è parte del perché non costruisce più
nessuna regola.

**Asimmetria che ne segue, e che il criterio dichiara**: `text.heading` è nominato
nel vocabolario di `ir2_model.py:58-67` con la nota «il criterio non esiste,
milestone sua»; la coppia etichetta-valore **non è nel vocabolario affatto**. Le
due metà non costano lo stesso e non sono ugualmente istruite.

## 10. Che cosa decidono gli esiti

| esito del §6.A | giro successivo |
| --- | --- |
| **forma** | si costruisce un nodo. Precondizione: la sola conservazione dei caratteri — costruire un nodo non sottrae primitive. Si parte dai precedenti del §9. |
| **sottrazione** | si toglie testo dal flusso. Precondizioni: **entrambi** i porting **e** una decisione architetturale dedicata — vedi sotto. |
| terzo ramo, o senza verdetto | serve un fatto nuovo |

**Il ramo sottrazione richiede una milestone, non solo due strumenti.** Il §5
definisce `arredo` come intestazione corrente, piè di pagina, numero di pagina e
linguetta di capitolo, che è **marginalia** parola per parola, e `AGENTS.MD:599`
vieta «l'esclusione automatica di marginalia» senza decisione architetturale
dedicata (e `:598` il detector automatico su marginalia e bande laterali). Il
precedente è a tre voci e uniforme: Milestone 26 aprì «clustering» così,
Milestone 34 «resolution», Milestone 38 «IR 2» — Modalità P più due giri di
revisione disgiunti. **L'etichettatura umana di questo criterio non è un detector
e non viola niente**; è il giro successivo che va aperto come si deve, e la v2
prometteva quel giro elencando due porting e non la milestone.

**I due porting procedono in parallelo a questa misura** — sono strumenti e non
toccano l'emissione — ma **non sono un trapianto**, e il §3 li tiene fuori dalla
finestra di produzione col pin di revisione. `ir2_builder.join_lines` **toglie il
trattino** alla giunzione di sillabazione (`return f"{left[:-1]}{right}"`,
`ir2_builder.py:197`), mentre `_non_space_multiset` della fetta verticale conta
ogni carattere non-spazio, trattino compreso — e la fetta non sillaba, unisce con
`" ".join(words)`. Portare quell'invariante così com'è lo renderebbe **falso per
costruzione** su ogni pagina che ricompone una parola spezzata, caso a verbale su
DB p.99 (`dimez-`/`zati`). Il porting richiede quindi di **decidere che cosa
significhi conservazione quando l'emettitore toglie caratteri di proposito**: è
una scelta sul contratto dell'emettitore, non uno strumento da spostare.

**Che cosa questo criterio NON decide.** Il criterio di `text.heading` né la forma
della coppia etichetta-valore: solo se valga la pena costruirli. Non tocca nessun
producer, non apre Resolution, non accende `--tables` né `--interrupt-corridor`,
non modifica IR 2. Non riapre la linea tabelle, in pausa per decisione
dell'utente. Non decide niente sull'AI locale: il VLM locale come **oracolo per
costruire un campione** — non come detector in pipeline — resta aperto, separato,
e richiede la sua decisione di Modalità P.
