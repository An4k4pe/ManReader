# Esito — la riparazione della regione, rimisurata: **CADE di nuovo**

Misura di `Criterio_RiparazioneRegioneIR2_v2.md`, 20 settembre 2026.
Prima: `output/resa/senza-riparo` (riparazione scollegata, schede collegate).
Dopo: `output/resa/verifica`, lo stato committato in `b26d245`.

## 1. La previsione era sbagliata, e per difetto

Avevo scritto al §3: «il veto scatta ancora, su **tre** regioni invece di
cinque», e che Dag idx 359 restava dubbio. Dei cinque casi nominati dalla v1:

| caso | previsto | misurato |
| --- | --- | --- |
| Dag idx 230 (stampata 229) | risolto dalle schede | **risolto** — la tabella non esiste piu', ne' con ne' senza |
| DB idx 43 (stampata 42) | veto | **veto** — entrano tre voci dell'elenco AZIONI |
| Dag idx 116 (stampata 115) | veto | **veto** — entrano sei nodi di prosa interi |
| Dag idx 311 (stampata 310) | veto | **veto** — entra il titolo `LA SCHEDA MADRE` e il paragrafo di Fase 2 |
| Dag idx 359 (stampata 358) | dubbio | **veto** — 99 primitive da 9 nodi, le schede dei compagni intere |

Quattro su cinque scattano ancora. Le schede ne risolvono uno solo, ed e' quello
che era una scheda per intero.

## 2. E il problema e' piu' grande dei cinque casi

`riparo_entrate.py` mostra che la riparazione allarga tabelle fantasma su pagine
che tabelle non ne hanno affatto. Tre pagine guardate sull'immagine:

- **Dag idx 311 (stampata 310)**: prosa e diagrammi, nessuna tabella. La
  riparazione tira dentro l'intestazione di capitolo e un paragrafo.
- **DB idx 43 (stampata 42)**: la scatola AZIONI e' un **elenco puntato a due
  colonne** dentro una cornice decorata, non una tabella. Nessuna tabella sulla
  pagina.
- **Dag idx 108 (stampata 107)**: due colonne di pura prosa — INTERLUDI, RIPOSO
  BREVE, RIPOSO LUNGO. Entrano **68 righe di prosa da 13 blocchi**.

La tabella fantasma su quelle pagine c'e' anche senza la riparazione: e'
`table_candidate` a proporre la regione. La riparazione non la crea, **la
gonfia** — ed e' questo che il veto vieta.

## 3. Una misura che ho scartato, e perche'

Avevo contato meccanicamente le pagine dove «due o piu' righe di sorgente di
prosa dello stesso blocco entrano in una tabella»: **84** (DB 32, Apo 10, Dag
42). **Quel numero e' sull'asse sbagliato e non va citato.** La riparazione
serve proprio a far entrare in tabella righe che prima erano paragrafi:
l'intestazione `D12 STIRPE` e l'ultima riga `12 Lupinide` erano nodi di prosa
per costruzione, e recuperarle e' il suo mestiere. Il veto della v1 non dice
«era un paragrafo prima», dice «la pagina lo stampa **fuori** dalla tabella», e
quello si giudica sull'immagine. Il conteggio conta insieme i successi e i
fallimenti.

## 4. Gli altri veti

- **A. Barra.** 1729 test verdi, Ruff pulito, barra E-B 9 su 10 con la sola Fab idx 126, quella gia' a verbale.
- **B. Nessuna primitiva esce da una tabella.** Regge: `senza-riparo ->
  verifica` da 0 ridotte e 0 sparite su tutti e tre i manuali. Le tabelle
  crescono e basta — DB 50, Apo 16, Dag 49, piu' 2 nuove su Dag.

## 5. La conseguenza, dichiarata prima

Il §3 del criterio diceva: «se la previsione e' giusta, il criterio cade di
nuovo e la conseguenza e' scollegare». **Scollegato**: `build_page_ir2` usa la
regione grezza.

Il codice resta in albero — non si cancella, si tagga. `_repaired_region`,
`_repair_region_y`, `_repair_region_x` e `_row_clusters` restano in
`ir2_builder.py` con i loro test, che ora applicano la funzione **direttamente**
invece che attraverso la pipeline.

**Scollegare non costa niente alle schede**, verificato: su Dag idx 230 la
pagina della sirena resta senza nessuna riga di tabella e la scheda si legge
uguale; su DB idx 123 la riga 11 dei tesori resta intera.

## 6. Che cosa resta da capire, e non e' la riparazione

Il difetto vero che questa misura ha messo in luce non e' suo: **`table_candidate`
propone regioni su pagine di pura prosa**. Dag idx 108 e' due colonne di testo e
ha una regione; DB idx 43 e' un elenco puntato in una cornice. La riparazione le
rende visibili perche' le allarga, ma toglierla le lascia li', piu' piccole.
