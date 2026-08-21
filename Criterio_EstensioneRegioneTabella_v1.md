# Criterio — l'estensione verticale della regione tabella

Registrato **prima** dell'implementazione e prima della misura. Da committare in
un commit **senza codice** (`AGENTS.MD` §15).

Esiste perché in questa sessione **quattro ipotesi di seguito** sull'estensione
verticale sono state provate e ritirate decidendo a posteriori sui numeri. È la
firma che `State.md` registra per `--min-flanking-chars` (cinque valori, tre
correzioni, conclusione: «il criterio non discrimina la classe giusta»). Questo
giro si scarica per iscritto o non si fa.

## 1. La domanda, una sola

> Dato un gruppo di corridoi verticali che descrivono le colonne di una tabella,
> **dove comincia e dove finisce la tabella**?

Non «dove sono le colonne», che è risolto: su DB pagina 76 i corridoi danno gli
otto confini giusti, verificati contro i tracciamenti dell'utente.

## 2. L'ipotesi da provare, nella formulazione dell'utente

> Identificati i gutter, si estendono banda per banda finché **nessuno di essi
> interseca testo** e **almeno uno ha testo a lato**.

Le due clausole sono congiunte e vanno implementate come tali. **Una versione
precedente aveva sbagliato la prima** — chiedeva che *almeno un* gutter fosse
libero invece di *tutti* — e con quella il piè di pagina di DB pagina 76 non
fermava la corsa. Correzione dell'utente.

«A lato» è definito qui e non dopo: c'è testo in almeno una delle due colonne che
quel gutter separa, dove le colonne sono delimitate dai gutter adiacenti del
gruppo o dal bordo dell'inchiostro di pagina.

## 3. Il campione, e il suo limite dichiarato subito

**Le 17 tabelle fornite dall'utente sono pagine di SVILUPPO**, non un campione
cieco: l'ipotesi del §2 è stata formulata guardandole, e quattro ipotesi
precedenti sono state falsificate su di esse. Un esito positivo qui **non è una
verifica**, è una condizione necessaria.

Indici 0-based: Dag 117/133/135, DB 61/75/122, DrM 32/35, DrW 32/239/247,
Lan 18/40/51, BoB 238, Wil 73/77.

**La verifica richiede un secondo insieme**, che l'utente fornisce e che Chat A
non vede prima della misura. Senza quello l'esito resta «necessario, non
sufficiente», e va citato con quelle parole.

## 4. La regola di pass/fail — **una sola**, e automatica

Il difetto misurato è che la regione si allunga oltre la tabella e le colonne
ricalcolate dentro **collassano**: su DB pagina 76 i corridoi trovano 8 gutter,
la regione arriva a `y66,9-774,5` (tutta la pagina) e le colonne scendono a 5.

> **Regge** se, su tutte e 17, il numero di colonne prodotte dentro la regione è
> **almeno pari** al numero di gutter del gruppo che l'ha generata, più uno.
>
> **Cade** se anche una sola regione ne perde.

È una coerenza interna, quindi calcolabile senza giudizio umano, e **falsificabile
oggi**: allo stato attuale DB pagina 76 la viola (5 contro 9).

## 5. L'errore squalificante

> Nessuna delle 17 deve perdere colonne o righe rispetto allo stato migliore
> noto, registrato qui prima della modifica:

| pagina | colonne × righe |
| --- | --- |
| Lan pag19 | 7 × 13 |
| Lan pag52 | 3 × 10 **e** 3 × 10 |
| BoB pag239 | 2 × 7 |
| DB pag62 | 2 × 20 |
| Wil pag78 | 4 × 6 |
| DrW pag240 | 12 × 22 |
| DrW pag248 | 4 × 44 |
| Wil pag74 | 2 × 17 |
| DrW pag33 | 4 × 53 |
| DB pag76 | 5 × 34 |
| Dag pag136 | 4 × 22 |

Una sola regressione ferma il giro. Stessa forma del §3/§5 di
`Criterio_TabellaInIR2_v1.md`.

**Serve perché è esattamente così che sono cadute le quattro ipotesi
precedenti**: ciascuna aggiustava la pagina che aveva in mente e ne rompeva da
sei a nove altre, e me ne sono accorto solo eseguendo.

## 6. Limiti dichiarati prima

**Non misura le colonne**, che sono già a posto, né le righe, né la resa. Se il
§4 regge e l'uscita resta illeggibile, l'esito è comunque «regge»: misura una cosa
sola.

**Non misura la copertura**: le 17 sono tabelle per costruzione. Il tasso di falsi
positivi — 31 proposte su 35 erano prosa, sul campione cieco delle 60 — resta una
domanda aperta e separata.

**Il conteggio di gutter del §4 viene dallo stesso meccanismo che produce la
regione**, quindi la coerenza interna può essere soddisfatta rendendo il gruppo
più povero invece che la regione più corta. È la via di aggiramento, ed è la
ragione per cui il §5 elenca i numeri di adesso: senza quelli, il §4 da solo si
può passare peggiorando.

## 7. Che cosa NON decide

Non decide se il confine verticale sia ricavabile dai soli corridoi. Se il §2
cade, l'ipotesi successiva — un **secondo segnale** indipendente dai gutter, per
esempio i producer visuali che vedono il fregio o il piede di pagina — richiede un
criterio proprio, non un emendamento di questo.
