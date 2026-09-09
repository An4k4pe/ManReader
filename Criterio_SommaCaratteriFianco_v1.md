# La somma dei caratteri di fianco — criterio pre-registrato

Proposta dell'utente, 8 settembre 2026: in caso di sospetta tabella i caratteri
di fianco a un corridoio **non si contino riga per riga ma si sommino**, cosi'
che sei righe da un carattere superino la soglia di cinque. Piu' la richiesta di
provarla anche **globalmente**, non solo dentro le tabelle.

Diagnostica: nessuna modifica a `page_analysis_column_band.py`. Le varianti si
calcolano in uno script che ricompone la decisione sopra il profilo misurato dal
producer, cosi' il confronto e' fra regole e non fra implementazioni.

## Le varianti
- **V0, oggi**: si scarta se meno di **2 righe per lato** portano almeno 5
  caratteri (`wordy_minimum < 2`).
- **V1, somma globale**: si scarta se il lato piu' povero somma meno di 5
  caratteri su tutte le sue righe. Sostituisce V0 ovunque.
- **V2, somma solo in tabella**: V1 dove un `table_candidate` contiene il
  corridoio, V0 altrove.

V1 e' una pura **rilassatezza**: un corridoio che oggi passa ha almeno 2 righe da
5+ caratteri per lato, quindi somma almeno 10 e passa anche con V1. Nessuna
variante puo' togliere bande, solo aggiungerne. La domanda e' quante ne aggiunge
di sbagliate.

## La verita' di riferimento
I **quattordici corridoi** che l'utente ha giudicato a vista su quindici pagine
di DB:
- **nove devono formarsi** (colonne dei numeri di dado, dentro un
  `table_candidate`): IMPREVISTI MAGICI 60, FANTASMA 88, RAGNO GIGANTE 96,
  IMPREVISTI 102, TESORI 2 122, ORCO 111, ARMI IMPROVVISATE 120 (x 77-84 e
  x 96-98), TESORI 1 121 (x 77-84 e x 88-95);
- **cinque non devono formarsi** (rientro sospeso degli elenchi, x 74, fuori da
  ogni tabella): MAGO 20, I GOBLIN 115, SALA GRANDE 117 (due), TORRE 119.

## Predizioni registrate
- **W1** — V1 accetta tutti e nove i corridoi blu. Una colonna di dado ha da 6 a
  21 righe da 1-2 caratteri: somma sempre sopra 5.
- **W2** — V1 accetta anche **almeno uno** dei cinque rientri sospesi, e quindi
  introduce falsi positivi: il marcatore di elenco e' un carattere, e su sei
  righe fa sei. Predico **2 falsi positivi su 5** (TORRE con 6 fianchi, MAGO con
  5); i tre con 3-4 fianchi resterebbero sotto.
- **W3** — V2 e' corretta su **14 su 14**, perche' i rientri sospesi non stanno
  dentro nessun `table_candidate` e restano giudicati da V0.
- **W4** — l'effetto globale di V1 su DB non e' concentrato solo sulle pagine con
  tabelle: mi aspetto nuove bande anche altrove, ed e' la ragione per cui la
  variante globale va guardata prima di adottarla.

## Criterio di accettazione
Una variante si accetta se e' corretta su **tutti e quattordici** i corridoi
verificati. Se nessuna lo e', si riporta quale sbaglia dove e non si sceglie.
L'effetto globale (quante bande in piu' su tutto DB, dove) si riporta comunque,
anche per la variante che passa: una regola corretta sui casi verificati puo'
essere disastrosa sui casi non verificati, ed e' esattamente quello che questo
progetto ha gia' pagato piu' volte.

Nessun numero di questo giro modifica il producer: e' una misura, non una patch.

---

# V3, aggiunta dopo l'esito di V1 e PRIMA dei suoi dati

## Perche'
L'unico errore di V1 e' una **classe**, non un caso: la tabella FORESTA di
DB 121 e' un D6 **tagliato in due meta' affiancate da tre righe ciascuna**
(numeri `1 2 3` a sinistra, `4 5 6` a destra), quindi la colonna dei numeri
somma 3 caratteri e la soglia 5 la scarta per costruzione. Rilievo dell'utente:
«e' una tabella tagliata che continua nella colonna a fianco».

E la soglia 5 non ha una ragione: e' `min_flanking_chars`, nata per dire «una
riga con almeno cinque caratteri porta una parola» — non si va a capo dopo un
articolo. Sommare su piu' righe e' un'altra grandezza, e riusare la stessa
costante e' arbitrario.

I dati misurati dicono che i due gruppi non si distinguono per quanto sommano,
ma per **se sommano**: rientro sospeso 0, colonne di dado da 3 a 34.

## La variante
- **V3, lato non vuoto**: si scarta se un lato somma **zero** caratteri.
  Nessuna soglia: e' la distinzione fra «c'e' testo» e «non c'e'».
  Gli altri due criteri (`too_few_lines`, `too_short`) restano quelli del
  producer, ricalcolati come in V1.

## Predizioni registrate
- **X1** — V3 e' corretta su **14 su 14** della verita' di riferimento: accetta
  tutte e nove le colonne di dado (somme 3-34) e scarta tutti e cinque i rientri
  sospesi (somma 0).
- **X2** — V3 e' piu' permissiva di V1 e aggiunge bande anche fuori dalle
  tabelle. Predico su DB **piu' del doppio** delle nuove bande di V1 (V1 ne
  aggiunge 28), e una quota fuori tabella **superiore** a quella di V1 (1 su 28).
- **X3** — se X2 e' vera in modo marcato, «lato non vuoto» e' troppo debole come
  criterio unico e va detto, anche se sulla verita' di riferimento e' perfetta:
  quattordici corridoi giudicati a vista non autorizzano un criterio che tocca
  centinaia di pagine.

## Accettazione
Si riporta la ripartizione. Nessuna variante viene adottata qui: questa resta
diagnostica, e la modifica al producer e' una milestone sua.

---

# V4, aggiunta dopo l'ispezione delle pagine Apo e PRIMA dei suoi dati

## Il fatto che la impone
Le 33 pagine dove V3 apre bande fuori dalle tabelle su Apo sono state
**ispezionate**, non assunte: il fianco sinistro e' il carattere `h` nel font
`NelsonOrnaments`, cioe' il **punto elenco del manuale**. E' lo stesso rientro
sospeso che l'utente ha lasciato non marcato su DB; l'unica differenza e' che su
DB quelle righe risultano span **vuoti** (somma 0) e su Apo il marcatore e' un
carattere vero (somma 2-4).

Quindi V3 e' 14 su 14 sulla verita' di riferimento per un **accidente di
codifica** del manuale su cui quella verita' e' stata raccolta.

E le due classi si sovrappongono nei numeri:
    colonna D6 della FORESTA (da tenere)      somma 3
    punto elenco di Apo (da scartare)         somma 2-4
**Nessuna soglia sulla somma puo' separarle.** La somma da sola non basta, ed e'
il contrario di quello che avevo concluso ieri guardando solo DB.

## La variante
- **V4, somma non vuota solo in tabella**: dentro un `table_candidate` si scarta
  se un lato somma zero; fuori vale V0 invariato.

Rimette il cancello del `table_candidate` che avevo dichiarato inutile: la
distinzione che serve non e' nel profilo del corridoio, e' nel fatto che una
tabella copra quella regione. E' la relazione fra candidati di producer diversi
che `AGENTS.MD` colloca in Resolution o nel consumer.

## Predizioni registrate
- **Y1** — V4 e' corretta su **14 su 14**: la FORESTA sta dentro un
  `table_candidate` (verificato) e passa con somma 3; i cinque rientri sospesi di
  DB stanno fuori e restano giudicati da V0.
- **Y2** — su Apo V4 aggiunge solo le bande **dentro** le tabelle (13 nel conto
  0-100) e **zero** fuori: i 33 elenchi puntati non passano.
- **Y3** — su DB V4 aggiunge circa 31 bande, tutte in tabella, e zero fuori.

## Accettazione
Come sopra: si riporta, non si adotta. Ma se Y1 e Y2 reggono, V4 e' l'unica
delle quattro varianti corretta su tutto cio' che e' stato guardato a vista **e**
contenuta su un manuale diverso da quello da cui viene la verita'.
