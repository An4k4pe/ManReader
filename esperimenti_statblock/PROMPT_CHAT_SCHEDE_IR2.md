# Prompt di apertura — chat dedicata alle schede statistiche, bersaglio IR 2

**Da incollare come primo messaggio di una chat nuova.** Scritto il 10 settembre
2026. È autosufficiente: contiene percorsi, comandi e numeri, e non dipende dal
ritrovare altre conversazioni.

---

Devi chiudere il riconoscimento delle **schede statistiche** dei manuali TTRPG e
farle uscire in Markdown attraverso **IR 2**, che è il percorso di produzione.

## Dove sei, e cosa fare per prima cosa

Il repository è un worktree di `/home/an4k4pe/Documenti/ManReader (Copia)`.
Il ramo da cui partire è **`claude/ir2-porta-42-43`**: contiene IR 2, le milestone
sull'ordine di lettura e la cartella `esperimenti_statblock/` con tutto il lavoro
sulle schede.

    git checkout claude/ir2-porta-42-43

Python e strumenti (**non** usare `python` di sistema):

    "/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python"   # 3.14, PyMuPDF 1.28
    "/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/ruff" check <file>
    "/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/basedpyright" <file>
    ./venv/bin/python -m unittest        # 1671 test verdi su questo ramo

I manuali **non stanno nel repository** (`*.pdf` è gitignorato). Percorsi locali:

    manuale 1, banco di sviluppo — su cui il metodo è stato progettato, NON valida
      /home/an4k4pe/Documenti/KDrive/ManualiGdr/DaggerHeart/Daggerheart-SRD-9-09-25.pdf
      (868 KB, 68 pagine)

    manuale 2, bruciato dal test di validazione
      /home/an4k4pe/Documenti/KDrive/ManualiGdr/Dragonbane/Dragonbane-Quickstart-jxfem8_647f908c2f17e.pdf
      (47 pagine)

    terzo manuale — SIGILLATO, non aprirlo se non alla fine e col criterio scritto
      /home/an4k4pe/Documenti/KDrive/ManualiGdr/Draw_Steel_Monsters_v1.01.pdf
      (385 pagine, sistema mai usato, bestiario numeroso)

    benchmark del repo (DB, Fab, Dag, Apo, Lan…) in
      /home/an4k4pe/Documenti/ManReader (Copia)/*.pdf
    Per farli vedere al worktree basta un symlink: cadono sotto `*.pdf` del
    .gitignore e non entrano nel diff. Un test ne ha bisogno (`Dag.pdf`).

## Leggi prima queste cose, in quest'ordine

1. `CLAUDE.md` e `AGENTS.MD` per intero (invarianti e vincoli).
2. `ManReader_TwoChat_Agent_Workflow.md` (ruoli e formati).
3. Di `State.md`: la sezione **«Schede statistiche — lavoro esplorativo»** e le
   voci **Milestone 43 e 44**. Non il file intero. `State.md` finisce con una
   riga sentinella: se non la ricevi, la tua copia è troncata, fermati e dillo.
4. `esperimenti_statblock/PASSAGGIO_DI_CONSEGNE.md` (il metodo, fino al 5
   settembre) e **`PASSAGGIO_DI_CONSEGNE_2.md`** (cosa è successo dopo, gli
   errori commessi, l'ordine di ripartenza).

**Non leggere `State_Archive.md`**: è dettaglio narrativo di milestone chiuse,
costa molto e non serve.

## I rami non sono uno, e i numeri collidono

- `claude/ir2-porta-42-43` — **la tua base**. IR 2 più le milestone 43 e 44.
- `claude/asset-note-visibility-e14deb` — IR 2 e le Milestone 38-42. **C'è una
  sessione che ci lavora: non committarci sopra.**
- `claude/statblock-asset-class-yf3y9c-2054f9` — l'origine del lavoro sulle
  schede. La cartella `esperimenti_statblock/` è la stessa che hai già.

Prima di numerare una milestone controlla i numeri **su tutti i rami**. È già
successo il contrario: due Milestone 42 diverse, nate su rami che non si
conoscevano, e la rinumerazione ha toccato una quindicina di file su due rami.
Le milestone sull'ordine di lettura sono la **43** e la **44** ovunque.

## Il compito, in due parti

**A. Portare il riconoscimento delle schede su IR 2.** Oggi
`esperimenti_statblock/markdown_ir.py` produce Markdown attraverso **IR 1** ed è
un secondo percorso: non estenderlo. Il precedente da imitare è come i confini di
colonna sono arrivati a `ir2_builder` — **un solo innesto** in
`scripts/prototype_ir2_page.py`, da cui `main_ir2.py` importa, con confronto
prima/dopo su un intervallo di pagine e verifica che cambino **solo** le pagine
che devono cambiare.

**B. Chiudere i punti aperti del riconoscimento**, nell'ordine più sotto.

## Cosa è già stabilito: NON rifarlo e non ri-misurarlo

- **Le basi riproducono.** `pila.py` congelato riproduce `out_pila.txt` riga per
  riga sul manuale 1 (474 record, 148/148) e riproduce il fallimento documentato
  sul manuale 2 (34 etichette di schema, 16 gruppi).
- **I confini di una scheda non si deducono, si leggono.** Il riquadro è
  disegnato sulla pagina, e i producer che lo trovano (`embedded_visual`,
  `interior_visual_frame`) sono wired da Milestone 28 e 31. Consumandoli, le
  schede escono cominciando **dal nome 4 volte su 4**, contro 2 su 4 della pila
  di testa che contava righe.
- **Il criterio di riconoscimento non passa dalla frequenza**: un riquadro che
  contiene almeno **due righe con almeno due coppie etichetta/valore**. È
  l'appunto di `State.md` sulle schede alla lettera. Su un manuale intero: 4
  schede vere, 1 falso positivo. La frequenza serve solo a dare un **nome** al
  template.
- **La misura di copertura è accettata** (`esperimenti_statblock/copertura.py`):
  eseguita sul rilevatore congelato — cioè sul giro che aveva fallito **in
  silenzio** — produce due righe su 47 pagine, e la prima sono le quattro schede
  mostro sulle pagine esatte della verità. Usala come allarme, non ricostruirla.
- **Le correzioni 2 e 3 sono state fatte e NON accettate.** Leggi perché prima di
  riproporle: due predizioni su quattro cadute, e sotto la causa diagnosticata ce
  n'era una seconda mai isolata.
- **L'ordine di lettura non è più il collo di bottiglia.** Misurato: il danno
  reale (testo affiancato letto senza colonne) è fra lo **0% e il 5,2%** del
  testo di pagina, non il 90% che sembrava.
- **Le tabelle dentro le schede sono migliorate**: Resolution ammette ora la
  colonna dei numeri di dado come separatore, e `ir2_builder` la consuma. Su DB
  `| D20 TESORO | VALORE |` è diventato `| D20 | TESORO | VALORE |`.

## I punti aperti, in ordine

1. **Correzione 1, la co-occorrenza.** Mai fatta, e la sua valutazione è oggi
   **inquinata**: il template si forma da solo per un conteggio gonfiato da
   occorrenze che schede non sono. Criterio proposto, da registrare prima di
   eseguire: dopo la co-occorrenza la firma `Ferocia/Taglia/Resistenza` deve
   **spostarsi** dal residuo a template, e **nessun'altra** firma residua deve
   farlo.
2. **Il titolo centrato sopra due colonne.** La pila di testa non può
   raggiungerlo contando righe; il riquadro sì. Proposta: la pila serve dove il
   riquadro non c'è, non al posto suo.
3. **La regola di non-perdita spara nel posto sbagliato**: le uniche quattro
   regioni «struttura non riconosciuta» emesse sono righe di prosa che cominciano
   con la parola *Dragonbane*. Va ristretta a ciò che ha davvero forma di record.
4. **Lo sfondo decorativo della scheda come nota.** Non fatto, ed è **metà
   dell'obiettivo** (`AGENTS.MD` §Obiettivo: immagini, sfondi ed elementi
   ripetuti sostituiti da note brevi, con gli asset in una cartella
   referenziata). Lo stesso riquadro che dà i confini è l'asset da sostituire:
   un oggetto, due ruoli. Misurate 4.208 sovrapposizioni regione × visuale.
5. **Il terzo manuale.** Si apre solo alla fine e solo col criterio di
   accettazione già scritto.

## Le regole che questa linea di lavoro ha violato più spesso

- **Il criterio si scrive prima di guardare i dati**, con la predizione e il modo
  di falsificarla. Sei predizioni su dieci sono cadute, e ogni caduta ha
  insegnato qualcosa: senza registrarle sarebbero passate per successi.
- **Nessuna soglia cablata.** I confini si deducono dal documento. E se una
  costante esiste già per un'altra grandezza, non riusarla per la tua: una soglia
  «5 caratteri per riga» non è una soglia «5 caratteri sommati».
- **`pila.py` è congelato.** Se lo modifichi, dichiaralo e sappi che il confronto
  con i giri precedenti non vale più.
- **Una implementazione sola.** Prima di scrivere un meccanismo, cerca se esiste
  già: `ir2_builder.build_table` raggruppa già le righe di tabella per
  sovrapposizione verticale, e un modulo che rifaceva la stessa cosa è stato
  scritto prima di accorgersene.
- **Di' nel messaggio ogni strada che apri e chiudi**, e porta le decisioni con
  più esiti difendibili **prima**, non dopo.
- **Niente commit automatici**, niente `git add .`, e output/dump non committati.

## Le trappole misurate, dove la sessione precedente ha sbagliato

- **Misurare su un manuale solo**: una regola era 14 su 14 su DB e apriva 33
  elenchi puntati come colonne su Apo. La differenza non era tipografica ma di
  **estrazione** — su DB quei fianchi sono span vuoti, su Apo un glifo vero.
- **Generalizzare da tre casi ispezionati**: quindici pagine marcate a mano
  dall'utente hanno ribaltato la conclusione, 10 corridoi su 10.
- **Riportare numeri non misurati**: «alto ~2 righe» era dedotto; il valore vero
  era a **sei centesimi di punto** dalla soglia, e il numero inventato nascondeva
  il fatto interessante.
- **Chiedere il giudizio a vista**, e chiedere anche pagine di **controllo** dove
  il meccanismo dovrebbe funzionare: senza, si misurano solo i casi che
  confermano.

## Primo passo suggerito

Non partire dal rilevatore: parti dalla **pagina resa**.

    ./venv/bin/python main_ir2.py <manuale>.pdf --out /tmp/prova \
        --pages <intervallo> --tabelle --processi 4

Prendi un intervallo che contenga schede di bestiario, guarda il `page_ir2.md`
che ne esce, e **di' cosa vedi** prima di proporre qualunque cosa. Da lì decidi
se il primo lavoro è il riconoscimento o la resa — e dillo prima di cominciare.
