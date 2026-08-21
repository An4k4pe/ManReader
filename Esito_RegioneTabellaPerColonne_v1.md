# Esito — la regione tabella dal massimo numero di colonne coerenti

Verbale di ciò che questa sessione ha stabilito sulle regioni tabella. Registra
sia quello che funziona sia le **nove ipotesi cadute**, perché nessuna venga
riprovata.

Non è un criterio: i risultati qui sotto sono su pagine di **sviluppo**, fornite
dall'utente o guardate durante il lavoro. Un giudizio richiede un insieme mai
visto, e va registrato prima.

---

## 1. Il ribaltamento, e a chi appartiene

**Proposta dell'utente.** Fino a quel punto il meccanismo faceva: *scegli delle
bande → ricava i gutter*, e per scegliere le bande giuste bisognerebbe già sapere
dov'è la tabella. Circolare, e sei ipotesi ci si sono rotte sopra.

Il ribaltamento: **si cerca l'insieme di gutter più numeroso che regge, e le bande
che quei gutter attraversano SONO la tabella.** La regione non si sceglie: si
deduce.

Regole fissate dall'utente e implementate come date:

- vince **più colonne**, non più altezza — due gutter che sopravvivono a tutta la
  pagina eliminando quelli interni descrivono l'impaginazione, non una tabella;
- servono **almeno 3 gutter compresi gli esterni** e **almeno 3 righe**: sotto, si
  descrive meglio con testo semplice o un elenco;
- trovati i gutter, si **estendono** finché nessuno incontra testo (ne basta uno a
  fermarli tutti) e finché almeno una **cella** fra due gutter contiene testo;
- un gutter che verrebbe interrotto si **restringe** per adattarsi, non spezza la
  regione.

## 2. Che cosa esce, su 16 tabelle vere

| esito | quante |
| --- | --- |
| corrette | **13** |
| sbagliate | **3** — DrM pag36, Dag pag136, DrW pag248 |
| falso allarme dell'indicatore | 1 — DrW pag240 |

Le tre sbagliate hanno **una causa sola**: la regione **attraversa il gutter di
pagina** e unisce due colonne di impaginazione diverse.

Le tabelle su cui l'utente aveva tracciato i gutter a mano escono **identiche ai
suoi tracciamenti**: DB pag76 otto gutter su otto (8 confermati anche da
`column_band`), Lan pag19 sei su sei, BoB pag239 il suo.

Esempio di uscita, DB pag76 — 9 colonne, 31 righe, **0 residui**:

```
| ARMA | IMP. | FOR | TATA | DANNO | BILITÀ | COSTO | NIBILITÀ | QUALITÀ |
| Ogg. Contundente, Leggero | 1M | — | FOR | D8 | 3 | — | — | Contundente, può essere lanciato |
```

## 3. La pienezza — **il §3 precedente era falso, ritirato**

Diceva che la pienezza si era rivelata un indicatore di revisione, con «le tre
regioni sbagliate al 45%, 73%, 75% e le corrette al 100%».

**Non regge.** Rilievo della revisione indipendente, verificato nel codice:
`prototype_table_max_columns.py` calcola `coherence` dentro `evaluate`, cioè sulla
finestra **seme**, e la riporta invariata dopo che l'estensione ha cambiato `b0` e
`b1`. Il numero pubblicato descrive una finestra che **non è la regione emessa**.

Ricalcolata sulla regione vera, la separazione **sparisce**: DB pag76, corretta,
scende dal 100% al 72%; DB pag62, corretta, al 52%; DrM pag36, **sbagliata**, sale
al 57% e quindi sta **sopra** una corretta.

Resta un candidato, proposto dalla revisione e **non ancora pre-registrato**: il
**minimo** fra le colonne, calcolato sulla regione emessa. Lì i valori sono
DrW pag248 2%, DrW pag240 4%, DrM pag36 7%, Dag pag136 35%, poi un salto a
DB pag62 52% — cioè esattamente le tre sbagliate più il falso allarme noto. È
un'osservazione post-hoc sulle stesse 16 pagine e va registrata prima di crederci.

## 4. Quattro volte il repo aveva già la risposta

1. **Il fondo di pagina non interrompe un corridoio.** `State.md` lo registra con
   le stesse coordinate ricomparse qui: su DB pag76 il primo bloccante è
   `(-8, -8, 613, 799)` e annullava l'estensione.
2. **Un visivo blocca solo se non ci vive testo dentro** — `State.md`, «chiusure di
   riquadro 0, fondi 21-63». Senza, il fregio `ARMI DA MISCHIA` teneva fuori metà
   intestazione.
3. **`embedded_visual`** raggruppa i frammenti del fregio; una fusione locale
   scritta a mano non basta.
4. **`edge_strip`** in `page_analysis_column_band.py:764`: «il minimo di larghezza
   si applica **solo alle colonne che toccano il bordo della pagina** — una
   linguetta di capitolo produce una colonna strettissima al bordo, una tabella la
   produce all'interno». Regola dell'utente, già in produzione.

E una volta ho **duplicato** lavoro esistente: il ritaglio all'inchiostro della
bbox `column_band` era già in `measure_column_band_table_candidate_overlap.py`
come variante «observed-extent».

## 5. Le nove ipotesi cadute, tutte a verbale nel codice

Sull'**estensione verticale**, sei, e le prime quattro decidendo a posteriori sui
numeri: corsa più lunga fra i bin; gruppo ristretto alle bande dove sono liberi
tutti i corridoi; gutter come linea più lunga larga un bin più la regola di
estensione; `--region auto` da corse di corridoi; la clausola «tutti i gutter
liberi» applicata a gutter fissati sul seme; i gutter esterni dentro la clausola 1.

Sulla **scelta della spina** (modello di riga), tre: passo mediano più largo; non
va a capo misurato sull'interlinea; più ancore ma non più delle bande y.

E sul **vincolo di banda**, uno: «un gutter di `column_band` dentro la regione
dev'essere fra i suoi confini di colonna». Non scatta dove serve — il gutter di
pagina viene adottato come colonna dalla regione stessa — e faceva perdere
DB pag123.

## 6. Una correzione a una mia diagnosi, che era sbagliata

Avevo scritto che una linea mobile «trova quasi sempre un passaggio, quindi la
corsa attraversa anche la prosa». **Falso**, e scritto senza guardare i render.
Chiesti dall'utente e disegnati, le linee non attraversavano la prosa: erano
**margini** (BoB pag239, Lan pag52) e **spazio occupato da illustrazioni**
(Lan pag19, dove la griglia di occupazione contava solo il testo).

## 7. Che cosa resta aperto

**Un difetto di codice, non ancora corretto**: in `_blockers`
(`prototype_table_gutter_extension.py:119` e `:208`) le variabili `width` e
`height` della pagina sono **ombreggiate** dentro il ciclo sui disegni. Dal primo
disegno in poi `covers_page` confronta col disegno precedente invece che con la
pagina: su pagine con arredo pesante si perdono fino a due terzi dei bloccanti.
Misurato dalla revisione su 40 pagine: 11 perdono bloccanti. Sulle due provate
l'uscita non cambia, quindi e' **latente**, ma qualunque misura futura
sull'estensione fatta con questo codice ha un ingresso corrotto.

**Il vincolo di banda.** `column_band` wired **ha** l'informazione — su DrM pag36
dà le due colonne di pagina, `(0,98,245,783)` e `(264,98,603,783)` — ma la riporta
nella **stessa forma** con cui riporta le colonne di una tabella: su DB pag76 le
sue bande sorelle sono due colonne della tabella. Distinguerle è il punto
bloccante 2 di Milestone 33, aperto da allora.

Segnale indicato dall'utente e **non misurato**: al primo taglio, due rami
paragonabili sono colonne di pagina, un ramo minuscolo e uno enorme è una colonna
di tabella. Su DrM pag36 `134 : 188`, su DB pag76 `36 : 258`. **Due pagine non
sono una misura**, e va registrato un criterio prima.

**`layout.side_band` non è wired** — Milestone 6 lo ha congelato come baseline
diagnostica — quindi non esiste oggi un producer che tolga le linguette di
capitolo fatte di **testo**. `page_edge_visual` vede solo quelle visuali: su
quattro pagine guardate ne trova **una**.
