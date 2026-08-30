# ManReader

**Obiettivo, da rileggere e non da ricordare** (`AGENTS.MD` §Obiettivo per
intero): PDF TTRPG → Markdown ed EPUB **semantici**, contenuto preservato;
immagini, sfondi ed elementi ripetuti **sostituiti da note brevi che dicono cosa
sostituiscono**, con gli asset in una cartella referenziata. Ogni scelta si
giudica contro questo, non contro la coerenza interna del meccanismo su cui si
sta lavorando: e' la domanda che ferma un giro di rifinitura che non avvicina un
EPUB.

Leggi `AGENTS.MD` (invarianti e vincoli) e `ManReader_TwoChat_Agent_Workflow.md`
(ruoli e formati) prima di proporre qualunque cosa. Per lo stato corrente, la
sezione pertinente di `State.md`, non il file intero.

**Non leggere `State_Archive.md`**: dettaglio narrativo di milestone chiuse,
costa molto e non serve alle decisioni correnti.

- `--page N` negli script diagnostici è un indice **posizionale** (`page_index =
  N - 1`), non il numero stampato. Lo scostamento varia per manuale e non è
  lineare. Verifica con un render prima di citare qualunque risultato di pagina.
- **Ma il numero stampato è quasi sempre un dato che hai, non una cosa da
  indovinare.** `page.get_label()` lo dichiara su **13 manuali su 16** — tutti
  tranne FW, FWK e Wil — e su quei tre lo deduce `deduced_number_slots`
  (rispettivamente 20/20, 18/20 e 20/20 su una finestra di venti pagine). Cita il
  numero stampato **accanto** all'indice: lasciare all'utente un indice
  posizionale da tradurre a mano è un costo che non serve pagare.
- Python: `./venv/bin/python`. Test: `python -m unittest`.
- Prima di un giro di misure, dichiara scopo e criterio di accettazione **per
  iscritto e prima di guardare i dati**. Una misura che conferma chi l'ha
  progettata va trattata come non verificata finché qualcuno non guarda le
  pagine.
- **Un veto che cade apre la diagnosi, non la chiude.** Il criterio si dichiara
  prima e non si ritocca per far passare un risultato: quello resta. Ma prima di
  ritirare un meccanismo, guarda **perché** è caduto e stabilisci **che cosa** è
  caduto — un veto scritto nella moneta sbagliata, o su una popolazione tracciata
  sull'asse sbagliato, cade su se stesso e non dice niente sul meccanismo. Allora
  il criterio si emenda, l'emendamento si dichiara, il giudizio si rifà, e a
  verbale si scrive che è stato emendato e perché.

  La prova che separa l'emendamento lecito dal salvataggio: **deve reggere senza
  sapere se il meccanismo poi passa.** Se l'unica ragione per cambiarlo è che
  altrimenti il risultato non passa, è un salvataggio.

  Le due cadute del 30 agosto 2026 sono cadute così, e nessuna delle due diceva
  quello che ho scritto che diceva: `Criterio_TitoloSopraIlParagrafo_v1` §3
  tracciava la popolazione **per manuale** — fuori DrM e DrW — quando il
  confondente è **per pagina**, e le schede stanno dentro i manuali contati;
  `Criterio_MarcatoreDaFont_v2` §3.A vietava sui **caratteri** quando la v1 era
  stata scaricata sulle **voci prodotte**.
