# La dimensione serve? Criterio scritto PRIMA di eseguire

## La domanda
Il rilevamento usa la dimensione del carattere per due cose: tagliare il
documento in zone candidate, e trovare la riga-nome. Se lo schema (l'insieme di
etichette obbligatorie) e' affidabile, la dimensione serve ancora?

## L'esperimento
Si toglie **ogni** uso della dimensione dal rilevamento delle regioni:
- etichetta = primo span di una riga che ha almeno due stili diversi
  (nessun confronto di dimensione, nessuna nozione di "corpo");
- frequenza documento-wide -> etichette ricorrenti = schema;
- record = corsa massimale di righe vicine che portano etichette dello schema,
  nell'ordine di colonna.

Nessun livello, nessun delta, nessuna soglia in punti.

## Predizione registrata
La versione senza dimensione **trovera' il blocco dei campi ma non il record**:
- perdera' la riga-nome in cima, che non porta etichette;
- perdera' la coda in fondo (features, prosa), che non porta etichette dello
  schema ed e' indistinguibile dalla prosa circostante con le sole etichette.

Se questa predizione e' giusta, la dimensione non serve a **trovare** i record:
serve a sapere **dove finiscono**. Se e' sbagliata e la versione senza
dimensione recupera anche gli estremi, la dimensione va tolta dal metodo.

## Misura
Per ognuna delle 148 schede note: la regione trovata senza dimensione copre la
stessa estensione di quella trovata con la dimensione? Si contano le righe
mancanti in testa e in coda.
