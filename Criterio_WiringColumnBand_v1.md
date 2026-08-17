# Criterio di accettazione — wiring ridotto di `column_band`

Scritto **prima** dell'implementazione, come i quattro criteri della sessione
precedente. Il commit che introduce questo file non contiene wiring.

Nasce da una revisione indipendente che ha detto **«non procedere al wiring
nello scope attuale»** e ha indicato lo scope ridotto che segue. Non è una
riduzione per prudenza generica: ogni pezzo tolto è un pezzo che oggi nessun
livello a valle saprebbe leggere.

---

## 1. Cosa entra, e cosa resta fuori

**Entra**: `column_band` fra i producer montati dal job, e il consumer della
fetta verticale che usa i suoi candidati per ordinare.

**Restano fuori, ciascuno con la sua ragione:**

| escluso | perché |
| --- | --- |
| **le bande annidate** — si emette il **solo primo livello** | emetterle alla pari dei genitori le presenta come **alternative**, mentre sono vere a due livelli insieme. Senza una regola di Resolution che sappia dell'annidamento, un consumer ha due sole letture coerenti: duplicare il contenuto o perderne un livello. Entrambe violano «contenuto preservato». È una **cancellazione**, reversibile quando Resolution esisterà |
| la misura satellite `ColumnBandMeasurements` | serve a **misurare**, non a consumare: un assemblatore di reading order usa la geometria delle bande e l'assegnazione delle primitive, non `column_count`. Costruirla ora sarebbe un altro pezzo che nessuno legge |
| una regola di Resolution per `column_band` | è il blocco vero e non si chiude qui; se ne prende atto e si limita lo scope di conseguenza |

## 2. Il difetto noto che NON blocca, e dove va

Piè di pagina e numero di pagina finiscono dentro una banda e ne escono nel
posto sbagliato (Dag p.84: `Capitolo 1: Guida Aggiuntiva per i Giocatori` e `82`
emessi in mezzo al testo). **Non è un difetto di `column_band`**: sono elementi
**ripetuti**, e la loro rimozione appartiene alla **deduplicazione**, che
`AGENTS.MD` §Obiettivo prevede esplicitamente («sostituire immagini, sfondi ed
elementi ripetuti con note brevi»). Decisione dell'utente. Non blocca il wiring
e va registrato come lavoro dovuto, non come limite accettato.

## 3. Il criterio di accettazione, fissato prima

**Sul testo renderizzato, non sui candidati.** Un candidato ben formato non dice
niente sulla leggibilità: il validatore strutturale esclude output malformato,
non output sbagliato.

**Pagine: mai usate come ancore.** Le sette pagine su cui il producer è stato
verificato sono le stesse su cui il meccanismo è stato messo a punto. Il set di
questo giro si estrae con regola dichiarata qui e si guarda dopo:
**10 pagine uniformi da un pool non condizionato, seed 20260817**, escludendo
per costruzione DrW 97, Dag 164, Dag 84, Dag 24, Dag 25, Dag 36, DB 9, DB 13,
DB 27, DB 29, DB 31, DB 44, DB 50, DB 53, DB 99, Fab 2.

**W1 — nessun falso negativo su regione multicolonna reale.** Su nessuna pagina
del campione il testo di due colonne deve uscire concatenato riga per riga. È
l'errore non recuperabile: Resolution non può emettere un candidato mai
prodotto, e senza regola di Resolution non può nemmeno rifiutarne uno sbagliato.

**W2 — nessuna regressione contro la variante senza bande.** Il termine di
paragone è `page_lines.md`, mai `page.md`.

**W3 — l'arredo di pagina non conta.** Piè di pagina e numeri di pagina fuori
posto non fanno fallire W1 né W2: sono assegnati alla deduplicazione (§2). Si
contano e si scrivono.

## 4. Controllo negativo che può fallire

I due controlli esistenti — pagina vuota e colonna singola — non possono
fallire: sono controlli di sanità. Il controllo che discrimina discende dalla
tesi del meccanismo («separa la persistenza verticale, non la larghezza»):
**un canale bianco verticale persistente che NON è un gutter** — un blocco
centrato su pagina a colonna unica — **non deve produrre bande**. Va aggiunto ai
test prima del wiring.

## 5. Regressione documentata da tenere nel set

**Dag p.84** entra stabilmente nei test: è l'unica pagina del progetto con
un'aspettativa verificata a render (due colonne) **e** una risposta precedente
nota e sbagliata (`column_count=1` del meccanismo di Fase 1/2). È il caso di
regressione più economico che esista, ed era fuori dalla verifica del producer.

## 6. Cosa si sa già e non va spacciato per altro

- Il porting è verificato **bbox per bbox** su cinque pagine, non per conteggi:
  corrispondenza esatta su quattro, e su DB p.53 una banda di 4pt che il
  producer scarta perché non contiene primitive.
- Il «7 su 7 valide» del producer contava due pagine rese valide dal ritaglio
  introdotto perché fallivano. Non va citato come verifica.
- Nessun campione cieco dopo i cambi del 15-16 agosto 2026; il terzo invariante
  sull'ordine, che confronta con un riferimento umano, continua a non esistere.

## 7. Dopo

L'esito si scrive. **Nessun altro giro viene proposto dall'interno di questo**:
se W1 cade, si scrive cosa è caduto e su quale pagina, e ci si ferma.
