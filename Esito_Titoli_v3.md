# Esito di `Criterio_Titoli_v3.md`, secondo giudizio — **precisione ~89%, copertura 62%**

**Stato in una riga**: **21 titoli mancati**, e fra le voci che il lettore vede
davvero **3 non sono titoli**. Il veto §4.A cade in entrambe le direzioni. Ma per
la prima volta le due direzioni sono misurate sullo stesso materiale, e i difetti
si raggruppano in quattro schemi.

> **Correzione a questo stesso verbale, prima che venisse usato.** La prima
> versione diceva «45 voci marcate, 34 titolo, 9 non titolo» e ne ricavava una
> precisione del **76%**. Era falso: **sei delle nove «non titolo» sono numeri di
> pagina che la pipeline TOGLIE** — stanno in `review_ir2.md`, non nel corpo. Il
> materiale me li mostrava lo stesso, perche' leggevo `document_ir2.json`, che
> contiene **tutti** i nodi: l'esclusione dell'arredo e' una decisione di resa, e
> il contratto dice «il nodo resta, cambia la resa».
>
> Il giudizio su quelle sei era corretto — numeri di pagina non sono titoli — ma
> era su cose **che il lettore non vede**. Lo strumento ora legge gli id esclusi
> dal canale review e non li mette nel materiale: le voci passano da 45 a 38.

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
| voci giudicate | 45 |
| di cui **mai rese nel corpo** | **7** |
| voci che il lettore vede | **38** |
| titolo | **34** |
| non titolo, nel corpo | **3** |
| incerto | 2 |
| **titoli mancati** | **21** |

**Precisione ≈ 34/38 = 89%** sulle voci rese — **94%** se le due `incerto` non si
contano contro. **Copertura 34/55 = 62%.**

I tre falsi positivi veri: `Fortuna & Sciagura 115` su Kul (testatina più folio),
`[218]` su Lan (numero di pagina), `STILE NOME EFFETTO` su Wil (etichette di
colonna concatenate).

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

### C — Il numero di pagina, e la correzione che ridimensiona questo schema

Il giudizio ha trovato nove voci che titoli non sono, e otto erano arredo di
pagina: `223`, `151`, `[208]`, `[211]`, `[218]`, `155`, `166`, e la testatina più
folio `Fortuna & Sciagura 115`.

**Ma sei di quelle otto la pipeline le toglie davvero.** Verificato una per una
sulla resa: stanno in `review_ir2.md`. Erano nel materiale per il difetto
descritto in testa a questo verbale.

**Restano due**, e sono veri: `Fortuna & Sciagura 115` su Kul e `[218]` su Lan —
dove il folio finisce a `###` in mezzo al testo. Su Lan lo slot porta l'etichetta
della propria pagina solo su **4 pagine su 20**, sotto la soglia di un quarto del
ramo 1; su Kul lo stesso, 4 su 20.

> **Non è un difetto dei titoli**: la condizione 4 del §1 — «non è già escluso
> come arredo» — c'è ed è rispettata. È l'arredo che su quei due manuali non
> arriva alla soglia.

Con quei due tolti la precisione passerebbe dall'89% al **95%**.

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
| **titoli in linea** | **11 dei 21** mancati | **i titoli** |
| il padre perso | 3 dei 21 | i titoli, e serve la gerarchia |
| targhette non prese | 4 dei 21 | i titoli |
| arredo sotto soglia | 2 dei 3 falsi positivi | l'arredo |
| etichette di colonna | 1 dei 3 | i titoli |
| instabilità fra pagine | non quantificata | i titoli |

> **Il difetto dominante è la copertura, non la precisione**, ed è l'opposto di
> quello che la prima versione di questo verbale diceva. I titoli in linea da soli
> valgono metà dei mancati.

Non si ritocca niente in questo giro: il §4 lo vieta, e i due difetti maggiori
stanno in due fascicoli diversi.

## 7. Verifiche

Suite **1474** test, un solo fallimento, quello ambientale già a verbale.
