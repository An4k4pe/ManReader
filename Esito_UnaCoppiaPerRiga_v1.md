# Esito — una coppia per riga: **il veto scatta**, e dice perché

Misura di `Criterio_UnaCoppiaPerRiga_v1.md`, 24 settembre 2026, con l'unità
sulla riga come indicato dall'utente. Nove manuali, resa in
`output/resa/unacoppia`. Riferimenti: `output/resa/rete` (DB, Apo, Dag) e
`output/resa/maitoccati/senza-*` (i sei mai toccati).

## 1. Che cosa succede: otto manuali su nove cominciano a parlare

| manuale | combinazioni prima | dopo |
| --- | ---: | ---: |
| DB | 2 | 13 |
| Dag | 17 | 104 |
| Apo | 0 | **0** |
| Wil | 0 | **9** |
| BiD | 0 | 22 |
| DIE | 0 | 8 |
| SV | 0 | 10 |
| Kul | 0 | 8 |
| Vil | 0 | 6 |

**Su Wil ci sono esattamente i tre campi previsti**: `{sentieri}`, `{mostri}`,
`{umani}`. Apocalisse resta muto, ed è giusto. Il §4.B del criterio — «dove
taceva, parla» — passa.

## 2. Il veto scatta, su un capitolo intero

**Dag idx 120 (stampata 119)**, guardata sull'immagine: è una tabella **vera**,
stampata con l'intestazione `NOME | TRATTO | PORTATA | DANNO | IMPUGNATURA |
CARATTERISTICA`. L'ultima colonna contiene `Sfarzosa:`, `Esplosivo:`,
`Spaventoso:`, `Versatile:`, `Ritornante:`, `Potente:`, `Brutale:`,
`Persuasiva:`, `Affidabile:`, `Rinvigorente:`.

Sono etichette dichiarate, ripetute in tutto il manuale, e **sempre alla stessa
x** — perché sono una colonna. Passano la ripetizione e passano il profilo di
posizione. La regola le prende per campi di scheda e le porta fuori dalla
tabella:

```
prima  | Spada Danzante | Forza | Mischia | d10+4 mag | A due mani | Versatile: Quest'arma può essere utilizzata
dopo   | Spada Danzante | Forza | Mischia | d10+4 mag | A due mani | le seguenti statistiche — Conoscenza, Lonta
```

Non è un caso isolato: **23 pagine di Dag** perdono celle che cominciano con
un'etichetta dichiarata, e quindici sono il capitolo delle tabelle delle armi
(idx 116-130).

## 3. Gli altri veti

| veto | esito |
| --- | --- |
| **A** dove funzionava non peggiora | **CADE** — Dag idx 120 e il capitolo delle armi |
| **B** dove taceva parla | **sì** — Wil riconosce `{sentieri}`, `{mostri}`, `{umani}` |
| **C** il rischio noto, misurato | **misurato, ed è peggio di come l'avevo scritto**: non sono gli elenchi con `Durata:`, sono le **celle di tabella** |
| **D** nessuna prosa tagliata | **CADE** — un orfano nuovo su BiD, uno su DIE |
| **E** barra | non eseguita: il veto ferma la misura |

**I due orfani di D** sono prosa tagliata a metà davanti a una riga che porta
un'etichetta **in mezzo**, non all'inizio:

```
BiD idx 138 (stampata 131)  «controllata. Successo Parziale (4/5): Risultato Misto. Quando comincia…»
DIE idx 366 (stampata 355)  «scossoni o da un forte rumore. Ha i seguenti effetti: Speciale: Se il bersaglio…»
```

`opens_a_record` cerca i due punti su **tutte** le etichette della riga —
emendamento del 20 settembre, perché il PDF spezza `Canto Incantatore - Azione:`
in tre span — e con una coppia sola per riga quella larghezza diventa un taglio
in mezzo alla prosa.

## 4. Che cosa ha dimostrato questa misura

**L'utente aveva ragione sulla premessa**: «almeno due coppie su una riga» non
descrive le schede, descrive Dragonbane e Daggerheart. Wil lo prova: con una
coppia per riga le sue carte AREA si riconoscono dai campi, e i tre campi trovati
sono i tre campi veri.

**E ha dato il controesempio giusto**: «ci sono schede che sono simili a
tabelle, come per DIE». Il rovescio è quello che ha fatto cadere la misura: ci
sono **tabelle le cui celle sono identiche a campi di scheda**. `Versatile:
Quest'arma…` dentro una cella e `Sentieri: Baia di Aso…` dentro una scheda sono
la stessa cosa, riga per riga.

**Quindi il numero di coppie non è mai stato il discriminante** — e toglierlo
lascia scoperto ciò che teneva nascosto. Il discriminante che manca non è sulla
riga: è **intorno** alla riga.

## 5. Conseguenza e strada

Come dichiarato, la regola si ritira: `_MINIMO_COPPIE_PER_RIGA` torna a 2 e la
misura di documento torna a chiedere due etichette. Resta il test negativo
imparato qui — `Meteo Costiero.` finisce con il punto e non è un campo.

La strada che la diagnosi indica, e che va dichiarata e misurata a parte: una
riga di campi **dentro una cella** ha testo alla sua sinistra alla stessa
altezza, dentro la stessa regione di tabella; una riga di campi di una scheda no.
Il rischio è noto in anticipo: su DB la scheda del gigante sta nella colonna
destra, e alla sua sinistra c'è la prosa della colonna sinistra — quindi «testo a
sinistra» va misurato **dentro la regione**, non sulla pagina.
