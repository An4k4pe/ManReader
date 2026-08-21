# Esito di `Criterio_TabellaNormale_v1.md` — **CADE**

Eseguito con la configurazione del §2, **quella fissata prima e non un'altra**:

```
--region text-lines --repair xy --bounds middle --rows spine --admit in-column
```

## 1. Le etichette, date prima di qualunque uscita

Sul campione cieco di 60 pagine (`Campione_TabellaNormale_v1.md`, seed `20260822`),
l'utente ha etichettato a vista sui render. Esito:

| etichetta | pagine |
| --- | --- |
| **tabella normale** | **3** — BiD idx 227, Dag idx 197, Wil idx 58 |
| tabella speciale | 1 — DIE idx 222 |
| sheet con una tabella dentro | 1 — Wil idx 173 |
| non tabella | 55 |

**Primo giro di etichette perso** e rifatto: descriveva `idx - 1`, verificato per
ricerca testuale su tre casi. Causa dichiarata: la colonna `idx` dell'indice
scambiata per un numero di pagina. I file sono stati rinominati
(`BiD_pagina0035_idx0034.png`) perché non si ripeta.

## 2. Il §4, applicato come è scritto

> Regge se, sulle regioni etichettate normali, almeno il **90%** produce una
> tabella che l'utente giudica corretta a vista.

| pagina | uscita | lettura |
| --- | --- | --- |
| **BiD pag228** | **1 colonna** — nessuna tabella prodotta | fallita |
| **Dag pag198** | 3 colonne, 8 righe: la regione parte da `potete utilizzare:`, che è prosa, e spezza `Amicizia` / `con la Natura` su due righe | non corretta |
| **Wil pag59** | 2 colonne, 4 righe: ogni riga fonde più voci in un blocco unico, con dentro il numero di pagina `59` | non corretta |

**Zero su tre.** Sotto il 90% per qualunque lettura. **Il criterio cade.**

## 3. Il §5, il conteggio che si riporta e non decide

**Falsi negativi: zero.** Tutte e tre le tabelle etichettate normali avevano una
regione proposta da `text/lines`. Il difetto non è la copertura: è la qualità di
ciò che esce.

## 4. Che cosa questo chiude, e che cosa no

**Chiude** la domanda che il criterio poneva: la configurazione del producer
wired, con il modello di riga a spina, **non** produce tabelle corrette su tabelle
normali mai viste. Tre pagine sono poche per una percentuale, ma zero su tre non
è un caso limite.

**Non chiude** nulla sul meccanismo a massimo numero di colonne costruito dopo:
quello non ha un criterio, e il §2 di questo vietava di sostituire la
configurazione senza scriverne uno. Il fatto che sia stato costruito lo stesso è
il rilievo principale della revisione indipendente, ed è a verbale.

**Non autorizza** a rileggere questo esito come conferma del meccanismo nuovo. Sono
due domande diverse, e la seconda non è stata posta.

## 5. Il limite che il §3 del criterio dichiarava prima

Il campione cieco di 60 pagine contiene **3 tabelle normali**. Con un denominatore
di tre, una barra al 90% non ha potere: distingue zero da tre e nient'altro.

Il criterio l'aveva previsto in forma diversa — «il campione è di regioni proposte,
non di tabelle» — ma non aveva previsto che il tasso di base fosse così basso.
**Per una misura con potere serve un campione di tabelle**, non di pagine: 60
pagine uniformi ne contengono tre.
