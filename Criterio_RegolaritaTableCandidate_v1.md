# Criterio — la regolarità dentro un `table_candidate` distingue tabella da scheda?

Registrato **prima** della misura, come `AGENTS.MD` §Regole operative punto 15
richiede per una misura che decide se una linea di lavoro prosegue. Decide se la
milestone «categoria scheda mostro» si apre e con quale meccanismo.

## 1. L'ipotesi, nella formulazione dell'utente

Una scheda è «una combinazione di gutter e righe in configurazione **non
regolare**, e molti dati nome-variabile-variabile»; se fosse **regolare**,
`table_candidate` la risolverebbe già bene.

Già misurato e **non** in discussione qui: `table_candidate` scatta comunque, su
regolari e irregolari. Quindi il discriminante non può essere la sua presenza. La
riformulazione che si misura è: **la regolarità della struttura *dentro* un
`table_candidate`**.

## 2. Che cosa misuro

Per ogni `table_candidate`, le sue primitive testuali si raggruppano in **righe
visive** (righe di sorgente le cui estensioni y si sovrappongono), e per ogni riga
visiva si conta quante **righe di sorgente distinte** la compongono — che è il
numero di campi affiancati, misurato su DB p.99 dove `Movimento:`, `Danno Bonus:`
e `PF` sono tre righe di sorgente sulla stessa riga visiva.

La geometria qui **misura**, non ricostruisce: serve solo a dire quali righe di
sorgente stanno affiancate, e il testo continua a venire dalla sorgente.

Metrica per candidato: la quota di righe visive che condividono il conteggio di
campi **modale**.

## 3. Le etichette, assegnate PRIMA di misurare

Dai render già ispezionati:

| candidato | etichetta attesa |
| --- | --- |
| DB idx 89, `x62-249 y268-637` (`D6 ATTACCO`) | **TABELLA** |
| DB idx 89, `x346-531 y133-323` (pannello statistiche) | **SCHEDA** |
| DrM idx 86, `x316-552 y74-555` (Devil Legate) | **SCHEDA** |
| Vil idx 222, `x57-393 y85-445` | **MISTO** — ingloba la striscia `DIFFICOLTÀ` e la tabella `DADO OSCURITÀ` insieme, e non è né l'una né l'altra |

## 4. Soglia e regola di lettura, fissate prima

- **regolare** = ≥ 80% delle righe visive ha lo stesso numero di campi;
- **irregolare** = < 80%.

**Il discriminante regge** se le due SCHEDA risultano irregolari **e** la TABELLA
risulta regolare.

**Il discriminante cade** se anche una sola SCHEDA risulta regolare, oppure se la
TABELLA risulta irregolare. In quel caso la milestone non si apre su questo
meccanismo, e il verbale lo dice.

Il caso **MISTO** non concorre al verdetto — è già noto come difetto di
perimetro del candidato, non come prova sulla regolarità. Si riporta e basta.

## 5. Seconda misura: candidati annidati

Se esistano `table_candidate` la cui bbox ne contiene un'altra. È una domanda di
fatto, senza soglia e senza verdetto: serve a sapere se «guardare dentro un
candidato» incontri il problema di quale candidato guardare.

## 6. Limite dichiarato prima

Tre pagine, tre manuali. Non è un campione e non va citato come tale. Se il
discriminante regge qui, il passo successivo **non** è scrivere il producer: è
provarlo su pagine non scelte da me.
