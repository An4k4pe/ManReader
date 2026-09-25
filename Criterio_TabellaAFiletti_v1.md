# Criterio — una tabella è ciò che i filetti risolvono

Dichiarato il 25 settembre 2026, **prima** della misura decisiva. Richiesta
dell'utente: «tabelle deve stare acceso, poi muoviti verso le tabelle fantasma».

## 0. Il problema, e perché ora conta

Le tabelle sono accese di default da `c19324d`. `table_candidate` cerca le
colonne con la strategia **a testo** di pdfplumber (`vertical_strategy: "text"`,
`horizontal_strategy: "lines"`): le colonne sono dove il testo si allinea, le
righe dove c'è un filetto. Su una pagina a due colonne di prosa con un filetto di
separazione, quella strategia vede una tabella: due colonne, qualche riga. Visto
in questa sessione, sull'immagine:

| pagina | che cos'è davvero |
| --- | --- |
| Dag idx 108 (stampata 107) | due colonne di pura prosa, INTERLUDI |
| DB idx 43 (stampata 42) | la scatola AZIONI, un elenco puntato in cornice |
| Dag idx 15 (stampata 14) | le opzioni di classe, titoli e schede illustrate |
| Dag idx 311 (stampata 310) | prosa e diagrammi, nessuna tabella |
| Dag idx 50 (stampata 49) | la scheda del compagno del Ranger |

Su ognuna la resa costruisce una tabella, e la prosa diventa righe di una
griglia che non esiste.

## 1. Da dove viene l'idea — non è nuova

`Criterio_TabellaRisolvibile_v1.md`, registrato il 20 agosto e **mai eseguito**:
«una regione che una strategia a **filetti** risolve con celle piene è una
tabella». Nell'esplorazione di allora le tabelle vere davano 100% di celle piene
e i pannelli 0%. La soglia — **80%** di celle non vuote — fu fissata allora,
«in mezzo a quel divario, non tarata sul risultato». Qui non la ritocco.

## 2. L'esplorazione di oggi, con le etichette fissate prima

`output/resa/filetti.py`, sulle dieci pagine guardate a vista in questa sessione.
Per ogni regione di `table_candidate`, `find_tables` con la strategia di default
(a filetti) sul ritaglio della regione:

| pagina | etichetta a vista | griglie a filetti |
| --- | --- | --- |
| Dag idx 108 | fantasma | **nessuna** |
| DB idx 43 | fantasma | 9%, 0% |
| Dag idx 15 | fantasma | **nessuna** |
| Dag idx 311 | fantasma | **nessuna** |
| Dag idx 50 | fantasma | 7%, 50%, 0% |
| Dag idx 120 | vera, armi | **100%** |
| Dag idx 324 | vera, armi | **100%** |
| DB idx 123 | vera, tesori | **100%** |
| DB idx 90 | vera, D6 ATTACCO | **100%** |
| Wil idx 137 | mista: INGREDIENTI vera | **86%** |

Dieci su dieci. Ma sono dieci pagine scelte da me, e una misura che conferma chi
l'ha progettata va trattata come non verificata: decide il paragrafo 5.

## 3. La regola

1. **Producer** `page_analysis.ruled_table`: `find_tables` con la strategia a
   filetti sulla pagina; ogni griglia con **almeno due celle** e **almeno l'80%**
   di celle non vuote è un candidato `layout.ruled_table`.
2. **Consumer**, terza regola di `resolve_page_candidates`: un candidato di
   `table_candidate` è **accettato** se contiene il centro di almeno una griglia a
   filetti, **respinto** (`not_resolved_by_rules`) altrimenti. Senza l'analisi a
   filetti la regola tace, e il comportamento di prima non cambia.
3. **`run()`**: a tabelle accese costruisce l'analisi a filetti, e una regione
   respinta non diventa tabella — il suo testo resta prosa.

La regione della tabella resta quella di `table_candidate`: questo giro decide
**se** c'è una tabella, non **dove** finisce. Le tabelle miste — Wil idx 137,
INGREDIENTI vera e TRATTI no — restano miste.

## 4. La popolazione

Nove manuali — DB, Apo, Dag, Wil, BiD, DIE, SV, Kul, Vil — resi con i
predefiniti (tabelle e schede accese). Riferimenti: `output/resa/nucleo2/{Dag,Wil}`
e `output/resa/nucleo/sempre-*` / `muta-*` per gli altri.

## 5. Che cosa deve succedere perché passi

**A. Le tabelle che spariscono sono fantasmi.** Ogni tabella che sparisce si
guarda sull'immagine. Se sono più di 40, si guardano tutte quelle di DB, Dag e
Wil fino a 20, e poi una ogni *k* delle altre in ordine di manuale e pagina fino
a 40.

**B. Veto: nessuna tabella vera sparisce.** Una tabella che la pagina stampa come
tabella e che non esce più è il veto. Il rischio è noto in anticipo: una tabella
vera **senza filetti né righe ombreggiate** — solo testo allineato — la strategia
a filetti non la trova.

**C. Le tabelle che restano non cambiano.** Il markdown delle tabelle non sparite
è identico al riferimento: la regola decide solo se una regione è tabella.

**D. Nessuna prosa tagliata.** I paragrafi che cominciano in minuscola non
salgono.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab idx 126.

## 6. La previsione

- **Dag e DB perdono molte tabelle, e sono fantasmi**: le pagine di sola prosa e
  i riquadri.
- **Il veto è probabile su un manuale a tabelle senza filetti**: non so quale.
  Apocalisse ha le tabelle `COMPLICAZIONI`, e non ricordo se hanno righe
  ombreggiate. Se il veto scatta lì, la v2 è una seconda strada per le tabelle a
  testo allineato, non l'abbandono di questa.
