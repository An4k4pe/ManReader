# Criterio — le schede arrivano a IR 2 dal producer, non dal canale laterale

Dichiarato il 20 settembre 2026, **prima** della misura.

## 0. Che cosa cambia

Oggi le aree di scheda si calcolano in `main_ir2.py` — prima passata sulle righe
dell'ordine di lettura, `recurring_field_combinations`, poi
`field_line_indices` dentro `run()` — e si passano a `build_page_ir2` come
parametro. Dal commit `e964b04` esiste `page_analysis.stat_block`, che le
propone come **candidati di pagina**.

Il lavoro porta le schede sulla strada dell'architettura:

1. **policy di documento** (`document_stat_block_measurements.py` +
   `document_stat_block_policy.py`): quali combinazioni di etichette il
   documento ripete e mette sempre nello stesso posto. Stessa forma di
   `heading_bands`: si misura una volta sulle pagine catturate e si passa giu'.
2. **consumer** (`resolution_page_candidates.py`): un candidato `layout.stat_block`
   e' accettato se porta una combinazione ammessa dalla policy, respinto
   altrimenti.
3. **wiring IR 2**: `run()` costruisce le aree dai candidati **risolti** invece
   che chiamando `stat_block_field_lines`.

## 1. Il cambio che puo' spostare il risultato, dichiarato adesso

La strada di oggi conta le righe nell'**ordine di lettura** (`stat_block_inputs`
sulla catena di lettura, che vuole pdfplumber e costa una passata intera). Il
producer e la policy nuovi contano le righe dal **`source_observation_id`**,
come fa gia' `page_analysis_column_band`.

Sono due nozioni di «riga» diverse, e possono dare combinazioni diverse. Se le
danno, l'uscita cambia. Non lo so prima di misurare, e lo scrivo qui perche' non
sembri una sorpresa dopo.

La strada dei **riquadri disegnati** resta dov'e', sulla catena di lettura:
questo giro non la tocca.

## 2. Che cosa deve succedere perche' passi

Resa di DB, Apo e Dag con `--tabelle --schede-campi`, confrontata con
`output/resa/senza-riparo`, cioe' lo stato committato in `d59a22f`.

**A. L'uscita non cambia.** Markdown e IR 2 identici byte a byte sui tre
manuali. E' il caso che ci si aspetta se le due nozioni di riga coincidono dove
conta.

**B. Se cambia, il cambiamento si giudica.** Ogni tabella che cambia e ogni
pagina di scheda che cambia si guardano sull'immagine, con lo stesso giudizio di
`Criterio_SchedaControLaTabella_v1.md`: **meglio** se una riga di scheda esce da
una tabella che la pagina stampa fuori, **peggio** se una riga che la pagina
stampa dentro una tabella ne esce. Passa se meglio > peggio e se nessuna scheda
vera sparisce.

**C. Le sei tabelle gia' giudicate restano come sono.** DB idx 87, 90, 97 e
123; Dag idx 230 e 359.

**D. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab
idx 126.

**Veto.** Se la tabella dei tesori di DB idx 123 torna a perdere righe, la
policy non sta applicando il requisito posizionale e il wiring e' sbagliato.

## 3. Che cosa questo giro NON fa

- Non toglie `stat_block_field_lines.recurring_field_combinations`: resta finche'
  la strada vecchia non e' spenta, e le due devono poter convivere per essere
  confrontate.
- Non sposta la strada dei riquadri nel producer. Un riquadro disegnato e' un
  candidato di un altro producer, e vederlo tocca al consumer: e' un giro a
  parte.
- Non fa girare `page_analysis.stat_block` dentro `job_page_analysis_runner`
  nella resa: `main_ir2` costruisce i candidati chiamando il producer
  direttamente, come fa gia' per gli altri.
