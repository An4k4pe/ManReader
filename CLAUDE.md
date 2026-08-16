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
- Python: `./venv/bin/python`. Test: `python -m unittest`.
- Prima di un giro di misure, dichiara scopo e criterio di accettazione **per
  iscritto e prima di guardare i dati**. Una misura che conferma chi l'ha
  progettata va trattata come non verificata finché qualcuno non guarda le
  pagine.
