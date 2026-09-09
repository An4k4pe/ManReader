# Milestone 42 — perche' `column_band` non emette bande. Verbale della diagnostica

Criterio pre-registrato: `Criterio_BandeMancanti_v1.md` (Fase 1 e Fase 2, la
seconda scritta dopo l'esito della prima e prima dei suoi dati).
Script: `scripts/scan_missing_column_bands.py`, che importa **invariate** le
funzioni del producer di produzione. Nessuna soglia toccata, nessun producer
modificato, nessun wiring.

## Esito delle predizioni
- **H1 (`too_short` e' la causa): FALSIFICATA.** Sulle 14 pagine senza bande del
  Dragonbane Quickstart `too_short` scarta 1 corridoio su 15.
- **H2 (nessun corridoio incatenato): vera su 7 pagine su 14**, ma per una
  ragione che non e' un difetto: quelle pagine hanno 1-3 righe di testo.
- **H3 (distribuzione diversa fra pagine con e senza bande): confermata.**
  Senza bande: `too_few_lines` 86,7%. Con bande: 56,0%, con `too_few_wordy_lines`
  al 32,8% e `too_short` all'11,2%.
- **K1 (il testo fuori banda sta sopra la prima o sotto l'ultima): CONFERMATA**,
  94,6% sul Quickstart, e dominante su tutti e cinque i manuali di benchmark.

Attribuzione completa: **0 pagine senza causa**, su tutte e 14. Il criterio di
accettazione (residuo non attribuito sotto il 5%) e' soddisfatto.

## La domanda era mal posta, ed e' un rilievo contro chi l'ha posta
«Perche' non emette bande» era la domanda sbagliata. **12 delle 14 pagine senza
bande sono frontespizi e stacchi**: una pagina con due righe non ha colonne, e
non averle riconosciute non e' un difetto. Il numero «43 pagine su 47 hanno testo
fuori dalle bande», che avevo riportato io, contava le pagine con **almeno una**
riga fuori: la quota reale di testo fuori banda e' il **6,1%**.

Il problema vero e' quello, e sta concentrato: pagina 28 ha 52 span su 98 fuori,
pagina 35 ne ha 45 su 81, pagina 33 41 su 80.

## Cosa succede davvero, misurato
    pagina 28: testo da y 81 a y 763.  Bande: y 418-750.
    pagina 33: testo da y 286 a y 763. Banda:  y 300-464.
    pagina 35: testo da y 266 a y 763. Banda:  y 280-440.

La banda copre **il tratto in cui il corridoio e' dimostrato**, e li' si ferma.
Sopra e sotto, la pagina resta senza struttura di colonna — anche dove a occhio
le colonne ci sono. Su pagina 28 e' la meta' superiore, ed e' prosa a due
colonne: e' esattamente il testo che l'utente ha visto interlacciato.

Perche' il corridoio si ferma: vale finche' non viene **attraversato**. Nella
meta' superiore di pagina 28 ci sono tabelle a tutta larghezza, che lo tagliano.
Il meccanismo si comporta come dichiarato in Milestone 37.

## I criteri di ammissione non sono il colpevole — ispezionato, non assunto
I tre corridoi scartati piu' alti dei campioni, guardati riga per riga
(`AGENTS.MD` §Regole operative punto 14, ispezionare prima di progettare):

| caso | corridoio | cosa c'e' a sinistra |
| --- | --- | --- |
| Dragonbane p.29 | 17,3 righe, `too_few_wordy_lines` | `1 2 3 4 5 6`: la colonna del d6 della tabella attacchi |
| Fab p.191 | 34,1 righe, `too_few_wordy_lines` | `190`, `W`, `Chimerista`: numero di pagina, glifo, testatina |
| Apo p.30 | 7,5 righe, `too_few_wordy_lines` | `h h h`: tre glifi decorativi di margine |

**Nessuno dei tre e' un separatore fra due colonne di prosa.** In tutti e tre
`too_few_wordy_lines` scarta correttamente. Il criterio che `AGENTS.MD` elenca
come questione aperta qui fa il suo mestiere; non e' li' che si perde l'ordine.

## Conclusione
Il difetto non e' in `column_band` e non e' in una soglia. E':

> **Nessuno ha deciso cosa governa la parte di pagina che nessuna banda copre.**
> Il consumer, non avendo un ordine, ne inventa uno per `y` — e lo fa in
> silenzio, che e' il guasto che questo progetto vieta.

Due direzioni, **nessuna scelta qui**:
1. **Piu' bande.** Un elemento a tutta larghezza che attraversa un corridoio non
   chiude la pagina: chiude una fascia e ne apre un'altra. Sopra la tabella di
   pagina 28 c'e' una struttura a due colonne che oggi non produce banda perche'
   il suo corridoio e' spezzato. E' il rovescio di
   `Criterio_InterruzioneCorridoio_v1.md`, che l'interruzione la usa per
   tagliare, non per aprire.
2. **Dichiararlo.** La regione che nessuna banda governa esce con una nota che
   dice che il suo ordine non e' stabilito. Non risolve, ma toglie il silenzio,
   ed e' gia' implementata nel giro Markdown del 6 settembre.

Le due non si escludono: la seconda vale comunque per il residuo della prima.

## Testo proposto per `State.md`, da incollare quando si decide
> ## Milestone 42 — perche' `column_band` non emette bande (diagnostica pura)
> Diagnostica sola, nessun producer e nessuna soglia toccati. Criterio
> pre-registrato in `Criterio_BandeMancanti_v1.md`, script
> `scripts/scan_missing_column_bands.py`. Campione: Dragonbane Quickstart per
> intero (il caso d'origine) piu' 20 pagine da ciascuno di DB, Fab, Dag, Apo,
> Lan con seed 20260906.
> Predizione H1 falsificata; K1 confermata su sei manuali. Attribuzione completa
> delle pagine senza bande. La domanda d'origine era mal posta: 12 pagine senza
> bande su 14 sono frontespizi, e la quota reale di testo fuori banda e' il 6,1%,
> concentrata su poche pagine. La causa e' che una banda copre solo il tratto in
> cui il corridoio e' dimostrato: sopra e sotto, la pagina non ha struttura di
> colonna e il consumer ordina per `y` **in silenzio**. I tre corridoi scartati
> piu' alti sono stati ispezionati e nessuno e' un separatore fra colonne di
> prosa. Resta aperto, e non deciso qui: cosa governa la parte di pagina che
> nessuna banda copre.

---

# Fase 3 — quanto e' grande davvero il problema

Criterio in `Criterio_BandeMancanti_v1.md` §Fase 3, registrato prima dei dati.
Una riga fuori banda fa danno **solo se ha righe affiancate** (sovrapposte in y,
disgiunte in x). Titoli, tabelle a tutta larghezza e prosa a colonna unica
stanno fuori dalle bande, e per loro l'ordine per `y` e' quello giusto.

## La pagina dello schizzo dell'utente si comporta gia' bene
DB.pdf indice 25 (stampata 24), quella con ETÀ | NOME sopra la tabella
`EFFETTI DELL'ETÀ`: 5 bande, 87 span su 92 dentro.
    banda y   0-236  2 colonne, gutter x 299-314   <- ETÀ | NOME
    banda y 236-274  3 colonne                      <- la tabella
    banda y 274-288  2 colonne
    banda y 288-374  3 colonne
    banda y 458-750  2 colonne, gutter x 297-314   <- sotto ATTRIBUTI
La banda del corridoio ETÀ|NOME **finisce dove comincia la tabella**, e sotto il
titolo `ATTRIBUTI` se ne apre un'altra: e' esattamente il comportamento che lo
schizzo indica come corretto. Su questa pagina non manca niente.

## La pagina che fallisce ha un'altra causa
Quickstart p.28, la pagina vista schiacciata. La sua meta' alta e':
    y  81  'EVENTI CASUALI'                     titolo a tutta larghezza
    y 108-132  due colonne di prosa, TRE RIGHE  x 95-292  |  x 313-511
    y 151-405  tabella TIRO/EVENTO              a tutta larghezza
Il corridoio fra le due colonne del cappello e' alto ~2 righe di pagina contro le
3 di `min_gutter_lines`: scartato da `too_short`. **Non e' un corridoio spezzato
da un elemento a tutta larghezza** — e' un blocco a due colonne troppo corto per
la soglia. Il resto del fuori banda di quella pagina e' la tabella, dove `y` e'
l'ordine giusto: il danno sono **6 righe**, non 52.

## Il danno, misurato su sei manuali
| manuale | fuori banda | di cui affiancate | danno sul testo di pagina |
| --- | --- | --- | --- |
| Dragonbane Quickstart | 6,1% | 51,7% | 3,2% |
| DB | 2,6% | 81,7% | 2,1% |
| Fab | 36,8% | 14,1% | 5,2% |
| Dag | 3,3% | 28,6% | 0,9% |
| Apo | 4,9% | 0,0% | 0,0% |
| Lan | 3,6% | 16,2% | 0,6% |

**P1 falsificata come affermazione generale**: prevedevo oltre il 60% di fuori
banda «solo» ovunque; regge su Fab, Dag, Apo e Lan, cade su DB (18,3%) e sul
Quickstart (48,3%).

## Cosa resta vero, e cosa va ritrattato
**Ritratto il modo in cui ho presentato il problema.** «43 pagine su 47 hanno
testo fuori dalle bande» contava le pagine con almeno una riga fuori e non
distingueva il testo che un ordine di colonna non lo vuole. Il danno reale e'
fra lo **0% e il 5,2%** del testo di pagina, concentrato in pochi blocchi.

Resta vero, e non e' stato toccato: quel danno e' **silenzioso**. Il consumer
ordina per `y` senza dichiarare che non ha una struttura di colonna, ed e' il
guasto che il progetto vieta a prescindere dalla sua dimensione.

E la direzione «piu' bande» cambia bersaglio: il caso da trattare **non** e' il
corridoio spezzato da un elemento a tutta larghezza — quello funziona gia' — ma
il **blocco affiancato troppo corto** perche' il suo corridoio raggiunga il
minimo in righe di pagina. Non e' deciso qui, e non si sposta nessuna soglia
prima di aver visto pagine marcate a mano.

---

# Correzione: il numero «~2 righe» era inventato, e il fatto vero e' piu' netto

Rilievo dell'utente: «se e' alto tre righe misurera' tre righe». Ha ragione, e
il valore che avevo scritto non l'avevo misurato — l'avevo dedotto. Misurato:

    corridoio del cappello, Quickstart p.28:  y 110,0-144,0  =  34,00pt
    interlinea mediana DELLA PAGINA:                            11,35pt
    minimo richiesto, 3 righe:                                  34,06pt

**Scartato per 0,06pt.** Non e' un blocco «troppo corto»: manca la soglia per sei
centesimi di punto.

E il difetto sotto e' un altro, gia' visto tre volte in questo progetto: le tre
righe del cappello hanno passo **12,0pt**, la mediana della pagina e' **11,35**.
Il criterio giudica un BLOCCO con l'unita' della PAGINA. In righe proprie il
corridoio ne misura 2,83; in righe di pagina esattamente 3,00. Un blocco
affiancato di tre righe sta sul filo del criterio e passa o cade per differenze
sotto il punto — che e' peggio di una soglia sbagliata, perche' non e'
prevedibile.

E' la stessa regola che il lavoro sulle schede ha imparato a caro prezzo: *ogni
statistica si calcola sulla popolazione della regione, mai sul documento*.
Registrata qui come quarta occorrenza, su codice di produzione questa volta.
Nessuna soglia toccata.

# Pagine proposte per la verifica a vista

Ordinate per **danno** (span affiancati letti senza struttura di colonna), non
per testo fuori banda. Numero stampato **letto dai margini della pagina**, non
dedotto da uno scostamento.

| manuale | stampata | indice | danno | fuori banda | bande |
| --- | --- | --- | --- | --- | --- |
| DB | 122 | 123 | 80 span | 87/242 | 2 |
| DB | 60 | 61 | 57 span | 92/92 | **0** |
| DB | 86 | 87 | 51 span | 84/114 | 1 |
| DB | 102 | 103 | 43 span | 70/80 | 1 |
| DB | 96 | 97 | 23 span | 43/73 | 1 |
| Quickstart | 27 | 28 | 26 span | 52/98 | 2 |
| Quickstart | 28 | 29 | 26 span | 61/61 | **0** |
| Quickstart | 32 | 33 | 24 span | 41/80 | 1 |
| Quickstart | 34 | 35 | 24 span | 45/81 | 1 |

Controlli, danno zero e molto testo: DB stampata 74 (indice 75, 294 span, 7
bande); DB indice 125 (278 span, 3 bande); DB indice 3 (239 span, 1 banda).

---

# Verifica a vista dell'utente: 6 pagine marcate, e una mia conclusione ritratta

L'utente ha marcato sei pagine di DB: **rosso** = banda che si forma, **blu** =
banda che dovrebbe formarsi e non si forma. Confronto col meccanismo:

| pagina (indice/stampata) | corridoio | righe | fianchi / con parole | esito | marcatura |
| --- | --- | --- | --- | --- | --- |
| 25 / 24  ETÀ NOME | x 299-314 | — | — | AMMESSO | rosso |
| 61 / 60  IMPREVISTI MAGICI | x 111-118 | 49,3 | 20 / **0** | `too_few_wordy_lines` | **blu** |
| 89 / 88  FANTASMA | x 77-84 | 30,0 | 6 / **0** | `too_few_wordy_lines` | **blu** |
| 89 / 88  FANTASMA | x 300-330 | 15,0 | 11 / 11 | AMMESSO | rosso |
| 97 / 96  RAGNO GIGANTE | x 77-84 | 17,1 | 6 / **0** | `too_few_wordy_lines` | **blu** |
| 97 / 96  RAGNO GIGANTE | x 302-313 | 8,2 | 5 / 5 | AMMESSO | rosso |
| 103 / 102 IMPREVISTI | x 112-118 | 34,4 | 13 / **0** | `too_few_wordy_lines` | **blu** |
| 103 / 102 INCONTRI CASUALI | x 296-313 | 5,1 | 5 / 5 | AMMESSO | rosso |
| 123 / 122 TESORI 2 | x 87-92 | 48,3 | 21 / **0** | `too_few_wordy_lines` | **blu** |
| 123 / 122 TESORI 2 | x 150-171 | 29,6 | 18 / 12 | AMMESSO | rosso |

**Sei pagine su sei, dieci corridoi su dieci.** Ogni blu e' lo stesso scarto:
`too_few_wordy_lines` con **zero righe con parole** dal lato della colonna dei
numeri di dado. Ogni rosso e' un corridoio ammesso. La pagina 123 e' il caso piu'
netto: nella STESSA tabella il separatore `TESORO | VALORE` e' ammesso e quello
`D20 | TESORO` no, e l'unica differenza sono i caratteri che portano le righe di
fianco.

## Ritratto la conclusione della Fase 1
Avevo scritto: «nessuno dei tre corridoi ispezionati e' un separatore fra colonne
di prosa, `too_few_wordy_lines` scarta correttamente, non e' li' che si perde
l'ordine». **E' sbagliato.** Avevo ispezionato tre casi e generalizzato; il
giudizio a vista su sei pagine dice che la colonna dei numeri di una tabella e'
un separatore di colonna a tutti gli effetti, e che quel criterio e' esattamente
dove l'ordine si perde. Mi ero fermato su un campione scelto da me.

## Il dato che rende la correzione praticabile
`too_few_wordy_lines` mette insieme due cose diverse, e **un producer gia' wired
le separa**:

| caso | `table_candidate` che contiene il corridoio |
| --- | --- |
| DB 61, colonna del D20 (blu) | **1** — bbox (96,7 · 117,6)-(508,7 · 722,3) |
| DB 103, colonna del D12 (blu) | **1** — bbox (79,4 · 129,9)-(532,5 · 722,3) |
| Fab 191, numero di pagina + testatina | **0** |
| Apo 30, glifi decorativi di margine | **0** |

Cioe': i corridoi che l'utente vuole tenere stanno dentro un `table_candidate`,
quelli di arredo no. La distinzione che manca al producer esiste gia' nel
contratto di un altro producer, e `AGENTS.MD` §Layout e candidati dice dove va
usata: «la relazione fra candidati di producer diversi si decide in Resolution o
nel consumer, **mai dentro un producer**». `too_few_wordy_lines` e' precisamente
un producer che filtra i propri candidati per anticipare una decisione del
consumer — il caso che `AGENTS.MD` elenca come questione aperta, citando proprio
questo criterio. La marcatura dell'utente la chiude: il corridoio si emette.

## Avvertenza da non perdere per il giro successivo
Emettere la banda **non basta** a leggere bene una tabella. Una banda a due
colonne letta come colonne da' «tutti i numeri, poi tutte le descrizioni», che su
una tabella e' l'ordine sbagliato. La banda e' il fatto strutturale giusto; la
lettura per RIGHE e' una decisione del consumer, e l'informazione per prenderla
e' il `table_candidate` che copre la stessa regione. Le due cose vanno tenute
distinte o si sostituisce un difetto con un altro.

---

# Secondo giro di marcature: nove pagine, e i quattro dubbi chiusi

L'utente ha marcato altre nove pagine di DB. **Sei sono esattamente le pagine
che avevo proposto come dubbie**, quindi i quattro dubbi hanno una risposta.

## La regola che regge su tutte le pagine con uno scarto
Ogni scarto osservato su quindici pagine e' `too_few_wordy_lines` con **zero**
righe con parole da un lato (unica eccezione uno `too_short` a 2,82 righe). E gli
scarti si dividono in due gruppi netti, separati da un producer gia' wired:

**Dentro un `table_candidate` — l'utente li vuole (blu):**
    ORCO 111        x  63- 69  27,1 righe   9 fianchi /  0 con parole
    ARMI IMPR. 120  x  77- 84  40,5 righe   6 /  0
    TESORI 1  121   x  77- 84  23,3 righe   3 /  0
    TESORI 1  121   x  88- 95  16,4 righe  11 /  0
    piu' i cinque gia' verificati (IMPREVISTI, IMPREVISTI MAGICI, TESORI 2,
    FANTASMA, RAGNO GIGANTE)

**Fuori da ogni tabella — l'utente NON li ha marcati:**
    MAGO 20         x  74- 75  10,4 righe   5 /  0
    I GOBLIN 115    x  74- 74  10,7 righe   3 /  0
    SALA GRANDE 117 x  74- 74  18,7 righe   4 /  0
    SALA GRANDE 117 x  74- 74  14,2 righe   3 /  0
    TORRE 119       x  74- 75  28,5 righe   6 /  0

Il secondo gruppo sta sempre a **x 74**, ed e' lo stesso elemento in tutto il
manuale: il **rientro sospeso** degli elenchi `✦` (marcatore a x 63,7, righe di
continuazione a x 76,8). Non e' una colonna, e l'utente non l'ha marcato.

**Il discriminatore `table_candidate` riproduce il giudizio a vista su ogni
pagina in cui c'e' uno scarto.** E' il dato che rende la correzione praticabile
senza inventare un criterio nuovo.

## I quattro dubbi, chiusi
1. **Rientro sospeso** (DB 119, 117, 115, 20): l'utente marca in rosso il
   separatore principale e **lascia non marcato** il corridoio a x 74. La regola
   proposta lo scarta correttamente. Dubbio chiuso a favore della regola.
2. **Due tabelle affiancate** (ARMI IMPROVVISATE 120): il separatore centrale
   (x 294-319, 47,1 righe) e' ammesso ed e' rosso; le due colonne dei numeri
   (x 77-84 e x 96-98) sono scartate e sono blu. La frammentazione in quattro
   bande dello stesso separatore non e' stata segnalata come problema.
3. **`too_short` sul filo** (ROUND E INIZIATIVA 41): il corridoio principale
   (28,0 righe) e' ammesso; quello da 2,82 righe e' scartato e non e' stato
   marcato. Il caso di confine non risulta un problema su questa pagina.
4. **Quattordici bande** (ARMI A DISTANZA 75): **tutti e 13 i corridoi sono
   ammessi, zero scarti.** Vedi il punto aperto qui sotto.

## Un punto che NON torna, e resta aperto
Su ARMI A DISTANZA (indice 76, stampata 75) l'utente ha marcato anche del blu,
ma il meccanismo non scarta niente: 13 corridoi su 13 ammessi, 14 bande emesse.
Due letture possibili e nessuna verificata: o le frecce blu li' segnavano
un'aspettativa («queste colonne di valori corti non si formeranno») smentita dal
fatto, oppure segnalano che su quella pagina l'ORDINE esce male per un'altra
ragione, e la banda c'entra poco. Va chiesto prima di concludere.

## La soglia vera, estratta dai dati
Il criterio scarta quando `wordy_minimum < 2`, cioe' quando **meno di due righe
per lato portano almeno 5 caratteri**. Una colonna di dado (`1`, `2`, ... `20`)
ne ha zero. Una colonna di valori come `180`, `1 arg.`, `Comune` ne ha
abbastanza, ed e' per questo che in ARMI A DISTANZA passano tutte. Non e' «i
numeri non contano»: e' «zero parole da un lato».

---

# La somma dei caratteri di fianco: misurata

Criterio pre-registrato in `Criterio_SommaCaratteriFianco_v1.md`, script
`scripts/compare_flanking_char_sum.py`. Il producer non e' stato toccato: le
varianti ricompongono la decisione sopra il profilo che il producer misura.

    V0  oggi:   scarta se meno di 2 righe per lato portano >= 5 caratteri
    V1  somma:  scarta se il lato piu' povero somma < 5 caratteri, ovunque
    V2  mista:  V1 dentro un `table_candidate`, V0 fuori

## Un difetto della MIA implementazione, trovato misurando
La prima versione leggeva il motivo di scarto del producer per sapere se un
altro criterio aveva gia' bocciato il corridoio. Ma `_reject_reason` si ferma al
primo motivo che scatta, e `too_few_wordy_lines` viene prima di `too_short`:
cosi' un corridoio non-wordy **e** troppo basso riportava solo il primo, e la
variante lo promuoveva ignorando l'altezza. Risultato: corridoi alti 0,75 righe
ammessi. Corretto ricalcolando i due criteri invece di leggerli. I numeri qui
sotto sono quelli dopo la correzione.

## Verita' di riferimento: 13 su 14
**Nove che devono formarsi** (colonne di dado): otto passano con V1.
    IMPREVISTI MAGICI 60  x 111-118  somma (31, 2849)   si
    FANTASMA 88           x  77- 84  somma  (6, 1295)   si
    RAGNO GIGANTE 96      x  77- 84  somma  (6, 1303)   si
    IMPREVISTI 102        x 112-118  somma (18, 2197)   si
    ORCO 111              x  63- 69  somma  (9, 1071)   si
    ARMI IMPROVVISATE 120 x  77- 84  somma  (6, 2620)   si
    TESORI 1 121          x  88- 95  somma (14,  743)   si
    TESORI 2 122          x  87- 92  somma (34, 2255)   si
    TESORI 1 121          x  77- 84  somma  (3, 1343)   **NO**  <- unico errore

**Cinque che non devono formarsi** (rientro sospeso, x 74): tutti e cinque
restano scartati, e per una ragione che non avevo previsto — la somma del lato
sinistro e' **zero**. Quelle righe di fianco sono **span vuoti**, non i punti
elenco: e' anche la spiegazione del fatto che ieri non trovavo testo a sinistra
di x 74 pur avendo il profilo 3-6 righe di fianco.

## Le predizioni
- **W1 (V1 accetta tutti e nove): FALSIFICATA**, otto su nove. L'errore ha somma
  3 su tre righe di fianco; con soglia 3 passerebbe, ma sceglierla dopo aver
  visto quale caso fallisce e' taratura, non correzione.
- **W2 (V1 introduce falsi positivi sui rientri sospesi): FALSIFICATA**, zero.
  Avevo previsto 2 su 5 ragionando su punti elenco da un carattere; sono span
  vuoti da zero caratteri.
- **W3 (V2 e' corretta 14 su 14): FALSIFICATA.** V2 sbaglia lo stesso caso di
  V1, perche' quel corridoio sta dentro una tabella. **Il cancello del
  `table_candidate` non aggiunge niente sulla verita' di riferimento.**
- **W4 (l'effetto globale non e' concentrato sulle tabelle): FALSIFICATA.** Lo e'
  quasi del tutto.

## Effetto globale
| manuale | pagine | corridoi | V0 | V1 | nuovi in tabella | nuovi fuori |
| --- | --- | --- | --- | --- | --- | --- |
| DB | 126 | 639 | 326 | **354** | 27 | 1 |
| Apo | 101 | 294 | 37 | **50** | 12 | 1 |
| Fab | 101 | 220 | 64 | **66** | 2 | 0 |

L'aumento e' contenuto e va quasi tutto dentro le tabelle. Su Apo — il manuale
che nel campione aveva 14 pagine su 20 senza bande — le bande crescono del 35%.

## La conseguenza architetturale, ed e' la cosa piu' importante
Il criterio della somma **da solo** separa la colonna di dado dal rientro
sospeso: la prima somma da 6 a 34 caratteri, il secondo somma zero. Quindi la
correzione **non ha bisogno** di leggere i candidati di un altro producer, e il
problema che avevo sollevato ieri — «un producer non deve anticipare una
decisione del consumer, la relazione fra candidati sta in Resolution» — **non si
pone**: la distinzione e' interna al profilo che `column_band` gia' misura.
V2 esiste ancora come opzione ma sulla verita' di riferimento non aggiunge nulla
e globalmente cambia di un caso su 126 pagine.

## Cosa resta vero e non e' stato risolto
- Una banda a due colonne su una tabella la fa **leggere per colonne**: tutti i
  numeri, poi tutte le descrizioni. La banda e' il fatto strutturale giusto, la
  lettura per righe resta una decisione del consumer, informata dal
  `table_candidate` che copre la stessa regione. Emettere le bande senza quella
  decisione peggiora la resa delle tabelle invece di migliorarla.
- Il giudizio a vista esiste solo su DB. Su Apo e Fab e' misurata la dimensione
  dell'effetto, non la sua correttezza.
- Nessuna soglia e' stata spostata e il producer non e' stato toccato.

## V3, «lato non vuoto»: perfetta sulla verita' verificata, incontrollata altrove

Rilievo dell'utente: la TESORI 1 «e' una tabella tagliata che continua nella
colonna a fianco». Verificato: sulla stessa pagina (DB 121) ci sono **due**
tabelle tagliate in meta' affiancate, e avevo attribuito male i corridoi.
La **FORESTA** e' un D6 diviso in due meta' da **tre righe** (`1 2 3` a x 70,9;
`4 5 6` a x 323,1): la sua colonna di numeri somma **3 caratteri**, e la soglia 5
la scarta per costruzione. L'unico errore di V1 non era un caso isolato, era
questa classe.

E la soglia 5 non ha una ragione propria: e' `min_flanking_chars`, nata per dire
«una riga con almeno cinque caratteri porta una parola». Sommare su piu' righe e'
un'altra grandezza. I dati dicono che i due gruppi non si distinguono per quanto
sommano ma per **se** sommano: rientro sospeso 0, colonne di dado 3-34.

    V3  lato non vuoto: si scarta se un lato somma ZERO caratteri. Nessuna soglia.

**X1 confermata: V3 e' 14 su 14.** Accetta anche il caso FORESTA (somma 3) e
scarta tutti e cinque i rientri sospesi (somma 0).

**X2 falsificata su DB, confermata su Apo** — ed e' il risultato che conta:

| manuale | corridoi | V0 | V1 | V3 | nuovi V3 in tabella | nuovi V3 fuori |
| --- | --- | --- | --- | --- | --- | --- |
| DB | 639 | 326 | 354 | **358** | 31 | 1 |
| Apo | 294 | 37 | 50 | **72** | 13 | **22** |
| Fab | 220 | 64 | 66 | **66** | 2 | 0 |

Su DB e Fab V3 e' contenuta quanto V1. Su Apo raddoppia quasi le bande e ne
aggiunge **22 fuori dalle tabelle** contro 1 di V1. Se avessi misurato solo DB
avrei concluso che V3 e' gratis.

**X3 e' il punto.** La verita' di riferimento e' fatta di quattordici corridoi,
tutti da DB. Su DB V3 e' perfetta; su Apo fa una cosa che nessuno ha guardato.
Quattordici corridoi giudicati a vista non autorizzano un criterio che tocca
centinaia di pagine su manuali diversi.

## Dove lascia la scelta
- **V1 (somma >= 5)**: contenuta su tutti e tre i manuali, sbaglia la classe
  delle tabelle tagliate in meta' corte.
- **V3 (lato non vuoto)**: corretta su tutto il verificato, ma su Apo aggiunge 22
  bande fuori tabella che nessuno ha ispezionato.
Nessuna delle due si adotta qui. Per scegliere serve il giudizio a vista su
alcune delle 22 pagine Apo, che e' l'unica cosa che i numeri non danno.

Una terza formulazione non misurata, da non trattare come proposta finche' non
lo e': «somma >= numero di righe di fianco», cioe' almeno un carattere per riga
in media. Sul verificato darebbe gli stessi esiti di V3 (FORESTA 3/3, rientro
0/6); su Apo non e' stata misurata.

## Le 33 pagine Apo, ispezionate: rispondono da sole

Estratte con `--elenco-v3` e **guardate**, non assunte. Sono 33 su tutto Apo
(22 nel tratto 0-100 misurato prima). Trentuno stanno alla stessa x, 66-73, e il
fianco sinistro e' sempre lo stesso: il carattere `h` nel font
**`NelsonOrnaments`**, cioe' il punto elenco del manuale, davanti a un rientro
sospeso.

    Apo 109  x 56,7-63,6  'h'  NelsonOrnaments   |  x 74,7-390,5  'Prigioniero. Gabriel...'
    Apo  49  idem                                |  'Interrogare Cleménce e' arduo...'
    Apo  31  idem                                |  'Igritte sovrintendera'...'

E' **lo stesso rientro sospeso** che su DB l'utente ha lasciato non marcato. La
sola differenza e' la codifica: su DB quelle righe risultano span **vuoti**
(somma 0), su Apo il marcatore e' un carattere vero (somma 2-4).

Conseguenza: **V3 era 14 su 14 per un accidente di codifica del manuale da cui
viene la verita'.** Su Apo apre 33 elenchi puntati come bande a due colonne.

E le due classi si sovrappongono nei numeri — colonna D6 della FORESTA: 3;
punto elenco di Apo: 2-4. **Nessuna soglia sulla somma le separa.**

## V4: la somma non vuota, ma solo dentro una tabella

| | verita' (14 corridoi) | DB 126 pag. | Apo 148 pag. |
| --- | --- | --- | --- |
| V0 oggi | 5/14 | 326 | 47 |
| V1 somma >= 5 | 13/14 | 354 (+27 tab, +1 fuori) | 69 (+21 tab, +1 fuori) |
| V3 lato non vuoto | 14/14 | 358 (+31 tab, +1 fuori) | 102 (+22 tab, **+33 fuori**) |
| **V4 non vuoto in tabella** | **14/14** | **357 (+31 tab, 0 fuori)** | **69 (+22 tab, 0 fuori)** |

V4 e' l'unica corretta su tutto cio' che e' stato guardato a vista **e** contenuta
su un manuale diverso da quello della verita'. Prende la classe delle tabelle
tagliate (FORESTA, somma 3) e non tocca nessun elenco puntato.

## Il costo architetturale di V4, dichiarato
V4 usa l'uscita di un **altro producer**. Ieri avevo scritto che il cancello del
`table_candidate` era inutile perche' la somma bastava: era vero su DB e falso su
Apo. Quindi la distinzione che serve **non** sta nel profilo del corridoio, e
`column_band` da solo non puo' prenderla.

Il che riporta esattamente dove `AGENTS.MD` §Layout e candidati dice che vada:
«la relazione fra candidati di producer diversi si decide in Resolution o nel
consumer, mai dentro un producer». V4 non e' adottabile come patch dentro
`column_band`; e' una regola di Resolution, oppure un consumer che combina banda
e tabella. Il che la rende piu' grande di una modifica di soglia, e giustifica
una milestone sua.
