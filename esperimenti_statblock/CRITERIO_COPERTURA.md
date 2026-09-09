# Correzione 4 — la misura di copertura. Criterio scritto PRIMA di eseguire

Riprende `PASSAGGIO_DI_CONSEGNE.md` §5.4 e `VERDETTO_MANUALE2.md` §Conseguenze 1.
Autorizzata dall'utente dopo il giro delle correzioni 2 e 3.

## Il guasto che questa misura esiste per impedire
Sul manuale 2 il metodo ha riportato 16 gruppi e 34 etichette di schema, tutte
nomi di abilita' di schede personaggio, **senza segnalare** di aver mancato un
template di 4 schede mostro. Il guasto peggiore e' quello silenzioso: serve un
numero che, guardato da solo, avrebbe fatto scattare l'allarme.

## Cosa NON e' questa misura
Non e' la correzione 1. La misura **riporta**, non cambia cio' che il
rilevatore emette: nessuna soglia si abbassa, nessun template raro viene
promosso. Se il residuo mostra una firma rara che ricorre, quello e' un dato per
la correzione 1, non una decisione presa qui.

## Definizioni, e perche' non introducono soglie nuove
- **Riga con etichette**: una riga da cui `etichette()` (o `etichetta()` per il
  rilevatore congelato) estrae almeno una coppia. Definizione gia' nel metodo.
- **Riga spiegata**: porta almeno un'etichetta dello schema indotto.
- **Riga residua**: porta etichette, e **nessuna** e' nello schema. Ha forma di
  campo e nessun template la spiega.
- **Corsa residua**: righe residue consecutive, con la stessa tolleranza di
  stacco (2) che `nuclei_di` usa per i nuclei. Stesso meccanismo, popolazione
  complementare: nessuna costante nuova.
- **Firma rara**: l'insieme delle etichette di una corsa residua. Le corse si
  raggruppano con lo stesso Jaccard 0,4 del metodo.

Il residuo si definisce sulle **etichette**, non sull'appartenenza a un record
emesso: e' esattamente cosi' che il fallimento e' stato silenzioso, perche' le
righe delle schede mostro erano finite dentro i record di un altro gruppo.

## Cosa riporta
1. **C1, descrittiva**: frazione dei caratteri non-spazio dentro un record
   emesso, e la stessa frazione per pagina. Nessun criterio di accettazione
   attaccato: e' un numero che dice quanto il metodo ha rivendicato, non quanto
   ha ragione.
2. **C2, l'allarme**: le firme rare che ricorrono su **3 o piu' pagine
   distinte**, ordinate per numero di pagine, con le pagine dove stanno.
3. **C3, dove si concentra**: le pagine con piu' corse residue.

## Predizioni registrate
- **A1 — il retro-test, ed e' il criterio vero.** La misura viene eseguita
  anche sull'output del rilevatore **congelato** `pila.py` (importato, non
  modificato) sul manuale 2, cioe' sul giro che ha fallito in silenzio. In
  quell'elenco C2 deve comparire una firma rara che contiene `Ferocia`,
  ricorrente su 4 pagine. **Se non compare, la misura non serve a niente**: e'
  nata per rendere rumoroso quel fallimento.
- **A1b — leggibilita'.** L'elenco C2 dev'essere corto abbastanza da guardarlo:
  fisso **30 voci** su un manuale di 47 pagine come limite prima di guardare. Se
  e' molto piu' lungo, la misura segnala tutto e quindi niente, e il criterio di
  ricorrenza per pagina va ripensato — non ritoccato dopo aver visto l'elenco.
- **A2 — deve discriminare.** Sul manuale 1 le pagine con piu' corse residue
  (C3) **non** devono essere le pagine dove vivono i 129 nuclei del gruppo
  avversari, cioe' dove il metodo riconosce 148 schede su 148. Le pagine si
  prendono dal metodo, non da un intervallo scritto a mano. Se il residuo e'
  massimo proprio li', la misura non distingue spiegato da non spiegato.
- **A3 — previsione sul manuale 2 corretto**: eseguita su `pila2.py`, dove il
  template `{Armatura, Movimento, PF}` si e' formato, la firma con `Ferocia`
  **resta** nel residuo, perche' `Ferocia` e `Taglia` hanno 4 occorrenze e
  restano sotto `MIN_RICORRENZA`. Se sparisse, vorrebbe dire che il residuo si
  svuota quando un template vicino si forma, e la misura misurerebbe la
  fortuna.

## Criterio di accettazione
La misura si accetta se **A1 e A2 reggono**. A1b e A3 si riportano comunque; se
A1b cade la misura si accetta lo stesso ma va dichiarata inutilizzabile a mano,
e la voce diventa lavoro aperto.

Nessun numero di questo giro vale come validazione: manuali 1 e 2 sono banco di
sviluppo. Il terzo manuale (Draw Steel: Monsters) resta sigillato.
