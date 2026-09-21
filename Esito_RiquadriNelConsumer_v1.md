# Esito — i riquadri disegnati nel consumer: **il veto scatta**, la regola si ritira

Misura di `Criterio_RiquadriNelConsumer_v1.md`, 21 settembre 2026.
Prima: `output/resa/unariga` (commit `a210405`). Dopo: `output/resa/riquadri`.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** il colosso si legge | **sì** |
| **B** il gigante non si restringe | **sì** — DB idx 90 non cambia |
| **C** le tabelle: meglio ≥ peggio | 1 meglio, 1 peggio |
| **D** nessuna prosa tagliata | **sì** — DB 71, Apo 38, Dag 124, invariati |
| **veto** nessuna tabella vera inglobata in una scheda | **CADE** su DB idx 92 |

```
DB:  unariga -> riquadri   uguali 69  SPARITE 1   (idx 92, stampata 91, 12 righe)
Apo: unariga -> riquadri   uguali 16
Dag: unariga -> riquadri   uguali 60  SPARITE 1   (idx 228, stampata 227, 20 righe)
```

## 2. Che cosa funziona

**Il colosso si legge riga per riga.** Dag idx 326, prima:

```
**Dimensioni:** 29 metri di altezza, 20 metri di larghezza **Segmenti:** 2 Gambe, 2 Braccia, 1 Torace e 1 Testa
**CARATTERISTICHE *Forza Colossale - Reazione:*** … ***Schiacciare gli Insetti - Reazione:*** …
```

adesso:

```
**Motivazioni e Tattiche:** Beccare, calpestare, intimidire, intrappolare
**Dimensioni:** 29 metri di altezza, 20 metri di larghezza
**Segmenti:** 2 Gambe, 2 Braccia, 1 Torace e 1 Testa
**Soglie:** 11/22 | **Stress:** 6
**Esperienza:** Enorme +2, Occhi d'Aquila +3
**CARATTERISTICHE**
***Forza Colossale - Reazione:*** Quando Ikeri fallisce un attacco, ottenete Paura.
***Schiacciare gli Insetti - Reazione:*** …
```

Lo stesso sugli altri colossi (Dag idx 333-336): il nome del segmento si stacca da
`Segmenti adiacenti:`, `CARATTERISTICHE` sta da solo, ogni caratteristica apre il
suo paragrafo.

**Dag idx 228 (stampata 227) è un meglio.** La tabella sparita era fantasma: la
pagina è fatta di tre schede avversario, ognuna nel suo riquadro, e nessuna
tabella. Le 20 righe tornano alle schede.

## 3. Che cosa è caduto

**DB idx 92 (stampata 91), il grifone.** La tabella `D6 ATTACCO` degli attacchi
mostruosi è una tabella vera, stampata come tale, ed è sparita: i numeri escono
come paragrafi, `1`, `2`, `3`, `4`.

La causa, da `output/resa/riquadri.py`: un candidato di riquadro,
`(54,117)-(550,382)`, **attraversa le due colonne** della pagina — dalla prosa di
sinistra («I grifoni sono predatori aggressivi…») alla fine della tabella di
destra. Sono quattro primitive vettoriali proposte da `embedded_visual` e da
`interior_visual_frame` con lo stesso bbox; `split_frame` non lo spezza, perché
un solo membro contiene gli altri. Contiene per intero la scheda accettata
(`Ferocia: 2 Taglia: Grande`, colonna sinistra), quindi la regola l'ha preso per
confine della scheda, e con lui la tabella.

**Il veto è nella moneta giusta.** Non c'è niente da emendare: la regola ha
prodotto esattamente il danno che il veto sorvegliava. La condizione «contiene
una scheda accettata» non distingue il riquadro di una scheda da un pannello di
pagina che per caso ne contiene una.

## 4. Conseguenza

Come dichiarato: **la regola si ritira**. `scripts/prototype_ir2_page.py` torna a
`a210405`, e con `--schede-producer` la strada dei riquadri resta dentro `run()`.
`resolution_stat_blocks.py` e i suoi sei test restano in albero, non collegati —
non si cancella, si tagga. Per ricollegarlo bastano i due interventi descritti
nel criterio §2: il ponte `resolved_stat_block_groups` chiama
`resolve_stat_blocks` sui candidati di `chain.analyses` più quelli del producer,
e sotto `--schede-producer` si spegne `stat_block_regions` dentro `run()`.

## 5. La strada che la diagnosi indica

Il riquadro del grifone ha una proprietà che nessun riquadro di scheda misurato
ha: **scavalca il corridoio fra le colonne**. Su Dag idx 326 e 228 ogni riquadro
di scheda sta in una colonna sola (71-308 o 319-556). Una condizione «il pezzo
non attraversa un corridoio di `column_band`» è una relazione fra rettangoli,
non una soglia, e il corridoio è già un fatto della pagina.

Rischio da misurare: le schede a tutta pagina, se un manuale le ha, cadrebbero
tutte. Va dichiarato e misurato come v2, non aggiunto qui.
