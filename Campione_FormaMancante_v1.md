# Campione — `Criterio_FormaMancante_v3.md` §4

Verbale dell'estrazione. **Le pagine non le ha scelte Chat A**: seed dichiarato
nel criterio, committato in `992de5f` **prima** che l'estrazione avvenisse.

Rigenerabile:

```
./venv/bin/python scripts/sample_ir2_verification_pages.py --pdf-dir . \
    --seed 20260824 --size 40 \
    --exclude-table-criterion-pages --exclude-normal-table-pages \
    --exclude-forma-mancante-pages
```

| | |
| --- | --- |
| seed | `20260824`, dichiarato nel criterio §4 prima dell'estrazione |
| pool | **5.088** pagine, 16 manuali (corpus 5.201 meno 113 esclusioni) |
| escluse per costruzione | **113** |
| campione | **40 pagine, 15 manuali** |
| scarti | **1** — Kul idx 241: nessun testo |
| commit di partenza (pin del §3) | `992de5f` |

Il pool coincide col numero che il criterio aveva previsto per calcolo
(≈5.088) prima di eseguire lo script.

## Le tre numerazioni, che hanno già fatto perdere un giro di etichette

| | esempio |
| --- | --- |
| `idx`, 0-based, quello degli script | `227` |
| **pagina del file**, 1-based, quella che mostra un lettore PDF | **228** |
| numero **stampato** sulla carta | non verificato |

I render si chiamano `DrW_pagina0228_idx0227.png` perché l'etichetta non possa
cadere su una pagina diversa da quella resa. **Il numero stampato non è stato
verificato e non va citato.**

## Che cosa è stato corretto prima di estrarre

Il §4 del criterio impone che l'estrazione avvenga **dopo** la correzione della
lista di esclusioni, perché il campione è funzione di (seed, pool, esclusioni,
procedura) e dichiarare il seed prima cambiando le esclusioni dopo non
vincolerebbe niente.

**Aggiunte a `NORMAL_TABLE_EXCLUSIONS`**: DB 61, Lan 18, Lan 51, Wil 77. Sono
pagine di sviluppo elencate in `Criterio_EstensioneRegioneTabella_v1.md:41-42`,
e due compaiono nelle righe di comando committate di
`scripts/inspect_table_gutter_regularity.py:22` e
`scripts/compare_table_gutters_with_column_band.py:16`. **La lacuna non nasceva
nello script**: `Criterio_TabellaNormale_v1.md:59-62` ne elenca 18 e lo script le
copia; le quattro mancavano nel criterio, scritto nello stesso commit del
criterio gemello che già ne elencava 17.

**Nuovo insieme `FORMA_MANCANTE_EXCLUSIONS`**: le 10 pagine del campione di
Milestone 38 e le 60 di `Campione_TabellaNormale_v1.md`. Sono le pagine su cui
l'utente ha **già dato un giudizio**, e questo criterio ha per regola che decide
un giudizio dell'utente. Le 60 sono elencate **letteralmente** e non rigenerate
con lo script: vedi sotto.

## Un difetto che sta fuori da questo campione, e va scritto

`NORMAL_TABLE_EXCLUSIONS` aveva **29 voci distinte** (35 scritte, 6 duplicate)
prima di questa correzione, mentre `Campione_TabellaNormale_v1.md:18` dichiara
«escluse per costruzione: 28 — 7 di sviluppo IR 2, 3 del criterio schede, 18 di
questa sessione». Le 11 in più — il blocco delle «16 tabelle su cui il meccanismo
a massimo numero di colonne è stato costruito» — sono state appese allo script
**dopo** l'estrazione di quel campione.

Conseguenza: **la riga di comando documentata in `Campione_TabellaNormale_v1.md`
non riproduce più le 60 pagine che quel file elenca**, e dopo questa correzione
ne escluderebbe 43. Il campione da 60 **non è contaminato** — verificato voce per
voce, nessuna pagina di sviluppo vi compare — e il verdetto di
`Esito_TabellaNormale_v1.md` regge. Ma quel file ha bisogno di una nota, o il
prossimo che lo rigenera otterrà un campione diverso credendo di avere lo stesso.

È anche la ragione per cui qui le 60 sono escluse **per elenco letterale**.

## Le 40 pagine

Indici **0-based**. Per gli script diagnostici, `--page-number` è `idx + 1`.
L'ordine è quello di estrazione, ed è **vincolante**: il §4 ricava da esso i due
sottoinsiemi.

| # | manuale | idx | `--page-number` | insieme |
| --- | --- | --- | --- | --- |
| 1 | DrW | 227 | 228 | verdetto · **etichette** |
| 2 | DIE | 379 | 380 | verdetto · **etichette** |
| 3 | BiD | 76 | 77 | verdetto · **etichette** |
| 4 | Fab | 247 | 248 | verdetto · **etichette** |
| 5 | Wil | 154 | 155 | verdetto · **etichette** |
| 6 | FWK | 70 | 71 | verdetto |
| 7 | Wil | 7 | 8 | verdetto |
| 8 | SV | 180 | 181 | verdetto |
| 9 | FW | 138 | 139 | verdetto |
| 10 | SV | 178 | 179 | verdetto |
| 11 | BiD | 8 | 9 | verdetto |
| 12 | Wil | 103 | 104 | verdetto |
| 13 | Lan | 243 | 244 | verdetto |
| 14 | Vil | 21 | 22 | verdetto |
| 15 | DIE | 286 | 287 | verdetto |
| 16 | Vil | 70 | 71 | verdetto |
| 17 | Apo | 56 | 57 | verdetto |
| 18 | Fab | 307 | 308 | verdetto |
| 19 | DrM | 361 | 362 | verdetto |
| 20 | Lan | 192 | 193 | verdetto |
| 21 | Lan | 20 | 21 | — |
| 22 | SV | 3 | 4 | — |
| 23 | Dag | 251 | 252 | — |
| 24 | Wil | 72 | 73 | — |
| 25 | Kul | 219 | 220 | — |
| 26 | Lan | 364 | 365 | — |
| 27 | DIE | 399 | 400 | — |
| 28 | SV | 198 | 199 | — |
| 29 | DIE | 382 | 383 | — |
| 30 | Vil | 208 | 209 | — |
| 31 | SV | 369 | 370 | — |
| 32 | Fab | 171 | 172 | — |
| 33 | Fab | 286 | 287 | — |
| 34 | DrM | 172 | 173 | — |
| 35 | DrM | 184 | 185 | — |
| 36 | Lan | 116 | 117 | — |
| 37 | BoB | 62 | 63 | — |
| 38 | Fab | 118 | 119 | — |
| 39 | DrW | 272 | 273 | — |
| 40 | Fab | 142 | 143 | — |

**Insieme del verdetto**: le prime 20, riga per riga come sopra.
**Insieme delle etichette**: le prime 5 delle 20, che risultano di **cinque
manuali diversi** — la regola di scarto per manuale già uscito non ha dovuto
scattare. Resta da applicare il filtro «pagine troppo corte» del §2, che dipende
dall'uscita del codice: se una delle cinque emette meno di 10 paragrafi, si
scende alla successiva delle 20 e lo si registra qui.

## Copertura

**15 manuali su 16. L'unico assente è `DB`**, ed è il manuale con più pagine
escluse per costruzione: DB 98, 17, 52, 49 (sviluppo IR 2), DB 89 (criterio
schede), DB 61, 75, 122 (sviluppo tabelle), più DB 53 fra le 60. La sua assenza
è quindi un effetto diretto delle esclusioni, non del caso — e va tenuta
presente leggendo l'esito, perché DB è anche il manuale su cui la maggior parte
del lavoro precedente è stata fatta e quello da cui vengono molti degli esempi a
verbale.

Nessun manuale compare più di sei volte (Fab sei, SV cinque, Lan cinque).

## Che cosa è stato prodotto

Per ciascuna delle 40, con la configurazione del §3 (`--tables` spento,
`--interrupt-corridor` spento, `--base` non passato): `page_ir2.md`,
`document_ir2.json`, `review_ir2.md` e gli asset estratti. Più un **render nudo**
della pagina (`scripts/render_sample_pages.py`, nessun overlay di candidati: chi
etichetta deve dire che cos'è un frammento sulla pagina, non vedere cosa ha già
deciso un meccanismo).

**Nessuna etichetta e nessun verdetto sono stati dati**, e finché non lo sono le
§6.A e §6.B non sono calcolabili e non le si inventa.
