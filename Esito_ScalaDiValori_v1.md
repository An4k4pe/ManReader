# Esito di `Criterio_ScalaDiValori_v1.md` — **il veto regge in pieno, la regressione cade**

**Stato in una riga**: il veto §4.A regge **20 su 20**, zero disaccordi e zero
`incerto`; la copertura §4.C regge **43 su 43**; la **regressione §4.B cade** — due
dei quattro elenchi veri sono andati persi; la giunzione §4.D lascia **6 casi da
guardare a occhio** su DB. Il criterio **non è scaricato**.

---

## 1. Veto §4.A — regge, e su nessuna voce l'agente ha esitato

20 blocchi, seed `20260919` dichiarato prima, 10 per classe, materiale costruito
**dalla resa** e non dalla sorgente.

| | |
| --- | ---: |
| concordi con la classificazione | **20 / 20** |
| `scala` giudicate elenco | **0** |
| `elenco` giudicate scala | **0** |
| `incerto` | **0** |

Le due direzioni del veto sono entrambe a zero, come il §4.A chiedeva.

**L'agente ha ricostruito la regola dai render, senza conoscerla**: «se il
carattere iniziale cambia da riga a riga portando un valore è una scala; se è lo
stesso segno su ogni riga è un punto elenco». È la stessa distinzione che il §1
del criterio pre-registra, arrivata da chi guardava solo le pagine.

E ha visto **che cosa sono davvero i glifi**: ingrandendo i render ha letto nei
badge di DrM `≤11`, `12-16`, `17+`, e ha notato che su `Gust of Wind` non c'è
nemmeno un danno — a variare per fascia è l'entità dello spostamento. È la
conferma indipendente che il glifo porta il valore.

### Quanto vale questo 20 su 20, detto senza sconti

**Tutte e 10 le `scala` vengono da DrM**, perché DrM è l'unico manuale del corpus
che ne produce. La distinzione che l'agente ha operato è quindi in buona parte
«schede mostro di DrM contro elenchi di altri manuali», e un campione che non
contiene **nessun caso di confine** conferma la regola invece di metterla alla
prova. È lo stesso limite già a verbale per l'arredo, e vale la pena ripeterlo:
il veto misura la precisione, e a testare la copertura sono le altre barre.

Zero disaccordi su 20 mette il tasso d'errore **sotto il 14%** al 95%, non vicino
a zero.

## 2. Copertura §4.C — regge

Verità di riferimento: i blocchi di DrM che contengono `!`, `@` e `#`.

| | |
| --- | ---: |
| blocchi tier | 43 |
| classificati `scala` | **43** |
| classificati `elenco` | **0** |

**100%**, contro una barra di tre quarti. E su tutte le pagine di scheda provate
DrM produce ora **zero** voci d'elenco, dove il giudizio precedente ne aveva
contate sei fasulle su nove cadute.

**Non è indipendente**, ed è dichiarato nel criterio: DrM è insieme il manuale su
cui ho visto la firma e quello su cui la copertura la misura.

## 3. Regressione §4.B — **cade**

`./venv/bin/python scripts/check_list_regression.py --pdf-dir .`

| voce | manuale | idx | righe ancora voci | esito |
| --- | --- | ---: | ---: | --- |
| 03 | FWK | 119 | **0** | **CADE** |
| 10 | FWK | 117 | **0** | **CADE** |
| 05 | BoB | 226 | 5 | ok |
| 08 | FW | 160 | 9 | ok |

Due dei quattro elenchi che il giudizio cieco precedente aveva dichiarato **veri**
non sono più elenchi: su FWK `•Comunica al Mondo:` è tornato paragrafo col glifo
dentro.

**La causa non è la firma di scala.** Lo erano già prima che la cablassi —
verificato confrontando le due rese — quindi il pezzo nuovo non c'entra. È la
**regola delle corse**: su FWK ogni marcatore di primo livello sta da solo nel suo
blocco, e i blocchi non sono consecutivi perché in mezzo stanno quelli delle
sotto-opzioni `*`. Corse di una riga, quindi niente elenco.

> **Non è stato ritoccato**, e il criterio lo dice: «se B cade, la regola compra
> precisione perdendo elenchi veri; non si ritocca la condizione per recuperarli,
> si riporta quanto si è perso».

È lo stesso annidamento che `Esito_Elenchi_v1.md` aveva già visto come perdita di
subordinazione, e che il §5 del criterio dichiara fuori scope. Qui torna con un
danno diverso: prima l'annidamento appiattiva, ora fa sparire il livello.

## 4. Giunzione §4.D — pulita su FWK, **6 casi da guardare** su DB

| manuale | pagine | blocchi cambiati | sospette |
| --- | ---: | ---: | ---: |
| FWK | 4 | 32 | **0** |
| DB | 3 | 13 | **6** |

Le sei stanno su due pagine, e la causa si vede: su DB p.117 il `✦` compare **in
mezzo alla prosa** — `spalancato verso l'ingresso del Cortile (#3). ✦**La
Trappola:** …` — quindi la resa a elenco spezza una frase e lascia un frammento
che comincia in minuscolo (`è collassato nel vecchio sotterraneo…`).

**Questa clausola chiede l'occhio, non uno strumento**, e le sei righe sono quelle
che vanno guardate. Lo strumento le ha portate a galla, che è tutto ciò che
poteva fare.

## 5. Che cosa questo pezzo ha spedito

- **La causa principale delle cadute è chiusa**: 6 voci su 9 erano schede mostro
  di DrM, e ora DrM produce zero elenchi fasulli.
- Il **legame glifo-testo** è riparato dove l'ordine di lettura lo rompeva: FW
  p.168 rende tutte e cinque le voci invece di tre più due orfani.
- Il **marcatore si toglie dai run** e non dalla stringa resa, e si tolgono
  **tutti** quelli in testa: due difetti misurati su FW.
- `document_line_start_measurements` e `document_list_policy` restano separati,
  misura e politica, come per l'arredo.

## 6. Che cosa resta aperto, e va detto insieme al resto

- **L'annidamento**, che ora costa due elenchi veri (§3). È il fascicolo più
  urgente di questo filone: il segnale che manca è il **rientro**, che sta nelle
  primitive e che nessuno guarda.
- **Le sei giunzioni di DB** (§4).
- **L'ellissi `…` di FW**, ancora un elenco per questa regola.
- **Due riquadri capacità di DB in blocchi consecutivi** — `b0003` e `b0004` a
  idx 13 — che formano una corsa di due e diventano un elenco. Misurato, non
  ritoccato: emendare due volte prima del giudizio avrebbe svuotato il veto.
- **Le schede mostro come categoria**, che `State.md` e la memoria del progetto
  nominano da agosto. Questo giro le ha aggirate per glifo; riconoscerle resta da
  fare.

## 7. Verifiche

Suite **1442** test, un solo fallimento, quello ambientale già a verbale
(`test_runs_table_candidate_for_known_dag_page` cerca `Dag.pdf` nella root), 8
skip. Ruff verde sui file toccati.

## 8. Conseguenza

Il meccanismo **fa ciò per cui è stato scritto** e **costa due elenchi veri**. Non
è «pronto» e non è «da buttare»: è un pezzo che chiude la causa maggiore e ne
lascia scoperta una minore, con il conto scritto.

`--elenchi` resta **spento di default**, e finché il §4.B non è recuperato è
giusto che lo resti: acceso, il bilancio su un manuale come FWK è negativo.
