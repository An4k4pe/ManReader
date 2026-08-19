# Criterio — i separatori di campo variano di posizione? (tabella contro scheda)

Registrato **prima** della misura (`AGENTS.MD` §15). Secondo tentativo sul
discriminante tabella/scheda; il primo è caduto ed è a verbale in
`Esito_RegolaritaTableCandidate_v1.md`.

## 1. L'ipotesi, nella formulazione dell'utente

Cercare i gutter **evitando le bande principali di pagina**, ammettendo anche
quelli alti **una sola riga**, e guardare se fra i due lati, sulla stessa riga, i
separatori — **sia tipografici sia no** — siano **diversi e variabili**.

## 2. Perché non ripete il criterio caduto

Il primo contava **quante righe di sorgente** compongono una riga visiva, ed è
caduto perché quel numero è instabile: lo stesso pannello dà 1 su DB idx 89 e 3 su
DB p.99, a seconda di come PyMuPDF ha raggruppato.

Questo criterio **non conta le righe**: guarda **dove cadono i separatori**, e
tratta allo stesso modo le due forme che il primo confondeva —

- separatore **tipografico**: una corsa di `U+2000`–`U+200A`, `U+2003`, `U+2002`,
  `U+2001`, tab, o due o più spazi normali, **dentro** una riga di sorgente;
- separatore **di vuoto**: lo spazio fra due righe di sorgente affiancate sulla
  stessa riga visiva.

Se il raggruppamento di PyMuPDF cambia, il separatore cambia di **tipo** ma resta
**nella stessa posizione x**. È la proprietà che il criterio precedente non aveva.

## 3. Che cosa misuro

Regione = un `table_candidate` (serve solo a delimitare l'area; i gutter di banda
principale restano fuori per costruzione, come chiede l'utente).

Per ogni riga visiva della regione, la **x del centro** di ogni separatore.
Poi: quanto quelle x si allineano fra righe diverse.

- **unità di tolleranza**: metà della **moda delle `font_size` della pagina**,
  cioè desunta dal documento e non fissata — è la sola forma di criterio
  page-local sopravvissuta al lavoro dopo Milestone 35;
- **metrica**: la quota di righe visive che partecipa al **cluster di x più
  popolato**.

## 4. Soglia e regola di lettura, fissate prima

- **allineato** = ≥ 70% delle righe con almeno un separatore partecipa al cluster
  modale;
- **variabile** = < 70%.

**Il discriminante regge** se **tutte** le regioni etichettate SCHEDA risultano
variabili **e** la TABELLA risulta allineata.

**Cade** se anche una sola SCHEDA risulta allineata, o se la TABELLA risulta
variabile.

## 5. Le etichette, assegnate prima

| regione | etichetta |
| --- | --- |
| DB idx 89 `x346-531` — pannello FANTASMA | **SCHEDA** |
| DB idx 89 `x62-249` — `D6 ATTACCO` | **TABELLA** |
| DrM idx 86 — Devil Legate | **SCHEDA** |
| **DB idx 98 — pannello GUERRIERO/ARCIERE/CAMPIONE** | **SCHEDA** |
| Vil idx 222 | **MISTO**, non concorre |

**DB idx 98 è aggiunta rispetto al criterio precedente, e va detto perché**: è la
pagina da cui è nata la segnalazione dell'utente, ed è il **controcaso** di DB idx
89 — stesso tipo di pannello, raggruppamento di sorgente opposto. Se il segnale è
stabile deve dare lo stesso esito sulle due. Aggiunta **prima** di misurare, non
dopo aver visto un risultato.

## 6. Limiti dichiarati prima

Quattro regioni utili, tre manuali. Non è un campione. Se regge, il passo
successivo **non** è scrivere il producer: è provarlo su pagine non scelte da me.
Se cade, la milestone non si apre e la terza formulazione **non** si cerca dentro
questo giro.
