# Esito — le schede su manuali mai toccati: **il meccanismo tace su tutti e sei**

Misura di `Criterio_SchedeSuManualiMaiToccati_v1.md`, emendato al §3.B **prima**
di giudicare qualunque pagina. 23 settembre 2026.
Rese in `output/resa/maitoccati/`, dodici in tutto.

## 1. Il risultato in una riga

**Zero combinazioni di campi ammesse su sei manuali su sei.** Il riconoscimento
delle schede, dove non è stato costruito, non riconosce niente.

| manuale | pagine | combinazioni ammesse | tabelle cambiate |
| --- | ---: | ---: | --- |
| Wil | 316 | **0** | 22 cresciute |
| BiD | 328 | **0** | nessuna |
| DIE | 408 | **0** | nessuna |
| SV | 372 | **0** | nessuna |
| Kul | 242 | **0** | nessuna |
| Vil | 272 | **0** | nessuna |

## 2. I veti

| veto | esito |
| --- | --- |
| **A** niente cade | **sì** — dodici render, uscita 0 |
| **B** (emendato) le tabelle cambiano nei due versi, e si giudicano | applicato |
| **C** meglio ≥ peggio | **CADE** — 0 meglio, 22 peggio, tutte su Wil |
| **D** nessuna prosa tagliata | **sì** — gli orfani non salgono su nessuno dei sei |
| **E** dove ci sono schede, si vedono | **CADE** — Wil ha schede e non ne vede nessuna |
| **veto** tabella vera che perde righe | **non scatta**: nessuna tabella perde una riga |

Il veto non scatta perché il meccanismo non tocca niente. È una buona notizia
solo in apparenza: non danneggia perché non agisce.

## 3. Dove si ferma la catena, misurato

Alla **prima** condizione: due coppie etichetta/valore **dichiarate sulla stessa
riga**.

| manuale | righe con ≥1 campo dichiarato | righe con ≥2 | combinazioni ripetute ≥3 volte |
| --- | ---: | ---: | ---: |
| Wil | 225 | **0** | 0 |
| Vil | 122 | **0** | 0 |
| Kul | 162 | **0** | 0 |
| BiD | 407 | 1 | 0 |
| SV | 160 | 2 | 0 |
| DIE | 273 | 16 | 0 |

I campi ci sono — 1.349 righe li dichiarano — ma **uno per riga**. Le poche righe
con due campi non sono schede: su SV `['4-5', '6', 'successocritico']`, su BiD
`['1-3', '4/5', '6']` sono esiti di un tiro; su DIE sono nomi di attacchi
(`['doppio-speciale', 'soffiodifuoco']`), ognuno unico, mai ripetuto.

La regola «almeno due coppie su una riga» descrive la forma di **Dragonbane e
Daggerheart**: `Ferocia: 3  Taglia: Enorme`, `Difficoltà: 14 | Soglie: 9/18 |
PF: 5 | Stress: 3`. Fuori da quei due impaginati non esiste.

## 4. Le 22 tabelle di Wil, giudicate sull'immagine

Sono le carte **AREA** di Wilder: un riquadro grande con dentro sotto-scatole
(`SENTIERI E COMUNITÀ`, `TRATTI`) e una tabella vera (`INGREDIENTI`, colonne
STILE/NOME/EFFETTO). Wil idx 137, stampata 138, guardata sulla pagina:

- **senza** `--schede-producer`: la tabella contiene solo `INGREDIENTI`, e i
  paragrafi di `TRATTI` restano fuori;
- **con**: i `TRATTI` entrano nella tabella come righe a colonna vuota —
  `| | | | Meteo Costiero. Ogni volta che il branco entra in un'Area…`

Tutte e 22 sono lo stesso caso. **Peggio**, e la causa non è una regola nuova che
sbaglia: è che `--schede-producer` **spegne** la vecchia strada dei riquadri
dentro `run()` (perché la Resolution dovrebbe averla sostituita) e, con la policy
muta, nessuno la sostituisce. Le schede d'area di Wil il vecchio riconoscimento
le vedeva; il nuovo no.

## 5. Che cosa dice questa misura, e che cosa no

**Dice** che la catena producer → policy → consumer → riquadri, che su DB e Dag
non sbaglia più niente, **non è universale**: riconosce una forma di scheda, e
quella forma è dei due manuali su cui è nata. E dice che la sua silenziosità
**non è gratis**, perché la strada che sostituisce viene spenta comunque.

**Non dice** che il meccanismo sia sbagliato: su DB e Dag continua a fare quello
che è stato misurato. Dice che il suo dominio è più stretto di quanto tre
manuali lasciassero vedere — ed è esattamente ciò che la previsione del §4 si
aspettava: «mi aspetto almeno un manuale con un difetto nuovo».

## 6. Le due strade, e la decisione è dell'utente

**La prima è piccola e sicura**: quando la policy non ammette nessuna
combinazione, `--schede-producer` **non deve spegnere** la vecchia strada dei
riquadri. Toglie le 22 tabelle peggiorate di Wil e non tocca DB e Dag, dove la
policy parla. Non allarga il dominio: lo lascia dov'era.

**La seconda è la domanda vera**: accettare come riga di campi anche una riga con
**una** coppia dichiarata. L'utente l'ha rifiutata l'11 settembre, su Daggerheart
e su un meccanismo diverso — il riquadro. Oggi ci sono sei manuali che dicono che
una coppia per riga è la forma **dominante** fuori da Dragonbane e Daggerheart:
1.349 righe contro 19. Va rimessa in discussione con questi numeri, non con
quelli di allora, e misurata: il rischio è preciso e noto, cioè prendere per
schede gli elenchi con `Durata:`, `Costo:`, `Prerequisiti:`.
