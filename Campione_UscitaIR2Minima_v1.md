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

## Stato del campione

**Dieci pagine su dieci utilizzabili.** `Wil` idx 71 faceva crashare la fetta al
primo giro; il difetto è stato chiuso in `2d6052b` e la pagina è rientrata.

L'ordine di lettura di tutte e dieci è stato **giudicato corretto dall'utente**
prima che IR 2 esistesse — nove pagine più `Wil` idx 71 dopo la correzione. Le
tabelle restano escluse dal giudizio perché il producer di tabelle non esiste.

Questo giudizio è la base di E-B in `Criterio_UscitaIR2Minima_v2.md`, e vale
perché è stato dato da una persona su pagine mai viste: non va rigenerato senza
essere rigiudicato. Dettagli in `Esito_PrecondizioniIR2_v1.md`.

*La versione precedente di questa sezione prescriveva una trascrizione a mano
delle pagine di riferimento. È caduta con la v1 del criterio: la referenza umana
era già stata prodotta dal campione stesso.*
