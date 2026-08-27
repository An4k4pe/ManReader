# Criterio — l'elenco numerato, e un giudizio esaustivo invece di un campione

**Scritto prima di implementarlo.**

## 0. Che cosa deve chiudere

Su FW p.168 sette voci escono schiacciate in un paragrafo solo:

```
1.	 Dai un **nome** all'Agente, e descrivilo. 2.	 Se ha un **Cast,** elenca tutti.
3.	 Scegli un **Tipo** e trascrivi il suo **Impulso**. …
```

`Criterio_Elenchi_v2.md` §4 li dichiarava fuori scope, con la ragione giusta: la
cifra è alfanumerica e **cambia a ogni voce**, quindi il discriminante «dove vive
il carattere» non la vede. Serve un'altra misura, ed è questa.

Rilievo dell'utente sulla resa di tre pagine, 27 agosto 2026.

## 1. Il segnale, che è più forte di tutti quelli usati finora

> Una riga apre una voce numerata se comincia con **un intero di una o due
> cifre**, un separatore (`.`, `)`, `]`) e uno spazio.
>
> Un **elenco numerato** è una corsa di due o più voci i cui interi sono
> **consecutivi** — `n`, `n+1`, `n+2` — che stanno nello stesso blocco o in
> blocchi **consecutivi della stessa pagina**.

**Gli interi consecutivi non sono una soglia**: sono auto-evidenti. `1, 2, 3` non
capita per caso, e non c'è nulla da tarare. È il segnale più forte di questo
filone — più della maggioranza a inizio riga, più della firma di blocco.

**Perché anche il vincolo di blocco e di pagina**, e viene dalla misura, non dal
gusto. Sui 16 manuali le righe che aprono con un numero sono **36 in tutto**, e
la maggior parte **non è un elenco**:

| manuale | che cosa sono davvero |
| --- | --- |
| **FW** | `1.`–`7.`, **tutte nel blocco `b0003`** — l'unico elenco numerato vero |
| **DIE** | `8. BESTIARIO` ripetuto su **9 pagine**: è una testatina corrente |
| **DIE** | `1. ASPETTO`, `2. …`, `3. ECHI` in blocchi `b0005`, `b0009`, `b0012` — titoli di sezione, blocchi non consecutivi |
| **Vil** | `1.`–`4.` sparsi su **pagine diverse** — titoli di sezione numerati |
| BiD, DB, Lan, SV | 1-4 righe ciascuno, da guardare |

Senza il vincolo, `8. BESTIARIO` e i titoli di DIE e Vil diventerebbero voci
d'elenco. Con il vincolo cadono da soli: la testatina ripete **lo stesso** numero,
i titoli stanno in blocchi lontani o su pagine diverse.

## 2. Che cosa succede al numero

> Il numero **esce dalla resa** e la voce diventa `1. `, cioè un elenco ordinato
> Markdown. Il nodo conserva il testo intero, come per i puntati.

Il numero **si rinumera da 1** nella resa? **No.** Si tiene quello del manuale: se
un elenco continua da una pagina precedente e comincia da `4.`, riscriverlo `1.`
direbbe una cosa falsa. Markdown accetta il numero di partenza.

## 3. Il giudizio: **esaustivo, non a campione**

La popolazione è **36 righe su tutto il corpus**. Si guardano **tutte**.

> Un campione qui sarebbe più debole, non più economico: con 36 casi il
> campionamento introdurrebbe un errore che non c'è motivo di accettare, e
> lascerebbe fuori proprio i casi rari che decidono.

Si producono due elenchi, e li si guarda entrambi:

- **le righe che la regola riconosce** come voci numerate;
- **le righe che apre con un numero e che la regola NON riconosce**, con il motivo
  per cui le ha scartate.

Il secondo è la parte che un campione non avrebbe: è lì che si vede se la regola
manca qualcosa.

## 4. Pass/fail

### A. Veto — cade a una sola riga, in entrambe le direzioni

> Cade se **una sola** riga riconosciuta non è una voce d'elenco numerato, o se
> **una sola** riga scartata lo era.

Zero, e stavolta senza la riserva statistica delle volte precedenti: non è un
campione, sono tutti i casi. Un veto esaustivo che regge dice davvero che la
regola non sbaglia su questo corpus.

### B. La giunzione

> Per ogni elenco prodotto si guarda il paragrafo immediatamente sopra e sotto.

`scripts/check_furniture_junction.py --elenchi`.

### C. Regressione

> I quattro elenchi puntati giudicati veri devono restare elenchi, e le scale di
> DrM devono restare scale.

`scripts/check_list_regression.py`. **Nota**: questa barra **è già caduta** per la
regola dei puntati (`Esito_ScalaDiValori_v1.md` §3), e qui serve solo a
verificare che il numerato non peggiori il conto.

### Se cade

- **A**, verso «riconosciuta e non lo era»: il vincolo di blocco/pagina è troppo
  largo. Non si stringe a occhio — si riporta quale caso l'ha rotto.
- **A**, verso «scartata e lo era»: la regola è troppo stretta, e si riporta
  quanto manca senza allargarla nello stesso giro.

## 5. Che cosa resta fuori

- **Gli elenchi con lettere** (`a)`, `b)`), non misurati.
- **L'annidamento**, che è il debito aperto più grosso di questo filone e che
  costa già due elenchi veri.
- **Le testatine correnti in cima**, che il ramo 2 dell'arredo lascia per scelta
  dichiarata: `8. BESTIARIO` di DIE resterà nel corpo, e questo criterio si limita
  a non promuoverla a voce d'elenco.
