# Esito di `Criterio_ArredoPerTesto_v1.md` — **una clausola ritirata, l'altra corretta e da rigiudicare**

**Stato in una riga**: la clausola A toglieva **contenuto su 7 voci su 12** ed è
**ritirata**; la clausola B ne ha sbagliata **1 su 9**, e la causa è che
l'implementazione non corrispondeva a ciò che il criterio aveva scritto.

---

## 1. Il verdetto, per clausola

21 voci, seed `20261010`, giudizio cieco. **Il totale non dice niente** — 13
arredo e 8 contenuto — perché le due clausole si comportano in modo opposto:

| clausola | voci | arredo | **contenuto** |
| --- | ---: | ---: | ---: |
| **A — testo ripetuto** | 12 | 5 | **7** |
| **B — verticale** | 9 | 8 | **1** |

Zero `incerto`.

## 2. Clausola A — **ritirata**

> Cade se una sola voce tolta è giudicata contenuto. **Sette su dodici.**

Che cosa toglieva, secondo chi ha guardato le pagine:

- **DrM `Stamina`** — «l'etichetta del terzo campo della riga statistiche della
  scheda mostro, stampata sotto il valore. Ricorre perché ricorre la scheda:
  perderla lascia il numero senza nome».
- **DrM, la cella-valore** della stessa riga statistiche.
- **DrW** — parole chiave di un'abilità (`Animapathy, Psionic, Ranged, Strike`),
  l'etichetta `Effect:`, il titolo `Grandmaster of Arms`.
- **DB** — righe di corpo e nomi di incantesimi (`Potere dal Corpo:`).

**Il difetto è nella condizione, non nella taratura.** «Almeno un testo si ripete
a quello slot» è soddisfatto da qualunque ripetizione **strutturale**: un campo di
scheda ricorre perché ricorre la scheda, non perché sia arredo. La condizione non
distingue una testatina da una struttura che si ripete.

> **La clausola resta calcolata e non usata**: `all_slots` non la include più. La
> misura serve a chi riaprirà il fascicolo, e il codice lo dice.

**Che cosa restava giusto**: 5 voci su 12 erano arredo vero, e tutte e cinque sono
le colonne di puntini decorativi del margine di Kul — le stesse che avevano già
dirottato la misura del corpo nel criterio dei titoli. Un fascicolo per loro
esisterebbe; questa clausola non era quello.

## 3. Clausola B — la singola caduta era **mia, non della regola**

La voce 17, Fab: la clausola toglieva `perfetti per viaggiare, e combatte con`,
prosa piena.

**La causa, verificata:**

```
Fab, slot (14,57), pagina per pagina
   idx 180  VERTICALE    'CONGEDO'
   idx 171  orizzontale  'perfetti per viaggiare, e combatte con'   ← tolta
   idx 187  orizzontale  'Esorcismo'
```

Il criterio §1.B dice «**una primitiva** la cui direzione non è orizzontale», e
l'avevo implementata marcando il suo **slot**. Lo slot porta testo verticale su
una pagina e prosa orizzontale su altre quattro, e la prosa usciva dal corpo.

**E c'era un secondo difetto sotto**, trovato correggendo il primo: gli **id di
primitiva non sono unici fra pagine**. `primitive:text:text:b0000:l0000:s0000`
esiste su ogni pagina, e su BiD **70 id su 203** sono ripetuti. Raccogliere gli id
verticali su tutto il documento marcava primitive omonime di altre pagine — il
titolo `attività di downtime` a corpo 30 finiva in review perché un'altra pagina
aveva una primitiva verticale con lo stesso id.

**Corretto**: gli id si raccolgono **per pagina**, e la verticalità non ha bisogno
della scansione del documento perché è un fatto della primitiva.

**Verificato dopo la correzione**: su BiD `## **attività di downtime**` resta nel
corpo e la testatina verticale `ATTIVITÀ DI DOWNTIME` esce; su Fab la prosa resta.

> **Il giudizio della clausola B non è più valido**: è stato dato su
> un'implementazione che non corrispondeva al criterio. Va rifatto sulla versione
> corretta, e le 8 voci giudicate arredo restano un indizio, non un verdetto.

## 4. Che cosa il giudizio conferma comunque

Le testatine verticali sono arredo: 8 voci su 9, e l'etichettatore le ha
riconosciute una per una descrivendone la composizione — «linguetta marrone sul
bordo destro con `TALENT` scritto in verticale, ruotato di 90°», «`4 // L'INCARICO`
in verticale sul bordo sinistro», «`PREMI START` sotto `CAPITOLO 3`».

E ha visto la distinzione che il criterio si era dato: su DrW «il vero titolo
compare separatamente in orizzontale (`Talent Tradition`), e quello resta».

## 5. Un limite del campione, dichiarato

Il ramo verticale produce **41 voci** e il campione ne ha 9: la stratificazione
per quota di ricorrenza tiene solo quelle sopra il 25%, e **le testatine verticali
cambiano col capitolo**, quindi il loro slot ricorre poco. Il campione copre circa
un quarto della classe, e non è esaustivo come il §3 lasciava intendere.

## 6. Conseguenza

- **Clausola A: ritirata.** Non si ritenta con una condizione in più nello stesso
  giro; il §4 del criterio lo vieta e il difetto è concettuale, non di taratura.
- **Clausola B: implementazione corretta, giudizio da rifare.**
- **Restano nel corpo** i casi che il criterio doveva chiudere e che dipendevano
  da A: i numeri e i nomi di capitolo in cima che non sono verticali.

## 7. Verifiche

Suite **1474** test, un solo fallimento, quello ambientale già a verbale.
