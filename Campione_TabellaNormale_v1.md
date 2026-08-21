# Campione — `Criterio_TabellaNormale_v1.md` §3

Verbale dell'estrazione. **Le pagine non le ha scelte Chat A**: seed dichiarato
nel criterio prima di guardare qualunque cosa.

Rigenerabile:

```
./venv/bin/python scripts/sample_ir2_verification_pages.py --pdf-dir . \
    --seed 20260822 --size 60 \
    --exclude-table-criterion-pages --exclude-normal-table-pages
```

| | |
| --- | --- |
| seed | `20260822`, dichiarato nel criterio §3 prima dell'estrazione |
| pool | 16 manuali |
| escluse per costruzione | **28** — 7 di sviluppo IR 2, 3 del criterio schede, **18 di questa sessione** |
| campione | **60 pagine, 16 manuali** |
| scarti | 3 — Dag idx 371, DrM idx 0, BiD idx 7: nessun testo |

**Tre numerazioni diverse, e vanno tenute separate** — il primo giro di
etichettatura si è perso proprio qui:

| | esempio su BiD |
| --- | --- |
| `idx`, 0-based, quello degli script | `34` |
| **pagina del file**, 1-based, quella che mostra un lettore PDF | **35** |
| numero **stampato** sulla carta | `28` |

I nomi dei file portano ora entrambi i primi due
(`BiD_pagina0035_idx0034.png`) perché l'etichetta non possa più cadere su una
pagina diversa da quella resa. Il numero stampato non è stato verificato e non va
citato.

**Primo giro di etichette: perso.** Le etichette date sul campione descrivevano
`idx - 1`, verificato per ricerca testuale su tre casi e non dedotto: la tabella
`GRADO DI EFFICACIA` sta a BiD idx 33 e non 34, `D20 | LESIONE | EFFETTO` a DB
idx 52 e non 53, `OGGETTO | PI | EFFETTO` a Fab idx 105 e non 106. Le pagine rese
erano quelle giuste; a scorrere di uno è stata la lettura della colonna `idx`
come se fosse un numero di pagina. Responsabilità di chi ha scritto l'indice.

## Che cosa è stato prodotto, e che cosa NO

Prodotti: **60 render**, uno per pagina, con sopra le regioni proposte dalle tre
sorgenti — **verde** `lines/lines`, **rosso** `text/lines` (la configurazione del
producer wired), **blu tratteggiato** le bande `column_band` con i gutter
ombreggiati.

**Nessuna uscita Markdown è stata prodotta**, come il §3 passo 2 prescrive. Il
percorso tabella non è stato eseguito su nessuna di queste pagine.

## Il conteggio grezzo, che non è un'etichetta

| | |
| --- | --- |
| pagine con **almeno una** regione proposta | **35** |
| pagine con **nessuna** regione proposta | **25** |

Questo dice quante pagine una sorgente qualsiasi tocca, **non** quante contengono
una tabella. Le 25 senza regione vanno guardate lo stesso: servono al §5, il
conteggio dei falsi negativi.

## Cosa manca prima di poter calcolare qualunque cosa

`Criterio_TabellaNormale_v1.md` §3 passo 3: **l'etichetta la dà l'utente a vista
sul render, prima di vedere qualunque uscita del codice.** Per ogni regione
disegnata: «normale» / «speciale» / «non è una tabella». Per ogni pagina: se c'è
una tabella che **nessuna** sorgente propone.

Finché non è data, il §4 non è calcolabile e non lo si inventa.

## Le 60 pagine

| # | idx (0-based) | file | lines | text-lines | band |
| --- | --- | --- | --- | --- | --- |
| 1 | FWK idx 146 | `FWK_pagina0147_idx0146.png` | 0 | 0 | 0 |
| 2 | Dag idx 356 | `Dag_pagina0357_idx0356.png` | 1 | 1 | 4 |
| 3 | Lan idx 21 | `Lan_pagina0022_idx0021.png` | 6 | 2 | 1 |
| 4 | Lan idx 282 | `Lan_pagina0283_idx0282.png` | 0 | 0 | 2 |
| 5 | BiD idx 207 | `BiD_pagina0208_idx0207.png` | 0 | 0 | 0 |
| 6 | Vil idx 69 | `Vil_pagina0070_idx0069.png` | 0 | 0 | 0 |
| 7 | Fab idx 7 | `Fab_pagina0008_idx0007.png` | 0 | 1 | 1 |
| 8 | Lan idx 165 | `Lan_pagina0166_idx0165.png` | 4 | 2 | 1 |
| 9 | BiD idx 227 | `BiD_pagina0228_idx0227.png` | 1 | 1 | 2 |
| 10 | Fab idx 106 | `Fab_pagina0107_idx0106.png` | 0 | 1 | 0 |
| 11 | BiD idx 306 | `BiD_pagina0307_idx0306.png` | 2 | 1 | 2 |
| 12 | Wil idx 173 | `Wil_pagina0174_idx0173.png` | 2 | 1 | 4 |
| 13 | Kul idx 176 | `Kul_pagina0177_idx0176.png` | 0 | 0 | 0 |
| 14 | BiD idx 34 | `BiD_pagina0035_idx0034.png` | 0 | 0 | 0 |
| 15 | Dag idx 254 | `Dag_pagina0255_idx0254.png` | 0 | 2 | 1 |
| 16 | FW idx 218 | `FW_pagina0219_idx0218.png` | 0 | 0 | 0 |
| 17 | Dag idx 340 | `Dag_pagina0341_idx0340.png` | 0 | 0 | 2 |
| 18 | Wil idx 267 | `Wil_pagina0268_idx0267.png` | 0 | 0 | 0 |
| 19 | FW idx 143 | `FW_pagina0144_idx0143.png` | 0 | 1 | 0 |
| 20 | Apo idx 117 | `Apo_pagina0118_idx0117.png` | 0 | 0 | 0 |
| 21 | Lan idx 98 | `Lan_pagina0099_idx0098.png` | 0 | 2 | 1 |
| 22 | Dag idx 139 | `Dag_pagina0140_idx0139.png` | 2 | 2 | 1 |
| 23 | DIE idx 191 | `DIE_pagina0192_idx0191.png` | 0 | 0 | 0 |
| 24 | Dag idx 197 | `Dag_pagina0198_idx0197.png` | 3 | 1 | 2 |
| 25 | Wil idx 111 | `Wil_pagina0112_idx0111.png` | 0 | 0 | 0 |
| 26 | Fab idx 28 | `Fab_pagina0029_idx0028.png` | 1 | 1 | 0 |
| 27 | DB idx 53 | `DB_pagina0054_idx0053.png` | 1 | 0 | 3 |
| 28 | DrM idx 182 | `DrM_pagina0183_idx0182.png` | 0 | 2 | 6 |
| 29 | Fab idx 11 | `Fab_pagina0012_idx0011.png` | 0 | 0 | 0 |
| 30 | DIE idx 319 | `DIE_pagina0320_idx0319.png` | 0 | 1 | 1 |
| 31 | Wil idx 109 | `Wil_pagina0110_idx0109.png` | 0 | 0 | 0 |
| 32 | Lan idx 220 | `Lan_pagina0221_idx0220.png` | 4 | 2 | 1 |
| 33 | DIE idx 128 | `DIE_pagina0129_idx0128.png` | 0 | 0 | 1 |
| 34 | Vil idx 75 | `Vil_pagina0076_idx0075.png` | 0 | 0 | 0 |
| 35 | FW idx 78 | `FW_pagina0079_idx0078.png` | 0 | 0 | 0 |
| 36 | Lan idx 281 | `Lan_pagina0282_idx0281.png` | 0 | 0 | 2 |
| 37 | DrW idx 256 | `DrW_pagina0257_idx0256.png` | 0 | 0 | 1 |
| 38 | Kul idx 195 | `Kul_pagina0196_idx0195.png` | 0 | 0 | 0 |
| 39 | SV idx 67 | `SV_pagina0068_idx0067.png` | 0 | 0 | 0 |
| 40 | BiD idx 190 | `BiD_pagina0191_idx0190.png` | 0 | 1 | 1 |
| 41 | Lan idx 173 | `Lan_pagina0174_idx0173.png` | 4 | 2 | 1 |
| 42 | BoB idx 31 | `BoB_pagina0032_idx0031.png` | 0 | 0 | 0 |
| 43 | Dag idx 71 | `Dag_pagina0072_idx0071.png` | 0 | 0 | 0 |
| 44 | Wil idx 58 | `Wil_pagina0059_idx0058.png` | 1 | 1 | 0 |
| 45 | DrW idx 275 | `DrW_pagina0276_idx0275.png` | 0 | 1 | 1 |
| 46 | Lan idx 184 | `Lan_pagina0185_idx0184.png` | 0 | 0 | 0 |
| 47 | DIE idx 222 | `DIE_pagina0223_idx0222.png` | 0 | 1 | 4 |
| 48 | Lan idx 297 | `Lan_pagina0298_idx0297.png` | 7 | 1 | 5 |
| 49 | Lan idx 31 | `Lan_pagina0032_idx0031.png` | 0 | 0 | 1 |
| 50 | FWK idx 220 | `FWK_pagina0221_idx0220.png` | 0 | 0 | 0 |
| 51 | SV idx 177 | `SV_pagina0178_idx0177.png` | 0 | 0 | 1 |
| 52 | Lan idx 289 | `Lan_pagina0290_idx0289.png` | 7 | 1 | 5 |
| 53 | SV idx 44 | `SV_pagina0045_idx0044.png` | 0 | 0 | 0 |
| 54 | BoB idx 376 | `BoB_pagina0377_idx0376.png` | 0 | 0 | 0 |
| 55 | DrW idx 327 | `DrW_pagina0328_idx0327.png` | 0 | 1 | 1 |
| 56 | Lan idx 128 | `Lan_pagina0129_idx0128.png` | 0 | 0 | 0 |
| 57 | Fab idx 253 | `Fab_pagina0254_idx0253.png` | 0 | 1 | 0 |
| 58 | BoB idx 247 | `BoB_pagina0248_idx0247.png` | 0 | 0 | 1 |
| 59 | FWK idx 60 | `FWK_pagina0061_idx0060.png` | 0 | 0 | 0 |
| 60 | Kul idx 85 | `Kul_pagina0086_idx0085.png` | 0 | 0 | 0 |
