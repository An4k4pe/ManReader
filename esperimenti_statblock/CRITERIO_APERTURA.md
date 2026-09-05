# Formalizzazione della soglia di apertura — criterio scritto PRIMA di eseguire

## Il problema
`apertura = riga con corpo > corpo_testo + delta` ha un `delta` in punti che
regge solo fra +1,0 e +2,0 su Daggerheart, e il valore giusto dipende dal salto
fra la dimensione dei sottotitoli e quella dei nomi di scheda. Non trasferisce.

## Il principio, indipendente dal manuale
La tipografia non usa un continuo: usa una **scala discreta di livelli**. Il
titolo di un record e' uno di quei livelli, e si distingue dagli altri livelli
alti non per quanto e' grande, ma per una proprieta' funzionale: **e' il livello
al quale il documento risulta piu' regolarmente strutturato**, cioe' quello le
cui occorrenze partizionano il testo in regioni che condividono uno schema.

Un livello di titolo di capitolo produce poche regioni senza schema condiviso.
Un livello di sottotitolo interno produce regioni il cui contenuto varia da
istanza a istanza. Il livello del nome-record produce molte regioni con lo
stesso insieme di etichette obbligatorie.

## La regola, che sostituisce la costante
Non si sceglie una soglia: si **cerca**. Per ogni livello di dimensione presente
nel documento, si esegue l'induzione completa usando quel livello come apertura,
e si tiene il livello che **spiega piu' regioni con schemi discriminanti**
(schemi che superano gia' il test di specificita' derivato: l'insieme di zone
che soddisfa gli obbligatori non supera 3x il gruppo che li ha indotti).

Il `delta` in punti sparisce. Restano solo quantita' derivate dal documento.

## Predizioni registrate PRIMA di eseguire
- **P1** — la ricerca sceglie il livello 12,0 (i nomi), non 10,0 (le
  intestazioni `FEATURES`) ne' 17,0 (i titoli di sezione) ne' il corpo.
- **P2** — con il livello scelto dalla ricerca, il risultato resta 148/148 con
  0 falsi positivi, senza toccare nessun'altra costante.
- **P3** — i livelli sbagliati NON produrranno semplicemente meno schede:
  produrranno schemi poco discriminanti, ed e' per questo che perdono.

## Falsificazione
- Se la ricerca sceglie un livello diverso da 12,0, la formalizzazione e'
  sbagliata e lo scrivo, senza aggiustare il criterio di selezione.
- Se serve un solo ritocco al criterio di selezione dopo aver visto l'esito,
  la formalizzazione va considerata **tarata su questo manuale** e il secondo
  manuale non puo' piu' validarla.

## Esecuzione
Una volta sola. L'esito si scrive comunque.
