# RUNBOOK: convertire un manuale in Markdown con script e agenti

Chi orchestra (una sessione di Claude, o un agente orchestratore) segue questi passi. **Tutto il lavoro
meccanico lo fa `orchestra.py`**; gli agenti fanno solo giudizio, su compiti già scritti, e le loro consegne
sono **validate dallo script** prima di andare avanti. Lo stato sta in `<radice>/stato.json`: se il lavoro si
interrompe, si riprende dall'ultima fase fatta e dai lotti non `OK`.

```
O=~/Documenti/ManReader_prova/processo/orchestra.py
PY="/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python"
R=~/Documenti/ManReader_prova/<Nome>
```

| # | Chi | Comando / compito | Esce | Controllo prima di proseguire |
|---|---|---|---|---|
| 1 | script | `$PY $O init $R --pdf <pdf> --titolo "<titolo>" --lingua <lingua>` | `manuale.json` | pagine e segnalibri stampati |
| 2 | script | `$PY $O immagini $R` | `_lavoro/raw`, provini, compito `asset.md` | classi stampate |
| 3 | **agente** | `_lavoro/compiti/asset.md` | `script/classi_immagini.json`, `arredo.md` | il file esiste e ha `sfondo`/`decorazione`/`doppi` |
| 4 | script | `$PY $O profilo $R` | `inventario_glifi.json`, compito `profilo.md` | numero di glifi |
| 5 | **agente** | `_lavoro/compiti/profilo.md` (in parallelo al 3) | `profilo.json`, `decisioni.md` | ogni glifo ha una resa |
| 6 | script | `$PY $O bozza $R` | `immagini/`, `sfondi_e_ripetuti/`, `_lavoro/bozza/`, `smistamento.json` | segnaposto = occorrenze immagine |
| 7 | script | `$PY $O compiti $R` (tutte le pagine) oppure `--smistamento --campione 15` | `_lavoro/compiti/pagine_*.md`, `immagini_*.md` | numero di lotti |
| 8 | **agenti** | un agente per lotto, in parallelo (prompt sotto) | `_lavoro/finale/`, `_lavoro/note/`, `_lavoro/log/` | — |
| 9 | script | `$PY $O valida $R` | stato dei lotti | lotti `DA RIFARE` → rilanciare l'agente **con i problemi elencati** |
| 10 | script | `$PY $O assembla $R` | `<Titolo>.md`, `sfondi_e_ripetuti/INDICE.md` | 0 note mancanti, 0 segnaposto, 0 riferimenti rotti |
| 11 | orchestratore | verbale (`VERBALE.md`) dai log, da `stato.json` e dai controlli | | numeri solo misurati |

**Prompt per un agente di lotto** (passo 8, uno per file in `_lavoro/compiti/`):
> Leggi per intero e segui alla lettera `<radice>/_lavoro/compiti/<lotto>.md`. Scrivi ogni pagina (o nota)
> appena finita. Nella risposta finale: che cosa hai fatto, correzioni ricorrenti, scelte da uniformare.

**Rilancio di un lotto DA RIFARE** (passo 9): stesso agente se è ancora vivo (continuazione con contesto),
altrimenti nuovo agente con il compito e in più: "La validazione ha trovato questi problemi: <elenco da
stato.json>. Correggi solo quelli."

**Quando usare lo smistamento** (`--smistamento`): solo se sul campione di controllo del manuale la bozza è
già sufficiente (≥ 0,99) su almeno l'80% delle pagine; la validazione lo misura e lo stampa. Su Vileborn e
Draw Steel **non** lo era (65% e 45%): per un manuale nuovo si parte da tutte le pagine.

**Regole per l'orchestratore**
- Non riscrivere a mano le pagine degli agenti; se serve un'uniformazione, farla con uno script e
  registrarla in `_lavoro/log/uniformazione.md`.
- Criteri di accettazione scritti **prima** di guardare i dati; una misura fallita si riporta come fallita.
- Una scelta di formato che emerge da più lotti va in `decisioni.md` **prima** di lanciare i lotti successivi.
- Script temporanei degli agenti solo nella loro cartella `_lavoro/agenti/<lotto>/`.

**Banco di prova della bozza**: `$PY processo/script/valuta_bozza.py <etichetta>` rigenera la bozza di Candela,
Vileborn e Draw Steel e la confronta con le loro pagine rivedute. Va lanciato dopo ogni modifica agli script
della bozza; un peggioramento su un manuale è una regressione anche se un altro migliora.

**Prima di modificare uno script: controllare ManReader** (regola aggiunta il 28 set 2026, dopo che i
marcatori `h` di Vileborn sono stati riscritti da zero benché ManReader li avesse già risolti).
Chi cambia uno script della bozza cerca prima in ManReader un criterio o un modulo per lo stesso problema
e registra l'esito in `CONSULTAZIONI_MANREADER.md` **prima** di scrivere codice: che cosa ha cercato, dove,
che cosa ha trovato, se l'ha ripreso, adattato o scartato e perché. "Non c'è niente" vale solo con la
ricerca fatta scritta accanto. Dove cercare:
- `Criterio_*.md` e `Esito_*.md` nella radice di ManReader **e nei worktree** `.claude/worktrees/*/`
  (molti criteri non sono committati: le tabelle stanno in `table-region-producer-005fb8`);
- moduli: `ir2_builder.py` (rottura di paragrafo, tabelle), `document_list_policy.py` (elenchi e
  marcatori), `epub_builder.py` (sillabazione), `page_analysis_*`, `scripts/prototype_*`;
- `State.md`, sezione pertinente (mai `State_Archive.md`).
