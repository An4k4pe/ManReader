# Milestone 43 — perche' `column_band` non emette bande. Criterio pre-registrato

Scritto **prima** di guardare qualunque numero di scarto, come chiede
`AGENTS.MD` §Regole operative punto 15 e `CLAUDE.md`.

## Il fatto che apre la milestone, e non viene da qui
Due osservazioni indipendenti, nessuna delle due mai indagata:

- **Milestone 38**, sul suo campione cieco di 10 pagine da 3 manuali: «6 pagine
  su 10 non producono bande», registrato come limite del potere discriminante
  di un test, non come difetto del meccanismo.
- **Giro Markdown del 6 settembre 2026** sul Dragonbane Quickstart, 47 pagine:
  43 pagine su 47 hanno testo fuori dalle bande, e **14 pagine su 47 non
  emettono nessuna banda**. Su pagina indice 29 sono 61 span su 61. Su quelle
  pagine l'ordine di lettura degrada a `y`, e due colonne di prosa escono
  interlacciate riga per riga.

Il secondo caso e' quello da cui nasce l'affermazione, quindi il criterio lo
vincola esplicitamente: il Quickstart entra nel campione **per intero**.

## La domanda, una sola
Quando una pagina a due colonne non produce bande, **quale passo del meccanismo
l'ha prodotto**? Il corridoio verticale non si forma mai (`_build_gap_grid` /
`_chain_gutters`), oppure si forma e viene scartato da un criterio di ammissione
(`_reject_reason`: `too_few_lines`, `too_few_wordy_lines`, `too_short`)?

## Cosa questa milestone NON fa
- Non tocca `page_analysis_column_band.py`, ne' le sue soglie, ne' i default.
- Non propone un producer, non fa wiring, non cambia l'ordine di lettura.
- Non decide se le pagine senza bande siano un difetto: prima si attribuisce la
  causa, poi si decide, e sono due milestone diverse.
Diagnostica pura, stesso perimetro di Milestone 25, 29 e 32.

## Metodo
Uno script committato in `scripts/` importa **invariate** le funzioni del
producer di produzione e, per ogni pagina, riporta:
- quanti corridoi verticali vengono incatenati prima dell'ammissione;
- quanti sono ammessi e quanti scartati, con il motivo per ognuno;
- per le pagine che finiscono con **zero** bande: il corridoio scartato con la
  maggiore estensione verticale, cioe' il miglior candidato a essere la colonna,
  con il suo motivo di scarto, la sua x, la sua altezza in righe di pagina e il
  profilo dei fianchi.

## Campione, fissato prima
- Dragonbane Quickstart: **tutte** le 47 pagine (il caso d'origine).
- Cinque manuali di benchmark del repo (DB, Fab, Dag, Apo, Lan): **20 pagine
  ciascuno**, estratte a caso con seed **20260906**, per verificare che il
  fenomeno non sia specifico di un manuale.

## Predizioni registrate
- **H1** — sulle pagine senza bande i corridoi ci sono, e a scartarli e'
  `too_short`: il corridoio esiste ma e' piu' basso del minimo in righe della
  pagina, perche' tabelle, riquadri e titoli a tutta larghezza lo spezzano in
  tratti corti. E' l'ipotesi che mi aspetto.
- **H2** — alternativa: sulle pagine senza bande **non viene incatenato alcun
  corridoio**. Se e' cosi', la causa non e' nei criteri di ammissione ma a monte,
  nella griglia dei vuoti, e H1 e' falsa.
- **H3** — la distribuzione dei motivi di scarto sulle pagine senza bande e'
  **diversa** da quella sulle pagine con bande. Se e' identica, i motivi di
  scarto non spiegano la differenza e la causa e' altrove.

Le tre non sono esclusive per costruzione: il campione puo' dare pagine di tipi
diversi. Riporto la ripartizione, non un vincitore.

## Criterio di accettazione
La diagnostica si accetta se, **per ogni pagina senza bande del campione**, dice
a quale passo la banda e' andata persa: corridoio mai formato, oppure scartato e
da quale criterio. Il residuo non attribuito si conta e si dichiara; se supera
il 5% delle pagine senza bande, la diagnostica non basta e va detto invece di
concludere.

Nessun numero di questa milestone autorizza a spostare una soglia. Attribuire
una causa non e' deciderne la correzione.

---

# Fase 2 — aggiunta DOPO l'esito della Fase 1, PRIMA di guardarne i dati

La Fase 1 ha attribuito tutte e 14 le pagine senza bande del Quickstart, e ha
falsificato H1: non e' `too_short`. Ma ha anche mostrato che **la domanda era
mal posta**, ed e' un rilievo contro di me: 12 delle 14 pagine senza bande hanno
1-3 righe di testo o fianchi vuoti — sono frontespizi e stacchi, e una pagina
con due righe non ha colonne. Le pagine senza bande **non sono il problema**.

Il problema e' l'altro numero, quello che avevo raccontato male: **il testo che
resta fuori dalle bande su pagine che le bande ce l'hanno**. Pagina indice 28 ha
2 bande e 46 primitive su 98 dentro; e' la pagina che l'utente ha visto
schiacciata, ed e' li' che l'ordine di lettura degrada.

## La domanda della Fase 2
Quando una pagina ha bande ma meta' del testo ne resta fuori, **dove sta** quel
testo rispetto alle bande?

## Predizioni registrate
- **K1** — sta **sopra la banda piu' alta o sotto la piu' bassa**: l'estensione
  verticale di un corridoio copre solo la fascia dove il corridoio e'
  dimostrato, quindi titoli, cappelli e code di pagina restano fuori per
  costruzione. E' l'ipotesi che mi aspetto.
- **K2** — alternativa: sta **dentro l'intervallo y delle bande ma fuori dalla
  loro x** (margini, note laterali, numeri di riga).
- **K3** — alternativa: sta **fra due bande consecutive**, in fasce verticali
  che nessuna banda copre.

Riporto la ripartizione fra le tre, non un vincitore. Se nessuna supera le
altre in modo netto, lo dico invece di scegliere quella che mi piace.

## Criterio di accettazione della Fase 2
Ogni primitiva fuori banda dev'essere attribuita a una delle tre posizioni. Il
residuo non attribuito si conta; sopra il 5% la diagnostica non basta.

---

# Fase 3 — aggiunta dopo la Fase 2, PRIMA dei suoi dati

## Perche' serve
La Fase 2 ha detto **dove** sta il testo fuori banda (sopra la prima, sotto
l'ultima). Non ha detto **se quel testo abbia bisogno di un ordine di colonna**.
Un titolo a tutta larghezza, una tabella a tutta larghezza e un paragrafo a
colonna unica stanno fuori dalle bande e vengono ordinati per `y`: per loro `y`
e' l'ordine **giusto**, e contarli come danno gonfia il problema.

Il caso che apre la fase, ispezionato: Quickstart p.28, 52 span fuori banda, di
cui la quasi totalita' e' la tabella `TIRO/EVENTO` a tutta larghezza. Il danno
reale sono le **6 righe** del cappello a due colonne (3 righe per colonna), il
cui corridoio e' alto ~2 righe di pagina contro le 3 di `min_gutter_lines`.

## La misura
Per ogni riga fuori banda si guarda se ha **righe affiancate**: un'altra riga che
si sovrappone al suo intervallo `y` e occupa un intervallo `x` disgiunto. Chi non
ne ha e' materiale a tutta larghezza o a colonna unica, e l'ordine per `y` non lo
danneggia. Chi ne ha e' testo affiancato letto senza struttura di colonna, ed e'
il danno vero.

Nessuna soglia nuova: «affiancate» e' una relazione geometrica fra due righe, non
un valore da scegliere.

## Predizioni registrate
- **P1** — la maggior parte del testo fuori banda **non** ha righe affiancate:
  predico **oltre il 60%**. Se e' cosi', il numero «43 pagine su 47» che ho
  riportato descrive un problema molto piu' piccolo di come suona, e il verbale
  deve dirlo.
- **P2** — il danno reale (fuori banda **e** affiancate) e' concentrato in pochi
  blocchi corti, non sparso: predico che su Quickstart stia su meno di 10 pagine.

## Criterio di accettazione
La misura si accetta se ogni riga fuori banda finisce in una delle due classi.
Non autorizza a spostare `min_gutter_lines` ne' nessun'altra soglia: dice quanto
grande e' il problema, non come si corregge.
