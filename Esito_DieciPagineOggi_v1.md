# Esito — le dieci pagine: **le due barre dure passano**, e il lavoro è la classifica

**Stato in una riga**: nessuna pagina perde contenuto, nessuna perde qualcosa
per colpa dell'arredo, nessuna è stata giudicata illeggibile — e **zero pagine su
dieci** sono senza rilievi. Ciò che non funziona non è la conservazione: è dire
che cosa le cose sono.

---

## 1. Le barre

| barra | esito |
| --- | --- |
| **A** — il contenuto si conserva | **PASSA**, 10 su 10: `manca qualcosa` vuoto ovunque |
| **B** — l'arredo non porta via contenuto | **PASSA**, 10 su 10: `tolto a torto` vuoto ovunque |
| **C** — la leggibilità, che si riporta | `si legge` vuoto ovunque; **rilievi di classifica su 10 pagine su 10** |

> Le due barre che potevano far cadere il giro **hanno retto**, e su un campione
> che non ho scelto io. La pipeline non distrugge e non nasconde: sbaglia a
> etichettare.

## 2. I difetti, per famiglia

### A — I titoli non riconosciuti, **4 pagine su 10**

```
Apo idx  34   REGOLE FERREE        «dovrebbe essere un titolo»
BiD idx 287   whitecrown           «è un titolo»
Vil idx  64   LA TUA PULSIONE      «dovrebbe essere titolo»
Wil idx  71   IL BANCHETTO         «titolo»
```

È il difetto dominante, e **conferma su un campione indipendente** ciò che
`Esito_Titoli_v3.md` misurava come copertura al 62%. Su Apo `REGOLE FERREE` è lo
stesso schema del ramo caduto ieri: composto più piccolo del corpo, sopra il
paragrafo.

### B — L'arredo che resta nel corpo, **4 pagine**

```
FWK idx  31   «Capitolo 2 da eliminare» + il numero di pagina
Vil idx  64   **Personaggi 61**  «è capitolo e numero pagina, da togliere»
Wil idx  71   il numero di pagina
Fab idx 126   CAPITOLO, il 2 della banda, e l'artefatto W
```

Le linguette di capitolo e i numeri di pagina passano ancora. `W` su Fab è
l'ornamento a un glifo che il ramo delle testatine rifiuta per la riga
`len(text) < 2` — già a verbale, e qui esce in un giudizio indipendente.

### C — Gli asset, **3 pagine**

```
Dag idx 199   «manca il riferimento all'immagine, ce ne sono due nel folder»
BiD idx 287   «l'immagine della carta da cui derivano i numeri non è negli estratti»
              «i disegni sono sbagliati»
BoB idx 297   «il riferimento alla banda laterale non serve che sia visualizzato»
```

**Verificato su Dag idx 199**: nel folder ci sono **quattro** immagini, non due, e
il corpo porta **zero** note. Tutte e quattro stanno nel canale review, perché
`RENDER_UNRESOLVED_ASSET_NOTES` è spento e nessun candidato le ha accettate.

È **metà dell'obiettivo** — «immagini sostituite da note brevi che dicono cosa
sostituiscono» — e su quella pagina non c'è.

**Verificato su BoB idx 297**: la nota è `[riquadro] 37×178 pt`, cioè una striscia
verticale: una banda di bordo classificata come riquadro interno.

### D — Le tabelle, fuori dal giudizio per dichiarazione

```
BiD idx 314   «è una tabella, bisogna solo unire le colonne»
Fab idx 126   «è una tabella, quindi sappiamo che è problematica»
```

Non contano contro nessuna barra, per il §4 del criterio. `BiD idx 314` porta
un'indicazione utile: quella tabella è a un passo, servono solo le colonne unite.

## 3. Il numero stampato: l'inferenza dell'utente, e la correzione

Rilievo su tre pagine: «*è la pagina sbagliata, stimandola hai stimato male, qui
il numero pagina e l'indice coincidono*».

**Il ramo non stima male.** Verificato leggendo l'inchiostro sulla pagina:

```
FWK idx 122   sulla pagina c'è '123'   dedotto '123'   ✓
FWK idx  31   sulla pagina c'è  '32'   dedotto  '32'   ✓
Wil idx  71   sulla pagina c'è  '72'   dedotto  '72'   ✓
FW  idx 150   sulla pagina c'è '151'   dedotto '151'   ✓
```

**Il difetto è mio, ed è di tubatura.** Nel materiale FWK idx 31 e Wil idx 71
uscivano `«?»`, e da lì l'impressione che il numero fosse indovinato male. La
causa: il numero dedotto vive nella scansione del documento, e quella finestra è
centrata **sul documento**, non sulla pagina richiesta. Il prototipo deduce numeri
per pagine che nessuno ha chiesto e non per quella che sta rendendo.

E una cosa che il rilievo dice bene: su questi tre manuali **il numero è stampato
sulla pagina**. `page.get_label()` non lo dichiara, ma l'inchiostro c'è. La riga
che ho scritto in `CLAUDE.md` resta vera nei numeri e va letta così: il ramo
**trova** il numero giusto, quando lo si interroga sulla pagina giusta.

## 4. Che cosa questo dice della domanda di partenza

L'utente aveva chiesto se queste dieci pagine reggano ancora come riferimento
statico di E-B, avendole giudicate prima di 26 commit sull'IR.

> **Reggono.** E-B controlla ordine e inclusione, e il giudizio non ha trovato
> né riordino né perdite: `manca qualcosa` è vuoto su tutte e dieci. Ciò che il
> giudizio ha trovato — titoli, arredo, asset — è **fuori** da ciò che E-B
> guarda, per costruzione.

Le due cose restano separate e valgono entrambe: E-B come non-regressione
indipendente sull'ordine, questo giudizio come stato dell'uscita.

## 5. Il lavoro, in ordine

1. **I titoli**, 4 pagine su 10 e primo difetto in tre giudizi di fila.
2. **Gli asset non resi**: Dag idx 199 non porta nessuna delle sue quattro
   immagini, ed è metà dell'obiettivo che manca.
3. **L'arredo residuo**: linguette di capitolo e numeri di pagina, 4 pagine.
4. **La finestra della scansione**, centrata sulla pagina invece che sul
   documento — difetto piccolo, e tocca ogni pagina resa.
