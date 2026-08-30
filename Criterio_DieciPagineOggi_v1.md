# Criterio — le dieci pagine di riferimento, giudicate **su quello che escono oggi**

**Scritto prima di guardare il materiale.** Una pagina, come il §17 prescrive.

## 0. Perché

Il giudizio che fonda E-B è del **17 agosto 2026** e copriva **il solo ordine di
lettura**, tabelle escluse, su una pipeline che non aveva paragrafi, elenchi,
titoli, enfasi né arredo. Da allora `ir2_builder.py`, `ir2_markdown.py` e
`ir2_model.py` hanno preso **26 commit**.

> **Nessuno ha mai giudicato l'uscita di IR 2 su queste dieci pagine.** È stata
> giudicata l'uscita della fetta verticale, ed è un altro artefatto.

Rilievo dell'utente: «io ho giudicato quelle pagine prima di molte modifiche
sulla IR e abbellimenti, sarebbe il caso di rivalutarle prima di usarle come test
statico».

**La base non è stantia** — verificato, è byte per byte quella giudicata,
rigenerata al commit dichiarato e confrontata su tutte e dieci. Stantia è la
copertura del giudizio, non il suo oggetto.

## 1. Che cosa si giudica

L'uscita **corrente**, con tutti i meccanismi accesi — `--arredo --elenchi` — di
ognuna delle dieci pagine, **contro l'immagine della pagina del PDF**. Non contro
la base: la base è l'uscita vecchia, e ancorarci il giudizio misurerebbe il
passato invece dell'obiettivo.

Quattro domande per pagina, nell'ordine in cui contano:

1. **Manca qualcosa** che sulla pagina c'è?
2. **È stato tolto qualcosa che non doveva?** Il canale `review` si mostra per
   intero accanto al corpo, ed è lì che l'arredo finisce.
3. **Si legge?** Che cosa rende la pagina confusa, brutta o faticosa.
4. **C'è qualcosa marcato male?** Un titolo che è prosa, una voce che non è una
   voce, un paragrafo spezzato o fuso.

## 2. Il campione

**Le stesse dieci pagine di `Campione_UscitaIR2Minima_v1.md`**, e la scelta è
deliberata: sono il riferimento di E-B, e la domanda è se reggano ancora come
tale. Sorteggiate a suo tempo con seed `20260818` da un pool non condizionato,
mai scelte da me.

Nessun campionamento nuovo e nessun seed: sono dieci e si guardano tutte.

## 3. Pass/fail

### A. La barra dura — il contenuto si conserva

> **Cade su una sola pagina** in cui il giudizio dice che manca del testo che
> sulla pagina c'è, e che non compare né nel corpo né in `review`.

È il primo invariante del progetto e non ammette tolleranza. La domanda 1 è
quella che lo misura, e il canale review sta nel materiale proprio perché uno
spostamento non venga scambiato per una perdita.

### B. L'arredo non porta via contenuto

> **Cade su una sola pagina** in cui qualcosa di tolto dal corpo sia giudicato
> contenuto.

È la stessa barra che ha già fatto cadere due clausole d'arredo — quella del
testo ripetuto e quella del verticale — e qui vale su un campione che non ho
scelto io.

### C. La leggibilità, che si riporta e non fa cadere

> Si elencano i difetti per pagina e si contano le pagine che ne hanno **zero**.

Non è una barra: è la misura dell'utente — *un file Markdown leggibile da occhi
umani* — e questo giro serve a dire dove sta, non a promuovere o bocciare.

## 4. Che cosa questo giudizio **non** decide

**Non sostituisce la base di E-B.** La base vale perché **non è prodotta dal
codice sotto esame**: se il riferimento diventasse l'uscita di IR 2, E-B
catturerebbe il cambiamento e non l'errore, e la sua validità starebbe tutta in un
giudizio umano. Le due cose restano separate e si tengono entrambe.

**Non riapre le tabelle**, che restano escluse dal giudizio come nel criterio
d'uscita: il producer non esiste e giudicare un compito che non c'è è scorretto.
Una tabella resa male si annota e non conta contro nessuna barra.

**Non decide la gerarchia dei titoli**, rimandata esplicitamente dall'utente.

## 5. Se cade

- **A**: si nomina la pagina e il testo perso, e diventa il lavoro successivo
  prima di qualunque altra cosa. Una perdita di contenuto non si mette in coda.
- **B**: si nomina quale clausola d'arredo l'ha causata. Sarebbe la terza.
- **C** non cade: qualunque numero esca, è il punto di partenza dichiarato del
  prossimo giro.
