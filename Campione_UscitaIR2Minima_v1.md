# Campione di verifica — IR 2 minima

Verbale dell'estrazione prescritta da `Criterio_UscitaIR2Minima_v1.md` §4, punto 2
dell'ordine vincolante del §6.

Prodotto da `scripts/sample_ir2_verification_pages.py`, committato **prima**
dell'estrazione insieme al criterio (`ef94791`). Rigenerabile:

```
./venv/bin/python scripts/sample_ir2_verification_pages.py --pdf-dir .
```

---

## Estrazione

| | |
| --- | --- |
| seed | `20260818`, dichiarato nel criterio prima dell'estrazione |
| pool | 5.194 pagine, 16 manuali, non condizionato |
| escluse per costruzione | 7 pagine di sviluppo |
| campione | **10 pagine, 8 manuali** |
| scarti per guardia o pagina vuota | **0** |
| estensione per coprire 4 manuali | **0** — non è servita, il campione ne copre 8 |

## Le dieci pagine

Indici **0-based**. Per gli script diagnostici, `--page-number` è `idx + 1`.

| # | manuale | idx (0-based) | `--page-number` |
| --- | --- | --- | --- |
| 1 | FWK | 122 | 123 |
| 2 | BiD | 287 | 288 |
| 3 | Apo | 34 | 35 |
| 4 | Vil | 64 | 65 |
| 5 | FWK | 31 | 32 |
| 6 | Wil | 71 | 72 |
| 7 | Dag | 199 | 200 |
| 8 | Fab | 126 | 127 |
| 9 | BoB | 297 | 298 |
| 10 | BiD | 314 | 315 |

**I numeri di pagina STAMPATI non sono stati verificati e non vanno citati.**
`CLAUDE.md` prescrive di verificarli a render prima di citarli, e qui non serviva:
il criterio, gli script e i render lavorano tutti sull'indice posizionale, e
introdurre un numero stampato non verificato aggiungerebbe solo la trappola che
questo progetto ha già pagato una volta con un'inversione di attribuzione.

## Copertura

8 manuali su 16: Apo, BiD, BoB, Dag, FWK, Fab, Vil, Wil. Il minimo richiesto era
4. Nessun manuale compare più di due volte (BiD e FWK due, gli altri uno).

Nessuno di questi 8 manuali è fra quelli su cui il meccanismo è stato costruito
per la parte di testo — DB, Dag, DrW — salvo **Dag**, che compare una volta con
una pagina (idx 199) non fra le sette escluse.

## Cosa manca prima di eseguire

Punto 3 dell'ordine vincolante del criterio: **le pagine di riferimento vanno
trascritte a mano dall'utente** e messe a verbale **prima** che lo stadio venga
eseguito su di esse. Finché non è fatto, E-B non è misurabile e l'esecuzione
produrrebbe solo una lettura post-hoc.
