# Prompt di apertura — chat dedicata alle schede statistiche, bersaglio IR 2

Da incollare come primo messaggio di una chat nuova. Scritto il 10 settembre 2026
alla chiusura della sessione precedente.

---

Devi chiudere il riconoscimento delle **schede statistiche** dei manuali TTRPG e
farle uscire in Markdown attraverso **IR 2**, che è il percorso di produzione.

## Leggi prima queste cose, in quest'ordine

1. `CLAUDE.md` e `AGENTS.MD` per intero (invarianti e vincoli).
2. `ManReader_TwoChat_Agent_Workflow.md` (ruoli e formati).
3. Di `State.md`: la sezione **«Schede statistiche — lavoro esplorativo»** e le
   voci **Milestone 43 e 44** sul ramo IR 2. Non il file intero.
4. `esperimenti_statblock/PASSAGGIO_DI_CONSEGNE.md` (il metodo, fino al 5
   settembre) e `PASSAGGIO_DI_CONSEGNE_2.md` (cosa è successo dopo, gli errori,
   l'ordine di ripartenza).

**Non leggere `State_Archive.md`.**

## Dove sta cosa: i rami non sono uno

- `claude/statblock-asset-class-yf3y9c-2054f9` — il lavoro sulle schede,
  cartella `esperimenti_statblock/`. Nulla è wired.
- `claude/asset-note-visibility-e14deb` — **IR 2** (`ir2_builder`,
  `ir2_markdown`, `main_ir2`) e le Milestone 38-42. **C'è una sessione che ci
  lavora: non committarci sopra.**
- `claude/ir2-porta-42-43` — le milestone sull'ordine di lettura portate su IR 2
  più l'innesto dei confini di Resolution. **È la base da cui partire.**

Prima di numerare una milestone controlla i numeri **su tutti i rami**: due
Milestone 42 diverse esistono già, ed è costata una rinumerazione.

## Il compito, in due parti

**A. Portare il riconoscimento delle schede su IR 2.** Oggi
`esperimenti_statblock/markdown_ir.py` produce Markdown attraverso **IR 1** ed è
un secondo percorso. Non estenderlo: il lavoro va rifatto consumando IR 2. Il
precedente da imitare è come i confini di colonna sono arrivati a
`ir2_builder` — un solo innesto in `scripts/prototype_ir2_page.py`, da cui
`main_ir2.py` importa, con confronto prima/dopo su un intervallo di pagine.

**B. Chiudere i punti aperti del riconoscimento**, nell'ordine sotto.

## Cosa è già stabilito: NON rifarlo, e non ri-misurarlo

- **Le basi riproducono.** `pila.py` congelato riproduce `out_pila.txt` riga per
  riga sul manuale 1 (474 record, 148/148) e riproduce il fallimento documentato
  sul manuale 2.
- **I confini di una scheda non si deducono, si leggono.** Il riquadro è
  disegnato sulla pagina, e i producer che lo trovano (`embedded_visual`,
  `interior_visual_frame`) sono wired da Milestone 28 e 31. Consumandoli, le
  schede escono cominciando dal nome **4 volte su 4**, contro 2 su 4 della pila
  di testa che contava righe.
- **Il criterio di riconoscimento non passa dalla frequenza**: un riquadro che
  contiene almeno **due righe con almeno due coppie etichetta/valore**. È
  `State.md:903` alla lettera. Su un manuale intero: 4 schede vere, 1 falso
  positivo. La frequenza serve solo a dare un **nome** al template.
- **La misura di copertura è accettata** (`copertura.py`): sul rilevatore
  congelato produce due righe su 47 pagine e la prima sono le quattro schede
  sulle pagine esatte della verità. Usala come allarme, non ricostruirla.
- **Le correzioni 2 e 3 sono state fatte e NON accettate.** Leggi perché prima di
  riproporle.
- **L'ordine di lettura non è più il collo di bottiglia.** Misurato: il danno
  reale è fra lo 0% e il 5,2% del testo di pagina, non il 90% che sembrava.

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
   dell'obiettivo** (`AGENTS.MD` §Obiettivo). Lo stesso riquadro che dà i confini
   è l'asset da sostituire con una nota: un oggetto, due ruoli. Misurate 4.208
   sovrapposizioni regione × visuale: non è un caso raro.
5. **Il terzo manuale.** `Draw Steel: Monsters` (385 pagine, sistema mai usato) è
   **sigillato**. Si apre solo alla fine e solo col criterio di accettazione già
   scritto.

## Le regole che questa linea di lavoro ha violato più spesso

- **Il criterio si scrive prima di guardare i dati**, con la predizione e il modo
  di falsificarla. Su questo progetto sei predizioni su dieci sono cadute, e ogni
  caduta ha insegnato qualcosa: senza registrarle sarebbero passate per successi.
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

Parti dal ramo `claude/ir2-porta-42-43`, esegui
`main_ir2.py <manuale> --out <dir> --pages <intervallo> --tabelle` su alcune
pagine di bestiario, e **guarda cosa esce oggi** per una scheda. Quello è il
punto di partenza reale: non il rilevatore, ma la pagina resa. Poi decidi se il
primo lavoro è il riconoscimento o la resa, e dillo prima di cominciare.

I manuali stanno in `PASSAGGIO_DI_CONSEGNE_2.md` §0, con i percorsi locali.
