# Esito — i riquadri nel consumer, v3: **passa**, previsione centrata su tutti e tre

Misura di `Criterio_RiquadriNelConsumer_v3.md`, 22 settembre 2026.
Riferimenti: `output/resa/unariga` (`a210405`), `output/resa/riquadri` (v1),
`output/resa/riquadri2` (v2). Dopo: `output/resa/riquadri3`.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** il grifone resta intero | **sì** — DB identico a `unariga` byte per byte |
| **B** Dag identico alla v1 | **sì** — byte per byte: Dag idx 214 recuperato, tutti i miglioramenti della v1 tenuti |
| **C** le tabelle | **sì** — una sola cambia, la fantasma di Dag idx 228; nessuna tabella vera perde righe |
| **D** nessuna prosa tagliata | **sì** — DB 71, Apo 38, Dag 124, invariati da `unariga` |
| **E** barra | **sì** — 1763 test verdi, Ruff pulito, E-B 9 su 10 con la sola Fab idx 126 |
| **veto** tabella vera inglobata | **regge** |

```
unariga -> riquadri3   DB uguali 70   Apo uguali 16   Dag uguali 60, SPARITA 1 (idx 228, fantasma)
DB  contro unariga:  IDENTICO
Apo contro unariga:  IDENTICO
Dag contro riquadri: IDENTICO
```

La previsione del §5 era: DB identico a `unariga`, Apo invariato, Dag identico
alla v1. Tutte e tre centrate.

## 2. Che cosa ha risolto il cambio

La v2 guardava dove passa il **bordo** del riquadro; la v3 guarda dove sta il suo
**contenuto**. Un pezzo non delimita una scheda se, all'altezza della scheda, ha
righe di testo dall'altra parte di un corridoio che la scheda non scavalca.

| pagina | oltre il corridoio, dentro il pezzo | v2 | v3 |
| --- | --- | --- | --- |
| DB idx 92, il grifone | la tabella `D6 ATTACCO` | scarta | **scarta** |
| Dag idx 214, i tre riquadri di destra | niente, solo il bordo | scarta | **tiene** |

Su Dag idx 214 il corridoio ammesso a x 322-324 è lo spazio fra il bordo sinistro
dei riquadri (x 319) e il testo dentro (x ≈331): il bordo lo scavalca, il testo
no. Era la regressione della v2, e non c'è più.

## 3. Il bilancio contro lo stato di partenza (`a210405`)

| | pagine |
| --- | --- |
| meglio | Dag idx 326, 333, 334, 335, 336 — i colossi si leggono riga per riga; Dag idx 228 — sparisce una tabella fantasma fatta di tre schede |
| peggio | **nessuna** |
| invariato | tutto DB, tutto Apo |

## 4. Che cosa resta aperto

La regola è stata formata guardando sei pagine di due manuali. Le tre condizioni
— per intero, massimali, contenuto oltre il corridoio — non sono mai state viste
su un manuale che non abbia partecipato alla loro costruzione. È esattamente ciò
che il test sui manuali mai toccati deve dire.
