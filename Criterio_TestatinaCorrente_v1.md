# Criterio — la testatina corrente, **a qualunque posizione**

**Scritto prima di implementarlo.**

## 0. Che cosa deve chiudere, e perché la clausola A non bastava

Indicazione dell'utente: «le testatine devono funzionare in qualsiasi posizione,
alto basso laterale e verso e recto, es i capitoli di Fab».

Restano nel corpo, misurati: `Vileborn` su Apo (80% delle pagine, y=18),
`Capitolo 6` e `Scourge` su FWK, `PREMI START` e `CAPITOLO` su Fab, `Fortuna &
Sciagura` su Kul — che è anche l'ultimo falso positivo rimasto del giudizio dei
titoli.

**La clausola A di `Criterio_ArredoPerTesto_v1.md` è caduta**, e va detto perché
questa non è la stessa cosa. Quella chiedeva: *«a questo slot si ripete qualche
testo?»* — **partiva dallo slot**. E un campo di scheda ripete il suo testo, per
cui `Stamina` di Draw Steel usciva dal corpo su 7 voci su 12 giudicate contenuto.

Questa parte **dal testo**:

> *«questo testo sta sempre nello stesso posto?»*

E la misura dice che è la domanda giusta: `Stamina` compare su 16 pagine sparsa su
**31 slot diversi**, `Psionic` di DrW su **71**. Una scheda si sposta col contenuto
della pagina. `Vileborn` compare su 16 pagine a **un solo slot**.

## 1. La regola

> Un testo è **testatina** se:
>
> 1. compare su almeno `RECURRENCE_SHARE` delle pagine;
> 2. la **maggioranza** delle sue occorrenze sta a **uno stesso slot
>    specchiato**;
> 3. quello slot ricorre su almeno `RECURRENCE_SHARE` delle pagine.
>
> **Nessun vincolo di posizione.**

**Nessun numero nuovo.** `RECURRENCE_SHARE` è lo 0,25 già usato dai rami 1 e 2, e
la *maggioranza* del punto 2 è la stessa soglia naturale che separa i marcatori
d'elenco dalla punteggiatura in `document_list_policy`: è il punto in cui un testo
smette di stare in giro e comincia a stare in un posto.

**Lo slot è specchiato** per la ragione già misurata: un arredo non centrato si
riflette fra recto e verso, e contarne le due posizioni separate lo dimezza. Si
usa `mirrored_centre`, perché lo specchio del bordo sinistro di un elemento
allineato a destra è il suo bordo destro — su Kul `100-72` fa 28 mentre il verso
sta a 25.

### Che cosa trova, misurato prima di eseguirlo

| manuale | trovate | dove |
| --- | --- | --- |
| Fab | `PREMI START`, `CAPITOLO` | y=43, 39 — **laterale** |
| FWK | `Capitolo 6`, `Scourge` | y=2 — alto |
| Kul | `Il Risveglio`, `Fortuna & Sciagura` | y=4 — alto |
| FW | `Il Mondo`, `capitolo 4` | y=1 — alto |
| BiD | `DOWNTIME` | y=23 — **verticale** |
| DrM, DrW | `Draw Steel`, `Talent` | y=85, 8 |
| Apo | `Secondo atto`, `Primo atto` | y=95 — basso |
| Vil | `Giocare`, `G I O C A R E` | y=95 e 11 |
| Dag | `Capitolo 3: Condurre…` | y=96 |
| DB, DIE, Lan | la filigrana d'acquisto, `8. BESTIARIO`, `Horus` | y=95-97 |
| **BoB, Wil** | **nessuna** | |

Da 0 a 3 voci per manuale, e **ogni voce dell'elenco è arredo**. Le posizioni
coprono tutto: y da 1 a 97, e il caso verticale di BiD.

## 2. Il rischio dichiarato

**BoB e Wil danno zero.** Non so se sia perché non hanno testatine o perché la
regola le manca, e il §3 lo chiede esplicitamente al giudizio.

> **Verificato il 30 agosto 2026, prima del giudizio.** I due zeri sono **fatti**.
> Su **BoB** nessun testo compare su almeno un quarto delle pagine, e le fasce
> alta e bassa portano solo corpo: il numero di pagina sta in una striscia
> decorativa al margine destro, che il ramo 1 prende. Su **Wil** ciò che ricorre
> sono le etichette della scheda d'area — `TRATTI` su 17 pagine ma **18 slot**,
> `Ottieni (1)` su 17 ma **30 slot**, concentrazione 6-25% — cioè esattamente il
> caso `Stamina`: la scheda si sposta col contenuto. In fondo alla pagina c'è un
> fregio decorativo col solo folio.
>
> La domanda del §3 su BoB e Wil resta comunque al giudizio, ma con
> l'aspettativa dichiarata: **non manca niente**.

**Un titolo di sezione ripetuto potrebbe passare.** Se un manuale stampa lo stesso
titolo in cima a più pagine consecutive di una sezione lunga, la regola lo prende.
È il rischio speculare a quello della clausola A, e la barra del §4.A esiste per
misurarlo.

## 3. Il campione

**Tutte le voci trovate** — sono 25 in tutto sui 16 manuali, e guardarle per
intero costa meno che difendere un campione. Nessun sorteggio, nessun seed.

**E una seconda domanda, sulle pagine di BoB e Wil**: si mostrano 4 pagine di
ciascuno e si chiede se ci sia una testatina che la regola non ha preso. È
l'unico modo di sapere se lo zero è un fatto o una lacuna.

Il materiale si costruisce con `scripts/build_judgement_material.py`, che legge
dalla pipeline e mostra la pagina intera.

## 4. Pass/fail

### A. Veto — cade a una sola voce

> Cade se **una sola** delle voci tolte è giudicata contenuto.

Zero, come per ogni clausola che sottrae testo. Etichette **arredo** /
**contenuto** / **incerto**, e vale il rinforzo: una riserva accanto a
un'etichetta netta conta come `incerto`.

### B. I casi nominati devono sparire

> Devono uscire dal corpo: `Vileborn` su Apo, `Capitolo 6` e `Scourge` su FWK,
> `PREMI START` e `CAPITOLO` su Fab, `Fortuna & Sciagura` su Kul.

Sono i casi che l'utente ha nominato guardando le pagine. Se la regola non li
prende, non ha chiuso ciò per cui è stata scritta.

### C. Regressione — il contenuto che la clausola A toglieva deve restare

> `Stamina` e la riga statistiche di DrM, le parole chiave delle abilità di DrW,
> le righe di corpo di DB **devono restare nel corpo**.

È la barra che distingue questa clausola da quella ritirata. Se cade, la regola è
la stessa con un altro nome.

### D. La giunzione

> Per ogni voce tolta si guarda il paragrafo sopra e sotto.

### Se cade

- **A**: si nomina la voce e la clausola si ritira, come la A. Non si aggiunge
  una condizione nello stesso giro.
- **B**: si riporta quali casi restano.
- **C**: ritiro immediato — sarebbe la clausola A rifatta.

## 5. Che cosa resta fuori

- **La distinzione fra testatina e titolo omonimo**: su BiD il capitolo si chiama
  `ATTIVITÀ DI DOWNTIME` e il titolo vero porta lo stesso testo. La clausola del
  verticale lo risolve per quel caso; in generale no, e la barra C non lo copre.
- **Le schede mostro come categoria.**
- **La clausola A**, che resta ritirata: questa non la resuscita, la sostituisce
  con una domanda diversa.
