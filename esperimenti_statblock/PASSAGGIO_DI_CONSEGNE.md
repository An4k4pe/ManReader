# Passaggio di consegne — riconoscimento delle schede statistiche

Documento di trasferimento verso una chat nuova. Scritto alla chiusura della
sessione che ha prodotto i nove commit del ramo
`claude/statblock-asset-class-yf3y9c`.

**Leggi prima `CLAUDE.md` e `AGENTS.MD` del repo, e la sezione pertinente di
`State.md`** (non il file intero, non `State_Archive.md`). Questo documento non
li sostituisce: dice cosa e' stato fatto qui, non quali sono le regole del
progetto.

**Niente di quanto segue e' una decisione architetturale.** E' materiale
esplorativo: nessun codice di produzione e' stato toccato, `esperimenti_statblock/`
non importa nulla dal repo e non e' wired da nessuna parte.

---

## 1. Da dove nasce

Una proposta esterna («lo statblock come classe di asset») e' arrivata da fuori
progetto, dichiarando A PRIORI ogni sua affermazione sul repo.
`Istruzione_PropostaStatblock_v1.md` (radice del repo) e' la verifica di quelle
affermazioni. Due esiti che contano ancora:

- il suo unico argomento era che sbloccava «il punto in cui il progetto e'
  fermo», il reading order multicolonna. Milestone 37 lo aveva gia' sbloccato
  nella stessa revisione che la proposta dichiarava di aver letto;
- **il caso era gia' registrato nel repo**: `State.md:903`, appunto di chiusura
  di Milestone 36, descrive le schede di bestiario come «campi etichetta:valore
  da preservare» e offre due rami — uno `structural_kind` dedicato **oppure** un
  trattamento di resa separato dalla classificazione geometrica. Il secondo ramo
  e' piu' economico e nessuno l'ha ancora esplorato.

## 2. Il principio del metodo, in una riga

**La frequenza separa lo schema dal contenuto.**

`Difficulty` compare 148 volte in un bestiario ed e' schema; `Daggers` compare
poche volte ed e' contenuto di quella scheda. Nessuna semantica serve per
distinguerli, nessun vocabolario va fornito, e la cosa e' indipendente da lingua
e sistema.

I passi:

1. **Etichetta** = span di stile diverso a inizio riga, seguito da testo di
   corpo. Definizione strutturale, non lessicale, e **non dipende dai due
   punti** (misurato: la variante ancorata ai due punti trova 0 schede su 2 su
   un formato che scrive `PF 5`).
2. **Frequenza** su tutto il documento: le etichette ricorrenti sono schema,
   quelle rare sono contenuto.
3. **Gruppi**: le regioni si raggruppano per somiglianza dell'insieme di
   etichette. Ogni gruppo e' un template.
4. **Schema**: dentro un gruppo, un'etichetta presente in quasi tutti i membri
   e' obbligatoria.
5. **Classificazione**: una regione e' una scheda di quel template se ha tutti
   i suoi obbligatori. **Lo schema indotto e' il classificatore**: non serve un
   LLM per decidere se una zona e' una scheda, e a differenza di un LLM
   risponde con un motivo verificabile.

## 3. Cosa e' stabilito, con l'evidenza

Su **Daggerheart SRD** (68 pagine, 1022 zone candidate), verita' costruita per
via indipendente dal metodo:

- **148 schede su 148 riconosciute, 0 rifiutate, 0 falsi positivi**;
- **due template indotti dal documento**, mai forniti: avversari (n=129,
  obbligatori `ATK, Difficulty, HP, Motives & Tactics, Stress, Thresholds`) e
  ambienti (n=17, obbligatori `Difficulty, Impulses, Potential Adversaries`);
- assegnazione al template: 129 avversari e 19 ambienti, **zero incroci**;
- non e' circolare: togliendo `Difficulty` dallo schema resta 148/148 con 0 FP;
- copertura del testo delle pagine 37-55: 100% dalle zone.

**Nessun LLM e' mai stato chiamato in nessuno di questi esperimenti.** Dove i
file parlano di «modello», e' simulato con dizionari scritti a mano, e serviva
solo a provare che il contratto intercetta invenzione e perdita.

Altre cose misurate e ferme:

- **L'ordine di lettura e' un prerequisito del rilevamento, non un problema
  parallelo.** Ordinando per y poi x su pagine a quattro colonne il conteggio
  crolla da 148 a 58: una scheda si delimita solo dentro la colonna.
- **La dimensione del carattere non serve a trovare le schede** (le sole
  etichette ne localizzano 148 su 148) ma serve a **marcarne la testa**: senza,
  si perdono ~3,6 righe in testa e ~15,5 in coda per scheda, cioe' quasi tutto
  il blocco delle capacita'. La coda di un record non porta etichette di schema
  per definizione, quindi e' invisibile a un metodo lessicale.
- **Sensibilita'**: sei costanti su dieci non pesano su intervalli larghi. Le
  fragili sbagliano **tutte allo stesso modo**: perdono il template meno
  numeroso e conservano quello grande con precisione intatta.

## 4. Cosa ha fallito, ed e' il punto da cui ripartire

`pila.py` (rilevamento per pila di testa) e' stato eseguito **congelato** sul
**Dragonbane Quickstart** italiano, 47 pagine, senza che mi fosse detta
l'etichetta ricorrente. Verita': 4 schede mostro.

**Fallito, per tre cause indipendenti** (dettaglio in `VERDETTO_MANUALE2.md`):

1. **Quattro istanze contro una soglia di cinque.** `Ferocia` compare 4 volte,
   sotto `MIN_RICORRENZA`, quindi scartata: il template non si forma mai. E' la
   fragilita' prevista e committata **prima** del test, e si e' manifestata
   **in silenzio** — il metodo ha riportato 16 gruppi e 34 etichette, tutte nomi
   di abilita' delle schede personaggio, senza segnalare nulla.
2. **Regressione mia**: `etichetta()` in `pila.py` prende solo il primo span
   della riga, ma il formato mette 2-3 campi per riga (`Ferocia: 2  Taglia:
   Normale`). `Taglia` risulta 0 occorrenze su 4, `Armatura` 1, `PF` 3. La
   versione precedente (`real5.py`) estraeva piu' coppie per riga. **Correggerla
   non avrebbe salvato il test**: resterebbero 4 occorrenze, sotto soglia.
3. **Il separatore di colonne non trasferisce**: `COL_GAP = 30pt`, tarato su
   quattro colonne larghe 250pt, frantuma una pagina a colonna singola da 612pt
   in 2-4 colonne spurie. Su 2 schede su 4 il nome centrato finisce in una
   colonna diversa dai propri campi.

**La pila di testa non e' mai stata validata**: il prerequisito e' fallito a
monte, quindi la formalizzazione resta non provata.

## 5. Le quattro correzioni pendenti

Nessuna iniziata. Non decise: sono la mia proposta, l'utente non le ha ancora
autorizzate.

1. **Co-occorrenza al posto del conteggio.** Legare la soglia di ricorrenza alla
   dimensione minima di gruppo impedisce per costruzione di vedere un template
   di 4 elementi. Il criterio giusto e' probabilmente che quelle 5 etichette
   compaiano **insieme**, sempre, in poche regioni vicine — non che ognuna sia
   frequente da sola.
2. **Separatore di colonne derivato** da un profilo di proiezione verticale del
   testo, non fissato in punti.
3. **Estrazione multipla per riga ripristinata** (piu' coppie etichetta/valore
   sulla stessa riga).
4. **Misura di copertura**, ed e' la piu' importante: quanto testo del documento
   non e' spiegato da nessuno schema, e dove si concentra. Con 4 schede su 47
   pagine quel residuo sarebbe saltato all'occhio, e il fallimento non sarebbe
   stato silenzioso.

**Entrambi i manuali disponibili sono ormai bruciati come banco di prova**: il
primo perche' il metodo e' stato progettato su di esso, il secondo perche' ne ha
rivelato i difetti. Validare le correzioni richiede un **terzo** manuale, mai
usato, meglio se di sistema diverso e con un bestiario numeroso.

## 6. Cosa e' congelato

`pila.py` e' congelato per la validazione (`SPEC_PILA.md`). Se lo modifichi,
dichiaralo e considera che il confronto con il giro precedente non vale piu'.
Le tre modifiche gia' fatte, tutte correzioni di difetto e non tarature, sono
elencate in fondo a `SPEC_PILA.md`.

## 7. Le regole di metodo, imparate a caro prezzo

Valgono oltre questo lavoro.

- **Ogni statistica si calcola sulla popolazione della regione, mai sul
  documento.** Ha sbagliato tre volte per lo stesso motivo: lo stile di corpo
  globale (9pt) non e' quello delle schede (8pt); il lift globale rende «raro»
  un corpo locale; una soglia globale cancella il template piccolo.
- **Il criterio si scrive prima di guardare i dati**, ed e' stato utile: due
  predizioni registrate sono state **falsificate** (la ricerca del livello
  tipografico ha scelto il corpo; lo stile di apertura derivato ha scelto la
  riga di descrizione). Senza registrazione preventiva sarebbero passate per
  successi con un ritocco.
- **Un manuale su cui un metodo e' stato progettato non lo puo' validare.** Due
  correzioni post-hoc bastano a bruciare un banco di prova.
- **Distinguere correzione di difetto da taratura di soglia**, e dichiarare
  entrambe. Una soglia spostata dopo aver visto il risultato non e' una
  correzione.
- **Il guasto peggiore e' quello silenzioso.** Un rifiuto con motivazione
  plausibile (`forma del valore incoerente`) ha scartato una scheda valida in un
  giro sintetico; sul manuale reale un template intero e' sparito senza che
  nessun allarme scattasse.

## 8. Se si arriva a produrre YAML

Non implementato, ma deciso a ragione:

- **trascrizione** (chiavi = etichette stampate, valori = stringhe **sempre
  quotate**, struttura = sequenza e non dizionario perche' le etichette si
  ripetono) separata dall'**interpretazione** verso uno schema bersaglio, che e'
  una mappa opzionale a valle e deve poter fallire senza perdere contenuto;
- lo YAML e' l'**asset**, non il prodotto per il lettore: file estratto, nota
  che lo referenzia, resa inline leggibile;
- se un giorno si emette per il plugin Obsidian: **non scrivere mai il campo
  `id`** (un id esplicito condivide lo stato fra tutte le istanze nel vault);
- **fallimento rumoroso**: una regione con forma di record che non corrisponde a
  nessuno schema si emette verbatim con una nota «struttura non riconosciuta»,
  mai si scarta.

## 9. Compito registrato, non iniziato

`COMPITO_APERTO_schede_rare.md`: dopo i template frequenti, etichettare e
rendere in Markdown anche le schede **rare o uniche**. Precondizione dichiarata
dall'utente: chiudere prima il punto corrente. Contiene la ragione per cui non
e' una questione di soglia e la distinzione fra «rara ma dello stesso template»
(gia' coperta in linea di principio) e «unica nel formato» (il caso vero).

## 10. Come far arrivare un manuale

L'utente ha ~30 MB di quota di caricamento. Non serve mandare il PDF:
`dump_spans.py` estrae solo cio' che il metodo usa e riduce 230x (Dragonbane:
17,0 MB -> 76 KB; ~1,3 KB per pagina). `pila_da_dump.py` esegue il rilevatore
sul dump, e l'equivalenza col PDF e' **verificata riga per riga**, non assunta.
Dettagli e avvertenze in `COME_MANDARE_UN_MANUALE.md`.

## 11. Cosa non c'e' nel repo, e non deve esserci

I PDF dei manuali e i dump degli span: contengono il testo integrale e ai fini
dei diritti valgono come il manuale (`.gitignore` esclude gia' `*.pdf`).
Chi riprende il lavoro deve farsi dare i file dall'utente.

## 12. Mappa dei file

| file | cos'e' |
| --- | --- |
| `CRITERIO.md` | criterio scritto prima dei dati sintetici |
| `synth.py`, `detect.py` | corpus sintetico e i quattro rilevatori pre-registrati |
| `posthoc.py`, `confound.py`, `nocolon.py` | metodi post-hoc dichiarati, e i due confondenti |
| `pipeline.py` | contratto zona -> ruoli -> assemblaggio verbatim -> verifica (modello simulato) |
| `schema.py`, `fit2.py` | induzione della forma, schema come classificatore |
| `CRITERIO_REALE.md`, `real5.py`, `RISULTATI_DAGGERHEART.txt` | il giro sul primo manuale reale |
| `sens.py`, `sens2.py`, `SENSIBILITA.txt` | analisi di sensibilita' sulle costanti |
| `CRITERIO_APERTURA.md`, `apertura*.py` | formalizzazione della soglia di apertura, predizione falsificata |
| `CRITERIO_SENZA_CORPO.md`, `senzacorpo*.py`, `stileapertura.py` | la dimensione serve? tre esperimenti |
| `SPEC_PILA.md`, `pila.py` | specifica congelata e implementazione della pila di testa |
| `VERDETTO_MANUALE2.md` | il fallimento sul secondo manuale, con le tre cause |
| `dump_spans.py`, `pila_da_dump.py`, `COME_MANDARE_UN_MANUALE.md` | ingresso alternativo al PDF |
| `COMPITO_APERTO_schede_rare.md` | il compito registrato e non iniziato |

Tutti gli script girano con `python3` e richiedono solo PyMuPDF.
