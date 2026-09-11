# La scheda e il suo nome in IR 2 — criterio pre-registrato (passo 3a)

Ordine deciso con l'utente il 10-11 settembre 2026: **3a** la scheda e il suo
nome, **3b** la nota dello sfondo, **3c** le righe dentro la scheda. Il
riconoscimento e' quello che gli esperimenti hanno accettato
(`esperimenti_statblock/RISULTATI_SEPARA_RIQUADRI.txt`); il passo 2, una coppia
per riga, non e' stato accettato (`RISULTATI_UNA_COPPIA.txt`), e gli ambienti di
Daggerheart restano scoperti per decisione dell'utente.

## L'innesto
- **`stat_block_regions.py`, modulo nuovo, consumer.** La separazione dei
  riquadri fusi (spostata da `esperimenti_statblock/riquadri.py`), le coppie
  etichetta/valore per riga (la regola di `pila2.etichette`, sulle primitive IR
  2), le regioni scheda, le righe del nome. Nessun producer toccato.
- **`scripts/prototype_ir2_page.py`**, da cui `main_ir2.py` importa: un punto
  solo, che calcola le schede e passa al costruttore le righe del nome.
- **`ir2_builder.build_page_ir2`**: ingresso facoltativo `stat_block_names`. Se
  vuoto l'uscita e' identica a oggi. Le righe del nome diventano **un** nodo
  `text.heading`, e il paragrafo si chiude prima e dopo di esse.
- **Livello del titolo**: uno sotto il piu' profondo delle fasce di titolo gia'
  dedotte per il documento (`DocumentScan.heading_levels`); senza fasce, 1. Non
  un numero fisso.
- **Con `--tabelle`**: una regione tabella che si sovrappone a una scheda senza
  starci dentro non si costruisce. Una tabella dentro la scheda resta.

Nessun cambio al contratto IR 2 (il titolo e' un `text.heading`, che esiste
gia'), nessuna soglia nuova.

## Cosa NON fa
La nota dello sfondo (3b); la segmentazione delle righe dentro la scheda (3c);
gli ambienti a una coppia per riga; la provenienza del titolo sul nodo
(`candidate_ids`), rinviata a 3b, che tocca comunque il contratto.

## Predizioni
- **R1, conteggi.** Il riconoscimento in IR 2 riproduce le regioni della misura
  d'esperimento (riquadri separati, tabelle escluse): **130** su Daggerheart
  idx 36-56, cioe' 129 avversari (idx 37-50) e un ambiente (idx 55); **6** su
  Dragonbane (idx 13 AZIONI, 29, 31, 32 GRUB, 33, 35). Su DB 95-125 il numero
  non e' predetto e si riporta. Se i primi due differiscono, si spiega prima di
  andare avanti: le righe IR 2 e le righe di `pila2` sono costruite in modo
  simile ma non identico.
- **R2, nomi.** Ogni regione ha un nome e il titolo emesso e' il nome della
  scheda: 130 su 130 e 6 su 6, controllati sul testo dei titoli.
- **R3, la condizione.** Su Daggerheart 36-56, Dragonbane intero e DB 95-125,
  senza `--tabelle`, le pagine senza schede sono **identiche byte a byte**, e
  cambiano **esattamente** le pagine dove il riconoscimento trova almeno una
  scheda.
- **R4, conservazione.** Su ogni pagina che cambia, i caratteri non-spazio del
  Markdown, tolti `#` e `*`, sono gli stessi prima e dopo.
- **R5, con `--tabelle`.** La stessa condizione di R3; in piu' si riporta quante
  regioni tabella non si costruiscono per la precedenza della scheda.
- **R6, E-B** (`scripts/check_eb.py --pdf-dir .`), obbligatoria perche' il diff
  tocca `ir2_builder.py`: nessuna differenza nuova rispetto al verbale (Fab idx
  126, gia' spiegata).
- **R7, test.** Suite completa verde, piu' i test nuovi del modulo e del
  costruttore; Ruff e BasedPyright puliti sui file toccati.

## Accettazione
R3 e' la condizione: **una sola pagina che cambia senza schede, e l'innesto non
si adotta.** R1, R2, R4 e R7 si verificano; R5 e R6 si riportano. Poi il
giudizio a vista dell'utente su alcune pagine che cambiano, piu' una di
controllo, prima del commit.

Il legacy non si tocca, nessun default si sposta, e i test esistenti di
`ir2_builder` devono restare verdi senza essere modificati.
