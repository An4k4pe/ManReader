# Criterio di accettazione — la tabella in IR 2

Registrato **prima** dell'implementazione, in un commit che non contiene codice.
Riferimento: `Proposta_TabellaInIR2_v3.md` §6.

**Uno solo.** La v1 della proposta aveva tre criteri che non potevano fallire; la
v2 li ha sostituiti con due che non potevano passare e uno ancora vacuo. Qui c'è
un errore squalificante e due conteggi che si riportano.

---

## 1. Il campione e le etichette

Riusa il protocollo già registrato in `Criterio_TabellaRisolvibile_v1.md` §4 e mai
eseguito: **12 pagine**, seed **`20260820`**, estratte uniformemente dal pool dei
16 manuali, con le esclusioni per costruzione già in
`scripts/sample_ir2_verification_pages.py`.

**L'etichetta la dà l'utente a vista sul render — «tabella», «scheda», «nessuna
delle due» — PRIMA di vedere qualunque uscita del codice nuovo.** Invertire
l'ordine renderebbe l'etichetta una lettura post-hoc.

## 2. Il baseline, salvato prima

Per ogni pagina del campione si salva su disco, **prima di toccare il codice**,
l'**elenco ordinato dei paragrafi** di `page_ir2.md`.

Elenco, non sequenza di caratteri: `_normalised_sequence` butta gli spazi, quindi
due paragrafi fusi e due separati danno la **stessa** stringa. Il difetto che
questo criterio deve cogliere è precisamente una fusione (§3).

## 3. L'errore squalificante — uno

> Dopo la modifica, l'elenco dei paragrafi di una pagina, **escludendo i nodi
> tabella**, deve essere una **sottosequenza esatta** del baseline: ogni voce
> presente identica carattere per carattere, e nell'ordine.

Un paragrafo che è diventato cella **sparisce** dall'elenco, ed è atteso. Un
paragrafo **fuso** con un altro non compare nel baseline, quindi fa fallire — che
è lo scopo.

**Perché serve**: `ir2_builder` decide i paragrafi sull'adiacenza nella sequenza
ricevuta. Estrarre le primitive delle celle rende adiacenti due righe che prima
non lo erano, e il titolo di una tabella può saldarsi alla sua nota a piè. Non lo
coglie il validatore — gli id restano coperti — né un confronto sui caratteri.

## 4. I due conteggi, che si riportano e non fissano una soglia

1. quante regioni etichettate **«tabella»** escono **come tabella**, giudicate a
   vista dall'utente con il render accanto;
2. quante escono sbagliate, **e in che modo**.

**Nessuna soglia sul numero di tabelle**, e la ragione è che quante se ne ottengano
dipende da un'ipotesi non misurata — che i gutter di `column_band` descrivano le
colonne (`Proposta_TabellaInIR2_v3.md` §3.1). Fissare adesso un numero
significherebbe inventarlo o tararlo su ciò che l'implementazione produrrà. Il
conteggio **lo giudica l'utente**, come il campione cieco di Milestone 38.

## 5. Regola d'arresto

**Una sola regressione fuori dalla tabella ferma il giro.**

**Zero tabelle riuscite non lo ferma**, ma va scritto come esito: «non ha rotto
niente e non ha prodotto nulla» è un esito, e su questo progetto è il più
frequente.

## 6. Verifiche di contratto, che non sostituiscono il criterio

Automatiche, verdi a ogni esecuzione, e non concorrono al giudizio: copertura di
`ir2_validate` estesa alle celle (unione delle celle uguale alle primitive del
nodo, coordinate complete e non sovrapposte); round-trip della serializzazione;
suite; ruff; basedpyright.

Sono guardie contro i bug, **non** misure del disegno — la distinzione che
Milestone 38 aveva dovuto scrivere dopo averla sbagliata.

## 7. Limiti dichiarati prima

**L'ipotesi portante non è misurata**: che i gutter descrivano le colonne di una
tabella. A favore DB p.76; contro `State.md:128` («accetta una colonna di tabella
e ne rifiuta le sorelle», Dag p.117, ispezionata) e i 109 confini di banda dentro
il bbox di una primitiva contati da G2.

**Se cade, cade l'impianto del §3 della proposta, non il criterio.** In quel caso
i confini di colonna vanno cercati altrove, e questo giro si chiude con l'esito
scritto.
