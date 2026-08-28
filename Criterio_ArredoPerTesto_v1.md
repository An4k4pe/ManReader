# Criterio — l'arredo si riconosce dal **testo che ripete**, non dalla fascia

**Scritto prima di implementarlo.**

## 0. Che cosa deve chiudere

Restano nel corpo, misurati e nominati dall'utente sulle pagine rese: `Capitolo 6`
e `Scourge` su FWK, `3` e `PREMI START` su Fab, il `5` su BiD, `[209]` su Lan, e
la testatina verticale `ATTIVITÀ DI DOWNTIME` sempre su BiD.

`Criterio_ArredoRicorrente_v3.md` §6 li dichiara fuori scope: «i titoli correnti
**in cima**», perché il ramo 2 guarda solo la fascia bassa e la fascia alta da
sola tira dentro corpo su tre manuali su sei.

> **Ma la fascia non è l'unico modo, e il repo lo dimostra già.** Il **ramo 1**
> non ha alcun vincolo di posizione: riconosce **che cosa** togliere — lo slot che
> porta l'etichetta della propria pagina — e lo toglie ovunque stia. La guardia
> contro la coincidenza è la ricorrenza dello slot, non la posizione.

Indicazione dell'utente, che ha ricordato quella regola e ha chiesto di cercarla:
è `document_furniture_policy.label_slots`. Questo criterio la generalizza da «il
numero di pagina» a «qualunque testo che si ripete».

## 1. Le due clausole

### A — lo slot che ripete **lo stesso testo**

> Uno slot ricorrente — occupato su almeno `RECURRENCE_SHARE` delle pagine — è
> **arredo, ovunque stia sulla pagina**, se **almeno un testo a quello slot
> compare su due o più pagine**.

**Nessuna fascia**, e nessun numero nuovo: `RECURRENCE_SHARE` è lo 0,25 del ramo
2, e «due» è il minimo per dire «si ripete», come altrove in questo progetto.

**È la condizione che separa**, misurata sulla fascia alta dove il ramo 2 non
arriva:

| manuale | slot | pagine | testi distinti | |
| --- | --- | ---: | ---: | --- |
| FWK | (44, 2) | 11 | **3** | `Capitolo 5` → arredo |
| FW | (44, 1) | 20 | **2** | `Il Mondo` → arredo |
| Lan | (92, 5) | 9 | **2** | `Harrison Armory` → arredo |
| DrW | (97, 8) | 8 | **1** | `Talent` → arredo |
| Kul | (4, 7) | 8 | **1** | `.` → arredo |
| BiD | (16, 7) | 10 | **10** | inizio della colonna di testo → **resta** |
| DrM | (10, 6) | 9 | **9** | `HUMANS`, titoli di scheda → **resta** |
| SV | (16, 8) | 9 | **9** | `ALLENARSI`, titoli veri → **resta** |

Una testatina ripete lo stesso testo; un titolo di sezione che capita in cima no.
Dove il testo cambia a ogni pagina la clausola tace, ed è esattamente il caso che
aveva fatto dichiarare la fascia alta troppo pericolosa.

### B — il testo **verticale**

> Una primitiva la cui direzione non è orizzontale è **arredo**.

Misurato su 20 pagine per manuale: il testo verticale esiste su **6 manuali su
16**, fra 9 e 36 primitive ciascuno, e **ogni** occorrenza è un nome di capitolo o
il titolo del manuale:

```
BiD  'ATTIVITÀ DI DOWNTIME', 'COINVOLGIMENTI'    8 testi distinti su 18
DrM  'Draw Steel', 'Hobgoblins'                  5 su 19
DrW  'Draw Steel', 'Tactician'                   4 su 18
Fab  'Arcanista', 'Artefice'                     8 su 36
Lan  'Harrison Armory', 'Horus'                  2 su  9
SV   '4 // L'Incarico', '5 // Downtime'          6 su 17
```

Nessuna somiglia a contenuto. È anche la classe che l'etichettatore dell'arredo
aveva nominato e che nessun ramo prendeva — `IL COLPO`, `GRIFFONS`, `TACTICIAN`.

**Su BiD la geometria lo dice senza ambiguità**: `ATTIVITÀ DI DOWNTIME` a slot
(96,18), 13,2 × 121,0, direzione `(0,-1)`; `DOWNTIME` a (1,23), direzione `(0,1)`
— bordo esterno, specchiato fra recto e verso. Il titolo vero è l'orizzontale a
corpo 30, e **compare una volta sola, a capo del capitolo**.

**Perché una clausola sua e non un caso della A**: una testatina verticale può
stare a slot diversi fra recto e verso e cambiare col capitolo, quindi la
ricorrenza dello slot non la coglie sempre. La direzione la coglie sempre.

## 2. Che cosa succede a ciò che esce

Invariato: esce dal corpo, va nel canale review, niente viene distrutto. È la
stessa macchina dei tre rami esistenti, con due sorgenti di slot in più.

## 3. Il campione

**12 voci** dalla clausola A e **tutte** le voci della clausola B — sono poche
abbastanza da guardarle per intero, e un campione le indebolirebbe. Seed
**`20261010`**, dichiarato qui.

**I manuali densi di schede restano nel campione**, a differenza del criterio dei
titoli: qui la categoria non altera la misura, perché l'arredo su una scheda è
arredo come altrove — e DrM e DrW hanno **entrambi** testatine verticali, che
sono metà di ciò che si giudica.

## 4. Pass/fail

### A. Veto — cade a una sola voce

> Cade se **una sola** voce tolta è giudicata contenuto.

Etichette **arredo** / **contenuto** / **incerto**, seed di controllo
**`20261011`**. Vale il rinforzo: una riserva accanto a un'etichetta netta conta
come `incerto`.

### B. Pavimento — i casi nominati devono sparire

> Devono uscire dal corpo: `Capitolo 6` e `Scourge` su FWK, `3` e `PREMI START`
> su Fab, il `5` su BiD, `[209]` su Lan, `ATTIVITÀ DI DOWNTIME` su BiD.

Sono i casi che l'utente ha nominato guardando le pagine rese. Se la regola non li
prende, non ha chiuso ciò per cui è stata scritta.

### C. Regressione — il titolo vero resta

> `attività di downtime` orizzontale a corpo 30 su BiD idx 162 deve **restare**
> un titolo nel corpo, e i quattro elenchi veri devono restare elenchi.

È la barra che impedisce alla clausola A di mangiarsi i titoli che portano lo
stesso testo della testatina. `check_list_regression.py` per la seconda metà.

### D. La giunzione

> Per ogni voce tolta si guarda il paragrafo sopra e sotto.

### Se cade

- **A**: la clausola che ha sbagliato si nomina e si ritira **da sola** — sono due
  clausole indipendenti e vanno potute spegnere separatamente.
- **B**: si riporta quali casi restano, senza allargare nello stesso giro.
- **C**: la clausola A è troppo larga e va ritirata; la B non può causarla, perché
  il titolo vero è orizzontale.

## 5. Che cosa resta fuori

- **Il font come seconda via per i marcatori d'elenco**, che sblocca Fab.
- **Le schede mostro come categoria.**
- **La gerarchia dei titoli.**
