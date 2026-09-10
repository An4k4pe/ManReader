# Compito aperto — le schede rare o uniche

**Registrato su richiesta dell'utente. Non iniziato, e da non iniziare finche'
il punto corrente non e' chiuso** (validazione della pila di testa su un
secondo manuale).

## L'enunciato
Una volta che il metodo riconosce i template **frequenti**, resta da trovare il
modo di **etichettare e rendere in Markdown anche le schede rare o singole**.

## Perche' non e' una questione di soglia
Il principio su cui poggia tutto il metodo corrente e' che **la frequenza
separa lo schema dal contenuto**: `Difficulty` compare 148 volte ed e' schema,
`Daggers` compare poche volte ed e' contenuto. Una scheda che compare **una
volta sola** non ha ricorrenza, quindi per costruzione e' invisibile a questo
principio. Non e' un parametro da abbassare: e' il limite del principio.
Abbassare le soglie non fa comparire la scheda unica, fa comparire rumore.

## La distinzione che va fatta prima di progettare
Due casi diversi, che oggi vengono confusi sotto «rara»:

1. **Rara ma dello stesso template** — un avversario unico che usa comunque i
   campi del template frequente (`Difficulty`, `HP`, `ATK`...). Questo caso
   **e' gia' risolto in linea di principio**: lo schema indotto dai 129 lo
   classifica, perche' la classificazione guarda gli obbligatori, non la
   frequenza dell'istanza. Va verificato, non progettato.
2. **Unica nel formato** — una scheda con una struttura che non compare altrove
   nel manuale. Qui non c'e' niente da indurre, ed e' il caso vero.

Il primo passo del compito e' **misurare quanti sono i casi del tipo 2** su
manuali reali. Se sono pochi, il costo di trattarli cambia natura.

## Direzioni candidate, nessuna verificata
- **Trasferimento fra manuali**: uno schema indotto su un manuale dello stesso
  sistema classifica le schede di un altro. Sposta il problema, non lo risolve
  per un sistema visto una volta sola.
- **Il modello locale, ed e' qui che guadagna il suo posto.** Una regione unica
  non si puo' indurre, ma si puo' far etichettare. E' l'unico punto della
  catena in cui un LLM fa qualcosa che il resto non sa fare. Vale il contratto
  gia' provato: il modello restituisce ruoli e indici, mai testo, e
  l'assemblaggio resta verbatim.
- **Regola di non-perdita, indipendente da tutto il resto**: una regione che ha
  forma di record ma non corrisponde a nessuno schema **non va scartata**. Va
  emessa come testo grezzo con una nota che dichiara «struttura non
  riconosciuta», perche' una scheda persa in silenzio e' il guasto che il
  progetto vieta. Questa parte si puo' fare senza aspettare nient'altro.

## Resa in Markdown
Distinta dal riconoscimento e non ancora affrontata per nessun caso, frequente
o raro: la scheda va estratta come asset, referenziata da una nota, e
rirenderizzata inline in forma leggibile. Per una scheda non riconosciuta la
resa e' il testo verbatim con la nota; per una riconosciuta e' la struttura a
campi. Il formato YAML gia' discusso e' l'asset, non il prodotto per il
lettore.

## Stato
Non iniziato. Precondizione: chiusura della validazione della pila di testa.
