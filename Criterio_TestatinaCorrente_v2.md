# Criterio — la testatina, v2: **non sta in mezzo a un testo**

Emenda `Criterio_TestatinaCorrente_v1.md`, che è scaricato a 23 voci su 25.
Aggiunge una condizione sola e non tocca il resto.

## 0. Il caso

Indicazione dell'utente su BiD idx 287: «*sono esattamente allo stesso posto? nel
caso non lo toglierei perché fa parte della lettura, e quindi aggiornerei la
regola sulle parole ripetute nello stesso punto solo sui bordi o comunque non in
mezzo ad un testo*».

**Sì, esattamente**, e misurato:

```
6 pagine su 20, tutte a  x 63,0→206,1   y 358,0→377,7   — identiche al decimale
```

E `punti di riferimento` **non è arredo**: introduce l'elenco dei luoghi del
quartiere, sta a metà pagina con testo sopra e sotto, e fa parte della lettura.

Le altre «testatine» che il ramo trova su quella finestra dicono da dove viene:
`Benessere`, `DETTAGLI`, `Influenza Criminale`, `Influenza Occulta`, `Scene:`,
`Sicurezza`, `TRATTI` — **etichette di una scheda ripetuta**. È il debito delle
schede per la **quinta** volta, con un profilo nuovo: la clausola regge quando i
campi si spostano col contenuto — `Stamina` di DrM sta su 31 slot — e cade quando
la scheda ha **campi a posizione fissa**.

## 1. Perché non una fascia di bordo

La formulazione «solo sui bordi» tradotta in una fascia tarata **escluderebbe
testatine vere**, misurato — distanza dal bordo più vicino, su 100:

```
G I O C A R E   Vil   11        Capitolo 6   FWK    2
CAPITOLO        Fab   10        Il Mondo     FW     1
PREMI START     Fab    7        DOWNTIME     BiD    1
```

Una fascia larga abbastanza da tenere `G I O C A R E` sarebbe larga 11 su 100, e
`punti di riferimento` sta a 30 — passerebbe. Ma la fascia sarebbe un numero
scelto guardando i dati, che è la cosa che qui non si fa.

## 2. La regola

> Una testatina deve avere **almeno un lato libero**: almeno una direzione —
> sopra, sotto, sinistra, destra — in cui, oltre di lei, sulla pagina non c'è
> altro testo.

È la formulazione letterale dell'utente, «non in mezzo a un testo», e non ha
numeri dentro. Il resto del `Criterio_TestatinaCorrente_v1.md` resta invariato:
si parte dal testo, si confronta testo **e** posizione, si specchia sul centro.

### Misurato prima di implementarla

```
testatine con almeno un lato libero:   32 su 33
circondate da testo:                    1
punti di riferimento:                   CIRCONDATA, nessun lato libero
```

## 3. Il costo, dichiarato

L'unica delle 33 che è circondata è **`CAPITOLO 5 – MAGIA` su DB**, già giudicata
arredo: sta in fondo alla pagina ma col folio sotto di sé, quindi nessuna
direzione le resta libera. **Resta nel corpo.**

Una persa per una salvata, ed è la scelta che l'utente ha fatto: `punti di
riferimento` «fa parte della lettura».

## 4. Pass/fail

### A. Il caso che l'ha imposta

> `punti di riferimento` deve restare nel corpo su BiD idx 287.

**Passa**: l'unica cosa che esce da quella pagina è il numero `280`.

### B. Le testatine che il giudizio ha confermato

> Le voci giudicate arredo in `Esito_TestatinaCorrente_v1.md` devono restare
> fuori dal corpo, salvo quelle che questo criterio dichiara perse.

**Passa sui casi nominati dall'utente**: `Personaggi 61` su Vil, `Capitolo 2` e
`32` su FWK, `72` su Wil, `CAPITOLO` su Fab escono tutti.
**Persa e dichiarata**: `CAPITOLO 5 – MAGIA` su DB.

### C. Il contenuto si conserva

> Nessuna pagina perde testo.

**Passa** sulle dieci: nessuna esclusione nuova oltre a quelle richieste.

## 5. Che cosa resta aperto, e non tocco qui

**Otto voci d'elenco false su Fab idx 126** — `- 2`, `- 3`, cifre sole sulla
pagina che è una tabella. Sono comparse spostando la finestra, non con questa
clausola, e violano la barra D di `Criterio_AmbitoDeiFatti_v2.md`. Vanno
diagnosticate in un giro loro: aggiungere qui una condizione sarebbe il giro di
rifinitura che il `CLAUDE.md` dice di fermare.
