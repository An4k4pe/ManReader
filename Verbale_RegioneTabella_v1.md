# Verbale — il lavoro sulle tabelle, per chi lo riprende

Scritto l'11 settembre 2026 dalla Chat A del ramo
`claude/table-region-producer-005fb8` (punta `0c1f1fa`, 21 agosto).

Sostituisce, **come unica lettura necessaria**, le tre proposte
`Proposta_RegioneTabella_v1..v3.md`. Non sono mai state committate e restano solo
in quel worktree:

```
/home/an4k4pe/Documenti/ManReader (Copia)/.claude/worktrees/table-region-producer-005fb8/Proposta_RegioneTabella_v{1,2,3}.md
```

Tutto ciò che conta di quelle tre è qui sotto. Ogni numero è misurato; dove non
lo è, è scritto. Il §8 — che cosa è successo dopo il 21 agosto su altre linee —
l'ho ricostruito **da git**, non lavorandoci: vale come mappa, non come verifica.

---

## 0. In sei righe

1. Tabelle normali con la regione wired e le righe a spina: criterio
   pre-registrato, **eseguito, CADE 0 su 3** su 60 pagine cieche. Delle tre
   cause, **due sono la regione**, una la riga.
2. Il meccanismo a **massimo numero di colonne** (idea dell'utente) fa 13 su 16
   tabelle vere, **ma è un fit** e non ha criterio. Sul cieco da 120 pagine
   produce una regione su 107.
3. Il difetto dominante della regione è **uno**: attraversa il gutter di pagina e
   lo adotta come colonna di tabella.
4. **`State.md` non contiene una riga di questo lavoro**, su nessun ramo
   (verificato su `e05ebfa`). Esiste solo nei file
   `Criterio_/Campione_/Esito_/Consegna_/Prompt_` e nelle docstring.
5. Dopo: M43, M44 e `c1b0307` hanno portato in IR 2 i confini di colonna ammessi
   da Resolution. **La regione viene ancora da `table_candidate`**, cioè dalla
   sorgente di cui qui sotto sono misurati i difetti, e **`build_table` è
   identico a `0c1f1fa`**.
6. Sei punti in documenti committati sono riferimenti morti o affermazioni
   superate (§7).

## 1. Dove sta il lavoro in git

| commit | contenuto |
| --- | --- |
| `5d88a7b` | `Criterio_TabellaNormale_v1.md`, `Criterio_EstensioneRegioneTabella_v1.md` — senza codice |
| `586c96c` | `Campione_TabellaNormale_v1.md`, `Esito_TabellaNormale_v1.md`, `Esito_EstensioneRegioneTabella_v1.md`, `Esito_RegioneTabellaPerColonne_v1.md`, `Consegna_TabelleChat_v1.md`, `Prompt_ChatNuova_v1.md`, `scripts/sample_ir2_verification_pages.py` |
| `0c1f1fa` | sette script: `inspect_table_region_sources.py`, `inspect_table_gutter_regularity.py`, `render_wired_producers.py`, `compare_table_gutters_with_column_band.py`, `prototype_table_columns_and_rows.py`, `prototype_table_gutter_extension.py`, `prototype_table_max_columns.py` |

Li contengono tutti e tre: `claude/statblock-markdown-ir2-7b2573` (punta
`e05ebfa`, la più recente), `claude/ir2-porta-42-43`,
`claude/asset-note-visibility-e14deb`, `claude/markdown-readability-text-form-184fa3`;
su origin attraverso questi ultimi due. **Non** su `main` né su `origin/main`
(`3a2238d`).

Nessun modulo di produzione è stato toccato: nessun producer nuovo, nessun wiring.

## 2. Tre numerazioni di pagina — la trappola che ha già fatto perdere un giro

- **idx**: 0-based, quello degli script e dei `frozenset` di esclusione.
- **pagN**: pagina del file, `idx + 1`, quella che mostra il lettore PDF. **È
  quella che l'utente fornisce** (verificato per contenuto su 13 casi). `--page N`
  degli script diagnostici è questa.
- **stampata**: il numero sulla carta; scostamento variabile e non lineare.

Esempio: BiD idx 34 → pag35 → stampata 28. I render si chiamano
`BiD_pagina0035_idx0034.png` per questo. Il primo giro di etichette dell'utente
sul campione da 60 è andato perso proprio così.

**Collisione concreta dentro questo lavoro**: `Dag pag136` (idx 135, una delle 16
tabelle dell'utente, caso del gutter di pagina) e `Dag idx 136` (pag137,
stampata 135, la pagina dell'oracolo di Milestone 20) sono **due pagine
diverse**. In questo verbale ogni pagina porta la sua forma esplicita.

I documenti di M43/M44 usano altre convenzioni («DB p.122», «DB indice 103
(stampata 102)»): prima di confrontare una pagina fra i due insiemi, renderla.

## 3. Proposta v1 (20 agosto) — ritirata; i fatti misurati restano

**Proponeva** un producer nuovo `layout.table_region`: la corsa massimale di
righe che condividono lo stesso insieme di gutter (confini y da `_segment_bands`),
ritagliata all'inchiostro. **Mai eseguito. Ritirata dalla v2** perché sei delle
sette pagine su cui era costruita non contengono una tabella vera.

I fatti, **eseguiti** con `scripts/inspect_table_region_sources.py`, restano veri.

**`text/lines`, la configurazione di `table_candidate`, ingoia e tronca.**

- Ingoia, su pagine che **non sono tabelle**: Apo idx 46 (pag47, st. 43) una
  regione `324×393` su tre blocchi «COSA PENSA»; Vil idx 166 (pag167, st. 163)
  una `366×415` su due elenchi zebrati più un titolo display; Wil idx 244
  (pag245) una `474×481` su sei strutture di una scheda.
- **Tronca, su una tabella vera: Dag idx 136 (pag137, st. 135).** Regione
  sinistra `(72.5, 73.7, 234.6, 744.2)`: esclude l'intera colonna `DESCRIZIONE`,
  che inizia a `x≈250`. Regione destra `(319.5, 73.7, 554.7, 418.2)`: si ferma
  alla riga `59` ed esclude la `60`.
- È la pagina dell'oracolo di M20, **verificato eseguendo**:
  `build_table_candidate_page_analysis` su idx 136 dà `(114, 57)`, l'asserzione
  di `tests/test_job_page_analysis_runner.py:257`; le vicine danno `(120, 72)` e
  `(35, 33)`. **I 114 sono il conteggio di una regione a cui manca una colonna**:
  l'oracolo verifica la riproducibilità, non la regione.
- La regione troncata ha **51 celle su 51 piene**: la quota di celle piene non
  vede una troncatura, perché conta le celle che ci sono.

**`lines/lines`**: l'«8 su 8 risolte, 0/35 span tagliati» di
`Esito_StrategiaTabella_v1.md` §2 è fatto di **strisce alte una riga** — tre
strisce d'intestazione `340×17` su Apo idx 46, cinque righe zebrate su Vil
idx 166, 14 su Dag idx 136. Regge come è scritto, non come suona.

**`column_band`** (wired da M37): Apo idx 46 tre bande giuste, gutter `x210-221`;
Vil idx 166 due bande giuste, gutter `x97-99`, `x144-155`, `x247-260`, **manca**
quello della colonna `#`; Wil idx 244 trova il gutter di `RESISTENZA` ma con
l'estensione y sbagliata; **Dag idx 136 quattro confini di colonna tutti giusti**
(`x163`, `x305`, `x343`, `x411`) ma bande alte quanto la pagina; DrM idx 267
13 bande annidate che non sono le tabelle; FW idx 62 e Fab idx 256 muto.

**Il legacy** (`extractor.py:160` `_find_table_regions`, `:206-227`
`_is_valid_text_line_table_region`), eseguito sulle sette: **peggio del producer
su tutte e sette**. Su Wil idx 244 emette `y0 = −32.8`, fuori dal foglio (il
producer la scarta già); su Dag idx 136 **rifiuta la tabella vera** perché è alta
l'85% della pagina contro una soglia fissa di 0,75; su DrM, FW e Fab tace
(`any()` su una lista vuota).

**Conseguenza non ancora applicata**: `Esito_TabellaInIR2_v1.md` §4 («i gutter
dentro le regioni sono pochi») va riformulato — i gutter ci sono e sono giusti,
erano le regioni a essere sbagliate.

**Non verificato nella v1**: DrM idx 267, FW idx 62, Fab idx 256 non aperte;
`interior_visual_frame` ed `embedded_visual` non provati sulla colonna
`RESISTENZA`, che è un rettangolo nero.

## 4. Proposta v2 (20 agosto) — le tabelle vere; §3 e §5 ritirati dalla v3

Cinque tabelle vere nel percorso IR 2 con `--tables` (`prototype_ir2_page.py`);
`tables=1/1` sulle quattro eseguite.

| pagina | cosa | esito |
| --- | --- | --- |
| DB idx 75 (pag76, st. 74) | ARMI DA MISCHIA, 9 col, 28 righe | corretta, ogni riga di dati giusta |
| Lan idx 118 (pag119) | armi, 5 col | corretta |
| Fab idx 284 (pag285) | equipaggiamento, 4 col | corretta, intestazione al posto giusto |
| Lan idx 284 (pag285) | classi per ruolo, 2 col | parziale: una riga fonde quattro voci |
| Dag idx 136 (pag137) | due tabelle affiancate | regione troncata (§3) |

**I quattro difetti, in ordine di quanto sporcano l'uscita.** Stanno tutti in
`ir2_builder.build_table`, che **oggi è identico** (diff della funzione fra
`0c1f1fa` ed `e05ebfa`, verificato):

1. **Una cella che va a capo diventa una riga in più** (DB idx 75
   `Ogg. Contundente, / Leggero`; su Fab idx 284 ogni descrizione). Le righe di
   griglia vengono dalle righe di sorgente raggruppate per sovrapposizione in y.
2. **L'intestazione resta fuori dalla regione** (DB idx 75: undici frammenti
   `IMP.`, `FOR`, `POR-`, `TATA`… escono come paragrafi dopo la tabella, e la
   prima riga di dati diventa l'intestazione Markdown). Su Fab idx 284 non succede.
3. **Testo che sfugge dai bordi laterali** (DB idx 75: `Infido, perforante,
   tagliente,` oltre `x1 = 539.6`). Stessa classe della troncatura di Dag, di
   grado minore.
4. **Righe che si fondono** (Lan idx 284: `ASSALTO Assassino Asso Assaltatore` in
   una riga).

L'1 e il 4 sono lo stesso parametro visto dai due lati.

**I gutter su DB idx 75**: `column_band` ai default trova **8 confini su 8**
(`x159 183 209 244 284 321 358 422`), verificati sul render uno per uno.

**Lo sweep dei parametri**, chiesto dall'utente: sette configurazioni
(`min_flanking_chars` 5→2→1, `min_gutter_lines` 3→2→1,5, `min_column_chars` 10→3,
tutte insieme) su quattro pagine. **Nessun effetto** su DB idx 75 e Apo idx 46; su
Dag idx 136 `chars 5→2` aggiunge `x95-102` (`TIRO|BOTTINO`); su Vil idx 166 solo
tutto insieme aggiunge `x46-59` (la colonna `#`). **L'unica cosa che
l'allentamento recupera è la colonna di numeri.** `State.md` §Cosa NON rifare
vieta di tarare `--min-flanking-chars` e di far decidere a `column_band` se una
regione è una tabella; la via che la v2 indicava era **un secondo interrogante**,
non una taratura. È la strada che M44 ha poi preso, in Resolution (§8).

**Perché M39 aveva concluso il contrario**: il suo campione uniforme di 12 pagine
non conteneva quasi tabelle vere, e l'unica cosa trovata (Wil idx 244) era una
scheda.

**Ritirati dalla v3**: il §3 nella forma assoluta («i gutter non sono il
problema») e il §5 («un producer nuovo di regioni è fuori scope»). **Restano
veri**: il peso relativo sulle tabelle ben delimitate e i quattro difetti. Due di
essi (1 e 3) sono chiusi nel **prototipo** (`prototype_table_columns_and_rows.py`:
righe a spina, `repair_region_x/y`), **non** in `build_table`.

## 5. Proposta v3 (21 agosto) — le rettifiche e lo stato del meccanismo nuovo

### 5.1 Il criterio della tabella normale: CADE

`Criterio_TabellaNormale_v1.md`, pre-registrato. Configurazione fissata prima:
la regione del producer wired più riparazioni e righe a spina del prototipo,
`--region text-lines --repair xy --bounds middle --rows spine --admit in-column`.
Campione cieco di 60 pagine, seed `20260822`, etichette dell'utente sui render
**prima** di qualunque uscita; barra ≥ 90%.

Etichette: **3 tabelle normali**, 1 speciale (DIE idx 222), 1 scheda con una
tabella dentro (Wil idx 173), 55 non tabelle.

| pagina | uscita | causa |
| --- | --- | --- |
| BiD idx 227 (pag228) | 1 colonna, nessuna tabella | **regione** |
| Dag idx 197 (pag198) | la regione parte da `potete utilizzare:`, che è prosa; `Amicizia` / `con la Natura` spezzato | **regione** |
| Wil idx 58 (pag59) | 2 col, 4 righe che fondono più voci, con dentro il folio `59` | **riga** |

**Zero su tre. Falsi negativi zero**: il difetto è la qualità, non la copertura.
Con un denominatore di tre la barra distingue solo zero da tre: **per una misura
con potere serve un campione di tabelle, non di pagine**.

La rettifica che ne segue, e che sostituisce il §3 della v2:

> Su tabelle già ben delimitate la regione non è il difetto e la riga sì. Dove la
> delimitazione è sbagliata — 2 tabelle cieche su 3 — la regione è il difetto
> principale, e nessun lavoro sulle righe la recupera.

### 5.2 Il criterio dell'estensione: cade due volte

`Criterio_EstensioneRegioneTabella_v1.md` («nessun gutter incontra testo E almeno
uno ha testo a lato») cade due volte (`Esito_EstensioneRegioneTabella_v1.md`), la
seconda dopo che l'utente aveva corretto l'implementazione della sua stessa regola.

### 5.3 Il meccanismo a massimo numero di colonne — la settima sorgente di regione

`scripts/prototype_table_max_columns.py`. **Il ribaltamento è dell'utente**: non
si scelgono le bande per ricavarne i gutter; si cerca l'insieme di gutter più
numeroso che regge, e le bande che attraversa **sono** la tabella.

Regole date dall'utente e implementate come date: vince **più colonne**, non più
altezza; servono **≥ 3 gutter compresi gli esterni** e **≥ 3 righe**; i gutter si
estendono finché nessuno incontra testo (ne basta uno a fermarli tutti) e finché
almeno una cella fra due gutter ha testo; un gutter che verrebbe interrotto **si
restringe**, non spezza la regione. Semi: i corridoi propri più i gutter di
`column_band` più le righe disegnate.

**Su 16 tabelle vere** — l'elenco dell'utente, pagine del file: Dag pag134,
pag136; DB pag62, pag76, pag123; DrM pag33, pag36; DrW pag33, pag240, pag248; Lan
pag19, pag41, pag52; BoB pag239; Wil pag74, pag78 (Dag pag118 era nell'elenco e
**non è una tabella**) — **13 corrette**, 3 sbagliate (**DrM pag36, Dag pag136,
DrW pag248**) con una causa sola. Dove l'utente aveva tracciato i gutter a mano,
coincidono con i suoi: DB pag76 otto su otto, Lan pag19 sei su sei, BoB pag239 il
suo. DB pag76 esce a 9 colonne, 31 righe, 0 residui.

**Il 13 su 16 non è una misura.** Sei regolazioni sono state aggiunte una per
pagina, su sei di quelle stesse pagine: il fondo di pagina non blocca; un visivo
con testo dentro non blocca; `embedded_visual` per i frammenti del fregio; testo
ruotato escluso; confine di banda sull'interlinea di pagina; pienezza come
spareggio. **Nessun criterio**: è l'unica delle sette sorgenti di regione mai
sottoposta a una regola scritta prima.

### 5.4 Sul cieco da 120 pagine (seed `20260823`, senza verbale)

- **107 su 120 producono una regione**: il tasso di base registrato da M35 è
  intatto.
- Col filtro sulla pienezza al 100% ne restano 16, di cui 10 a due colonne. Di
  cinque aperte, **quattro non sono tabelle**: prosa a due colonne, riquadri di
  scheda affiancati, due elenchi puntati, un elenco dove il «gutter» separa il
  pallino dal testo.
- **La pienezza è un artefatto**: calcolata sulla finestra seme e riportata dopo
  l'estensione. Ricalcolata sulla regione emessa, la separazione **sparisce** (DB
  pag76, corretta, da 100% a 72%; DB pag62, corretta, 52%; DrM pag36, sbagliata,
  57%).
- Candidato **post-hoc, non pre-registrato**: il **minimo** fra le colonne sulla
  regione emessa. DrW pag248 2%, DrW pag240 4%, DrM pag36 7%, Dag pag136 35%, poi
  un salto a DB pag62 52%: le tre sbagliate più il falso allarme noto (DrW pag240).

### 5.5 Il difetto dominante, e il secondo

**La regione attraversa il gutter di pagina e lo adotta come colonna di
tabella**: DrM pag36, Dag pag136, DrW pag248, più Dag pag198 dal cieco.
`column_band` wired **ha l'informazione** — su DrM pag36 dà le due colonne di
pagina `(0,98,245,783)` e `(264,98,603,783)` — ma nella **stessa forma** con cui
riporta le colonne di una tabella (su DB pag76 le bande sorelle sono colonne della
tabella stessa). È il punto bloccante 2 di M33, aperto da allora. **Cinque forme
di vincolo provate, nessuna scatta dove serve.**

Segnale dell'utente, **non misurato**: al primo taglio, due rami paragonabili sono
colonne di pagina, uno minuscolo e uno enorme è una colonna di tabella — DrM
pag36 `134 : 188`, DB pag76 `36 : 258`. Due pagine non sono una misura.

**Il secondo, su due pagine: la scheda vince sulla tabella.** Su DrM pag49 e
pag199 il meccanismo prende la striscia d'intestazione delle schede (dieci
colonne) invece della tabella vera in fondo (sei).

### 5.6 Che cosa serve prima di chiamarlo un risultato

1. un criterio pre-registrato, con le etichette a vista prima di qualunque
   conteggio, su un **campione di tabelle** — e **come costruirlo senza
   sceglierlo a mano** è la prima domanda aperta;
2. l'indicatore ricalcolato sulla regione emessa (candidato: il minimo);
3. una regola contro il gutter di pagina che scatti davvero.

## 6. Rilievi sul codice dei prototipi

**Verificati, non corretti:**

1. `coherence` è calcolato sul **seme** e riportato dopo l'estensione
   (`prototype_table_max_columns.py`, `evaluate` → `:236` → `:304`).
2. In `_blockers` `width` e `height` della pagina sono **ombreggiate** dal ciclo
   sui disegni (`prototype_table_gutter_extension.py:119-120` contro `:208`). La
   revisione ha misurato 11 pagine su 40 che perdono bloccanti; sulle due provate
   l'uscita non cambia. Latente, ma ogni misura futura sull'estensione fatta con
   quel codice ha un ingresso corrotto.
3. `analyse` emette **una sola regione per pagina** (`:298-312`, una lista di un
   solo elemento). Lan pag52 ha due tabelle
   (`Esito_EstensioneRegioneTabella_v1.md:18`), quindi una si perde. *Nota:
   `Consegna_TabelleChat_v1.md` lo mette fra i non verificati e
   `Prompt_ChatNuova_v1.md` fra i verificati; l'ho verificato oggi leggendo il
   codice.*
4. `columns` resta `count - 1` anche quando il restringimento scarta un gutter
   tutto bloccato (`:289-290`, `:302`). Rilievo della revisione, verificato oggi
   leggendo il codice; l'effetto sulle uscite non è misurato.
5. La velocità: avevo scritto «55 s a pagina, sei ore a manuale». Misurato:
   **1,7 s a pagina**, 171 s su 120 pagine. Nessuna ottimizzazione serve.

**Verificato e chiuso da un'altra chat.** Le quattro pagine di sviluppo che
mancavano dalle esclusioni — DB idx 61, Lan idx 18, Lan idx 51, Wil idx 77, cioè
pag62, pag19, pag52, pag78, le pagine tracciate dall'utente — le ha aggiunte
`6473522` (`Criterio_FormaMancante_v3.md` §4). Mancavano già nel criterio
(`Criterio_TabellaNormale_v1.md:59-62`), non solo nello script. Quella chat ha
verificato che nessuna compare fra le 60: il campione non è contaminato.

**Trovato da un'altra chat, non corretto, ed è un errore mio.**
`NORMAL_TABLE_EXCLUSIONS` in `586c96c` ha **29 voci distinte** (35 scritte, 6
duplicate), mentre `Campione_TabellaNormale_v1.md:18` dichiara **28 esclusioni
totali** (7 + 3 + 18). Le 11 in più — il blocco «16 tabelle» — le ho **appese io,
nello stesso commit, dopo l'estrazione**: il diff `586c96c..0c1f1fa` sullo script
è vuoto, quindi erano già lì. La riga di comando documentata in
`Campione_TabellaNormale_v1.md:9-12` oggi esclude 39 pagine (43 dopo `6473522`) e
**non riproduce più le 60**. Il verdetto regge; **il file ha bisogno di una
nota**, e nessun commit successivo gliel'ha data.

**Non verificati, dalla revisione indipendente**: l'`edge_strip` del prototipo non
scatta mai su BoB pag239 (operandi `lo/hi`); `bonus` nel punteggio premia
l'adozione del gutter di pagina; `MIN_WIDTH` non è riverificato dopo il
restringimento; 33 regioni su 107 hanno un «gutter» ≥ 30pt.

## 7. Documenti committati che vanno corretti

- `Prompt_ChatNuova_v1.md:25` rimanda a `Proposta_RegioneTabella_v3.md`, **che
  non è nel repo**; `:30-32` dice «`main` a `a2f5e18`… Niente committato», ormai
  falso.
- `Consegna_TabelleChat_v1.md`: §1 «Niente è committato» è falso; l'ordine di
  commit del §7 è stato eseguito (e non comprende la v3). **Il §8 chiede di
  ritirare per iscritto la contraddizione fra v2 e v3: la v3 la ritira, ma non è
  nel repo**, quindi nel repo la contraddizione è ancora aperta. Questo verbale,
  se committato, la chiude.
- `scripts/inspect_table_region_sources.py:3,13`: la docstring cita
  `Proposta_RegioneTabella_v1.md` §1 e §4, che non sono nel repo. I numeri sono
  nel §3 di questo verbale.
- `Campione_TabellaNormale_v1.md`: manca la nota sulle esclusioni (§6).
- `Esito_TabellaInIR2_v1.md` §4: da riformulare (§3).
- `Esito_RegioneTabellaPerColonne_v1.md:4` dice «nove ipotesi cadute», il suo §5
  ne elenca dieci (6 + 3 + 1).

## 8. Dopo il 21 agosto, sulle altre linee (ricostruito da git)

- **A giudicare dai commit, la chat successiva ha scelto l'opzione A** (la forma
  del testo): `992de5f`, `6473522`, poi M40-42 (uscita leggibile, titoli per
  fascia). Nessun commit successivo tocca la regione tabella.
- **M43**, diagnostica di `column_band`: su 15 pagine di DB marcate dall'utente,
  la colonna dei numeri di dado è un separatore **10 corridoi su 10**. Quattro
  varianti del criterio di fianco; **V4, «non vuoto in tabella»**: 14/14 sulla
  verità, DB 357 con 0 fuori tabella, Apo 69 con 0 fuori. **Il discriminatore
  sono i candidati di `table_candidate`.** `AGENTS.MD` §Layout e candidati è
  stato aggiornato di conseguenza (`9da51b0`).
- **M44**: i corridoi respinti diventano una misura
  (`page_analysis_column_band_rejected_gutters.py`), V4 va in Resolution
  (`resolution_column_boundaries.py`), e c'è `table_row_reading_order.py` (due
  righe stanno nella stessa riga di tabella se le estensioni verticali si
  sovrappongono).
- **`c1b0307`** (9 settembre, `Criterio_ConfiniInTabellaIR2_v1.md`):
  `prototype_ir2_page.py`, da cui `main_ir2.py` importa, somma ai gutter di banda
  i confini ammessi. L'ordinamento per righe **non** è collegato perché
  `build_table` fa già la stessa cosa. Su DB 95-125 cambiano 11 pagine, **le
  stesse 11** in cui Resolution ammette un confine; tabelle da 10 a 12, righe da
  288 a 346, celle piene da 720 a 846. DB 96 perde una cella piena e DB 102
  cinque: le descrizioni attraversano un gutter e `_column_of` le lascia
  paragrafo, per scelta dichiarata. Tempo invariato (57,1 s contro 57,0).
- **`e05ebfa`** (11 settembre): con le tabelle accese, una regione
  `table_candidate` che attraversa il confine di una scheda **non si costruisce**
  (su Daggerheart copre colonne intere di tre schede).
- **In IR 2 le tabelle restano spente per default**: `main_ir2.py --tabelle` e
  `prototype_ir2_page.py --tables` sono entrambi `store_true`.

## 9. Come si incastrano i due filoni

Ogni punto è un fatto misurato da una delle due parti; **l'incastro non l'ha
misurato nessuno**.

1. **La regione di IR 2 è ancora quella di `table_candidate`**, e V4 ammette un
   confine solo dentro una regione `table_candidate`. È la stessa sorgente la cui
   troncatura è misurata su Dag idx 136, e che in 2 tabelle cieche su 3 è la
   causa della caduta. Un confine ammesso aiuta la parte che sta dentro la
   regione, non quella che la regione ha perso.
2. **Lo sweep della v2 e V4 cercano la stessa cosa**: la colonna dei numeri che
   `column_band` scarta. Lo sweep l'aveva trovata su Dag idx 136 (`x95-102`) e su
   Vil idx 166 (`x46-59`). **Se V4 la ammetta su quelle due pagine non è
   misurato**: è il controllo più economico che collega le due linee —
   `scripts/verify_resolution_column_boundaries.py` sulle due, con la predizione
   scritta prima.
3. **`c1b0307` non tocca né la regione né il raggruppamento in righe.** Sui due
   casi ciechi di regione può al più aggiungere una colonna dentro la regione
   sbagliata; sul caso di riga niente. Non misurato.
4. **I quattro difetti della v2 sono nel codice di produzione** (`build_table`
   invariato). Il prototipo ne chiude due, ma il criterio con quelle riparazioni
   è caduto 0 su 3 per colpa della regione.
5. **`_column_of` lascia paragrafo il testo che attraversa un gutter**: è la
   stessa scelta del mio `--admit in-column`, ed è il motivo per cui DB 102 ha
   una griglia quasi vuota.
6. **La scheda che vince sulla tabella** (DrM pag49, pag199) ha oggi una regola
   dal lato del consumer (`e05ebfa`), ma scritta per le regioni `table_candidate`;
   sul meccanismo a massimo numero di colonne non è misurata.

## 10. Da dove si può ripartire

Le opzioni sono tutte aperte e la scelta è dell'utente, contro l'obiettivo: un
Markdown leggibile a occhio. In ordine di costo:

- **A. Pulizia, senza misure.** I sei punti del §7, e committare questo verbale
  così che la v3 esista nel repo. Non avvicina il Markdown, ma toglie affermazioni
  che oggi un lettore del repo prenderebbe per vere.
- **B. Il controllo di collegamento** (§9.2): un'esecuzione, con la predizione
  scritta prima. Dice se la linea M44 copre già la parte «colonna dei numeri» di
  questo lavoro.
- **C. La regione.** È la causa di 2 casi ciechi su 3. Prima di qualunque
  meccanismo serve il campione di tabelle (§5.6). Cinque vincoli sul gutter di
  pagina sono già caduti; il segnale dell'utente sul primo taglio è l'unico non
  provato.
- **D. Le righe in `build_table`.** È il percorso di produzione, tocca 1 caso
  cieco su 3 e i quattro difetti della v2. Stesso problema di campione.

**Raccomandazione**: A e B prima, perché costano poco e dicono quanto di questo
lavoro è già superato; poi C o D, con il campione di tabelle come primo passo in
entrambi i casi. Da tenere a mente: sul cieco una tabella perfetta cambia 3
pagine su 60.

## 11. Regole imparate qui

1. **Criterio scritto e committato senza codice prima della misura**
   (`AGENTS.MD` §15). Dove è stato fatto ha retto; le quattro ipotesi decise a
   posteriori sono cadute.
2. **Numeri solo se misurati.** Tre affermazioni false in questo lavoro, tutte
   trovate da altri: la velocità (sbagliata di 39 volte), la separazione della
   pienezza, e «la linea mobile attraversa la prosa». Le linee erano **margini**
   (BoB pag239 `x395-414`, Lan pag52 `x48-59`) e **illustrazioni** (Lan pag19).
3. **Cercare nel repo prima di proporre.** Quattro volte aveva già la risposta: il
   fondo di pagina non interrompe un corridoio; un visivo blocca solo se dentro
   non ci vive testo; `embedded_visual`; `edge_strip` a
   `page_analysis_column_band.py:764`, regola dell'utente già in produzione. Una
   volta ho duplicato il ritaglio all'inchiostro che era già in
   `measure_column_band_table_candidate_overlap.py`.
4. **Applicare tutte le regole insieme**, non solo l'ultima: è la correzione che
   l'utente ha dovuto ripetere più spesso in questa chat.
5. **Non provare su 17 pagine un principio che non funziona su una.**
6. **Le dieci ipotesi cadute** sono nelle docstring degli script, con la pagina e
   i numeri: sei sull'estensione verticale, tre sulla scelta della spina, una sul
   vincolo di banda. Non vanno riprovate.
7. **Da non riaprire**: tarare `--min-flanking-chars`; far decidere a
   `column_band` se una regione è una tabella; rieseguire
   `Criterio_TabellaNormale_v1.md`; ottimizzare il prototipo.
