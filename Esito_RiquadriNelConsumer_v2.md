# Esito — i riquadri nel consumer, v2: **passa**, con un difetto che la previsione non vedeva

Misura di `Criterio_RiquadriNelConsumer_v2.md`, 21 settembre 2026.
Riferimenti: `output/resa/unariga` (`a210405`), `output/resa/riquadri` (v1).
Dopo: `output/resa/riquadri2`.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** il grifone torna intero | **sì** — DB identico a `unariga` byte per byte |
| **B** i miglioramenti della v1 restano | **sì** — i colossi (Dag idx 326, 333-336) e Dag idx 228 come nella v1 |
| **C** le tabelle | **sì** — 1 meglio (Dag idx 228, fantasma), 0 peggio |
| **D** nessuna prosa tagliata | **sì** — DB 71, Apo 38, Dag 124, invariati |
| **E** barra | **sì** — 1763 test verdi, Ruff pulito, E-B 9 su 10 con la sola Fab idx 126 |
| **veto** tabella vera inglobata | **regge** |

```
unariga -> riquadri2   DB uguali 70   Apo uguali 16   Dag uguali 60, SPARITA 1 (idx 228, fantasma)
riquadri -> riquadri2  Dag: tabelle uguali 60; paragrafi 7686 -> 7676, una pagina cambiata
```

## 2. La previsione era sbagliata su una pagina

Avevo scritto: DB identico a `unariga`, **Dag identico alla v1**, Apo invariato.
DB e Apo sì. Dag no: differisce dalla v1 su **Dag idx 214 (stampata 213)**, con
10 paragrafi in meno — e su quella pagina anche `unariga` li aveva. È una
**regressione** rispetto allo stato committato, e il criterio non la sorvegliava:
C guarda le tabelle, D la prosa tagliata, B i miglioramenti della v1.

**La causa.** La pagina ha sei schede avversario in due colonne. `column_band`
ammette un corridoio a **x 322-324**, alto tutta la colonna destra (y 100-690).
Non è il corridoio fra le colonne — quello sta fra x 307 e 319 — ma lo spazio fra
il bordo sinistro dei riquadri di destra (x 319) e il testo dentro (x ≈331). I tre
riquadri di destra lo scavalcano, le loro righe di campi no, e la condizione li
scarta: le tre schede perdono il riquadro come confine, e con lui le rotture di
record delle caratteristiche.

**Che cosa distingue davvero il grifone.** Il pannello del grifone contiene
**testo** dall'altra parte del corridoio: la tabella degli attacchi. I riquadri di
Dag idx 214 dall'altra parte del corridoio hanno solo il proprio bordo. La
condizione della v2 guarda dove sta il **bordo** del riquadro; quella giusta
guarda dove sta il suo **contenuto**.

## 3. Il bilancio contro lo stato committato

| | pagine |
| --- | --- |
| meglio | Dag idx 326, 333, 334, 335, 336 (i colossi si leggono riga per riga), Dag idx 228 (tabella fantasma sparita) |
| peggio | Dag idx 214 (tre schede perdono le rotture di record) |
| invariato | tutto DB, tutto Apo |

## 4. La v3 che la diagnosi indica

Un pezzo non delimita una scheda se, all'altezza della scheda, c'è un corridoio
ammesso che la scheda non scavalca e **il pezzo contiene righe di testo
dall'altra parte**. È una relazione fra rettangoli come la v2, senza soglie; sul
grifone scarta il pannello (la tabella sta dall'altra parte), su Dag idx 214 tiene
i riquadri (dall'altra parte non c'è testo). Da dichiarare e misurare a parte.
