# Criterio — le righe della scheda vanno a capo

**20 settembre 2026.** Rilievo dell'utente sulla resa consegnata: «in tutti la
formattazione e i ritorni a capo sono un po' carenti, con le varie etichette
separate da | e la riga successiva unita alla prima senza |», e «sirena non e'
completa pero', manca la seconda caratteristica».

## 1. I due difetti sono lo stesso difetto

Su Dag idx 230 (stampata 229), resa `output/resa/posizione`:

```
**Diffi  coltà:** 14 | **Soglie:** 9/18 | **PF:** 5 | **Stress:** 3 **ATT:** +2 | **Mascella Disarticolata:** Mischia | 2d6+3 fi s
```

Due righe della scheda saldate in una. E:

```
**CARATTERISTICHE *Ascoltatore Avvinto - Passiva:*** ... danni invece dei danni base. ***Canto** Incantato**re - Azione:***** Spendete una Paura** per cantare
```

L'intestazione della **seconda** caratteristica incollata in coda al paragrafo
della prima: la caratteristica non manca, ha perso il suo a capo. Il resto del
suo testo sta nel paragrafo dopo, preceduto da `MINOTAURO DEMOLITORE` — e quello
e' un difetto d'ordine di lettura a due colonne, non di questo criterio.

La causa e' una sola: `breaks_paragraph` rompe dove cambia il **blocco** della
sorgente, e le righe di una scheda stanno nello stesso blocco. La regola e'
giusta per la prosa — l'ha misurata `Criterio_RotturaParagrafo_v2.md` — ed e'
sbagliata dentro una scheda, dove ogni riga e' un record e non un pezzo di frase.

## 2. La regola

Dentro un'area di scheda, **una riga che si apre con un'etichetta apre un
paragrafo**.

«Si apre con un'etichetta» vuol dire che la prima etichetta della riga comincia
al bordo sinistro della riga: scostamento zero nella stessa unita' —  larghezze
di carattere — che `Criterio_PosizioneRelativaDeiCampi_v1.md` usa per i profili.
Nessuna soglia nuova, nessun conteggio nuovo: le etichette e le loro posizioni
sono gia' in `LineFacts`.

Le righe che **non** si aprono con un'etichetta continuano a comportarsi come
prosa: `Armi: i giganti portano spesso grandi armi. Se un gigante perde la sua
arma...` va a capo nella sorgente e resta un paragrafo solo, perche' la riga
seguente non apre un'etichetta.

Il calcolo resta fuori da `ir2_builder`, come tutto cio' che riguarda le schede:
`StatBlockAreaInput` porta gia' le primitive dell'area, e prende un campo in piu'
con le primitive che aprono un record. Il costruttore sa solo che li' si rompe.

## 3. Che cosa deve succedere perche' passi

Resa di DB, Apo e Dag con `--schede-campi`, confrontata con
`output/resa/posizione`.

**A. I due difetti citati spariscono.** Su Dag idx 230 la riga `Diffi coltà: ...`
e la riga `ATT: ...` sono due paragrafi, e `Canto Incantatore - Azione:` apre il
suo.

**B. Le tabelle non si muovono.** Nessuna tabella sparita, ridotta, cresciuta o
nuova rispetto a `output/resa/posizione` su nessuno dei tre manuali: questo
criterio tocca i paragrafi, non le tabelle.

**C. Nessun paragrafo di prosa si spezza.** Sulle cinque pagine gia' giudicate —
DB idx 87, 90, 97, Dag idx 230, 359 — nessuna frase che prima era intera esce
tagliata in due.

**D. La barra E-B** resta 9 su 10 con la sola Fab idx 126 diversa, e i test
restano verdi.

**Veto.** Se cade C, il segnale «si apre con un'etichetta» prende righe di prosa
e va ristretto. Se cade B, il campo nuovo sta cambiando cio' che la tabella
consuma, che non e' quello che fa.

---

## 5. Emendamento del §2, dopo la caduta del veto C

**Misurato prima dell'emendamento**, resa `output/resa/acapo` contro
`output/resa/posizione`: le tabelle non si muovono (veto B regge, 70 uguali su
DB), ma **il veto C cade**. Su DB idx 69 (stampata 68) la regola taglia una
frase in due:

```
**Ondata:** l'ondina può lanciare **ONDATA** allo stesso livello di potere dell'incantesimo che
l'ha evocata, usando i **PV** del suo creatore.
```

**Perche' e' caduto.** `field_labels` non rileva etichette: rileva **alternanze
di stile** (`label_spans`). Su una riga di continuazione che contiene una parola
in grassetto, tutto il testo che la precede diventa «etichetta», e comincia al
bordo sinistro. Sulla pagina misurata: `l’haevocata,usandoi`, `pv` in `PV del suo
creatore.`, `gettodifuoco` in `GETTO DI FUOCO allo stesso livello di potere`.

La regola delle combinazioni non ne soffriva perche' e' protetta dalla
**ripetizione**: un'etichetta inventata cosi' non si ripete tre volte. La regola
dei record non aveva nessuna protezione.

**L'emendamento.** «Si apre con un'etichetta» diventa: **si apre con
un'etichetta che si dichiara tale**, cioe' il cui testo finisce con i due punti.
Non e' una nozione nuova: `normalised_label` toglie gia' «i due punti finali»
per confrontare le etichette, quindi il modulo sa gia' che un campo si scrive
`Etichetta:`. Qui quel fatto smette di essere solo normalizzazione e diventa il
requisito.

**Perche' questo emendamento non e' un salvataggio.** Regge senza sapere come
finisce la misura: un rilevatore di alternanze di stile chiamato «etichette»
produce etichette su ogni riga andata a capo che contenga una parola in
grassetto, e una regola che si appoggia alla **prima** di quelle sta guardando
«la riga comincia con uno stile diverso», che non e' cio' che il §2 dice di
guardare. Il difetto sta nella formulazione, non nel risultato.

Le tre righe che il veto C ha mostrato tagliate sono tutte senza due punti; le
righe di record vere — `Movimento:`, `Armatura:`, `Armi:`, `Ondata:`,
`Resistenza:`, `Immunità:`, `Getto di Fuoco:` — li hanno tutte.

I veti del §3 restano quelli, e la misura si rifa' da capo.

### 5.1 Correzione dell'emendamento, prima di misurarlo

«Si apre con un'etichetta che si dichiara tale» era stato scritto come **la
prima** etichetta finisce con i due punti. Sbagliato, e si vede su Dag idx 230
riga 13:

```
span: 'Canto ' (BoldItalic) | 'Incantato' (Light) | 're - Azione:' (BoldItalic) | ' ' | 'Spendete una Paura' (Bold) | ' per cantare '
```

Un intoppo di font spezza `Canto Incantatore - Azione:` in tre pezzi, e i due
punti finiscono nel terzo. Chiedere che sia il **primo** span a portarli
significa guardare la segmentazione degli span, non il campo — ed e' proprio la
riga che il rilievo dell'utente indicava («manca la seconda caratteristica»).

La forma che vale, e che la misura giudichera': **la prima etichetta comincia al
bordo sinistro della riga e sulla riga c'e' almeno un'etichetta che finisce con
i due punti.** Sulle due pagine di controllo prende tutte le righe di record
vere — `Movimento:`, `Armatura:`, `Armi:`, `Ondata:`, `Resistenza:`,
`Immunità:`, `Getto di Fuoco:`, `Motivazioni e Tattiche:`, `Difficoltà:`,
`ATT:`, `Esperienza:`, `Ascoltatore Avvinto - Passiva:`,
`Canto Incantatore - Azione:` — e nessuna delle tre righe di prosa che il veto C
aveva mostrato tagliate.
