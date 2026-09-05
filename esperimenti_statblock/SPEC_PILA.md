# Specifica della «pila di testa» — scritta PRIMA di implementare, e congelata

## Cosa sostituisce
La soglia di apertura in punti (`corpo + delta`) e la ricerca sul livello
tipografico. Entrambe fallite: la prima e' document-dipendente, la seconda ha
scelto il livello del corpo e ha richiesto due toppe post-hoc.

## Il principio
Le etichette di schema localizzano i record senza alcuna dimensione
(misurato: 148/148). Cio' che manca e' la **testa**. La testa non e' una riga
singola: e' una **pila di strati**, ciascuno uno stile che compare a una
distanza costante prima della corsa di campi. Su Daggerheart si vede come nome
a 3 righe, tier a 2, descrizione a 1. Il record comincia allo strato **piu'
esterno**, non al piu' vicino: e' l'errore che ha falsificato il tentativo
precedente.

## L'algoritmo, definitivo
1. **Nuclei**: corse di righe che portano etichette ricorrenti, nell'ordine di
   colonna. Nessuna dimensione.
2. **Gruppi**: i nuclei si raggruppano per somiglianza dell'insieme di
   etichette (Jaccard). Le statistiche di testa si calcolano **dentro il
   gruppo**, non globalmente: e' la cura della fragilita' gia' misurata, per
   cui un template poco numeroso veniva cancellato da soglie globali.
3. **Strati**: per ogni gruppo e per ogni distanza d = 1, 2, 3, ... si guarda
   se esiste uno stile presente a distanza d prima di almeno **META'** dei
   nuclei del gruppo. Si cammina all'indietro e ci si ferma alla **prima
   distanza senza strato consistente**. La profondita' della testa e' l'ultima
   distanza consistente.
4. **Estensione**: il record parte a `inizio_nucleo - profondita'` e finisce
   subito prima della testa del record successivo nella stessa colonna.

## Le costanti, e perche' quel valore
- **meta' (0,5)**: e' la maggioranza, scelta per una ragione indipendente
  dall'esito, non perche' massimizza un punteggio.
- **profondita' massima esplorata (8)**: e' un limite di ricerca, non una
  soglia che modella la risposta; la fermata la decide la consistenza.
- **Jaccard 0,4**: gia' misurato con pianoro 0,2-0,5 nel giro di sensibilita'.

## Regola di condotta, vincolante
Su Daggerheart questa implementazione e' **sviluppo, non validazione**: il
manuale su cui un metodo e' stato progettato non lo puo' convalidare. Sono
ammesse solo correzioni di **difetto** (cose sbagliate a prescindere
dall'esito). **Non** e' ammesso spostare una soglia per migliorare il numero.
Ogni modifica dopo la prima esecuzione va elencata qui sotto con la sua ragione.

Poi si congela, e il secondo manuale si esegue **senza toccare nulla**.

## Cosa misurera' il secondo manuale
- la profondita' di testa che il metodo deduce da solo;
- quante schede localizza e con quale estensione;
- se perde in silenzio un template poco numeroso.

## Modifiche fatte dopo la prima esecuzione

Tre, tutte correzioni di difetto (cose sbagliate a prescindere dall'esito).
Nessuna soglia e' stata spostata per migliorare un numero.

1. **Uno strato deve essere specifico, non solo presente.** La specifica diceva
   «uno stile presente a distanza d prima della maggioranza dei nuclei». Lo
   stile di corpo sta prima di quasi ogni riga, quindi soddisfaceva sempre la
   condizione e la camminata all'indietro non si fermava mai (profondita' 8 =
   il limite di ricerca, per tutti i gruppi). Aggiunta la condizione di
   **lift**: lo stile dev'essere almeno 2x piu' frequente in quella posizione
   che su una riga qualunque. E' lo stesso criterio di specificita' gia'
   derivato per gli schemi.

2. **Il lift si misura sulla regione, non sul documento.** Con la base globale
   lo stile di corpo delle pagine-schede (8pt) risultava raro nel documento
   (dove il corpo e' 9pt) e otteneva lift 5x: la camminata continuava a non
   fermarsi. La base va calcolata sulle pagine dove il gruppo vive. E' la terza
   volta in questo lavoro che una statistica globale sbaglia dove serviva
   quella locale, ed e' ormai una regola del metodo: **ogni statistica si
   calcola sulla popolazione della regione, mai sul documento.**

3. **La soglia di ricorrenza e' legata alla dimensione minima di gruppo.** Era
   un 20 scelto a mano, e cadeva per sfortuna appena sopra i 19 ambienti,
   cancellandone la testa. Non l'ho abbassata guardando il risultato: l'ho
   legata a una ragione interna — un'etichetta che ricorre meno volte della
   dimensione minima di un gruppo non puo' caratterizzare nessun gruppo
   ammissibile — quindi `MIN_RICORRENZA = MIN_GRUPPO`. Sweep riportato: la
   localizzazione da 148/148 per ogni valore fra 3 e 30, quindi la costante non
   tocca il rilevamento, solo le teste dei gruppi piccoli.

## Stato su Daggerheart alla chiusura (sviluppo, NON validazione)
- avversari: 129 nuclei, profondita' di testa **3**, nome a 3 righe, lift 13,1x
- ambienti: 19 nuclei, profondita' di testa **4**, nome a 4 righe, lift 24,0x
- 148 record su 148 soddisfano la verita' testuale
- 25 gruppi con >= 5 nuclei; molti sono strutture ripetute reali (tabelle armi,
  carte dominio) con profondita' 0
- **difetto residuo non corretto**: un gruppo (carte dominio) raggiunge la
  profondita' massima esplorata (8), cioe' per esso la camminata non si ferma.

## CONGELATO
Da qui in avanti il file `pila.py` non si tocca. Il secondo manuale si esegue
con `python3 pila.py <file.pdf> [--verita REGEX]` e nessuna modifica.
