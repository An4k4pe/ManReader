# Esito — la posizione relativa dei campi

Misura di `Criterio_PosizioneRelativaDeiCampi_v1.md`, 20 settembre 2026.
Rese confrontate: `output/resa/riparo` (base), `output/resa/unione` (il
meccanismo senza il requisito posizionale), `output/resa/posizione` (con).

## 1. Il criterio passa

| condizione | esito |
| --- | --- |
| **A** il difetto di DB idx 123 sparisce | **sì** — 173 → 183 primitive rispetto a `unione`, cioè la tabella torna quella di `riparo` |
| **B** le cinque buone restano | **sì** — DB idx 87, 90, 97 ridotte, Dag idx 230 sparita, idx 359 ridotta, identiche a `unione` |
| **C** nessuna tabella nuova o cresciuta rispetto alla base | **sì** — 0 su tutti e tre |
| **D** Apo intatto | **sì** — 16 tabelle uguali |
| **E** barra E-B e test | **sì** — barra 9 su 10, l'unica diversa è Fab idx 126, quella già a verbale; test verdi |

Conteggio delle tabelle, `riparo -> posizione`:

```
DB:  uguali 67  ridotte 3  SPARITE 0  CRESCIUTE 0  nuove 0
Apo: uguali 16  ridotte 0  SPARITE 0  CRESCIUTE 0  nuove 0
Dag: uguali 62  ridotte 1  SPARITE 1  CRESCIUTE 0  nuove 0
```

Combinazioni ammesse: DB 4 → 3, Apo 1 → 1, Dag 24 → 22.

## 2. Quello che la misura ha detto e che non mi aspettavo

**Su Dag il requisito toglie combinazioni e non cambia niente.** Le schede di
Daggerheart continuano a uscire come prima. La ragione e' che su quel manuale le
schede hanno un **riquadro disegnato**, e la strada dei riquadri le prende tutte
da sola; le righe di campi servono dove i riquadri sono ciechi, cioe' su
Dragonbane. Le due strade erano state messe in unione proprio per questo, e qui
si vede che e' l'unione a reggere, non una delle due.

Ne segue una cosa da tenere a mente: **il requisito posizionale non e' ancora
stato messo alla prova dove conta.** Su DB separa i tre insiemi veri dai numeri
del D6; su Dag e' innocuo perche' un'altra strada copre. Un manuale con schede
senza riquadro e valori di larghezza molto variabile potrebbe fargli respingere
schede vere.

## 3. Un difetto del mio diagnostico, per il verbale

Lo script di diagnosi contava le occorrenze di una combinazione su **tutte** le
righe che la contengono, sovrainsiemi compresi; la regola conta le righe il cui
insieme di etichette e' **esattamente** quello. Sono due popolazioni diverse, e i
numeri per combinazione che ho riportato durante la diagnosi (`60/168`,
`51/153`, `50/149` su Dag) sono quelli della popolazione larga, non quelli su cui
la regola decide. Il segno della separazione non cambia — su DB i tre insiemi
veri hanno un profilo dominante e i numeri del D6 no, con cinque profili su
cinque occorrenze — ma i rapporti esatti vanno rifatti sulla popolazione giusta
prima di essere citati altrove.

Il conteggio che invece e' misurato sulla popolazione giusta e' quello del §1:
DB 4 → 3 combinazioni, Dag 24 → 22.

## 4. Che cosa resta aperto

- Quali **due** combinazioni cadano su Dag non e' misurato: il log stampa il
  conteggio, non gli insiemi.
- Le schede non sono un producer. Restano calcolate in `main_ir2.py` e passate a
  `build_page_ir2` da un canale laterale, e nella lista dei `page_analysis_*.py`
  un producer di schede non c'e'. L'utente lo ha messo in coda: «per ora
  facciamo funzionare sheet, poi lo integrerai».
