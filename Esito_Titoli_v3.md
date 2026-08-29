# Esito di `Criterio_Titoli_v3.md`, secondo giudizio — **precisione 76%, copertura 62%**

**Stato in una riga**: 45 voci marcate, **34 titolo, 9 non titolo, 2 incerto**; e
**21 titoli mancati** che il meccanismo non ha preso. Il veto §4.A cade in
entrambe le direzioni. Ma per la prima volta **le due direzioni sono misurate
sullo stesso materiale**, e i difetti si raggruppano in quattro schemi.

---

## 1. Perché questo giudizio vale e il precedente no

Il primo giudizio della v3 è stato invalidato a metà: il campione ricalcolava la
classificazione e la sua non era quella della pipeline. Qui il materiale viene da
`scripts/build_judgement_material.py`, che **non ricalcola niente**: fa girare la
pipeline e legge il `kind` dei nodi da `document_ir2.json`.

E il giudizio ha **due domande invece di due metà**: «questa voce è un titolo?» e
«che cosa sulla pagina avrebbe dovuto esserlo?». La copertura si misura guardando
la pagina, non un insieme di candidati ricostruito — che è il modo in cui l'utente
l'aveva misurata a mano, elencando `ridurre il sospetto`, `recuperare`,
`alleviare lo stress`.

14 pagine, seed `20261024` dichiarato prima, pagine sorteggiate **prima** di
renderle.

| | |
| --- | ---: |
| voci marcate | 45 |
| titolo | **34** |
| non titolo | **9** |
| incerto | 2 |
| **titoli mancati** | **21** |

**Precisione 34/45 = 76%. Copertura 34/55 = 62%.**

## 2. I quattro schemi, che valgono più dei numeri

### A — I titoli **in linea** non vengono mai presi (11 dei 21 mancati)

Dove l'intestazione sta sulla stessa riga tipografica del testo che apre, o viene
fusa nel paragrafo in fase di resa, il meccanismo la perde **sempre**:

```
Apo   **LA DONNA DI CENDRES** Nonostante alcune remore…
Vil   **DONI I doni sono aspetti del tuo retaggio oscuro…
Fab   sette barre-intestazione su sette, nessuna presa
```

Pagine 01 (2 su 2), 12 (2 su 2), 06 (**7 su 7**). È il difetto di copertura
dominante, ed è lo stesso che l'utente aveva visto su BiD e Dag e che la v3 aveva
chiuso per i casi dove il titolo è una riga sua. Qui il titolo **non è una riga**.

### B — Prende i figli e perde il padre (3 mancati)

Su Lan tutti i blocchi-sistema sono marcati e **tutte e tre le barre `LICENZA …`
che li raggruppano** sono mancate:

```
marcati:   GENERATORE DI FULMINI, IMPULSO EMP, SMARTGUN, ARMA MIMICA…
mancato:   LICENZA III: GENERATORE DI FULMINI, IMPULSO EMP
```

Il risultato è una gerarchia **senza contenitori**: i figli restano orfani del
loro livello.

### C — Il numero di pagina entra come titolo (8 dei 9 falsi positivi)

`223`, `151`, `[208]`, `[211]`, `[218]`, `155`, `166`, e la testatina più folio
`Fortuna & Sciagura 115`. **Otto dei nove falsi positivi sono arredo di pagina**,
e su Lan il folio finisce a `###` in mezzo al testo.

> **Non è un difetto dei titoli.** La condizione 4 del §1 — «non è già escluso
> come arredo» — c'è ed è rispettata: è l'arredo che non li prende. E
> `Esito_ArredoPerTesto_v1.md` ha appena **ritirato** la clausola che avrebbe
> dovuto farlo.

Con l'arredo a posto, la precisione passerebbe da **76% a 96%** senza toccare una
riga del meccanismo dei titoli.

### D — Targhette identiche trattate in modo diverso

Su Wil, nella stessa scheda, `INGREDIENTI` è marcata e `SENTIERI E COMUNITÀ` e
`TRATTI` no, «benché siano la stessa forma grafica». E le etichette di colonna
`STILE NOME EFFETTO` sono marcate su idx 154 e **non** su idx 165 — **la stessa
tabella dello stesso manuale**.

È il rilievo più scomodo: non è che la regola sbagli in una direzione, è che **non
è stabile** fra due pagine equivalenti.

## 3. Due difetti puntuali, entrambi reali

**Doppia marcatura dello stesso titolo.** Su Fab idx 183 `ARTEFICE` esce due
volte, a livello **1** e a livello **3**: «nell'EPUB produrrà due voci d'indice per
un solo titolo». Sono lo stesso oggetto sulla pagina.

**La gerarchia appiattita.** Su Dag i livelli tipografici sono **tre** — viola
grande, viola col quadratino, arancione — e il meccanismo li rende tutti `###`.
È il collasso a tre livelli deciso con l'utente, e qui si vede il suo costo su una
pagina che ne aveva davvero tre distinti.

## 4. Le due `incerto`, e il canale che funziona

`AREA` su Wil, due volte: «è la targhetta incastonata sopra il cartiglio, qualifica
il **tipo** di scheda, e il contenuto sta semanticamente sotto il nome dell'area,
non sotto la parola AREA. Sta in cima al riquadro quindi si comporta da
intestazione, ma è un'etichetta di categoria ripetuta identica su ogni scheda».

È un dubbio vero, dichiarato come `incerto` invece che nascosto accanto a
un'etichetta netta. Seconda volta di fila che il rinforzo del protocollo funziona.

## 5. Che cosa il giudizio conferma

Le 34 voci giuste coprono tutto il ventaglio: nomi di mech (`HORUS MANTICORE`),
di classe (`ARTEFICE`, `Autostoppista`), di sezione (`MORTE DI UN PERSONAGGIO`,
`IMPOSTARE`), di riquadro (`CARATTERISTICHE PRIMARIE`, `TRATTI`), di area
(`FIUME YHAYHE`). E cinque pagine su quattordici sono dichiarate **senza nulla di
mancante**.

L'etichettatore ha anche escluso **volutamente** dai mancanti tre classi che
titoli non sono: i raggruppatori di righe dati (`SCAFO`, `AGILITÀ`), i badge
(`SUPPORTO FLESSIBILE`), le righe di qualifica (`Assalto`, `Sostituisce
**Furfante**`, `ANCHE: Alchimista, …`). Sono distinzioni che il criterio non aveva
nominato e che valgono per il prossimo giro.

## 6. Conseguenza

Il criterio **non è scaricato**, ma per la prima volta si sa **dove** e in che
proporzione:

| difetto | quanto pesa | dove sta il fascicolo |
| --- | --- | --- |
| arredo non tolto | **8 dei 9** falsi positivi | **l'arredo**, non i titoli |
| titoli in linea | **11 dei 21** mancati | i titoli |
| il padre perso | 3 dei 21 | i titoli, e serve la gerarchia |
| instabilità fra pagine | non quantificata | i titoli |

> **Il primo non è nostro da risolvere qui**, e da solo porta la precisione dal
> 76% al 96%. Il secondo è il pezzo di lavoro più grosso e più utile che resta sui
> titoli.

Non si ritocca niente in questo giro: il §4 lo vieta, e i due difetti maggiori
stanno in due fascicoli diversi.

## 7. Verifiche

Suite **1474** test, un solo fallimento, quello ambientale già a verbale.
