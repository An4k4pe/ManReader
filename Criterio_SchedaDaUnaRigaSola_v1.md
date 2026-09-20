# Criterio — una riga di campi sola basta a fare una scheda

Dichiarato il 20 settembre 2026, **prima** della misura.

## 0. Correzione di una causa sbagliata

`Esito_SchedeDalProducerAIR2_v1.md` §2 attribuisce le nove rotture di paragrafo
perse su Dag alla **nozione di riga** — righe dell'ordine di lettura contro
righe del `source_observation_id` — e propone al §5 di unire le righe di
sorgente sulla stessa banda orizzontale. **È sbagliato**, e la diagnosi
successiva lo mostra: su Dag idx 326 `Dimensioni:` e `Segmenti:` sono due righe
**impilate**, non affiancate, e nessuna banda orizzontale le unirebbe.

La causa vera è un'altra riga di codice. `stat_block_field_lines.field_line_groups`
restituisce anche i gruppi di **una riga sola**, e la strada vecchia ne faceva
un'area di scheda; `page_analysis_stat_block` li scarta con
`_MINIMO_RIGHE_PER_SCHEDA = 2`.

Misurato sulle sette pagine che hanno perso una rottura:

| pagina | righe di campi | gruppi da una riga sola |
| --- | ---: | --- |
| Dag idx 326 (stampata 325) | 8 | `Soglie: 11/22 \| Stress: 6`, `Diffi coltà: 14 \| PF: 8` |
| Dag idx 333 (stampata 332) | 4 | `Soglie: 25/48 \| Stress: 6`, `Diffi coltà: 13 \| PF: 6` |
| Dag idx 335 (stampata 334) | 2 | `Soglie: 30/65 \| Stress: 6`, `Diffi coltà: 17 \| PF: 6` |
| Dag idx 36, 37, 359, 360 | **0** | — |

Le quattro pagine con zero righe di campi sono i casi dell'apostrofo: il
producer non le vede comunque, con o senza il minimo, e non le deve vedere.

## 1. La regola

`_MINIMO_RIGHE_PER_SCHEDA` scende da 2 a 1: **una riga che porta due o più
coppie dichiarate propone gia' una scheda.**

**Non è la regola che l'utente ha rifiutato.** L'11 settembre era caduta «una
**coppia** per riga», cioè accettare righe con un solo campo. Qui la riga deve
avere almeno due coppie come prima: cambia solo quante righe servono a fare un
blocco.

**Perché è lecito indebolire il producer.** Il candidato «non è un fatto di
impaginato approvato, né una rivendicazione di proprietà, né una decisione»: chi
decide è il consumer, che chiede alla riga di portare una combinazione che il
documento ripete almeno tre volte e mette sempre nello stesso posto. Il minimo
di due righe era una seconda guardia nel posto sbagliato — nel producer, dove la
ripetizione non si può vedere.

## 2. La popolazione

DB, Apo e Dag interi, `--tabelle --schede-producer`. Prima:
`output/resa/producer`. Riferimento: `output/resa/senza-riparo`, cioè la strada
vecchia committata in `d59a22f`.

## 3. Che cosa deve succedere perché passi

**A. Le tre perdite vere tornano.** Dag idx 326, 333 e 335 riprendono la
rottura di paragrafo davanti a `Soglie:` e a `Diffi coltà:`.

**B. Le quattro dell'apostrofo restano perse.** Dag idx 36, 37, 359 e 360 non
cambiano: il producer non ha righe di campi lì, e recuperarle vorrebbe dire
rimettere l'artefatto.

**C. Le tabelle non si muovono.** Zero ridotte, sparite, cresciute o nuove
rispetto a `output/resa/producer` su tutti e tre i manuali. In particolare la
tabella dei tesori di DB idx 123 non perde righe: il consumer deve continuare a
respingere le righe del D6.

**D. Nessuna rottura di prosa nuova.** Il conteggio dei paragrafi che cominciano
in minuscola — una frase orfana, cioè prosa tagliata — non sale su nessuno dei
tre manuali.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Se C o D cadono, il minimo nel producer stava reggendo qualcosa che il
consumer non regge, e va rimesso.

## 4. La previsione, scritta prima di guardare

Le tre tornano, le quattro no, e le tabelle non si muovono: il consumer respinge
gia' oggi i candidati della tabella dei tesori, e abbassare il minimo gliene dà
altri da respingere, non da accettare. Mi aspetto che il confronto con
`senza-riparo` scenda da 9 paragrafi di differenza a **6**, tutti dell'apostrofo.
