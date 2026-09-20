# Esito — le righe della scheda contro la tabella

**Tre giri, in ordine, e nessuno riscritto dopo:** il primo **cade** sul veto, il
secondo **non passa** il conteggio (uno a uno), il terzo **passa**. I due giri
successivi al primo non toccano il criterio: correggono l'ingresso del
riconoscimento, ognuno su un rilievo dell'utente.

## Primo giro, 17 settembre: **CADE sul veto**

Misurato il 17 settembre 2026 contro `Criterio_SchedaControLaTabella_v1.md`,
dichiarato prima. Prima: `output/resa/riparo`; dopo: `output/resa/schede`;
confronto con `output/resa/schede_confronto.py`.

## Verdetto

**Cade.** Due tabelle che la pagina stampa **spariscono** — DB p87 e p119, le
tabelle `ATTACCHI MOSTRUOSI` del drago e del cavaliere brigante — e altre cinque
tabelle vere si svuotano. Il conteggio è meglio 2, peggio 8.

## §4.A — Barra
1714 test verdi (30 portati col modulo delle schede, 4 della regola nuova), ruff
pulito. E-B: **9 su 10**, l'unica diversa Fab idx 126, gia' a verbale
(`output/resa/eb-schede.log`). La barra regge: il collegamento tocca solo il
percorso con `--tabelle`.

## §4.B — Nessuna tabella cresce: **tiene**

| manuale | prima | dopo | uguali | ridotte | sparite | **cresciute** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB  | 70 | 68 | 61 | 7 | 2 | **0** |
| Apo | 16 | 16 | 16 | 0 | 0 | **0** |
| Dag | 64 | 63 | 63 | 0 | 1 | **0** |

Dieci tabelle cambiate in tutto: si giudicano tutte.

## §4.C — Il giudizio

| manuale | idx | stampata | che cosa succede | giudizio |
| --- | ---: | ---: | --- | --- |
| Dag | 230 | 229 | **sparisce** la tabella fatta di tre schede di avversari | meglio |
| DB  |  43 |  42 | il riquadro AZIONI passa da 97 primitive a 16: la pagina lì non stampa una tabella | meglio |
| DB  |  88 |  87 | **sparisce** `ATTACCHI MOSTRUOSI` del drago, 26 righe | **peggio, veto** |
| DB  | 120 | 119 | **sparisce** `ATTACCHI MOSTRUOSI` del cavaliere brigante, 40 righe | **peggio, veto** |
| DB  |  87 |  86 | gli attacchi del demone perdono 18 primitive su 55 | peggio |
| DB  |  92 |  91 | gli attacchi del grifone passano da 26 righe a 4 | peggio |
| DB  |  93 |  92 | gli attacchi della manticora passano da 23 righe a 3 | peggio |
| DB  |  96 |  95 | `ANIMALI COMUNI` resta con la sola colonna dei nomi: `\| Gatto \| \| \| \| \|` | peggio |
| DB  |  99 |  98 | gli attacchi del troll perdono i numeri di riga | peggio |
| DB  | 122 | 121 | la tabella delle trappole perde 9 primitive su 66 | peggio |

**meglio 2, peggio 8, e il veto scatta**: due tabelle stampate sono sparite.

## Che cosa è caduto — la diagnosi

**Non la regola dell'utente**, e nemmeno la sua forma: dove la scheda è
riconosciuta bene la regola fa esattamente quello che deve. Su Dag p229 le tre
schede si tengono le loro righe e la tabella sbagliata non si costruisce; su
DB p106 la tabella vera sopravvive perdendo la sola riga del riquadro sotto,
mentre la regola del ramo delle schede la cancellava.

**Sono cadute due cose, entrambe misurate:**

1. **Su DB il riquadro preso per scheda è grande quanto la pagina.** Non è un
   blocco statistiche: su p87 la scheda è `x0-533 y0-656` e le sue righe
   cominciano da `DRAGO` e dalla prosa del testo; su p95 è `x131-612 y0-590`; su
   p91 è `x0-524 y174-791`. La strada dei riquadri disegnati, misurata su
   Daggerheart, su questo manuale prende l'inquadratura della pagina.
2. **La mia prova di contenimento è fragile.** La tabella degli attacchi del
   drago sporge di **8 punti** dal riquadro, quella del cavaliere brigante di
   **4**: tanto basta per passare da «dentro la scheda, tiene tutto» a
   «la attraversa, perde tutto». Un esito non può girare su quattro punti.

**Lo stesso danno esiste già sul ramo delle schede**, in altra forma. Il loro
`Esito_SchedaInIR2_v1.md` registra «R5, tabelle attraverso una scheda: … 6 su DB,
non costruite» come comportamento atteso. Questa misura dice **quali sono**: le
tabelle degli attacchi del bestiario. Va riportato a quella chat.

## Che cosa resta aperto

- I tre casi del veto della riparazione che non hanno schede — Dag p115, p310,
  p360 — restano come erano.
- Il modulo portato (`stat_block_regions.py`) e i suoi 30 test restano nel ramo
  come sono: non si cancella, si tagga.

---

# Secondo giro, 17-18 settembre: il riquadro di una scheda è **disegnato**

Il primo verdetto resta. Questa è la misura rifatta dopo aver corretto l'ingresso
del riconoscimento, e il criterio del 17 settembre non è stato toccato.

## La correzione, e da dove viene

**Rilievo dell'utente**: «su DB non mi risulta ci siano tabelle o schede che
escono dalla pagina, ti starai confondendo con lo sfondo.» Misurato, ha ragione:
i riquadri che il riconoscimento prendeva per schede su DB sono **candidati
raster** di `embedded_visual`, cioè una sola primitiva **immagine** ciascuno.

| pagina | riquadro preso per scheda | quota di pagina | primitive |
| --- | --- | ---: | --- |
| DB p87 | l'illustrazione del drago | 72% | 1 immagine |
| DB p91 | il grifone | 67% | 1 immagine |
| DB p95 | il pipistrello | 59% | 1 immagine |
| DB p119 | l'illustrazione del cavaliere | 34% | 1 immagine |
| DB p42 | la pergamena del riquadro AZIONI | 34% | 1 immagine |
| Dag p229 | i tre riquadri veri delle schede | 9-16% | 3 e 7 **disegni** |

Le schede giuste sono **vettoriali**, i falsi positivi sono **raster**. Lo dice
il modulo stesso nella sua prima riga: «i confini di una scheda non si deducono,
si leggono: il riquadro è **disegnato** sulla pagina». Il difetto era in chi
glieli passava — il mio innesto — che gli mandava anche le illustrazioni.
Corretto lì, in `scripts/prototype_ir2_page.py`: alla scheda vanno solo i
candidati fatti **tutti** di primitive di disegno. Nessuna soglia.

**Vale anche per il ramo delle schede**: `e05ebfa` passa al modulo gli stessi
candidati senza filtro, ed è la ragione delle «6 tabelle su DB non costruite» del
loro `Esito_SchedaInIR2_v1.md`. Da riportare a quella chat.

## §4.A — Barra

1714 test verdi, ruff pulito sui file toccati (i 78 rilievi di `ruff check .`
stanno in `epub_builder`, `deduplicator`, `describer` e `asset_manager`, non
toccati). E-B rifatta dopo la correzione: **9 su 10**, l'unica diversa Fab idx
126 gia' a verbale (`output/resa/eb-schede2.log`).

## §4.B — Nessuna tabella cresce: tiene

| manuale | prima | dopo | uguali | ridotte | sparite | cresciute |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB  | 70 | 70 | 69 | 1 | 0 | **0** |
| Apo | 16 | 16 | 16 | 0 | 0 | **0** |
| Dag | 64 | 63 | 63 | 0 | 1 | **0** |

Le undici tabelle danneggiate del primo giro scendono a **una**, e le due
sparite tornano intere.

## §4.C — Il giudizio: **meglio 1, peggio 1**

| manuale | idx | stampata | che cosa succede | giudizio |
| --- | ---: | ---: | --- | --- |
| Dag | 230 | 229 | **sparisce** la tabella fatta di tre schede di avversari | meglio |
| DB  | 122 | 121 | la tabella delle trappole perde `1 Ramo Basso` e 9 primitive su 66 | peggio |

Il **veto tiene**: nessuna tabella stampata sparisce. Ma il §4.C chiedeva
**meglio > peggio**, e uno contro uno non lo è: **il criterio non passa**, e non
lo riscrivo dopo aver visto il risultato.

**Perché DB p121 perde righe**: le «schede» sono i riquadri disegnati delle
trappole (`1 Ramo Basso`, `5 Vipera`). La pagina le stampa come righe di una
tabella; il riconoscimento le prende per schede perché i punti elenco — il
simbolo in un font diverso dal testo — contano come coppie etichetta/valore. È un
difetto del riconoscimento, non della regola, e va alla chat delle schede insieme
al filtro raster.

## Lo stato, in due righe

La regola dell'utente — le righe di una scheda sono della scheda — fa ciò che
deve dove la scheda è riconosciuta bene: su Dag p229 toglie la tabella fatta di
tre schede, su DB p106 salva una tabella vera che la regola del ramo schede
cancellava. Il suo costo residuo è **una** tabella su tre manuali, e dipende da
due falsi positivi noti del riconoscimento.

---

# Terzo giro, 18 settembre: **PASSA**

## La seconda correzione, e da dove viene

**Rilievo dell'utente**: «DB p121 non sono schede ma tabelle, lo vedo dal numero
che incrementa, dalle etichette che non si ripetono e dalle colonne ordinate.»

I riquadri disegnati delle trappole passavano per schede perche' il
riconoscimento conta le **alternanze di stile** (`label_pairs`), e un punto
elenco — simbolo in un font diverso dal testo — ne produce una. Contati invece i
**campi** veri (`line_facts.labels`), la separazione e' netta e non ha soglie da
scegliere: sono i due numeri che il modulo dichiara per se', «almeno due righe
con almeno due coppie etichetta/valore».

| | righe con almeno due campi |
| --- | ---: |
| 18 schede di Daggerheart (p224, p225, p229, p244) | **2 o 3** ciascuna |
| i 2 blocchi statistiche di Dragonbane (p91, p95) | **2** |
| i riquadri delle trappole di DB p121 | **0** |

Corretto in `scripts/prototype_ir2_page.py`: una regione conta come scheda solo
se almeno due delle sue righe portano almeno due campi.

## Le tre barre

- **§4.A**: 1714 test verdi, ruff pulito sui file toccati, E-B **9 su 10** con la
  sola Fab idx 126 gia' a verbale (`output/resa/eb-schede3.log`).
- **§4.B**: nessuna tabella cresce.

| manuale | prima | dopo | uguali | ridotte | sparite | cresciute |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB  | 70 | 70 | 70 | 0 | 0 | **0** |
| Apo | 16 | 16 | 16 | 0 | 0 | **0** |
| Dag | 64 | 63 | 63 | 0 | 1 | **0** |

- **§4.C**: **una sola tabella cambia su tre manuali** — Dag p229, la tabella
  fatta di tre schede di avversari, che **sparisce**. **meglio 1, peggio 0**, e
  nessuna tabella stampata sparisce: il veto tiene. **Il criterio passa.**

## Che cosa resta da dire

Le due correzioni dei giri 2 e 3 sono **toppe alla strada vecchia**: il
riconoscimento per riquadri disegnati e' la regola di 3a. Il ramo delle schede ha
gia' una strada nuova, dalla **struttura ripetuta** (`--schede-struttura`,
dichiarata in prova), che non guarda i riquadri — quindi lo sfondo non la tocca —
e che scarta da se' le strutture «a righe ordinate», cioe' le trappole di DB p121.
**Rilievo dell'utente**: giudicare la strada vecchia serve a poco. La misura di
queste tabelle andrebbe rifatta contro la strada nuova, quando la si porta.

Le due cose da riportare alla chat delle schede restano:

1. il filtro raster — al modulo vanno passati solo i riquadri **disegnati**;
2. i punti elenco contati come coppie etichetta/valore, che fanno passare per
   schede i riquadri delle trappole.

---

# Quarto giro, 18 settembre: la **strada nuova**, e perche' oggi non aiuta le tabelle

**Rilievo dell'utente**: «che senso ha giudicare una roba obsoleta?». Le due
correzioni dei giri 2 e 3 sono toppe alla strada dei riquadri, che e' la regola
di 3a; la strada dalla struttura ripetuta non ha quei due problemi. Portata e
misurata.

## Che cosa e' stato portato

1. **La catena di lettura estratta in una funzione sola** (`reading_chain`), come
   sul ramo delle schede e per la stessa ragione: la prima passata deve vedere le
   **stesse** righe della resa. Riordino puro, verificato prima di andare avanti:
   DB reso col codice riordinato e' **identico byte a byte** — markdown e IR 2 —
   a quello del terzo giro.
2. **Il ramo dalla struttura** in `run()` (`stat_blocks_from_structures`), e la
   **prima passata** in `main_ir2` dietro `--schede-struttura`: raccoglie le
   righe di tutte le pagine catturate e ne ricava le strutture ricorrenti.

## Le strutture trovate

| manuale | strutture | la prima |
| --- | ---: | --- |
| Apo | 2 | `difficolta`, `precisione`, `ragione`, `ansia`, `complicazioni` |
| DB  | 2 | `ferocia`, `movimento`, `armatura`, `abilita`, `ali`, `armi`, **`artigli!`**, `dannobonus` |
| Dag | 6 | `att`, `difficolta`, `esperienza`, `impeti`, `dimensioni` |

Le schede giuste le trova: su Dag la scheda avversario, su DB il blocco del
bestiario e gli attributi dei PNG. **Ma su DB la struttura include `artigli!`**,
che e' una riga della tabella degli attacchi.

## L'effetto sulle tabelle, contro l'11 settembre

| manuale | prima | dopo | uguali | ridotte | sparite |
| --- | ---: | ---: | ---: | ---: | ---: |
| DB  | 70 | 64 | 56 | 8 | **6** |
| Apo | 16 | 11 | 11 | 0 | **5** |
| Dag | 64 | 61 | 58 | 3 | 3 |

Su DB spariscono le tabelle `ATTACCHI MOSTRUOSI` di drago, demone, grifone,
manticora e p93, e quella del cavaliere brigante passa da 40 righe a 1. Sono
tabelle che la pagina stampa: **il veto scatterebbe**.

## Perche', misurato — e non e' la regola, e' la fine della scheda

| pagina | dove arriva la scheda | la sua ultima riga |
| --- | --- | --- |
| DB p87 | 50 righe da `DRAGO` in giu' | `Andrea Bruna - 550401`, la filigrana |
| DB p119 | 52 righe | `Andrea Bruna - 550401` |
| DB p91 | 51 righe, colonna sinistra | una riga della tabella degli attacchi |

La scheda non finisce dove finisce il blocco statistiche: su Dragonbane **niente
la interrompe** fino a fondo pagina, e si porta dentro la tabella degli attacchi.
Il loro `_block_end` la ferma a cio' che la interrompe — il nome di un'altra
scheda, una riga di dimensione da titolo, il bordo del riquadro, la scheda
successiva, la fine della pagina — e su Dragonbane nessuna di queste arriva prima.

**Non e' un difetto della mia regola**: con la loro — bloccare la tabella che
attraversa il riquadro della scheda — le stesse tabelle muoiono lo stesso.
Verificato su quelle pagine con `crossed_stat_blocks`: su DB p87 e p119
**BLOCCATA**. L'unica differenza e' su DB p91, dove il riquadro non arriva alla
colonna destra e la loro regola la costruisce mentre la mia no, perche' l'ordine
di lettura alterna le colonne e le righe della tabella cadono dentro la corsa
della scheda.

## Che cosa dice questo giro

- Per il **percorso tabella**, oggi, la strada dei riquadri con le due correzioni
  e' migliore: 1 meglio e 0 peggio, contro 14 tabelle sparite della strada nuova.
- Su **Daggerheart** la strada nuova toglie due tabelle fantasma in piu' (p227,
  che e' una pagina di tre schede, e le schede del personaggio p358 e p360): la'
  probabilmente migliora, e andrebbe giudicato a parte.
- La strada nuova resta **portata e spenta** dietro `--schede-struttura`: non si
  cancella, si tagga. Quando la fine della scheda reggera' anche su Dragonbane,
  questa misura si rifa' con un comando.
- **Per la chat delle schede**, oltre ai due difetti dei giri 2 e 3: su Dragonbane
  la scheda dalla struttura ripetuta arriva fino alla filigrana di pagina, e si
  mangia la tabella degli attacchi.

---

# Quinto giro, 19 settembre: la scheda e' una **riga di campi**

Non e' una variante di regola: e' un modo diverso di **riconoscere** la scheda,
indicato dall'utente guardando due pagine del bestiario di Dragonbane, e misurato
con lo stesso §4 di questo criterio.

## L'indicazione

«La scheda e' il riquadro piccolo: `Ferocia: 3  Taglia: Enorme`,
`Movimento: 24  Armatura: 6  PF: 84`, poi i tratti. `ATTACCHI MOSTRUOSI` e
`ANIMALI COMUNI` sono tabelle. Non basta che le etichette ci siano: devono essere
nella stessa posizione relativa.»

E, sul metro da usare: «se la tabella lo risolve non preoccupiamocene troppo,
deve essere leggibile».

## Che cosa dice la misura, prima di scrivere il codice

Le **combinazioni di etichette sulla stessa riga**, ripetute nel documento:

| combinazione | volte | dove |
| --- | ---: | --- |
| `ferocia + taglia` | 13 | le 13 creature di Dragonbane (p85-99, p119) |
| `movimento + armatura + pf` | 12 | le stesse |
| `movimento + pf` | 4 | le creature evocate, p67-69 |
| `difficolta + soglie + pf + stress` | 149 | le schede avversario di Daggerheart |
| `2 + 3 + 4 + 5 + tiraund6` | 4 | **una tabella**: i tesori di DB p122 |
| — | 0 | **Apocalisse**, che schede non ne ha |

Le tabelle non producono queste righe: l'intestazione di `ANIMALI COMUNI` ha le
celle tutte dello stesso stile e non forma coppie; le righe di `COMPLICAZIONI`
portano un valore per cella. L'unica eccezione e' la tabella dei tesori, che
elenca sei voci numerate sulla stessa riga.

**La posizione relativa, misurata, non discrimina** e va detto: sulle istanze
giudicate a vista le schede vere stanno al 33-71% di conformita' e le tabelle allo
0-100%, e le sfide di Apocalisse conformano al **100%** perche' una tabella *e'*
una griglia. Serve la co-occorrenza sulla riga, non l'allineamento.

## Il meccanismo

`stat_block_field_lines.py` (nuovo, 6 test): una riga e' di campi se porta almeno
**due etichette insieme** in una combinazione che il documento ripete almeno tre
volte -- il tre e' il minimo che `repeated_structures` chiede gia' a una
struttura. Contenimento e non uguaglianza; righe vicine nell'ordine di lettura
sono la stessa scheda.

E le due strade si **sommano**, perche' sono complementari, misurato: i riquadri
disegnati sono precisi dove esistono (Daggerheart, 1 scheda su 170 sconfina) e
quasi ciechi altrove (3 schede su Dragonbane, 0 su Apocalisse); le righe di campi
valgono ovunque ma rivendicano solo se stesse. **Una scheda e' cio' che un
riquadro delimita oppure cio' che una riga di campi dichiara.**

## Il confronto fra tutte le varianti provate

| variante | sparite | ridotte | tabelle vere danneggiate |
| --- | ---: | ---: | ---: |
| struttura ripetuta, righe alla scheda | 14 | 11 | 8 |
| struttura ripetuta, blocca la tabella (regola del ramo schede) | 23 | 0 | molte |
| struttura ripetuta + fine al cambio di colonna | 2 | 17 | 8 |
| righe di campi | 0 | 6 | 1 |
| **righe di campi + riquadri disegnati** | **1** | **5** | **1** |

## §4, applicato senza ritocchi

- **§4.A**: 1720 test verdi (6 del modulo nuovo), ruff pulito sui file toccati,
  E-B **9 su 10** con la sola Fab idx 126 gia' a verbale (`output/resa/eb-campi.log`).
- **§4.B**: nessuna tabella cresce. DB 70->70, Apo 16->16, Dag 64->63.
- **§4.C**: **meglio 5, peggio 1.**

| manuale | pagina | che cosa succede | giudizio |
| --- | ---: | --- | --- |
| Dag | 229 | **sparisce** la tabella fatta di tre schede di avversari | meglio |
| Dag | 358 | la finta tabella a tre colonne delle forme bestiali perde 60 primitive | meglio |
| DB | 89 | `Ferocia: 1 Taglia: Enorme` e `Movimento: 18 …` escono dalla tabella fantasma | meglio |
| DB | 86, 96 | una riga di prosa introduttiva esce dalla tabella fantasma | meglio |
| DB | 122 | la riga 11 dei tesori, `Tira un D6. 1: pugnale, 2: spada corta…`, perde il testo | **peggio** |

- Il veto tiene: nessuna tabella stampata sparisce.
- **Apocalisse non cambia di una riga**: le quattordici pagine di sfida che i giri
  precedenti rovinavano restano intatte.

## Che cosa resta aperto

- **Dag p229 esce meglio ma non bene**: la riga statistiche torna testo leggibile,
  il resto della scheda resta in una tabella a due colonne con la prima vuota.
  Lo risolve il riquadro, e infatti la tabella non si costruisce piu'; la resa
  della scheda in se' e' lavoro della chat delle schede.
- **DB p122**: una tabella che elenca voci numerate sulla stessa riga imita una
  riga di campi. Una riga, una pagina, tre manuali.
- La strada dalla struttura ripetuta resta portata e spenta: quando la fine della
  scheda reggera' anche su Dragonbane, si rimisura con un comando.
