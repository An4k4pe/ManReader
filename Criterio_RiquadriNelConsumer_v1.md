# Criterio — i riquadri disegnati nel consumer: il confine dal disegno, l'identità dalla policy

Dichiarato il 21 settembre 2026, **prima** della misura. Richiesta dell'utente:
«porta i riquadri disegnati nel consumer».

## 0. Il problema, su una pagina

Dag idx 326 (stampata 325), il colosso. Dalla strada del producer
(`output/resa/unariga`) l'area della scheda di Ikeri è **la sola riga**
`Soglie: 11/22 | Stress: 6`, perché un'area riconosciuta dalle righe di campi è
fatta solo delle righe di campi. Quindi `Dimensioni:` e `Segmenti:` restano
incollate — portano un campo ciascuna — e così le caratteristiche:

```
**Dimensioni:** 29 metri di altezza, 20 metri di larghezza **Segmenti:** 2 Gambe, 2 Braccia, 1 Torace e 1 Testa

**CARATTERISTICHE *Forza Colossale - Reazione:*** … ***Schiacciare gli Insetti - Reazione:*** …
```

Il riquadro grigio della scheda c'è ed è disegnato. La strada dei riquadri però è
rimasta dentro `run()`, sulla catena di lettura, con la sua regola d'identità —
«almeno due righe con almeno due coppie» — che è lo stesso test debole del
producer fatto una seconda volta, e che su quel riquadro non passa.

## 1. Che cosa c'è sulla pagina, misurato prima di scrivere la regola

`output/resa/riquadri.py`. Su Dag idx 326 i riquadri disegnati, spezzati da
`split_frame` nei loro massimali, sono cinque pezzi — uno per scheda — e **ogni
pezzo contiene una sola proposta**:

| pezzo | righe dentro | proposta dentro |
| --- | ---: | --- |
| (71,85)-(308,300), IKERI | 18, dal nome alla fine delle caratteristiche | `Soglie: 11/22 \| Stress: 6` |
| (319,85)-(556,249), TESTA | 13 | `Diffi coltà: 16 \| PF: 5 …` |
| (319,255)-(555,397), TORACE | 11 | `Diffi coltà: 14 \| PF: 8` |
| (71,565)-(307,737), BRACCIO | 14 | `Diffi coltà: 13 \| PF: 3 …` |
| (319,566)-(556,690), GAMBA | 9 | `Diffi coltà: 13 \| PF: 3 …` |

Il riquadro bianco interno non compare da solo: sta dentro il grigio, e vince il
massimale. Ogni riquadro è proposto due volte, da `embedded_visual` e da
`interior_visual_frame`, con lo stesso bbox.

**Su DB la situazione è un'altra, e decide una condizione.** La pergamena delle
schede di Dragonbane è un'immagine **raster**, esclusa dal filtro «solo
disegnati» (`stat_block_inputs`, correzione dell'utente: «ti starai confondendo
con lo sfondo»). Su DB idx 90 l'unico riquadro disegnato vicino alla scheda è il
filetto sotto `Ferocia: 1 Taglia: Enorme`, che contiene **una** delle due righe
della scheda. Una regola «il riquadro che contiene la scheda ne è il confine»
senza condizioni restringerebbe il gigante a una riga.

Su DB idx 43 (la scatola AZIONI) e idx 123 (i tesori) i riquadri disegnati sono
fasce di titolo e piè di pagina: non contengono proposte accettate.

## 2. La regola

1. I riquadri **disegnati** della pagina — candidati di `interior_visual_frame` e
   di `embedded_visual` fatti solo di primitive vettoriali — si spezzano con
   `split_frame` nei loro massimali. Due pezzi con lo stesso bbox sono uno.
2. Un pezzo **delimita una scheda** se contiene **per intero** almeno una
   proposta accettata dal consumer: ogni riga della proposta ha il centro dentro
   il pezzo. **Il riquadro dà il confine, non l'identità**: un riquadro senza
   una scheda accettata dentro resta quello che è — è la condizione del 12
   settembre, «può essere un elemento, ma non lo userei come unico
   discriminante», perché lo stesso fondo fa anche da box di regole.
3. Fra due pezzi che delimitano e stanno uno dentro l'altro vince il più
   **grande**: è la stessa regola dei massimali di `split_frame`, estesa ai
   pezzi di candidati diversi.
4. L'area della scheda è il pezzo, e le sue righe sono tutte le righe di testo
   col centro dentro. Le proposte accettate che non stanno per intero in nessun
   pezzo restano schede da sole, come oggi.
5. Dove sta: in un modulo di Resolution parallelo, `resolution_stat_blocks.py`,
   sul precedente di `resolution_column_boundaries.py` (Milestone 43):
   `resolve_page_candidates` decide un esito per candidato e non produce
   regioni nuove, e questa regola produce regioni.

**Nessuna soglia nuova**: contenimento per intero, massimali, centro della riga
dentro il pezzo — tutte relazioni fra rettangoli già usate da `split_frame`.

**Con `--schede-producer` la strada dei riquadri dentro `run()` si spegne.** Il
riquadro passa al consumer, non si duplica. Con `--schede-campi` resta tutto
com'è, per il confronto.

## 3. La popolazione

DB, Apo e Dag interi, `--tabelle --schede-producer`. Prima: `output/resa/unariga`
(la strada del producer con i riquadri ancora dentro `run()`, commit `a210405`).

## 4. Che cosa deve succedere perché passi

**A. Il colosso si legge.** Su Dag idx 326, `Dimensioni:`, `Segmenti:` e
`Soglie: | Stress:` stanno su tre paragrafi, e `Forza Colossale - Reazione:` e
`Schiacciare gli Insetti - Reazione:` aprono ciascuna il suo.

**B. Il gigante non si restringe.** Su DB idx 90 la scheda resta di due righe e la
tabella resta com'è.

**C. Le tabelle.** Ogni tabella che cambia rispetto a `unariga` si guarda
sull'immagine, con il giudizio di `Criterio_SchedaControLaTabella_v1.md`:
**meglio** se esce una riga che la pagina stampa **fuori** dalla tabella,
**peggio** se esce una riga che la pagina stampa **dentro**. Passa se meglio ≥
peggio, e nessuna delle sei tabelle già giudicate peggiora — DB idx 87, 90, 97,
123; Dag idx 230, 359.

**D. Nessuna prosa tagliata.** Il conteggio dei paragrafi che cominciano in
minuscola non sale su nessuno dei tre manuali.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Se una tabella che la pagina stampa come tabella perde righe perché un
riquadro l'ha inglobata in una scheda, la condizione «contiene una scheda
accettata» non basta, e la regola si ritira.

## 5. La previsione, scritta prima di guardare

- Dag: le rotture di paragrafo **aumentano** nelle pagine delle schede, perché le
  aree diventano i riquadri interi; le tabelle cambiano poco, perché su
  Daggerheart la strada vecchia dei riquadri copriva già quasi tutto. Il colosso
  passa A.
- DB: quasi nessun cambiamento. I riquadri disegnati di DB sono filetti e fasce,
  la pergamena è raster, e la condizione «per intero» li scarta.
- Apo: nessun cambiamento. Nessuna proposta accettata, quindi nessun riquadro
  delimita niente.

Rischio che dichiaro: su Daggerheart la strada vecchia dei riquadri accettava
anche schede con due righe di coppie **non dichiarate**; quelle che non portano
una combinazione ammessa dalla policy qui non passano. Se ce ne sono, perdono
l'area e con lei le loro rotture di record.
