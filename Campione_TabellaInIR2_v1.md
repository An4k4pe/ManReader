# Campione di verifica — la tabella in IR 2

Verbale dell'estrazione prescritta da `Criterio_TabellaInIR2_v1.md` §1, che
riusa il protocollo di `Criterio_TabellaRisolvibile_v1.md` §4 — registrato il
19 agosto e mai eseguito fino a ora.

Rigenerabile:

```
./venv/bin/python scripts/sample_ir2_verification_pages.py --pdf-dir . \
    --seed 20260820 --size 12 --exclude-table-criterion-pages
```

| | |
| --- | --- |
| seed | `20260820`, dichiarato nel criterio prima dell'estrazione |
| pool | 5.191 pagine, 16 manuali |
| escluse per costruzione | 10 — le 7 pagine di sviluppo più DB idx 89, DrM idx 86, Vil idx 222 |
| campione | **12 pagine, 8 manuali** |
| scarti | 1 — DrW idx 416, nessun testo |

## Le dodici pagine

Indici **0-based**. Per gli script, `--page-number` è `idx + 1`.

| # | manuale | idx | `--page-number` |
| --- | --- | --- | --- |
| 1 | DIE | 50 | 51 |
| 2 | Lan | 244 | 245 |
| 3 | Kul | 34 | 35 |
| 4 | DIE | 289 | 290 |
| 5 | Wil | 244 | 245 |
| 6 | DrW | 3 | 4 |
| 7 | Fab | 175 | 176 |
| 8 | Wil | 199 | 200 |
| 9 | FW | 222 | 223 |
| 10 | DIE | 2 | 3 |
| 11 | SV | 350 | 351 |
| 12 | FW | 44 | 45 |

Otto manuali: DIE (3), FW (2), Wil (2), Lan, Kul, DrW, Fab, SV. **Nessuno dei
manuali su cui il meccanismo è stato costruito** — DB e DrM non compaiono.

I numeri di pagina **stampati** non sono stati verificati e non vanno citati.

## Cosa manca prima di eseguire

`Criterio_TabellaInIR2_v1.md` §1: **l'etichetta la dà l'utente a vista sul
render — «tabella», «scheda», «nessuna delle due» — prima di vedere qualunque
uscita del codice nuovo.** Finché non è data, i due conteggi del §4 non sono
calcolabili.

Il §3, l'errore squalificante, non dipende dalle etichette e si può verificare
comunque.
