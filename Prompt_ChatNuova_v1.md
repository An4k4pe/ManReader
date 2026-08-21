# Prompt per la chat nuova — ManReader

Da incollare in una conversazione nuova. Sei Chat A.

## L'obiettivo, che si rilegge e non si ricorda

`AGENTS.MD` §Obiettivo per intero. In breve: **PDF TTRPG → Markdown ed EPUB
semantici**, contenuto preservato, **e** immagini, sfondi ed elementi ripetuti
**sostituiti da note brevi che dicono cosa sostituiscono**, con gli asset in una
cartella referenziata.

Il metro di questo giro, dichiarato dall'utente: **un file Markdown leggibile a
occhio umano.** La domanda che ferma qualunque proposta è quella di `CLAUDE.md`:
*questo avvicina un Markdown leggibile, o solo la coerenza interna del meccanismo
su cui stiamo lavorando?*

## Che cosa leggere, in quest'ordine

1. `CLAUDE.md`, `AGENTS.MD`, `ManReader_TwoChat_Agent_Workflow.md` — **interi**.
2. `State.md`, la **sola Milestone 39**. Verifica di aver ricevuto la riga
   sentinella in fondo al file: se non compare, la copia è troncata, fermati e
   dillo. **Non leggere `State_Archive.md`.**
3. `Consegna_TabelleChat_v1.md` — dove si è fermato il lavoro sulle tabelle, i
   rilievi verificati e non corretti, e la trappola delle tre numerazioni di pagina.
4. `Proposta_RegioneTabella_v3.md` — le rettifiche alle due affermazioni della v2
   che non reggono più.

## Dove siamo

`main` a `a2f5e18`, branch `claude/table-region-producer-005fb8`. **Niente
committato**: tre criteri, quattro esiti, sette script, tre proposte fuori dal
repo. L'ordine di commit è nel §7 della consegna.

## La prima cosa da fare: **scegliere su che cosa lavorare**

Non è già deciso. Sotto ci sono le tre opzioni con i numeri che le riguardano,
tutti già misurati e a verbale. La scelta è dell'utente; Chat A porta i numeri e
una raccomandazione, non una decisione presa.

---

### Opzione A — la forma del testo: titoli e coppie etichetta-valore

**A favore.**
- Su Wil p.245, la pagina che Milestone 39 usa come metro: 55 paragrafi emessi, di
  cui **38 (69%) di due parole o meno**; l'ordine sbagliato è il **4%**. *L'ordine
  è quasi giusto, è la forma che manca.*
- Quel 69% è fatto di **titoli di sezione** (`text.heading`, criterio inesistente)
  e **coppie etichetta-valore** (`text.labelled_entry`, la cui ritrattazione è
  stata a sua volta ritirata).
- Tocca **ogni pagina**, non una classe.
- `State.md` Milestone 39 la mette **prima** nell'elenco «aperto, in ordine di
  quanto blocca».

**Contro.**
- `text.heading` non ha un criterio, e su DB p.99 il solo corpo di pagina ne
  prenderebbe **uno su quattro** (`SCHELETRO` a 34pt contro una moda di 9, ma tre
  titoli di pannello a 10).
- La misura del 69% è su **una pagina sola**.

**Primo passo proposto, e non è un meccanismo**: misurare su un campione cieco
quanti paragrafi emessi da IR 2 sono di ≤2 parole, manuale per manuale. Il proxy
esiste già. Dice se il 69% è di quella pagina o del progetto, e **decide da solo**
se la strada è questa. Criterio registrato prima, commit senza codice.

---

### Opzione B — le tabelle

**A favore.**
- Il meccanismo a massimo numero di colonne funziona: 13 tabelle corrette su 16, e
  sulle pagine tracciate a mano dall'utente i gutter coincidono con i suoi.
- Il difetto dominante è **uno solo e identificato**: la regione attraversa il
  gutter di pagina e lo adotta come colonna. Misurato su quattro pagine.
- Molta della strada è fatta: colonne, righe, estensione, restringimento.

**Contro.**
- Un campione cieco di 60 pagine contiene **3 tabelle normali**. Anche una tabella
  perfetta lascia 57 pagine su 60 come sono.
- Il «13 su 16» è un **fit**: sei regolazioni tarate su sei di quelle stesse
  pagine. Un numero fuori campione non esiste.
- Sul cieco da 120 pagine, **107 producono una regione** e delle 16 filtrate al
  100% quattro su cinque aperte non sono tabelle. Il tasso di base è intatto.
- L'indicatore di qualità è un **artefatto** (calcolato sulla finestra sbagliata) e
  va rifatto.
- Per il difetto dominante **cinque forme di vincolo sono già cadute**.

**Primo passo se si sceglie questa**: un criterio pre-registrato per il meccanismo
nuovo, su un campione **di tabelle** e non di pagine — 60 pagine uniformi ne
contengono tre, quindi il campione va costruito in un altro modo, e come si
costruisce senza sceglierlo a mano è la prima domanda da risolvere.

---

### Opzione C — irrobustire `column_band` e lo scarto dei bordi

**A favore.** È infrastruttura che serve a tutto il resto, e due difetti sono
identificati: le linguette di capitolo fatte di **testo** non hanno oggi nessun
producer che le tolga (`side_band` non è wired, Milestone 6 l'ha congelato), e i
numeri display alti come mezza pagina rompono il raggruppamento in bande.

**Contro.** Serve all'**ordine di lettura**, che sulla pagina di riferimento è già
al **4%** di errore. Migliora la parte che funziona.

---

## Che cosa NON riaprire, deciso e misurato

- **Tarare `--min-flanking-chars`** e **far decidere a `column_band` se una regione
  è una tabella**: chiusi in `State.md` §Cosa NON rifare.
- **`Criterio_TabellaNormale_v1.md`**: eseguito, **cade** (zero su tre su campione
  cieco). Non va rieseguito, va superato da un criterio nuovo.
- **Le dieci ipotesi cadute** sull'estensione della regione e sulla scelta della
  riga: sono a verbale nelle docstring degli script, ciascuna con la pagina e i
  numeri che la falsificano.
- **L'ottimizzazione del prototipo tabelle**: il codice è **39 volte più veloce** di
  quanto un verbale precedente affermasse. 1,7 s a pagina, misurato.

## Tre rilievi verificati e non corretti, da chiudere se si tocca quel codice

1. `coherence` è calcolato sulla finestra **seme** e riportato dopo l'estensione:
   il numero non descrive la regione emessa.
2. `_blockers` ha `width`/`height` di pagina **ombreggiate** dal ciclo sui disegni:
   fino a due terzi dei bloccanti persi su pagine con arredo pesante.
3. `analyse` emette **una sola regione per pagina**: su Lan pag52, che ne ha due,
   una si perde.

Altri sette rilievi della revisione indipendente non sono stati verificati: sono
elencati nel §3 della consegna.

## Come lavorare — tre regole imparate a caro prezzo

1. **Prima di una misura che decide se una linea prosegue, registra il criterio per
   iscritto e committalo senza codice** (`AGENTS.MD` §15). Dove è stato fatto ha
   funzionato; dove non è stato fatto sono cadute quattro ipotesi decise a
   posteriori.
2. **Un conteggio non sostituisce uno sguardo, e un orologio non è una misura.**
   Due numeri sono finiti in un verbale senza essere stati misurati — la velocità
   del prototipo, sbagliata di 39×, e la separazione dell'indicatore di pienezza —
   ed entrambi sono stati trovati da una revisione indipendente, non da chi li
   aveva scritti.
3. **Cerca nel repo prima di proporre.** Quattro volte in una sessione il progetto
   aveva già la risposta, e una era una regola dell'utente già in produzione.

## Che cosa consegnare

Una proposta sola, con: il difetto osservato che la motiva **con la pagina**, il
criterio di accettazione scritto prima, il perimetro chiuso, e cosa resta
esplicitamente fuori. Poi il giro di revisione indipendente.
