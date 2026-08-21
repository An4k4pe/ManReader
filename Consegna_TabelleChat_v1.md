# Consegna — dove sta il lavoro sulle tabelle

Per chi riprende in una chat nuova. Leggere prima `CLAUDE.md`, `AGENTS.MD` e
`ManReader_TwoChat_Agent_Workflow.md`; di `State.md` la sola Milestone 39.

---

## 1. Lo stato in cinque righe

Il branch è `claude/table-region-producer-005fb8`, portato in fast-forward a
`a2f5e18`. **Niente è committato.** Il lavoro ha prodotto tre criteri
pre-registrati, quattro esiti, sei script diagnostici e prototipi, e una revisione
indipendente che ha trovato dieci rilievi, dei quali **tre verificati da Chat A**
e non ancora corretti nel codice.

## 2. Che cosa è stato deciso, con la misura

**`Criterio_TabellaNormale_v1.md` è stato eseguito e CADE**
(`Esito_TabellaNormale_v1.md`): la configurazione del producer wired
(`text/lines` + riparazioni + modello a spina) dà **zero tabelle corrette su tre**
etichettate normali in un campione cieco di 60 pagine. Zero falsi negativi: il
difetto è la qualità, non la copertura.

**`Criterio_EstensioneRegioneTabella_v1.md` è caduto due volte**
(`Esito_EstensioneRegioneTabella_v1.md`), la seconda dopo che l'utente aveva
corretto l'implementazione della sua stessa regola.

**Un meccanismo nuovo esiste e non ha criterio.**
`scripts/prototype_table_max_columns.py`: la tabella è dove si forma il maggior
numero di colonne coerenti, poi si estende con le due regole dell'utente. Su 16
tabelle vere ne fa 13 giuste, **ma quel 13 è un fit**: sei regolazioni sono state
aggiunte una per pagina su sei di quelle pagine.

## 3. I tre rilievi verificati e NON corretti

1. **`coherence` è calcolato sul seme, non sulla regione emessa**
   (`prototype_table_max_columns.py`, `evaluate` → riga 236 → riga 304). Il §3 del
   verbale è già stato ritirato. Il candidato di sostituzione, non pre-registrato:
   il **minimo** fra le colonne sulla regione finale.
2. **Variabili ombreggiate in `_blockers`**
   (`prototype_table_gutter_extension.py:119-120` contro `:208`): `width` e
   `height` di pagina vengono riassegnate nel ciclo sui disegni. Fino a due terzi
   dei bloccanti persi su pagine con arredo pesante. Latente sulle pagine provate.
3. **La velocità dichiarata era falsa.** Chat A aveva scritto «55 s a pagina» e
   «sei ore per un manuale»: misurato, **1,7 s a pagina**, 171 s per 120 pagine.
   Il numero era stato dedotto da una durata d'orologio, mai cronometrato.
   Nessuna ottimizzazione serve.

Altri sette rilievi della revisione **non verificati da Chat A**: lo scarto del
bordino non scatta su BoB pag239; `analyse` emette una sola regione per pagina
(Lan pag52 ne perdeva una); quattro pagine di sviluppo mancano dalle esclusioni
(DB 61, Lan 18, Lan 51, Wil 77); `bonus` nel punteggio premia l'adozione del
gutter di pagina; `columns` e `MIN_WIDTH` non sono riverificati dopo il
restringimento; 33 regioni su 107 hanno un «gutter» ≥ 30pt; il campione da 120
pagine non ha verbale.

## 4. Il difetto dominante, misurato su quattro pagine

Le regioni sbagliate hanno **una causa sola**: la regione **attraversa il gutter di
pagina** e lo adotta come colonna di tabella. DrM pag36, Dag pag136, DrW pag248,
e Dag pag198 dal campione cieco.

`column_band` wired **ha** l'informazione — su DrM pag36 dà le due colonne di
pagina — ma la riporta nella **stessa forma** con cui riporta le colonne di una
tabella: su DB pag76 le sue bande sorelle sono due colonne della tabella stessa.
È il punto bloccante 2 di Milestone 33, aperto da allora.

Segnale indicato dall'utente e **non misurato**: al primo taglio, due rami
paragonabili sono colonne di pagina, un ramo minuscolo e uno enorme è una colonna
di tabella. DrM pag36 `134 : 188`, DB pag76 `36 : 258`. **Due pagine non sono una
misura.**

E una seconda causa, su due pagine: **la scheda vince sulla tabella**. Su DrM
pag49 e pag199 il meccanismo prende la striscia d'intestazione delle schede mostro
(dieci colonne) invece della tabella vera in fondo (sei).

## 5. Le dieci ipotesi cadute, da non riprovare

Tutte a verbale nelle docstring del codice, ciascuna con la pagina e i numeri che
la falsificano. Sei sull'estensione verticale, tre sulla scelta della spina, una
sul vincolo di banda.

## 6. Come si numera una pagina, che ha già fatto perdere un giro

Tre numerazioni diverse e vanno tenute separate: `idx` 0-based degli script;
**pagina del file** 1-based, quella del lettore PDF; numero **stampato** sulla
carta. Su BiD: idx 34 → pagina 35 → stampato 28. I render si chiamano
`BiD_pagina0035_idx0034.png` per questo.

I numeri di pagina che l'utente fornisce sono **pagine del file**, verificato per
contenuto su 13 casi.

## 7. Che cosa committare, e in che ordine

1. **Senza codice**: `Criterio_TabellaNormale_v1.md`,
   `Criterio_EstensioneRegioneTabella_v1.md`.
2. **Campione ed esiti**: `Campione_TabellaNormale_v1.md`,
   `scripts/sample_ir2_verification_pages.py` (modificato),
   `Esito_TabellaNormale_v1.md`, `Esito_EstensioneRegioneTabella_v1.md`,
   `Esito_RegioneTabellaPerColonne_v1.md`, questo file.
3. **Diagnostica e prototipi**: i sei script in `scripts/`.
4. **Fuori dal repo**: `Proposta_RegioneTabella_v1.md` (ritirata) e `v2.md`.

## 8. La domanda che il prossimo giro deve porsi

`Proposta_RegioneTabella_v2.md` aveva misurato che sulle **tabelle vere** il
meccanismo di Milestone 39 funziona (`tables=1/1` su cinque) e che il difetto è la
**riga**, non la regione — mettendo un producer di regioni **fuori scope**. Un
giorno dopo è stata costruita la settima sorgente di regione.

Le due posizioni non possono stare entrambe in `State.md`. Una va ritirata per
iscritto, e la scelta non è di chi implementa.
