# Criterio — gli elenchi, v2. Che cosa è caduto della v1 e con che cosa si sostituisce

## 0. La v1 è caduta sul suo stesso §5.C, e va detto per primo

`Criterio_Elenchi_v1.md` fissava un veto di falso positivo: *«si stampano i
marcatori trovati per ognuno dei 16 manuali e si guardano; cade se la regola
dichiara marcatore un carattere che nel manuale è punteggiatura»*. Eseguito:

| | la v1 trovava |
| --- | --- |
| Kul | `.` ×1098 — righe fatte **solo di un punto** |
| SV | `“` ×84 — aperture di dialogo |
| Apo | `+` ×4 — valori di scheda, `+1` |
| **DB** | **niente**, e DB ha `✦` su 312 righe |
| **BoB, BiD, DrM, DrW, Vil, Lan, Wil** | **niente** |

Falsi positivi **e** falsi negativi insieme, cioè il peggio dei due mondi.

**La causa è una mia asserzione mai verificata.** La condizione 3 della v1
chiedeva «almeno due righe dello **stesso blocco sorgente**», e l'avevo scritta
come «il minimo che fa di un elenco un elenco». Misurata: su DB `✦` apre 312
righe e ha **zero** blocchi con due righe, perché **ogni voce d'elenco è un
blocco a sé**. La condizione non era il minimo di un elenco: era la descrizione
di un elenco che non esiste.

> Una barra di falsificazione scritta prima ha fatto esattamente il suo mestiere.
> È la seconda volta in questo giro — il pavimento dell'arredo era caduto allo
> stesso modo — e in entrambi i casi il difetto era una quantità che avevo
> dichiarato ovvia senza guardarla.

## 1. La regola nuova

> Un carattere è **marcatore d'elenco di quel documento** se:
>
> 1. è non alfanumerico e non spazio;
> 2. **non è punteggiatura appaiata** — categorie Unicode `Ps`, `Pe`, `Pi`,
>    `Pf`;
> 3. la **maggioranza** delle sue occorrenze apre una riga;
> 4. su una **maggioranza** delle righe che apre, del **testo lo segue**: sulla
>    stessa riga, o sulla riga successiva quando il marcatore sta da solo — e
>    quella riga successiva non deve essere a sua volta un marcatore;
> 5. apre righe su almeno **due pagine**.

**Nessuna delle cinque è un numero tarato, e ognuna ha il suo fatto.**

- La **2** non è una lista di caratteri scelta a mano: è una proprietà che
  Unicode dichiara. Un carattere che apre o chiude una coppia vive dentro una
  frase per definizione. È ciò che scarta `“` di SV e le parentesi.
- La **3** resta della v1 ed è la sola che ha retto: separa dove un carattere
  vive, a inizio riga o in mezzo alle frasi.
- La **4** è quella che sostituisce la condizione caduta, e viene da una misura:
  su FW `•` sta da solo 41 volte su 41 e la riga dopo è il testo della voce; su
  Kul `.` sta da solo 1096 volte su 1098 e la riga dopo è **un altro punto** —
  una fila di puntini decorativi. Guardare solo la riga del marcatore li
  confondeva; guardare che cosa segue li separa.
- La **5** dice che un elenco è un modo di comporre che il manuale usa, non un
  caso capitato una volta. Due pagine è il minimo per dire «ricorre», ed è lo
  stesso ragionamento che rende document-level la misura dell'arredo. Scarta
  `—`×1 di BoB, `"`×1 di FWK, `¿`×1 di Lan, `+`×4 di Apo.

### Il risultato sui 16 manuali

| manuale | marcatori |
| --- | --- |
| Apo, Vil | `↳` |
| BiD | `\x90` |
| BoB | `\x8b` |
| DB | `✦` (312 righe) |
| DIE | `¥` |
| Dag | `•` |
| DrM | `!` `@` `#` |
| DrW | `¥` `£` |
| FW | `•`, **`…`** |
| FWK | `*` `•` |
| Lan | `⬣` |
| Wil | `◈` |
| **Fab, Kul, SV** | **nessuno** |

Kul, SV e Fab a zero è il risultato **giusto**: i loro candidati erano puntini,
virgolette e niente.

> **`…` di FW resta**, ed è il caso di contenuto che la v1 aveva nominato in
> anticipo. Sopravvive a tutti e cinque i filtri strutturali perché per struttura
> *è* un marcatore: apre 18 righe su 18, non è appaiato, ha testo dopo, sta su
> più pagine. Solo la lettura può dire che è un'ellissi che continua la frase
> precedente. **È il lavoro del veto §3.A, non di un filtro.**

## 2. Che cosa succede al marcatore

Invariato dalla v1: esce dalla resa, resta nel nodo, la voce diventa `- `.

Due cose imparate implementando, che la v1 non prevedeva e che stanno qui perché
non si ripetano:

**Il marcatore si toglie dai run, non dalla stringa resa.** Su FW il glifo è in
grassetto, quindi `render_runs` lo avvolge in asterischi e cercarlo in testa alla
stringa già resa lo mancava: usciva `- • Afflizione`.

**Si tolgono tutti i marcatori in testa, non il primo.** Dove l'ordine di lettura
interlaccia due colonne d'elenco arrivano due glifi di fila — misurato su FW
p.168, blocchi `b0011` a x=58 e `b0012` a x=214 — e toglierne uno ne lasciava uno
in mezzo alla voce.

**Una voce senza testo non si rende.** Stesso caso: un glifo orfano del suo testo
produceva `- ` vuoto, e il testo finiva in un paragrafo a parte. Ora il glifo
sparisce e il testo resta un paragrafo. È il limite dell'ordine di lettura a due
colonne, già a verbale nel builder per DB p.53, e **non** si finge risolto.

## 3. Pass/fail

### A. Veto di contenuto — cade a una sola voce

> Cade se **una sola voce** è giudicata `non elenco`: il carattere tolto portava
> significato, o le righe non erano un elenco.

**Il campione**: 12 voci con seed `20260912` — invariato dalla v1, perché non è
stato speso — dai dieci manuali mai usati. Più, **d'ufficio e non a sorteggio**,
le righe `…` di FW e un elenco di DB.

Giudizio come `Criterio_NumeroDedotto_v1.md` §4: agente cieco, poi l'utente sulle
contestate più un terzo delle altre, seed `20260913`. Un dubbio in prosa è un
`incerto`.

**Se cade solo su `…`**: non si butta la regola, si cambia il §2 — il marcatore
si tiene invece di toglierlo — e si rigiudica. *Dove sta un elenco* e *che fare
del marcatore* restano due decisioni separate.

### B. Pavimento — invariato

> Le righe che si aprono con un marcatore e che oggi finiscono dentro un
> paragrafo insieme ad altre devono diventare voci d'elenco per almeno **tre
> quarti**.

Senza pavimento la regola nulla — non riconoscere niente — passerebbe il veto a
pieni voti. È il difetto che ha fatto cadere la v2 dell'arredo.

### C. Falso positivo — **non è più un test indipendente, ed è la cosa più
importante di questo criterio**

Il §5.C della v1 è stato usato come **strumento di progetto**: l'ho eseguito,
è caduto, ho cambiato la regola, l'ho rieseguito. La tabella del §1 è quindi
il risultato di un'iterazione contro quella barra, **non una sua verifica**.

`AGENTS.MD` §16 permette di iterare sul progetto del meccanismo su pagine già
spese. Ma ciò che è stato tarato contro una barra non può essere dichiarato
scaricato da quella barra, e questo criterio **non lo dichiara**.

> Ciò che resta indipendente è il **veto A**, su un campione mai estratto, e il
> **pavimento B**. Sono quelli che decidono.

Il modello nullo si esegue lo stesso, come controllo che la barra non sia finta:
`--nullo` prende `“` su 12 manuali e `(` su 11.

### D. La giunzione — invariata

> Per ogni elenco prodotto si guarda il paragrafo immediatamente sopra e sotto.

Con il bersaglio in più della v1: la riga che introduce l'elenco non deve finire
inghiottita nella prima voce.

### E. L'emendamento a E-B — invariato e già implementato

I marcatori dichiarati escono dal confronto **da entrambi i lati**, sulla forma
del precedente della deidratazione (`Criterio_ParagrafoDaRiga_v1.md` §3).

## 4. Che cosa resta fuori

Come la v1: elenchi annidati, elenchi numerati, la riga introduttiva che non
diventa titolo, i titoli, la coppia etichetta-valore. Più, esplicito ora:

- **Gli elenchi su due colonne** dove l'ordine di lettura separa il glifo dal suo
  testo. Misurato su FW p.168, dichiarato al §2, non risolto.
- **DrM usa tre marcatori alternati** — `!`, `@`, `#`, uno per tier — e la regola
  li tratta come tre elenchi distinti invece che come tre livelli di uno. È
  l'annidamento, che resta fuori.
