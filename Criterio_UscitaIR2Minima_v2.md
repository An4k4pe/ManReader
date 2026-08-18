# Criterio di uscita — IR 2 minima, bersaglio Markdown (v2)

**Supera `Criterio_UscitaIR2Minima_v1.md`.** Nulla è stato eseguito contro la v1:
l'ordine vincolante del suo §6 era commit → estrazione → riferimento → esecuzione,
e siamo fra il secondo e il terzo passo. Riscrivere ora è legittimo; riscrivere
dopo l'esecuzione sarebbe il difetto che `Criterio_ParagrafoDaBlocco_v1.md` porta
scritto in testa.

Restano invariati dalla v1: il §1 (che cosa questo criterio non è), E-A, e la
regola di estrazione del campione, già eseguita e messa a verbale in
`Campione_UscitaIR2Minima_v1.md`.

---

## 1. Perché E-B cambia

La v1 formulava E-B come «l'ordine emesso è sbagliato?», con un riferimento umano
da produrre trascrivendo le pagine a mano.

**La domanda era mal posta, e il campione stesso lo ha dimostrato.** Eseguita la
fetta verticale sulle nove pagine eseguibili del campione, il giudizio a vista
dell'utente è stato: *l'ordine di lettura è già corretto, a parte le tabelle, che
sono ovviamente sbagliate perché il producer di tabelle non esiste.*

Nove pagine su nove, estratte a caso da un pool non condizionato, mai viste prima,
giudicate **prima che IR 2 esista**. L'ordine non è il rischio: è già acquisito.

Il rischio vero è l'altro, e la v1 non lo misurava: **che IR 2 rompa un ordine che
oggi è corretto.**

## 2. E-B, riscritto

> L'ordine emesso da IR 2 sulle nove pagine deve essere **identico** alla base.
> Ogni differenza va **spiegata**; una differenza non spiegata fa fallire il giro.

**La base**, identificata senza ambiguità e senza committare output: l'uscita di
`scripts/prototype_vertical_slice_page.py --emit-order-variants` (file
`page_bands.md`) al commit **`3a2238d`**, sulle nove pagine di
`Campione_UscitaIR2Minima_v1.md` diverse da `Wil` idx 71. Nessuno dei commit di
criterio tocca codice, quindi la base è deterministicamente rigenerabile.

**Questo criterio può fallire**, ed è il motivo per cui sostituisce il precedente:
se IR 2 riordina, il confronto lo mostra. Non è un confronto «migliora rispetto a
un'uscita sbagliata» — è un confronto contro un'uscita **giudicata corretta da una
persona su un campione cieco**.

## 3. Le due esclusioni, dichiarate prima

**Le tabelle.** Il producer di tabelle non esiste, l'utente ha già identificato
quelle regioni come sbagliate nella base, e giudicare lo stadio su un compito che
non ha sarebbe scorretto. Le differenze dentro una regione di tabella si riportano
e non fanno fallire.

**`Wil` idx 71.** Non ha una base, perché la fetta ci crasha (§ *Difetto Wil* di
`Esito_PrecondizioniIR2_v1.md`). Rientra nel campione quando il crash è chiuso, e
fino ad allora il campione è di **nove** pagine, non dieci.

Restano valide le esclusioni della v1: il rumore da note d'asset sulle pagine
ricche di arredo, e l'assenza di titoli.

## 4. Cosa NON sostituisce il confronto con la base

Il confronto prima/dopo dice **cosa è cambiato**, non **se è giusto**. È lo stesso
rapporto che `State.md:144` fissa fra I2 e il terzo invariante, e la distinzione fu
aggiunta lì proprio perché i due erano stati trovati contraddittori.

Qui regge solo perché la base **è stata giudicata da una persona** prima che IR 2
esistesse. Se un giorno la base venisse rigenerata da una pipeline modificata e non
rigiudicata, il criterio tornerebbe a non poter fallire, e andrebbe rifatto il
giudizio a vista su un campione nuovo.

## 5. Ordine delle operazioni, vincolante

1. Questo file viene committato. *(fatto in questo commit)*
2. Il crash di `Wil` idx 71 viene chiuso, o la pagina resta esclusa.
3. L'implementazione viene eseguita sul campione e confrontata con la base.
4. Ogni differenza viene spiegata **prima** di dichiarare l'esito.

Il passo 4 non è formalità: spiegare le differenze dopo aver deciso l'esito è la
lettura post-hoc che `AGENTS.MD` §Regole operative punto 15 vieta.
